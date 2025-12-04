# Documentation Accuracy Review: PR #77 - Bonus Betting Strategies

## Summary

The documentation quality in this PR is excellent overall. The module-level docstrings, class docstrings, and method docstrings are comprehensive, accurate, and well-structured. All public APIs have appropriate documentation with proper type hints. I found one medium-severity issue regarding the return value constraint documentation and a few low-severity improvement opportunities.

## Findings by Severity

### Critical

None identified.

### High

None identified.

### Medium

#### M1: BonusStrategy Protocol docstring has incomplete return value constraint

**File:** `src/let_it_ride/strategy/bonus.py`
**Lines:** 63-65

The Protocol's `get_bonus_bet` method docstring states:
```python
Returns:
    The bonus bet amount (0 means no bonus bet).
    Must be within [0, context.max_bonus_bet].
```

This is incomplete because the implementation actually returns 0 if the bet is below `min_bonus_bet`. The `_clamp_bonus_bet` function enforces: if `bet < context.min_bonus_bet`, it returns 0.0. This behavior is important for API users to understand.

**Recommendation:** Update the docstring to:
```python
Returns:
    The bonus bet amount (0 means no bonus bet).
    Returns 0 if below min_bonus_bet, otherwise clamped to max_bonus_bet.
```

### Low

#### L1: Module docstring could mention the factory function

**File:** `src/let_it_ride/strategy/bonus.py`
**Lines:** 1-10

The module-level docstring lists the strategy classes but does not mention the `create_bonus_strategy` factory function, which is a key public API for configuration integration.

**Current:**
```python
"""Bonus betting strategies for the Three-Card Bonus side bet.

This module provides implementations for various bonus betting strategies:
- NeverBonusStrategy: Never places bonus bets
- AlwaysBonusStrategy: Always places a fixed bonus bet amount
- StaticBonusStrategy: Fixed amount or ratio of base bet
- BankrollConditionalBonusStrategy: Bet based on session profit and bankroll conditions

All strategies respect min/max bonus bet limits.
"""
```

**Recommendation:** Add a line mentioning the factory function:
```python
Use `create_bonus_strategy()` to instantiate strategies from configuration.
```

#### L2: BankrollConditionalBonusStrategy behavior when both scaling_tiers and profit_percentage are set

**File:** `src/let_it_ride/strategy/bonus.py`
**Lines:** 229-235

The docstring for `profit_percentage` states:
```python
profit_percentage: If set, bet this fraction of session profit
    instead of base_amount. None uses base_amount.
```

However, the implementation shows that `profit_percentage` **overrides** the scaling tiers when both are configured (lines 287-289). This is not explicitly documented.

**Recommendation:** Clarify the precedence in the docstring:
```python
profit_percentage: If set and session is profitable, bet this fraction
    of session profit, overriding scaling_tiers. None uses base_amount
    or scaling tiers.
```

#### L3: `_clamp_bonus_bet` is a private function but could benefit from a note about min_bonus_bet behavior

**File:** `src/let_it_ride/strategy/bonus.py`
**Lines:** 70-84

The function docstring is accurate but the phrase "Returns 0 if bet is below min_bonus_bet" could be slightly more explicit about the semantic meaning (i.e., amounts below minimum are treated as "no bet" rather than "minimum bet").

**Current behavior is correct and documented, but slightly ambiguous for API consumers who might expect clamping UP to the minimum rather than returning 0.**

This is a minor stylistic preference and the current documentation is technically accurate.

#### L4: Test module docstring lists strategies but omits StreakBasedBonusStrategy caveat

**File:** `tests/unit/strategy/test_bonus.py`
**Lines:** 1-8

The test module docstring lists tested strategies but does not mention that `streak_based`, `session_conditional`, `combined`, and `custom` strategies are documented as not yet implemented. This is minor since the factory tests do cover the `NotImplementedError` cases.

## Documentation Completeness Checklist

| Component | Status | Notes |
|-----------|--------|-------|
| Module docstring | Pass | Clear, lists strategies |
| BonusContext docstring | Pass | All 9 attributes documented with types and semantics |
| BonusStrategy Protocol | Pass (minor issue) | Return constraint slightly incomplete (M1) |
| NeverBonusStrategy | Pass | Clear, concise |
| AlwaysBonusStrategy | Pass | Well documented |
| StaticBonusStrategy | Pass | Mutual exclusivity documented |
| BankrollConditionalBonusStrategy | Pass (minor issue) | Precedence could be clearer (L2) |
| create_bonus_strategy factory | Pass | Raises documented, return documented |
| Type hints | Pass | All public APIs have complete type hints |
| strategy/__init__.py exports | Pass | All new types exported and listed in __all__ |

## Type Hint Verification

All type hints are accurate and complete:

- `BonusContext`: All 9 fields have explicit types (float, int)
- `BonusStrategy.get_bonus_bet`: Correct signature `(context: BonusContext) -> float`
- `_clamp_bonus_bet`: Correct signature `(bet: float, context: BonusContext) -> float`
- `StaticBonusStrategy.__init__`: Uses `float | None` union types correctly
- `BankrollConditionalBonusStrategy.__init__`: Complex type `list[tuple[float, float | None, float]] | None` for scaling_tiers is accurate
- `create_bonus_strategy`: Return type `BonusStrategy` correctly uses Protocol type

## README/CLAUDE.md Verification

The `CLAUDE.md` file already mentions `BonusStrategy` protocol with `get_bonus_bet()` method (line 53), which is consistent with this implementation. The `bonus_strategy` configuration section (line 75) lists the types that are now implemented.

## Recommendations Summary

1. **[Medium]** Update `BonusStrategy.get_bonus_bet` return docstring to document the min_bonus_bet clamping behavior
2. **[Low]** Add `create_bonus_strategy` mention to module docstring
3. **[Low]** Clarify precedence when both `scaling_tiers` and `profit_percentage` are set

## Overall Assessment

**Documentation Quality: Excellent**

The PR demonstrates strong documentation practices with comprehensive docstrings on all public APIs. The documentation is accurate, type hints are complete, and the module structure is clear. The issues identified are minor refinements rather than critical gaps.
