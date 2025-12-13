# Performance Review: PR #131 - LIR-37 Streak-Based Bonus Strategy

## Summary

The `StreakBasedBonusStrategy` implementation is well-optimized with `__slots__` usage and efficient O(1) operations for the core hot path methods. However, there are moderate performance concerns with string-based dispatch in `_matches_trigger` and `_should_reset` methods that use sequential if-chains for every hand, and code duplication between `_calculate_bet` and `current_multiplier` that could benefit from consolidation. Overall, the implementation should not prevent achieving the 100,000 hands/second target.

## Findings

### Medium

#### M1: String-based dispatch in hot path methods

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/strategy/bonus.py`
**Lines:** 456-488

The `_matches_trigger` and `_should_reset` methods use sequential string comparisons (`if self._trigger == "main_win"`, etc.) that are evaluated on every call to `record_result`. For simulations running millions of hands, this creates unnecessary overhead.

```python
def _matches_trigger(self, main_won: bool, bonus_won: bool | None) -> bool:
    """Check if the result matches our trigger type."""
    if self._trigger == "main_win":
        return main_won
    if self._trigger == "main_loss":
        return not main_won
    if self._trigger == "bonus_win":
        return bonus_won is True
    # ... 6 comparisons total
```

**Recommendation:** Consider using a dictionary-based dispatch or precomputing a bound method during `__init__` to avoid repeated string comparisons:

```python
# In __init__:
self._trigger_check = self._build_trigger_check(trigger)

def _build_trigger_check(self, trigger: str) -> Callable[[bool, bool | None], bool]:
    dispatch = {
        "main_win": lambda m, b: m,
        "main_loss": lambda m, b: not m,
        "bonus_win": lambda m, b: b is True,
        # etc.
    }
    return dispatch[trigger]
```

#### M2: Duplicate calculation logic in _calculate_bet and current_multiplier

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/strategy/bonus.py`
**Lines:** 399-426 and 501-531

The `_calculate_bet` method and `current_multiplier` property contain nearly identical logic for computing multiplier/bet values based on action type. This duplication means the same calculations are performed separately, and if `current_multiplier` is frequently called (e.g., for logging/monitoring), it recomputes values that `_calculate_bet` already computed.

```python
def _calculate_bet(self) -> float:
    # ... triggers calculation
    if self._action_type == "multiply":
        multiplier = self._action_value**triggers
        # ...

@property
def current_multiplier(self) -> float:
    # ... same triggers calculation
    if self._action_type == "multiply":
        multiplier = self._action_value**triggers
        # ... same logic
```

**Recommendation:** Consider caching the computed multiplier in a slot variable that is updated when streak changes, or refactor to have a single `_compute_multiplier` method used by both.

#### M3: Exponentiation in hot path for multiply action

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/strategy/bonus.py`
**Lines:** 408-412

When using the "multiply" action type, every call to `_calculate_bet` performs an exponentiation operation (`self._action_value**triggers`). For large trigger counts, this is more expensive than multiplication.

```python
if self._action_type == "multiply":
    multiplier = self._action_value**triggers  # Exponentiation on every bet calculation
```

**Recommendation:** Cache the current multiplier value and update it incrementally when the streak triggers (multiply by `action_value` once) rather than recomputing via exponentiation.

### Positive Observations

1. **`__slots__` usage (line 323-333):** Correctly uses `__slots__` to minimize memory footprint per strategy instance - important for multi-seat table simulations.

2. **O(1) core operations:** The `get_bonus_bet`, `record_result`, and `reset` methods are all O(1) with no loops or allocations in the hot path.

3. **Early exit in get_bonus_bet (line 392-393):** The quick return for `not self._is_betting` avoids unnecessary computation for "stop" action strategies.

4. **Integer division for triggers (line 406):** Uses integer division `//` which is efficient for computing trigger counts.

## Performance Impact Assessment

The identified issues are **medium severity** and unlikely to prevent achieving the 100,000 hands/second target on their own. The string comparisons add nanoseconds per hand, which becomes noticeable only at 10M+ hand scale. The implementation correctly prioritizes memory efficiency with `__slots__`, which is important for the <4GB memory target.

For production optimization, addressing M1 (string dispatch) would provide the most benefit if streak-based bonus is used heavily in benchmarks.
