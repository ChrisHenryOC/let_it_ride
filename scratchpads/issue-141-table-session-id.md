# Issue 141: LIR-57 Add table_session_id to SessionResult

GitHub Issue: https://github.com/chrishenry/let_it_ride/issues/141

## Summary

Multi-seat table simulations need `table_session_id` tracking to identify which seats shared community cards.

## Implementation Complete ✅

### Changes Made

1. **`SessionResult`** (session.py):
   - Added `table_session_id: int | None = None` field
   - Updated `to_dict()` to include `table_session_id`
   - Renamed `with_seat_number()` → `with_table_session_info(table_session_id, seat_number)`

2. **`controller.py`**:
   - Updated to use `with_table_session_info()` passing `session_id` as `table_session_id`

3. **`parallel.py`**:
   - Updated `_run_single_table_session()` to return `SeatSessionResult` directly
   - Updated `run_worker_sessions()` to attach `table_session_id` when processing results

4. **`export_csv.py`**:
   - Added `table_session_id` as first field in `SESSION_RESULT_FIELDS`
   - Field order: `table_session_id, seat_number, outcome, ...`

### Tests Updated

- `tests/unit/simulation/test_session.py`: Added tests for `with_table_session_info()` and `to_dict()`
- `tests/unit/analytics/test_chair_position.py`: Updated to use new method
- `tests/integration/test_export_csv.py`: Updated E2E tests for CSV column order

### Verification

- All 2551 tests pass (1 unrelated failure in README validation)
- mypy: No type errors
- ruff: No linting errors
