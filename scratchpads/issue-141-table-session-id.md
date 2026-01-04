# Issue 141: LIR-57 Add table_session_id to SessionResult

GitHub Issue: https://github.com/chrishenry/let_it_ride/issues/141

## Summary

Multi-seat table simulations need `table_session_id` tracking to identify which seats shared community cards.

## Implementation Complete ✅

### Changes Made

1. **`SessionResult`** (src/let_it_ride/simulation/session.py):
   - Added `table_session_id: int | None = None` field
   - Updated `to_dict()` to include `table_session_id`
   - Renamed `with_seat_number()` → `with_table_session_info(table_session_id, seat_number)`
   - Added input validation: `table_session_id` must be non-negative, `seat_number` must be 1-6

2. **`SimulationController`** (src/let_it_ride/simulation/controller.py):
   - Updated `_run_sequential()` to use `with_table_session_info()` passing `session_id` as `table_session_id`

3. **`parallel.py`** (src/let_it_ride/simulation/parallel.py):
   - Updated `_run_single_table_session()` to return `SeatSessionResult` directly
   - Updated `run_worker_sessions()` to attach `table_session_id` when processing results

4. **`export_csv.py`** (src/let_it_ride/analytics/export_csv.py):
   - Added `table_session_id` as first field in `SESSION_RESULT_FIELDS`
   - Field order: `table_session_id, seat_number, outcome, ...`

### Tests Updated

- `tests/unit/simulation/test_session.py`: Added tests for `with_table_session_info()` and `to_dict()`
- `tests/unit/analytics/test_chair_position.py`: Updated to use new method
- `tests/integration/test_export_csv.py`: Updated E2E tests for CSV column order, added sync test
- `tests/integration/test_parallel.py`: Added tests for table_session_id grouping semantics
- `tests/integration/test_controller.py`: Added test for single-seat mode (table_session_id = None)

### Verification

- All tests pass
- mypy: No type errors
- ruff: No linting errors
