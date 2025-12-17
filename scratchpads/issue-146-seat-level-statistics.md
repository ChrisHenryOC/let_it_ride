# Issue #146 (LIR-60): Seat-Level Statistics Missing from Multi-Seat Simulation Output

GitHub: https://github.com/ChrisHenryOC/let_it_ride/issues/146

## Problem
Multi-seat simulations lose seat_number when extracting results in SimulationController. The CSV export has no seat_number column.

## Tasks
1. [x] Add `seat_number: int | None` field to SessionResult dataclass
2. [x] Update SimulationController to preserve seat_number when extracting results
3. [x] Update CSV export with seat_number column in SESSION_RESULT_FIELDS
4. [x] Add export_seat_aggregate_csv function for per-seat statistics
5. [x] Write unit tests for seat-level export functionality
6. [x] Run tests, lint, and type check

## Implementation Summary

### SessionResult Changes (session.py)
- Added `seat_number: int | None = None` field to SessionResult dataclass
- Updated `to_dict()` to include seat_number as first field
- Added `with_seat_number()` method to create copy with seat number assigned
- Default None for single-seat sessions

### Controller Changes (controller.py and parallel.py)
- Updated `_run_sequential()` to use `seat_result.session_result.with_seat_number()`
- Updated `_run_single_table_session()` in parallel.py similarly
- Both sequential and parallel execution now preserve seat numbers

### CSV Export Changes (export_csv.py)
- Added "seat_number" as first field in SESSION_RESULT_FIELDS
- Added SEAT_AGGREGATE_FIELDS list for seat statistics
- Added `export_seat_aggregate_csv()` function:
  - Exports per-seat statistics (win rate, CI, profit)
  - Includes summary row with chi-square test results
  - Validates non-empty seat statistics

### Analytics Module (__init__.py)
- Exported `export_seat_aggregate_csv` function

## Files Modified
- src/let_it_ride/simulation/session.py
- src/let_it_ride/simulation/controller.py
- src/let_it_ride/simulation/parallel.py
- src/let_it_ride/analytics/export_csv.py
- src/let_it_ride/analytics/__init__.py
- tests/integration/test_export_csv.py

## Test Coverage
- TestSeatNumberInSessionResult: 7 tests for SessionResult seat_number field
- TestExportSeatAggregateCsv: 9 tests for seat aggregate CSV export
- All 2521 tests pass, 98% code coverage
