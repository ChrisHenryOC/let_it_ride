# LIR-12: Custom Strategy Configuration Parser

Issue: https://github.com/ChrisHenryOC/let_it_ride/issues/15

## Overview

Implement custom strategy rule parsing from YAML configuration, plus conservative/aggressive presets.

## Dependencies (Completed)

- LIR-7: Hand Analysis Utilities - provides `HandAnalysis` dataclass with all fields
- LIR-8: Three-Card Hand Evaluation - provides `analyze_three_cards` function

## Implementation Plan

### 1. Create StrategyRule dataclass and CustomStrategy class

**File**: `src/let_it_ride/strategy/custom.py`

Key design decisions:
- `StrategyRule` is a simple dataclass with `condition: str` and `action: Decision`
- `CustomStrategy` holds separate rule lists for bet1 and bet2
- Condition evaluation uses safe expression parsing (no `eval()`)
- Support for boolean operators: `and`, `or`, `not`
- Support for comparisons: `>=`, `<=`, `>`, `<`, `==`, `!=`
- Special keyword `default` matches all hands

### 2. Condition Evaluation Approach

Parse conditions safely using a simple expression evaluator that:
1. Tokenizes the condition string
2. Extracts HandAnalysis field references
3. Evaluates boolean/comparison expressions

**Allowed HandAnalysis fields for conditions:**
- `high_cards`, `suited_cards`, `connected_cards`, `gaps`
- `has_paying_hand`, `has_pair`, `has_high_pair`, `has_trips`
- `is_flush_draw`, `is_straight_draw`, `is_open_straight_draw`
- `is_inside_straight_draw`, `is_straight_flush_draw`, `is_royal_draw`
- `suited_high_cards`, `is_excluded_sf_consecutive`, `straight_flush_spread`

**Example condition parsing:**
- `"has_paying_hand"` -> `analysis.has_paying_hand`
- `"is_royal_draw and suited_high_cards >= 3"` -> `analysis.is_royal_draw and analysis.suited_high_cards >= 3`
- `"high_cards >= 2"` -> `analysis.high_cards >= 2`

### 3. Conservative and Aggressive Presets

**File**: `src/let_it_ride/strategy/presets.py`

**ConservativeStrategy** - ride only on made hands:
- Bet 1: Ride on paying hands only
- Bet 2: Ride on paying hands only

**AggressiveStrategy** - ride on any draw:
- Bet 1: Ride on paying hands, any flush draw, any straight draw
- Bet 2: Ride on paying hands, any flush draw, any straight draw

These are implemented as factory functions returning `CustomStrategy` instances.

### 4. Export Strategy in __init__.py

Update `src/let_it_ride/strategy/__init__.py` to export:
- `StrategyRule`
- `CustomStrategy`
- `conservative_strategy`
- `aggressive_strategy`

### 5. Unit Tests

**File**: `tests/unit/strategy/test_custom.py`
- Test rule parsing from dict/config format
- Test condition evaluation with various HandAnalysis fields
- Test boolean operators (and, or, not)
- Test comparison operators
- Test first-match-wins rule priority
- Test default rule fallback
- Test invalid condition handling

**File**: `tests/unit/strategy/test_presets.py`
- Test ConservativeStrategy behavior (only rides on made hands)
- Test AggressiveStrategy behavior (rides on draws)
- Test both strategies conform to Strategy protocol

## File Structure

```
src/let_it_ride/strategy/
├── __init__.py        # Update exports
├── base.py            # Existing
├── basic.py           # Existing
├── custom.py          # NEW - StrategyRule, CustomStrategy
└── presets.py         # NEW - conservative_strategy, aggressive_strategy

tests/unit/strategy/
├── __init__.py        # Existing
├── test_basic.py      # Existing
├── test_custom.py     # NEW
└── test_presets.py    # NEW
```

## Implementation Notes

1. Use a safe expression parser - avoid `eval()` for security
2. Provide clear error messages for invalid conditions
3. Document available condition fields and operators
4. Keep rules simple and performant (evaluated per hand)
5. Follow existing code patterns from BasicStrategy
