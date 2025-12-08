# Performance Review: PR #111 - LIR-22 Simulation Results Aggregation

## Summary

This PR introduces simulation results aggregation functionality with `AggregateStatistics` dataclass and `aggregate_results()`, `merge_aggregates()`, and `aggregate_with_hand_frequencies()` functions. The implementation is generally well-optimized for the expected use case (aggregating hundreds to thousands of sessions), but there are **two medium-severity issues** related to memory efficiency when scaling to millions of hands. The code correctly uses `__slots__` and `frozen=True` for the dataclass, which is a positive performance pattern.

---

## Findings by Severity

### Critical Issues

**None identified.** The aggregation code runs post-simulation and operates on session-level data (not per-hand), so it will not impact the 100,000 hands/second throughput target.

---

### High Issues

**None identified.**

---

### Medium Issues

#### M1: Memory Growth from `session_profits` Tuple Retention

**File:** `src/let_it_ride/simulation/aggregation.py`
**Lines:** 214, 277, 370, 401

**Issue:** The `session_profits` tuple is stored in `AggregateStatistics` to support merge operations. For large-scale simulations (e.g., 10M hands across 100,000 sessions), this tuple will contain 100,000 float values (~800KB per aggregate). When using `merge_aggregates()` repeatedly in a tree-like reduction pattern, intermediate aggregates retain their profits tuples, potentially causing memory pressure.

**Impact:** With 100,000 sessions at 100 hands each = 10M hands:
- Each `session_profits` tuple: ~800KB
- Intermediate merges create new tuples without releasing old ones during reduction
- Total memory for profits data: O(n log n) in a balanced merge tree, where n = number of sessions

**Recommendation:** Consider one of these approaches:
1. Use a generator or streaming statistics approach that computes mean/std incrementally without storing all values
2. Provide an option to compute "final" statistics without retaining `session_profits`
3. Document the memory tradeoff clearly for users running large simulations

**Code Example - Incremental Statistics (Welford's Algorithm):**
```python
# For incremental mean/variance without storing all values:
class IncrementalStats:
    __slots__ = ('n', 'mean', 'm2', 'min_val', 'max_val')

    def __init__(self):
        self.n = 0
        self.mean = 0.0
        self.m2 = 0.0
        self.min_val = float('inf')
        self.max_val = float('-inf')

    def update(self, x: float) -> None:
        self.n += 1
        delta = x - self.mean
        self.mean += delta / self.n
        self.m2 += delta * (x - self.mean)
        self.min_val = min(self.min_val, x)
        self.max_val = max(self.max_val, x)

    @property
    def variance(self) -> float:
        return self.m2 / self.n if self.n > 1 else 0.0

    @property
    def std(self) -> float:
        return self.variance ** 0.5
```

---

#### M2: Repeated Dictionary Iteration in `merge_aggregates()`

**File:** `src/let_it_ride/simulation/aggregation.py`
**Lines:** 236-247 (diff positions corresponding to lines 357-367 in the file)

**Issue:** The hand frequency merge iterates twice through dictionaries:
```python
for hand_rank, count in agg1.hand_frequencies.items():
    hand_frequencies[hand_rank] = count
for hand_rank, count in agg2.hand_frequencies.items():
    hand_frequencies[hand_rank] = hand_frequencies.get(hand_rank, 0) + count
```

Then immediately iterates again for percentage calculation:
```python
for hand_rank, count in hand_frequencies.items():
    hand_frequency_pct[hand_rank] = count / total_freq
```

**Impact:** For 10 hand ranks (typical), this is negligible. However, the pattern could be simplified.

**Recommendation:** Use `collections.Counter` for cleaner merge semantics:
```python
from collections import Counter

# Merge frequencies in one operation
hand_frequencies = dict(Counter(agg1.hand_frequencies) + Counter(agg2.hand_frequencies))
```

This is a minor optimization but improves code clarity.

---

### Low Issues

#### L1: Multiple List Iterations in `aggregate_results()`

**File:** `src/let_it_ride/simulation/aggregation.py`
**Lines:** 117-157 (diff positions corresponding to lines 238-278 in the file)

**Issue:** The function iterates through the `results` list multiple times:
1. Three `sum(1 for r in results if ...)` calls for counting outcomes (lines 238-240)
2. One `sum(r.hands_played for r in results)` (line 247)
3. Three more `sum()` calls for financial metrics (lines 250-255)
4. One more iteration for `session_profits` tuple creation (line 277)

**Impact:** For 1,000 sessions, this is 8 passes = 8,000 iterations. Still O(n) complexity and fast in absolute terms, but could be consolidated.

**Recommendation:** Consider a single-pass aggregation:
```python
def aggregate_results(results: list[SessionResult]) -> AggregateStatistics:
    if not results:
        raise ValueError("Cannot aggregate empty results list")

    # Single-pass aggregation
    winning = losing = push = 0
    total_hands = 0
    main_wagered = bonus_wagered = net_result = 0.0
    profits = []

    for r in results:
        # Count outcomes
        if r.outcome == SessionOutcome.WIN:
            winning += 1
        elif r.outcome == SessionOutcome.LOSS:
            losing += 1
        else:
            push += 1

        # Accumulate metrics
        total_hands += r.hands_played
        main_wagered += r.total_wagered
        bonus_wagered += r.total_bonus_wagered
        net_result += r.session_profit
        profits.append(r.session_profit)

    # ... rest of calculations
```

This reduces from ~8 passes to 1 pass, providing approximately 8x speedup for the aggregation loop itself (though this is unlikely to be a bottleneck given session-level granularity).

---

#### L2: Object Recreation in `aggregate_with_hand_frequencies()`

**File:** `src/let_it_ride/simulation/aggregation.py`
**Lines:** 284-335 (diff positions corresponding to lines 405-456 in the file)

**Issue:** The function calls `aggregate_results()` to create a base stats object, then immediately creates a new `AggregateStatistics` copying all fields except `hand_frequencies` and `hand_frequency_pct`. This creates two full dataclass instances.

**Impact:** Minimal - dataclass creation is fast. However, the pattern is verbose.

**Recommendation:** Consider using `dataclasses.replace()` for cleaner code (though note: this does not work with `frozen=True` slots dataclasses in some Python versions). Alternatively, accept this as a reasonable tradeoff for code clarity. The current implementation is correct and readable.

---

## Positive Performance Patterns

1. **`@dataclass(frozen=True, slots=True)`** - Correct use of slots reduces per-instance memory overhead by ~40-50% compared to `__dict__`-based storage. This is especially important for `SessionResult` objects created per-session.

2. **Tuple for `session_profits`** - Immutable tuple is more memory-efficient than a list for read-only data.

3. **Division-by-zero guards** - All divisions check for zero denominators, avoiding exception overhead in edge cases.

4. **Post-simulation aggregation** - This code runs after simulation completes, so it does not impact the critical 100,000 hands/second throughput target.

---

## Memory Budget Analysis

For the target of <4GB RAM for 10M hands:

| Component | Size per Unit | Units (10M hands, 100 hands/session) | Total Memory |
|-----------|---------------|--------------------------------------|--------------|
| `session_profits` tuple | 8 bytes/float | 100,000 sessions | ~800 KB |
| `AggregateStatistics` | ~500 bytes | 1 (final) | ~500 bytes |
| Intermediate merges (worst case) | ~1 MB | log2(100,000) ~ 17 levels | ~17 MB |

**Conclusion:** The aggregation module's memory footprint is well within budget, contributing less than 1% of the 4GB limit even in worst-case merge scenarios.

---

## Recommendations Summary

| ID | Severity | Recommendation | Effort |
|----|----------|----------------|--------|
| M1 | Medium | Document memory implications of `session_profits` retention; consider streaming stats for very large simulations | Medium |
| M2 | Medium | Use `Counter` for frequency merging (optional) | Low |
| L1 | Low | Consolidate to single-pass aggregation loop | Low |
| L2 | Low | No action needed - current pattern is acceptable | N/A |

---

## Conclusion

This PR introduces well-designed aggregation functionality that will not impact simulation throughput targets. The memory efficiency is adequate for the stated 10M hand / 4GB budget. The medium-severity items are recommendations for future optimization if scaling to significantly larger simulations (100M+ hands) becomes necessary.

**Verdict: Approve with suggestions for documentation.**
