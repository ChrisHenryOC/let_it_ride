# Performance Review - PR #125

## Summary

The strategy comparison analytics module is well-designed from a performance perspective. It correctly uses tuples for immutable data, frozen dataclasses with `__slots__`, and delegates heavy statistical computation to optimized scipy functions. The algorithmic complexity is appropriate for the analytics use case (post-simulation analysis) and will not impact the critical 100,000 hands/second simulation throughput target. However, there are opportunities to reduce redundant iterations over session results lists.

## Critical Issues

None found.

## High Severity Issues

None found.

## Medium Severity Issues

### M1: Multiple Redundant Iterations Over Results Lists in `compare_strategies()`

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/comparison.py`
**Lines:** 337-367

The `compare_strategies()` function iterates over the results lists multiple times redundantly:

```python
# Line 337-338: First pass to extract profits
profits_a = tuple(r.session_profit for r in results_a)
profits_b = tuple(r.session_profit for r in results_b)

# Lines 344-345: Second pass to count wins
winning_a = sum(1 for r in results_a if r.session_profit > 0)
winning_b = sum(1 for r in results_b if r.session_profit > 0)

# Lines 352-357: Third and fourth passes for EV calculation
total_profit_a = sum(r.session_profit for r in results_a)
total_hands_a = sum(r.hands_played for r in results_a)
total_profit_b = sum(r.session_profit for r in results_b)
total_hands_b = sum(r.hands_played for r in results_b)

# Lines 364-367: Fifth pass (implicit) for mean/stdev
profit_mean_a = mean(profits_a)
profit_mean_b = mean(profits_b)
profit_std_a = stdev(profits_a) if n_a > 1 else 0.0
profit_std_b = stdev(profits_b) if n_b > 1 else 0.0
```

**Impact:** For large session counts (e.g., 10,000+ sessions), this results in 4-5 iterations per results list instead of 1. While this is post-simulation analytics (not hot path), it adds latency when comparing strategies after large simulations.

**Recommendation:** Consolidate into a single pass with running accumulators:

```python
def _extract_metrics(results: list[SessionResult]) -> tuple[tuple[float, ...], int, float, int]:
    """Extract all needed metrics in a single pass."""
    profits = []
    winning_count = 0
    total_profit = 0.0
    total_hands = 0
    for r in results:
        profits.append(r.session_profit)
        if r.session_profit > 0:
            winning_count += 1
        total_profit += r.session_profit
        total_hands += r.hands_played
    return tuple(profits), winning_count, total_profit, total_hands
```

### M2: Quadratic Complexity in `compare_multiple_strategies()` for Many Strategies

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/comparison.py`
**Lines:** 435-444

```python
for i, name_a in enumerate(strategy_names):
    for name_b in strategy_names[i + 1 :]:
        comparison = compare_strategies(...)
```

**Impact:** This generates O(n^2) comparisons for n strategies. For typical use cases (2-5 strategies), this is fine. However, comparing 10 strategies yields 45 comparisons, each with multiple scipy calls.

**Recommendation:** Document the expected use case and consider adding a warning if comparing more than 10 strategies:

```python
if len(strategy_names) > 10:
    import warnings
    warnings.warn(
        f"Comparing {len(strategy_names)} strategies will generate "
        f"{len(strategy_names) * (len(strategy_names) - 1) // 2} pairwise comparisons",
        stacklevel=2,
    )
```

## Low Severity Issues

### L1: `set()` Creation for Identical Values Check

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/comparison.py`
**Line:** 229

```python
if len(set(data_a)) == 1 and len(set(data_b)) == 1 and data_a[0] == data_b[0]:
```

**Impact:** Creates two sets to check if all values are identical. For large datasets, this is O(n) space.

**Recommendation:** For the Mann-Whitney edge case check, short-circuit if the first few elements differ:

```python
def _all_identical(data: tuple[float, ...]) -> bool:
    """Check if all values are identical (short-circuits early)."""
    if not data:
        return True
    first = data[0]
    return all(x == first for x in data)
```

### L2: String Concatenation in Report Formatting

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/comparison.py`
**Lines:** 458-512

The `format_comparison_report()` function builds a list and joins at the end, which is already the efficient pattern. No issue here.

## Recommendations

### 1. Single-Pass Metric Extraction (Medium Priority)

Consolidate the multiple iterations in `compare_strategies()` into a single pass. This will reduce latency when analyzing large simulation runs with many sessions.

**Before (5+ passes per list):**
```python
profits_a = tuple(r.session_profit for r in results_a)
winning_a = sum(1 for r in results_a if r.session_profit > 0)
total_profit_a = sum(r.session_profit for r in results_a)
total_hands_a = sum(r.hands_played for r in results_a)
```

**After (1 pass per list):**
```python
profits_a, winning_a, total_profit_a, total_hands_a = _extract_metrics(results_a)
```

### 2. Consider Lazy Evaluation for Multiple Comparisons (Low Priority)

For `compare_multiple_strategies()`, consider returning a generator instead of a list if callers might not need all comparisons:

```python
def compare_multiple_strategies(...) -> Iterator[StrategyComparison]:
    """Yields comparisons lazily."""
    for i, name_a in enumerate(strategy_names):
        for name_b in strategy_names[i + 1:]:
            yield compare_strategies(...)
```

### 3. Cache scipy Import at Module Level (Already Done)

The code already imports scipy at module level, which is correct. The statistical functions (ttest_ind, mannwhitneyu) are called with tuples which scipy handles efficiently.

## Performance Characteristics

| Operation | Complexity | Notes |
|-----------|------------|-------|
| `compare_strategies()` | O(n) per result list | Multiple passes; can be optimized |
| `_perform_ttest()` | O(n log n) | scipy internal sorting |
| `_perform_mannwhitney()` | O(n log n) | scipy ranking algorithm |
| `_calculate_cohens_d()` | O(n) | Single pass for mean/variance |
| `compare_multiple_strategies()` | O(k^2 * n) | k strategies, n results each |
| `format_comparison_report()` | O(1) | Fixed output size |

## Compatibility with Performance Targets

- **Throughput (100,000 hands/second):** No impact. This module runs post-simulation.
- **Memory (<4GB for 10M hands):** No impact. Processes session-level results, not individual hands.

The code correctly follows the project's pattern of using frozen dataclasses with `__slots__` for memory efficiency, and uses tuples instead of lists for immutable sequences passed to scipy.

## Positive Observations

1. **Proper use of `__slots__`:** All dataclasses use `frozen=True, slots=True` per project conventions
2. **Immutable data structures:** Uses tuples for statistical data, enabling potential future caching
3. **Delegating to scipy:** Heavy statistical computations use optimized C implementations
4. **Early returns for edge cases:** Functions return early for empty/insufficient data
5. **No memory leaks:** No unclosed resources or circular references
6. **GIL-friendly:** No parallel execution attempted; scipy releases GIL for heavy computation

## Conclusion

The implementation is production-ready from a performance perspective. The medium-severity issues are optimization opportunities rather than blockers. The code will not impact simulation throughput and handles large result sets appropriately.

**Overall Assessment: APPROVED**
