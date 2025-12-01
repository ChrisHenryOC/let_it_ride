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


# Pre-computed for straight detection: valid 3-card straight patterns
# Each tuple is (low_value, mid_value, high_value)
# Ace can be low (1) in A-2-3 or high (14) in Q-K-A
_WHEEL_VALUES = (2, 3, 14)  # A-2-3 where Ace is low
_BROADWAY_VALUES = (12, 13, 14)  # Q-K-A (Mini Royal if suited)


def _is_three_card_straight(sorted_values: list[int]) -> bool:
    """Check if three sorted rank values form a valid straight.

    Valid straights:
    - A-2-3 (wheel): Ace plays low
    - Any 3 consecutive values: 2-3-4, 3-4-5, ..., Q-K-A

    Invalid:
    - K-A-2 (no wraparound allowed)

    Args:
        sorted_values: Three rank values sorted in ascending order.

    Returns:
        True if the values form a valid 3-card straight.
    """
    # Check for wheel (A-2-3): values would be [2, 3, 14]
    if tuple(sorted_values) == _WHEEL_VALUES:
        return True

    # Check for regular consecutive values (including Q-K-A)
    return (
        sorted_values[2] - sorted_values[0] == 2
        and sorted_values[1] - sorted_values[0] == 1
    )


def _is_mini_royal(sorted_values: list[int]) -> bool:
    """Check if the hand is specifically AKQ (Mini Royal pattern).

    Args:
        sorted_values: Three rank values sorted in ascending order.

    Returns:
        True if the values are Q-K-A (12, 13, 14).
    """
    return tuple(sorted_values) == _BROADWAY_VALUES


def evaluate_three_card_hand(cards: Sequence[Card]) -> ThreeCardHandRank:
    """Evaluate a three-card poker hand for bonus bet.

    Args:
        cards: Exactly 3 Card objects.

    Returns:
        ThreeCardHandRank indicating the hand type.

    Raises:
        ValueError: If not exactly 3 cards provided or duplicate cards detected.
    """
    if len(cards) != 3:
        raise ValueError(f"Expected 3 cards, got {len(cards)}")

    # Validate no duplicate cards
    unique_cards = {(c.rank, c.suit) for c in cards}
    if len(unique_cards) != 3:
        raise ValueError("Duplicate cards detected in hand")

    # Extract rank values and suits for processing
    rank_values = [card.rank.value for card in cards]
    suits = [card.suit for card in cards]

    # Build rank frequency
    rank_counts: dict[int, int] = {}
    for v in rank_values:
        rank_counts[v] = rank_counts.get(v, 0) + 1

    unique_ranks = len(rank_counts)

    # Check for flush (all same suit)
    first_suit = suits[0]
    is_flush = suits[1] == first_suit and suits[2] == first_suit

    # Check for straight
    sorted_values = sorted(rank_values)
    is_straight = unique_ranks == 3 and _is_three_card_straight(sorted_values)

    # Determine hand rank
    if is_flush and is_straight:
        if _is_mini_royal(sorted_values):
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
