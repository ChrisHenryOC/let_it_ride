"""Test fixtures for three-card hand evaluation (bonus bet).

This module provides sample hands for testing the three-card hand evaluator,
covering all 7 hand ranks with multiple examples including edge cases.
"""

from let_it_ride.core.card import Card, Rank, Suit
from let_it_ride.core.three_card_evaluator import ThreeCardHandRank

# Helper to create cards concisely: "Ah" -> Ace of Hearts
_RANK_MAP = {
    "2": Rank.TWO,
    "3": Rank.THREE,
    "4": Rank.FOUR,
    "5": Rank.FIVE,
    "6": Rank.SIX,
    "7": Rank.SEVEN,
    "8": Rank.EIGHT,
    "9": Rank.NINE,
    "T": Rank.TEN,
    "J": Rank.JACK,
    "Q": Rank.QUEEN,
    "K": Rank.KING,
    "A": Rank.ACE,
}

_SUIT_MAP = {
    "c": Suit.CLUBS,
    "d": Suit.DIAMONDS,
    "h": Suit.HEARTS,
    "s": Suit.SPADES,
}


def make_card(notation: str) -> Card:
    """Create a Card from notation like 'Ah' (Ace of Hearts)."""
    rank = _RANK_MAP[notation[0]]
    suit = _SUIT_MAP[notation[1]]
    return Card(rank, suit)


def make_three_card_hand(notations: str) -> list[Card]:
    """Create a 3-card hand from space-separated notation like 'Ah Kh Qh'."""
    return [make_card(n) for n in notations.split()]


# ============================================================================
# MINI ROYAL samples (AKQ suited only)
# ============================================================================
MINI_ROYAL_SAMPLES = [
    (make_three_card_hand("Ah Kh Qh"), ThreeCardHandRank.MINI_ROYAL),
    (make_three_card_hand("As Ks Qs"), ThreeCardHandRank.MINI_ROYAL),
    (make_three_card_hand("Ad Kd Qd"), ThreeCardHandRank.MINI_ROYAL),
    (make_three_card_hand("Ac Kc Qc"), ThreeCardHandRank.MINI_ROYAL),
]

# ============================================================================
# STRAIGHT FLUSH samples (3 consecutive suited, NOT AKQ)
# ============================================================================
STRAIGHT_FLUSH_SAMPLES = [
    # KQJ suited
    (make_three_card_hand("Kh Qh Jh"), ThreeCardHandRank.STRAIGHT_FLUSH),
    # QJT suited
    (make_three_card_hand("Qs Js Ts"), ThreeCardHandRank.STRAIGHT_FLUSH),
    # Wheel suited (A-2-3)
    (make_three_card_hand("Ah 2h 3h"), ThreeCardHandRank.STRAIGHT_FLUSH),
    (make_three_card_hand("3d 2d Ad"), ThreeCardHandRank.STRAIGHT_FLUSH),
    # Low straight flush
    (make_three_card_hand("4c 3c 2c"), ThreeCardHandRank.STRAIGHT_FLUSH),
    # Mid straight flush
    (make_three_card_hand("8h 7h 6h"), ThreeCardHandRank.STRAIGHT_FLUSH),
    # JT9 suited
    (make_three_card_hand("Jd Td 9d"), ThreeCardHandRank.STRAIGHT_FLUSH),
]

# ============================================================================
# THREE OF A KIND samples
# ============================================================================
THREE_OF_A_KIND_SAMPLES = [
    # Trip Aces
    (make_three_card_hand("Ah As Ad"), ThreeCardHandRank.THREE_OF_A_KIND),
    # Trip Kings
    (make_three_card_hand("Kh Ks Kd"), ThreeCardHandRank.THREE_OF_A_KIND),
    # Trip Twos
    (make_three_card_hand("2h 2s 2d"), ThreeCardHandRank.THREE_OF_A_KIND),
    # Trip Sevens
    (make_three_card_hand("7c 7h 7s"), ThreeCardHandRank.THREE_OF_A_KIND),
]

# ============================================================================
# STRAIGHT samples (3 consecutive, not suited)
# ============================================================================
STRAIGHT_SAMPLES = [
    # Broadway (AKQ offsuit)
    (make_three_card_hand("Ah Ks Qd"), ThreeCardHandRank.STRAIGHT),
    # KQJ offsuit
    (make_three_card_hand("Kh Qs Jd"), ThreeCardHandRank.STRAIGHT),
    # Wheel (A-2-3 offsuit)
    (make_three_card_hand("Ah 2s 3d"), ThreeCardHandRank.STRAIGHT),
    (make_three_card_hand("3c 2h As"), ThreeCardHandRank.STRAIGHT),
    # Low straight
    (make_three_card_hand("4h 3s 2d"), ThreeCardHandRank.STRAIGHT),
    # Mid straight
    (make_three_card_hand("8h 7s 6d"), ThreeCardHandRank.STRAIGHT),
    # High straight
    (make_three_card_hand("Jh Ts 9d"), ThreeCardHandRank.STRAIGHT),
]

# ============================================================================
# FLUSH samples (3 same suit, not straight)
# ============================================================================
FLUSH_SAMPLES = [
    # Ace-high flush (not straight)
    (make_three_card_hand("Ah Kh 9h"), ThreeCardHandRank.FLUSH),
    # King-high flush
    (make_three_card_hand("Ks Js 4s"), ThreeCardHandRank.FLUSH),
    # Low flush
    (make_three_card_hand("7d 5d 2d"), ThreeCardHandRank.FLUSH),
    # Queen-high flush
    (make_three_card_hand("Qc 8c 3c"), ThreeCardHandRank.FLUSH),
]

# ============================================================================
# PAIR samples
# ============================================================================
PAIR_SAMPLES = [
    # Pair of Aces
    (make_three_card_hand("Ah As Kd"), ThreeCardHandRank.PAIR),
    # Pair of Kings
    (make_three_card_hand("Kh Ks Qd"), ThreeCardHandRank.PAIR),
    # Pair of Twos
    (make_three_card_hand("2h 2s Ad"), ThreeCardHandRank.PAIR),
    # Pair of Sevens
    (make_three_card_hand("7h 7s 9d"), ThreeCardHandRank.PAIR),
    # Pair of Queens
    (make_three_card_hand("Qh Qs 5d"), ThreeCardHandRank.PAIR),
]

# ============================================================================
# HIGH CARD samples (no made hand)
# ============================================================================
HIGH_CARD_SAMPLES = [
    # Ace-high (not flush, not straight)
    (make_three_card_hand("Ah Ks 9d"), ThreeCardHandRank.HIGH_CARD),
    # King-high
    (make_three_card_hand("Kh Js 5d"), ThreeCardHandRank.HIGH_CARD),
    # Queen-high
    (make_three_card_hand("Qh 9s 4d"), ThreeCardHandRank.HIGH_CARD),
    # Seven-high (lowest possible)
    (make_three_card_hand("7h 5s 2d"), ThreeCardHandRank.HIGH_CARD),
]

# ============================================================================
# EDGE CASES - invalid straights
# ============================================================================
INVALID_STRAIGHT_SAMPLES = [
    # K-A-2 is NOT a straight (no wraparound)
    (make_three_card_hand("Kh As 2d"), ThreeCardHandRank.HIGH_CARD),
    # Q-K-2 is NOT a straight
    (make_three_card_hand("Qh Ks 2d"), ThreeCardHandRank.HIGH_CARD),
    # Gap in the middle
    (make_three_card_hand("Ah 3s 5d"), ThreeCardHandRank.HIGH_CARD),
]

# ============================================================================
# ALL SAMPLES combined for iteration
# ============================================================================
ALL_THREE_CARD_SAMPLES = (
    MINI_ROYAL_SAMPLES
    + STRAIGHT_FLUSH_SAMPLES
    + THREE_OF_A_KIND_SAMPLES
    + STRAIGHT_SAMPLES
    + FLUSH_SAMPLES
    + PAIR_SAMPLES
    + HIGH_CARD_SAMPLES
    + INVALID_STRAIGHT_SAMPLES
)
