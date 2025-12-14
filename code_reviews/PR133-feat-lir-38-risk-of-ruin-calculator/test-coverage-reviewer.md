# Test Coverage Review - PR #133

## Summary

PR #133 introduces comprehensive unit tests for the risk of ruin calculator module with 874 lines of test code covering 419 lines of implementation in `risk_of_ruin.py`. The test file demonstrates excellent coverage of the core module with strong statistical validation tests, edge case handling, and reproducibility verification. However, there is a critical gap: the `risk_curves.py` visualization module (260 lines) has no dedicated unit tests despite similar visualization modules having test coverage in the existing codebase.

## Findings

### Critical

#### C1. No Tests for `risk_curves.py` Visualization Module

**Files:**
- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/visualizations/risk_curves.py` (260 lines, untested)

The entire visualization module has no unit tests. This is a critical gap given:

1. The module is 260 lines of code with 3 public items exported in `__init__.py`: `RiskCurveConfig`, `plot_risk_curves()`, `save_risk_curves()`
2. Similar visualizations (`histogram.py`, `trajectory.py`) have comprehensive tests in `/Users/chrishenry/source/let_it_ride/tests/integration/test_visualizations.py`
3. The module contains validation logic at line 67-68:
   ```python
   if not report.results:
       raise ValueError("Cannot create plot from report with no results")
   ```
4. Configuration options need verification (`show_confidence_bands`, `show_analytical`, `show_thresholds`)
5. The `save_risk_curves` function validates output format at line 241-242:
   ```python
   if output_format not in ("png", "svg"):
       raise ValueError(f"Invalid format '{output_format}'. Must be 'png' or 'svg'.")
   ```

**Missing test coverage for:**
- `RiskCurveConfig` dataclass default values and custom values
- `plot_risk_curves()` - figure creation, empty results error, custom config, legend contents, axis labels
- `save_risk_curves()` - PNG/SVG output, extension handling, directory creation, invalid format error, custom DPI

**Recommendation:** Create tests in `/Users/chrishenry/source/let_it_ride/tests/integration/test_visualizations.py` following the existing pattern for histogram and trajectory modules, or create a new file `/Users/chrishenry/source/let_it_ride/tests/unit/analytics/test_risk_curves.py`.

---

### High

#### H1. Missing Test for Zero `base_bet` Inference Edge Case

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py:327`

When `base_bet` is None and all sessions have `total_hands == 0`, the code falls back to `base_bet = 1.0`. This fallback behavior is not tested.

```python
# Line 327 in implementation
estimated_base = total_wagered / (total_hands * 3) if total_hands > 0 else 1.0
```

The existing `test_auto_infer_base_bet` test at diff line 2536-2551 only tests the happy path where hands are played. No test verifies the fallback when `total_hands == 0`.

**Recommendation:** Add a test that creates SessionResult objects with `hands_played=0` and verifies `base_bet` defaults to `1.0`.

---

#### H2. Missing Test for NaN Analytical Estimate Handling in Formatter

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py:414-417`

The `format_risk_of_ruin_report` function handles NaN values by skipping them:

```python
if not math.isnan(analytical):
    lines.append(f"  Analytical Estimate: {analytical:.2%}")
```

No test verifies that when `analytical_estimates` contains NaN values, the formatted output correctly omits the "Analytical Estimate" line for those entries.

**Recommendation:** Add a test in `TestFormatRiskOfRuinReport` that creates a report with NaN analytical estimates and verifies they are omitted from output.

---

#### H3. Missing Test for Unsorted Bankroll Units Input

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py:346`

The implementation sorts bankroll units before processing:

```python
for units in sorted(bankroll_units):
```

The `test_basic_calculation` test at diff line 2500-2519 verifies results are sorted but uses already-sorted input `[20, 40, 60]`. No test explicitly verifies that unsorted input (e.g., `[60, 20, 40]`) produces correctly sorted output.

**Recommendation:** Add a test that provides unsorted bankroll units and verifies the output results are sorted ascending.

---

#### H4. Missing Test for Analytical Estimate with Zero Mean AND Zero Std

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py:143-145`

The `_calculate_analytical_ruin_probability` function has a branch for zero standard deviation:

```python
if std_profit == 0:
    # No variance means deterministic outcome
    return 0.0 if mean_profit > 0 else 1.0  # What about mean_profit == 0?
```

The test class `TestAnalyticalRuinProbability` has tests for:
- `test_zero_std_positive_ev` (mean > 0, std = 0)
- `test_zero_std_negative_ev` (mean < 0, std = 0)

But no test for `mean_profit == 0` AND `std_profit == 0`, which would return `1.0` per the current logic. This edge case should be explicitly tested and documented.

**Recommendation:** Add `test_zero_std_zero_ev` to verify behavior when both mean and std are zero.

---

### Medium

#### M1. Missing Boundary Tests for Confidence Levels Near 0 and 1

**File:** `/Users/chrishenry/source/let_it_ride/tests/unit/analytics/test_risk_of_ruin.py` (diff lines 2265-2288)

The `TestValidateConfidenceLevel` class tests exact boundaries (0.0 and 1.0) and negative values, but does not test values very close to boundaries that are valid:

```python
def test_valid_confidence_level(self) -> None:
    _validate_confidence_level(0.95)
    _validate_confidence_level(0.90)
    _validate_confidence_level(0.99)
```

Missing tests for boundary-adjacent values like `0.001` and `0.999`.

**Recommendation:** Add tests for extreme but valid confidence levels to ensure numerical stability.

---

#### M2. Missing Test for Single Simulation Count

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py:280`

No test validates behavior with very small `simulations_per_level` (e.g., 1 simulation). While the code should handle this, testing the minimum case ensures robustness.

**Recommendation:** Add a test with `simulations_per_level=1` to verify it does not crash and produces valid (though imprecise) results.

---

#### M3. Hardcoded Confidence Level String Not Tested

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py:406-408`

The format function hardcodes "95% CI" in output:

```python
f"(95% CI: {result.confidence_interval.lower:.2%} - "
```

But the actual confidence level is stored in `result.confidence_interval.level`. No test verifies this discrepancy or ensures the hardcoded value matches expected output.

**Recommendation:** Add a test that uses a non-95% confidence level and verifies the output string correctly reflects (or is documented as always showing "95%").

---

#### M4. No Property-Based Testing for Statistical Invariants

**File:** `/Users/chrishenry/source/let_it_ride/tests/unit/analytics/test_risk_of_ruin.py`

The test file does not use hypothesis for property-based testing. For a statistical calculation module, property-based tests would strengthen coverage by validating:

1. Ruin probability monotonicity (larger bankroll should never increase ruin risk)
2. Threshold ordering (quarter_risk >= half_risk >= ruin_probability)
3. Confidence interval validity (lower <= estimate <= upper)
4. Probabilities always in [0, 1] range

**Recommendation:** Consider adding hypothesis-based tests for statistical invariants as a future enhancement.

---

### Low

#### L1. Missing Integration Test for Full Workflow

No test verifies the complete pipeline: `calculate_risk_of_ruin()` -> `plot_risk_curves()` -> `save_risk_curves()`.

**Recommendation:** Add an integration test that exercises the end-to-end workflow.

---

#### L2. Test Imports Private Functions

**File:** `/Users/chrishenry/source/let_it_ride/tests/unit/analytics/test_risk_of_ruin.py` (diff lines 2061-2072)

The test file imports and tests private functions prefixed with `_`:

```python
from let_it_ride.analytics.risk_of_ruin import (
    _calculate_analytical_ruin_probability,
    _calculate_ruin_for_bankroll_level,
    _run_monte_carlo_ruin_simulation,
    _validate_bankroll_units,
    _validate_confidence_level,
    _validate_session_results,
    ...
)
```

While testing private functions provides good coverage, it couples tests to implementation details. This is acceptable given the functions are well-documented, but worth noting.

---

### Informational (Positive Findings)

#### P1. Excellent Arrange-Act-Assert Pattern

The tests consistently follow the AAA pattern with clear setup, execution, and assertions. Test names are descriptive and follow the `test_<condition>_<expected_result>` convention.

#### P2. Strong Statistical Validation Tests

**File:** `/Users/chrishenry/source/let_it_ride/tests/unit/analytics/test_risk_of_ruin.py` (diff lines 2752-2806)

The `TestConvergenceOfMonteCarloEstimates` class provides excellent validation:
- `test_more_simulations_narrower_ci` - verifies Monte Carlo convergence
- `test_estimate_stability` - verifies reproducibility across seeds

#### P3. Comprehensive Known Scenario Testing

**File:** `/Users/chrishenry/source/let_it_ride/tests/unit/analytics/test_risk_of_ruin.py` (diff lines 2809-2862)

`TestKnownRiskScenarios` tests deterministic edge cases:
- Guaranteed loss (100% ruin)
- Guaranteed win (0% ruin)
- Break-even with high variance

#### P4. Good Numerical Stability Tests

**File:** `/Users/chrishenry/source/let_it_ride/tests/unit/analytics/test_risk_of_ruin.py` (diff lines 2864-2924)

`TestNumericalStability` covers important edge cases:
- Very small profits
- Very large profits
- Constant values (zero variance)

#### P5. Helper Functions Reduce Test Boilerplate

**File:** `/Users/chrishenry/source/let_it_ride/tests/unit/analytics/test_risk_of_ruin.py` (diff lines 2077-2133)

The `create_session_result()` and `create_session_results()` helper functions reduce test boilerplate and improve maintainability.

#### P6. Reproducibility Testing with Seeds

Multiple tests verify that the same random seed produces identical results, ensuring deterministic testing:
- `test_reproducibility_with_seed` in `TestMonteCarloSimulation`
- `test_reproducibility` in `TestCalculateRiskOfRuin`

#### P7. Frozen Dataclass Immutability Tests

Tests verify that `frozen=True` dataclasses raise `AttributeError` on modification attempts (diff lines 2156-2168 and 2199-2210).

---

## Coverage Summary

| Module | Lines | Test Coverage | Test Classes |
|--------|-------|---------------|--------------|
| `risk_of_ruin.py` | 419 | Comprehensive | 13 test classes, 50+ test methods |
| `risk_curves.py` | 260 | **None** | 0 test classes |

## Recommendations

1. **[Critical]** Add unit tests for `risk_curves.py` following the pattern in `test_visualizations.py` for histogram and trajectory modules.

2. **[High]** Add edge case tests for:
   - Zero `base_bet` inference fallback
   - NaN analytical estimate formatting
   - Unsorted bankroll units input
   - Zero mean AND zero std analytical calculation

3. **[Medium]** Add boundary confidence level tests (0.001, 0.999).

4. **[Low]** Consider property-based tests using hypothesis for statistical invariants.

5. **[Low]** Add integration test for the complete workflow pipeline.
