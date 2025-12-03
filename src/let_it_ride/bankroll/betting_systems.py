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
