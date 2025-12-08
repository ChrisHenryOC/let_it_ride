# Code Quality Review: PR #114 - LIR-44 Chair Position Analytics

## Summary

This PR introduces a well-structured analytics module for comparing outcomes by seat position at multi-player tables. The implementation follows the project's established patterns closely, using frozen dataclasses with `__slots__`, proper type annotations, and appropriate separation of concerns. The code is readable and maintainable, with one medium-severity issue around variable shadowing and a few minor suggestions for improvement.

## Findings by Severity

### Medium

#### M1: Variable Name Shadows Standard Library Import (chair_position.py:250)
**File:** `src/let_it_ride/analytics/chair_position.py:250`

The local variable `stats_for_seat` in `analyze_chair_positions()` is fine, but elsewhere `stats` from scipy is imported at module level, and then `seat_stats` (a list) is created. More importantly, the function parameter in `_test_seat_independence` is named `seat_stats`, which is clear, but the field access `s.wins for s in seat_stats` uses `s` - this is acceptable but could be more descriptive.

The actual concern is the local variable name collision potential. In `_calculate_seat_statistics`:
```python
def _calculate_seat_statistics(
    seat_number: int,
    agg: _SeatAggregation,
    confidence_level: float,
) -> SeatStatistics:
```

The function creates a `SeatStatistics` return value, but in `analyze_chair_positions`, the loop variable is:
```python
stats_for_seat = _calculate_seat_statistics(...)
```

This is good naming. However, inside `analyze_chair_positions` at line 249-250:
```python
chi_sq, p_val, is_independent = _test_seat_independence(
    seat_stats, significance_level
)
```

The `seat_stats` variable shadows nothing here, but `stats` from scipy is imported at the top level. While Python's scoping prevents actual issues, having both `stats` (scipy) and `seat_stats` (list of SeatStatistics) in the module can be confusing. Consider renaming the scipy import:

**Recommendation:** Use a more explicit import alias for scipy.stats:
```python
from scipy import stats as scipy_stats
```

Or continue using `from scipy import stats` but rename local variables to avoid any potential confusion (e.g., `seat_statistics_list`).

**Impact:** Minor confusion risk; no runtime issue.

---

### Low

#### L1: Inconsistent Confidence Interval Documentation (chair_position.py:35-36)
**File:** `src/let_it_ride/analytics/chair_position.py:35-36`

The docstring for `SeatStatistics` states:
```python
win_rate_ci_lower: Lower bound of 95% CI for win rate.
win_rate_ci_upper: Upper bound of 95% CI for win rate.
```

However, the confidence level is actually configurable via the `confidence_level` parameter in `analyze_chair_positions()`. The "95%" is hardcoded in the docstring but the actual CI level depends on what is passed.

**Recommendation:** Update the docstring to:
```python
win_rate_ci_lower: Lower bound of CI for win rate.
win_rate_ci_upper: Upper bound of CI for win rate.
```

Or add a `confidence_level` field to `SeatStatistics` to track what level was used.

---

#### L2: Missing Input Validation for confidence_level and significance_level (chair_position.py:215-218)
**File:** `src/let_it_ride/analytics/chair_position.py:215-218`

The `analyze_chair_positions` function accepts `confidence_level` and `significance_level` parameters but does not validate them. Invalid values (e.g., negative, > 1) would propagate to `calculate_wilson_confidence_interval` and `scipy.stats.chisquare`, potentially causing confusing errors or incorrect results.

**Recommendation:** Add validation at the entry point, consistent with `statistics.py:261-273`:
```python
if not 0 < confidence_level < 1:
    raise ValueError(f"confidence_level must be between 0 and 1, got {confidence_level}")
if not 0 < significance_level < 1:
    raise ValueError(f"significance_level must be between 0 and 1, got {significance_level}")
```

The `_validate_confidence_level` helper from `statistics.py` could potentially be extracted to a shared location and reused.

---

#### L3: Test Helper Ignores Provided Outcome Parameter (test_chair_position.py:73-79)
**File:** `tests/unit/analytics/test_chair_position.py:73-79`

The `create_session_result` helper function signature includes `outcome: SessionOutcome = SessionOutcome.WIN`, but the function body immediately overrides this based on the `profit` value:
```python
def create_session_result(
    *,
    outcome: SessionOutcome = SessionOutcome.WIN,
    profit: float = 100.0,
    hands_played: int = 50,
) -> SessionResult:
    """Create a SessionResult with sensible defaults for testing."""
    if profit > 0:
        outcome = SessionOutcome.WIN
    elif profit < 0:
        outcome = SessionOutcome.LOSS
    else:
        outcome = SessionOutcome.PUSH
```

The `outcome` parameter is never used; it's always derived from `profit`. This is misleading to readers and test authors.

**Recommendation:** Either:
1. Remove the `outcome` parameter entirely since it's not used:
   ```python
   def create_session_result(
       *,
       profit: float = 100.0,
       hands_played: int = 50,
   ) -> SessionResult:
   ```
2. Or use the provided outcome instead of deriving it:
   ```python
   def create_session_result(
       *,
       outcome: SessionOutcome = SessionOutcome.WIN,
       profit: float = 100.0,
       hands_played: int = 50,
   ) -> SessionResult:
       # Use the provided outcome directly
       return SessionResult(outcome=outcome, ...)
   ```

---

#### L4: Magic Values in Test Data (test_chair_position.py:88-93)
**File:** `tests/unit/analytics/test_chair_position.py:88-93`

The `create_session_result` helper uses several unexplained magic values:
```python
total_wagered=hands_played * 15.0,  # 3 bets of $5 each
total_bonus_wagered=0.0,
peak_bankroll=max(1000.0, 1000.0 + profit),
max_drawdown=50.0,
max_drawdown_pct=0.05,
```

While there's a comment for `total_wagered`, the values `50.0` and `0.05` for drawdown are unexplained.

**Recommendation:** Extract magic values to named constants at the top of the test file:
```python
DEFAULT_STARTING_BANKROLL = 1000.0
DEFAULT_BASE_BET = 5.0
BETS_PER_HAND = 3
DEFAULT_MAX_DRAWDOWN = 50.0
DEFAULT_MAX_DRAWDOWN_PCT = 0.05
```

---

#### L5: Boolean Comparison Style Inconsistency (test_chair_position.py:641-642, 680, 704)
**File:** `tests/unit/analytics/test_chair_position.py:641-642`

Several assertions use explicit boolean comparison with `== True` or `== False`:
```python
assert analysis.is_position_independent == True  # noqa: E712
assert is_indep == False  # noqa: E712
```

The `# noqa: E712` comments suppress the ruff/flake8 warning, indicating awareness that this is not idiomatic Python. While there's a case for explicit boolean comparison in tests for clarity, the codebase generally uses `is True` or just `assert condition`.

**Recommendation:** For consistency with the project style, use:
```python
assert analysis.is_position_independent is True
```
or simply:
```python
assert analysis.is_position_independent
```

---

## Positive Observations

1. **Consistent with existing patterns:** The dataclass definitions follow the exact pattern used in `statistics.py` and `validation.py` (frozen, slots, comprehensive docstrings with attribute documentation).

2. **Excellent separation of concerns:** The module is well-organized with clear responsibilities:
   - `_SeatAggregation`: Mutable accumulator for intermediate state
   - `_aggregate_seat_data`: Data collection logic
   - `_calculate_seat_statistics`: Per-seat computation
   - `_test_seat_independence`: Statistical test isolation
   - `analyze_chair_positions`: Public orchestration

3. **Proper edge case handling:** The code correctly handles edge cases like:
   - Empty results list (raises ValueError)
   - Single seat (returns defaults for chi-square)
   - Zero wins (returns defaults rather than dividing by zero)
   - Zero rounds (produces zeroed statistics)

4. **Comprehensive test coverage:** The test file covers a wide range of scenarios including:
   - Dataclass immutability verification
   - Edge cases (empty, single seat, all wins/losses)
   - Uniform vs. biased distributions
   - Parameter validation

5. **Good use of type hints:** All function signatures have complete type annotations, including the private helper functions.

6. **Reuse of existing utilities:** The code correctly imports and uses `calculate_wilson_confidence_interval` from the validation module rather than reimplementing it.

---

## Recommendations Summary

| Priority | Item | Action |
|----------|------|--------|
| Medium | M1 | Consider aliasing scipy.stats import to avoid potential confusion |
| Low | L1 | Update docstring to not hardcode "95%" |
| Low | L2 | Add input validation for confidence_level and significance_level |
| Low | L3 | Remove unused `outcome` parameter from test helper |
| Low | L4 | Extract magic values to named constants |
| Low | L5 | Use consistent boolean assertion style |

---

## Inline PR Comments

```
INLINE_COMMENT:
- file: src/let_it_ride/analytics/chair_position.py
- position: 42
- comment: The docstring mentions "95% CI" but the confidence level is actually configurable. Consider updating to "CI for win rate" without specifying a fixed percentage, or add a `confidence_level` field to track what was used.

INLINE_COMMENT:
- file: tests/unit/analytics/test_chair_position.py
- position: 29
- comment: The `outcome` parameter is immediately overwritten based on `profit` and never used. Consider removing it to avoid confusion, or change the logic to respect the provided value.

INLINE_COMMENT:
- file: src/let_it_ride/analytics/chair_position.py
- position: 216
- comment: Consider adding validation for `confidence_level` and `significance_level` parameters (must be between 0 and 1). The `_validate_confidence_level` pattern from `statistics.py` could be reused here.
```
