## Summary

PR 149 adds seat-level aggregate CSV export integration with good test coverage for the happy path scenarios. The tests cover the new `analyze_session_results_by_seat()` function, `CsvOutputConfig.include_seat_aggregate` configuration option, and `export_all()` integration. However, there are gaps in edge case coverage for error handling paths and missing tests for the `export_seat_aggregate()` method on `CSVExporter`.

## Findings

### Critical

No critical issues identified.

### High

**[H1] Missing unit test for `CSVExporter.export_seat_aggregate()` method directly**

The new `export_seat_aggregate()` method on `CSVExporter` (line 313-325 in `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/export_csv.py`) is only tested indirectly through `export_all()`. There should be direct unit tests for this method similar to how `export_sessions()`, `export_aggregate()`, and `export_hands()` have their own tests in `TestCSVExporter`.

```python
# /Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/export_csv.py:313-325
def export_seat_aggregate(self, analysis: ChairPositionAnalysis) -> Path:
    """Export per-seat aggregate statistics to CSV."""
    self._ensure_output_dir()
    path = self._output_dir / f"{self._prefix}_seat_aggregate.csv"
    export_seat_aggregate_csv(analysis, path, self._include_bom)
    return path
```

Missing tests:
- `test_export_seat_aggregate` verifying file path and existence
- `test_export_seat_aggregate_with_custom_prefix`
- `test_export_seat_aggregate_bom_setting`

**[H2] No test for error propagation from `analyze_session_results_by_seat()` in `export_all()`**

The `export_all()` method calls `analyze_session_results_by_seat()` which can raise `ValueError` for empty results or missing seat data. There are no tests verifying that these errors propagate correctly through `export_all()`.

```python
# /Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/export_csv.py:378-381
if include_seat_aggregate and num_seats > 1:
    analysis = analyze_session_results_by_seat(results.session_results)
    seat_aggregate_path = self.export_seat_aggregate(analysis)
    created_files.append(seat_aggregate_path)
```

Missing test scenarios:
- `test_export_all_with_seat_aggregate_empty_results_raises`
- `test_export_all_with_seat_aggregate_no_seat_data_raises`

### Medium

**[M1] Missing test for PUSH outcome in `_aggregate_session_results_by_seat()`**

The unit tests for `_aggregate_session_results_by_seat()` in `/Users/chrishenry/source/let_it_ride/tests/unit/analytics/test_chair_position.py` (lines 672-709) only test WIN and LOSS outcomes. The PUSH path is not exercised.

```python
# /Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/chair_position.py:295-300
if result.outcome == SessionOutcome.WIN:
    agg.wins += 1
elif result.outcome == SessionOutcome.LOSS:
    agg.losses += 1
elif result.outcome == SessionOutcome.PUSH:
    agg.pushes += 1
```

**[M2] No test for `confidence_level` and `significance_level` parameters in `analyze_session_results_by_seat()`**

While the existing `TestAnalyzeChairPositions` class has tests for these parameters (`test_confidence_level_parameter` and `test_significance_level_parameter`), the new `TestAnalyzeSessionResultsBySeat` class does not verify these work correctly.

```python
# /Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/chair_position.py:307-311
def analyze_session_results_by_seat(
    results: list[SessionResult],
    confidence_level: float = 0.95,
    significance_level: float = 0.05,
) -> ChairPositionAnalysis:
```

**[M3] Integration test does not verify computed statistical values**

The integration test `test_export_all_with_seat_aggregate_multi_seat` in `/Users/chrishenry/source/let_it_ride/tests/integration/test_export_csv.py` (lines 1346-1470) verifies the file structure but does not validate that the computed statistics (win_rate, expected_value, etc.) are correct for the test data.

```python
# Lines 1463-1470 - only checks structure, not computed values
assert rows[0]["seat_number"] == "1"
assert rows[1]["seat_number"] == "2"
assert rows[2]["seat_number"] == "SUMMARY"
assert rows[2]["chi_square_statistic"] != ""
assert rows[2]["chi_square_p_value"] != ""
```

### Low

**[L1] Test `test_consistent_with_analyze_chair_positions` does not verify all statistics**

The consistency test in `/Users/chrishenry/source/let_it_ride/tests/unit/analytics/test_chair_position.py` (lines 749-792) compares only a subset of statistics between the two analysis methods.

```python
# Lines 775-792 - missing comparisons for:
# - pushes
# - total_rounds
# - win_rate_ci_lower
# - win_rate_ci_upper
# - expected_value
# - total_profit
```

**[L2] No boundary value tests for seat numbers in aggregation**

The `_aggregate_session_results_by_seat()` function does not have tests verifying behavior with boundary seat numbers (e.g., seat 1 and seat 6 being the min/max valid values).

**[L3] Missing test for seats not starting at 1**

The tests assume seat numbers are contiguous starting at 1. There is no test for non-contiguous seat numbers (e.g., seats 2, 4, 6 only) which the implementation would handle but is not explicitly tested.

```python
# Test case that should be added:
def test_non_contiguous_seat_numbers(self) -> None:
    """Test aggregation with non-contiguous seat numbers."""
    results = [
        create_session_result(profit=100.0).with_seat_number(2),
        create_session_result(profit=-50.0).with_seat_number(4),
        create_session_result(profit=200.0).with_seat_number(6),
    ]
    aggregations = _aggregate_session_results_by_seat(results)
    assert set(aggregations.keys()) == {2, 4, 6}
```

**[L4] No determinism test with fixed seed for chi-square calculation**

The statistical tests in `TestAnalyzeSessionResultsBySeat` do not use fixed seeds. While the current tests pass with small sample sizes, adding a determinism test with a fixed seed would make the test more robust.
