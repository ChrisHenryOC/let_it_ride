# Performance Review: PR #114 - LIR-44 Chair Position Analytics

**Reviewer:** Performance Specialist
**Date:** 2025-12-08
**PR:** #114 (feat: LIR-44 Chair Position Analytics)

## Summary

The chair position analytics implementation is well-designed for performance with O(n) time complexity for aggregation and proper use of `__slots__` on accumulator classes. The code will not impede the project's throughput target of 100,000 hands/second since analytics runs post-simulation. One medium-severity optimization opportunity exists in the aggregation loop where dictionary membership checks could be avoided.

## Findings by Severity

### Critical

No critical performance issues found.

### High

No high-severity performance issues found.

### Medium

#### M1: Dictionary Key Lookup Overhead in Hot Loop

**File:** `src/let_it_ride/analytics/chair_position.py`
**Lines:** 277-296 (diff lines 103-122)

The `_aggregate_seat_data` function performs a dictionary key lookup (`seat_num not in aggregations`) for every seat in every table result, then immediately performs another lookup to retrieve the value:

```python
for table_result in results:
    for seat_result in table_result.seat_results:
        seat_num = seat_result.seat_number
        if seat_num not in aggregations:
            aggregations[seat_num] = _SeatAggregation()

        agg = aggregations[seat_num]  # Second lookup
```

**Impact:** For a simulation with 10,000 table sessions and 6 seats, this results in 120,000 iterations. The double dictionary lookup adds unnecessary overhead.

**Recommendation:** Use `dict.setdefault()` or the "get-or-create" pattern to reduce to a single lookup:

```python
for table_result in results:
    for seat_result in table_result.seat_results:
        seat_num = seat_result.seat_number
        agg = aggregations.get(seat_num)
        if agg is None:
            agg = _SeatAggregation()
            aggregations[seat_num] = agg
        # ... continue with agg
```

Or alternatively:
```python
from collections import defaultdict

def _aggregate_seat_data(results: list[TableSessionResult]) -> dict[int, _SeatAggregation]:
    aggregations: dict[int, _SeatAggregation] = defaultdict(_SeatAggregation)
    for table_result in results:
        for seat_result in table_result.seat_results:
            agg = aggregations[seat_result.seat_number]
            # ... continue
```

**Estimated improvement:** 5-10% reduction in aggregation time for large result sets.

### Low

#### L1: List Comprehension in Chi-Square Test

**File:** `src/let_it_ride/analytics/chair_position.py`
**Lines:** 368-369 (diff lines 194-195)

```python
observed_wins = [s.wins for s in seat_stats]
total_wins = sum(observed_wins)
```

This creates an intermediate list only to immediately sum it.

**Recommendation:** Use a generator expression for memory efficiency:

```python
total_wins = sum(s.wins for s in seat_stats)
observed_wins = [s.wins for s in seat_stats]  # Still needed for scipy
```

**Impact:** Minimal since `seat_stats` is at most 6 elements (seats 1-6). Not worth changing unless this pattern appears in larger contexts.

#### L2: Sorted Dictionary Iteration

**File:** `src/let_it_ride/analytics/chair_position.py`
**Lines:** 422-429 (diff lines 248-255)

```python
for seat_num in sorted(aggregations.keys()):
    stats_for_seat = _calculate_seat_statistics(...)
```

**Impact:** The `sorted()` call is O(k log k) where k is number of seats (max 6). This is negligible but worth noting for pattern awareness.

**Recommendation:** Acceptable as-is. The sorting ensures deterministic output order, which is valuable for testing and reproducibility.

## Positive Performance Patterns

### P1: Proper Use of `__slots__`

**File:** `src/let_it_ride/analytics/chair_position.py`
**Lines:** 249-258 (diff lines 75-84)

The `_SeatAggregation` class correctly uses `__slots__` to reduce memory overhead:

```python
class _SeatAggregation:
    __slots__ = ("wins", "losses", "pushes", "total_profit")
```

This is excellent practice for accumulator classes that may be instantiated many times.

### P2: Immutable Result Dataclasses with `__slots__`

**File:** `src/let_it_ride/analytics/chair_position.py`
**Lines:** 202-229 and 231-247 (diff lines 28-73)

Both `SeatStatistics` and `ChairPositionAnalysis` use `frozen=True, slots=True`:

```python
@dataclass(frozen=True, slots=True)
class SeatStatistics:
```

This provides:
- Memory efficiency from `__slots__`
- Thread safety from immutability
- Hashability for potential caching use cases

### P3: Single-Pass Aggregation

The aggregation algorithm processes results in a single O(n * k) pass where n is number of table sessions and k is seats per table. This is optimal for the problem.

### P4: Lazy scipy Import Pattern

The module uses `from scipy import stats` at module level, but scipy is only called in:
- `_test_seat_independence()` - one `stats.chisquare()` call
- The existing `calculate_wilson_confidence_interval()` - `stats.norm.ppf()`

These are called once per analysis (not per-hand), so the scipy overhead is acceptable.

## Performance Impact Assessment

| Metric | Assessment |
|--------|------------|
| **Time Complexity** | O(n * k) for aggregation where n=sessions, k=seats |
| **Space Complexity** | O(k) for aggregations dict (max 6 entries) |
| **Throughput Impact** | None - runs post-simulation |
| **Memory Impact** | Negligible - uses `__slots__` throughout |
| **Target Compliance** | Compliant - does not affect 100k hands/sec target |

## Recommendations Summary

| ID | Severity | Recommendation | Effort |
|----|----------|----------------|--------|
| M1 | Medium | Use `defaultdict` or `get()` pattern in aggregation loop | Low |
| L1 | Low | Use generator for `sum()` (optional) | Trivial |
| L2 | Low | Keep as-is - sorting is appropriate | None |

## Conclusion

This PR is **approved from a performance perspective**. The analytics module is well-designed with appropriate complexity for its purpose. The M1 finding is a minor optimization opportunity that could be addressed in a follow-up PR if desired, but it does not block this feature since analytics runs as a post-processing step outside the simulation hot path.
