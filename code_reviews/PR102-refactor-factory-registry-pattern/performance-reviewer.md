# Performance Review: PR #102 - Refactor Factory Registry Pattern

## Summary

This PR replaces if-elif chains with dictionary-based registry pattern for strategy and betting system factories. The refactor provides **equivalent or slightly better performance** at the factory level. The registry pattern offers O(1) dictionary lookup vs O(n) sequential if-elif chain traversal in the worst case. However, factory creation is called once per simulation setup, not in the hot path, so the impact on the 100,000+ hands/second throughput target is negligible.

## Performance Analysis

### Registry Lookup Performance

**Complexity Improvement:**
- **Before:** O(n) worst case for if-elif chains (up to 6 comparisons for strategies, 7 for betting systems)
- **After:** O(1) average case for dictionary `.get()` lookup

**Real-World Impact:** Negligible

The factory functions `create_strategy()` and `create_betting_system()` are called once per simulation run during setup (line 352-357 in `controller.py`), not per-hand. With 100,000+ hands per second as the target, the factory creation cost is amortized to effectively zero.

### Memory Analysis

**Module-Level Registries:**
```python
_STRATEGY_FACTORIES: dict[str, Callable[[StrategyConfig], Strategy]]  # 6 entries
_BETTING_SYSTEM_FACTORIES: dict[str, Callable[[BankrollConfig], BettingSystem] | None]  # 8 entries
```

- **Memory overhead:** ~600-800 bytes total for both dictionaries
- **Allocation timing:** Once at module import
- **Impact on 4GB budget for 10M hands:** Negligible (0.00002% of budget)

The lambda functions in `_STRATEGY_FACTORIES` (e.g., `lambda _: BasicStrategy()`) are created at module import time and persist for the application lifetime. This is appropriate for a registry pattern.

### Custom Strategy Creation

**Lines 86-93 (diff lines 25-32):**
```python
bet1_rules = [
    StrategyRule(condition=rule.condition, action=_action_to_decision(rule.action))
    for rule in config.custom.bet1_rules
]
bet2_rules = [
    StrategyRule(condition=rule.condition, action=_action_to_decision(rule.action))
    for rule in config.custom.bet2_rules
]
```

- **Complexity:** O(r) where r = number of rules
- **Called:** Once per simulation setup
- **Impact:** None - this code existed before the refactor, just moved to a dedicated function

### Betting System Factory Lookup Optimization

**Lines 249-253 (diff lines 215-218):**
```python
system_type = config.betting_system.type
if system_type not in _BETTING_SYSTEM_FACTORIES:
    raise ValueError(f"Unknown betting system type: {system_type}")

factory = _BETTING_SYSTEM_FACTORIES[system_type]
```

**Minor Observation:** The code performs two dictionary lookups - one for `in` check and one for `[]` access. This could be consolidated to a single lookup:

```python
factory = _BETTING_SYSTEM_FACTORIES.get(system_type)
if factory is None and system_type not in _BETTING_SYSTEM_FACTORIES:
    raise ValueError(f"Unknown betting system type: {system_type}")
```

However, this pattern is intentional to distinguish between "key not in dict" (ValueError) vs "key exists but value is None" (NotImplementedError). The current implementation correctly handles both cases. The double lookup adds ~100 nanoseconds which is immaterial given this runs once per simulation.

## Findings by Severity

### Critical Issues
None identified.

### High Severity Issues
None identified.

### Medium Severity Issues
None identified.

### Low Severity Issues

**1. Double Dictionary Lookup (informational only)**
- **Location:** `src/let_it_ride/simulation/controller.py`, lines 249-253
- **Impact:** ~100ns per factory call (once per simulation)
- **Recommendation:** No action needed - the current pattern correctly handles the semantic difference between unknown types and unimplemented types.

## Positive Performance Observations

1. **Appropriate use of `__slots__`:** The `SimulationResults` dataclass at line 109 correctly uses `slots=True`, reducing memory overhead for result objects.

2. **Factory pattern efficiency:** Creating betting systems via factory function allows fresh state per session without duplicating configuration parsing logic.

3. **Registry pattern enables O(1) extensibility:** Adding new strategy/betting types requires only adding a new entry to the registry dictionary, without modifying conditional logic.

4. **Module-level initialization:** Registries are initialized once at import time, avoiding per-call overhead.

## Test File Performance

The new test file `tests/unit/simulation/test_factories.py` (502 lines) tests factory functionality thoroughly. The tests use Pydantic config objects which have some overhead, but this is test code and does not impact production performance.

**Note:** The test file uses `object.__setattr__` to bypass Pydantic validation for edge case testing. This is an appropriate testing pattern and has no production impact.

## Conclusion

This refactor is **performance-neutral** with respect to the project's throughput and memory targets:
- **Throughput target (100,000+ hands/sec):** No impact - factory calls are not in the hot path
- **Memory target (<4GB for 10M hands):** No impact - registry memory is negligible (~800 bytes)

The registry pattern is a clean architectural improvement that does not introduce any performance regressions.
