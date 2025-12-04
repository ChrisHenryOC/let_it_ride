"""Betting systems for Let It Ride.

This module provides the BettingSystem protocol and implementations:
- BettingContext: State information for betting decisions
- BettingSystem: Protocol for all betting system implementations
- FlatBetting: Constant bet amount (baseline system)
"""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class BettingContext:
    """Context for betting system decisions.

    Provides bankroll state information that betting systems use to
    determine the appropriate bet amount.

    Attributes:
        bankroll: Current bankroll amount.
        starting_bankroll: Original starting bankroll for the session.
        session_profit: Current session profit/loss (positive = profit).
        last_result: Result of the last hand (None if first hand).
        streak: Current win/loss streak. Positive = consecutive wins,
            negative = consecutive losses, 0 = no streak or first hand.
        hands_played: Number of hands played this session.
    """

    bankroll: float
    starting_bankroll: float
    session_profit: float
    last_result: float | None
    streak: int
    hands_played: int


class BettingSystem(Protocol):
    """Protocol defining the interface for all betting system implementations.

    A betting system determines bet amounts based on bankroll state and
    may track internal state for progressive systems.
    """

    def get_bet(self, context: BettingContext) -> float:
        """Determine the bet amount for the next hand.

        Args:
            context: Current bankroll state information.

        Returns:
            The bet amount. Should not exceed available bankroll.
        """
        ...

    def record_result(self, result: float) -> None:
        """Record the result of a completed hand.

        Progressive systems use this to track wins/losses for
        bet progression. Flat systems may ignore this.

        Args:
            result: The hand result. Positive for wins, negative for losses.
        """
        ...

    def reset(self) -> None:
        """Reset the betting system state for a new session.

        Called at the start of each session to clear any internal
        state from previous sessions.
        """
        ...


class FlatBetting:
    """Flat (constant) betting system.

    Always returns the same base bet amount, reduced only when
    the bankroll is insufficient to cover the full bet.
    """

    __slots__ = ("_base_bet",)

    def __init__(self, base_bet: float) -> None:
        """Initialize the flat betting system.

        Args:
            base_bet: The constant bet amount to use.

        Raises:
            ValueError: If base_bet is not positive.
        """
        if base_bet <= 0:
            raise ValueError("Base bet must be positive")
        self._base_bet = base_bet

    @property
    def base_bet(self) -> float:
        """Return the configured base bet amount."""
        return self._base_bet

    def get_bet(self, context: BettingContext) -> float:
        """Return the bet amount for the next hand.

        Returns the base bet if bankroll is sufficient, otherwise
        returns the remaining bankroll (allowing reduced final bets).

        Args:
            context: Current bankroll state information.

        Returns:
            The bet amount, never exceeding available bankroll.
        """
        if context.bankroll <= 0:
            return 0.0
        return min(self._base_bet, context.bankroll)

    def record_result(self, result: float) -> None:
        """Record the result of a completed hand.

        Flat betting doesn't track results, so this is a no-op.

        Args:
            result: The hand result (ignored).
        """
        pass

    def reset(self) -> None:
        """Reset the betting system state.

        Flat betting has no state to reset, so this is a no-op.
        """
        pass

    def __repr__(self) -> str:
        """Return a string representation of the betting system."""
        return f"FlatBetting(base_bet={self._base_bet})"


class MartingaleBetting:
    """Martingale betting system.

    Doubles the bet after each loss until a win or limits are reached.
    Resets to base bet after a win.
    """

    __slots__ = ("_base_bet", "_loss_multiplier", "_max_bet", "_max_progressions", "_current_progression")

    def __init__(
        self,
        base_bet: float,
        loss_multiplier: float = 2.0,
        max_bet: float = 500.0,
        max_progressions: int = 6,
    ) -> None:
        """Initialize the Martingale betting system.

        Args:
            base_bet: The starting bet amount.
            loss_multiplier: Multiplier applied after each loss (default 2.0).
            max_bet: Maximum bet limit (table limit).
            max_progressions: Maximum number of progressions allowed.

        Raises:
            ValueError: If base_bet is not positive, loss_multiplier <= 1,
                max_bet is not positive, or max_progressions < 1.
        """
        if base_bet <= 0:
            raise ValueError("Base bet must be positive")
        if loss_multiplier <= 1:
            raise ValueError("Loss multiplier must be greater than 1")
        if max_bet <= 0:
            raise ValueError("Max bet must be positive")
        if max_progressions < 1:
            raise ValueError("Max progressions must be at least 1")

        self._base_bet = base_bet
        self._loss_multiplier = loss_multiplier
        self._max_bet = max_bet
        self._max_progressions = max_progressions
        self._current_progression = 0

    @property
    def base_bet(self) -> float:
        """Return the configured base bet amount."""
        return self._base_bet

    @property
    def loss_multiplier(self) -> float:
        """Return the configured loss multiplier."""
        return self._loss_multiplier

    @property
    def max_bet(self) -> float:
        """Return the configured maximum bet."""
        return self._max_bet

    @property
    def max_progressions(self) -> int:
        """Return the configured maximum progressions."""
        return self._max_progressions

    @property
    def current_progression(self) -> int:
        """Return the current progression level."""
        return self._current_progression

    def get_bet(self, context: BettingContext) -> float:
        """Return the bet amount based on current progression.

        Args:
            context: Current bankroll state information.

        Returns:
            The bet amount, capped at max_bet and bankroll.
        """
        if context.bankroll <= 0:
            return 0.0

        # Calculate bet based on progression level
        bet = self._base_bet * (self._loss_multiplier ** self._current_progression)

        # Apply caps
        bet = min(bet, self._max_bet)
        bet = min(bet, context.bankroll)

        return bet

    def record_result(self, result: float) -> None:
        """Record the result and adjust progression.

        Win: Reset to base bet (progression 0).
        Loss: Increase progression (up to max_progressions).

        Args:
            result: The hand result. Positive for wins, negative for losses.
        """
        if result >= 0:
            # Win or push - reset progression
            self._current_progression = 0
        else:
            # Loss - increase progression (capped)
            self._current_progression = min(
                self._current_progression + 1,
                self._max_progressions - 1
            )

    def reset(self) -> None:
        """Reset the progression to zero for a new session."""
        self._current_progression = 0

    def __repr__(self) -> str:
        """Return a string representation of the betting system."""
        return (
            f"MartingaleBetting(base_bet={self._base_bet}, "
            f"loss_multiplier={self._loss_multiplier}, "
            f"max_bet={self._max_bet}, "
            f"max_progressions={self._max_progressions})"
        )


class ReverseMartingaleBetting:
    """Reverse Martingale (Anti-Martingale/Parlay) betting system.

    Increases bet after wins, resets to base bet after losses.
    Optionally resets after reaching a profit target streak.
    """

    __slots__ = ("_base_bet", "_win_multiplier", "_profit_target_streak", "_max_bet", "_win_streak")

    def __init__(
        self,
        base_bet: float,
        win_multiplier: float = 2.0,
        profit_target_streak: int = 3,
        max_bet: float = 500.0,
    ) -> None:
        """Initialize the Reverse Martingale betting system.

        Args:
            base_bet: The starting bet amount.
            win_multiplier: Multiplier applied after each win (default 2.0).
            profit_target_streak: Number of consecutive wins before reset.
            max_bet: Maximum bet limit (table limit).

        Raises:
            ValueError: If base_bet is not positive, win_multiplier <= 1,
                profit_target_streak < 1, or max_bet is not positive.
        """
        if base_bet <= 0:
            raise ValueError("Base bet must be positive")
        if win_multiplier <= 1:
            raise ValueError("Win multiplier must be greater than 1")
        if profit_target_streak < 1:
            raise ValueError("Profit target streak must be at least 1")
        if max_bet <= 0:
            raise ValueError("Max bet must be positive")

        self._base_bet = base_bet
        self._win_multiplier = win_multiplier
        self._profit_target_streak = profit_target_streak
        self._max_bet = max_bet
        self._win_streak = 0

    @property
    def base_bet(self) -> float:
        """Return the configured base bet amount."""
        return self._base_bet

    @property
    def win_multiplier(self) -> float:
        """Return the configured win multiplier."""
        return self._win_multiplier

    @property
    def profit_target_streak(self) -> int:
        """Return the configured profit target streak."""
        return self._profit_target_streak

    @property
    def max_bet(self) -> float:
        """Return the configured maximum bet."""
        return self._max_bet

    @property
    def win_streak(self) -> int:
        """Return the current win streak count."""
        return self._win_streak

    def get_bet(self, context: BettingContext) -> float:
        """Return the bet amount based on current win streak.

        Args:
            context: Current bankroll state information.

        Returns:
            The bet amount, capped at max_bet and bankroll.
        """
        if context.bankroll <= 0:
            return 0.0

        # Calculate bet based on win streak
        bet = self._base_bet * (self._win_multiplier ** self._win_streak)

        # Apply caps
        bet = min(bet, self._max_bet)
        bet = min(bet, context.bankroll)

        return bet

    def record_result(self, result: float) -> None:
        """Record the result and adjust win streak.

        Win: Increase streak (reset if target reached).
        Loss: Reset streak to zero.

        Args:
            result: The hand result. Positive for wins, negative for losses.
        """
        if result > 0:
            # Win - increase streak
            self._win_streak += 1
            # Reset if profit target reached
            if self._win_streak >= self._profit_target_streak:
                self._win_streak = 0
        else:
            # Loss or push - reset streak
            self._win_streak = 0

    def reset(self) -> None:
        """Reset the win streak to zero for a new session."""
        self._win_streak = 0

    def __repr__(self) -> str:
        """Return a string representation of the betting system."""
        return (
            f"ReverseMartingaleBetting(base_bet={self._base_bet}, "
            f"win_multiplier={self._win_multiplier}, "
            f"profit_target_streak={self._profit_target_streak}, "
            f"max_bet={self._max_bet})"
        )


class ParoliBetting:
    """Paroli betting system.

    Increases bet after wins by a multiplier, resets to base bet after
    a specified number of consecutive wins or any loss.
    """

    __slots__ = ("_base_bet", "_win_multiplier", "_wins_before_reset", "_max_bet", "_consecutive_wins")

    def __init__(
        self,
        base_bet: float,
        win_multiplier: float = 2.0,
        wins_before_reset: int = 3,
        max_bet: float = 500.0,
    ) -> None:
        """Initialize the Paroli betting system.

        Args:
            base_bet: The starting bet amount.
            win_multiplier: Multiplier applied after each win (default 2.0).
            wins_before_reset: Number of consecutive wins before resetting.
            max_bet: Maximum bet limit (table limit).

        Raises:
            ValueError: If base_bet is not positive, win_multiplier <= 1,
                wins_before_reset < 1, or max_bet is not positive.
        """
        if base_bet <= 0:
            raise ValueError("Base bet must be positive")
        if win_multiplier <= 1:
            raise ValueError("Win multiplier must be greater than 1")
        if wins_before_reset < 1:
            raise ValueError("Wins before reset must be at least 1")
        if max_bet <= 0:
            raise ValueError("Max bet must be positive")

        self._base_bet = base_bet
        self._win_multiplier = win_multiplier
        self._wins_before_reset = wins_before_reset
        self._max_bet = max_bet
        self._consecutive_wins = 0

    @property
    def base_bet(self) -> float:
        """Return the configured base bet amount."""
        return self._base_bet

    @property
    def win_multiplier(self) -> float:
        """Return the configured win multiplier."""
        return self._win_multiplier

    @property
    def wins_before_reset(self) -> int:
        """Return the configured wins before reset."""
        return self._wins_before_reset

    @property
    def max_bet(self) -> float:
        """Return the configured maximum bet."""
        return self._max_bet

    @property
    def consecutive_wins(self) -> int:
        """Return the current consecutive win count."""
        return self._consecutive_wins

    def get_bet(self, context: BettingContext) -> float:
        """Return the bet amount based on consecutive wins.

        Args:
            context: Current bankroll state information.

        Returns:
            The bet amount, capped at max_bet and bankroll.
        """
        if context.bankroll <= 0:
            return 0.0

        # Calculate bet based on consecutive wins
        bet = self._base_bet * (self._win_multiplier ** self._consecutive_wins)

        # Apply caps
        bet = min(bet, self._max_bet)
        bet = min(bet, context.bankroll)

        return bet

    def record_result(self, result: float) -> None:
        """Record the result and adjust consecutive win count.

        Win: Increase count (reset if limit reached).
        Loss: Reset count to zero.

        Args:
            result: The hand result. Positive for wins, negative for losses.
        """
        if result > 0:
            # Win - increase count
            self._consecutive_wins += 1
            # Reset if wins before reset reached
            if self._consecutive_wins >= self._wins_before_reset:
                self._consecutive_wins = 0
        else:
            # Loss or push - reset count
            self._consecutive_wins = 0

    def reset(self) -> None:
        """Reset the consecutive win count to zero for a new session."""
        self._consecutive_wins = 0

    def __repr__(self) -> str:
        """Return a string representation of the betting system."""
        return (
            f"ParoliBetting(base_bet={self._base_bet}, "
            f"win_multiplier={self._win_multiplier}, "
            f"wins_before_reset={self._wins_before_reset}, "
            f"max_bet={self._max_bet})"
        )


class DAlembertBetting:
    """D'Alembert betting system.

    Increases bet by one unit after a loss, decreases by one unit after a win.
    The bet is clamped between min_bet and max_bet.
    """

    __slots__ = ("_base_bet", "_unit", "_min_bet", "_max_bet", "_current_bet")

    def __init__(
        self,
        base_bet: float,
        unit: float = 5.0,
        min_bet: float = 5.0,
        max_bet: float = 500.0,
    ) -> None:
        """Initialize the D'Alembert betting system.

        Args:
            base_bet: The starting bet amount.
            unit: Unit to add/subtract after loss/win (default 5.0).
            min_bet: Minimum bet floor (default 5.0).
            max_bet: Maximum bet limit (table limit).

        Raises:
            ValueError: If base_bet is not positive, unit is not positive,
                min_bet is not positive, max_bet is not positive,
                or min_bet > max_bet.
        """
        if base_bet <= 0:
            raise ValueError("Base bet must be positive")
        if unit <= 0:
            raise ValueError("Unit must be positive")
        if min_bet <= 0:
            raise ValueError("Min bet must be positive")
        if max_bet <= 0:
            raise ValueError("Max bet must be positive")
        if min_bet > max_bet:
            raise ValueError("Min bet cannot exceed max bet")

        self._base_bet = base_bet
        self._unit = unit
        self._min_bet = min_bet
        self._max_bet = max_bet
        self._current_bet = base_bet

    @property
    def base_bet(self) -> float:
        """Return the configured base bet amount."""
        return self._base_bet

    @property
    def unit(self) -> float:
        """Return the configured unit size."""
        return self._unit

    @property
    def min_bet(self) -> float:
        """Return the configured minimum bet."""
        return self._min_bet

    @property
    def max_bet(self) -> float:
        """Return the configured maximum bet."""
        return self._max_bet

    @property
    def current_bet(self) -> float:
        """Return the current bet amount."""
        return self._current_bet

    def get_bet(self, context: BettingContext) -> float:
        """Return the current bet amount.

        Args:
            context: Current bankroll state information.

        Returns:
            The bet amount, capped at bankroll if needed.
        """
        if context.bankroll <= 0:
            return 0.0

        return min(self._current_bet, context.bankroll)

    def record_result(self, result: float) -> None:
        """Record the result and adjust bet.

        Win: Decrease bet by unit (min at min_bet).
        Loss: Increase bet by unit (max at max_bet).

        Args:
            result: The hand result. Positive for wins, negative for losses.
        """
        if result > 0:
            # Win - decrease bet by unit
            self._current_bet = max(self._current_bet - self._unit, self._min_bet)
        elif result < 0:
            # Loss - increase bet by unit
            self._current_bet = min(self._current_bet + self._unit, self._max_bet)
        # Push (result == 0) - no change

    def reset(self) -> None:
        """Reset the bet to base_bet for a new session."""
        self._current_bet = self._base_bet

    def __repr__(self) -> str:
        """Return a string representation of the betting system."""
        return (
            f"DAlembertBetting(base_bet={self._base_bet}, "
            f"unit={self._unit}, "
            f"min_bet={self._min_bet}, "
            f"max_bet={self._max_bet})"
        )


class FibonacciBetting:
    """Fibonacci betting system.

    Follows the Fibonacci sequence on losses, regresses on wins.
    Bet = base_unit * fibonacci[position].
    """

    __slots__ = ("_base_unit", "_win_regression", "_max_bet", "_max_position", "_position")

    # Pre-computed Fibonacci sequence (first 20 numbers should cover most needs)
    _FIBONACCI: tuple[int, ...] = (1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987, 1597, 2584, 4181, 6765)

    def __init__(
        self,
        base_unit: float = 5.0,
        win_regression: int = 2,
        max_bet: float = 500.0,
        max_position: int = 10,
    ) -> None:
        """Initialize the Fibonacci betting system.

        Args:
            base_unit: The base unit for bet calculation (default 5.0).
            win_regression: How many positions to regress on a win (default 2).
            max_bet: Maximum bet limit (table limit).
            max_position: Maximum position in Fibonacci sequence.

        Raises:
            ValueError: If base_unit is not positive, win_regression < 1,
                max_bet is not positive, or max_position < 1.
        """
        if base_unit <= 0:
            raise ValueError("Base unit must be positive")
        if win_regression < 1:
            raise ValueError("Win regression must be at least 1")
        if max_bet <= 0:
            raise ValueError("Max bet must be positive")
        if max_position < 1:
            raise ValueError("Max position must be at least 1")

        self._base_unit = base_unit
        self._win_regression = win_regression
        self._max_bet = max_bet
        self._max_position = min(max_position, len(self._FIBONACCI) - 1)
        self._position = 0

    @property
    def base_unit(self) -> float:
        """Return the configured base unit."""
        return self._base_unit

    @property
    def win_regression(self) -> int:
        """Return the configured win regression amount."""
        return self._win_regression

    @property
    def max_bet(self) -> float:
        """Return the configured maximum bet."""
        return self._max_bet

    @property
    def max_position(self) -> int:
        """Return the configured maximum position."""
        return self._max_position

    @property
    def position(self) -> int:
        """Return the current position in the Fibonacci sequence."""
        return self._position

    def get_bet(self, context: BettingContext) -> float:
        """Return the bet amount based on current Fibonacci position.

        Args:
            context: Current bankroll state information.

        Returns:
            The bet amount, capped at max_bet and bankroll.
        """
        if context.bankroll <= 0:
            return 0.0

        # Calculate bet based on Fibonacci position
        bet = self._base_unit * self._FIBONACCI[self._position]

        # Apply caps
        bet = min(bet, self._max_bet)
        bet = min(bet, context.bankroll)

        return bet

    def record_result(self, result: float) -> None:
        """Record the result and adjust Fibonacci position.

        Win: Regress by win_regression positions (min 0).
        Loss: Advance one position (max at max_position).

        Args:
            result: The hand result. Positive for wins, negative for losses.
        """
        if result > 0:
            # Win - regress in sequence
            self._position = max(0, self._position - self._win_regression)
        elif result < 0:
            # Loss - advance in sequence
            self._position = min(self._position + 1, self._max_position)
        # Push (result == 0) - no change

    def reset(self) -> None:
        """Reset the position to 0 for a new session."""
        self._position = 0

    def __repr__(self) -> str:
        """Return a string representation of the betting system."""
        return (
            f"FibonacciBetting(base_unit={self._base_unit}, "
            f"win_regression={self._win_regression}, "
            f"max_bet={self._max_bet}, "
            f"max_position={self._max_position})"
        )
