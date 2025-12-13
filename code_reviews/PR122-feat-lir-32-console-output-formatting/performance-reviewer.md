# Performance Review

## Summary

This PR introduces console output formatting using the Rich library. The implementation is well-structured with appropriate use of `__slots__` on the `OutputFormatter` class to reduce memory overhead. However, there is a notable performance concern in `app.py` where `aggregate_results()` is now called redundantly after simulation completion, potentially causing duplicate iteration over session results. The formatting code itself is display-only and executes after simulation, so it does not impact the core performance target of 100,000 hands/second.

## Findings

### Critical

None identified.

### High

**H1: Redundant aggregation computation in app.py**
- **File:** `src/let_it_ride/cli/app.py:255`
- **Issue:** The `aggregate_results()` function is called after simulation completes to compute statistics for display. However, this aggregation involves iterating over all `session_results` and computing statistics (mean, median, stdev) which may already be computed elsewhere or could be computed once and reused.
- **Impact:** For large simulations (e.g., 100,000 sessions), this adds O(n) iteration with statistical computations. The `statistics.stdev()` and `statistics.median()` functions in Python's standard library have O(n) complexity, and median requires sorting internally.
- **Previous Code:** The old code (lines 224-235, now removed) performed a simple single-pass iteration to compute win/loss counts and profit totals. The new code delegates to `aggregate_results()` which computes significantly more statistics.
- **Recommendation:** If the simulation controller already produces aggregate statistics, pass them through rather than recomputing. Alternatively, consider lazy computation in `AggregateStatistics` for statistics only needed in verbose mode.

### Medium

**M1: Repeated dictionary lookups in print_hand_frequencies()**
- **File:** `src/let_it_ride/cli/formatters.py:627-632` (diff lines)
- **Issue:** The loop calls `frequencies.get(rank, 0)` and `HAND_RANK_DISPLAY.get(rank, rank)` for each rank in `HAND_RANK_ORDER`. While dictionaries have O(1) average lookup, the pattern of iterating a fixed list and doing lookups could be slightly optimized.
- **Impact:** Minimal - only 11 iterations for a fixed set of hand ranks. This is display code and not in the simulation hot path.
- **Code Location:** formatters.py lines 626-632 in the diff (absolute lines 316-322 in the new file)
```python
for rank in HAND_RANK_ORDER:
    count = frequencies.get(rank, 0)
    if count > 0:
        pct = count / total
        display_name = HAND_RANK_DISPLAY.get(rank, rank)
        table.add_row(display_name, f"{count:,}", self._format_percent(pct, 2))
```
- **Recommendation:** No change needed - impact is negligible for display code.

**M2: String concatenation in _color() helper**
- **File:** `src/let_it_ride/cli/formatters.py:408-410` (diff lines)
- **Issue:** The `_color()` method creates f-strings with Rich markup tags. This is called repeatedly for colorized output.
- **Impact:** Minimal for display code. F-string formatting is efficient in Python 3.6+.
- **Recommendation:** No change needed - this is idiomatic Python and performance is acceptable for display purposes.

**M3: Table creation overhead per method call**
- **File:** `src/let_it_ride/cli/formatters.py` (multiple methods)
- **Issue:** Each `print_*` method creates a new `Table` object. Rich's `Table` class has some initialization overhead.
- **Impact:** Negligible - tables are created once per simulation completion, not per hand.
- **Recommendation:** No change needed - this is appropriate for the use case.

### Low

**L1: Use of `__slots__` is good practice**
- **File:** `src/let_it_ride/cli/formatters.py:379`
- **Note:** The `OutputFormatter` class correctly uses `__slots__ = ("verbosity", "use_color", "console")` which reduces memory footprint and slightly improves attribute access speed. This is good practice for a class that may be instantiated frequently.

**L2: Early return pattern for verbosity checks is efficient**
- **File:** `src/let_it_ride/cli/formatters.py` (multiple methods)
- **Note:** Methods like `print_config_summary()`, `print_statistics()`, etc. check `self.verbosity` at the top and return early if the output should be suppressed. This avoids unnecessary computation in quiet mode.

**L3: Type hints use TYPE_CHECKING guard appropriately**
- **File:** `src/let_it_ride/cli/formatters.py:328`
- **Note:** Imports for type hints are guarded with `if TYPE_CHECKING:` to avoid import overhead at runtime. This is good practice.

**L4: Consider lazy formatting for large session lists**
- **File:** `src/let_it_ride/cli/formatters.py:637-666` (print_session_details method)
- **Issue:** For verbose mode with many sessions, `print_session_details()` iterates over all results and formats each one.
- **Impact:** Could be slow for simulations with 100,000+ sessions in verbose mode, but this is user-requested behavior.
- **Recommendation:** Consider adding a `max_session_display` parameter to limit output for very large simulations, with a summary like "... and 99,990 more sessions".

## Recommendations

### Priority 1: Avoid Redundant Aggregation

The most significant performance improvement would be to avoid redundant aggregation. Options:

1. **Preferred:** Have `SimulationController` return pre-computed aggregate statistics along with `SimulationResults`, so the CLI does not need to recompute.

2. **Alternative:** If aggregation must happen in the CLI, ensure it only happens once and the result is passed to all formatters.

Current flow in `app.py`:
```python
# Line 255 - new code
stats = aggregate_results(results.session_results)
formatter.print_statistics(stats, duration_secs)
formatter.print_hand_frequencies(stats.hand_frequencies)
```

The `aggregate_results()` function (from `aggregation.py`) performs:
- 3 separate generator passes for win/loss/push counts (lines 134-136)
- 1 sum for total hands
- Multiple sums for financial metrics
- Tuple creation for all session profits
- Statistics module calls: `mean()`, `stdev()`, `median()`, `min()`, `max()`

For 100,000 sessions, this is not negligible, though it only runs once after simulation completion.

### Priority 2: Session Details Limit

For verbose mode, add a configurable limit to session details display:

```python
def print_session_details(
    self,
    results: list[SessionResult],
    max_display: int = 100
) -> None:
    """Display per-session details (verbose mode only).

    Args:
        results: List of session results.
        max_display: Maximum number of sessions to display (default 100).
    """
    if self.verbosity < 2:
        return

    display_results = results[:max_display]
    hidden_count = len(results) - len(display_results)

    # ... table creation ...

    if hidden_count > 0:
        self.console.print(f"  ... and {hidden_count:,} more sessions")
```

### Priority 3: No Action Required

The following are non-issues that do not require changes:
- String formatting operations are efficient and appropriate
- Table creation overhead is negligible for post-simulation display
- Dictionary lookups for hand ranks are O(1) and minimal iterations
- Memory usage for formatter is minimal with `__slots__`

## Performance Impact Assessment

| Aspect | Impact | Notes |
|--------|--------|-------|
| Simulation throughput | None | Formatting code runs after simulation completes |
| Memory usage | Negligible | `__slots__` used, tables are temporary |
| Post-simulation latency | Low-Medium | Redundant aggregation adds overhead for large simulations |
| Core 100k hands/sec target | Not affected | This PR does not modify simulation code |

## Conclusion

This PR is **acceptable from a performance perspective** for the following reasons:

1. The formatting code executes after simulation completion, not during the hot path
2. Good practices are followed (`__slots__`, early returns, TYPE_CHECKING guard)
3. The redundant aggregation issue (H1) is the only notable concern, and its impact is limited to post-simulation display time, not the core simulation throughput target

The project's performance targets of 100,000 hands/second and <4GB RAM for 10M hands are **not threatened** by this PR since the output formatting is display-only code that runs after simulation completion.
