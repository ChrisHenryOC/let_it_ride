## Summary

This PR integrates seat-level aggregate CSV export into the output pipeline by adding a new `analyze_session_results_by_seat()` function and updating `CSVExporter.export_all()`. The implementation is memory-efficient for the expected data sizes (up to 6 seats), but the redundant iteration over `results.session_results` in `export_all()` introduces unnecessary overhead that could impact throughput for large simulations.

## Findings

### Critical

None identified.

### High

**H1: Redundant full iteration of session_results in export_all()**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/export_csv.py`
Lines: 361-381

The `export_all()` method iterates over `results.session_results` multiple times:
1. Line 361: `export_sessions()` iterates all results to write CSV
2. Line 365: `aggregate_results()` iterates all results for statistics
3. Line 380: `analyze_session_results_by_seat()` iterates all results again

For a 10M hand simulation with 100 hands/session, this processes ~100K SessionResult objects three times. With the project target of 100,000 hands/second, the export phase could become a bottleneck.

```python
# Current: Three separate iterations
sessions_path = self.export_sessions(results.session_results)  # Iteration 1
stats = aggregate_results(results.session_results)              # Iteration 2
analysis = analyze_session_results_by_seat(results.session_results)  # Iteration 3
```

Consider consolidating aggregation into a single pass or computing seat aggregation alongside the existing `aggregate_results()` call.

### Medium

**M1: Function-level import inside frequently-called method**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/export_csv.py`
Lines: 352-355

```python
def export_all(self, ...):
    from let_it_ride.analytics.chair_position import (
        analyze_session_results_by_seat,
    )
    from let_it_ride.simulation.aggregation import aggregate_results
```

While Python caches module imports, placing imports inside `export_all()` adds lookup overhead on every call. For CLI single-run usage this is negligible, but if `export_all()` were called in a loop or batch processing scenario, this becomes measurable. Move imports to module level or at least outside the method body.

**M2: Multiple tuple iterations for summary row computation**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/export_csv.py`
Lines: 477-485

```python
summary_row: dict[str, Any] = {
    "seat_number": SUMMARY_ROW_LABEL,
    "total_rounds": sum(s.total_rounds for s in analysis.seat_statistics),
    "wins": sum(s.wins for s in analysis.seat_statistics),
    "losses": sum(s.losses for s in analysis.seat_statistics),
    "pushes": sum(s.pushes for s in analysis.seat_statistics),
    ...
    "total_profit": sum(s.total_profit for s in analysis.seat_statistics),
}
```

This creates 5 separate iterations over `seat_statistics` (max 6 seats). While the tuple size is small (6 seats max), a single-pass accumulation would be more efficient:

```python
total_rounds = wins = losses = pushes = 0
total_profit = 0.0
for s in analysis.seat_statistics:
    total_rounds += s.total_rounds
    wins += s.wins
    losses += s.losses
    pushes += s.pushes
    total_profit += s.total_profit
```

### Low

**L1: Dictionary allocation on every iteration in _aggregate_session_results_by_seat**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/chair_position.py`
Lines: 283-304

```python
for result in results:
    if result.seat_number is None:
        continue
    seat_num = result.seat_number
    agg = aggregations.get(seat_num)
    if agg is None:
        agg = _SeatAggregation()
        aggregations[seat_num] = agg
```

The pattern is correct, but using `setdefault()` would reduce attribute lookups:

```python
for result in results:
    if result.seat_number is None:
        continue
    agg = aggregations.setdefault(result.seat_number, _SeatAggregation())
```

This is a micro-optimization but aligns with Python performance best practices.

**L2: Eager list creation for sorted seat statistics**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/chair_position.py`
Lines: 339-346

```python
seat_stats: list[SeatStatistics] = []
for seat_num in sorted(aggregations.keys()):
    stats_for_seat = _calculate_seat_statistics(...)
    seat_stats.append(stats_for_seat)
```

With a maximum of 6 seats, this is acceptable. However, for consistency with the existing `analyze_chair_positions()` function (which uses the same pattern), this could use a list comprehension:

```python
seat_stats = [
    _calculate_seat_statistics(seat_num, aggregations[seat_num], confidence_level)
    for seat_num in sorted(aggregations.keys())
]
```

**L3: SessionResult.with_seat_number creates a new object**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py`
Lines: 258-271

The `with_seat_number()` method creates a full copy of `SessionResult` just to add the seat number. This is called for every session in multi-seat simulations. While `SessionResult` uses `slots=True` for memory efficiency, the allocation still occurs. This is acceptable for the current design but worth noting if profiling shows hot spots.

## Performance Impact Assessment

Given the project targets (100,000 hands/second, <4GB for 10M hands):

- **Memory**: No significant impact. Seat aggregation uses O(seats) additional memory, where seats <= 6.
- **Throughput**: The redundant iteration (H1) adds ~10-20% overhead to the export phase for large simulations. Since export happens once at the end, this does not affect the core simulation throughput target.
- **Recommendation**: Address H1 if profiling shows export as a bottleneck for large simulations (>1M sessions).
