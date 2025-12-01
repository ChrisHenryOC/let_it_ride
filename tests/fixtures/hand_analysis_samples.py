"""Test fixtures for hand analysis utilities.

This module provides sample hands for testing hand analysis functions,
covering all draw types, made hands, and edge cases for both 3-card
and 4-card analysis.
"""

from let_it_ride.core.card import Card, Rank, Suit

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
    """Create a hand from space-separated notation like 'Ah Kh Qh'."""
    return [make_card(n) for n in notations.split()]


# ============================================================================
# THREE-CARD SAMPLES - For Bet 1 Analysis
# ============================================================================

# Made hands - 3 cards
THREE_CARD_TRIPS_SAMPLES = [
    make_hand("Ah As Ad"),  # Trip Aces
    make_hand("Kh Ks Kd"),  # Trip Kings
    make_hand("2h 2s 2d"),  # Trip Twos
]

THREE_CARD_HIGH_PAIR_SAMPLES = [
    make_hand("Ah As Kd"),  # Pair of Aces
    make_hand("Kh Ks Qd"),  # Pair of Kings
    make_hand("Th Ts 9d"),  # Pair of Tens (minimum paying)
]

THREE_CARD_LOW_PAIR_SAMPLES = [
    make_hand("9h 9s Ad"),  # Pair of Nines (non-paying)
    make_hand("2h 2s Kd"),  # Pair of Twos
    make_hand("7h 7s Qd"),  # Pair of Sevens
]

# Flush draws - 3 cards suited
THREE_CARD_FLUSH_DRAW_SAMPLES = [
    make_hand("Ah Kh 9h"),  # Hearts flush draw
    make_hand("2s 7s Ks"),  # Spades flush draw
    make_hand("3d 6d Jd"),  # Diamonds flush draw
]

# Royal flush draws - 3 suited high cards including Ace
THREE_CARD_ROYAL_DRAW_SAMPLES = [
    make_hand("Ah Kh Qh"),  # AKQ suited - Mini Royal / Royal draw
    make_hand("As Ks Ts"),  # AKT suited
    make_hand("Ad Qd Td"),  # AQT suited
    make_hand("Ac Jc Tc"),  # AJT suited
]

# Straight flush draws - 3 connected suited
THREE_CARD_STRAIGHT_FLUSH_DRAW_SAMPLES = [
    make_hand("9h Th Jh"),  # 9TJ suited
    make_hand("5s 6s 7s"),  # 567 suited
    make_hand("Ah 2h 3h"),  # Wheel suited
    make_hand("Qd Kd Ad"),  # QKA suited (also royal draw)
]

# Straight draws (not flush) - 3 cards
THREE_CARD_STRAIGHT_DRAW_SAMPLES = [
    make_hand("9h Ts Jd"),  # 9TJ offsuit
    make_hand("5h 6s 7d"),  # 567 offsuit
    make_hand("Ah 2s 3d"),  # Wheel offsuit
    make_hand("Qh Ks Ad"),  # QKA offsuit
    make_hand("Jh Qs Kd"),  # JQK offsuit
]

# No draws - 3 cards
THREE_CARD_NO_DRAW_SAMPLES = [
    make_hand("2h 5s Kd"),  # No flush, no straight potential
    make_hand("3h 7s Jd"),  # Gaps too large
    make_hand("Ah 4s 9d"),  # Disconnected
]

# High card counting samples
THREE_CARD_ALL_HIGH_SAMPLES = [
    make_hand("Th Jd Qc"),  # 3 high cards (10, J, Q)
    make_hand("Kh Qs Ad"),  # 3 high cards (K, Q, A)
]

THREE_CARD_NO_HIGH_SAMPLES = [
    make_hand("2h 5s 9d"),  # 0 high cards
    make_hand("3h 7s 8d"),  # 0 high cards
]

THREE_CARD_MIXED_HIGH_SAMPLES = [
    make_hand("2h 5s Td"),  # 1 high card (10)
    make_hand("3h Ks Ad"),  # 2 high cards (K, A)
]

# ============================================================================
# FOUR-CARD SAMPLES - For Bet 2 Analysis
# ============================================================================

# Made hands - 4 cards
FOUR_CARD_TRIPS_SAMPLES = [
    make_hand("Ah As Ad Kc"),  # Trip Aces + King
    make_hand("Kh Ks Kd 2c"),  # Trip Kings + 2
]

FOUR_CARD_HIGH_PAIR_SAMPLES = [
    make_hand("Ah As Kd Qc"),  # Pair of Aces
    make_hand("Th Ts 9d 2c"),  # Pair of Tens
]

FOUR_CARD_LOW_PAIR_SAMPLES = [
    make_hand("9h 9s Ad Kc"),  # Pair of Nines
    make_hand("2h 2s Ad Kc"),  # Pair of Twos
]

FOUR_CARD_TWO_PAIR_SAMPLES = [
    make_hand("Ah As Kd Kc"),  # Aces and Kings
    make_hand("Th Ts 2d 2c"),  # Tens and Twos
    make_hand("9h 9s 8d 8c"),  # Nines and Eights (non-paying)
]

# Flush draws - 4 cards suited (one away from flush)
FOUR_CARD_FLUSH_DRAW_SAMPLES = [
    make_hand("Ah Kh 9h 2h"),  # Hearts flush draw
    make_hand("2s 7s Ks As"),  # Spades flush draw
]

# Royal flush draws - 4 suited high cards including Ace
FOUR_CARD_ROYAL_DRAW_SAMPLES = [
    make_hand("Ah Kh Qh Jh"),  # AKQJ suited - one from royal
    make_hand("As Ks Qs Ts"),  # AKQT suited
    make_hand("Ad Kd Jd Td"),  # AKJT suited
]

# Open-ended straight draws - 4 consecutive cards
FOUR_CARD_OPEN_STRAIGHT_SAMPLES = [
    make_hand("5h 6s 7d 8c"),  # 5678 - open-ended (needs 4 or 9)
    make_hand("8h 9s Td Jc"),  # 89TJ - open-ended (needs 7 or Q)
    make_hand("3h 4s 5d 6c"),  # 3456 - open-ended (needs 2 or 7)
]

# Inside (gutshot) straight draws - 4 cards with gap
FOUR_CARD_INSIDE_STRAIGHT_SAMPLES = [
    make_hand("5h 6s 8d 9c"),  # 5689 - needs 7 only
    make_hand("9h Ts Qd Kc"),  # 9TQK - needs J only
    make_hand("Ah 2s 3d 5c"),  # A235 - needs 4 only
]

# Straight flush draws - 4 connected suited
FOUR_CARD_STRAIGHT_FLUSH_DRAW_SAMPLES = [
    make_hand("8h 9h Th Jh"),  # 89TJ suited
    make_hand("4s 5s 6s 7s"),  # 4567 suited
    make_hand("Qd Kd Ad 2c"),  # QKA suited (not straight flush - 2 breaks it)
]

# No draws - 4 cards
FOUR_CARD_NO_DRAW_SAMPLES = [
    make_hand("2h 5s 9d Kc"),  # No flush, no straight potential
    make_hand("3h 7s Jd Ac"),  # Gaps too large
]

# Edge cases for straight detection
FOUR_CARD_WHEEL_SAMPLES = [
    make_hand("Ah 2s 3d 4c"),  # A234 - needs 5 (inside draw)
    make_hand("Ah 2s 3d 5c"),  # A235 - needs 4 (inside draw)
    make_hand("2h 3s 4d 5c"),  # 2345 - open-ended
]

FOUR_CARD_BROADWAY_SAMPLES = [
    make_hand("Th Js Qd Kc"),  # TJQK - open-ended (needs 9 or A)
    make_hand("Jh Qs Kd Ac"),  # JQKA - inside (needs T only, can't go higher)
]
