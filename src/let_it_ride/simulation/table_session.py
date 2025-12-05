"""Multi-player table session management for Let It Ride.

This module provides TableSession that manages bankrolls and stop conditions
for multiple players at a table, building on the Table class from core.

Key types:
- TableSessionConfig: Configuration for a multi-player session
- SeatSessionResult: Per-seat results reusing SessionResult
- TableSessionResult: Aggregated results for entire table session
- TableSession: Orchestrates multi-player session state and execution
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
        max_hands: Maximum hands (rounds) to play. None for unlimited.
        stop_on_insufficient_funds: If True, stop seat when bankroll cannot
            cover the minimum bet (base_bet * 3 + bonus_bet).
        bonus_bet: Fixed bonus bet amount per hand. 0 to disable bonus.
    """

    table_config: TableConfig
    starting_bankroll: float
    base_bet: float
    win_limit: float | None = None
    loss_limit: float | None = None
    max_hands: int | None = None
    stop_on_insufficient_funds: bool = True
    bonus_bet: float = 0.0

    def __post_init__(self) -> None:
        """Validate configuration values."""
        if self.starting_bankroll <= 0:
            raise ValueError("starting_bankroll must be positive")
        if self.base_bet <= 0:
            raise ValueError("base_bet must be positive")
        if self.win_limit is not None and self.win_limit <= 0:
            raise ValueError("win_limit must be positive if set")
        if self.loss_limit is not None and self.loss_limit <= 0:
            raise ValueError("loss_limit must be positive if set")
        if self.max_hands is not None and self.max_hands <= 0:
            raise ValueError("max_hands must be positive if set")
        if self.bonus_bet < 0:
            raise ValueError("bonus_bet cannot be negative")

        # Validate at least one stop condition is configured
        has_stop_condition = (
            self.win_limit is not None
            or self.loss_limit is not None
            or self.max_hands is not None
            or self.stop_on_insufficient_funds
        )
        if not has_stop_condition:
            raise ValueError(
                "At least one stop condition must be configured: "
                "win_limit, loss_limit, max_hands, or stop_on_insufficient_funds"
            )

        # Validate starting bankroll covers minimum bet
        min_bet_required = (self.base_bet * 3) + self.bonus_bet
        if self.starting_bankroll < min_bet_required:
            raise ValueError(
                f"starting_bankroll ({self.starting_bankroll}) must be at least "
                f"base_bet * 3 + bonus_bet ({min_bet_required})"
            )


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

    Attributes:
        seat_results: Results for each seat at the table.
        total_rounds: Total number of rounds played.
        stop_reason: The reason the session stopped (from last triggered seat).
    """

    seat_results: tuple[SeatSessionResult, ...]
    total_rounds: int
    stop_reason: StopReason


class _SeatState:
    """Internal mutable state for a single seat during a session.

    This class tracks per-seat state including bankroll, wagering totals,
    and streak information needed for BettingContext.
    """

    __slots__ = (
        "bankroll",
        "total_wagered",
        "total_bonus_wagered",
        "last_result",
        "streak",
        "stop_reason",
    )

    def __init__(self, starting_bankroll: float) -> None:
        """Initialize seat state.

        Args:
            starting_bankroll: Initial bankroll amount.
        """
        self.bankroll = BankrollTracker(starting_bankroll)
        self.total_wagered: float = 0.0
        self.total_bonus_wagered: float = 0.0
        self.last_result: float | None = None
        self.streak: int = 0
        self.stop_reason: StopReason | None = None

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


class TableSession:
    """Manages a multi-player Let It Ride table session.

    A table session runs multiple rounds using a Table until all seats
    hit stop conditions. It tracks per-seat bankroll, statistics, and
    provides context for strategy and betting decisions.

    For single-seat tables (num_seats=1), behavior matches the existing
    Session class for backwards compatibility.
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
            _SeatState(config.starting_bankroll) for _ in range(num_seats)
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

    def _minimum_bet_required(self) -> float:
        """Return the minimum amount needed to play a round.

        A round requires 3 base bets plus any bonus bet.
        """
        return (self._config.base_bet * 3) + self._config.bonus_bet

    def _check_seat_stop_condition(self, seat_state: _SeatState) -> bool:
        """Check if a seat has hit any stop condition.

        Updates the seat's stop_reason if a condition is met.

        Args:
            seat_state: The seat state to check.

        Returns:
            True if the seat should stop.
        """
        if seat_state.stop_reason is not None:
            return True

        # Check win limit
        if (
            self._config.win_limit is not None
            and seat_state.bankroll.session_profit >= self._config.win_limit
        ):
            seat_state.stop_reason = StopReason.WIN_LIMIT
            return True

        # Check loss limit
        if (
            self._config.loss_limit is not None
            and seat_state.bankroll.session_profit <= -self._config.loss_limit
        ):
            seat_state.stop_reason = StopReason.LOSS_LIMIT
            return True

        # Check max hands (rounds for table session)
        if (
            self._config.max_hands is not None
            and self._rounds_played >= self._config.max_hands
        ):
            seat_state.stop_reason = StopReason.MAX_HANDS
            return True

        # Check insufficient funds
        if self._config.stop_on_insufficient_funds:
            min_required = self._minimum_bet_required()
            if seat_state.bankroll.balance < min_required:
                seat_state.stop_reason = StopReason.INSUFFICIENT_FUNDS
                return True

        return False

    def _all_seats_stopped(self) -> bool:
        """Check if all seats have hit stop conditions.

        Returns:
            True if every seat has stopped.
        """
        return all(seat.is_stopped for seat in self._seat_states)

    def should_stop(self) -> bool:
        """Check if the table session should stop.

        The session stops when all seats have hit their stop conditions.

        Returns:
            True if the session should stop.
        """
        if self._stop_reason is not None:
            return True

        # Check each seat's stop conditions
        for seat_state in self._seat_states:
            self._check_seat_stop_condition(seat_state)

        # Session stops when all seats have stopped
        if self._all_seats_stopped():
            # Use the stop reason from the last seat that triggered
            # (Find the last seat that became stopped this check)
            for seat_state in reversed(self._seat_states):
                if seat_state.stop_reason is not None:
                    self._stop_reason = seat_state.stop_reason
                    break
            return True

        return False

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

            # Skip seats that have already stopped
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

        return result

    def run_to_completion(self) -> TableSessionResult:
        """Run the session until all seats hit stop conditions.

        Returns:
            TableSessionResult with complete session statistics.
        """
        while not self.should_stop():
            self.play_round()

        # Build per-seat results
        seat_results: list[SeatSessionResult] = []
        for idx, seat_state in enumerate(self._seat_states):
            seat_number = idx + 1

            # Determine outcome
            profit = seat_state.bankroll.session_profit
            if profit > 0:
                outcome = SessionOutcome.WIN
            elif profit < 0:
                outcome = SessionOutcome.LOSS
            else:
                outcome = SessionOutcome.PUSH

            # Seat stop reason is guaranteed to be set
            assert seat_state.stop_reason is not None

            session_result = SessionResult(
                outcome=outcome,
                stop_reason=seat_state.stop_reason,
                hands_played=self._rounds_played,
                starting_bankroll=self._config.starting_bankroll,
                final_bankroll=seat_state.bankroll.balance,
                session_profit=profit,
                total_wagered=seat_state.total_wagered,
                total_bonus_wagered=seat_state.total_bonus_wagered,
                peak_bankroll=seat_state.bankroll.peak_balance,
                max_drawdown=seat_state.bankroll.max_drawdown,
                max_drawdown_pct=seat_state.bankroll.max_drawdown_pct,
            )

            seat_results.append(
                SeatSessionResult(
                    seat_number=seat_number,
                    session_result=session_result,
                )
            )

        # Table stop reason is guaranteed to be set
        assert self._stop_reason is not None

        return TableSessionResult(
            seat_results=tuple(seat_results),
            total_rounds=self._rounds_played,
            stop_reason=self._stop_reason,
        )
