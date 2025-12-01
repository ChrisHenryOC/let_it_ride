"""Test fixtures for five-card hand evaluation.

This module provides sample hands for testing the hand evaluator, covering
all 10 hand ranks with multiple examples including edge cases.
"""

from let_it_ride.core.card import Card, Rank, Suit
from let_it_ride.core.hand_evaluator import FiveCardHandRank

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


def make_hand(notations: str) -> list[Card]:
    """Create a hand from space-separated notation like 'Ah Kh Qh Jh Th'."""
    return [make_card(n) for n in notations.split()]


# ============================================================================
# ROYAL FLUSH samples (A-K-Q-J-10 suited)
# ============================================================================
ROYAL_FLUSH_SAMPLES = [
    (make_hand("Ah Kh Qh Jh Th"), FiveCardHandRank.ROYAL_FLUSH, (Rank.ACE,)),
    (make_hand("As Ks Qs Js Ts"), FiveCardHandRank.ROYAL_FLUSH, (Rank.ACE,)),
    (make_hand("Ad Kd Qd Jd Td"), FiveCardHandRank.ROYAL_FLUSH, (Rank.ACE,)),
    (make_hand("Ac Kc Qc Jc Tc"), FiveCardHandRank.ROYAL_FLUSH, (Rank.ACE,)),
]

# ============================================================================
# STRAIGHT FLUSH samples (5 consecutive, same suit, not royal)
# ============================================================================
STRAIGHT_FLUSH_SAMPLES = [
    # King-high straight flush
    (make_hand("Kh Qh Jh Th 9h"), FiveCardHandRank.STRAIGHT_FLUSH, (Rank.KING,)),
    # Six-high straight flush
    (make_hand("6s 5s 4s 3s 2s"), FiveCardHandRank.STRAIGHT_FLUSH, (Rank.SIX,)),
    # Steel wheel (A-2-3-4-5 suited) - Ace is LOW, high card is 5
    (make_hand("Ah 2h 3h 4h 5h"), FiveCardHandRank.STRAIGHT_FLUSH, (Rank.FIVE,)),
    (make_hand("5d 4d 3d 2d Ad"), FiveCardHandRank.STRAIGHT_FLUSH, (Rank.FIVE,)),
    # Nine-high straight flush
    (make_hand("9c 8c 7c 6c 5c"), FiveCardHandRank.STRAIGHT_FLUSH, (Rank.NINE,)),
]

# ============================================================================
# FOUR OF A KIND samples
# ============================================================================
FOUR_OF_A_KIND_SAMPLES = [
    # Four Aces
    (make_hand("Ah As Ad Ac Kh"), FiveCardHandRank.FOUR_OF_A_KIND, (Rank.ACE,)),
    # Four Kings
    (make_hand("Kh Ks Kd Kc Qh"), FiveCardHandRank.FOUR_OF_A_KIND, (Rank.KING,)),
    # Four Twos
    (make_hand("2h 2s 2d 2c Ah"), FiveCardHandRank.FOUR_OF_A_KIND, (Rank.TWO,)),
    # Four Tens
    (make_hand("Th Ts Td Tc 9h"), FiveCardHandRank.FOUR_OF_A_KIND, (Rank.TEN,)),
]

# ============================================================================
# FULL HOUSE samples (3 of a kind + pair)
# ============================================================================
FULL_HOUSE_SAMPLES = [
    # Aces full of Kings
    (
        make_hand("Ah As Ad Kh Ks"),
        FiveCardHandRank.FULL_HOUSE,
        (Rank.ACE, Rank.KING),
    ),
    # Kings full of Aces
    (
        make_hand("Kh Ks Kd Ah As"),
        FiveCardHandRank.FULL_HOUSE,
        (Rank.KING, Rank.ACE),
    ),
    # Twos full of Threes
    (
        make_hand("2h 2s 2d 3h 3s"),
        FiveCardHandRank.FULL_HOUSE,
        (Rank.TWO, Rank.THREE),
    ),
    # Tens full of Jacks
    (
        make_hand("Th Ts Td Jh Js"),
        FiveCardHandRank.FULL_HOUSE,
        (Rank.TEN, Rank.JACK),
    ),
]

# ============================================================================
# FLUSH samples (5 same suit, not straight)
# ============================================================================
FLUSH_SAMPLES = [
    # Ace-high flush
    (
        make_hand("Ah Kh 8h 5h 2h"),
        FiveCardHandRank.FLUSH,
        (Rank.ACE, Rank.KING, Rank.EIGHT, Rank.FIVE, Rank.TWO),
    ),
    # King-high flush
    (
        make_hand("Ks Js 9s 7s 3s"),
        FiveCardHandRank.FLUSH,
        (Rank.KING, Rank.JACK, Rank.NINE, Rank.SEVEN, Rank.THREE),
    ),
    # Seven-high flush (lowest possible flush)
    (
        make_hand("7d 5d 4d 3d 2d"),
        FiveCardHandRank.FLUSH,
        (Rank.SEVEN, Rank.FIVE, Rank.FOUR, Rank.THREE, Rank.TWO),
    ),
]

# ============================================================================
# STRAIGHT samples (5 consecutive, not suited)
# ============================================================================
STRAIGHT_SAMPLES = [
    # Broadway (A-K-Q-J-10, not suited)
    (make_hand("Ah Ks Qd Jc Th"), FiveCardHandRank.STRAIGHT, (Rank.ACE,)),
    # King-high straight
    (make_hand("Kh Qs Jd Tc 9h"), FiveCardHandRank.STRAIGHT, (Rank.KING,)),
    # Wheel (A-2-3-4-5, not suited) - Ace is LOW, high card is 5
    (make_hand("Ah 2s 3d 4c 5h"), FiveCardHandRank.STRAIGHT, (Rank.FIVE,)),
    (make_hand("5s 4h 3c 2d As"), FiveCardHandRank.STRAIGHT, (Rank.FIVE,)),
    # Six-high straight
    (make_hand("6h 5s 4d 3c 2h"), FiveCardHandRank.STRAIGHT, (Rank.SIX,)),
]

# ============================================================================
# THREE OF A KIND samples
# ============================================================================
THREE_OF_A_KIND_SAMPLES = [
    # Trip Aces
    (make_hand("Ah As Ad Kh Qh"), FiveCardHandRank.THREE_OF_A_KIND, (Rank.ACE,)),
    # Trip Kings
    (make_hand("Kh Ks Kd Ah 2h"), FiveCardHandRank.THREE_OF_A_KIND, (Rank.KING,)),
    # Trip Twos
    (make_hand("2h 2s 2d Ah Kh"), FiveCardHandRank.THREE_OF_A_KIND, (Rank.TWO,)),
    # Trip Tens
    (make_hand("Th Ts Td 9h 8h"), FiveCardHandRank.THREE_OF_A_KIND, (Rank.TEN,)),
]

# ============================================================================
# TWO PAIR samples
# ============================================================================
TWO_PAIR_SAMPLES = [
    # Aces and Kings
    (
        make_hand("Ah As Kh Ks Qh"),
        FiveCardHandRank.TWO_PAIR,
        (Rank.ACE, Rank.KING),
    ),
    # Kings and Twos
    (
        make_hand("Kh Ks 2h 2s Ah"),
        FiveCardHandRank.TWO_PAIR,
        (Rank.KING, Rank.TWO),
    ),
    # Tens and Nines
    (
        make_hand("Th Ts 9h 9s Ah"),
        FiveCardHandRank.TWO_PAIR,
        (Rank.TEN, Rank.NINE),
    ),
    # Threes and Twos
    (
        make_hand("3h 3s 2h 2s Ah"),
        FiveCardHandRank.TWO_PAIR,
        (Rank.THREE, Rank.TWO),
    ),
]

# ============================================================================
# PAIR TENS OR BETTER samples (10, J, Q, K, A pairs - these PAY)
# ============================================================================
PAIR_TENS_OR_BETTER_SAMPLES = [
    # Pair of Aces
    (make_hand("Ah As Kh Qh Jh"), FiveCardHandRank.PAIR_TENS_OR_BETTER, (Rank.ACE,)),
    # Pair of Kings
    (make_hand("Kh Ks Ah Qh Jh"), FiveCardHandRank.PAIR_TENS_OR_BETTER, (Rank.KING,)),
    # Pair of Queens
    (make_hand("Qh Qs Ah Kh 2h"), FiveCardHandRank.PAIR_TENS_OR_BETTER, (Rank.QUEEN,)),
    # Pair of Jacks
    (make_hand("Jh Js Ah Kh Qh"), FiveCardHandRank.PAIR_TENS_OR_BETTER, (Rank.JACK,)),
    # Pair of Tens (boundary case - just qualifies)
    (make_hand("Th Ts Ah Kh Qh"), FiveCardHandRank.PAIR_TENS_OR_BETTER, (Rank.TEN,)),
]

# ============================================================================
# PAIR BELOW TENS samples (2-9 pairs - these LOSE)
# ============================================================================
PAIR_BELOW_TENS_SAMPLES = [
    # Pair of Nines (boundary case - just misses)
    (make_hand("9h 9s Ah Kh Qh"), FiveCardHandRank.PAIR_BELOW_TENS, (Rank.NINE,)),
    # Pair of Eights
    (make_hand("8h 8s Ah Kh Qh"), FiveCardHandRank.PAIR_BELOW_TENS, (Rank.EIGHT,)),
    # Pair of Fives
    (make_hand("5h 5s Ah Kh Qh"), FiveCardHandRank.PAIR_BELOW_TENS, (Rank.FIVE,)),
    # Pair of Twos (lowest pair)
    (make_hand("2h 2s Ah Kh Qh"), FiveCardHandRank.PAIR_BELOW_TENS, (Rank.TWO,)),
]

# ============================================================================
# HIGH CARD samples (no made hand)
# ============================================================================
HIGH_CARD_SAMPLES = [
    # Ace-high (best high card)
    (make_hand("Ah Ks Qd Jc 9h"), FiveCardHandRank.HIGH_CARD, (Rank.ACE,)),
    # King-high
    (make_hand("Kh Qs Jd 9c 7h"), FiveCardHandRank.HIGH_CARD, (Rank.KING,)),
    # Seven-high (worst possible hand)
    (make_hand("7h 5s 4d 3c 2h"), FiveCardHandRank.HIGH_CARD, (Rank.SEVEN,)),
    # Nine-high
    (make_hand("9h 7s 5d 3c 2h"), FiveCardHandRank.HIGH_CARD, (Rank.NINE,)),
]

# ============================================================================
# ALL SAMPLES combined for iteration
# ============================================================================
ALL_HAND_SAMPLES = (
    ROYAL_FLUSH_SAMPLES
    + STRAIGHT_FLUSH_SAMPLES
    + FOUR_OF_A_KIND_SAMPLES
    + FULL_HOUSE_SAMPLES
    + FLUSH_SAMPLES
    + STRAIGHT_SAMPLES
    + THREE_OF_A_KIND_SAMPLES
    + TWO_PAIR_SAMPLES
    + PAIR_TENS_OR_BETTER_SAMPLES
    + PAIR_BELOW_TENS_SAMPLES
    + HIGH_CARD_SAMPLES
)
