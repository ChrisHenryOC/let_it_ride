"""Multi-player table session management for Let It Ride.

This module provides TableSession that manages bankrolls and stop conditions
for multiple players at a table, building on the Table class from core.

Key types:
- TableSessionConfig: Configuration for a multi-player session
- SeatSessionResult: Per-seat results reusing SessionResult
- TableSessionResult: Aggregated results for entire table session
- TableSession: Orchestrates multi-player session state and execution

Seat Replacement Mode:
When `table_total_rounds` is configured, seats that hit individual stop
conditions are reset with fresh bankroll (simulating a new player sitting
down). The table runs for the configured number of rounds, with seats
cycling through multiple player sessions.
"""

from dataclasses import dataclass

from let_it_ride.bankroll.betting_systems import BettingContext, BettingSystem
from let_it_ride.bankroll.tracker import BankrollTracker
from let_it_ride.config.models import TableConfig
from let_it_ride.core.table import Table, TableRoundResult
from let_it_ride.simulation.session import (
    SessionOutcome,
    SessionResult,
    StopReason,
    calculate_new_streak,
    validate_session_config,
)
from let_it_ride.strategy.base import StrategyContext


@dataclass(frozen=True, slots=True)
class TableSessionConfig:
    """Configuration for a multi-player table session.

    All seats share the same configuration parameters.

    Attributes:
        table_config: Configuration for the table (number of seats).
        starting_bankroll: Initial bankroll amount for each seat.
        base_bet: Base bet amount per circle.
        win_limit: Stop seat when profit reaches this amount. None to disable.
        loss_limit: Stop seat when loss reaches this amount (positive value).
            None to disable.
        max_hands: Maximum hands per player session. None for unlimited.
            In seat replacement mode, this applies per-session, not globally.
        stop_on_insufficient_funds: If True, stop seat when bankroll cannot
            cover the minimum bet (base_bet * 3 + bonus_bet).
        bonus_bet: Fixed bonus bet amount per hand. 0 to disable bonus.
        table_total_rounds: Total rounds to run the table. When set, enables
            seat replacement mode: seats hitting stop conditions are reset
            with fresh bankroll. None to use classic "all seats stop" mode.
    """

    table_config: TableConfig
    starting_bankroll: float
    base_bet: float
    win_limit: float | None = None
    loss_limit: float | None = None
    max_hands: int | None = None
    stop_on_insufficient_funds: bool = True
    bonus_bet: float = 0.0
    table_total_rounds: int | None = None

    def __post_init__(self) -> None:
        """Validate configuration values."""
        validate_session_config(
            starting_bankroll=self.starting_bankroll,
            base_bet=self.base_bet,
            win_limit=self.win_limit,
            loss_limit=self.loss_limit,
            max_hands=self.max_hands,
            bonus_bet=self.bonus_bet,
            stop_on_insufficient_funds=self.stop_on_insufficient_funds,
        )
        # Validate table_total_rounds
        if self.table_total_rounds is not None and self.table_total_rounds <= 0:
            raise ValueError("table_total_rounds must be positive if set")


@dataclass(frozen=True, slots=True)
class SeatSessionResult:
    """Result for a single seat in a table session.

    Wraps a SessionResult with seat position information.

    Attributes:
        seat_number: The seat position (1-based).
        session_result: Complete session results for this seat.
    """

    seat_number: int
    session_result: SessionResult


@dataclass(frozen=True, slots=True)
class TableSessionResult:
    """Complete results of a finished table session.

    In classic mode (table_total_rounds=None), seat_results contains one
    result per seat. In seat replacement mode, seat_sessions contains
    all sessions per seat position (potentially multiple per seat).

    Attributes:
        seat_results: Results for each seat at the table (classic mode).
            In seat replacement mode, this contains only the final/in-progress
            session for backwards compatibility. Use seat_sessions for full data.
        total_rounds: Total number of rounds played.
        stop_reason: The reason the session stopped.
        seat_sessions: All sessions per seat position (seat_number -> sessions).
            Only populated in seat replacement mode. None in classic mode.
    """

    seat_results: tuple[SeatSessionResult, ...]
    total_rounds: int
    stop_reason: StopReason
    seat_sessions: dict[int, list[SeatSessionResult]] | None = None


class _SeatState:
    """Internal mutable state for a single seat during a session.

    This class tracks per-seat state including bankroll, wagering totals,
    and streak information needed for BettingContext.

    In seat replacement mode, also tracks completed sessions and supports
    resetting for new players.
    """

    __slots__ = (
        "bankroll",
        "total_wagered",
        "total_bonus_wagered",
        "last_result",
        "streak",
        "stop_reason",
        "completed_sessions",
        "session_start_round",
        "_starting_bankroll",
    )

    def __init__(self, starting_bankroll: float, current_round: int = 0) -> None:
        """Initialize seat state.

        Args:
            starting_bankroll: Initial bankroll amount.
            current_round: The round number when this session starts.
        """
        self._starting_bankroll = starting_bankroll
        self.bankroll = BankrollTracker(starting_bankroll)
        self.total_wagered: float = 0.0
        self.total_bonus_wagered: float = 0.0
        self.last_result: float | None = None
        self.streak: int = 0
        self.stop_reason: StopReason | None = None
        self.completed_sessions: list[SeatSessionResult] = []
        self.session_start_round = current_round

    def update_streak(self, result: float) -> None:
        """Update the win/loss streak based on hand result.

        Args:
            result: The net result of the hand.
        """
        self.streak = calculate_new_streak(self.streak, result)

    @property
    def is_stopped(self) -> bool:
        """Return True if this seat has hit a stop condition."""
        return self.stop_reason is not None

    def hands_played_this_session(self, current_round: int) -> int:
        """Return the number of hands played in the current session.

        Args:
            current_round: The current round number.

        Returns:
            Number of hands (rounds) played since session started.
        """
        return current_round - self.session_start_round

    def reset(self, current_round: int) -> None:
        """Reset seat state for a new player session.

        Clears all state and starts fresh with the original starting bankroll.
        Does NOT clear completed_sessions - that persists across resets.

        Args:
            current_round: The round number when the new session starts.
        """
        self.bankroll = BankrollTracker(self._starting_bankroll)
        self.total_wagered = 0.0
        self.total_bonus_wagered = 0.0
        self.last_result = None
        self.streak = 0
        self.stop_reason = None
        self.session_start_round = current_round


class TableSession:
    """Manages a multi-player Let It Ride table session.

    A table session runs multiple rounds using a Table. It tracks per-seat
    bankroll, statistics, and provides context for strategy and betting decisions.

    Classic Mode (table_total_rounds=None):
        Session runs until all seats hit stop conditions. Stopped seats "sit out"
        while remaining seats continue.

    Seat Replacement Mode (table_total_rounds set):
        Table runs for a fixed number of rounds. When a seat hits its stop
        condition, the completed session is recorded and the seat is reset
        with a fresh bankroll (simulating a new player sitting down).
        This models a busy casino table where seats are continuously occupied.

    For single-seat tables (num_seats=1) with max_hands and no table_total_rounds,
    behavior matches the existing Session class for backwards compatibility.
    """

    __slots__ = (
        "_config",
        "_table",
        "_betting_system",
        "_seat_states",
        "_rounds_played",
        "_stop_reason",
    )

    def __init__(
        self,
        config: TableSessionConfig,
        table: Table,
        betting_system: BettingSystem,
    ) -> None:
        """Initialize a new table session.

        Args:
            config: Table session configuration.
            table: Table for playing rounds.
            betting_system: BettingSystem for determining bet sizes.
                Shared across all seats.
        """
        self._config = config
        self._table = table
        self._betting_system = betting_system
        self._rounds_played = 0
        self._stop_reason: StopReason | None = None

        # Initialize per-seat states
        num_seats = config.table_config.num_seats
        self._seat_states: list[_SeatState] = [
            _SeatState(config.starting_bankroll, current_round=0)
            for _ in range(num_seats)
        ]

        # Reset betting system for new session
        self._betting_system.reset()

    @property
    def rounds_played(self) -> int:
        """Return the number of rounds played."""
        return self._rounds_played

    @property
    def is_complete(self) -> bool:
        """Return True if the session has stopped."""
        return self._stop_reason is not None

    @property
    def seat_replacement_mode(self) -> bool:
        """Return True if seat replacement mode is enabled."""
        return self._config.table_total_rounds is not None

    def _minimum_bet_required(self) -> float:
        """Return the minimum amount needed to play a round.

        A round requires 3 base bets plus any bonus bet.
        """
        return (self._config.base_bet * 3) + self._config.bonus_bet

    def _build_session_result_for_seat(
        self, seat_idx: int, stop_reason: StopReason
    ) -> SeatSessionResult:
        """Build a SeatSessionResult for the given seat.

        Args:
            seat_idx: The seat index (0-based).
            stop_reason: The reason this session stopped.

        Returns:
            SeatSessionResult with complete statistics.
        """
        seat_state = self._seat_states[seat_idx]
        seat_number = seat_idx + 1

        # Determine outcome
        profit = seat_state.bankroll.session_profit
        if profit > 0:
            outcome = SessionOutcome.WIN
        elif profit < 0:
            outcome = SessionOutcome.LOSS
        else:
            outcome = SessionOutcome.PUSH

        # Calculate hands played for this session
        hands_played = seat_state.hands_played_this_session(self._rounds_played)

        session_result = SessionResult(
            outcome=outcome,
            stop_reason=stop_reason,
            hands_played=hands_played,
            starting_bankroll=self._config.starting_bankroll,
            final_bankroll=seat_state.bankroll.balance,
            session_profit=profit,
            total_wagered=seat_state.total_wagered,
            total_bonus_wagered=seat_state.total_bonus_wagered,
            peak_bankroll=seat_state.bankroll.peak_balance,
            max_drawdown=seat_state.bankroll.max_drawdown,
            max_drawdown_pct=seat_state.bankroll.max_drawdown_pct,
        )

        return SeatSessionResult(
            seat_number=seat_number,
            session_result=session_result,
        )

    def _check_seat_stop_condition(self, seat_idx: int) -> StopReason | None:
        """Check if a seat has hit any stop condition.

        In seat replacement mode, hitting a stop condition triggers:
        1. Save current session result to completed_sessions
        2. Reset the seat for a new player

        In classic mode, just sets the seat's stop_reason.

        Args:
            seat_idx: The seat index (0-based).

        Returns:
            The StopReason if triggered, None otherwise.
        """
        seat_state = self._seat_states[seat_idx]

        if seat_state.stop_reason is not None:
            return seat_state.stop_reason

        stop_reason: StopReason | None = None

        # Check win limit
        if (
            self._config.win_limit is not None
            and seat_state.bankroll.session_profit >= self._config.win_limit
        ):
            stop_reason = StopReason.WIN_LIMIT

        # Check loss limit
        elif (
            self._config.loss_limit is not None
            and seat_state.bankroll.session_profit <= -self._config.loss_limit
        ):
            stop_reason = StopReason.LOSS_LIMIT

        # Check max hands (per-session in seat replacement mode)
        elif self._config.max_hands is not None:
            hands_this_session = seat_state.hands_played_this_session(
                self._rounds_played
            )
            if hands_this_session >= self._config.max_hands:
                stop_reason = StopReason.MAX_HANDS

        # Check insufficient funds
        elif self._config.stop_on_insufficient_funds:
            min_required = self._minimum_bet_required()
            if seat_state.bankroll.balance < min_required:
                stop_reason = StopReason.INSUFFICIENT_FUNDS

        if stop_reason is not None:
            if self.seat_replacement_mode:
                # Seat replacement mode: save session and reset
                result = self._build_session_result_for_seat(seat_idx, stop_reason)
                seat_state.completed_sessions.append(result)
                seat_state.reset(self._rounds_played)
                # Return None to indicate seat is ready to continue
                return None
            else:
                # Classic mode: mark seat as stopped
                seat_state.stop_reason = stop_reason
                return stop_reason

        return None

    def _all_seats_stopped(self) -> bool:
        """Check if all seats have hit stop conditions.

        Only relevant in classic mode.

        Returns:
            True if every seat has stopped.
        """
        return all(seat.is_stopped for seat in self._seat_states)

    def should_stop(self) -> bool:
        """Check if the table session should stop.

        In seat replacement mode: stops when table_total_rounds is reached.
        In classic mode: stops when all seats have hit their stop conditions.

        Returns:
            True if the session should stop.
        """
        if self._stop_reason is not None:
            return True

        # Seat replacement mode: check total rounds
        if self.seat_replacement_mode:
            assert self._config.table_total_rounds is not None
            if self._rounds_played >= self._config.table_total_rounds:
                self._stop_reason = StopReason.TABLE_ROUNDS_COMPLETE
                return True
            return False

        # Classic mode: check each seat's stop conditions
        for seat_idx in range(len(self._seat_states)):
            self._check_seat_stop_condition(seat_idx)

        # Session stops when all seats have stopped
        if self._all_seats_stopped():
            # Use the stop reason from the last seat that triggered
            for seat_state in reversed(self._seat_states):
                if seat_state.stop_reason is not None:
                    self._stop_reason = seat_state.stop_reason
                    break
            return True

        return False

    @property
    def stop_reason(self) -> StopReason | None:
        """Return the reason the session stopped, or None if not stopped."""
        return self._stop_reason

    def play_round(self) -> TableRoundResult:
        """Play a single round and update session state for all seats.

        Returns:
            The result of the round.

        Raises:
            RuntimeError: If the session is already complete.
        """
        if self._stop_reason is not None:
            raise RuntimeError("Cannot play round: session is already complete")

        # In seat replacement mode, check stop conditions before playing
        # This handles seats that just completed a session
        if self.seat_replacement_mode:
            for seat_idx in range(len(self._seat_states)):
                self._check_seat_stop_condition(seat_idx)

        # Get bet amount from betting system using first active seat's context
        # (all seats share the same betting system state)
        first_active_seat = next(
            (s for s in self._seat_states if not s.is_stopped),
            self._seat_states[0],
        )
        betting_context = BettingContext(
            bankroll=first_active_seat.bankroll.balance,
            starting_bankroll=self._config.starting_bankroll,
            session_profit=first_active_seat.bankroll.session_profit,
            last_result=first_active_seat.last_result,
            streak=first_active_seat.streak,
            hands_played=self._rounds_played,
        )
        base_bet = self._betting_system.get_bet(betting_context)

        # Get bonus bet from config
        bonus_bet = self._config.bonus_bet

        # Create strategy context using first active seat
        strategy_context = StrategyContext(
            session_profit=first_active_seat.bankroll.session_profit,
            hands_played=self._rounds_played,
            streak=first_active_seat.streak,
            bankroll=first_active_seat.bankroll.balance,
        )

        # Play the round
        result = self._table.play_round(
            round_id=self._rounds_played,
            base_bet=base_bet,
            bonus_bet=bonus_bet,
            context=strategy_context,
        )

        # Update state for each seat
        for seat_result in result.seat_results:
            seat_idx = seat_result.seat_number - 1
            seat_state = self._seat_states[seat_idx]

            # Skip seats that have already stopped (classic mode only)
            if seat_state.is_stopped:
                continue

            # Update seat state
            seat_state.total_wagered += seat_result.bets_at_risk
            seat_state.total_bonus_wagered += bonus_bet
            seat_state.bankroll.apply_result(seat_result.net_result)
            seat_state.last_result = seat_result.net_result
            seat_state.update_streak(seat_result.net_result)

        self._rounds_played += 1

        # Record result in betting system (using net result of first seat)
        if result.seat_results:
            self._betting_system.record_result(result.seat_results[0].net_result)

        # In seat replacement mode, check stop conditions after playing
        if self.seat_replacement_mode:
            for seat_idx in range(len(self._seat_states)):
                self._check_seat_stop_condition(seat_idx)

        return result

    def run_to_completion(self) -> TableSessionResult:
        """Run the session until completion.

        In seat replacement mode: runs until table_total_rounds is reached.
        In classic mode: runs until all seats hit stop conditions.

        Returns:
            TableSessionResult with complete session statistics.
        """
        while not self.should_stop():
            self.play_round()

        if self.seat_replacement_mode:
            return self._build_seat_replacement_result()
        else:
            return self._build_classic_result()

    def _build_classic_result(self) -> TableSessionResult:
        """Build result for classic mode (all seats stop).

        Returns:
            TableSessionResult with one result per seat.
        """
        seat_results: list[SeatSessionResult] = []
        for idx, seat_state in enumerate(self._seat_states):
            # Seat stop reason is guaranteed to be set
            assert seat_state.stop_reason is not None
            result = self._build_session_result_for_seat(idx, seat_state.stop_reason)
            seat_results.append(result)

        # Table stop reason is guaranteed to be set
        assert self._stop_reason is not None

        return TableSessionResult(
            seat_results=tuple(seat_results),
            total_rounds=self._rounds_played,
            stop_reason=self._stop_reason,
            seat_sessions=None,
        )

    def _build_seat_replacement_result(self) -> TableSessionResult:
        """Build result for seat replacement mode.

        Returns:
            TableSessionResult with all sessions per seat position.
        """
        # Build seat_sessions dict with all completed + in-progress sessions
        seat_sessions: dict[int, list[SeatSessionResult]] = {}

        for idx, seat_state in enumerate(self._seat_states):
            seat_number = idx + 1

            # Start with completed sessions
            sessions = list(seat_state.completed_sessions)

            # Add in-progress session if any hands were played
            if seat_state.hands_played_this_session(self._rounds_played) > 0:
                in_progress_result = self._build_session_result_for_seat(
                    idx, StopReason.IN_PROGRESS
                )
                sessions.append(in_progress_result)

            seat_sessions[seat_number] = sessions

        # For backwards compatibility, seat_results contains the last session per seat
        seat_results: list[SeatSessionResult] = []
        for sessions in seat_sessions.values():
            if sessions:
                seat_results.append(sessions[-1])

        # Table stop reason is guaranteed to be set
        assert self._stop_reason is not None

        return TableSessionResult(
            seat_results=tuple(seat_results),
            total_rounds=self._rounds_played,
            stop_reason=self._stop_reason,
            seat_sessions=seat_sessions,
        )
