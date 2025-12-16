# Code Quality Review: PR #143 - LIR-58 Multi-Seat Stop Condition Behavior Options

## Summary

This PR introduces "seat replacement mode" for multi-seat table sessions, where seats that hit individual stop conditions are reset with fresh bankroll rather than sitting out. The implementation is well-structured, maintains backward compatibility with the existing "classic mode," and follows established patterns. The code demonstrates good use of helper methods for result building and clean separation between the two modes. Minor concerns include potential edge cases in stop condition checking order and a few opportunities to improve type safety.

---

## Findings by Severity

### Medium

#### 1. Double Stop Condition Check in `play_round()` May Cause Subtle Issues
**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py` (lines 460-462, 522-524)

In seat replacement mode, `_check_seat_stop_condition()` is called both before and after playing the round. While the intent is to handle seats that just completed a session, this double-checking could cause issues if a seat exactly hits a stop condition (e.g., `max_hands`) and immediately resets before the round is played, potentially leading to off-by-one behavior.

```python
# Before playing round (lines 460-462)
if self.seat_replacement_mode:
    for seat_idx in range(len(self._seat_states)):
        self._check_seat_stop_condition(seat_idx)

# ... play round ...

# After playing round (lines 522-524)
if self.seat_replacement_mode:
    for seat_idx in range(len(self._seat_states)):
        self._check_seat_stop_condition(seat_idx)
```

**Recommendation:** Consider documenting the expected behavior more explicitly, or consolidating to a single check point. The pre-round check seems redundant since stop conditions are checked at the end of the previous round. Verify this does not create edge cases with `max_hands` counting.

---

#### 2. `IN_PROGRESS` as StopReason is Semantically Confusing
**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py` (lines 118-119, 127)

Adding `IN_PROGRESS` to `StopReason` enum is semantically awkward since it represents the absence of a stop condition. A session that is "in progress" has not stopped, yet it is assigned a "stop reason."

```python
class StopReason(Enum):
    ...
    IN_PROGRESS = "in_progress"  # Session is still active
```

**Recommendation:** Consider either:
1. Renaming to `SessionEndReason` to encompass both completed and incomplete states
2. Using `Optional[StopReason]` in `SeatSessionResult` and handling `None` for in-progress sessions
3. Adding a separate `is_complete: bool` field to distinguish complete from in-progress results

---

#### 3. Implicit Ordering Dependency in `seat_results` Population
**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py` (lines 593-596)

In `_build_seat_replacement_result()`, `seat_results` is populated by iterating over `seat_sessions.values()`. Dictionary iteration order is guaranteed in Python 3.7+, but relying on insertion order for seat ordering could be fragile if the dict is ever modified or reconstructed differently.

```python
seat_results: list[SeatSessionResult] = []
for sessions in seat_sessions.values():
    if sessions:
        seat_results.append(sessions[-1])
```

**Recommendation:** Iterate explicitly over seat numbers to ensure deterministic ordering:
```python
for seat_number in sorted(seat_sessions.keys()):
    if seat_sessions[seat_number]:
        seat_results.append(seat_sessions[seat_number][-1])
```

---

### Low

#### 4. Type Annotation Could Be More Precise for `completed_sessions`
**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py` (lines 133-143, 159)

The `__slots__` declaration includes `completed_sessions` and `session_start_round`, but the type annotation is only provided in `__init__`. Adding explicit type comments or a class-level type annotation pattern would improve IDE support and documentation.

```python
__slots__ = (
    ...
    "completed_sessions",
    "session_start_round",
    "_starting_bankroll",
)

def __init__(self, starting_bankroll: float, current_round: int = 0) -> None:
    ...
    self.completed_sessions: list[SeatSessionResult] = []
```

**Recommendation:** This follows the existing pattern in the codebase, so it is acceptable. However, for future consideration, using a typed class variable pattern with `ClassVar` or adding docstrings to `__slots__` would improve discoverability.

---

#### 5. Assertion in `should_stop()` Could Use Narrower Scope
**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py` (line 420)

The assertion `assert self._config.table_total_rounds is not None` is used after checking `seat_replacement_mode`, which already implies `table_total_rounds is not None`. While the assertion helps type narrowing, it duplicates the semantic check.

```python
if self.seat_replacement_mode:
    assert self._config.table_total_rounds is not None
    if self._rounds_played >= self._config.table_total_rounds:
```

**Recommendation:** The assertion is acceptable for type narrowing purposes and follows existing patterns in the codebase. No change required, but consider whether a helper method that returns `int` (raising if None) would be cleaner.

---

#### 6. Test Case Uses `type: ignore` for `completed_sessions` Validation
**File:** `/Users/chrishenry/source/let_it_ride/tests/unit/simulation/test_table_session.py` (line 1300)

The test appends a string to `completed_sessions` with a type ignore comment:

```python
state.completed_sessions.append("dummy_session")  # type: ignore[arg-type]
```

**Recommendation:** While pragmatic for testing, consider creating a minimal valid `SeatSessionResult` fixture instead to maintain type safety in tests. This would also verify that the list properly accepts the expected type.

---

#### 7. Magic Number: Multiplier `3` for Minimum Bet
**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py` (line 283)

The calculation `base_bet * 3` to compute minimum bet required is repeated without a named constant. This was noted in previous reviews (PR #88) and remains unaddressed.

```python
return (self._config.base_bet * 3) + self._config.bonus_bet
```

**Recommendation:** Extract to a module-level constant `BETTING_CIRCLES = 3` for clarity. This is a pre-existing issue, not introduced by this PR.

---

## Positive Observations

1. **Backward Compatibility:** The implementation correctly preserves classic mode behavior when `table_total_rounds` is `None`, with explicit `seat_sessions=None` in classic mode results.

2. **Clean Refactoring:** The extraction of `_build_session_result_for_seat()` eliminates duplication between classic and replacement modes and improves maintainability.

3. **Comprehensive Test Coverage:** The test suite includes 540+ lines of new tests covering configuration validation, multiple stop condition types, independent seat resets, and edge cases like last-round resets.

4. **Clear Documentation:** Module docstrings, class docstrings, and inline comments clearly explain the two modes and their differences.

5. **Proper Use of `__slots__`:** New attributes in `_SeatState` are correctly added to `__slots__` for memory efficiency.

6. **Validation in Dataclass:** `TableSessionConfig.__post_init__` properly validates `table_total_rounds > 0` when set.

7. **Test Class Organization:** Tests are well-organized into semantic groups (`TestTableSessionConfigSeatReplacement`, `TestSeatReplacementMode`, `TestSeatReplacementBackwardsCompatibility`, etc.).

8. **Formatting Improvements:** The PR includes minor formatting fixes to existing test files to comply with ruff standards.

---

## Actionable Recommendations (Prioritized)

1. **Medium Impact:** Review the double stop-condition check in `play_round()` to ensure no edge cases with `max_hands` counting.

2. **Medium Impact:** Consider explicit seat number iteration in `_build_seat_replacement_result()` rather than relying on dict value order.

3. **Low Impact:** For semantic clarity, consider whether `IN_PROGRESS` truly belongs in `StopReason` or warrants a different representation.

4. **Low Impact:** Replace `type: ignore` in test with a proper mock `SeatSessionResult` for better type safety.

---

## Files Reviewed

- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py` (modified, +220 lines, significant feature addition)
- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py` (modified, +8 lines, new StopReason values)
- `/Users/chrishenry/source/let_it_ride/tests/unit/simulation/test_table_session.py` (modified, +540 lines, comprehensive tests)
- `/Users/chrishenry/source/let_it_ride/tests/unit/simulation/test_session.py` (modified, +2 lines, StopReason count update)
- `/Users/chrishenry/source/let_it_ride/tests/integration/test_multi_seat.py` (modified, formatting fixes)
- `/Users/chrishenry/source/let_it_ride/tests/integration/test_parallel.py` (modified, formatting fixes)
- `/Users/chrishenry/source/let_it_ride/tests/unit/cli/test_formatters.py` (modified, formatting fixes)
- `/Users/chrishenry/source/let_it_ride/scratchpads/issue-142-multi-seat-stop-condition.md` (new, design document)
- `/Users/chrishenry/source/let_it_ride/scratchpads/INDEX.md` (modified, index update)
