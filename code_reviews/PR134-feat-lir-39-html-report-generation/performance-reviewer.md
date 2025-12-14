# Performance Review: PR #134 - LIR-39 HTML Report Generation

## Summary

This PR introduces HTML report generation with embedded Plotly visualizations. The implementation is well-structured with `__slots__` usage on dataclasses and follows existing project patterns. However, there are several performance concerns: redundant aggregation computation in the render path, potential memory issues with raw session data for large simulations, and O(n) iterations over session results during chart generation that could be optimized.

## Findings

### High Severity

#### H1: Redundant Aggregation Computation in `HTMLReportGenerator.render()`

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/export_html.py:847-849`

```python
def render(
    self,
    results: SimulationResults,
    stats: DetailedStatistics,
) -> str:
    from let_it_ride.simulation.aggregation import aggregate_results
    aggregate_stats = aggregate_results(results.session_results)
```

The `aggregate_results()` function is called every time `render()` is invoked, even though the caller may already have computed aggregate statistics. Looking at `aggregate_results()` in `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/aggregation.py:113-205`, it performs O(n) iterations multiple times over the session results (for outcome counting, summing wagered amounts, calculating statistics via `mean`, `median`, `stdev`, etc.).

For 10 million hands across 100,000 sessions, this redundant computation is wasteful. Consider:
1. Accepting `AggregateStatistics` as an optional parameter
2. Computing it only if not provided
3. Caching the result if the class is reused

---

### Medium Severity

#### M1: Memory Overhead with `include_raw_data=True` for Large Simulations

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/export_html.py:869-880`

```python
if self._config.include_raw_data:
    context.raw_sessions = [
        {
            "outcome": r.outcome.value,
            "hands_played": r.hands_played,
            "starting_bankroll": _format_currency(r.starting_bankroll),
            "final_bankroll": _format_currency(r.final_bankroll),
            "session_profit": _format_currency(r.session_profit),
            "max_drawdown": _format_currency(r.max_drawdown),
        }
        for r in results.session_results
    ]
```

With the project target of handling 10 million hands (potentially 100,000+ sessions), building a list of dictionaries with formatted strings creates significant memory pressure. Each dictionary contains 6 formatted strings, and Python dicts have substantial overhead.

For 100,000 sessions:
- ~100,000 dicts x ~500 bytes per dict = ~50MB just for this structure
- Plus the HTML template expansion with all session rows

Consider:
1. Paginating raw data output
2. Using generators or streaming for large datasets
3. Warning users about memory impact when `include_raw_data=True` with large session counts

---

#### M2: Multiple O(n) Passes in Chart Generation Functions

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/export_html.py:417-435`

```python
def _create_histogram_chart(
    session_results: list[SessionResult],
    bins: int | str = "auto",
) -> go.Figure:
    profits = [r.session_profit for r in session_results]
    # ...
    mean_profit = sum(profits) / len(profits)
```

This creates a full copy of all session profits as a list, then iterates again to compute the mean. With 100,000+ sessions, this creates memory pressure.

Similarly in `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/export_html.py:466-540`:

```python
def _create_trajectory_chart(
    session_results: list[SessionResult],
    sample_size: int = 10,
) -> go.Figure:
    # ...
    if len(session_results) <= sample_size:
        sampled = session_results
    else:
        step = len(session_results) // sample_size
        sampled = [session_results[i * step] for i in range(sample_size)]
```

The sampling approach is good, but for very large session lists, even `len(session_results)` is O(n) for some iterables (though list is O(1)).

---

#### M3: Plotly Chart Generation Overhead

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/export_html.py:779-831`

```python
def _generate_charts(
    self,
    results: SimulationResults,
    aggregate_stats: AggregateStatistics,
) -> _ChartData:
    # ...
    histogram_fig = _create_histogram_chart(
        results.session_results,
        bins=self._config.histogram_bins,
    )
    charts.histogram_html = histogram_fig.to_html(...)
```

Each `go.Figure.to_html()` call with `include_plotlyjs=True` embeds the entire Plotly.js library (~3MB minified). While only the first chart includes it, the chart generation and HTML serialization are synchronous and can be slow for large datasets.

Consider:
1. Documenting that report generation is not on the hot path
2. Adding progress callbacks for long-running generation
3. Using async generation if the report is called from a web context

---

### Low Severity

#### L1: Jinja2 Environment Created Per Instance

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/export_html.py:769-772`

```python
def __init__(self, config: HTMLReportConfig | None = None) -> None:
    self._config = config or HTMLReportConfig()
    self._env = Environment(
        loader=PackageLoader("let_it_ride.analytics", "templates"),
        autoescape=select_autoescape(["html", "xml"]),
    )
```

A new `Environment` instance is created for each `HTMLReportGenerator`. For single-use generation this is fine, but if the generator is instantiated repeatedly in a loop, the template compilation overhead accumulates.

Consider making the environment a class-level constant or using module-level lazy initialization.

---

#### L2: String Concatenation in Formatting Functions

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/export_html.py:651-655`

```python
"session_win_rate_ci": (
    f"{_format_percentage(stats.session_win_rate_ci.lower)} - "
    f"{_format_percentage(stats.session_win_rate_ci.upper)}"
),
```

While f-strings are efficient, the pattern of calling formatting functions and then concatenating appears throughout the `_detailed_stats_to_dict` and `_aggregate_stats_to_dict` functions. For single report generation this is negligible, but the pattern creates intermediate strings.

---

#### L3: Late Import Inside Method

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/export_html.py:847-848`

```python
def render(self, results: SimulationResults, stats: DetailedStatistics) -> str:
    from let_it_ride.simulation.aggregation import aggregate_results
```

Importing inside the method adds a small overhead on each call. While Python caches imports, the lookup still happens. For a method that may only be called once per report, this is acceptable, but moving it to module level is cleaner.

---

## Performance Impact Assessment

### Project Targets Evaluation

| Target | Status | Notes |
|--------|--------|-------|
| 100,000 hands/second | Not Affected | HTML generation is post-simulation, not on hot path |
| <4GB RAM for 10M hands | Potential Risk | `include_raw_data=True` with large session counts could exceed budget |

### Recommendations

1. **Accept pre-computed aggregates** - Modify `render()` to accept optional `AggregateStatistics` parameter
2. **Add session count warning** - Warn when `include_raw_data=True` and session count exceeds threshold (e.g., 10,000)
3. **Document performance characteristics** - Note that HTML generation is O(n) where n is session count
4. **Consider lazy chart generation** - Only generate charts if `include_charts=True` (already implemented)

The implementation is solid for typical use cases (hundreds to thousands of sessions). The concerns become relevant only for very large simulations where memory efficiency is critical.
