# Performance Review: PR #143 - LIR-58 Multi-Seat Stop Condition Behavior Options

## Summary

This PR adds seat replacement mode to `TableSession`, enabling seats to reset with fresh bankroll when hitting stop conditions. The implementation is generally efficient, using `__slots__` appropriately on `_SeatState` and avoiding unnecessary allocations in the hot path. However, there are several performance considerations around redundant stop condition checks, object creation during resets, and list operations that could impact the 100,000 hands/second throughput target at scale.

---

## Findings by Severity

### High

#### H1: Redundant Stop Condition Checks Per Round in Seat Replacement Mode

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py`
**Lines:** 460-462, 522-524

In seat replacement mode, `_check_seat_stop_condition()` is called for every seat **both before and after** playing a round:

```python
# Line 460-462 (before playing)
if self.seat_replacement_mode:
    for seat_idx in range(len(self._seat_states)):
        self._check_seat_stop_condition(seat_idx)

# Line 522-524 (after playing)
if self.seat_replacement_mode:
    for seat_idx in range(len(self._seat_states)):
        self._check_seat_stop_condition(seat_idx)
```

For a 6-seat table running 10M rounds, this results in 120M extra method calls that may be unnecessary. The pre-round check appears intended to handle seats that were just reset, but a seat just reset will have no stop condition until after playing.

**Impact:** For the 100k hands/second target, this overhead is measurable. Each check involves property access, method calls, and conditional branches.

**Recommendation:** Consider removing the pre-round check or restructuring to check only after playing, with the reset logic moved to ensure the next round sees a clean state.

---

### Medium

#### M1: BankrollTracker Object Recreation on Every Seat Reset

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py`
**Line:** 195

```python
def reset(self, current_round: int) -> None:
    self.bankroll = BankrollTracker(self._starting_bankroll)
    # ...
```

On each seat reset, a new `BankrollTracker` object is created. In high-churn scenarios (e.g., low `win_limit` with many resets per table), this creates allocation pressure.

**Impact:** With `max_hands=2` and `table_total_rounds=1M`, a single seat could reset 500k times, creating 500k `BankrollTracker` objects.

**Recommendation:** Consider adding a `BankrollTracker.reset()` method that reinitializes internal state without creating a new object, or document that seat replacement mode is designed for realistic casino simulation (where resets are infrequent) rather than stress testing.

---

#### M2: List Copy in _build_seat_replacement_result

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py`
**Line:** 581

```python
sessions = list(seat_state.completed_sessions)
```

This creates a copy of the completed sessions list for each seat. While this only happens once at session end, if a seat has many completed sessions (thousands), this creates unnecessary memory allocation.

**Impact:** Minor for typical use cases. Could matter if `table_total_rounds` is very high with frequent resets.

**Recommendation:** If mutation is not needed, iterate directly over `seat_state.completed_sessions` and build `seat_sessions[seat_number]` incrementally, or use `seat_state.completed_sessions[:]` for a potentially faster shallow copy.

---

#### M3: Repeated Property Access for seat_replacement_mode

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py`
**Lines:** 460, 522, 540

The `seat_replacement_mode` property is accessed multiple times per round:

```python
@property
def seat_replacement_mode(self) -> bool:
    return self._config.table_total_rounds is not None
```

While property access in Python is fast, this involves attribute lookup on `self`, then `_config`, then `table_total_rounds`, plus the `is not None` check.

**Impact:** Minimal but accumulates over millions of rounds.

**Recommendation:** Cache the mode in `__init__` as `self._seat_replacement_mode = config.table_total_rounds is not None`.

---

### Low

#### L1: Generator Expression in _all_seats_stopped Could Short-Circuit Better

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py`
**Line:** 404

```python
return all(seat.is_stopped for seat in self._seat_states)
```

This is already efficient due to `all()` short-circuiting. No change needed; included for completeness.

---

#### L2: completed_sessions List Grows Unbounded in Long Simulations

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py`
**Line:** 159, 385

```python
self.completed_sessions: list[SeatSessionResult] = []
# ...
seat_state.completed_sessions.append(result)
```

Each `SeatSessionResult` contains a `SessionResult` dataclass with 11 fields. In extreme scenarios with many resets, this list grows unbounded.

**Impact:** For the 4GB memory budget with 10M hands, this should be monitored. Each `SeatSessionResult` is approximately 200-300 bytes. 100k resets per seat with 6 seats would consume ~180MB.

**Recommendation:** Consider an optional streaming/callback mode for seat replacement results if memory becomes a concern in extreme scenarios.

---

#### L3: SeatSessionResult Dataclass Creation in Hot Path

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py`
**Lines:** 284-329

`_build_session_result_for_seat()` creates multiple dataclass instances (`SessionResult`, `SeatSessionResult`). This is called on every reset. The dataclasses use `frozen=True, slots=True` which is optimal.

**Impact:** Acceptable given the dataclasses are properly configured with `__slots__`.

---

#### L4: Iteration Pattern Uses range(len()) Instead of enumerate()

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py`
**Lines:** 427, 461, 523

```python
for seat_idx in range(len(self._seat_states)):
    self._check_seat_stop_condition(seat_idx)
```

While functionally correct, `enumerate()` is generally preferred for readability. Performance difference is negligible.

---

## Performance Target Assessment

| Target | Status | Notes |
|--------|--------|-------|
| 100,000 hands/second | **LIKELY MET** | Core changes add minimal overhead per hand. Redundant checks (H1) are the main concern. |
| <4GB RAM for 10M hands | **MET** | `completed_sessions` growth is bounded by reset frequency. Typical scenarios well under budget. |

---

## Recommendations Summary

1. **High Priority:** Eliminate redundant pre-round stop condition checks in seat replacement mode (H1)
2. **Medium Priority:** Consider `BankrollTracker.reset()` method to avoid object churn (M1)
3. **Medium Priority:** Cache `seat_replacement_mode` boolean in `__init__` (M3)
4. **Low Priority:** Monitor memory usage in extreme reset scenarios (L2)
