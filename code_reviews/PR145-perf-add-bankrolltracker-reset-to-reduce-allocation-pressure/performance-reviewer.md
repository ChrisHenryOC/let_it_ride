# Performance Review for PR #145

## Summary

This PR adds a `reset()` method to `BankrollTracker` and updates `_SeatState.reset()` to use it instead of creating new `BankrollTracker` instances. This is a targeted micro-optimization for seat replacement mode scenarios where seats frequently hit stop conditions and reset. The approach correctly addresses allocation pressure in high-churn scenarios, though the performance benefit will be modest in typical use cases.

## Findings

### Critical

None.

### High

None.

### Medium

#### 1. Missing `__slots__` on `BankrollTracker` Class
**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/bankroll/tracker.py:8`

The `BankrollTracker` class does not use `__slots__`, while other similar classes in the codebase (e.g., `_SeatState`, betting system classes) do. For a class that may be instantiated many times (one per seat, potentially reset frequently in seat replacement mode), adding `__slots__` would:
- Reduce per-instance memory by ~50-100 bytes (eliminating `__dict__`)
- Speed up attribute access
- Complement the `reset()` optimization by making the reused object more memory-efficient

**Recommendation:** Add `__slots__` to `BankrollTracker`:
```python
class BankrollTracker:
    __slots__ = (
        "_starting",
        "_balance",
        "_peak",
        "_max_drawdown",
        "_peak_at_max_drawdown",
        "_track_history",
        "_history",
    )
```

This would multiply the benefit of object reuse since each reused instance takes less memory.

---

#### 2. `list.clear()` vs Reassignment Trade-off
**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/bankroll/tracker.py:184`

```python
self._history.clear()
```

Using `list.clear()` is the correct choice here for object reuse because:
- It maintains the existing list object (avoids allocation)
- It keeps any over-allocated capacity for future appends

However, if `track_history=True` and a session had thousands of entries, the cleared list retains its allocated capacity. In seat replacement mode with history tracking, memory could accumulate across many resets.

**Impact:** Only relevant when `track_history=True` (disabled by default). With the 4GB memory budget and typical session lengths, this is unlikely to be an issue.

**Recommendation:** Document this behavior in the docstring. If memory becomes a concern in extreme cases, consider `self._history = []` only when `len(self._history) > THRESHOLD` to reclaim capacity.

---

### Low

#### 3. Duplicated Validation Logic
**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/bankroll/tracker.py:175-178`

The negative amount check in `reset()` duplicates logic from `__init__()`:
```python
if starting_amount is not None:
    if starting_amount < 0:
        raise ValueError("Starting amount cannot be negative")
```

**Impact:** Negligible - validation runs once per reset, not in hot paths.

**Recommendation:** Consider extracting to a private `_validate_starting_amount()` method for DRY, but this is truly optional.

---

## Positive Observations

1. **Correct Hot Path Optimization:** The change targets `_SeatState.reset()` which is called in seat replacement mode's hot path. This is the right place to optimize.

2. **Preserved Behavioral Semantics:** The `reset()` method correctly handles:
   - Optional `starting_amount` parameter (uses original if `None`)
   - Clears all stateful fields (`_peak`, `_max_drawdown`, etc.)
   - Preserves `_track_history` setting across resets

3. **Comprehensive Test Coverage:** The test suite thoroughly covers:
   - All field resets
   - New starting amount
   - `None` starting amount (original preserved)
   - Negative amount validation
   - Post-reset operation correctness

4. **Memory-Conscious Design:** Using `reset()` instead of object recreation avoids:
   - Garbage collection pressure
   - Allocation overhead
   - Potential memory fragmentation in long-running simulations

---

## Performance Target Assessment

| Target | Status | Notes |
|--------|--------|-------|
| >=100,000 hands/second | Not Impacted | Optimization improves throughput marginally in seat replacement mode |
| <4GB RAM for 10M hands | Not Impacted | Reduces allocation churn; minor memory improvement |

**Quantitative Estimate:** In seat replacement mode with 6 seats and aggressive stop conditions (e.g., tight loss limits), a table running 10M rounds might see thousands of seat resets. Avoiding ~thousands of `BankrollTracker` allocations saves:
- ~48KB-96KB of allocations (assuming 48-96 bytes per instance with `__slots__`)
- GC pressure from short-lived objects

The optimization is sound but provides marginal benefit. The primary value is reducing GC pause variability in long simulations.

---

## Recommendations Summary

| Priority | Issue | Action |
|----------|-------|--------|
| Medium | Missing `__slots__` on `BankrollTracker` | Add `__slots__` to maximize reuse benefit |
| Medium | `list.clear()` capacity retention | Document behavior; consider threshold-based reallocation if needed |
| Low | Duplicated validation | Optional refactor for DRY |
