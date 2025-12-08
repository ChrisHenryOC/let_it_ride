# Test Coverage Review - PR #113

## Summary

This PR adds a comprehensive statistics calculator module (`analytics/statistics.py`) with 45 unit tests providing strong coverage of the core statistical calculations. The test suite demonstrates good coverage of happy paths, edge cases, and numerical stability. A few areas could benefit from additional testing, particularly around confidence interval boundary conditions, property-based testing opportunities, and cross-validation with scipy reference implementations.

## Findings

### Critical

None

### High

**H1. Missing Test for Empty session_profits in AggregateStatistics**
- File: `tests/unit/analytics/test_statistics.py`
- Issue: The `calculate_statistics()` function raises `ValueError` when `session_profits` is empty (line 547 of statistics.py), but the test `test_zero_sessions_raises_error` only tests the `total_sessions <= 0` condition. There is no explicit test verifying the error path at line 547.
- Risk: The two error conditions (`total_sessions <= 0` and empty `session_profits`) are checked separately but only one is explicitly tested.
- Recommendation: Add a test case where `total_sessions > 0` but `session_profits` is an empty tuple to ensure both validation paths are covered.

### Medium

**M1. Skewness and Kurtosis Calculations Lack Reference Validation**
- File: `tests/unit/analytics/test_statistics.py:797-896`
- Issue: The skewness and kurtosis tests verify behavior qualitatively (positive/negative direction, edge cases) but do not validate against known reference values or scipy's implementation.
- Risk: Subtle bugs in the Fisher-Pearson adjustment formulas would not be detected.
- Recommendation: Add tests comparing `_calculate_skewness` and `_calculate_kurtosis` results against `scipy.stats.skew` and `scipy.stats.kurtosis` for known datasets.

**M2. Confidence Interval t-Distribution Critical Value Not Validated**
- File: `tests/unit/analytics/test_statistics.py:1006-1056`
- Issue: The mean confidence interval tests verify structural properties (wider with higher confidence, narrower with more data) but do not validate the actual calculated bounds against expected values.
- Risk: An error in the t-critical value lookup or margin calculation would not be caught.
- Recommendation: Add a test with a small known dataset (e.g., n=10) where the CI bounds can be manually calculated and verified.

**M3. Risk Metrics Boundary Conditions for Loss Thresholds**
- File: `tests/unit/analytics/test_statistics.py:1058-1126`
- Issue: The `prob_loss_50pct` and `prob_loss_100pct` calculations use `<=` comparisons but tests do not verify exact boundary behavior (e.g., a loss of exactly 50% vs 50.01%).
- Risk: Off-by-one errors in threshold comparisons.
- Recommendation: Add tests with profits exactly at the -50% and -100% thresholds to verify inclusive boundary behavior.

**M4. Missing Test for Custom Percentiles Including Edge Values (0, 100)**
- File: `src/let_it_ride/analytics/statistics.py:343-351`
- Issue: The `_calculate_percentiles` function has special handling for percentiles 0 and 100 (returning min/max), but this is not tested.
- Risk: The special case handling for 0th and 100th percentiles may have bugs.
- Recommendation: Add a test case requesting percentiles `(0, 50, 100)` to verify boundary handling.

### Low

**L1. No Property-Based Testing with Hypothesis**
- File: `tests/unit/analytics/test_statistics.py`
- Issue: Given the statistical nature of this module, property-based testing would be valuable for finding edge cases in numerical computations.
- Recommendation: Consider adding hypothesis-based tests for properties like:
  - Mean CI always contains the actual mean for reasonable confidence levels
  - Distribution stats maintain consistency (e.g., `iqr == percentiles[75] - percentiles[25]`)
  - Skewness is bounded when data is finite

**L2. Test Helper Functions Could Use Validation**
- File: `tests/unit/analytics/test_statistics.py:657-741`
- Issue: The `create_aggregate_statistics` helper manually calculates some fields (like `session_win_rate`) that could diverge from the actual `AggregateStatistics` dataclass behavior.
- Risk: Tests may pass with incorrect helper values that would fail with real data.
- Recommendation: Consider using the actual `aggregate_results()` function where feasible to ensure test data matches production behavior.

**L3. Missing Test for Zero Starting Bankroll in Risk Metrics**
- File: `src/let_it_ride/analytics/statistics.py:479-486`
- Issue: When `starting_bankroll` is 0 or not provided, `prob_loss_50pct` and `prob_loss_100pct` default to 0.0. This behavior is not explicitly tested.
- Recommendation: Add a test verifying risk metrics behavior when `starting_bankroll=0.0`.

**L4. Integration Test Coverage Limited to Single Code Path**
- File: `tests/unit/analytics/test_statistics.py:1333-1395`
- Issue: The `TestIntegrationWithAggregation` class has only one test covering the happy path. No integration tests for error conditions or edge cases.
- Recommendation: Consider adding integration tests for empty results, single result, and very large result sets.

## Recommendations

### Immediate Actions (Before Merge)

1. **Add reference validation for skewness/kurtosis** (M1):
```python
def test_skewness_matches_scipy(self) -> None:
    """Verify skewness matches scipy.stats.skew."""
    from scipy import stats as scipy_stats
    data = (1.0, 2.0, 2.0, 3.0, 3.0, 3.0, 10.0, 20.0)
    from statistics import mean, stdev
    data_mean = mean(data)
    data_std = stdev(data)
    expected = scipy_stats.skew(data, bias=False)  # Fisher-Pearson
    actual = _calculate_skewness(data, data_mean, data_std)
    assert abs(actual - expected) < 0.01
```

2. **Add boundary test for risk metric thresholds** (M3):
```python
def test_loss_threshold_boundary_exact_50pct(self) -> None:
    """Exactly 50% loss should count toward prob_loss_50pct."""
    profits = (-500.0, -499.99, 100.0)  # First is exactly 50%, second is not
    risk = _calculate_risk_metrics(
        session_profits=profits, starting_bankroll=1000.0
    )
    assert risk.prob_loss_50pct == 1/3  # Only -500.0 qualifies
```

3. **Add test for percentile edge values** (M4):
```python
def test_percentile_0_and_100(self) -> None:
    """Percentiles 0 and 100 should return min and max."""
    data = (5.0, 10.0, 15.0, 20.0, 25.0)
    percentiles = _calculate_percentiles(data, (0, 50, 100))
    assert percentiles[0] == 5.0   # min
    assert percentiles[100] == 25.0  # max
```

### Future Improvements

1. **Add property-based tests using hypothesis** for statistical invariants
2. **Add deterministic tests with fixed seeds** for reproducibility
3. **Consider adding statistical accuracy tests** that verify convergence to theoretical values with large synthetic datasets
4. **Add performance benchmarks** to ensure statistics calculation meets the project's throughput targets

## Test Coverage Summary

| Component | Coverage | Notes |
|-----------|----------|-------|
| ConfidenceInterval dataclass | Excellent | Immutability and creation tested |
| DistributionStats dataclass | Excellent | Immutability and creation tested |
| RiskMetrics dataclass | Good | Used implicitly, no standalone tests |
| DetailedStatistics dataclass | Good | Used implicitly, no standalone tests |
| `_calculate_skewness` | Good | Qualitative tests, lacks reference validation |
| `_calculate_kurtosis` | Good | Qualitative tests, lacks reference validation |
| `_calculate_percentiles` | Good | Missing 0/100 edge cases |
| `_calculate_distribution_stats` | Excellent | Known dataset, edge cases covered |
| `_calculate_mean_confidence_interval` | Good | Property tests, lacks value validation |
| `_calculate_risk_metrics` | Good | Basic paths covered, boundary gaps |
| `calculate_statistics` | Excellent | Multiple scenarios covered |
| `calculate_statistics_from_results` | Good | Basic usage and error cases |
| Numerical stability | Excellent | Large/small values tested |
| Integration | Adequate | Single happy path test |

Overall, this is a well-tested module with comprehensive coverage of the main statistical calculations. The identified gaps are relatively minor and represent opportunities to strengthen confidence in edge case behavior rather than fundamental coverage deficiencies.
