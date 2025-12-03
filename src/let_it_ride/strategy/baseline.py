"""Baseline strategies for variance analysis.

This module provides two extreme strategies that serve as variance bounds
for strategy comparison:
- AlwaysRideStrategy: Maximum variance (never pulls, all 3 bets ride)
- AlwaysPullStrategy: Minimum variance (always pulls, only mandatory bet 3 remains)
"""

from let_it_ride.core.hand_analysis import HandAnalysis
from let_it_ride.strategy.base import Decision, StrategyContext


class AlwaysRideStrategy:
    """Maximum variance baseline strategy - always lets bets ride.

    This strategy never pulls any bets, meaning all three bets remain
    on the table for every hand. This maximizes both potential wins
    and potential losses, creating maximum variance.

    Use this as an upper bound for variance comparison.
    """

    def decide_bet1(
        self,
        analysis: HandAnalysis,  # noqa: ARG002
        context: StrategyContext,  # noqa: ARG002
    ) -> Decision:
        """Always ride Bet 1."""
        return Decision.RIDE

    def decide_bet2(
        self,
        analysis: HandAnalysis,  # noqa: ARG002
        context: StrategyContext,  # noqa: ARG002
    ) -> Decision:
        """Always ride Bet 2."""
        return Decision.RIDE


class AlwaysPullStrategy:
    """Minimum variance baseline strategy - always pulls bets.

    This strategy always pulls Bet 1 and Bet 2, leaving only the
    mandatory Bet 3 on the table. This minimizes both potential
    wins and potential losses, creating minimum variance.

    Use this as a lower bound for variance comparison.
    """

    def decide_bet1(
        self,
        analysis: HandAnalysis,  # noqa: ARG002
        context: StrategyContext,  # noqa: ARG002
    ) -> Decision:
        """Always pull Bet 1."""
        return Decision.PULL

    def decide_bet2(
        self,
        analysis: HandAnalysis,  # noqa: ARG002
        context: StrategyContext,  # noqa: ARG002
    ) -> Decision:
        """Always pull Bet 2."""
        return Decision.PULL
