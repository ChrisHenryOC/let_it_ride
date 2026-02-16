"""Progressive jackpot side bet for Let It Ride.

This module implements the 5-card progressive jackpot side bet, which is
evaluated on the final 5-card hand (unlike the 3-card bonus). The jackpot
pool grows with each bet and resets (partially or fully) when hit.

Key types:
- ProgressivePayout: A single payout rule (fixed dollar or percentage of jackpot)
- ProgressivePaytable: Maps FiveCardHandRank to ProgressivePayout entries
- ProgressiveJackpot: Manages the mutable jackpot pool state
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from let_it_ride.core.hand_evaluator import FiveCardHandRank

if TYPE_CHECKING:
    from let_it_ride.config.models import ProgressiveSideBetConfig


@dataclass(frozen=True, slots=True)
class ProgressivePayout:
    """A single payout rule: either fixed dollar or percentage of jackpot.

    Attributes:
        type: "fixed" for a dollar amount, "jackpot_percentage" for pool fraction.
        value: The payout value (dollars for fixed, 0-1 fraction for percentage).
    """

    type: Literal["fixed", "jackpot_percentage"]
    value: float


@dataclass(frozen=True, slots=True)
class ProgressivePaytable:
    """Maps FiveCardHandRank to ProgressivePayout entries.

    Attributes:
        name: Descriptive name for this paytable.
        payouts: Mapping of hand ranks to payout rules.
    """

    name: str
    payouts: dict[FiveCardHandRank, ProgressivePayout]


class ProgressiveJackpot:
    """Manages the progressive jackpot pool.

    The pool grows with each bet (contribution_rate * bet_amount) and pays
    out based on the final 5-card hand. Fixed-dollar payouts do not affect
    the pool. Percentage payouts deduct the paid fraction from the pool.
    A full jackpot hit (value >= 1.0) resets the pool to the seed amount
    if reset_to_seed is True; otherwise the pool drops to zero.
    """

    __slots__ = (
        "_pool",
        "_seed_amount",
        "_contribution_rate",
        "_reset_to_seed",
        "_paytable",
    )

    def __init__(
        self,
        seed_amount: float,
        starting_pool: float,
        contribution_rate: float,
        paytable: ProgressivePaytable,
        reset_to_seed: bool = True,
    ) -> None:
        """Initialize the progressive jackpot.

        Args:
            seed_amount: Base amount the jackpot resets to after being hit.
            starting_pool: Initial pool value at session start.
            contribution_rate: Fraction of each bet added to the pool (0-1).
            paytable: Paytable mapping hand ranks to payouts.
            reset_to_seed: If True, reset pool to seed_amount after 100% hit.
        """
        self._pool = starting_pool
        self._seed_amount = seed_amount
        self._contribution_rate = contribution_rate
        self._reset_to_seed = reset_to_seed
        self._paytable = paytable

    @property
    def current_pool(self) -> float:
        """Return the current jackpot pool value."""
        return self._pool

    def contribute(self, bet_amount: float) -> None:
        """Add a contribution to the jackpot pool.

        Args:
            bet_amount: The bet amount placed by the player.

        Raises:
            ValueError: If bet_amount is negative.
        """
        if bet_amount < 0:
            raise ValueError(f"bet_amount must be non-negative, got {bet_amount}")
        self._pool += self._contribution_rate * bet_amount

    def evaluate_payout(self, hand_rank: FiveCardHandRank) -> float:
        """Evaluate the payout for a given hand rank.

        If the hand qualifies for a payout, computes the amount and adjusts
        the pool accordingly. For jackpot_percentage payouts, the payout
        fraction is deducted from the pool. If the entire jackpot is hit
        (100%) and reset_to_seed is True, the pool resets to seed_amount.

        Args:
            hand_rank: The evaluated 5-card hand rank.

        Returns:
            The payout amount (0.0 if hand doesn't qualify).
        """
        payout_rule = self._paytable.payouts.get(hand_rank)
        if payout_rule is None:
            return 0.0

        if payout_rule.type == "fixed":
            return payout_rule.value

        # jackpot_percentage
        payout_amount = self._pool * payout_rule.value
        self._pool -= payout_amount

        # Reset to seed if full jackpot was hit
        if payout_rule.value >= 1.0 and self._reset_to_seed:
            self._pool = self._seed_amount

        return payout_amount

    def reset(self) -> None:
        """Reset the pool to the seed amount."""
        self._pool = self._seed_amount


# Module-level cached paytable (immutable, safe to share across sessions)
_STANDARD_PROGRESSIVE_PAYTABLE = ProgressivePaytable(
    name="standard_progressive",
    payouts={
        FiveCardHandRank.ROYAL_FLUSH: ProgressivePayout(
            type="jackpot_percentage", value=1.0
        ),
        FiveCardHandRank.STRAIGHT_FLUSH: ProgressivePayout(
            type="jackpot_percentage", value=0.10
        ),
        FiveCardHandRank.FOUR_OF_A_KIND: ProgressivePayout(type="fixed", value=500.0),
        FiveCardHandRank.FULL_HOUSE: ProgressivePayout(type="fixed", value=100.0),
        FiveCardHandRank.FLUSH: ProgressivePayout(type="fixed", value=75.0),
        FiveCardHandRank.STRAIGHT: ProgressivePayout(type="fixed", value=50.0),
    },
)


def standard_progressive_paytable() -> ProgressivePaytable:
    """Return the standard progressive jackpot paytable.

    Standard payouts:
        Royal Flush:     100% of jackpot
        Straight Flush:  10% of jackpot
        Four of a Kind:  $500 fixed
        Full House:      $100 fixed
        Flush:           $75 fixed
        Straight:        $50 fixed

    Returns:
        A ProgressivePaytable with standard payouts (cached, immutable).
    """
    return _STANDARD_PROGRESSIVE_PAYTABLE


def create_progressive_jackpot(
    config: ProgressiveSideBetConfig,
) -> ProgressiveJackpot:
    """Create a ProgressiveJackpot from configuration.

    If the config has a custom paytable, it maps hand rank names to
    ProgressivePayout entries. Otherwise, uses the standard paytable.

    Args:
        config: Progressive side bet configuration.

    Returns:
        A configured ProgressiveJackpot instance.
    """
    if config.paytable:
        # Build paytable from config
        valid_names = [r.name for r in FiveCardHandRank]
        payouts: dict[FiveCardHandRank, ProgressivePayout] = {}
        for hand_name, entry in config.paytable.items():
            try:
                hand_rank = FiveCardHandRank[hand_name.upper()]
            except KeyError:
                raise ValueError(
                    f"Invalid hand rank name '{hand_name}'. "
                    f"Valid names: {', '.join(valid_names)}"
                ) from None
            payouts[hand_rank] = ProgressivePayout(type=entry.type, value=entry.value)
        paytable = ProgressivePaytable(name="custom_progressive", payouts=payouts)
    else:
        paytable = standard_progressive_paytable()

    return ProgressiveJackpot(
        seed_amount=config.seed_amount,
        starting_pool=config.starting_jackpot,
        contribution_rate=config.contribution_rate,
        paytable=paytable,
        reset_to_seed=config.reset_to_seed,
    )
