"""Session state management for Let It Ride.

This module provides session lifecycle management with stop conditions:
- SessionConfig: Configuration for a session
- StopReason: Why a session stopped
- SessionOutcome: Final outcome (win/loss/push)
- SessionResult: Complete results of a completed session
- Session: Manages complete session state and execution
- HandCallback: Type alias for per-hand callback functions (for testing/debugging RNG)
"""

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

from let_it_ride.bankroll.betting_systems import BettingContext, BettingSystem
from let_it_ride.bankroll.tracker import BankrollTracker
from let_it_ride.core.game_engine import GameEngine, GameHandResult
from let_it_ride.strategy.base import StrategyContext
from let_it_ride.strategy.bonus import BonusContext, BonusStrategy

# Type alias for per-hand callback function.
# Called with (hand_id, GameHandResult) after each hand completes.
HandCallback = Callable[[int, GameHandResult], None]


def calculate_new_streak(current_streak: int, result: float) -> int:
    """Calculate updated win/loss streak based on hand result.

    Args:
        current_streak: Current streak value (positive for wins, negative for losses).
        result: The net result of the hand.

    Returns:
        New streak value after applying the result.
    """
    if result > 0:
        # Win: increment if winning streak, else start new winning streak
        return current_streak + 1 if current_streak > 0 else 1
    elif result < 0:
        # Loss: decrement if losing streak, else start new losing streak
        return current_streak - 1 if current_streak < 0 else -1
    # Push (result == 0) doesn't change streak
    return current_streak


class StopReason(Enum):
    """Reason why a session stopped.

    WIN_LIMIT: Session profit reached or exceeded win limit.
    LOSS_LIMIT: Session loss reached or exceeded loss limit.
    MAX_HANDS: Maximum number of hands reached.
    INSUFFICIENT_FUNDS: Bankroll too low to place minimum bet.
    """

    WIN_LIMIT = "win_limit"
    LOSS_LIMIT = "loss_limit"
    MAX_HANDS = "max_hands"
    INSUFFICIENT_FUNDS = "insufficient_funds"


class SessionOutcome(Enum):
    """Final outcome of a session based on profit/loss.

    WIN: Session ended with positive profit.
    LOSS: Session ended with negative profit.
    PUSH: Session ended with zero profit.
    """

    WIN = "win"
    LOSS = "loss"
    PUSH = "push"


@dataclass(frozen=True, slots=True)
class SessionConfig:
    """Configuration for a session.

    Attributes:
        starting_bankroll: Initial bankroll amount.
        base_bet: Base bet amount per circle (used for min bet calculation).
        win_limit: Stop when profit reaches this amount. None to disable.
        loss_limit: Stop when loss reaches this amount (positive value).
            None to disable.
        max_hands: Maximum hands to play. None for unlimited.
        stop_on_insufficient_funds: If True, stop when bankroll cannot
            cover the minimum bet (base_bet * 3).
        bonus_bet: Fixed bonus bet amount per hand. 0 to disable bonus.
    """

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
class SessionResult:
    """Complete results of a finished session.

    Attributes:
        outcome: Whether the session was a WIN, LOSS, or PUSH.
        stop_reason: Why the session stopped.
        hands_played: Total number of hands played.
        starting_bankroll: Initial bankroll amount.
        final_bankroll: Bankroll at end of session.
        session_profit: Net profit/loss (final - starting).
        total_wagered: Sum of all bets placed.
        total_bonus_wagered: Sum of all bonus bets placed.
        peak_bankroll: Highest bankroll reached during session.
        max_drawdown: Maximum peak-to-trough decline.
        max_drawdown_pct: Maximum drawdown as percentage of peak.
    """

    outcome: SessionOutcome
    stop_reason: StopReason
    hands_played: int
    starting_bankroll: float
    final_bankroll: float
    session_profit: float
    total_wagered: float
    total_bonus_wagered: float
    peak_bankroll: float
    max_drawdown: float
    max_drawdown_pct: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON/CSV export.

        Enum values are converted to their string values.

        Returns:
            Dictionary with all fields suitable for export.
        """
        return {
            "outcome": self.outcome.value,
            "stop_reason": self.stop_reason.value,
            "hands_played": self.hands_played,
            "starting_bankroll": self.starting_bankroll,
            "final_bankroll": self.final_bankroll,
            "session_profit": self.session_profit,
            "total_wagered": self.total_wagered,
            "total_bonus_wagered": self.total_bonus_wagered,
            "peak_bankroll": self.peak_bankroll,
            "max_drawdown": self.max_drawdown,
            "max_drawdown_pct": self.max_drawdown_pct,
        }


class Session:
    """Manages a complete Let It Ride session.

    A session runs multiple hands using a GameEngine until a stop
    condition is met. It tracks bankroll, statistics, and provides
    the context needed for strategy and betting decisions.
    """

    __slots__ = (
        "_config",
        "_engine",
        "_betting_system",
        "_bonus_strategy",
        "_bankroll",
        "_hands_played",
        "_total_wagered",
        "_total_bonus_wagered",
        "_last_result",
        "_streak",
        "_bonus_streak",
        "_stop_reason",
        "_hand_callback",
    )

    def __init__(
        self,
        config: SessionConfig,
        engine: GameEngine,
        betting_system: BettingSystem,
        bonus_strategy: BonusStrategy | None = None,
        hand_callback: HandCallback | None = None,
    ) -> None:
        """Initialize a new session.

        Args:
            config: Session configuration.
            engine: GameEngine for playing hands.
            betting_system: BettingSystem for determining bet sizes.
            bonus_strategy: Optional BonusStrategy for dynamic bonus betting.
                If provided, overrides config.bonus_bet with dynamic amounts.
            hand_callback: Optional callback called after each hand completes.
                Called with (hand_id, GameHandResult).
        """
        self._config = config
        self._engine = engine
        self._betting_system = betting_system
        self._bonus_strategy = bonus_strategy
        self._hand_callback = hand_callback
        self._bankroll = BankrollTracker(config.starting_bankroll)
        self._hands_played = 0
        self._total_wagered = 0.0
        self._total_bonus_wagered = 0.0
        self._last_result: float | None = None
        self._streak = 0
        self._bonus_streak = 0
        self._stop_reason: StopReason | None = None

        # Reset betting system for new session
        self._betting_system.reset()

        # Reset bonus strategy if it has a reset method
        if self._bonus_strategy is not None and hasattr(self._bonus_strategy, "reset"):
            self._bonus_strategy.reset()

    @property
    def hands_played(self) -> int:
        """Return the number of hands played."""
        return self._hands_played

    @property
    def is_complete(self) -> bool:
        """Return True if the session has stopped."""
        return self._stop_reason is not None

    @property
    def session_profit(self) -> float:
        """Return the current session profit/loss."""
        return self._bankroll.session_profit

    @property
    def bankroll(self) -> float:
        """Return the current bankroll balance."""
        return self._bankroll.balance

    @property
    def streak(self) -> int:
        """Return the current win/loss streak."""
        return self._streak

    def _update_streak(self, result: float) -> None:
        """Update the win/loss streak based on hand result.

        Args:
            result: The net result of the hand.
        """
        self._streak = calculate_new_streak(self._streak, result)

    def _minimum_bet_required(self) -> float:
        """Return the minimum amount needed to play a hand.

        A hand requires 3 base bets plus any bonus bet.
        """
        return (self._config.base_bet * 3) + self._config.bonus_bet

    def should_stop(self) -> bool:
        """Check if any stop condition is met.

        Returns:
            True if the session should stop.
        """
        if self._stop_reason is not None:
            return True

        # Check win limit
        if (
            self._config.win_limit is not None
            and self._bankroll.session_profit >= self._config.win_limit
        ):
            self._stop_reason = StopReason.WIN_LIMIT
            return True

        # Check loss limit (loss_limit is positive, session_profit is negative when losing)
        if (
            self._config.loss_limit is not None
            and self._bankroll.session_profit <= -self._config.loss_limit
        ):
            self._stop_reason = StopReason.LOSS_LIMIT
            return True

        # Check max hands
        if (
            self._config.max_hands is not None
            and self._hands_played >= self._config.max_hands
        ):
            self._stop_reason = StopReason.MAX_HANDS
            return True

        # Check insufficient funds
        if self._config.stop_on_insufficient_funds:
            min_required = self._minimum_bet_required()
            if self._bankroll.balance < min_required:
                self._stop_reason = StopReason.INSUFFICIENT_FUNDS
                return True

        return False

    def stop_reason(self) -> StopReason | None:
        """Return the reason the session stopped, or None if not stopped."""
        return self._stop_reason

    def play_hand(self) -> GameHandResult:
        """Play a single hand and update session state.

        Returns:
            The result of the hand.

        Raises:
            RuntimeError: If the session is already complete.
        """
        if self._stop_reason is not None:
            raise RuntimeError("Cannot play hand: session is already complete")

        # Get bet amount from betting system
        betting_context = BettingContext(
            bankroll=self._bankroll.balance,
            starting_bankroll=self._config.starting_bankroll,
            session_profit=self._bankroll.session_profit,
            last_result=self._last_result,
            streak=self._streak,
            hands_played=self._hands_played,
        )
        base_bet = self._betting_system.get_bet(betting_context)

        # Get bonus bet from strategy or config
        if self._bonus_strategy is not None:
            bonus_context = BonusContext(
                bankroll=self._bankroll.balance,
                starting_bankroll=self._config.starting_bankroll,
                session_profit=self._bankroll.session_profit,
                hands_played=self._hands_played,
                main_streak=self._streak,
                bonus_streak=self._bonus_streak,
                base_bet=base_bet,
                min_bonus_bet=1.0,  # Default minimum
                max_bonus_bet=100.0,  # Default maximum
            )
            bonus_bet = self._bonus_strategy.get_bonus_bet(bonus_context)
        else:
            bonus_bet = self._config.bonus_bet

        # Create strategy context
        strategy_context = StrategyContext(
            session_profit=self._bankroll.session_profit,
            hands_played=self._hands_played,
            streak=self._streak,
            bankroll=self._bankroll.balance,
        )

        # Play the hand
        result = self._engine.play_hand(
            hand_id=self._hands_played,
            base_bet=base_bet,
            bonus_bet=bonus_bet,
            context=strategy_context,
        )

        # Determine win/loss for main and bonus bets
        main_won = result.main_payout > 0
        bonus_won: bool | None = None
        if result.bonus_bet > 0:
            bonus_won = result.bonus_payout > 0

        # Update session state
        self._hands_played += 1
        self._total_wagered += result.bets_at_risk
        self._total_bonus_wagered += bonus_bet
        self._bankroll.apply_result(result.net_result)
        self._last_result = result.net_result
        self._update_streak(result.net_result)
        self._update_bonus_streak(bonus_won)

        # Record result in betting system
        self._betting_system.record_result(result.net_result)

        # Record result in bonus strategy if it supports state tracking
        if self._bonus_strategy is not None and hasattr(
            self._bonus_strategy, "record_result"
        ):
            self._bonus_strategy.record_result(main_won=main_won, bonus_won=bonus_won)

        # Call hand callback if registered
        if self._hand_callback is not None:
            self._hand_callback(result.hand_id, result)

        return result

    def _update_bonus_streak(self, bonus_won: bool | None) -> None:
        """Update the bonus win/loss streak based on bonus result.

        Args:
            bonus_won: True if bonus won, False if lost, None if no bonus bet.
        """
        if bonus_won is None:
            # No bonus bet placed, streak unchanged
            return
        if bonus_won:
            self._bonus_streak = (
                self._bonus_streak + 1 if self._bonus_streak > 0 else 1
            )
        else:
            self._bonus_streak = (
                self._bonus_streak - 1 if self._bonus_streak < 0 else -1
            )

    def run_to_completion(self) -> SessionResult:
        """Run the session until a stop condition is met.

        Returns:
            SessionResult with complete session statistics.
        """
        while not self.should_stop():
            self.play_hand()

        # Determine outcome
        profit = self._bankroll.session_profit
        if profit > 0:
            outcome = SessionOutcome.WIN
        elif profit < 0:
            outcome = SessionOutcome.LOSS
        else:
            outcome = SessionOutcome.PUSH

        # Build result - _stop_reason is guaranteed to be set since at least
        # one stop condition is required by SessionConfig validation
        assert self._stop_reason is not None
        return SessionResult(
            outcome=outcome,
            stop_reason=self._stop_reason,
            hands_played=self._hands_played,
            starting_bankroll=self._config.starting_bankroll,
            final_bankroll=self._bankroll.balance,
            session_profit=profit,
            total_wagered=self._total_wagered,
            total_bonus_wagered=self._total_bonus_wagered,
            peak_bankroll=self._bankroll.peak_balance,
            max_drawdown=self._bankroll.max_drawdown,
            max_drawdown_pct=self._bankroll.max_drawdown_pct,
        )
