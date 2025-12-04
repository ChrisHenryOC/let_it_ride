# Security Code Review: PR #77 - Bonus Betting Strategies

**Reviewer:** Security Code Reviewer
**Date:** 2025-12-03
**PR:** #77 - LIR-14 Bonus Betting Strategies
**Files Reviewed:**
- `src/let_it_ride/strategy/bonus.py` (358 lines added)
- `tests/unit/strategy/test_bonus.py` (778 lines added)
- `src/let_it_ride/strategy/__init__.py` (16 lines added)

---

## Summary

This PR implements bonus betting strategies for a casino game simulator. The code is well-structured with good defensive programming practices. The implementation correctly handles the primary division-by-zero risk when `starting_bankroll` is zero. However, there are several low-severity issues related to floating-point edge cases, input validation gaps, and missing validation for negative amounts that could lead to unexpected behavior or incorrect betting calculations.

---

## Findings by Severity

### Critical

**No critical security vulnerabilities identified.**

### High

**No high-severity security issues identified.**

### Medium

#### M1: Missing Validation for Negative Amounts in Strategy Constructors

**Location:** `src/let_it_ride/strategy/bonus.py:120-126`, `src/let_it_ride/strategy/bonus.py:152-173`, `src/let_it_ride/strategy/bonus.py:212-242`

**Description:** The strategy constructors (`AlwaysBonusStrategy`, `StaticBonusStrategy`, `BankrollConditionalBonusStrategy`) do not validate that amount/ratio values are non-negative. While the `_clamp_bonus_bet` function handles negative bets at runtime by returning 0, allowing negative configuration values could indicate configuration errors that should be caught early.

**Impact:**
- A configuration error (e.g., `amount=-5.0`) would silently result in no bonus bets being placed, rather than flagging the invalid configuration
- This could lead to confusion during debugging when expected bets are not being placed

**Remediation:**
```python
def __init__(self, amount: float) -> None:
    if amount < 0:
        raise ValueError("amount must be non-negative")
    self._amount = amount
```

**CWE Reference:** CWE-20 (Improper Input Validation)

---

#### M2: Missing Validation for Ratio Bounds in StaticBonusStrategy

**Location:** `src/let_it_ride/strategy/bonus.py:152-173`

**Description:** The `ratio` parameter accepts any float value without bounds checking. While extremely large ratios would be clamped by `max_bonus_bet`, negative ratios could result in unexpected behavior, and very large ratios (e.g., `ratio=1e308`) could cause floating-point issues.

**Impact:**
- Negative ratios would silently result in 0 bets due to the clamp function
- Extremely large ratios combined with large base bets could produce `inf` values

**Remediation:**
```python
if ratio is not None and ratio < 0:
    raise ValueError("ratio must be non-negative")
```

**CWE Reference:** CWE-20 (Improper Input Validation)

---

### Low

#### L1: Floating-Point Edge Cases Not Explicitly Handled

**Location:** `src/let_it_ride/strategy/bonus.py:70-84` (`_clamp_bonus_bet` function)

**Description:** The `_clamp_bonus_bet` function does not explicitly handle floating-point special values (`float('inf')`, `float('-inf')`, `float('nan')`). While Python's comparison operators handle `inf` correctly (it would be clamped to `max_bonus_bet`), `nan` comparisons always return `False`, which could lead to unexpected behavior.

**Impact:**
- If `bet` is `nan`, the function would return `nan` (since `nan <= 0` is `False`, `nan < context.min_bonus_bet` is `False`, and `min(nan, x)` returns `nan`)
- If `context.max_bonus_bet` is `nan` or `inf`, the clamp may not work as expected

**Remediation:**
```python
def _clamp_bonus_bet(bet: float, context: BonusContext) -> float:
    import math
    if math.isnan(bet) or bet <= 0:
        return 0.0
    if bet < context.min_bonus_bet:
        return 0.0
    if math.isinf(bet):
        return context.max_bonus_bet
    return min(bet, context.max_bonus_bet)
```

**CWE Reference:** CWE-682 (Incorrect Calculation)

---

#### L2: No Validation That min_bonus_bet <= max_bonus_bet in BonusContext

**Location:** `src/let_it_ride/strategy/bonus.py:18-47` (`BonusContext` dataclass)

**Description:** The `BonusContext` dataclass does not validate that `min_bonus_bet <= max_bonus_bet`. If these values are inverted, the betting logic could behave unexpectedly.

**Impact:**
- If `min_bonus_bet > max_bonus_bet`, a valid bet amount could be clamped to `max_bonus_bet` but then treated as below `min_bonus_bet` in subsequent logic (though the current implementation avoids this by clamping after the min check)
- The current implementation would return 0 for any bet when `min > max`, which may not be the intended behavior

**Remediation:**
```python
def __post_init__(self) -> None:
    if self.min_bonus_bet > self.max_bonus_bet:
        raise ValueError("min_bonus_bet cannot exceed max_bonus_bet")
```

**CWE Reference:** CWE-20 (Improper Input Validation)

---

#### L3: Profit Percentage Calculation Could Use Stale/Inconsistent Session Profit

**Location:** `src/let_it_ride/strategy/bonus.py:287-289`

**Description:** The profit percentage calculation uses `context.session_profit` directly without validating its consistency with `bankroll` and `starting_bankroll`. If `session_profit` is not correctly maintained by the calling code (i.e., `session_profit != bankroll - starting_bankroll`), the bet calculation could be incorrect.

**Impact:**
- This is more of a design consideration than a security issue
- Incorrect session_profit values could lead to over-betting or under-betting

**Remediation:**
Consider adding a consistency check or documenting the invariant clearly:
```python
# In BonusContext.__post_init__
expected_profit = self.bankroll - self.starting_bankroll
if abs(self.session_profit - expected_profit) > 0.01:
    raise ValueError("session_profit inconsistent with bankroll values")
```

**CWE Reference:** CWE-682 (Incorrect Calculation)

---

#### L4: Scaling Tiers Overlap Not Validated

**Location:** `src/let_it_ride/strategy/bonus.py:279-285`

**Description:** The scaling tiers are processed in order and the first matching tier is used. However, there is no validation that tiers don't overlap or have gaps. This could lead to configuration errors where the wrong tier is selected.

**Impact:**
- If tiers overlap, the behavior depends on tier ordering (first match wins)
- This is expected behavior but could be confusing if not documented

**Remediation:**
Consider validating tier boundaries in the constructor or documenting the first-match behavior clearly.

**CWE Reference:** CWE-670 (Always-Incorrect Control Flow Implementation)

---

### Informational

#### I1: Good Practice: Division by Zero Protection

**Location:** `src/let_it_ride/strategy/bonus.py:261`, `src/let_it_ride/strategy/bonus.py:267`

The code correctly checks `context.starting_bankroll > 0` before performing division operations to calculate bankroll ratio and drawdown. This is a positive security practice.

---

#### I2: Good Practice: Use of Frozen Dataclass

**Location:** `src/let_it_ride/strategy/bonus.py:18`

Using `@dataclass(frozen=True, slots=True)` for `BonusContext` prevents accidental mutation and provides memory efficiency. This is a good practice for immutable data structures.

---

#### I3: Good Practice: Type Annotations Throughout

All functions and methods have complete type annotations, which helps catch type-related bugs at static analysis time with mypy.

---

## Specific Recommendations

### File: `src/let_it_ride/strategy/bonus.py`

| Line | Severity | Recommendation |
|------|----------|----------------|
| 120-126 | Medium | Add validation: `if amount < 0: raise ValueError(...)` |
| 152-173 | Medium | Add validation for negative ratio values |
| 70-84 | Low | Add explicit `math.isnan()` check for NaN handling |
| 18-47 | Low | Add `__post_init__` to validate `min_bonus_bet <= max_bonus_bet` |

### File: `tests/unit/strategy/test_bonus.py`

The test file provides good coverage including edge cases. Consider adding tests for:
- Negative amount values passed to constructors (expect ValueError)
- NaN and infinity values in context fields
- Overlapping scaling tiers to document expected behavior

---

## Conclusion

The implementation is generally secure and well-designed for a simulation tool. The identified issues are low-to-medium severity and relate primarily to input validation edge cases that could cause unexpected behavior rather than exploitable security vulnerabilities. The code demonstrates good defensive programming practices, particularly in handling division-by-zero scenarios. The recommendations above would make the code more robust against configuration errors and floating-point edge cases.
