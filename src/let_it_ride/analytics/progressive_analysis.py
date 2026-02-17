"""Progressive jackpot expected value and breakeven analysis.

Standalone analytical module for computing progressive jackpot EV,
house edge, and breakeven jackpot amounts. No simulation needed.

Key types:
- BreakevenResult: Result of breakeven jackpot calculation
- HouseEdgeResult: Result of house edge calculation

Key functions:
- calculate_expected_payout(): Expected payout for a given jackpot amount
- calculate_breakeven_jackpot(): Jackpot size where EV equals bet amount
- calculate_house_edge(): House edge at a given jackpot level
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from let_it_ride.analytics.validation import THEORETICAL_HAND_PROBS
from let_it_ride.core.hand_evaluator import FiveCardHandRank

if TYPE_CHECKING:
    from let_it_ride.core.progressive_jackpot import ProgressivePaytable


@dataclass(frozen=True, slots=True)
class BreakevenResult:
    """Result of breakeven jackpot calculation.

    Attributes:
        breakeven_jackpot: Jackpot amount where expected payout equals bet.
        bet_amount: The bet amount used in the calculation.
        contribution_rate: The contribution rate used.
        fixed_ev: Expected value from fixed-dollar payouts alone.
        percentage_ev_coefficient: Sum of (prob * percentage) for jackpot payouts.
        paytable_name: Name of the paytable used.
    """

    breakeven_jackpot: float
    bet_amount: float
    contribution_rate: float
    fixed_ev: float
    percentage_ev_coefficient: float
    paytable_name: str


@dataclass(frozen=True, slots=True)
class HouseEdgeResult:
    """Result of house edge calculation.

    Attributes:
        jackpot_amount: The jackpot amount used in the calculation.
        bet_amount: The bet amount used.
        expected_payout: Expected payout per bet.
        house_edge: House edge as a fraction (0-1). Negative means player advantage.
        player_return: Player return as a fraction (expected_payout / bet_amount).
        contribution_rate: The contribution rate used.
    """

    jackpot_amount: float
    bet_amount: float
    expected_payout: float
    house_edge: float
    player_return: float
    contribution_rate: float


# Mapping from FiveCardHandRank to THEORETICAL_HAND_PROBS key names.
# Only ranks that appear in standard progressive paytables are included.
_RANK_TO_PROB_KEY: dict[FiveCardHandRank, str] = {
    FiveCardHandRank.ROYAL_FLUSH: "royal_flush",
    FiveCardHandRank.STRAIGHT_FLUSH: "straight_flush",
    FiveCardHandRank.FOUR_OF_A_KIND: "four_of_a_kind",
    FiveCardHandRank.FULL_HOUSE: "full_house",
    FiveCardHandRank.FLUSH: "flush",
    FiveCardHandRank.STRAIGHT: "straight",
    FiveCardHandRank.THREE_OF_A_KIND: "three_of_a_kind",
    FiveCardHandRank.TWO_PAIR: "two_pair",
}


def _hand_rank_probability(rank: FiveCardHandRank) -> float:
    """Return the theoretical probability for a five-card hand rank.

    Maps FiveCardHandRank enum values to probabilities from
    THEORETICAL_HAND_PROBS in validation.py.

    Args:
        rank: The five-card hand rank.

    Returns:
        The probability of the hand rank (0.0 if not in the mapping).
    """
    key = _RANK_TO_PROB_KEY.get(rank)
    if key is None:
        return 0.0
    return THEORETICAL_HAND_PROBS.get(key, 0.0)


def calculate_expected_payout(
    paytable: ProgressivePaytable,
    jackpot_amount: float,
) -> float:
    """Calculate the expected payout for a progressive side bet.

    Sums over all paytable entries:
    - Fixed payouts contribute: probability * fixed_value
    - Percentage payouts contribute: probability * percentage * jackpot_amount

    Args:
        paytable: The progressive paytable to evaluate.
        jackpot_amount: Current jackpot pool amount.

    Returns:
        Expected payout per bet.
    """
    expected = 0.0
    for rank, payout in paytable.payouts.items():
        prob = _hand_rank_probability(rank)
        if payout.type == "fixed":
            expected += prob * payout.value
        else:
            # jackpot_percentage
            expected += prob * payout.value * jackpot_amount
    return expected


def calculate_breakeven_jackpot(
    paytable: ProgressivePaytable,
    bet_amount: float = 1.0,
    contribution_rate: float = 0.71,
) -> BreakevenResult:
    """Calculate the jackpot amount where expected payout equals bet amount.

    Solves algebraically: J = (bet_amount - E_fixed) / E_percentage_coefficient
    where:
    - E_fixed = sum(prob * fixed_value) for fixed payouts
    - E_percentage_coefficient = sum(prob * percentage) for jackpot payouts

    Args:
        paytable: The progressive paytable to evaluate.
        bet_amount: The side bet amount (default $1).
        contribution_rate: Fraction of bet added to jackpot pool (default 0.71).

    Returns:
        BreakevenResult with the breakeven jackpot amount and components.

    Raises:
        ValueError: If paytable has no percentage-based payouts (no breakeven).
    """
    fixed_ev = 0.0
    percentage_ev_coefficient = 0.0

    for rank, payout in paytable.payouts.items():
        prob = _hand_rank_probability(rank)
        if payout.type == "fixed":
            fixed_ev += prob * payout.value
        else:
            percentage_ev_coefficient += prob * payout.value

    if percentage_ev_coefficient == 0.0:
        raise ValueError(
            "Paytable has no percentage-based payouts; breakeven jackpot is undefined"
        )

    breakeven_jackpot = (bet_amount - fixed_ev) / percentage_ev_coefficient

    return BreakevenResult(
        breakeven_jackpot=breakeven_jackpot,
        bet_amount=bet_amount,
        contribution_rate=contribution_rate,
        fixed_ev=fixed_ev,
        percentage_ev_coefficient=percentage_ev_coefficient,
        paytable_name=paytable.name,
    )


def calculate_house_edge(
    paytable: ProgressivePaytable,
    jackpot_amount: float,
    bet_amount: float = 1.0,
    contribution_rate: float = 0.71,
) -> HouseEdgeResult:
    """Calculate the house edge for a progressive side bet.

    house_edge = 1 - (expected_payout / bet_amount)

    A positive house_edge means the house has an advantage.
    A negative house_edge means the player has an advantage.

    Args:
        paytable: The progressive paytable to evaluate.
        jackpot_amount: Current jackpot pool amount.
        bet_amount: The side bet amount (default $1).
        contribution_rate: Fraction of bet added to jackpot pool (default 0.71).

    Returns:
        HouseEdgeResult with house edge and related metrics.
    """
    expected_payout = calculate_expected_payout(paytable, jackpot_amount)
    player_return = expected_payout / bet_amount if bet_amount > 0 else 0.0
    house_edge = 1.0 - player_return

    return HouseEdgeResult(
        jackpot_amount=jackpot_amount,
        bet_amount=bet_amount,
        expected_payout=expected_payout,
        house_edge=house_edge,
        player_return=player_return,
        contribution_rate=contribution_rate,
    )
