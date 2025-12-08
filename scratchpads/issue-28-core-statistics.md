# LIR-25: Core Statistics Calculator

**GitHub Issue:** https://github.com/ChrisHenryOC/let_it_ride/issues/28

## Overview

Implement calculation of all primary statistics from simulation results. This provides detailed statistical analysis beyond what's in `AggregateStatistics`.

## Planned Tasks

1. [ ] Create `ConfidenceInterval` dataclass
2. [ ] Create `DistributionStats` dataclass with skewness, kurtosis, percentiles
3. [ ] Create `DetailedStatistics` dataclass as the main output
4. [ ] Implement `calculate_statistics()` function
5. [ ] Implement Wilson score interval helper (reuse from validation.py)
6. [ ] Implement mean confidence interval calculation (using t-distribution)
7. [ ] Implement percentile calculations (5th, 25th, 50th, 75th, 95th)
8. [ ] Implement skewness calculation
9. [ ] Implement kurtosis calculation (excess kurtosis)
10. [ ] Implement IQR calculation
11. [ ] Implement risk metrics (probability of specific loss levels)
12. [ ] Write comprehensive unit tests with known data sets
13. [ ] Test numerical stability with edge cases

## Key Design Decisions

### Input Data
- Primary input: `AggregateStatistics` from simulation/aggregation.py
- Access `session_profits: tuple[float, ...]` for distribution calculations
- May also accept raw `list[SessionResult]` as convenience

### Reuse from validation.py
- `calculate_wilson_confidence_interval()` already implemented
- Import and reuse rather than duplicate

### Statistical Calculations

**Skewness (Fisher-Pearson):**
```
g1 = (n / ((n-1)(n-2))) * sum((xi - mean)^3) / std^3
```

**Kurtosis (excess, Fisher):**
```
g2 = ((n(n+1)) / ((n-1)(n-2)(n-3))) * sum((xi - mean)^4) / std^4 - 3*(n-1)^2/((n-2)(n-3))
```

**Percentiles:**
- Use `statistics.quantiles(data, n=100)` for Python 3.10+
- Map indices: percentile 5 → index 4, percentile 25 → index 24, etc.

**Mean CI (t-distribution):**
```
CI = mean ± t(α/2, n-1) * (std / sqrt(n))
```

### Risk Metrics
- P(loss > X) for configurable loss levels
- Based on empirical distribution (count sessions with profit < -X)

## Files to Create/Modify

- `src/let_it_ride/analytics/statistics.py` (new)
- `tests/unit/analytics/test_statistics.py` (new)
- `src/let_it_ride/analytics/__init__.py` (update exports)

## Dependencies

- LIR-22 (Simulation Results Aggregation) ✅ Complete
- Uses scipy.stats for t-distribution critical values

## Test Cases

1. Known dataset with manually calculated values
2. Single session (edge case)
3. All same values (zero variance edge case)
4. Highly skewed distribution
5. Normal-like distribution
6. Empty data (should raise ValueError)
7. Numerical stability with very large/small values
