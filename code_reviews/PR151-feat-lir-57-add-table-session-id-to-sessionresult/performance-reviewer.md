# Performance Review: PR #151 - Add table_session_id to SessionResult

## Summary

This PR adds a `table_session_id` field to `SessionResult` to enable grouping seats that shared community cards in multi-seat simulations. The implementation follows good performance practices: `SessionResult` uses `frozen=True, slots=True`, the new field has minimal memory overhead (single `int | None`), and the `with_table_session_info()` method creates a necessary copy for immutable dataclasses. No critical performance issues identified; this change should not impact the 100,000 hands/second target.

## Findings by Severity

### Critical

None identified.

### High

None identified.

### Medium

**M1: Object Copy in Hot Path (Acceptable but Worth Monitoring)**

- **File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py:266-280`
- **File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/parallel.py:250-255`

The `with_table_session_info()` method creates a full copy of `SessionResult` for every seat in every table session:

```python
def with_table_session_info(
    self, table_session_id: int, seat_number: int
) -> "SessionResult":
    return SessionResult(
        outcome=self.outcome,
        stop_reason=self.stop_reason,
        hands_played=self.hands_played,
        starting_bankroll=self.starting_bankroll,
        final_bankroll=self.final_bankroll,
        session_profit=self.session_profit,
        total_wagered=self.total_wagered,
        total_bonus_wagered=self.total_bonus_wagered,
        peak_bankroll=self.peak_bankroll,
        max_drawdown=self.max_drawdown,
        max_drawdown_pct=self.max_drawdown_pct,
        table_session_id=table_session_id,
        seat_number=seat_number,
    )
```

**Impact Analysis:**
- This occurs once per seat per session (e.g., 6 seats x 1M sessions = 6M copies)
- Each copy involves 13 field assignments
- However, `SessionResult` uses `__slots__` via `slots=True`, minimizing memory overhead
- The copy operation is O(1) with fixed 13 fields
- This happens at session-end, not per-hand, so it is NOT in the critical hot path

**Mitigation:** This is acceptable for the current architecture. The frozen dataclass pattern requires copies for immutability. The alternative (mutable dataclass) would introduce thread-safety concerns in parallel execution. Monitor if this becomes a bottleneck at scale.

### Low

**L1: Dictionary Creation in to_dict() Method**

- **File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py:219-241`

The `to_dict()` method creates a new dictionary with 13 fields on each call:

```python
def to_dict(self) -> dict[str, Any]:
    return {
        "table_session_id": self.table_session_id,
        "seat_number": self.seat_number,
        "outcome": self.outcome.value,
        # ... 10 more fields
    }
```

**Impact:** Only called during export (once per session result), not in the simulation hot path. Memory is transient and immediately used for serialization. No action needed.

**L2: Tuple Conversion in Parallel Execution**

- **File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/parallel.py:181`

```python
return list(table_result.seat_results)
```

The change from list comprehension to `list()` on a tuple is a micro-optimization that is essentially equivalent in performance. No concern.

## Positive Observations

1. **Proper Use of `slots=True`**: `SessionResult` at line 183 correctly uses `@dataclass(frozen=True, slots=True)`, ensuring minimal memory footprint per instance.

2. **Field Order Optimization**: The new `table_session_id` field is placed with default value at the end of the dataclass, avoiding positional argument issues.

3. **No Hot Path Changes**: The simulation core (hand evaluation, deck operations, strategy decisions) is unaffected. The new code only runs once per session completion.

4. **Efficient ID Scheme**: The composite ID calculation in parallel.py (`session_id * num_seats + seat_idx`) uses simple integer arithmetic, avoiding any string concatenation or hashing overhead.

## Performance Target Assessment

| Target | Status | Notes |
|--------|--------|-------|
| >= 100,000 hands/second | PASS | No hot path modifications |
| < 4GB RAM for 10M hands | PASS | Single `int | None` field adds ~8-16 bytes per result |

## Memory Impact Estimate

For 10M sessions with 6 seats (60M SessionResult objects):
- Additional memory per object: 8 bytes (int) or 0 bytes (None case - shared singleton)
- Worst case additional memory: ~480 MB (if all table_session_id are unique ints)
- This remains well within the 4GB budget

## Recommendations

1. **No immediate action required** - The implementation is performance-appropriate.

2. **Future consideration:** If `with_table_session_info()` becomes a bottleneck at extreme scale, consider:
   - Having `SeatSessionResult` directly include `table_session_id` at creation time in `TableSession._build_session_result_for_seat()`
   - This would eliminate the copy operation by embedding the ID during initial construction

3. **Test validation:** Ensure existing performance benchmarks still pass after this change.
