# Performance Review - PR #113

## Summary

The PR implements a statistics module for calculating detailed metrics from simulation results. The implementation uses appropriate data structures (`__slots__`, frozen dataclasses) but has several algorithmic inefficiencies where data is iterated multiple times unnecessarily. The skewness and kurtosis calculations perform O(n) iterations that could be combined with existing mean/variance calculations, and the risk metrics function iterates through data up to 4 separate times.

## Findings

### Critical

None

### High

**H1: Multiple Redundant Iterations in `_calculate_risk_metrics`**
- File: `src/let_it_ride/analytics/statistics.py`
- Lines: 474-483
- Issue: The function iterates through the `profits` tuple 4 separate times: once for counting losses (line 475), once for 50% losses (line 482), and once for 100% losses (line 483), plus the conversion at line 447.
- Impact: For 10M sessions, this means 40M+ iterations instead of 10M.
- Recommendation: Combine all counting into a single loop:

```python
# Current (4 iterations):
losses = sum(1 for p in profits if p < 0)
prob_loss_50pct = sum(1 for p in profits if p <= loss_50pct_threshold) / n
prob_loss_100pct = sum(1 for p in profits if p <= loss_100pct_threshold) / n

# Optimized (1 iteration):
losses = loss_50pct_count = loss_100pct_count = 0
for p in profits:
    if p < 0:
        losses += 1
        if p <= loss_50pct_threshold:
            loss_50pct_count += 1
            if p <= loss_100pct_threshold:
                loss_100pct_count += 1
```

### Medium

**M1: Separate Iterations for Skewness and Kurtosis**
- File: `src/let_it_ride/analytics/statistics.py`
- Lines: 282 and 311
- Issue: `_calculate_skewness` and `_calculate_kurtosis` each iterate through all data to compute sum of cubed/fourth power deviations. Both are called from `_calculate_distribution_stats` where mean and std are already computed via iteration.
- Impact: The total iterations become 5-6x instead of 1-2x (mean, variance, skewness, kurtosis, min, max, percentiles).
- Recommendation: Consider using NumPy or combining the skewness/kurtosis calculations:

```python
# Combine skewness and kurtosis into single pass:
def _calculate_higher_moments(data, data_mean, data_std):
    n = len(data)
    if n < 4 or data_std == 0:
        return 0.0, 0.0

    sum_cubed = sum_fourth = 0.0
    for x in data:
        deviation = x - data_mean
        dev_sq = deviation * deviation
        sum_cubed += deviation * dev_sq
        sum_fourth += dev_sq * dev_sq

    # skewness
    skew_adj = n / ((n - 1) * (n - 2))
    skewness = skew_adj * sum_cubed / (data_std ** 3)

    # kurtosis
    kurt_term1 = (n * (n + 1)) / ((n - 1) * (n - 2) * (n - 3))
    kurt_term3 = (3 * (n - 1) ** 2) / ((n - 2) * (n - 3))
    kurtosis = kurt_term1 * sum_fourth / (data_std ** 4) - kurt_term3

    return skewness, kurtosis
```

**M2: `quantiles()` Creates Full 99-Element List**
- File: `src/let_it_ride/analytics/statistics.py`
- Line: 339
- Issue: `quantiles(data, n=100)` computes all 99 quantile cut points even though only 5 are typically used (5th, 25th, 50th, 75th, 95th).
- Impact: Minor memory allocation overhead, but sorting dominates complexity (O(n log n)).
- Recommendation: For large datasets, consider using `numpy.percentile()` which can compute specific percentiles more efficiently, or implement a selection-based algorithm for individual percentiles.

**M3: Repeated Tuple Conversion from SessionResult**
- File: `src/let_it_ride/analytics/statistics.py`
- Lines: 447-448
- Issue: When `session_results` is provided, the function creates new tuples by iterating through all results for profits and drawdowns.
- Impact: Allocates new tuples that may already exist in `AggregateStatistics.session_profits`.
- Recommendation: Accept the already-computed `session_profits` tuple from `AggregateStatistics` when available instead of recomputing from results.

### Low

**L1: Consider NumPy for Large-Scale Statistics**
- File: `src/let_it_ride/analytics/statistics.py`
- Issue: The module uses Python's `statistics` library which operates on Python lists/tuples. For the target scale (10M hands across multiple sessions), NumPy would provide significant speedup through vectorized operations.
- Impact: NumPy can be 10-100x faster for statistical calculations on large arrays.
- Recommendation: Consider offering NumPy-based implementations for production use:

```python
import numpy as np

def _calculate_distribution_stats_numpy(data: np.ndarray) -> DistributionStats:
    return DistributionStats(
        mean=np.mean(data),
        std=np.std(data, ddof=1),
        variance=np.var(data, ddof=1),
        skewness=scipy.stats.skew(data),
        kurtosis=scipy.stats.kurtosis(data),
        min=np.min(data),
        max=np.max(data),
        percentiles={p: np.percentile(data, p) for p in DEFAULT_PERCENTILES},
        iqr=np.percentile(data, 75) - np.percentile(data, 25),
    )
```

**L2: `scipy.stats.t.ppf` Called Without Caching**
- File: `src/let_it_ride/analytics/statistics.py`
- Line: 422
- Issue: The t-distribution critical value is computed fresh each time. For repeated calls with the same confidence level and similar sample sizes, this could be cached.
- Impact: Minor - t.ppf is fast, but repeated calls add up.
- Recommendation: Consider `@lru_cache` for t-critical value lookups if called frequently with same parameters.

**L3: Good Use of `__slots__` and Frozen Dataclasses**
- File: `src/let_it_ride/analytics/statistics.py`
- Lines: 170, 185, 212, 231
- Impact: Positive - reduces memory footprint per instance and prevents accidental attribute assignment.

## Recommendations

1. **Immediate (High Priority)**: Consolidate the multiple iterations in `_calculate_risk_metrics` into a single pass through the data. This is a straightforward change with clear benefit.

2. **Short-term (Medium Priority)**: Combine skewness and kurtosis calculations into a single function that computes both in one pass.

3. **Future Consideration**: If profiling shows statistics calculation as a bottleneck at scale, refactor to use NumPy arrays. The current implementation is clean and correct; NumPy would be an optimization if needed.

## Performance Impact Assessment

Given the project's performance targets (100,000 hands/second, <4GB RAM for 10M hands):

- **Will not block targets**: The statistics module is called once after simulation completes, not per-hand. The inefficiencies identified affect post-processing time, not throughput.
- **Memory**: The module creates additional tuples (profits, drawdowns, percentiles), but these are small relative to the session count, not the hand count. For 10,000 sessions, overhead is negligible.
- **Recommendation**: The current implementation is acceptable for the target scale. Apply optimizations if statistics calculation time becomes noticeable (>1 second for typical workloads).

## Code Quality Notes

The implementation correctly uses:
- Frozen dataclasses for immutability
- `__slots__` for memory efficiency
- Type hints throughout
- Appropriate edge case handling (empty data, single values, zero variance)
