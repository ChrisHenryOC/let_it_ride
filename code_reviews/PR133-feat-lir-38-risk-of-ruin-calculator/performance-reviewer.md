# Performance Review - PR #133

## Summary

The Monte Carlo risk of ruin calculator contains a critical performance bottleneck: the inner simulation loop at lines 191-214 in `risk_of_ruin.py` uses pure Python iteration over up to 100 million iterations (10,000 simulations x 10,000 sessions per simulation) per bankroll level. With 5 default bankroll levels, this creates 500 million Python loop iterations. This should be vectorized using NumPy operations for orders-of-magnitude improvement. Additional concerns include redundant array allocation inside the simulation loop and sequential processing of independent bankroll levels.

## Findings

### Critical

**[C1] Pure Python nested loops in Monte Carlo simulation - O(simulations x max_sessions_per_sim) Python iterations**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py`
Lines: 191-214 (in diff), actual lines 162-214

```python
for _ in range(simulations):
    current_bankroll = bankroll
    hit_half = False
    hit_quarter = False

    # Sample session outcomes
    sampled_profits = rng.choice(session_profits, size=max_sessions_per_sim)

    for profit in sampled_profits:
        current_bankroll += profit

        # Track threshold crossings
        if not hit_quarter and current_bankroll <= quarter_threshold:
            hit_quarter = True
            quarter_loss_count += 1

        if not hit_half and current_bankroll <= half_threshold:
            hit_half = True
            half_loss_count += 1

        # Check for ruin
        if current_bankroll <= 0:
            ruin_count += 1
            break
```

With default parameters of `simulations=10000` and `max_sessions_per_sim=10000`, this creates up to 100 million Python loop iterations per bankroll level. For 5 bankroll levels, that is 500 million iterations total. Given the project target of 100,000 hands/second, this implementation will take minutes to complete a single risk of ruin report.

**Impact on Performance Targets:**
- The inner Python loop is approximately 100-1000x slower than equivalent vectorized NumPy operations
- A single `calculate_risk_of_ruin()` call with defaults could take 2-10 minutes
- This directly blocks meeting the project performance target

**Recommended Fix:** Vectorize using NumPy:
```python
# Sample all at once: shape (simulations, max_sessions_per_sim)
all_samples = rng.choice(session_profits, size=(simulations, max_sessions_per_sim))

# Cumulative sum along axis 1 to create all trajectories
trajectories = bankroll + np.cumsum(all_samples, axis=1)

# Find threshold crossings using vectorized operations
ruin_mask = np.any(trajectories <= 0, axis=1)
half_mask = np.any(trajectories <= half_threshold, axis=1)
quarter_mask = np.any(trajectories <= quarter_threshold, axis=1)

ruin_count = np.sum(ruin_mask)
half_loss_count = np.sum(half_mask)
quarter_loss_count = np.sum(quarter_mask)
```

This would reduce runtime from minutes to sub-second for typical parameters.

### High

**[H1] Redundant array allocation inside simulation loop**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py`
Lines: 196-197 (in diff)

```python
for _ in range(simulations):
    ...
    sampled_profits = rng.choice(session_profits, size=max_sessions_per_sim)
```

Each simulation iteration allocates a new NumPy array of 10,000 float64 elements (80KB per allocation). With 10,000 simulations, this creates 10,000 allocations per bankroll level, totaling approximately 800MB of allocation churn per level.

**Impact:**
- Excessive garbage collection pressure
- Memory fragmentation
- Additional overhead beyond the loop iteration cost

**Recommended Fix:** Pre-allocate all samples in a single call (as shown in C1 fix) or pre-allocate a reusable buffer.

---

**[H2] Sequential processing of independent bankroll levels - no parallelization**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py`
Lines: 346-354 (in diff), actual lines around 275-283

```python
for units in sorted(bankroll_units):
    result = _calculate_ruin_for_bankroll_level(
        session_profits=session_profits,
        base_bet=base_bet,
        bankroll_units=units,
        ...
    )
    results.append(result)
```

Each bankroll level is computed sequentially. Since they are independent calculations, these could be parallelized. With 5 default bankroll levels and the current slow implementation, this adds linear scaling to an already slow operation.

**Recommended Fix:** After vectorizing the Monte Carlo simulation (C1), consider parallelizing with `concurrent.futures.ThreadPoolExecutor` or `ProcessPoolExecutor` for additional speedup. Note that after vectorization, NumPy operations release the GIL, making thread-based parallelism effective.

### Medium

**[M1] Using Python stdlib `mean()` instead of NumPy for array data**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py`
Lines: 333-334 (in diff), actual around line 251

```python
mean_profit = float(mean(session_profits))
```

The `session_profits` is already a NumPy array, but the code uses `statistics.mean()` which internally iterates over the data as Python objects. Using `np.mean()` would be more efficient:

```python
mean_profit = float(np.mean(session_profits))
```

**Impact:** Minor for small arrays, but adds unnecessary overhead when `session_profits` is already a NumPy array.

---

**[M2] Multiple passes over session_results for data extraction**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py`
Lines: 317-327 (in diff), actual around lines 235-245

```python
session_profits = np.array([r.session_profit for r in session_results])
starting_bankroll = session_results[0].starting_bankroll

if base_bet is None:
    total_wagered = sum(r.total_wagered for r in session_results)
    total_hands = sum(r.hands_played for r in session_results)
```

This iterates over `session_results` up to 3 times. Could be consolidated:

```python
profits, wagered, hands = [], 0, 0
starting_bankroll = session_results[0].starting_bankroll
for r in session_results:
    profits.append(r.session_profit)
    if base_bet is None:
        wagered += r.total_wagered
        hands += r.hands_played
session_profits = np.array(profits)
```

**Impact:** Minor - the session_results list is typically small (10-10,000 items) compared to the simulation iterations.

---

**[M3] Visualization creates multiple NumPy arrays from same source**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/visualizations/risk_curves.py`
Lines: 73-79 (in diff), actual around lines 57-63

```python
bankroll_units = np.array([r.bankroll_units for r in report.results])
ruin_probs = np.array([r.ruin_probability for r in report.results])
half_risks = np.array([r.half_bankroll_risk for r in report.results])
quarter_risks = np.array([r.quarter_bankroll_risk for r in report.results])
ci_lowers = np.array([r.confidence_interval.lower for r in report.results])
ci_uppers = np.array([r.confidence_interval.upper for r in report.results])
```

Six separate iterations over `report.results`. For small result sets (5-10 items) this is negligible, but could be a single-pass extraction for consistency.

**Impact:** Negligible given typical result set sizes.

### Low

**[L1] Late import inside function**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/visualizations/risk_curves.py`
Lines: 190-191 (in diff), actual around lines 174-175

```python
from matplotlib.ticker import FuncFormatter
ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y:.0%}"))
```

Import is inside the function body. While matplotlib is already imported at module level, this specific import could be moved to the top for marginal improvement and cleaner code organization.

**Impact:** Minimal - only affects first call to the function.

---

**[L2] Repeated string formatting in report formatter**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py`
Lines: 402-417 (in diff)

The formatting loop creates many intermediate strings. For large reports, using `io.StringIO` would be more efficient, though with typical result sizes (5-10 levels) this is not significant.

**Impact:** Negligible for typical use cases.

### Informational

**[I1] Good use of `__slots__` on dataclasses**

Files: `risk_of_ruin.py` lines 29, 50; `risk_curves.py` line 18

```python
@dataclass(frozen=True, slots=True)
class RiskOfRuinResult:
```

Using `slots=True` reduces memory footprint per instance and improves attribute access speed. This is a positive pattern.

---

**[I2] Proper use of NumPy random Generator API**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py`
Line: 340 (in diff)

```python
rng = np.random.default_rng(random_seed)
```

Using the modern `numpy.random.Generator` API instead of the legacy `numpy.random` functions provides better statistical properties and thread safety.

---

**[I3] Efficient analytical formula with overflow protection**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py`
Lines: 152-159 (in diff)

```python
exponent = -2 * mean_profit * bankroll / (std_profit**2)
if exponent < -700:
    return 0.0
return math.exp(exponent)
```

Good handling of numerical edge cases to prevent floating-point overflow.

---

**[I4] Proper figure cleanup in visualization**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/visualizations/risk_curves.py`
Lines: 257-260 (in diff)

```python
try:
    fig.savefig(path, format=output_format, dpi=config.dpi, bbox_inches="tight")
finally:
    plt.close(fig)
```

Using `try/finally` to ensure figure is closed prevents memory leaks from accumulated matplotlib figures.

---

**[I5] Wilson confidence interval is O(1) per calculation**

The confidence interval calculation uses the Wilson score interval which is a closed-form formula, avoiding any iterative methods that could add overhead.

## Performance Impact Assessment

| Finding | Impact on 100K hands/sec target | Impact on 4GB memory target |
|---------|--------------------------------|----------------------------|
| C1 | **BLOCKING** - Current implementation may take minutes per report | Moderate - 100M loop iterations have significant overhead |
| H1 | High - Excessive allocations add GC pressure | Moderate - 800MB allocation churn per bankroll level |
| H2 | Medium - Linear scaling with bankroll levels | None |
| M1-M3 | Low - Marginal improvement opportunities | None |
| L1-L2 | Negligible | None |

## Recommendations Summary

1. **Critical (Must Fix):** Vectorize the Monte Carlo simulation using NumPy `cumsum` and array operations. This is the single most impactful change and will improve performance by 100-1000x.

2. **High Priority:** Pre-allocate samples as part of the vectorization fix. Consider parallelization across bankroll levels for additional speedup.

3. **Medium Priority:** Use `np.mean()` and `np.std()` consistently with NumPy arrays. Consolidate iteration over session_results.

4. **Low Priority:** Move FuncFormatter import to module level. These are minor style improvements.

## Memory Usage Estimate

With default parameters after vectorization:
- Sample array: 10,000 simulations x 10,000 sessions x 8 bytes = 800MB per bankroll level
- With 5 bankroll levels processed sequentially: peak 800MB (if arrays are deallocated between levels)

This is within the 4GB budget but should be monitored. Consider processing in batches if memory becomes an issue with larger simulation parameters.
