# Performance Review: PR #127 - LIR-30 Bankroll Trajectory Visualization

## Summary

This PR introduces bankroll trajectory visualization with generally acceptable performance characteristics for its visualization use case. The code follows established patterns from the histogram module and uses `__slots__` for memory efficiency. However, there is one medium-severity issue related to global random state mutation that could cause non-deterministic behavior in parallel contexts, and a few minor memory optimization opportunities.

## Findings by Severity

### Medium Severity

#### 1. Global Random State Mutation in `_sample_sessions`

**File:** `src/let_it_ride/analytics/visualizations/trajectory.py:243-244`

**Issue:** The function calls `random.seed(random_seed)` which mutates global random state. This can cause subtle bugs in concurrent/parallel execution where multiple threads share the global random state.

```python
def _sample_sessions(
    results: list[SessionResult],
    histories: list[list[float]],
    n_samples: int,
    random_seed: int | None,
) -> tuple[list[SessionResult], list[list[float]]]:
    # ...
    if random_seed is not None:
        random.seed(random_seed)  # Mutates global state
    indices = random.sample(range(len(results)), n_samples)
```

**Recommendation:** Use a local `random.Random` instance instead:

```python
def _sample_sessions(
    results: list[SessionResult],
    histories: list[list[float]],
    n_samples: int,
    random_seed: int | None,
) -> tuple[list[SessionResult], list[list[float]]]:
    if len(results) <= n_samples:
        return results, histories

    rng = random.Random(random_seed)  # Local instance
    indices = rng.sample(range(len(results)), n_samples)
    sampled_results = [results[i] for i in indices]
    sampled_histories = [histories[i] for i in indices]
    return sampled_results, sampled_histories
```

**Impact:** Thread safety issue; may cause non-reproducible results in parallel visualization generation.

---

### Low Severity

#### 2. Unnecessary List Creation with Unpacking

**File:** `src/let_it_ride/analytics/visualizations/trajectory.py:319-321`

**Issue:** Creates a new list by prepending starting_bankroll using unpacking, then creates another range-based list for x_values. For large histories, this creates memory pressure.

```python
full_history = [starting_bankroll, *history]
x_values = list(range(len(full_history)))
```

**Context:** This occurs inside the plotting loop but is bounded by `sample_sessions` (default 20), so the actual impact is minimal. However, for sessions with thousands of hands each, this creates unnecessary intermediate allocations.

**Recommendation:** For a cleaner approach without extra allocations:

```python
# Plot starting point separately, then history
ax.plot(
    range(len(history) + 1),
    [starting_bankroll, *history],
    # ... rest of params
)
```

Or if performance became critical, use numpy arrays and `np.concatenate`.

**Impact:** Negligible for typical usage (20 sessions x hundreds of hands). Only relevant if sample_sessions is increased significantly.

---

#### 3. Multiple Passes Over Sampled Results for Counting

**File:** `src/let_it_ride/analytics/visualizations/trajectory.py:382-384`

**Issue:** Three generator expressions iterate over `sampled_results` to count outcomes:

```python
win_count = sum(1 for r in sampled_results if r.outcome == SessionOutcome.WIN)
loss_count = sum(1 for r in sampled_results if r.outcome == SessionOutcome.LOSS)
push_count = displayed - win_count - loss_count
```

**Context:** This iterates over the sampled list twice (win_count and loss_count). With default `sample_sessions=20`, this is negligible.

**Recommendation:** Could be consolidated into a single pass with Counter, but given the small N (max 20 by default), this is not worth changing:

```python
from collections import Counter
outcome_counts = Counter(r.outcome for r in sampled_results)
win_count = outcome_counts[SessionOutcome.WIN]
loss_count = outcome_counts[SessionOutcome.LOSS]
push_count = outcome_counts[SessionOutcome.PUSH]
```

**Impact:** Negligible. The sample_sessions parameter bounds this to a small number.

---

## Items Reviewed - No Issues Found

### Positive Performance Patterns

1. **`__slots__` usage on `TrajectoryConfig`** (line 179): Correct use of `slots=True` in the dataclass decorator reduces memory footprint and improves attribute access speed.

2. **Early return in `_sample_sessions`** (line 240-241): Correctly short-circuits when sampling is unnecessary.

3. **Proper figure cleanup** (lines 465-468): The `try/finally` block ensures `plt.close(fig)` is called even if `savefig` fails, preventing memory leaks from unclosed figures.

4. **Bounded iteration**: The main plotting loop is bounded by `sample_sessions` (default 20), ensuring visualization generation time is predictable regardless of input size.

5. **No N+1 patterns**: The code does not make repeated I/O or expensive computations inside loops.

### Performance Target Assessment

This visualization code is **not on the critical path** for the simulation throughput target of >=100,000 hands/second. It is post-processing/reporting code that runs after simulation completion. The memory usage is well-controlled through the `sample_sessions` parameter which limits the amount of data actually rendered.

The `bankroll_histories` data structure (`list[list[float]]`) passed to this function could be large for 10M hands, but this is a concern for the caller (simulation engine), not this visualization code which samples down to a manageable subset.

---

## Recommendations Summary

| Priority | Issue | File:Line | Effort |
|----------|-------|-----------|--------|
| Medium | Global random state mutation | trajectory.py:243-244 | Low |
| Low | Unnecessary list unpacking | trajectory.py:319-321 | Low |
| Low | Multiple counting passes | trajectory.py:382-384 | Low |

**Recommended Action:** Address the medium-severity global random state issue before merge. The low-severity items can be deferred or ignored as they have negligible impact given the bounded input size from `sample_sessions`.
