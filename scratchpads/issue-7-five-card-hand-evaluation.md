# Scratchpad: Issue #7 - Five-Card Hand Evaluation

**GitHub Issue:** [#7](https://github.com/ChrisHenryOC/let_it_ride/issues/7)
**Implementation Plan Issue:** #4
**Created:** 2025-12-01

## Problem Statement

Implement accurate 5-card poker hand evaluation for the main game payouts. This is a critical foundation component that will be used by the game engine to determine payouts.

## Key Requirements

1. **FiveCardHandRank enum** - 11 distinct hand ranks from Royal Flush (10) to High Card (0)
2. **HandResult dataclass** - Contains rank, primary cards, and kickers
3. **evaluate_five_card_hand()** function - Takes 5 cards, returns HandResult
4. **Edge cases**: Wheel straight (A-2-3-4-5), steel wheel (suited A-2-3-4-5)
5. **Let It Ride specific**: Distinguish PAIR_TENS_OR_BETTER from PAIR_BELOW_TENS (only 10+ pays)
6. **Performance**: 100,000 hands in under 1 second

## Hand Rankings (Highest to Lowest)

| Rank | Value | Description |
|------|-------|-------------|
| ROYAL_FLUSH | 10 | A-K-Q-J-10 all same suit |
| STRAIGHT_FLUSH | 9 | 5 consecutive cards, same suit (includes wheel) |
| FOUR_OF_A_KIND | 8 | 4 cards of same rank |
| FULL_HOUSE | 7 | 3 of a kind + pair |
| FLUSH | 6 | 5 cards same suit, not sequential |
| STRAIGHT | 5 | 5 consecutive cards, different suits |
| THREE_OF_A_KIND | 4 | 3 cards of same rank |
| TWO_PAIR | 3 | Two different pairs |
| PAIR_TENS_OR_BETTER | 2 | Pair of 10, J, Q, K, or A |
| PAIR_BELOW_TENS | 1 | Pair of 2-9 |
| HIGH_CARD | 0 | No made hand |

## Implementation Approach

### Step 1: Core Data Structures

```python
class FiveCardHandRank(Enum):
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

@dataclass
class HandResult:
    rank: FiveCardHandRank
    primary_cards: tuple[Rank, ...]  # Main ranks determining hand (e.g., pair rank)
    kickers: tuple[Rank, ...]  # Remaining cards for tiebreaker
```

### Step 2: Evaluation Algorithm

1. **Count ranks and suits** - Build frequency tables
2. **Check flush** - All 5 cards same suit?
3. **Check straight** - 5 consecutive ranks (including A-low wheel)?
4. **Determine hand type** based on rank frequencies:
   - 4 of a kind: one rank appears 4 times
   - Full house: one rank 3 times, another 2 times
   - Three of a kind: one rank 3 times
   - Two pair: two ranks appear 2 times each
   - One pair: one rank appears 2 times
   - High card: all ranks appear once

### Step 3: Edge Cases

- **Wheel straight**: A-2-3-4-5 (Ace is low)
- **Steel wheel**: A-2-3-4-5 suited (straight flush, not royal)
- **Royal flush**: 10-J-Q-K-A suited (specific straight flush)
- **Pair distinction**: 10s, Jacks, Queens, Kings, Aces pay; 2-9 don't pay

## Files to Create

1. `src/let_it_ride/core/hand_evaluator.py` - Main implementation
2. `tests/fixtures/hand_samples.py` - Test fixture data
3. `tests/unit/core/test_hand_evaluator.py` - Unit tests

## Test Cases (from requirements)

- All 11 hand ranks with multiple examples each
- Wheel straight (A-2-3-4-5)
- Steel wheel (A-2-3-4-5 suited)
- Royal flush (each suit)
- Pair boundary cases (9s vs 10s)
- Performance benchmark

## Dependencies

- Uses `Card`, `Rank`, `Suit` from `core/card.py` (Issue #2/GitHub #5) - DONE

## Notes

- The `primary_cards` tuple captures the ranks that define the hand (e.g., for a full house, the triple rank then pair rank)
- The `kickers` tuple captures remaining cards for tiebreaking
- For Let It Ride, kickers may not be used for payouts, but they're included for completeness
