# LIR-58: Multi-Seat Stop Condition Behavior Options

GitHub Issue: https://github.com/ChrisHenryOC/let_it_ride/issues/142

## Summary

When a player at a multi-seat table hits their individual stop condition, instead of "sitting out" while others continue, reset the seat with a fresh bankroll (simulating a new player sitting down).

## Current Behavior

- Seats stop individually via `is_stopped` flag
- Stopped seats skip rounds (`play_round` line 348-350)
- Table continues until **all seats** hit stop conditions
- No replacement/reset mechanism

## New Behavior: Seat Replacement

When a seat hits its stop condition:
1. Record the completed session result for that seat
2. Reset the seat with fresh bankroll and state
3. Continue playing with new "player"
4. Track multiple sessions per seat position

The table runs for a configurable number of **total rounds** rather than waiting for all seats to stop.

## Design Decisions

### 1. Table-Level Stop Condition

Add `table_total_rounds` to `TableSessionConfig`:
- Table stops when this many total rounds have been played
- Individual seat stop conditions still apply (they trigger seat reset)
- This replaces the "all seats stopped" logic

### 2. _SeatState Changes

Add to `_SeatState`:
- `completed_sessions: list[SeatSessionResult]` - track finished sessions
- `session_start_round: int` - when current session started (for hands_played)
- `reset()` method - start fresh session in seat

### 3. _check_seat_stop_condition Changes

When a seat hits a stop condition:
- Build `SeatSessionResult` from current state
- Append to `completed_sessions`
- Call `reset()` to start new session
- Clear `stop_reason` so seat continues

### 4. TableSessionResult Changes

Change from single result per seat to list:
```python
@dataclass
class TableSessionResult:
    total_rounds: int
    seat_sessions: dict[int, list[SeatSessionResult]]  # seat_number -> sessions
    stop_reason: StopReason  # Always TABLE_ROUNDS_COMPLETE
```

Add new `StopReason.TABLE_ROUNDS_COMPLETE`.

### 5. should_stop() Changes

Change from "all seats stopped" to "total rounds reached":
```python
def should_stop(self) -> bool:
    if self._config.table_total_rounds is not None:
        return self._rounds_played >= self._config.table_total_rounds
    # Fall back to all-seats-stopped for backward compat
    return self._all_seats_stopped()
```

## Implementation Steps

1. Add `table_total_rounds: int | None` to `TableSessionConfig`
2. Add `TABLE_ROUNDS_COMPLETE` to `StopReason` enum
3. Modify `_SeatState`:
   - Add `completed_sessions: list[SeatSessionResult]`
   - Add `session_start_round: int`
   - Add `reset(starting_bankroll, current_round)` method
4. Modify `_check_seat_stop_condition()`:
   - When stop condition met, save result and reset
5. Modify `should_stop()`:
   - Check `table_total_rounds` first
   - Fall back to `_all_seats_stopped()` if not set
6. Modify `run_to_completion()`:
   - Build results from `completed_sessions` plus any in-progress sessions
7. Update tests

## Backwards Compatibility

- If `table_total_rounds` is None, use existing "all seats stop" behavior
- Single-seat tables with `max_hands` behave same as before
- Existing configs work unchanged

## Files to Modify

- `src/let_it_ride/simulation/table_session.py` - main changes
- `src/let_it_ride/simulation/session.py` - add TABLE_ROUNDS_COMPLETE to StopReason
- `tests/unit/simulation/test_table_session.py` - add seat replacement tests
