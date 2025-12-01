# Scratchpad: Issue #10 - Hand Analysis Utilities

**GitHub Issue:** [#10](https://github.com/ChrisHenryOC/let_it_ride/issues/10)
**Implementation Plan Issue:** LIR-7
**Created:** 2025-12-01

## Problem Statement

Implement hand analysis functions that identify draws, potential, and characteristics needed for strategy decisions. This is essential for implementing basic strategy that makes optimal bet 1 and bet 2 decisions.

## Key Requirements

1. **HandAnalysis dataclass** - All analysis fields for draw/hand detection
2. **analyze_three_cards()** - For Bet 1 decision (player's initial 3 cards)
3. **analyze_four_cards()** - For Bet 2 decision (3 player cards + 1 community)
4. Detection features:
   - Flush draws (3 or 4 suited cards)
   - Straight draws (open-ended vs inside/gutshot)
   - Royal flush draws and straight flush draws
   - High card counting (10, J, Q, K, A)
   - Gap analysis for straight draw quality
   - Made hand detection (pair, high pair, trips)

## HandAnalysis Dataclass Fields

```python
@dataclass
class HandAnalysis:
    # Card counts
    high_cards: int           # Count of 10, J, Q, K, A
    suited_cards: int         # Maximum cards of same suit
    connected_cards: int      # Maximum sequential cards
    gaps: int                 # Gaps in potential straight

    # Made hand flags
    has_paying_hand: bool     # Already qualifies for payout
    has_pair: bool
    has_high_pair: bool       # Pair of 10s or better
    has_trips: bool
    pair_rank: Rank | None

    # Draw flags
    is_flush_draw: bool
    is_straight_draw: bool
    is_open_straight_draw: bool
    is_inside_straight_draw: bool
    is_straight_flush_draw: bool
    is_royal_draw: bool

    # For 3-card analysis: cards needed info
    suited_high_cards: int    # High cards that are suited together
```

## Implementation Approach

### Step 1: Helper Functions

1. **count_high_cards()** - Count 10, J, Q, K, A in hand
2. **get_suit_distribution()** - Count cards per suit, return max suited
3. **analyze_straight_potential()** - Determine gaps and connectivity
4. **detect_flush_draw()** - 3 or 4 cards of same suit
5. **detect_straight_draw()** - Open-ended vs inside draw classification

### Step 2: analyze_three_cards()

For Bet 1 decision. Analyze player's initial 3 cards:
- Look for made hands (pair, trips)
- Detect 3-card flush draws (suited cards)
- Detect 3-card straight draws
- Count high cards
- Identify royal/straight flush draws

### Step 3: analyze_four_cards()

For Bet 2 decision. Analyze player's 3 cards + 1 community:
- Look for made hands (pair, trips, two pair)
- Detect 4-card flush draws (only need 1 more)
- Detect 4-card straight draws (open-ended or inside)
- Identify complete draws vs partial draws

### Step 4: Straight Draw Classification

**Open-ended straight draw (4 cards):** Can be completed on either end
- Example: 5-6-7-8 (needs 4 or 9)

**Inside (gutshot) straight draw (4 cards):** Missing one card in the middle
- Example: 5-6-8-9 (needs 7 only)

**3-card straight draw considerations:**
- Needs 2 more cards for a straight
- "Potential" classifications for strategy decisions

### Step 5: High Card Definitions

For Let It Ride, high cards are: 10, J, Q, K, A (rank values 10-14)
These are the only cards that make a paying pair.

## Files to Create

1. `src/let_it_ride/core/hand_analysis.py` - Main implementation (~300 lines)
2. `tests/fixtures/hand_analysis_samples.py` - Test fixture data
3. `tests/unit/core/test_hand_analysis.py` - Unit tests

## Test Scenarios

### Made Hand Tests
- Has pair (high vs low)
- Has trips
- No made hand

### Flush Draw Tests
- 3 suited cards (3-card flush draw)
- 4 suited cards (4-card flush draw)
- 2 suited cards (not a draw)

### Straight Draw Tests
- Open-ended 4-card straight (5-6-7-8)
- Inside 4-card straight (5-6-8-9)
- 3 connected cards
- Cards with gaps

### Special Draw Tests
- Royal flush draw (3+ high suited cards including A)
- Straight flush draw (3+ consecutive suited)

### High Card Tests
- All high cards
- Mixed high/low cards
- No high cards

## Dependencies

- Uses `Card`, `Rank`, `Suit` from `core/card.py` (Issue #2/GitHub #5) - DONE
- Related to `hand_evaluator.py` for made hand detection patterns

## Notes

- Performance is important - these functions will be called for every hand
- Reuse patterns from hand_evaluator.py for consistency
- The analysis supports strategy decisions, not payouts (unlike evaluators)
