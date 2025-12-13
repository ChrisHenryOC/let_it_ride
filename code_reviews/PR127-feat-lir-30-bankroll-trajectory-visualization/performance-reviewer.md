# Performance Review - PR #127

## Summary

This PR introduces bankroll trajectory visualization with acceptable performance characteristics for post-simulation visualization. The code follows established patterns from `histogram.py`, uses `__slots__` for memory efficiency, and bounds the main plotting loop via `sample_sessions`. One medium-severity issue exists regarding global RNG state mutation that could cause non-deterministic behavior in concurrent contexts.

## Findings

### Critical

None.

### High

None.

### Medium

#### M1: Global Random State Mutation in `_sample_sessions`

**File:** `src/let_it_ride/analytics/visualizations/trajectory.py:89-95` (diff lines 1120-1126)

**Issue:** The `_sample_sessions` function mutates global random state by calling `random.seed(random_seed)`. This pollutes the global RNG state, which can cause:
- Non-deterministic behavior in parallel/concurrent visualization generation
- Interference with the main simulation RNG managed by `RNGManager`
- Test flakiness when tests run in parallel or in unexpected order

```python
if random_seed is not None:
    random.seed(random_seed)  # <-- Mutates global state

indices = random.sample(range(len(results)), n_samples)
```

**Impact:** Thread safety issue; may cause non-reproducible results if visualization is generated while simulation is running or in multi-threaded test environments.

**Recommendation:** Use a local `random.Random` instance:

```python
def _sample_sessions(
    results: list[SessionResult],
    histories: list[list[float]],
    n_samples: int,
    random_seed: int | None,
) -> tuple[list[SessionResult], list[list[float]]]:
    if len(results) <= n_samples:
        return results, histories

    rng = random.Random(random_seed)  # Local instance - no global state mutation
    indices = rng.sample(range(len(results)), n_samples)
    sampled_results = [results[i] for i in indices]
    sampled_histories = [histories[i] for i in indices]
    return sampled_results, sampled_histories
```

This aligns with the project's `RNGManager` philosophy of controlled randomness documented in CLAUDE.md.

---

### Low

#### L1: Intermediate List Allocations in Plotting Loop

**File:** `src/let_it_ride/analytics/visualizations/trajectory.py:166-168` (diff lines 1197-1199)

**Issue:** Creates intermediate lists in the plotting loop:

```python
full_history = [starting_bankroll, *history]
x_values = list(range(len(full_history)))
```

For each trajectory plotted, this creates:
1. A new list by prepending `starting_bankroll` to `history`
2. A new list from a `range` object

**Impact:** Negligible. The loop is bounded by `sample_sessions` (default 20), so at most 20 iterations occur regardless of total session count. Each history typically contains hundreds of values (hands per session), so total additional allocations are bounded by approximately `20 * 2 * 500 = 20,000` floats worst case (~160KB), which is trivial.

**Recommendation:** No change required. The bounded nature of the sampling makes this a non-issue for practical use cases. If `sample_sessions` were ever increased significantly (>1000), consider using numpy arrays with `np.concatenate`.

---

#### L2: Multiple Iteration Passes for Outcome Counting

**File:** `src/let_it_ride/analytics/visualizations/trajectory.py:228-230` (diff lines 1259-1261)

**Issue:** Three generator expressions iterate over `sampled_results`:

```python
win_count = sum(1 for r in sampled_results if r.outcome == SessionOutcome.WIN)
loss_count = sum(1 for r in sampled_results if r.outcome == SessionOutcome.LOSS)
push_count = displayed - win_count - loss_count
```

This iterates over the sampled results twice (for `win_count` and `loss_count`).

**Impact:** Negligible. With default `sample_sessions=20`, this iterates over at most 20 items twice. The third count (`push_count`) correctly uses arithmetic instead of a third iteration.

**Recommendation:** No change required. For cleaner code (not performance), could use `collections.Counter`:

```python
from collections import Counter
outcome_counts = Counter(r.outcome for r in sampled_results)
win_count = outcome_counts[SessionOutcome.WIN]
loss_count = outcome_counts[SessionOutcome.LOSS]
push_count = outcome_counts[SessionOutcome.PUSH]
```

However, the current approach is readable and the performance difference is unmeasurable.

---

#### L3: Label Assignment Logic in Plotting Loop

**File:** `src/let_it_ride/analytics/visualizations/trajectory.py:170-181` (diff lines 1201-1212)

**Issue:** The label assignment logic uses three boolean flags (`wins_plotted`, `losses_plotted`, `pushes_plotted`) and multiple conditional checks per iteration:

```python
label = None
if result.outcome == SessionOutcome.WIN and not wins_plotted:
    label = "Win"
    wins_plotted = True
elif result.outcome == SessionOutcome.LOSS and not losses_plotted:
    label = "Loss"
    losses_plotted = True
elif result.outcome == SessionOutcome.PUSH and not pushes_plotted:
    label = "Push"
    pushes_plotted = True
```

**Impact:** Negligible. This runs at most 20 times (bounded by `sample_sessions`). The if/elif chain has O(1) complexity per iteration with at most 4 comparisons per outcome check.

**Recommendation:** No change required. An alternative using a set would be marginally cleaner but not faster:

```python
plotted_outcomes: set[SessionOutcome] = set()
# ... in loop:
label = None
if result.outcome not in plotted_outcomes:
    label = result.outcome.value.title()  # Assumes enum values are "win", "loss", "push"
    plotted_outcomes.add(result.outcome)
```

---

## Positive Performance Patterns

The implementation demonstrates several good performance practices:

1. **`__slots__` on `TrajectoryConfig`** (line 1056): Correct use of `slots=True` in the dataclass decorator reduces memory footprint and speeds attribute access.

2. **Early Return in `_sample_sessions`** (lines 1117-1118): Correctly short-circuits when sampling is unnecessary (`len(results) <= n_samples`).

3. **Bounded Iteration**: The main plotting loop is bounded by `sample_sessions` (default 20), ensuring O(1) complexity regardless of input size for the core visualization logic.

4. **Proper Figure Cleanup** (lines 1342-1345): The `try/finally` block ensures `plt.close(fig)` is called even if `savefig` fails, preventing matplotlib figure memory leaks.

5. **No N+1 Patterns**: The code does not make repeated I/O calls or expensive computations inside loops.

6. **Input Validation Before Work**: Validates inputs (empty check, length mismatch) before performing any expensive operations.

---

## Performance Target Assessment

**Throughput Target (>=100,000 hands/second):** This visualization code is **NOT on the critical path** for simulation throughput. It is post-processing code that runs after simulation completion. No impact on throughput target.

**Memory Target (<4GB for 10M hands):** The visualization samples down to at most `sample_sessions` trajectories (default 20). Even if each trajectory contains 10,000 hands (floats), the plotted data is bounded at approximately:
- `20 sessions * 10,000 hands * 8 bytes/float = 1.6 MB`

The `bankroll_histories` parameter passed to this function could be large for 10M hands simulations, but this is a concern for the caller (simulation engine), not this visualization code which samples before rendering.

**Verdict:** This code does not block performance targets. The visualization is appropriately decoupled from simulation performance.

---

## Recommendations

| Priority | Issue | File:Line | Action |
|----------|-------|-----------|--------|
| Medium | Global RNG state mutation | trajectory.py:89-95 | Replace `random.seed()` with local `random.Random()` instance |
| Low | List allocations in loop | trajectory.py:166-168 | No action (bounded by sample_sessions) |
| Low | Multiple counting passes | trajectory.py:228-230 | No action (negligible with N=20) |
| Low | Label assignment logic | trajectory.py:170-181 | No action (negligible with N=20) |

**Recommended Action Before Merge:** Address the medium-severity global RNG state mutation issue to ensure thread safety and consistency with the project's RNG management philosophy. The low-severity items can be ignored as they have negligible impact given the bounded input size from `sample_sessions`.
