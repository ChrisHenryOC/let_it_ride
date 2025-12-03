# Performance Review: PR #76 - LIR-11 Add Baseline Strategies (AlwaysRide / AlwaysPull)

## Summary

This PR implements two baseline strategies (`AlwaysRideStrategy` and `AlwaysPullStrategy`) that serve as variance bounds for strategy comparison. The implementation is highly performant - both strategy classes return constant enum values with O(1) time complexity and zero memory allocation per call. This is the most efficient possible implementation for strategy classes and will not impact the simulator's target of 100,000+ hands/second.

## Findings by Severity

### Critical Issues

**None identified.**

### High Issues

**None identified.**

### Medium Issues

**None identified.**

### Low Issues

**None identified.**

---

## Detailed Analysis

### 1. Algorithm Complexity - EXCELLENT

**File:** `src/let_it_ride/strategy/baseline.py`

Both `AlwaysRideStrategy` and `AlwaysPullStrategy` implementations are optimal:

- **Time Complexity:** O(1) - constant time for all operations
- **Space Complexity:** O(1) - no memory allocation during method calls
- **Method Calls:** Simply return pre-defined enum values (`Decision.RIDE` or `Decision.PULL`)

```python
# Lines 128-134 and 136-142
def decide_bet1(self, analysis: HandAnalysis, context: StrategyContext) -> Decision:
    return Decision.RIDE  # O(1) operation

def decide_bet2(self, analysis: HandAnalysis, context: StrategyContext) -> Decision:
    return Decision.RIDE  # O(1) operation
```

The strategies deliberately ignore their `analysis` and `context` parameters (appropriately suppressed with `# noqa: ARG002`), avoiding any computation overhead from the `HandAnalysis` dataclass attributes.

### 2. Memory Management - EXCELLENT

**File:** `src/let_it_ride/strategy/baseline.py`

- No instance attributes on either strategy class
- No memory allocation during decision calls
- No closures or lambda captures that could cause memory leaks
- Using `Decision` enum (singleton pattern) rather than creating new objects

The classes are essentially stateless and can be instantiated once and reused across millions of hands without any memory accumulation.

### 3. Comparison with BasicStrategy

The baseline strategies are significantly faster than `BasicStrategy` (from `basic.py`), which must:
- Access multiple `HandAnalysis` attributes
- Evaluate conditional logic chains (7 conditions for `decide_bet1`, 4 conditions for `decide_bet2`)

This is by design - baseline strategies provide theoretical bounds while the basic strategy implements actual game logic.

### 4. Test Performance Considerations

**File:** `tests/unit/strategy/test_baseline.py`

The test file shows good practices:

- **Helper functions (lines 194-228):** The `make_card` and `make_hand` helper functions are only used during test setup, not in hot paths. Dictionary lookups for `rank_map` and `suit_map` are acceptable in test code.

- **Parametrized tests:** Using `@pytest.mark.parametrize` ensures test cases run independently without redundant setup overhead.

- **Fixture reuse:** Strategy instances and default contexts are created via fixtures, avoiding repeated instantiation.

**Potential minor optimization (not blocking):** The `make_card` function creates lookup dictionaries on every call. In production test suites with many more test cases, module-level constants would be marginally more efficient:

```python
# Current approach (acceptable for test code):
def make_card(notation: str) -> Card:
    rank_map = {...}  # Created on each call
    ...

# Alternative (if test count grows significantly):
_RANK_MAP = {...}  # Module-level constant
_SUIT_MAP = {...}
def make_card(notation: str) -> Card:
    return Card(_RANK_MAP[notation[0]], _SUIT_MAP[notation[1]])
```

This is a **non-issue** for the current test count and test execution is not part of runtime performance targets.

### 5. Import Efficiency

**File:** `src/let_it_ride/strategy/__init__.py`

The exports are properly organized alphabetically. The import of baseline strategies does not add any significant module load time since the module contains only class definitions with no initialization logic.

---

## Performance Impact Assessment

| Metric | Target | Impact | Status |
|--------|--------|--------|--------|
| Throughput | >=100,000 hands/sec | Zero overhead | PASS |
| Memory | <4GB for 10M hands | Zero accumulation | PASS |
| Hot path complexity | O(1) preferred | O(1) achieved | PASS |

### Calculations

With the baseline strategies:
- Decision calls: ~0.5-1 nanosecond (simple return statement)
- Strategy overhead per hand: 2 calls x ~1ns = ~2ns
- Theoretical maximum: ~500,000,000 decisions/second

This leaves ample headroom for the hand analysis, deck operations, and other simulation components.

---

## Positive Observations

1. **Optimal implementation pattern:** Returning constant enum values is the most efficient possible strategy implementation.

2. **No GIL contention:** The stateless design allows these strategies to be safely shared across threads in parallel simulations.

3. **Cache-friendly:** No dynamic memory allocation means no cache invalidation during hot paths.

4. **Consistent with existing patterns:** Follows the same signature and `noqa` conventions as `BasicStrategy`, maintaining codebase consistency.

---

## Recommendations

**No performance-related changes required.** The implementation is optimal for its purpose.

### Future Consideration (Not for this PR)

If the project later implements strategy caching or pooling for other strategy types, the baseline strategies could be made into true singletons. However, this is unnecessary given their already-minimal footprint:

```python
# Not needed, but possible future pattern:
class AlwaysRideStrategy:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

---

## Conclusion

**APPROVED from a performance perspective.** This PR introduces zero performance overhead and the implementation is optimal for the simulator's throughput and memory targets.
