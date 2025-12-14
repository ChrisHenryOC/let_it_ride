# Test Coverage Review - PR #133

## Summary

PR #133 introduces comprehensive unit tests for the risk of ruin calculator module with 874 lines of test code covering 419 lines of implementation. The test file provides excellent coverage of core functionality with strong validation tests, boundary condition tests, and statistical convergence tests. However, there is a critical gap: the `risk_curves.py` visualization module (260 lines) has no dedicated unit tests.

## Coverage Analysis

### `risk_of_ruin.py` (419 lines)

| Function/Class | Test Coverage | Test Class |
|---------------|---------------|------------|
| `RiskOfRuinResult` | Covered | `TestRiskOfRuinResultDataclass` |
| `RiskOfRuinReport` | Covered | `TestRiskOfRuinReportDataclass` |
| `_validate_bankroll_units()` | Covered | `TestValidateBankrollUnits` |
| `_validate_session_results()` | Covered | `TestValidateSessionResults` |
| `_validate_confidence_level()` | Covered | `TestValidateConfidenceLevel` |
| `_calculate_analytical_ruin_probability()` | Covered | `TestAnalyticalRuinProbability` |
| `_run_monte_carlo_ruin_simulation()` | Covered | `TestMonteCarloSimulation` |
| `_calculate_ruin_for_bankroll_level()` | Covered | `TestCalculateRuinForBankrollLevel` |
| `calculate_risk_of_ruin()` | Covered | `TestCalculateRiskOfRuin` |
| `format_risk_of_ruin_report()` | Covered | `TestFormatRiskOfRuinReport` |

### `risk_curves.py` (260 lines)

| Function/Class | Test Coverage | Test Class |
|---------------|---------------|------------|
| `RiskCurveConfig` | NOT COVERED | None |
| `plot_risk_curves()` | NOT COVERED | None |
| `save_risk_curves()` | NOT COVERED | None |

## Findings

### Critical

#### 1. No Tests for `risk_curves.py` Visualization Module
**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/visualizations/risk_curves.py`

The entire visualization module has no unit tests. This is a critical gap given:
- The module is ~260 lines of code with 3 public items exported in `__init__.py`
- Similar visualizations (`histogram.py`, `trajectory.py`) have comprehensive tests in `/Users/chrishenry/source/let_it_ride/tests/integration/test_visualizations.py`
- The module contains validation logic that should be tested (empty report check at line 67-68)
- Configuration options need verification (show_confidence_bands, show_analytical, show_thresholds)

Missing test coverage for:
- `RiskCurveConfig` dataclass default values and custom values
- `plot_risk_curves()` - figure creation, empty results error, custom config, legend contents, axis labels
- `save_risk_curves()` - PNG/SVG output, extension handling, directory creation, invalid format error, custom DPI

### High

#### 2. Missing Test for Zero `base_bet` Inference Edge Case
**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py:327`

When `base_bet` is None and all sessions have `total_hands == 0`, the code would set `base_bet = 1.0`. This fallback behavior is not tested.

```python
# Line 327
estimated_base = total_wagered / (total_hands * 3) if total_hands > 0 else 1.0
```

#### 3. Missing Test for NaN Handling in Analytical Estimates
**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py:365-366`

The code handles `None` from `_calculate_analytical_ruin_probability()` by converting to NaN, but there is no test verifying the returned function can return `None` and that NaN appears correctly in the report.

```python
analytical_estimates.append(
    analytical if analytical is not None else float("nan")
)
```

#### 4. Missing Test for Sorted Bankroll Units Output
**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py:346`

The `test_basic_calculation` test checks that results are sorted, but does not verify behavior when input is unsorted (e.g., `[60, 20, 40]` should produce results in `[20, 40, 60]` order).

### Medium

#### 5. Missing Edge Case: Single Session Result (Boundary at Minimum)
**File:** `/Users/chrishenry/source/let_it_ride/tests/unit/analytics/test_risk_of_ruin.py:1078-1089`

The test verifies that 9 results fail and 10 results pass, but there is no test for `session_profit_std` calculation when exactly 10 results all have identical profits (std would be 0, triggering the zero-variance branch in analytical formula).

#### 6. Missing Test for Analytical Estimate with Zero Mean and Zero Std
**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py:143-145`

There is a test for `zero_std_positive_ev` and `zero_std_negative_ev` but no test for `zero_std_zero_ev` (mean=0, std=0).

```python
if std_profit == 0:
    # No variance means deterministic outcome
    return 0.0 if mean_profit > 0 else 1.0  # What about mean_profit == 0?
```

#### 7. Missing Test for Extremely Large Simulations Count
**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py:280`

No test validates behavior with very small `simulations_per_level` (e.g., 1 simulation) or very large values that might cause memory issues.

#### 8. Missing Test for `format_risk_of_ruin_report` with NaN Analytical Estimates
**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py:414-417`

The formatting code handles NaN values by checking `math.isnan(analytical)`, but there is no test verifying that NaN analytical estimates are properly omitted from the formatted output.

```python
if not math.isnan(analytical):
    lines.append(f"  Analytical Estimate: {analytical:.2%}")
```

#### 9. Missing Boundary Test for Confidence Levels Near 0 and 1
**File:** `/Users/chrishenry/source/let_it_ride/tests/unit/analytics/test_risk_of_ruin.py:1096-1099`

Tests exist for 0.0 and 1.0 (invalid), but no tests for boundary valid values like 0.001 and 0.999.

### Low

#### 10. Hardcoded Confidence Level in Format Output
**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py:406-408`

The formatting function hardcodes "95% CI" regardless of the actual confidence level used. No test verifies this behavior or ensures it matches the actual `confidence_interval.level`.

```python
lines.append(
    f"  Ruin Probability: {result.ruin_probability:.2%} "
    f"(95% CI: {result.confidence_interval.lower:.2%} - "  # Hardcoded "95%"
```

#### 11. Missing Test for Empty `bankroll_units` When Default Used
**File:** `/Users/chrishenry/source/let_it_ride/tests/unit/analytics/test_risk_of_ruin.py:1348-1361`

The `test_default_bankroll_units` test verifies defaults are applied, but no test explicitly passes an empty sequence after the default is set (the validation happens after default assignment).

#### 12. No Property-Based Testing for Statistical Functions
**File:** `/Users/chrishenry/source/let_it_ride/tests/unit/analytics/test_risk_of_ruin.py`

The codebase could benefit from hypothesis-based property tests for:
- Ruin probability monotonicity (larger bankroll should not increase ruin risk)
- Threshold ordering (quarter_risk >= half_risk >= ruin_probability)
- Confidence interval validity (lower <= estimate <= upper)

#### 13. Missing Integration Test Between Risk of Ruin and Visualization
**File:** N/A

No test verifies the end-to-end workflow: `calculate_risk_of_ruin()` -> `plot_risk_curves()` -> `save_risk_curves()`.

### Positive

#### 14. Excellent Arrange-Act-Assert Pattern
The tests consistently follow the AAA pattern with clear setup, execution, and assertions. Test names are descriptive and follow the `test_<condition>_<expected_result>` convention.

#### 15. Strong Statistical Validation Tests
**File:** `/Users/chrishenry/source/let_it_ride/tests/unit/analytics/test_risk_of_ruin.py:1579-1634`

The `TestConvergenceOfMonteCarloEstimates` class provides excellent validation:
- `test_more_simulations_narrower_ci` - verifies Monte Carlo convergence
- `test_estimate_stability` - verifies reproducibility across seeds

#### 16. Comprehensive Known Scenario Testing
**File:** `/Users/chrishenry/source/let_it_ride/tests/unit/analytics/test_risk_of_ruin.py:1636-1689`

`TestKnownRiskScenarios` tests deterministic edge cases:
- Guaranteed loss (100% ruin)
- Guaranteed win (0% ruin)
- Break-even with high variance

#### 17. Good Numerical Stability Tests
**File:** `/Users/chrishenry/source/let_it_ride/tests/unit/analytics/test_risk_of_ruin.py:1691-1751`

`TestNumericalStability` covers important edge cases:
- Very small profits
- Very large profits
- Constant values

#### 18. Helper Functions for Test Data Generation
**File:** `/Users/chrishenry/source/let_it_ride/tests/unit/analytics/test_risk_of_ruin.py:904-960`

The `create_session_result()` and `create_session_results()` helper functions reduce test boilerplate and improve maintainability.

#### 19. Reproducibility Testing with Seeds
**File:** `/Users/chrishenry/source/let_it_ride/tests/unit/analytics/test_risk_of_ruin.py:1226-1246` and `1409-1429`

Multiple tests verify that the same random seed produces identical results, ensuring deterministic testing.

#### 20. Frozen Dataclass Immutability Tests
**File:** `/Users/chrishenry/source/let_it_ride/tests/unit/analytics/test_risk_of_ruin.py:983-995` and `1026-1037`

Tests verify that `frozen=True` dataclasses raise `AttributeError` on modification attempts.

## Recommendations

1. **Add unit tests for `risk_curves.py`** following the pattern in `test_visualizations.py` for histogram and trajectory modules. Create `/Users/chrishenry/source/let_it_ride/tests/unit/analytics/test_risk_curves.py` or add to the integration test file.

2. **Add property-based tests** using hypothesis for statistical invariant validation.

3. **Add test for NaN analytical estimate formatting** to verify the skip behavior works correctly.

4. **Consider fixing the hardcoded "95% CI"** text in `format_risk_of_ruin_report()` to use the actual confidence level from the result.

5. **Add integration test** for the complete workflow from session results through visualization output.
