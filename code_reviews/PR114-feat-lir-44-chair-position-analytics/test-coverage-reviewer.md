# Test Coverage Review: PR114 - LIR-44 Chair Position Analytics

## Summary

The test suite for chair position analytics is comprehensive and well-structured, covering the core functionality, edge cases, and statistical validation. The tests follow good practices with clear organization, proper use of factory functions, and thorough assertions. However, there are a few gaps in coverage related to integration testing, parameter validation edge cases, and a missing test for the second error path in `analyze_chair_positions`.

## Findings by Severity

### Medium

#### M1: Missing Integration Test for Chair Position Analytics with Real TableSession
**File:** `tests/unit/analytics/test_chair_position.py`
**Impact:** Integration coverage gap

The unit tests use hand-crafted `TableSessionResult` objects via factory functions, but there is no integration test that verifies `analyze_chair_positions()` works correctly with actual `TableSessionResult` objects produced by `TableSession.run_to_completion()`. This could miss data structure mismatches or unexpected field values in real simulation data.

**Recommendation:** Add an integration test in `tests/integration/test_table.py` that:
1. Runs a multi-seat TableSession to completion
2. Passes the results to `analyze_chair_positions()`
3. Verifies the analysis produces valid results

```python
def test_chair_position_analytics_integration(
    self,
    main_paytable: MainGamePaytable,
    rng: random.Random,
) -> None:
    """Verify analyze_chair_positions works with real TableSession results."""
    from let_it_ride.analytics import analyze_chair_positions

    table_config = TableConfig(num_seats=4)
    config = TableSessionConfig(
        table_config=table_config,
        starting_bankroll=500.0,
        base_bet=5.0,
        max_hands=20,
    )
    # ... create table and run sessions ...

    results = [session.run_to_completion() for _ in range(10)]
    analysis = analyze_chair_positions(results)

    assert len(analysis.seat_statistics) == 4
    assert all(s.total_rounds == 10 for s in analysis.seat_statistics)
```

---

#### M2: Missing Test for "No Seat Data Found" Error Path
**File:** `tests/unit/analytics/test_chair_position.py`
**Line Reference:** `src/let_it_ride/analytics/chair_position.py:244-245`
**Impact:** Error path not covered

The `analyze_chair_positions()` function has two distinct error paths:
1. Empty results list (line 238-239) - **tested** in `test_empty_results_raises_error`
2. No seat data found in results (line 244-245) - **NOT tested**

The second error path can occur when results contain `TableSessionResult` objects with empty `seat_results` tuples.

**Recommendation:** Add test case:

```python
def test_results_with_no_seat_data_raises_error(self) -> None:
    """Results with empty seat_results should raise ValueError."""
    # Create TableSessionResult with empty seat_results
    empty_result = TableSessionResult(
        seat_results=(),
        total_rounds=50,
        stop_reason=StopReason.MAX_HANDS,
    )
    with pytest.raises(ValueError, match="No seat data"):
        analyze_chair_positions([empty_result])
```

---

### Low

#### L1: No Test for Empty Seat Stats List in `_test_seat_independence`
**File:** `tests/unit/analytics/test_chair_position.py`
**Line Reference:** `src/let_it_ride/analytics/chair_position.py:189`
**Impact:** Minor edge case not covered

The `_test_seat_independence()` function handles the case where `len(seat_stats) < 2`, returning default values. The test `test_single_seat` covers the single-seat case, but there is no test for an empty list.

**Recommendation:** Add test case:

```python
def test_empty_seat_stats(self) -> None:
    """Empty seat stats should return default values."""
    chi_sq, p_val, is_indep = _test_seat_independence([], 0.05)
    assert chi_sq == 0.0
    assert p_val == 1.0
    assert is_indep is True
```

---

#### L2: Test Factory Function Overrides Outcome Parameter
**File:** `tests/unit/analytics/test_chair_position.py:468-479`
**Impact:** Test helper may behave unexpectedly

The `create_session_result()` factory function accepts an `outcome` parameter but immediately overrides it based on the `profit` value (lines 474-479). This could lead to confusion when tests pass an explicit `outcome` that gets ignored.

**Recommendation:** Either:
1. Remove the `outcome` parameter since it's not used, or
2. Only derive outcome from profit when `outcome` is not explicitly provided:

```python
def create_session_result(
    *,
    outcome: SessionOutcome | None = None,
    profit: float = 100.0,
    hands_played: int = 50,
) -> SessionResult:
    if outcome is None:
        if profit > 0:
            outcome = SessionOutcome.WIN
        elif profit < 0:
            outcome = SessionOutcome.LOSS
        else:
            outcome = SessionOutcome.PUSH
    # ...
```

---

#### L3: No Test for Invalid Parameter Values
**File:** `tests/unit/analytics/test_chair_position.py`
**Impact:** Input validation not verified

The `analyze_chair_positions()` function accepts `confidence_level` and `significance_level` parameters but there are no tests verifying behavior with invalid values (e.g., negative confidence level, significance level > 1.0). While `calculate_wilson_confidence_interval` may handle some of these, edge cases should be explicitly tested.

**Recommendation:** Add parameter validation tests:

```python
@pytest.mark.parametrize(
    "confidence_level,significance_level",
    [
        (-0.1, 0.05),  # negative confidence
        (1.5, 0.05),   # confidence > 1
        (0.95, -0.1),  # negative significance
        (0.95, 1.5),   # significance > 1
    ],
)
def test_invalid_parameter_values(
    self, confidence_level: float, significance_level: float
) -> None:
    """Invalid parameter values should raise or produce reasonable output."""
    results = [create_table_session_result([(1, SessionOutcome.WIN, 100.0)])]
    # Document expected behavior for invalid parameters
    # Either raise ValueError or clamp to valid range
```

---

#### L4: Confidence Interval Test Does Not Verify Actual Values
**File:** `tests/unit/analytics/test_chair_position.py:713-727`
**Impact:** Test assertions could be stronger

The `test_win_rate_confidence_interval` test verifies that the CI contains the point estimate and is within (0, 1), but does not verify the actual interval values match expected Wilson score calculations. This could miss calculation bugs.

**Recommendation:** Add verification against known Wilson CI values:

```python
def test_win_rate_ci_matches_wilson_calculation(self) -> None:
    """Wilson CI should match expected values for known inputs."""
    agg = _SeatAggregation()
    agg.wins = 30
    agg.losses = 70

    stats = _calculate_seat_statistics(1, agg, 0.95)

    # Expected Wilson CI for 30/100 successes at 95% confidence
    # Calculated independently: approximately (0.215, 0.404)
    assert 0.21 < stats.win_rate_ci_lower < 0.22
    assert 0.40 < stats.win_rate_ci_upper < 0.41
```

---

## Positive Observations

1. **Well-Organized Test Structure**: Tests are grouped logically into classes by component (`TestSeatStatisticsDataclass`, `TestAggregateSeatData`, `TestAnalyzeChairPositions`, etc.)

2. **Comprehensive Edge Cases**: Tests cover zero rounds, all wins, all losses, single seat, no wins, uniform distribution, and biased distribution scenarios

3. **Proper Use of Factory Functions**: The `create_table_session_result()` and `create_session_result()` helpers reduce boilerplate and make tests readable

4. **Deterministic Seeding**: Integration tests like `test_realistic_simulation_uniform` and `test_realistic_simulation_biased` use fixed seeds for reproducibility

5. **Statistical Assertions**: Tests verify chi-square behavior for both uniform (should pass independence test) and biased (should fail independence test) distributions

6. **Immutability Tests**: Tests verify that dataclasses are properly frozen (`test_immutability` tests)

7. **Parameter Variation Tests**: Tests for `confidence_level_parameter` and `significance_level_parameter` verify that parameters affect output appropriately

---

## Recommendations Summary

| Priority | Issue | Effort |
|----------|-------|--------|
| Medium | Add integration test with real TableSession | ~30 min |
| Medium | Add test for "No seat data found" error path | ~10 min |
| Low | Add test for empty seat stats list | ~5 min |
| Low | Fix factory function outcome override | ~10 min |
| Low | Add invalid parameter tests | ~15 min |
| Low | Add Wilson CI value verification | ~10 min |

---

## Test Coverage Metrics

| Component | Coverage |
|-----------|----------|
| `SeatStatistics` dataclass | Complete |
| `ChairPositionAnalysis` dataclass | Complete |
| `_SeatAggregation` class | Complete |
| `_aggregate_seat_data()` | Complete |
| `_calculate_seat_statistics()` | Complete |
| `_test_seat_independence()` | Near-complete (missing empty list) |
| `analyze_chair_positions()` | Near-complete (missing one error path) |
| Integration with real TableSession | Missing |
