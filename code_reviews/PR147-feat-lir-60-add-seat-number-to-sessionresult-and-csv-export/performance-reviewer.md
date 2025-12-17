# Performance Review for PR #147

## Summary

This PR adds a `seat_number` field to `SessionResult` and updates CSV export to include it. The implementation is performance-conscious, using `__slots__` on dataclasses, frozen/immutable objects, and generator-compatible CSV exports. The `with_seat_number()` method creates new objects rather than mutating, which is appropriate for frozen dataclasses but adds allocation overhead in hot paths.

## Findings

### Critical

None

### High

None

### Medium

1. **Object allocation in hot path via `with_seat_number()`** (`/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py:239-261`, `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/controller.py:439-442`, `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/parallel.py:179-182`)

   The `with_seat_number()` method creates a new `SessionResult` object by copying all 11 fields plus setting the new seat number. This is called once per seat per table session (up to 6 seats per session). For large-scale simulations (10M hands with multi-seat tables), this creates significant allocation pressure.

   ```python
   # controller.py:439-442
   for seat_result in table_result.seat_results:
       result_with_seat = seat_result.session_result.with_seat_number(
           seat_result.seat_number
       )
       session_results.append(result_with_seat)
   ```

   **Impact**: For a 6-seat table with 1M sessions = 6M additional `SessionResult` allocations. Each `SessionResult` has 12 fields (including the new `seat_number`), so this is non-trivial memory churn.

   **Recommendation**: Consider having `_build_session_result_for_seat()` in `table_session.py:291-335` set `seat_number` directly when constructing the initial `SessionResult`, eliminating the need for the copy operation. The `SeatSessionResult` wrapper could then become unnecessary or simplified.

### Low

1. **Summary row iteration in `export_seat_aggregate_csv`** (`/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/export_csv.py:446-454`)

   The summary row calculation iterates over `analysis.seat_statistics` four times (once for each `sum()` call):

   ```python
   summary_row: dict[str, Any] = {
       "seat_number": "SUMMARY",
       "total_rounds": sum(s.total_rounds for s in analysis.seat_statistics),
       "wins": sum(s.wins for s in analysis.seat_statistics),
       "losses": sum(s.losses for s in analysis.seat_statistics),
       "pushes": sum(s.pushes for s in analysis.seat_statistics),
       # ...
       "total_profit": sum(s.total_profit for s in analysis.seat_statistics),
   }
   ```

   For tables with 1-6 seats, this is negligible (max 24 iterations), but could be consolidated into a single pass if this becomes a bottleneck.

2. **`SESSION_RESULT_FIELDS` list recreation** (`/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/export_csv.py:32-45`)

   The `SESSION_RESULT_FIELDS` list is defined at module level and used as a default in `export_sessions_csv()`. This is correct and efficient since it is a module-level constant.

### Positive

1. **Proper use of `__slots__`** (`/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py:146`, `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/export_csv.py:218`)

   Both `SessionResult` and `CSVExporter` use `slots=True`, reducing memory footprint per instance and improving attribute access speed.

2. **Frozen dataclass for `SessionResult`** (`/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py:183`)

   The frozen dataclass ensures immutability, preventing accidental mutations and enabling potential hash-based optimizations.

3. **Generator support in CSV export** (`/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/export_csv.py:168-206`)

   The `export_hands_csv()` function accepts `Iterable[HandRecord]`, enabling streaming exports for large datasets without loading all records into memory. This is critical for meeting the <4GB memory target for 10M hands.

4. **Efficient field validation** (`/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/export_csv.py:124-126`)

   Field validation uses set operations (`set(field_names) - set(SESSION_RESULT_FIELDS)`) which is O(n) rather than O(n*m) nested loops.

5. **Pre-allocated result list in parallel merge** (`/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/parallel.py:390-391`)

   The `_merge_results` method pre-allocates a list of the expected size, enabling O(1) direct assignment rather than O(n) appends.

6. **Single-pass session result collection** (`/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/controller.py:438-442`)

   Results are appended to a list in a single pass through `seat_results`, avoiding multiple iterations.

## Performance Impact Assessment

The changes are unlikely to impact the project's throughput target of >=100,000 hands/second. The `with_seat_number()` allocation occurs once per session result (not per hand), so even with multi-seat tables, the overhead is proportional to the number of sessions, not hands.

For the memory budget (<4GB for 10M hands), the additional `seat_number: int | None` field adds approximately 8 bytes per `SessionResult` on 64-bit systems. With 10M hands across sessions of ~50 hands each, this would be approximately 200K sessions * 8 bytes = ~1.6MB additional memory, which is negligible.
