"""Basic strategy implementation for Let It Ride.

This module implements the mathematically optimal basic strategy for
pull/ride decisions based on published strategy charts.

Basic Strategy Reference:

Bet 1 (3 cards) - LET IT RIDE when holding:
1. Any paying hand (pair of 10s+, three of a kind)
2. Three to a Royal Flush (3 suited royals including Ace)
3. Three suited in sequence (straight flush draw) EXCEPT A-2-3, 2-3-4
4. Three to straight flush, spread 4, with 1+ high card
5. Three to straight flush, spread 5, with 2+ high cards

Bet 2 (4 cards) - LET IT RIDE when holding:
1. Any paying hand (pair 10+, trips, two pair)
2. Four to a flush
3. Four to outside straight with 1+ high card
4. Four to inside straight with 4 high cards (10-J-Q-K)
"""

from let_it_ride.core.hand_analysis import HandAnalysis
from let_it_ride.strategy.base import Decision, StrategyContext


class BasicStrategy:
    """Mathematically optimal basic strategy for Let It Ride.

    This strategy implements the optimal play decisions based on
    published basic strategy charts. It only considers the current
    hand analysis and does not use session context (bankroll, streak, etc.).
    """

    def decide_bet1(
        self,
        analysis: HandAnalysis,
        context: StrategyContext,  # noqa: ARG002
    ) -> Decision:
        """Decide whether to pull or ride Bet 1 (3-card decision).

        Let it ride on:
        1. Any paying hand (pair of 10s+, three of a kind)
        2. Three to a Royal Flush
        3. Three suited in sequence (straight flush draw) except A-2-3, 2-3-4
        4. Three to straight flush, spread 4, with 1+ high card
        5. Three to straight flush, spread 5, with 2+ high cards

        Args:
            analysis: Analysis of the player's 3-card hand.
            context: Session context (not used by basic strategy).

        Returns:
            Decision.RIDE or Decision.PULL.
        """
        # Rule 1: Any paying hand (pair 10+, trips)
        if analysis.has_paying_hand:
            return Decision.RIDE

        # Rule 2: Three to a Royal Flush
        # Royal draw requires 3 suited high cards including Ace
        if analysis.is_royal_draw:
            return Decision.RIDE

        # Rules 3-5: Three to straight flush draws
        # These require all 3 cards to be suited and form a SF draw
        if analysis.is_straight_flush_draw and analysis.suited_cards == 3:
            spread = analysis.straight_flush_spread

            # Rule 3: Three suited consecutive (spread 3)
            # Exception: A-2-3 and 2-3-4 are excluded
            if spread == 3 and not analysis.is_excluded_sf_consecutive:
                return Decision.RIDE

            # Rule 4: Three to straight flush, spread 4 (1 gap), with 1+ high card
            if spread == 4 and analysis.suited_high_cards >= 1:
                return Decision.RIDE

            # Rule 5: Three to straight flush, spread 5 (2 gaps), with 2+ high cards
            if spread == 5 and analysis.suited_high_cards >= 2:
                return Decision.RIDE

        # No ride condition met
        return Decision.PULL

    def decide_bet2(
        self,
        analysis: HandAnalysis,
        context: StrategyContext,  # noqa: ARG002
    ) -> Decision:
        """Decide whether to pull or ride Bet 2 (4-card decision).

        Let it ride on:
        1. Any paying hand (pair 10+, trips, two pair)
        2. Four to a flush
        3. Four to outside straight with 1+ high card
        4. Four to inside straight with 4 high cards (10-J-Q-K)

        Args:
            analysis: Analysis of the 4-card hand (3 player + 1 community).
            context: Session context (not used by basic strategy).

        Returns:
            Decision.RIDE or Decision.PULL.
        """
        # Rule 1: Any paying hand
        if analysis.has_paying_hand:
            return Decision.RIDE

        # Rule 2: Four to a flush
        if analysis.is_flush_draw and analysis.suited_cards >= 4:
            return Decision.RIDE

        # Rule 3: Four to outside straight with 1+ high card
        if analysis.is_open_straight_draw and analysis.high_cards >= 1:
            return Decision.RIDE

        # Rule 4: Four to inside straight with 4 high cards (10-J-Q-K)
        # This is specifically 10-J-Q-K which has exactly 4 high cards
        # and is missing the Ace (or 9) to complete
        if analysis.is_inside_straight_draw and analysis.high_cards >= 4:
            return Decision.RIDE

        # No ride condition met
        return Decision.PULL
