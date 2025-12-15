# Performance Review: PR #140 - LIR-56 Table Configuration Integration with CLI

## Summary

This PR integrates multi-seat table configuration into the simulation controller and parallel executor. The changes are largely low-risk from a performance standpoint, with appropriate use of conditional branching to preserve single-seat performance. However, there are several inefficiencies in the multi-seat path including redundant computations per session and per-seat object allocation overhead that could impact the 100,000 hands/second throughput target when running multi-seat simulations.

---

## Findings

### Medium

#### M1: Redundant `calculate_bonus_bet()` and `create_table_session_config()` Calls Per Session

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/controller.py:547-548`

**Code:**
```python
def _create_table_session(
    self,
    rng: random.Random,
    strategy: Strategy,
    main_paytable: MainGamePaytable,
    bonus_paytable: BonusPaytable | None,
    betting_system_factory: Callable[[], BettingSystem],
) -> TableSession:
    ...
    bonus_bet = calculate_bonus_bet(self._config)
    table_session_config = create_table_session_config(self._config, bonus_bet)
```

**Issue:** The `calculate_bonus_bet()` and `create_table_session_config()` functions are called inside `_create_table_session()`, which is invoked once per session in the sequential execution path. These values are constant across all sessions for a given configuration and could be computed once and reused.

**Impact:** For 10,000 sessions, this results in 10,000 redundant bonus_bet calculations and 10,000 redundant TableSessionConfig instantiations. While each call is cheap, the cumulative overhead is unnecessary.

**Recommendation:** Compute `bonus_bet` and `table_session_config` once in `_run_sequential()` and pass them to `_create_table_session()`, similar to how `strategy`, `main_paytable`, and `bonus_paytable` are already hoisted.

---

#### M2: Redundant Computation in Parallel `_run_single_table_session()`

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/parallel.py:157-158`

**Code:**
```python
def _run_single_table_session(
    seed: int,
    config: FullConfig,
    ...
) -> list[SessionResult]:
    ...
    bonus_bet = calculate_bonus_bet(config)
    table_session_config = create_table_session_config(config, bonus_bet)
```

**Issue:** Unlike the single-session path which receives a pre-computed `session_config`, the multi-seat path recomputes `bonus_bet` and `table_session_config` on every session invocation.

**Impact:** In `run_worker_sessions()`, the worker already computes `bonus_bet = calculate_bonus_bet(task.config)` at line 198, but this value is not passed to `_run_single_table_session()`. Each table session call redundantly recomputes these values.

**Recommendation:** Pass `bonus_bet` and `table_session_config` as parameters to `_run_single_table_session()`, mirroring the pattern used for `_run_single_session()` which receives `session_config`.

---

### Low

#### L1: List Comprehension Creates Intermediate List in Result Extraction

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/parallel.py:178`

**Code:**
```python
table_result = table_session.run_to_completion()
return [seat_result.session_result for seat_result in table_result.seat_results]
```

**Issue:** This creates an intermediate list of SessionResult objects. For a 6-seat table across thousands of sessions, this is many small list allocations.

**Impact:** Minor - the list is small (max 6 elements) and short-lived. The overhead is negligible compared to the actual simulation work.

**Recommendation:** No action needed. The clarity of the list comprehension outweighs the minimal allocation cost.

---

#### L2: Nested Loop in Sequential Multi-Seat Result Collection

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/controller.py:430-432`

**Code:**
```python
for seat_result in table_result.seat_results:
    session_results.append(seat_result.session_result)
```

**Issue:** Each `append()` call may trigger list reallocation. With `num_sessions * num_seats` total results, this could cause O(n) reallocations with O(n) copies each.

**Impact:** For 10,000 sessions with 6 seats, this is 60,000 appends. Python lists over-allocate, so the actual number of reallocations is O(log n), making total cost O(n log n). Still, pre-allocation would be O(n).

**Recommendation:** Pre-allocate the result list if multi-seat mode is detected:
```python
expected_results = num_sessions * num_seats if use_table_session else num_sessions
session_results: list[SessionResult] = []
session_results = [None] * expected_results  # Pre-allocate
```
Or use `list.extend()` instead of individual `append()` calls.

---

### Info

#### I1: Appropriate Single-Seat Optimization Preserved

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/controller.py:419-421`

**Code:**
```python
use_table_session = num_seats > 1

for session_id in range(num_sessions):
    ...
    if use_table_session:
        # Multi-seat: use TableSession
        ...
    else:
        # Single-seat: use Session for efficiency
        ...
```

**Observation:** The PR correctly preserves the optimized single-seat path using the existing `Session` class rather than forcing all simulations through `TableSession`. This ensures no performance regression for the common single-seat case.

---

#### I2: Conditional Check Moved Outside Hot Loop

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/parallel.py:209-211`

**Code:**
```python
num_seats = task.config.table.num_seats
use_table_session = num_seats > 1

for session_id in task.session_ids:
    ...
    if use_table_session:
```

**Observation:** The `num_seats` lookup and boolean flag computation are correctly hoisted outside the session loop, avoiding repeated attribute access inside the hot path.

---

#### I3: Efficient Memory Management in `_merge_results()`

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/parallel.py:372-378`

**Code:**
```python
expected_results = num_sessions * num_seats

# Pre-allocate result list for O(1) direct assignment
results: list[SessionResult | None] = [None] * expected_results
for worker_result in worker_results:
    for result_id, session_result in worker_result.session_results:
        results[result_id] = session_result
```

**Observation:** The result merging correctly scales the pre-allocated list by `num_seats` and uses direct index assignment for O(1) insertion. This is efficient and avoids the dict-based approach's hash overhead.

---

#### I4: `__slots__` Usage in Data Classes

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py:29`, `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/table.py:24`

**Observation:** The existing `TableSessionConfig`, `SeatSessionResult`, `TableSessionResult`, `PlayerSeat`, and `TableRoundResult` classes all use `@dataclass(frozen=True, slots=True)`, which is appropriate for frequently instantiated value objects. This reduces memory footprint and improves attribute access speed.

---

## Performance Impact Assessment

| Scenario | Impact | Notes |
|----------|--------|-------|
| Single-seat simulation | None | Preserves existing optimized path |
| Multi-seat sequential | Low | Redundant computations per session (M1) |
| Multi-seat parallel | Low | Redundant computations per session (M2) |
| Memory usage | Negligible | Proper use of `__slots__`, pre-allocation |

## Recommendations Summary

### Should Fix Before Merge

None - the identified issues are optimizations rather than blockers.

### Should Fix Soon (Medium Priority)

1. **M1**: Hoist `bonus_bet` and `table_session_config` computation outside the session loop in `_run_sequential()`
2. **M2**: Pass pre-computed `bonus_bet` and `table_session_config` to `_run_single_table_session()`

### Consider for Future (Low Priority)

1. **L2**: Pre-allocate `session_results` list for multi-seat mode in sequential execution

---

## Throughput Estimate

The redundant computations (M1, M2) add approximately 1-5 microseconds per session. For 10,000 sessions this translates to 10-50ms of overhead - negligible compared to the actual simulation time. The 100,000 hands/second target should not be impacted by this PR, assuming the underlying `Table` and `TableSession` implementations are efficient.
