# Scratchpad: Issue #13 - Basic Strategy Implementation

**GitHub Issue:** [#13](https://github.com/ChrisHenryOC/let_it_ride/issues/13)
**Implementation Plan Issue:** LIR-10
**Created:** 2025-12-02

## Problem Statement

Implement the mathematically optimal basic strategy for Let It Ride pull/ride decisions. This is a critical component that makes the core betting decisions for each hand.

## Key Requirements

1. **Strategy Protocol** - Define the interface for all strategy implementations
2. **Decision enum** - PULL or RIDE
3. **StrategyContext dataclass** - Context available for decision making
4. **BasicStrategy class** - Implement optimal bet 1 and bet 2 decisions
5. **100% accuracy** - Match published basic strategy charts

## Basic Strategy Reference

### Bet 1 (3 cards) - LET IT RIDE when holding:
1. Any paying hand (pair of 10s+, three of a kind)
2. Three to a Royal Flush (3 suited royals including A)
3. Three suited in sequence (straight flush draw) EXCEPT A-2-3, 2-3-4
4. Three to straight flush, spread 4, with 1+ high card
5. Three to straight flush, spread 5, with 2+ high cards

### Bet 2 (4 cards) - LET IT RIDE when holding:
1. Any paying hand (pair 10+, trips, two pair)
2. Four to a flush
3. Four to outside straight with 1+ high card
4. Four to inside straight with 4 high cards (10-J-Q-K)

## Implementation Approach

### Files to Create

1. `src/let_it_ride/strategy/base.py` - Protocol and types
2. `src/let_it_ride/strategy/basic.py` - BasicStrategy implementation
3. `tests/fixtures/basic_strategy_cases.py` - Test case data
4. `tests/unit/strategy/test_basic.py` - Unit tests

### Key Types

```python
class Decision(Enum):
    PULL = "pull"
    RIDE = "ride"

@dataclass
class StrategyContext:
    """Context available to strategy for decisions"""
    session_profit: float
    hands_played: int
    streak: int  # Positive = wins, negative = losses
    bankroll: float
    deck_composition: dict[Rank, int] | None  # For composition-dependent

class Strategy(Protocol):
    def decide_bet1(self, analysis: HandAnalysis, context: StrategyContext) -> Decision
    def decide_bet2(self, analysis: HandAnalysis, context: StrategyContext) -> Decision
```

### Bet 1 Logic Breakdown

The `decide_bet1()` method needs to check these conditions in order:

1. **Paying hand check**: `analysis.has_paying_hand` (trips or high pair)
2. **Royal draw check**: `analysis.is_royal_draw`
3. **Straight flush draw check**: Need to verify consecutive suits AND exclude A-2-3, 2-3-4
4. **Spread 4 SF draw**: 3 cards span 4 values (1 gap), suited, 1+ high card
5. **Spread 5 SF draw**: 3 cards span 5 values (2 gaps), suited, 2+ high cards

Key insight: The HandAnalysis provides `is_straight_flush_draw` but we need more info about the spread (gaps). Need to calculate:
- Spread = (max rank value - min rank value) + 1
- Spread 3 = consecutive (0 gaps)
- Spread 4 = 1 gap
- Spread 5 = 2 gaps

### Bet 2 Logic Breakdown

The `decide_bet2()` method needs to check:

1. **Paying hand check**: `analysis.has_paying_hand`
2. **Flush draw check**: `analysis.is_flush_draw` (4 suited cards)
3. **Outside straight check**: `analysis.is_open_straight_draw` AND `analysis.high_cards >= 1`
4. **Inside straight with 4 high cards**: `analysis.is_inside_straight_draw` AND `analysis.high_cards == 4`

## Test Cases Needed

### Bet 1 Positive Cases (RIDE)
- Pair of 10s, Jacks, Queens, Kings, Aces
- Three of a kind
- Three to royal (e.g., As-Ks-Qs)
- Three consecutive suited (e.g., 7s-8s-9s)
- Spread 4 with 1 high (e.g., 8s-9s-Js)
- Spread 5 with 2 high (e.g., 8s-Ts-Qs)

### Bet 1 Negative Cases (PULL)
- Pair of 9s or below
- A-2-3 suited (excluded exception)
- 2-3-4 suited (excluded exception)
- Three suited, spread 4, 0 high cards
- Three suited, spread 5, 0-1 high cards
- Three unsuited connected

### Bet 2 Positive Cases (RIDE)
- Paying hands (pair 10+, trips, two pair)
- Four to flush
- Open-ended straight with 1+ high
- 10-J-Q-K inside straight (4 highs)

### Bet 2 Negative Cases (PULL)
- Low pair (9s or below)
- Three suited (not 4)
- Inside straight with <4 high cards
- Open-ended straight with 0 high cards

## Dependencies

- `HandAnalysis` from `core/hand_analysis.py` (LIR-7) - DONE
- `Card`, `Rank`, `Suit` from `core/card.py` - DONE

## Notes

- The strategy context is passed but BasicStrategy only uses `analysis`
- Other strategies may use context for bankroll-based or streak-based decisions
- The protocol allows future strategies without changing the interface
