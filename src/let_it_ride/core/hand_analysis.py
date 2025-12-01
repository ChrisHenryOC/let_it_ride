"""Hand analysis utilities for Let It Ride strategy decisions.

This module provides hand analysis functions that identify draws, potential,
and characteristics needed for strategy decisions. These functions support
the Bet 1 (3-card) and Bet 2 (4-card) decision points in the game.

Key features detected:
- Made hands (pair, high pair, trips)
- Flush draws (3 or 4 suited cards)
- Straight draws (open-ended vs inside/gutshot)
- Royal flush draws and straight flush draws
- High card counting (10, J, Q, K, A)
"""

from collections.abc import Sequence
from dataclasses import dataclass

from let_it_ride.core.card import Card, Rank

# High card ranks (10 through Ace) - these make paying pairs
_HIGH_CARD_VALUES = frozenset({10, 11, 12, 13, 14})

# Royal flush card values (10-J-Q-K-A)
_ROYAL_VALUES = frozenset({10, 11, 12, 13, 14})


@dataclass(frozen=True)
class HandAnalysis:
    """Analysis result for strategy decision support.

    This dataclass captures all relevant hand characteristics needed
    for making optimal Bet 1 and Bet 2 decisions in Let It Ride.

    Attributes:
        high_cards: Count of 10, J, Q, K, A in the hand.
        suited_cards: Maximum number of cards sharing the same suit.
        connected_cards: Maximum number of sequential rank values.
        gaps: Number of gaps in the longest potential straight sequence.

        has_paying_hand: True if hand already qualifies for payout (pair 10+).
        has_pair: True if hand contains exactly one pair (not two pair, not
            trips or better).
        has_high_pair: True if hand contains pair of 10s or better.
        has_trips: True if hand contains three of a kind.
        pair_rank: The rank of the pair if exactly one pair exists, None
            otherwise. Not set for two pair, trips, or better hands since
            in Let It Ride only the hand type matters, not the specific ranks.

        is_flush_draw: True if 3+ cards of same suit (potential flush).
        is_straight_draw: True if hand has straight potential.
        is_open_straight_draw: True if 4 consecutive cards (can complete on
            either end).
        is_inside_straight_draw: True if 4 cards with 1 gap (gutshot).
        is_straight_flush_draw: True if straight draw cards are suited.
        is_royal_draw: True if drawing to a royal flush (3+ suited royals).

        suited_high_cards: Count of high cards that are suited together.
    """

    # Card counts
    high_cards: int
    suited_cards: int
    connected_cards: int
    gaps: int

    # Made hand flags
    has_paying_hand: bool
    has_pair: bool
    has_high_pair: bool
    has_trips: bool
    pair_rank: Rank | None

    # Draw flags
    is_flush_draw: bool
    is_straight_draw: bool
    is_open_straight_draw: bool
    is_inside_straight_draw: bool
    is_straight_flush_draw: bool
    is_royal_draw: bool

    # Suited high card info
    suited_high_cards: int


def _count_high_cards(rank_values: Sequence[int]) -> int:
    """Count high cards (10, J, Q, K, A) in the given rank values."""
    return sum(1 for v in rank_values if v in _HIGH_CARD_VALUES)


def _get_max_suited(cards: Sequence[Card]) -> tuple[int, list[Card]]:
    """Get the maximum suited count and the cards of that suit.

    Uses a single pass through the cards for efficiency.

    Returns:
        Tuple of (max_count, suited_cards) where suited_cards are the cards
        of the most frequent suit.
    """
    if not cards:
        return 0, []

    # Single-pass grouping by suit
    suit_groups: dict[str, list[Card]] = {}
    for card in cards:
        suit_key = card.suit.value
        if suit_key not in suit_groups:
            suit_groups[suit_key] = []
        suit_groups[suit_key].append(card)

    # Find the suit with maximum count
    max_group = max(suit_groups.values(), key=len)
    return len(max_group), max_group


def _analyze_straight_potential(
    rank_values: Sequence[int],
) -> tuple[int, int, bool, bool]:
    """Analyze straight draw potential for a set of rank values.

    Args:
        rank_values: Sequence of rank values (2-14).

    Returns:
        Tuple of (connected_cards, gaps, is_open_ended, is_inside_draw).
        - connected_cards: Cards in best potential straight window
        - gaps: Number of gaps in the best potential straight
        - is_open_ended: True if 4 consecutive cards (open-ended draw)
        - is_inside_draw: True if 4 cards with 1 internal gap (gutshot)
    """
    if len(rank_values) < 3:
        return 0, 0, False, False

    unique_values = sorted(set(rank_values))

    # Build list of value sets to try (regular + ace-low if applicable)
    value_sets = [unique_values]

    # Handle Ace-low: if we have ace and low cards, also try ace as 1
    has_ace = 14 in unique_values
    has_low_cards = any(v <= 5 for v in unique_values if v != 14)

    if has_ace and has_low_cards:
        # Create version with ace as 1 instead of 14
        ace_low_values = sorted([1 if v == 14 else v for v in unique_values])
        value_sets.append(ace_low_values)

    best_connected = 1
    best_gaps = 4  # Start with max gaps
    is_open_ended = False
    is_inside = False

    for values in value_sets:
        n = len(values)
        if n < 3:
            continue

        # Try all possible 5-card straight windows
        # Windows: 1-5, 2-6, 3-7, ..., 10-14
        for window_low in range(1, 11):
            window_high = window_low + 4

            # Count cards in this window
            cards_in_window = [v for v in values if window_low <= v <= window_high]
            num_cards = len(cards_in_window)

            if num_cards < 3:
                continue

            num_gaps = 5 - num_cards

            # Update best if this window is better
            if num_cards > best_connected or (
                num_cards == best_connected and num_gaps < best_gaps
            ):
                best_connected = num_cards
                best_gaps = num_gaps

                # Determine draw type for 4-card hands
                if num_cards == 4 and len(rank_values) >= 4:
                    sorted_window = sorted(cards_in_window)
                    # Check if 4 cards are consecutive
                    consecutive = (sorted_window[-1] - sorted_window[0] == 3)

                    if consecutive:
                        # 4 consecutive cards
                        min_val = sorted_window[0]
                        max_val = sorted_window[-1]
                        # Open-ended: can complete on either end
                        # Not open-ended if at edge (A-2-3-4 or J-Q-K-A)
                        can_go_low = min_val > 1  # Can add card below
                        can_go_high = max_val < 14  # Can add card above

                        # Special case: A-2-3-4 (ace low) can only go high (5)
                        if min_val == 1 and max_val == 4:
                            can_go_low = False
                            can_go_high = True

                        is_open_ended = can_go_low and can_go_high
                        is_inside = not is_open_ended
                    else:
                        # Gap in the middle - inside draw (gutshot)
                        is_inside = True
                        is_open_ended = False

    return best_connected, best_gaps, is_open_ended, is_inside


def _is_royal_draw(suited_cards: Sequence[Card]) -> bool:
    """Check if suited cards form a royal flush draw.

    A royal draw requires 3+ suited cards that are all royal values
    (10, J, Q, K, A) and includes the Ace.
    """
    if len(suited_cards) < 3:
        return False

    suited_values = [c.rank.value for c in suited_cards]
    royal_suited = [v for v in suited_values if v in _ROYAL_VALUES]

    # Need 3+ royal cards and must include Ace for a true royal draw
    return len(royal_suited) >= 3 and 14 in royal_suited


def _is_straight_flush_draw(suited_cards: Sequence[Card]) -> bool:
    """Check if suited cards form a straight flush draw.

    Requires 3+ suited cards that are consecutive or nearly consecutive
    (within a 5-card window with at most 1 gap).
    """
    if len(suited_cards) < 3:
        return False

    suited_values = sorted([c.rank.value for c in suited_cards])

    # Check if the cards fit within a 5-card window (potential straight)
    # Also handle ace-low wheel draws
    has_ace = 14 in suited_values

    # Try regular values first
    span = suited_values[-1] - suited_values[0]
    if span <= 4:
        # All cards within 5-card span - valid straight flush draw
        return True

    # Try ace-low if applicable
    if has_ace and suited_values[0] <= 5:
        ace_low_values = sorted([1 if v == 14 else v for v in suited_values])
        span = ace_low_values[-1] - ace_low_values[0]
        if span <= 4:
            return True

    return False


def analyze_three_cards(cards: Sequence[Card]) -> HandAnalysis:
    """Analyze a 3-card hand for Bet 1 decision support.

    This function examines the player's initial 3 cards to identify
    made hands, draw potential, and characteristics needed for the
    first betting decision.

    Args:
        cards: Exactly 3 Card objects (player's initial hand).

    Returns:
        HandAnalysis with all relevant hand characteristics.

    Raises:
        ValueError: If not exactly 3 cards provided.
    """
    if len(cards) != 3:
        raise ValueError(f"Expected 3 cards, got {len(cards)}")

    rank_values = [c.rank.value for c in cards]

    # Count high cards
    high_cards = _count_high_cards(rank_values)

    # Get suit information
    suited_count, suited_cards = _get_max_suited(cards)

    # Analyze straight potential
    connected, gaps, is_open, is_inside = _analyze_straight_potential(rank_values)

    # Check for made hands
    rank_counts: dict[int, int] = {}
    for v in rank_values:
        rank_counts[v] = rank_counts.get(v, 0) + 1

    max_count = max(rank_counts.values()) if rank_counts else 0
    has_trips = max_count == 3
    has_pair = max_count == 2  # Exactly 2, not trips

    pair_rank: Rank | None = None
    has_high_pair = False

    if has_pair:
        # Find the pair rank
        for v, count in rank_counts.items():
            if count == 2:
                pair_rank = Rank(v)
                has_high_pair = v in _HIGH_CARD_VALUES
                break

    # Determine if we have a paying hand
    # In Let It Ride, minimum paying hand is pair of 10s
    has_paying_hand = has_trips or has_high_pair

    # Check for draws
    # 3-card flush draw: all 3 cards same suit
    is_flush_draw = suited_count == 3

    # 3-card straight draw: 3 cards within a 5-card straight window
    is_straight_draw = connected >= 3

    # Check special draws
    is_straight_flush_draw = is_flush_draw and _is_straight_flush_draw(suited_cards)
    is_royal_draw = is_flush_draw and _is_royal_draw(suited_cards)

    # Count suited high cards
    suited_high_cards = sum(
        1 for c in suited_cards if c.rank.value in _HIGH_CARD_VALUES
    )

    return HandAnalysis(
        high_cards=high_cards,
        suited_cards=suited_count,
        connected_cards=connected,
        gaps=gaps,
        has_paying_hand=has_paying_hand,
        has_pair=has_pair,
        has_high_pair=has_high_pair,
        has_trips=has_trips,
        pair_rank=pair_rank,
        is_flush_draw=is_flush_draw,
        is_straight_draw=is_straight_draw,
        is_open_straight_draw=is_open,
        is_inside_straight_draw=is_inside,
        is_straight_flush_draw=is_straight_flush_draw,
        is_royal_draw=is_royal_draw,
        suited_high_cards=suited_high_cards,
    )


def analyze_four_cards(cards: Sequence[Card]) -> HandAnalysis:
    """Analyze a 4-card hand for Bet 2 decision support.

    This function examines the player's 3 cards plus 1 community card
    to identify made hands, draw potential, and characteristics needed
    for the second betting decision.

    Args:
        cards: Exactly 4 Card objects (3 player + 1 community).

    Returns:
        HandAnalysis with all relevant hand characteristics.

    Raises:
        ValueError: If not exactly 4 cards provided.
    """
    if len(cards) != 4:
        raise ValueError(f"Expected 4 cards, got {len(cards)}")

    rank_values = [c.rank.value for c in cards]

    # Count high cards
    high_cards = _count_high_cards(rank_values)

    # Get suit information
    suited_count, suited_cards = _get_max_suited(cards)

    # Analyze straight potential
    connected, gaps, is_open, is_inside = _analyze_straight_potential(rank_values)

    # Check for made hands
    rank_counts: dict[int, int] = {}
    for v in rank_values:
        rank_counts[v] = rank_counts.get(v, 0) + 1

    max_count = max(rank_counts.values()) if rank_counts else 0
    unique_ranks = len(rank_counts)

    has_trips = max_count == 3
    # Check for two pair (unique_ranks == 2 with max_count == 2)
    has_two_pair = unique_ranks == 2 and max_count == 2
    # has_pair is True for single pair (not trips, not two pair)
    has_pair = max_count == 2 and not has_two_pair

    pair_rank: Rank | None = None
    has_high_pair = False

    # Only set pair_rank for single pairs (not two pair, trips, etc.)
    # In Let It Ride, only the hand type matters, not the specific ranks
    if has_pair:
        for v, count in rank_counts.items():
            if count == 2:
                pair_rank = Rank(v)
                has_high_pair = v in _HIGH_CARD_VALUES
                break

    # Determine if we have a paying hand
    # Two pair is a paying hand regardless of which pairs
    has_paying_hand = has_trips or has_high_pair or has_two_pair

    # Check for draws
    # 4-card flush draw: 4 cards same suit (only need 1 more)
    is_flush_draw = suited_count >= 4

    # 4-card straight draw: 4 cards in a 5-card straight window
    is_straight_draw = connected >= 4

    # Check special draws
    is_straight_flush_draw = is_flush_draw and _is_straight_flush_draw(suited_cards)
    is_royal_draw = is_flush_draw and _is_royal_draw(suited_cards)

    # Count suited high cards
    suited_high_cards = sum(
        1 for c in suited_cards if c.rank.value in _HIGH_CARD_VALUES
    )

    return HandAnalysis(
        high_cards=high_cards,
        suited_cards=suited_count,
        connected_cards=connected,
        gaps=gaps,
        has_paying_hand=has_paying_hand,
        has_pair=has_pair,
        has_high_pair=has_high_pair,
        has_trips=has_trips,
        pair_rank=pair_rank,
        is_flush_draw=is_flush_draw,
        is_straight_draw=is_straight_draw,
        is_open_straight_draw=is_open,
        is_inside_straight_draw=is_inside,
        is_straight_flush_draw=is_straight_flush_draw,
        is_royal_draw=is_royal_draw,
        suited_high_cards=suited_high_cards,
    )
