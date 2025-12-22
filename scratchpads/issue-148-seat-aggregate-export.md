# Issue #148: LIR-61 - Integrate seat-level aggregate CSV export

GitHub Issue: https://github.com/ChrisHenryOC/let_it_ride/issues/148

## Problem

The `export_seat_aggregate_csv()` function exists but isn't integrated into the CLI/output pipeline. Multi-seat simulations can't automatically export per-seat aggregate statistics.

## Key Challenge

`analyze_chair_positions()` expects `list[TableSessionResult]`, but by the time results reach the CLI, they've been flattened into `list[SessionResult]`. However, `SessionResult` now has a `seat_number` field (added in LIR-60/PR #147).

## Solution Approach

Create a new function `analyze_session_results_by_seat()` that works directly with flattened `SessionResult` objects using their `seat_number` field. This avoids changing the data flow architecture.

## Tasks

- [x] Add `include_seat_aggregate` to `CsvOutputConfig` model (default: False)
- [x] Create `analyze_session_results_by_seat()` function in `chair_position.py`
- [x] Add `export_seat_aggregate()` method to `CSVExporter` class
- [x] Update `CSVExporter.export_all()` to call seat aggregate export
- [x] Update CLI to pass config through for seat aggregate export
- [x] Unit tests for config option
- [x] Integration test for end-to-end export

## Files to Modify

1. `src/let_it_ride/config/models.py` - Add `include_seat_aggregate: bool = False`
2. `src/let_it_ride/analytics/chair_position.py` - Add `analyze_session_results_by_seat()`
3. `src/let_it_ride/analytics/export_csv.py` - Update `CSVExporter`
4. `src/let_it_ride/cli/app.py` - Pass through config for export
5. `tests/unit/config/test_models.py` - Test new config option
6. `tests/integration/test_export_csv.py` - Test end-to-end export
