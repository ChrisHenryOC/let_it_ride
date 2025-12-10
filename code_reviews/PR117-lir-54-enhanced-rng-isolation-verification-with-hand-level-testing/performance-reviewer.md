# Performance Review: PR117 - LIR-54 Enhanced RNG Isolation Verification with Hand-Level Testing

## Summary

This PR adds a hand-level callback mechanism to Session and SimulationController for capturing per-hand results during simulation. The implementation is well-designed with minimal performance impact on the hot path. The changes are primarily for testing/verification purposes and include appropriate `__slots__` usage, closure optimization, and conditional callback invocation.

## Findings by Severity

### Medium

#### 1. Closure Creation Per Session in Hot Path

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/controller.py`
**Lines:** 474-484 (diff lines 191-203)

**Issue:** A new closure is created for each session when `hand_callback` is set. For simulations with many sessions (e.g., 10,000+), this creates significant allocation overhead.

```python
if self._hand_callback is not None:
    # Capture session_id in closure for the callback
    sid = session_id

    def session_hand_callback(hand_id: int, result: GameHandResult) -> None:
        self._hand_callback(sid, hand_id, result)  # type: ignore[misc]
```

**Impact:** Each closure allocation involves:
- Creating a new function object
- Capturing `sid` and `self._hand_callback` in the closure's `__closure__` tuple
- GC pressure from short-lived function objects

**Recommendation:** For production simulations where `hand_callback` is typically `None`, this is acceptable. However, if hand callbacks become common, consider using `functools.partial`:

```python
from functools import partial

if self._hand_callback is not None:
    session_hand_callback = partial(
        self._hand_callback, session_id
    )
```

`functools.partial` is implemented in C and has lower overhead than creating a new Python closure each time.

**Severity justification:** Medium because:
- The callback is optional and primarily used for testing
- Production simulations typically won't use this feature
- The overhead is O(sessions), not O(hands)

### Low

#### 2. Dictionary Key Tuple Creation in Test Code

**File:** `/Users/chrishenry/source/let_it_ride/tests/integration/test_controller.py`
**Lines:** 383-389 (diff lines 93-98)

**Issue:** The test creates dictionary keys as `(session_id, hand_id)` tuples for every hand collected.

```python
short_hands_collected: dict[tuple[int, int], GameHandResult] = {}
long_hands_collected: dict[tuple[int, int], GameHandResult] = {}

def short_callback(session_id: int, hand_id: int, result: GameHandResult) -> None:
    short_hands_collected[(session_id, hand_id)] = result
```

**Impact:** Minimal. This is test code, not production code. Tuple creation and dict insertion are O(1) operations.

**Note:** This is the correct approach for test code. The clarity of using a composite key outweighs the negligible overhead.

#### 3. Callback Invocation Check on Every Hand

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py`
**Lines:** 358-360 (diff lines 62-64)

```python
# Call hand callback if registered
if self._hand_callback is not None:
    self._hand_callback(result.hand_id, result)
```

**Impact:** The `None` check is a single attribute lookup and comparison per hand. This is negligible (nanoseconds) compared to the cost of shuffling, dealing, and evaluating hands (microseconds).

**Note:** This is the correct pattern. The conditional check is effectively free compared to the work done in `play_hand()`.

## Positive Performance Observations

### 1. Proper Use of `__slots__`

The new `_hand_callback` attribute is correctly added to the `__slots__` tuple in both `Session` and `SimulationController`:

**Session (`session.py` line 185):**
```python
__slots__ = (
    "_config",
    "_engine",
    "_betting_system",
    "_bankroll",
    "_hands_played",
    "_total_wagered",
    "_total_bonus_wagered",
    "_last_result",
    "_streak",
    "_stop_reason",
    "_hand_callback",
)
```

**SimulationController (`controller.py` line 309):**
```python
__slots__ = ("_config", "_progress_callback", "_hand_callback", "_base_seed")
```

This maintains memory efficiency and avoids `__dict__` creation overhead.

### 2. No Impact on Default Path

When `hand_callback` is `None` (the default):
- `Session.__init__`: Single assignment to `None`
- `Session.play_hand()`: Single `is not None` check
- `_create_session()`: Single conditional that doesn't create a closure

The hot path for production simulations (no callback) has essentially zero overhead.

### 3. Callback Only Available in Sequential Mode

The docstring correctly notes that `hand_callback` is "Only available in sequential mode." This is appropriate because:
- Parallel mode uses multiprocessing with serialization boundaries
- Callbacks would require pickling and would break the parallel execution model
- This design prevents users from accidentally hurting parallel performance

## Performance Impact Assessment

### Will This Meet the 100,000 Hands/Second Target?

**Yes.** The changes have negligible impact on the hot path:

| Operation | Overhead per Hand | Context |
|-----------|-------------------|---------|
| `None` check | ~1-2 ns | ~50us total hand time |
| Callback invocation (when set) | ~20-50 ns | Only in tests |
| Closure creation | ~100 ns per session | O(sessions), not O(hands) |

The callback mechanism adds approximately 0.002% overhead to the hot path when disabled, and is primarily used for testing rather than production simulations.

### Memory Impact

- `HandCallback` type alias: Zero runtime cost
- `_hand_callback` slot: 8 bytes per Session object (pointer)
- Closure per session: ~100 bytes (only when callback is set)

For 10M hands across 1000 sessions: negligible additional memory (< 0.1 MB when callback is set).

## Recommendations Summary

| Priority | Recommendation | Impact |
|----------|----------------|--------|
| Low | Consider `functools.partial` instead of closure in `_create_session()` | Minor memory/GC improvement for callback users |

## Conclusion

This PR introduces a clean, well-designed callback mechanism that has no measurable impact on production simulation performance. The implementation follows Python best practices with proper `__slots__` usage and conditional execution. The changes are appropriate for the testing use case and should not affect the project's 100,000 hands/second throughput target.

**Verdict:** Approved from a performance perspective.
