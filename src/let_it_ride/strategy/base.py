"""Base types and protocols for Let It Ride strategy implementations.

This module defines the Strategy protocol that all strategy implementations
must follow, along with supporting types like Decision and StrategyContext.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from let_it_ride.core.card import Rank
from let_it_ride.core.hand_analysis import HandAnalysis


class Decision(Enum):
    """Betting decision for pull/ride choices.

    PULL: Take the bet back (not confident in the hand)
    RIDE: Let the bet ride (confident in the hand)
    """

    PULL = "pull"
    RIDE = "ride"


@dataclass(frozen=True)
class StrategyContext:
    """Context available to strategy implementations for decision making.

    This context provides session state information that advanced strategies
    may use for bankroll-based or streak-based decision adjustments.

    Attributes:
        session_profit: Current session profit/loss (positive = profit).
        hands_played: Number of hands played this session.
        streak: Current win/loss streak. Positive = consecutive wins,
            negative = consecutive losses.
        bankroll: Current bankroll amount.
        deck_composition: For composition-dependent strategies, a dict mapping
            Rank to remaining count. None if not tracking composition.
    """

    session_profit: float
    hands_played: int
    streak: int
    bankroll: float
    deck_composition: dict[Rank, int] | None = None


class Strategy(Protocol):
    """Protocol defining the interface for all strategy implementations.

    A strategy makes pull/ride decisions at two points in the game:
    - Bet 1: After seeing the player's initial 3 cards
    - Bet 2: After seeing 3 player cards + 1 community card (4 total)

    Strategy implementations do not need to inherit from this protocol;
    they just need to implement the required methods.
    """

    def decide_bet1(self, analysis: HandAnalysis, context: StrategyContext) -> Decision:
        """Decide whether to pull or ride Bet 1 (3-card decision).

        Args:
            analysis: Analysis of the player's 3-card hand.
            context: Session context (profit, streak, bankroll, etc.).

        Returns:
            Decision.RIDE to let the bet ride, Decision.PULL to take it back.
        """
        ...

    def decide_bet2(self, analysis: HandAnalysis, context: StrategyContext) -> Decision:
        """Decide whether to pull or ride Bet 2 (4-card decision).

        Args:
            analysis: Analysis of the 4-card hand (3 player + 1 community).
            context: Session context (profit, streak, bankroll, etc.).

        Returns:
            Decision.RIDE to let the bet ride, Decision.PULL to take it back.
        """
        ...
