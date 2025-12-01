"""Paytable configuration for Let It Ride.

This module provides configurable paytables for both the main game and
three-card bonus bet, including payout calculation and validation.
"""

from dataclasses import dataclass
from functools import cache

from let_it_ride.core.hand_evaluator import FiveCardHandRank
from let_it_ride.core.three_card_evaluator import ThreeCardHandRank


class PaytableValidationError(Exception):
    """Raised when a paytable fails validation."""


@dataclass(frozen=True)
class MainGamePaytable:
    """Paytable for the main Let It Ride game (5-card hands).

    Attributes:
        name: Identifier for this paytable variant.
        payouts: Mapping from FiveCardHandRank to payout ratio (multiplier).
            A ratio of N means the player wins N times their bet.
            A ratio of 0 means the player loses their bet.
    """

    name: str
    payouts: dict[FiveCardHandRank, int]

    def calculate_payout(self, rank: FiveCardHandRank, bet: float) -> float:
        """Calculate payout for a hand rank.

        Args:
            rank: The evaluated hand rank.
            bet: The bet amount.

        Returns:
            The payout amount (bet * ratio). Returns 0.0 for losing hands.
            This is pure profit - the original bet is not included.
        """
        ratio = self.payouts[rank]
        return bet * ratio

    def validate(self) -> None:
        """Validate that this paytable is complete and valid.

        Raises:
            PaytableValidationError: If validation fails.
        """
        # Check all hand ranks are covered
        missing = set(FiveCardHandRank) - set(self.payouts.keys())
        if missing:
            rank_names = ", ".join(r.name for r in missing)
            raise PaytableValidationError(
                f"Paytable '{self.name}' missing ranks: {rank_names}"
            )

        # Check no negative payouts
        for rank, payout in self.payouts.items():
            if payout < 0:
                raise PaytableValidationError(
                    f"Paytable '{self.name}' has negative payout for {rank.name}: {payout}"
                )


@dataclass(frozen=True)
class BonusPaytable:
    """Paytable for the Three Card Bonus side bet.

    Attributes:
        name: Identifier for this paytable variant.
        payouts: Mapping from ThreeCardHandRank to payout ratio (multiplier).
            A ratio of N means the player wins N times their bet.
            A ratio of 0 means the player loses their bet.
    """

    name: str
    payouts: dict[ThreeCardHandRank, int]

    def calculate_payout(self, rank: ThreeCardHandRank, bet: float) -> float:
        """Calculate payout for a three-card hand rank.

        Args:
            rank: The evaluated three-card hand rank.
            bet: The bet amount.

        Returns:
            The payout amount (bet * ratio). Returns 0.0 for losing hands.
            This is pure profit - the original bet is not included.
        """
        ratio = self.payouts[rank]
        return bet * ratio

    def validate(self) -> None:
        """Validate that this paytable is complete and valid.

        Raises:
            PaytableValidationError: If validation fails.
        """
        # Check all hand ranks are covered
        missing = set(ThreeCardHandRank) - set(self.payouts.keys())
        if missing:
            rank_names = ", ".join(r.name for r in missing)
            raise PaytableValidationError(
                f"Paytable '{self.name}' missing ranks: {rank_names}"
            )

        # Check no negative payouts
        for rank, payout in self.payouts.items():
            if payout < 0:
                raise PaytableValidationError(
                    f"Paytable '{self.name}' has negative payout for {rank.name}: {payout}"
                )


@cache
def standard_main_paytable() -> MainGamePaytable:
    """Create the standard main game paytable.

    Returns:
        MainGamePaytable with standard casino payouts:
        - Royal Flush: 1000:1
        - Straight Flush: 200:1
        - Four of a Kind: 50:1
        - Full House: 11:1
        - Flush: 8:1
        - Straight: 5:1
        - Three of a Kind: 3:1
        - Two Pair: 2:1
        - Pair of 10s+: 1:1
        - All other: 0 (loss)
    """
    return MainGamePaytable(
        name="standard",
        payouts={
            FiveCardHandRank.ROYAL_FLUSH: 1000,
            FiveCardHandRank.STRAIGHT_FLUSH: 200,
            FiveCardHandRank.FOUR_OF_A_KIND: 50,
            FiveCardHandRank.FULL_HOUSE: 11,
            FiveCardHandRank.FLUSH: 8,
            FiveCardHandRank.STRAIGHT: 5,
            FiveCardHandRank.THREE_OF_A_KIND: 3,
            FiveCardHandRank.TWO_PAIR: 2,
            FiveCardHandRank.PAIR_TENS_OR_BETTER: 1,
            FiveCardHandRank.PAIR_BELOW_TENS: 0,
            FiveCardHandRank.HIGH_CARD: 0,
        },
    )


@cache
def bonus_paytable_a() -> BonusPaytable:
    """Create bonus paytable variant A (lower volatility).

    This paytable has lower variance with a smaller Mini Royal payout
    but slightly better odds on straights. House edge ~2.4%.

    Returns:
        BonusPaytable with variant A payouts:
        - Mini Royal: 50:1
        - Straight Flush: 40:1
        - Three of a Kind: 30:1
        - Straight: 6:1
        - Flush: 3:1
        - Pair: 1:1
        - High Card: 0 (loss)
    """
    return BonusPaytable(
        name="paytable_a",
        payouts={
            ThreeCardHandRank.MINI_ROYAL: 50,
            ThreeCardHandRank.STRAIGHT_FLUSH: 40,
            ThreeCardHandRank.THREE_OF_A_KIND: 30,
            ThreeCardHandRank.STRAIGHT: 6,
            ThreeCardHandRank.FLUSH: 3,
            ThreeCardHandRank.PAIR: 1,
            ThreeCardHandRank.HIGH_CARD: 0,
        },
    )


@cache
def bonus_paytable_b() -> BonusPaytable:
    """Create bonus paytable variant B (default).

    This is the most common bonus paytable found in casinos.
    House edge ~3.5%.

    Returns:
        BonusPaytable with variant B payouts:
        - Mini Royal: 100:1
        - Straight Flush: 40:1
        - Three of a Kind: 30:1
        - Straight: 5:1
        - Flush: 4:1
        - Pair: 1:1
        - High Card: 0 (loss)
    """
    return BonusPaytable(
        name="paytable_b",
        payouts={
            ThreeCardHandRank.MINI_ROYAL: 100,
            ThreeCardHandRank.STRAIGHT_FLUSH: 40,
            ThreeCardHandRank.THREE_OF_A_KIND: 30,
            ThreeCardHandRank.STRAIGHT: 5,
            ThreeCardHandRank.FLUSH: 4,
            ThreeCardHandRank.PAIR: 1,
            ThreeCardHandRank.HIGH_CARD: 0,
        },
    )


@cache
def bonus_paytable_c(progressive_payout: int = 1000) -> BonusPaytable:
    """Create bonus paytable variant C (progressive).

    This paytable features a progressive jackpot for Mini Royal
    and higher straight flush payouts. House edge varies based
    on jackpot size.

    Args:
        progressive_payout: The payout ratio for Mini Royal.
            In a real progressive, this would be the jackpot value
            divided by the bet amount. Default is 1000:1.

    Returns:
        BonusPaytable with variant C payouts:
        - Mini Royal: progressive_payout:1
        - Straight Flush: 200:1
        - Three of a Kind: 30:1
        - Straight: 6:1
        - Flush: 4:1
        - Pair: 1:1
        - High Card: 0 (loss)
    """
    return BonusPaytable(
        name="paytable_c",
        payouts={
            ThreeCardHandRank.MINI_ROYAL: progressive_payout,
            ThreeCardHandRank.STRAIGHT_FLUSH: 200,
            ThreeCardHandRank.THREE_OF_A_KIND: 30,
            ThreeCardHandRank.STRAIGHT: 6,
            ThreeCardHandRank.FLUSH: 4,
            ThreeCardHandRank.PAIR: 1,
            ThreeCardHandRank.HIGH_CARD: 0,
        },
    )
