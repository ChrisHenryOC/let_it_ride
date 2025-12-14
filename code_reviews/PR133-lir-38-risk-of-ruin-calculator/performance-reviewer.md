# Performance Review - PR #133

## Summary

The Monte Carlo risk of ruin calculator has a critical performance issue: the inner simulation loop at lines 191-214 in `risk_of_ruin.py` uses pure Python iteration over 10,000 sessions per simulation across 10,000 simulations (default), resulting in 100 million Python loop iterations per bankroll level. This should be vectorized using NumPy cumulative sums and threshold detection for orders-of-magnitude speedup. The visualization code is appropriately efficient for its use case.

## Findings

### Critical

**[C1] Pure Python nested loops in Monte Carlo simulation - O(simulations * max_sessions_per_sim) Python iterations**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py`
Lines: 191-214

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

With default parameters of `simulations=10000` and `max_sessions_per_sim=10000`, this creates up to 100 million Python loop iterations per bankroll level. For 5 bankroll levels, that is 500 million iterations total.

**Recommended fix:** Vectorize using NumPy:
```python
# Sample all at once: shape (simulations, max_sessions_per_sim)
all_samples = rng.choice(session_profits, size=(simulations, max_sessions_per_sim))
# Cumulative sum along axis 1
trajectories = bankroll + np.cumsum(all_samples, axis=1)
# Find first crossing of each threshold per simulation
ruin_mask = np.any(trajectories <= 0, axis=1)
half_mask = np.any(trajectories <= half_threshold, axis=1)
quarter_mask = np.any(trajectories <= quarter_threshold, axis=1)
```

This would reduce runtime from minutes to sub-second for typical parameters.

### High

**[H1] Redundant array allocation inside simulation loop**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py`
Lines: 196-197

```python
for _ in range(simulations):
    ...
    sampled_profits = rng.choice(session_profits, size=max_sessions_per_sim)
```

Each simulation iteration allocates a new array of 10,000 elements. With 10,000 simulations, this creates 10,000 allocations per bankroll level. Pre-allocating a batch or generating all samples upfront would reduce allocation overhead.

**[H2] Sequential processing of bankroll levels - no parallelization**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py`
Lines: 346-354

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

Each bankroll level is computed sequentially. Since they are independent, these could be computed in parallel using `concurrent.futures.ThreadPoolExecutor` or `ProcessPoolExecutor` (especially after vectorization releases the GIL during NumPy operations).

### Medium

**[M1] Using Python stdlib `mean()` instead of NumPy for array data**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py`
Lines: 333-334

```python
mean_profit = float(mean(session_profits))
```

The `session_profits` is already a NumPy array, but the code uses `statistics.mean()` which requires converting to Python floats. Use `np.mean()` for better performance:
```python
mean_profit = float(np.mean(session_profits))
```

**[M2] Multiple passes over session_results for data extraction**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py`
Lines: 317-327

```python
session_profits = np.array([r.session_profit for r in session_results])
starting_bankroll = session_results[0].starting_bankroll

if base_bet is None:
    total_wagered = sum(r.total_wagered for r in session_results)
    total_hands = sum(r.hands_played for r in session_results)
```

This iterates over `session_results` up to 3 times. Could be consolidated into a single pass:
```python
profits, wagered, hands = [], 0, 0
for r in session_results:
    profits.append(r.session_profit)
    if base_bet is None:
        wagered += r.total_wagered
        hands += r.hands_played
session_profits = np.array(profits)
```

**[M3] Visualization creates multiple NumPy arrays from same source**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/visualizations/risk_curves.py`
Lines: 73-79

```python
bankroll_units = np.array([r.bankroll_units for r in report.results])
ruin_probs = np.array([r.ruin_probability for r in report.results])
half_risks = np.array([r.half_bankroll_risk for r in report.results])
quarter_risks = np.array([r.quarter_bankroll_risk for r in report.results])
ci_lowers = np.array([r.confidence_interval.lower for r in report.results])
ci_uppers = np.array([r.confidence_interval.upper for r in report.results])
```

Six separate iterations over `report.results`. For small result sets this is negligible, but could be single-pass for consistency.

### Low

**[L1] Late import inside function**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/visualizations/risk_curves.py`
Lines: 190-191

```python
from matplotlib.ticker import FuncFormatter
ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y:.0%}"))
```

Import is inside the function. While matplotlib is already imported at module level, this specific import could be moved to the top for marginal improvement and cleaner code.

**[L2] Repeated string formatting in report formatter**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py`
Lines: 402-417

The formatting loop creates many intermediate strings. For large reports, using `io.StringIO` would be more efficient, though with typical result sizes (5-10 levels) this is not significant.

### Positive

**[P1] Good use of `__slots__` on dataclasses**

Files: `risk_of_ruin.py` lines 29, 50; `risk_curves.py` line 18

```python
@dataclass(frozen=True, slots=True)
class RiskOfRuinResult:
```

Using `slots=True` reduces memory footprint per instance and improves attribute access speed.

**[P2] Proper use of NumPy random Generator API**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py`
Line: 340

```python
rng = np.random.default_rng(random_seed)
```

Using the modern `numpy.random.Generator` API instead of the legacy `numpy.random` functions provides better statistical properties and thread safety.

**[P3] Efficient analytical formula with overflow protection**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py`
Lines: 152-159

```python
exponent = -2 * mean_profit * bankroll / (std_profit**2)
if exponent < -700:
    return 0.0
return math.exp(exponent)
```

Good handling of numerical edge cases to prevent overflow.

**[P4] Proper figure cleanup in visualization**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/visualizations/risk_curves.py`
Lines: 257-260

```python
try:
    fig.savefig(path, format=output_format, dpi=config.dpi, bbox_inches="tight")
finally:
    plt.close(fig)
```

Using `try/finally` to ensure figure is closed prevents memory leaks from accumulated matplotlib figures.

**[P5] Wilson confidence interval is O(1) per calculation**

The confidence interval calculation uses the Wilson score interval which is a closed-form formula, avoiding any iterative methods that could add overhead.

## Performance Impact Assessment

| Finding | Impact on 100K hands/sec target | Impact on 4GB memory target |
|---------|--------------------------------|----------------------------|
| C1 | BLOCKING - Current implementation may take minutes per report | Moderate - 100M loop iterations have overhead |
| H1 | High - Excessive allocations add GC pressure | Moderate - 10K arrays per level |
| H2 | Medium - Linear scaling with bankroll levels | None |
| M1-M3 | Low - Marginal improvement opportunities | None |

The critical finding (C1) directly blocks meeting performance targets. With vectorization, the Monte Carlo simulation should complete in under 1 second for typical parameters, compared to potentially several minutes with pure Python loops.
