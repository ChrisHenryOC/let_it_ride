"""Three-card poker hand evaluation for Let It Ride bonus bet.

This module provides hand evaluation for the Three Card Bonus side bet,
correctly identifying all 7 hand types from Mini Royal through High Card.

The Mini Royal (AKQ suited) is distinguished from other straight flushes
because it typically has a higher payout in bonus bet paytables.
"""

from collections.abc import Sequence
from enum import Enum

from let_it_ride.core.card import Card


class ThreeCardHandRank(Enum):
    """Three-card poker hand rankings for bonus bet evaluation.

    Values are ordered from highest (7) to lowest (1) for comparison.
    MINI_ROYAL is distinguished from STRAIGHT_FLUSH because bonus paytables
    typically pay Mini Royal (AKQ suited) at a higher rate.
    """

    MINI_ROYAL = 7  # AKQ suited only
    STRAIGHT_FLUSH = 6  # Other straight flushes
    THREE_OF_A_KIND = 5
    STRAIGHT = 4
    FLUSH = 3
    PAIR = 2
    HIGH_CARD = 1

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, ThreeCardHandRank):
            return NotImplemented
        return self.value < other.value

    def __le__(self, other: object) -> bool:
        if not isinstance(other, ThreeCardHandRank):
            return NotImplemented
        return self.value <= other.value

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, ThreeCardHandRank):
            return NotImplemented
        return self.value > other.value

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, ThreeCardHandRank):
            return NotImplemented
        return self.value >= other.value


def evaluate_three_card_hand(cards: Sequence[Card]) -> ThreeCardHandRank:
    """Evaluate a three-card poker hand for bonus bet.

    Args:
        cards: Exactly 3 Card objects.

    Returns:
        ThreeCardHandRank indicating the hand type.

    Raises:
        ValueError: If not exactly 3 cards provided.
    """
    if len(cards) != 3:
        raise ValueError(f"Expected 3 cards, got {len(cards)}")

    # Direct unpacking avoids list/dict allocations on this hot path.
    # This function is called millions of times during simulation, so
    # avoiding temporary object creation improves throughput significantly.
    c0, c1, c2 = cards
    r0, r1, r2 = c0.rank.value, c1.rank.value, c2.rank.value
    s0, s1, s2 = c0.suit, c1.suit, c2.suit

    # Manual 3-element sort (sorting network) avoids sorted() allocation.
    # Three comparisons and at most three swaps to sort 3 elements in-place.
    if r0 > r1:
        r0, r1 = r1, r0
    if r1 > r2:
        r1, r2 = r2, r1
    if r0 > r1:
        r0, r1 = r1, r0
    # Now r0 <= r1 <= r2

    # Determine unique rank count directly (avoids dict allocation)
    if r0 == r1 == r2:
        unique_ranks = 1
    elif r0 == r1 or r1 == r2:
        # After sorting, r0 == r2 implies all equal (already handled above)
        unique_ranks = 2
    else:
        unique_ranks = 3

    # Check for flush (all same suit)
    is_flush = s0 == s1 == s2

    # Check for straight (only possible with 3 unique ranks)
    # Wheel (A-2-3): sorted values are [2, 3, 14]
    # Regular consecutive: r2 - r0 == 2 and r1 - r0 == 1
    is_straight = unique_ranks == 3 and (
        (r0 == 2 and r1 == 3 and r2 == 14)  # Wheel
        or (r2 - r0 == 2 and r1 - r0 == 1)  # Consecutive
    )

    # Determine hand rank
    if is_flush and is_straight:
        # Mini Royal: Q-K-A suited (12, 13, 14)
        if r0 == 12 and r1 == 13 and r2 == 14:
            return ThreeCardHandRank.MINI_ROYAL
        return ThreeCardHandRank.STRAIGHT_FLUSH

    # Three of a kind: all 3 cards same rank
    if unique_ranks == 1:
        return ThreeCardHandRank.THREE_OF_A_KIND

    if is_straight:
        return ThreeCardHandRank.STRAIGHT

    if is_flush:
        return ThreeCardHandRank.FLUSH

    # Pair: exactly 2 unique ranks means one pair
    if unique_ranks == 2:
        return ThreeCardHandRank.PAIR

    return ThreeCardHandRank.HIGH_CARD
