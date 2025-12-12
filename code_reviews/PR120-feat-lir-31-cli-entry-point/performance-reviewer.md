# Performance Review - PR #120

## Summary

The CLI implementation is well-designed from a performance perspective. It does not introduce any critical bottlenecks that would prevent meeting the 100,000 hands/second target, as the actual simulation work is delegated to the existing `SimulationController`. The CLI layer adds minimal overhead through Pydantic model copies for config overrides and three generator comprehensions for statistics calculation, which are appropriate for the expected scale.

## Findings

### Critical

None.

### High

None.

### Medium

#### 1. Triple Iteration Over session_results for Statistics Calculation
**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/cli.py` (lines 220-226)

```python
winning_sessions = sum(1 for r in results.session_results if r.session_profit > 0)
losing_sessions = sum(1 for r in results.session_results if r.session_profit < 0)
# ...
total_profit = sum(r.session_profit for r in results.session_results)
```

The code iterates over `session_results` three separate times to calculate statistics. For simulations with many sessions (e.g., 1M sessions), this could add noticeable overhead.

**Impact:** For typical usage (hundreds to thousands of sessions), this is negligible. For extreme cases (1M+ sessions), consolidating into a single pass would provide modest improvement.

**Recommendation:** Consider consolidating into a single-pass calculation if session counts are expected to reach hundreds of thousands:

```python
winning_sessions = losing_sessions = total_profit = 0
for r in results.session_results:
    total_profit += r.session_profit
    if r.session_profit > 0:
        winning_sessions += 1
    elif r.session_profit < 0:
        losing_sessions += 1
```

However, given typical usage patterns (< 100K sessions) and that this is one-time post-processing, this is a low-priority optimization.

### Low

#### 2. Pydantic model_copy() Calls for Config Overrides
**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/cli.py` (lines 145-164)

```python
cfg = cfg.model_copy(
    update={
        "simulation": sim_config.model_copy(
            update={...}
        )
    }
)
```

The code uses nested `model_copy()` calls to apply CLI overrides. This creates intermediate Pydantic model instances, but occurs only once at startup.

**Impact:** Negligible. This is a one-time operation at CLI startup, not in any hot path.

**Status:** Acceptable - this is idiomatic Pydantic usage.

#### 3. Progress Callback Overhead in Sequential Mode
**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/cli.py` (lines 182-185)

```python
def progress_callback(completed: int, total: int) -> None:
    """Update progress bar."""
    if progress_bar is not None and task_id is not None:
        progress_bar.update(task_id, completed=completed, total=total)
```

The callback is invoked after each session. The closure access and Rich's `Progress.update()` call add some overhead per-session.

**Impact:** Minimal. The callback is called once per session (not per hand), and the overhead is dominated by I/O in Progress.update(). For 10K sessions, this might add a few milliseconds total.

**Status:** Acceptable - user feedback through progress bars is worth this minimal cost.

#### 4. Verbose Mode Output in Hot Path (Bounded by Session Count)
**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/cli.py` (lines 261-273)

```python
for i, r in enumerate(results.session_results):
    outcome_color = (
        "green" if r.session_profit > 0
        else "red" if r.session_profit < 0
        else "yellow"
    )
    console.print(...)
```

Verbose mode prints details for every session, which involves Rich formatting overhead per line.

**Impact:** For large session counts (10K+), verbose output could take noticeable time (seconds) due to terminal I/O. However, this is expected behavior for verbose mode and users requesting detailed output accept this tradeoff.

**Status:** Acceptable - verbose mode is opt-in and expected to be slower.

## Recommendations

1. **No immediate action required** - The CLI implementation is performant for its intended use case.

2. **Consider single-pass statistics** (low priority) - If simulations with > 100K sessions become common, consolidate the three generator comprehensions at lines 220-226 into a single loop.

3. **Consider verbose output limits** (future enhancement) - If verbose mode is used with very high session counts, consider adding a `--limit` option or automatic truncation with a message like "Showing first N of M sessions...".

4. **Startup time is acceptable** - Module imports (Typer, Rich, Pydantic, simulation modules) add typical Python startup overhead (~200-500ms depending on system). This is standard for CLI tools with rich dependencies.

## Positive Observations

1. **Delegation to SimulationController** - All heavy simulation work is properly delegated to the existing optimized `SimulationController`, keeping the CLI layer thin.

2. **Quiet mode available** - The `--quiet` flag skips progress bar overhead and verbose output, enabling maximum throughput for scripted/batch usage.

3. **No unnecessary object creation** - The CLI avoids creating intermediate data structures or copying large result sets.

4. **Generator expressions** - Statistics use generator expressions rather than building intermediate lists, keeping memory usage O(1) for the statistics calculation.

5. **CSVExporter uses streaming** - The export layer (not modified in this PR but used here) supports streaming/generator-based exports for memory efficiency with large datasets.

## Files Reviewed

- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/cli.py` (325 lines) - Main CLI implementation
- `/Users/chrishenry/source/let_it_ride/tests/integration/test_cli.py` (426 lines) - Integration tests
- `/Users/chrishenry/source/let_it_ride/tests/unit/test_cli.py` (86 lines) - Unit tests

## Performance Target Compliance

| Target | Status | Notes |
|--------|--------|-------|
| >= 100,000 hands/second | **Pass** | CLI layer adds negligible overhead; throughput determined by SimulationController |
| < 4GB RAM for 10M hands | **Pass** | CLI does not buffer or copy large data; statistics use O(1) memory |
