# Scratchpad: Issue #8 - Three-Card Hand Evaluation (Bonus Bet)

**GitHub Issue:** [#8](https://github.com/ChrisHenryOC/let_it_ride/issues/8)
**Implementation Plan Issue:** LIR-5
**Created:** 2025-12-01

## Problem Statement

Implement 3-card poker hand evaluation for the Three Card Bonus side bet in Let It Ride. This evaluates the player's initial 3 cards before any community cards are revealed.

## Key Requirements

1. **ThreeCardHandRank enum** - 7 distinct hand ranks:
   - MINI_ROYAL (7) - AKQ suited only (distinct from other straight flushes)
   - STRAIGHT_FLUSH (6) - Other straight flushes
   - THREE_OF_A_KIND (5)
   - STRAIGHT (4)
   - FLUSH (3)
   - PAIR (2)
   - HIGH_CARD (1)

2. **evaluate_three_card_hand()** function - Takes 3 cards, returns ThreeCardHandRank

3. **Edge cases**:
   - Mini Royal: AKQ suited is special (highest paying bonus)
   - Straight detection: A-2-3 is valid (wheel), A-K-Q is valid (broadway), K-A-2 is NOT valid
   - No kickers needed (bonus just pays on hand type, not tiebreakers)

## Reference Probabilities (22,100 total combinations)

| Hand | Combinations | Probability |
|------|--------------|-------------|
| Mini Royal | 4 | 0.0181% |
| Straight Flush | 44 | 0.199% |
| Three of a Kind | 52 | 0.235% |
| Straight | 720 | 3.26% |
| Flush | 1,096 | 4.96% |
| Pair | 3,744 | 16.94% |
| High Card | 16,440 | 74.39% |

## Implementation Approach

### Step 1: ThreeCardHandRank enum
- Simpler than FiveCardHandRank (no full house, two pair, four of a kind)
- MINI_ROYAL is special case of straight flush for bonus payouts
- Include comparison operators for ordering

### Step 2: evaluate_three_card_hand()
Algorithm:
1. Validate exactly 3 cards
2. Check flush (all same suit)
3. Check straight (3 consecutive ranks, handling A-2-3 and A-K-Q)
4. Determine hand type:
   - If flush AND straight AND AKQ: MINI_ROYAL
   - If flush AND straight: STRAIGHT_FLUSH
   - If 3 of a kind (same rank): THREE_OF_A_KIND
   - If straight: STRAIGHT
   - If flush: FLUSH
   - If pair (2 same rank): PAIR
   - Otherwise: HIGH_CARD

### Step 3: Straight detection for 3 cards
Valid straights:
- A-2-3 (wheel, 3-high)
- 2-3-4 through Q-K-A (broadway)
- A-K-Q is also valid (broadway, NOT a wheel)

Invalid:
- K-A-2 (can't wrap around)

### Step 4: Testing
- All 7 hand types with multiple examples
- Edge cases: Mini Royal vs other straight flushes, wheel, broadway
- Probability validation: enumerate all 22,100 combinations

## Files to Create

1. `src/let_it_ride/core/three_card_evaluator.py` - Main implementation
2. `tests/fixtures/three_card_samples.py` - Test fixture data
3. `tests/unit/core/test_three_card_evaluator.py` - Unit tests

## Dependencies

- Uses `Card`, `Rank`, `Suit` from `core/card.py` (Issue #2/GitHub #5) - DONE
- Similar pattern to `hand_evaluator.py` (Issue #4/GitHub #7) - DONE

## Notes

- Unlike 5-card evaluation, no HandResult dataclass needed since bonus pays purely on hand type
- No kickers or primary_cards needed for three-card bonus evaluation
- Mini Royal distinction is purely for paytable differentiation (typically 40:1 vs 9:1 for other straight flushes)
