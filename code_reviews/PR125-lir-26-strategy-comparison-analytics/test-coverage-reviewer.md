# Test Coverage Review - PR #125

## Summary

The test suite for the strategy comparison analytics module (`test_comparison.py`) provides good coverage of the core functionality with 663 lines of test code covering 514 lines of production code (1.29:1 ratio). The tests cover dataclass creation, statistical test functions, comparison logic, and report formatting. However, there are several gaps in edge case coverage, missing tests for specific code paths in `_determine_confidence`, and no numerical stability testing which is present in the sibling `test_statistics.py` module.

## Critical Issues

None found.

## High Severity Issues

None found.

## Medium Severity Issues

### M1: Missing Test for `_determine_confidence` First Branch (p < 0.001 Path)

**File:** `/Users/chrishenry/source/let_it_ride/tests/unit/analytics/test_comparison.py`
**Related production code:** `comparison.py:265-271`

The `_determine_confidence` function has a specific branch for "both tests highly significant (p < 0.001)" which returns "high" confidence even without checking effect size. The existing `test_high_confidence` test uses p=0.001 with a large effect size, which triggers the second branch (lines 273-279) rather than the first branch.

**Missing test case:**
```python
def test_high_confidence_very_low_p_value_negligible_effect(self) -> None:
    """Both tests highly significant (p < 0.001) -> high confidence regardless of effect."""
    ttest = SignificanceTest("t-test", 3.0, 0.0001, True)
    mw = SignificanceTest("mann-whitney", 2000.0, 0.0001, True)
    es = EffectSize(0.1, "negligible")  # Negligible effect but very low p

    assert _determine_confidence(ttest, mw, es) == "high"
```

### M2: Missing Test for Strategy B Being Better

**File:** `/Users/chrishenry/source/let_it_ride/tests/unit/analytics/test_comparison.py`

All tests for `better_strategy` verify that strategy A wins. No test verifies the logic when `profit_mean_b > profit_mean_a` (line 378 in `comparison.py`).

**Missing test case:**
```python
def test_compare_strategies_b_is_better(self) -> None:
    """Should correctly identify when strategy B is better."""
    profits_a = [-50.0, -40.0, -30.0, -20.0, 10.0] * 20
    profits_b = [50.0, 40.0, 30.0, 20.0, -10.0] * 20

    results_a = create_results_with_profits(profits_a)
    results_b = create_results_with_profits(profits_b)

    comp = compare_strategies(results_a, results_b, "loser", "winner")

    assert comp.better_strategy == "winner"
```

### M3: Missing Test for Zero Hands Edge Case

**File:** `/Users/chrishenry/source/let_it_ride/tests/unit/analytics/test_comparison.py`
**Related production code:** `comparison.py:354, 358`

The production code handles `total_hands_a > 0` and `total_hands_b > 0` checks for EV calculation (lines 354, 358), but no test verifies this branch. While unlikely in practice (sessions with 0 hands played), the code path exists and should be tested.

### M4: Missing Numerical Stability Tests

**File:** `/Users/chrishenry/source/let_it_ride/tests/unit/analytics/test_comparison.py`

The sibling module `test_statistics.py` includes a `TestNumericalStability` class with tests for very large and very small values. The comparison module performs similar statistical calculations but lacks these edge case tests.

**Missing test class:**
```python
class TestNumericalStability:
    """Tests for numerical stability with edge cases."""

    def test_very_large_profits_no_nan(self) -> None:
        """Should handle very large profit values without NaN."""
        profits = [1e15, 2e15, 1.5e15] * 10
        results_a = create_results_with_profits(profits)
        results_b = create_results_with_profits([p * 0.9 for p in profits])

        comp = compare_strategies(results_a, results_b, "a", "b")

        assert not math.isnan(comp.effect_size.cohens_d)
        assert not math.isnan(comp.ttest.statistic)
```

## Low Severity Issues

### L1: Duplicate `create_session_result` Helper Function

**File:** `/Users/chrishenry/source/let_it_ride/tests/unit/analytics/test_comparison.py:25-52`

The `create_session_result` helper is duplicated verbatim in both `test_comparison.py` and `test_statistics.py`. This violates DRY and requires updating both files if `SessionResult` changes.

**Recommendation:** Move to a shared `conftest.py` or `tests/unit/fixtures.py` module.

### L2: Missing Test for Negative Significance Level

**File:** `/Users/chrishenry/source/let_it_ride/tests/unit/analytics/test_comparison.py`

Tests verify `significance_level=0.0` and `significance_level=1.0` raise errors, but not negative values like `-0.1`.

### L3: `format_comparison_report` Missing Negative EV Formatting Test

**File:** `/Users/chrishenry/source/let_it_ride/tests/unit/analytics/test_comparison.py:551-606`

The report formatting tests don't explicitly verify correct formatting of negative EV values with the `$` sign (e.g., `$-0.0350` vs `-$0.0350`).

### L4: Missing Test for `compare_multiple_strategies` with Custom Significance Level

**File:** `/Users/chrishenry/source/let_it_ride/tests/unit/analytics/test_comparison.py:494-549`

While `compare_strategies` has a test for custom significance levels (`test_custom_significance_level`), `compare_multiple_strategies` is only tested with the default value.

### L5: No Property-Based Testing

Given this is a simulation project that performs statistical calculations, property-based testing with the `hypothesis` library could strengthen coverage. For example:
- Cohen's d sign should match the sign of `mean_a - mean_b`
- Effect size interpretation should be consistent with Cohen's d magnitude
- Win rate should always be between 0 and 1

## Recommendations

1. **Add test for first branch of `_determine_confidence`**: Create a test with p-values below 0.001 and negligible effect size to verify the first high-confidence path is correctly triggered.

2. **Add test for strategy B being the winner**: Ensure the `better_strategy` selection logic works in both directions.

3. **Add numerical stability tests**: Mirror the `TestNumericalStability` pattern from `test_statistics.py` to catch potential floating-point issues with extreme values.

4. **Extract shared test fixtures**: Move `create_session_result` and `create_results_with_profits` to a shared location (`conftest.py` or a fixtures module).

5. **Consider property-based tests**: Add hypothesis-based tests for invariants like:
   - `effect_size.cohens_d >= 0` implies `profit_mean_a >= profit_mean_b` (for positive d)
   - Statistical test p-values are always in [0, 1]

6. **Test scipy exception handling**: While scipy handles most edge cases internally, consider what happens if scipy raises unexpected exceptions (e.g., with pathological input data).

7. **Add integration test with real simulation data**: The code quality review noted this - running actual simulations with different strategies would provide end-to-end validation.
