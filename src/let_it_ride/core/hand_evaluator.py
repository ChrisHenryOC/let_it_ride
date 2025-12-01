"""Five-card poker hand evaluation for Let It Ride.

This module provides hand evaluation for the main game payouts, correctly
identifying all poker hand types from Royal Flush through High Card.

Let It Ride specific: Pairs are distinguished between PAIR_TENS_OR_BETTER
(which pays 1:1) and PAIR_BELOW_TENS (which loses).
"""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum

from let_it_ride.core.card import Card, Rank


class FiveCardHandRank(Enum):
    """Five-card poker hand rankings for Let It Ride.

    Values are ordered from highest (10) to lowest (0) for comparison.
    PAIR_TENS_OR_BETTER and PAIR_BELOW_TENS are distinguished because
    only 10s or better pay in Let It Ride.
    """

    ROYAL_FLUSH = 10
    STRAIGHT_FLUSH = 9
    FOUR_OF_A_KIND = 8
    FULL_HOUSE = 7
    FLUSH = 6
    STRAIGHT = 5
    THREE_OF_A_KIND = 4
    TWO_PAIR = 3
    PAIR_TENS_OR_BETTER = 2
    PAIR_BELOW_TENS = 1
    HIGH_CARD = 0

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, FiveCardHandRank):
            return NotImplemented
        return self.value < other.value

    def __le__(self, other: object) -> bool:
        if not isinstance(other, FiveCardHandRank):
            return NotImplemented
        return self.value <= other.value

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, FiveCardHandRank):
            return NotImplemented
        return self.value > other.value

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, FiveCardHandRank):
            return NotImplemented
        return self.value >= other.value


@dataclass(frozen=True)
class HandResult:
    """Result of evaluating a five-card poker hand.

    Attributes:
        rank: The hand ranking (e.g., FLUSH, TWO_PAIR).
        primary_cards: Ranks that define the hand, in order of importance.
            For example, a full house with three Kings and two Fives would
            have primary_cards=(Rank.KING, Rank.FIVE).
        kickers: Remaining card ranks for tiebreaking, sorted high to low.
    """

    rank: FiveCardHandRank
    primary_cards: tuple[Rank, ...]
    kickers: tuple[Rank, ...]

    def __lt__(self, other: object) -> bool:
        """Compare hands for ordering (lower is worse)."""
        if not isinstance(other, HandResult):
            return NotImplemented
        if self.rank != other.rank:
            return self.rank < other.rank
        if self.primary_cards != other.primary_cards:
            return self.primary_cards < other.primary_cards
        return self.kickers < other.kickers

    def __le__(self, other: object) -> bool:
        if not isinstance(other, HandResult):
            return NotImplemented
        return self == other or self < other

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, HandResult):
            return NotImplemented
        return other < self

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, HandResult):
            return NotImplemented
        return self == other or self > other


# Pre-computed for performance: ranks that qualify for PAIR_TENS_OR_BETTER
# Using rank values (10-14) for faster lookup
_TENS_OR_BETTER_VALUES = frozenset({10, 11, 12, 13, 14})

# Pre-computed wheel pattern for straight detection
_WHEEL_VALUES = (2, 3, 4, 5, 14)

# Rank value to Rank enum lookup for performance
_VALUE_TO_RANK: dict[int, Rank] = {r.value: r for r in Rank}


def evaluate_five_card_hand(cards: Sequence[Card]) -> HandResult:
    """Evaluate a five-card poker hand.

    Args:
        cards: Exactly 5 Card objects.

    Returns:
        HandResult with rank, primary_cards, and kickers.

    Raises:
        ValueError: If not exactly 5 cards provided.
    """
    if len(cards) != 5:
        raise ValueError(f"Expected 5 cards, got {len(cards)}")

    # Extract rank values and suits for faster processing
    rank_values = [card.rank.value for card in cards]
    suits = [card.suit for card in cards]

    # Build rank frequency using a simple dict (faster than Counter for small inputs)
    rank_counts: dict[int, int] = {}
    for v in rank_values:
        rank_counts[v] = rank_counts.get(v, 0) + 1

    # Check for flush (all same suit)
    first_suit = suits[0]
    is_flush = all(s == first_suit for s in suits[1:])

    # Check for straight
    sorted_values = sorted(rank_values)
    unique_count = len(rank_counts)

    is_straight = False
    straight_high_value: int | None = None

    if unique_count == 5:
        # Regular straight: 5 consecutive values
        if sorted_values[4] - sorted_values[0] == 4:
            is_straight = True
            straight_high_value = sorted_values[4]
        # Wheel (A-2-3-4-5): values are [2, 3, 4, 5, 14]
        elif tuple(sorted_values) == _WHEEL_VALUES:
            is_straight = True
            straight_high_value = 5  # 5 is high in wheel

    # Get ranks sorted by (count descending, value descending)
    sorted_rank_values = sorted(
        rank_counts.keys(), key=lambda v: (rank_counts[v], v), reverse=True
    )

    # Determine hand rank based on pattern
    if is_straight and is_flush:
        # Royal flush: A-K-Q-J-10 suited
        if straight_high_value == 14:
            return HandResult(
                rank=FiveCardHandRank.ROYAL_FLUSH,
                primary_cards=(Rank.ACE,),
                kickers=(),
            )
        # Straight flush (includes steel wheel)
        # straight_high_value is guaranteed to be non-None here
        assert straight_high_value is not None
        return HandResult(
            rank=FiveCardHandRank.STRAIGHT_FLUSH,
            primary_cards=(_VALUE_TO_RANK[straight_high_value],),
            kickers=(),
        )

    # Get max count for pattern detection
    max_count = rank_counts[sorted_rank_values[0]]

    if max_count == 4:
        # Four of a kind
        quad_rank = _VALUE_TO_RANK[sorted_rank_values[0]]
        kicker = _VALUE_TO_RANK[sorted_rank_values[1]]
        return HandResult(
            rank=FiveCardHandRank.FOUR_OF_A_KIND,
            primary_cards=(quad_rank,),
            kickers=(kicker,),
        )

    if max_count == 3:
        if unique_count == 2:
            # Full house (3 + 2)
            trips_rank = _VALUE_TO_RANK[sorted_rank_values[0]]
            pair_rank = _VALUE_TO_RANK[sorted_rank_values[1]]
            return HandResult(
                rank=FiveCardHandRank.FULL_HOUSE,
                primary_cards=(trips_rank, pair_rank),
                kickers=(),
            )
        # Three of a kind (3 + 1 + 1)
        trips_rank = _VALUE_TO_RANK[sorted_rank_values[0]]
        kicker_values = sorted(sorted_rank_values[1:], reverse=True)
        kickers = tuple(_VALUE_TO_RANK[v] for v in kicker_values)
        return HandResult(
            rank=FiveCardHandRank.THREE_OF_A_KIND,
            primary_cards=(trips_rank,),
            kickers=kickers,
        )

    if is_flush:
        # Flush (non-straight)
        sorted_by_rank = tuple(
            _VALUE_TO_RANK[v] for v in sorted(rank_values, reverse=True)
        )
        return HandResult(
            rank=FiveCardHandRank.FLUSH,
            primary_cards=sorted_by_rank,
            kickers=(),
        )

    if is_straight:
        # Straight (non-flush)
        # straight_high_value is guaranteed to be non-None when is_straight is True
        assert straight_high_value is not None
        return HandResult(
            rank=FiveCardHandRank.STRAIGHT,
            primary_cards=(_VALUE_TO_RANK[straight_high_value],),
            kickers=(),
        )

    if max_count == 2:
        if unique_count == 3:
            # Two pair (2 + 2 + 1)
            high_pair_val = max(sorted_rank_values[0], sorted_rank_values[1])
            low_pair_val = min(sorted_rank_values[0], sorted_rank_values[1])
            kicker = _VALUE_TO_RANK[sorted_rank_values[2]]
            return HandResult(
                rank=FiveCardHandRank.TWO_PAIR,
                primary_cards=(
                    _VALUE_TO_RANK[high_pair_val],
                    _VALUE_TO_RANK[low_pair_val],
                ),
                kickers=(kicker,),
            )
        # One pair (2 + 1 + 1 + 1)
        pair_value = sorted_rank_values[0]
        pair_rank = _VALUE_TO_RANK[pair_value]
        kicker_values = sorted(sorted_rank_values[1:], reverse=True)
        kickers = tuple(_VALUE_TO_RANK[v] for v in kicker_values)

        if pair_value in _TENS_OR_BETTER_VALUES:
            return HandResult(
                rank=FiveCardHandRank.PAIR_TENS_OR_BETTER,
                primary_cards=(pair_rank,),
                kickers=kickers,
            )
        return HandResult(
            rank=FiveCardHandRank.PAIR_BELOW_TENS,
            primary_cards=(pair_rank,),
            kickers=kickers,
        )

    # High card (unique_count == 5, no straight, no flush)
    sorted_by_rank = tuple(_VALUE_TO_RANK[v] for v in sorted(rank_values, reverse=True))
    return HandResult(
        rank=FiveCardHandRank.HIGH_CARD,
        primary_cards=sorted_by_rank[:1],
        kickers=sorted_by_rank[1:],
    )
