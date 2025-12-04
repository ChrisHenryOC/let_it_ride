# Code Quality Review: PR #77 - LIR-14: Bonus Betting Strategies

**Reviewer:** Code Quality Reviewer
**Date:** 2025-12-03
**PR:** https://github.com/ChrisHenryOC/let_it_ride/pull/77

## Summary

This PR implements bonus betting strategies for the Three-Card Bonus side bet with excellent code quality. The implementation follows project conventions with `__slots__` on all strategy classes, `slots=True` on the frozen dataclass, comprehensive type hints, and a clean protocol-based design. The code is well-structured with 50 tests providing thorough coverage. A few minor improvements are recommended, primarily around type safety and documentation clarity.

---

## Findings by Severity

### Critical

*No critical issues found.*

---

### High

*No high-severity issues found.*

The implementation correctly includes:
- `@dataclass(frozen=True, slots=True)` on `BonusContext` (line 18 in source, line 146 in diff)
- `__slots__` on all strategy classes (lines 94, 118, 150, 203-210 in source)

---

### Medium

#### M1: Type Ignore Comment in `StaticBonusStrategy.get_bonus_bet()`

**Location:** `src/let_it_ride/strategy/bonus.py:188` (diff line 316)

**Issue:** The `# type: ignore[operator]` comment indicates the type checker cannot verify the code is safe. While runtime validation in `__init__` ensures `self._ratio` is not None when this branch executes, a cleaner approach would make this explicit to the type checker.

**Current Code:**
```python
bet = context.base_bet * self._ratio  # type: ignore[operator]
```

**Recommended:** Use an assertion to satisfy the type checker without suppressing the warning:
```python
assert self._ratio is not None  # Guaranteed by __init__ validation
bet = context.base_bet * self._ratio
```

**Impact:** Minor - the current code works correctly, but assertions make the invariant explicit and improve maintainability.

---

#### M2: Scaling Tiers Order Dependency Not Documented

**Location:** `src/let_it_ride/strategy/bonus.py:278-285` (diff lines 406-413)

**Issue:** The scaling tiers loop uses `break` after finding the first matching tier. If tiers are provided out of order (not sorted by `min_profit`), the wrong tier could match. The docstring should document that tiers are matched in order and should be provided in ascending `min_profit` order.

**Current Code:**
```python
for min_profit, max_profit, tier_amount in self._scaling_tiers:
    in_range = context.session_profit >= min_profit and (
        max_profit is None or context.session_profit < max_profit
    )
    if in_range:
        bet = tier_amount
        break
```

**Recommendation:** Add to the `scaling_tiers` parameter docstring:
```python
scaling_tiers: List of (min_profit, max_profit, bet_amount) tuples.
    When profit is in range [min, max), use that bet_amount.
    Tiers are matched in order; provide in ascending min_profit order.
    If None, uses base_amount.
```

Alternatively, sort tiers during initialization:
```python
self._scaling_tiers = sorted(scaling_tiers, key=lambda t: t[0]) if scaling_tiers else None
```

---

#### M3: Profit Percentage Overrides Scaling Tiers Silently

**Location:** `src/let_it_ride/strategy/bonus.py:287-289` (diff lines 415-417)

**Issue:** When both `scaling_tiers` and `profit_percentage` are configured, the profit percentage silently overrides the tier-based amount. This interaction is not documented and could lead to confusing behavior.

**Current Code:**
```python
# Override with profit percentage if set
if self._profit_percentage is not None and context.session_profit > 0:
    bet = context.session_profit * self._profit_percentage
```

**Recommendation:** Either:
1. Document this precedence clearly in the docstring
2. Raise a ValueError in `__init__` if both are configured (mutually exclusive)
3. Add a comment explaining the intentional override behavior

---

### Low

#### L1: Test Uses `object.__setattr__` to Bypass Pydantic Validation

**Location:** `tests/unit/strategy/test_bonus.py:593, 600, 607, 623` (diff lines 1085, 1092, 1099, 1115)

**Issue:** Tests use `object.__setattr__(config, "type", ...)` to bypass Pydantic's frozen model validation. While this is a valid testing technique for edge cases, it's fragile and may break if Pydantic internals change.

**Current Code:**
```python
config = BonusStrategyConfig(type="never")
object.__setattr__(config, "type", "always")
```

**Recommended:** Use Pydantic's `model_construct()` for creating unvalidated instances:
```python
config = BonusStrategyConfig.model_construct(type="always")
```

This is the officially supported way to create Pydantic models without validation.

---

#### L2: Missing `__repr__` Methods for Debugging

**Location:** `src/let_it_ride/strategy/bonus.py`

**Issue:** The strategy classes lack `__repr__` methods, which makes debugging and logging less informative. For example, logging a strategy instance would show `<AlwaysBonusStrategy object at 0x...>` instead of `AlwaysBonusStrategy(amount=5.0)`.

**Recommendation (optional enhancement):** Add `__repr__` to strategy classes:
```python
def __repr__(self) -> str:
    return f"AlwaysBonusStrategy(amount={self._amount})"
```

Note: Since `__slots__` is used, you would need to add `"__repr__"` is not needed; methods don't go in slots.

---

#### L3: Unused `BonusContext` Fields

**Location:** `src/let_it_ride/strategy/bonus.py:41-46` (diff lines 169-174)

**Issue:** The `BonusContext` dataclass includes `main_streak` and `bonus_streak` fields, but none of the implemented strategies use them. These appear to be designed for the not-yet-implemented `streak_based` strategy.

**Impact:** No action needed - this is intentional forward compatibility. The fields are correctly documented and will be used by future strategy implementations.

---

## Positive Observations

1. **Performance-Conscious Design:** All classes use `__slots__` for memory efficiency, and the `BonusContext` dataclass uses `slots=True`. This aligns with the project's performance targets.

2. **Clean Protocol Design:** The `BonusStrategy` protocol is well-designed with a single `get_bonus_bet` method, matching the project's protocol-based architecture.

3. **Comprehensive Test Coverage:** 50 tests covering all strategies, edge cases (zero bankroll, large amounts, boundary conditions), protocol conformance, and factory function behavior.

4. **Good Documentation:** Docstrings are detailed with clear explanations of parameters, return values, and behavior.

5. **Proper Clamping Logic:** The `_clamp_bonus_bet` helper function correctly handles all edge cases (negative values, below min, above max).

6. **Zero Division Protection:** Bankroll ratio and drawdown calculations properly guard against division by zero when `starting_bankroll` is 0.

7. **Factory Pattern:** The `create_bonus_strategy` function cleanly encapsulates strategy instantiation from config models.

8. **Frozen Dataclass:** Using `frozen=True` on `BonusContext` ensures immutability, preventing accidental state modification during strategy execution.

9. **Consistent with Project Patterns:** The implementation mirrors existing patterns from `Strategy` protocol and betting systems.

---

## Recommendations by Priority

### Should Fix

1. **M1:** Replace type ignore with assertion in `StaticBonusStrategy.get_bonus_bet()`
2. **M2:** Document scaling tier order dependency or sort tiers
3. **M3:** Document the precedence between `profit_percentage` and `scaling_tiers`

### Nice to Have

4. **L1:** Use `model_construct()` in tests instead of `object.__setattr__`
5. **L2:** Add `__repr__` methods for improved debugging

---

## Files Reviewed

| File | Status |
|------|--------|
| `src/let_it_ride/strategy/bonus.py` | Reviewed - Minor Issues |
| `src/let_it_ride/strategy/__init__.py` | Reviewed - No Issues |
| `tests/unit/strategy/test_bonus.py` | Reviewed - Minor Issues |

---

## Diff Position Reference

For inline comments, positions are calculated from the `@@` hunk header lines:

| File | Hunk Start (diff line) |
|------|------------------------|
| `src/let_it_ride/strategy/__init__.py` | Line 83 |
| `src/let_it_ride/strategy/bonus.py` | Line 128 |
| `tests/unit/strategy/test_bonus.py` | Line 492 |
