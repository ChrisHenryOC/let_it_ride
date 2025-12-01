# Scratchpad: Issue #9 - Paytable Configuration System

**GitHub Issue:** [#9](https://github.com/ChrisHenryOC/let_it_ride/issues/9)
**Implementation Plan Issue:** LIR-6
**Created:** 2025-12-01

## Problem Statement

Implement configurable paytables for both main game and bonus bet with payout calculation. This is a foundation component that enables the game engine to calculate winnings based on hand rankings.

## Dependencies

- **FiveCardHandRank** from `core/hand_evaluator.py` (GitHub #7) - DONE
- **ThreeCardHandRank** from `core/three_card_evaluator.py` (GitHub #8) - DONE

## Key Requirements

### 1. MainGamePaytable dataclass
- Name identifier
- Payout mappings for all FiveCardHandRank values
- `calculate_payout(rank, bet) -> float` method
- `validate()` method to ensure all ranks covered

### 2. BonusPaytable dataclass
- Name identifier
- Payout mappings for all ThreeCardHandRank values
- `calculate_payout(rank, bet) -> float` method
- `validate()` method to ensure all ranks covered

### 3. Factory functions
- `standard_main_paytable()` - Standard main game payouts
- `bonus_paytable_a()` - Lower volatility bonus
- `bonus_paytable_b()` - Default bonus (per requirements)
- `bonus_paytable_c()` - Progressive bonus (jackpot simulated)

## Standard Main Game Paytable (from requirements)

| Hand | Payout Ratio |
|------|--------------|
| Royal Flush | 1000:1 |
| Straight Flush | 200:1 |
| Four of a Kind | 50:1 |
| Full House | 11:1 |
| Flush | 8:1 |
| Straight | 5:1 |
| Three of a Kind | 3:1 |
| Two Pair | 2:1 |
| Pair of 10s+ | 1:1 |
| Pair Below 10s | 0 (loss) |
| High Card | 0 (loss) |

## Bonus Paytables (from requirements)

### Paytable A (Lower Volatility, ~2.4% house edge)
| Hand | Payout |
|------|--------|
| Mini Royal | 50:1 |
| Straight Flush | 40:1 |
| Three of a Kind | 30:1 |
| Straight | 6:1 |
| Flush | 3:1 |
| Pair | 1:1 |
| High Card | 0 |

### Paytable B (Default, ~3.5% house edge)
| Hand | Payout |
|------|--------|
| Mini Royal | 100:1 |
| Straight Flush | 40:1 |
| Three of a Kind | 30:1 |
| Straight | 5:1 |
| Flush | 4:1 |
| Pair | 1:1 |
| High Card | 0 |

### Paytable C (Progressive)
| Hand | Payout |
|------|--------|
| Mini Royal | Progressive Jackpot |
| Straight Flush | 200:1 |
| Three of a Kind | 30:1 |
| Straight | 6:1 |
| Flush | 4:1 |
| Pair | 1:1 |
| High Card | 0 |

Note: For Paytable C, the progressive jackpot will be simulated with a fixed high value (e.g., 1000:1) or configurable.

## Implementation Approach

### Files to Create
- `src/let_it_ride/config/paytables.py` - Main implementation
- `tests/unit/config/test_paytables.py` - Unit tests

### Design Decisions

1. **Dataclass with frozen=True**: Paytables are immutable configuration
2. **Generic payout type**: Use `int` for payout ratios (bet multiplier)
3. **Validation on construction**: Ensure all hand ranks are covered
4. **Zero payouts**: Non-paying hands return 0 (player loses bet)

### Calculate Payout Logic
```python
def calculate_payout(self, rank: FiveCardHandRank, bet: float) -> float:
    """Calculate payout for a hand rank.

    Returns bet * payout_ratio for winning hands.
    Returns 0.0 for losing hands (pair below tens, high card).
    Original bet is NOT included - this is pure profit/loss.
    """
    ratio = self.payouts[rank]
    return bet * ratio
```

## Test Cases

### MainGamePaytable Tests
1. Calculate payout for each winning hand rank
2. Calculate payout for losing hands (returns 0)
3. Validation passes for complete paytable
4. Validation fails if missing hand rank
5. Custom paytable creation
6. Standard paytable factory returns correct payouts

### BonusPaytable Tests
1. Calculate payout for each bonus hand rank
2. Calculate payout for high card (returns 0)
3. Validation passes for complete paytable
4. Validation fails if missing hand rank
5. All three paytable variants (A, B, C) work correctly
6. Custom paytable creation

### Edge Cases
- Zero bet amount
- Large bet amounts (precision)
- Negative payout ratios should fail validation

## Estimated Scope
~200 lines implementation + ~150 lines tests
