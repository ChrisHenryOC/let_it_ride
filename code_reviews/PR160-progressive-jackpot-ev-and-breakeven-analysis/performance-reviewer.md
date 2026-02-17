# Performance Review -- PR #160

## Summary

This PR adds progressive jackpot EV/breakeven analysis (a standalone analytical module), progressive win tracking in Session/TableSession, and progressive breakdown fields in AggregateStatistics. The changes are well-structured with minimal impact on the hot path. The new analytical module is not called during simulation so it poses no throughput risk. The aggregation changes add two more `sum()` passes over results in `aggregate_results()` which compounds a pre-existing multi-pass pattern, though this is unlikely to breach performance targets given aggregation is post-simulation.

## Findings

### High Severity

None

### Medium Severity

**M1: `aggregate_results()` iterates over results 10+ times (pre-existing, worsened by this PR)**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/aggregation.py`, lines 143-188

The `aggregate_results()` function performs separate `sum()` generator expressions for each metric: 3 for outcome counting (lines 143-145), `sum(r.hands_played ...)`, `sum(r.total_wagered ...)`, `sum(r.total_bonus_wagered ...)`, `sum(r.total_progressive_wagered ...)`, `sum(r.total_progressive_won ...)`, `sum(r.session_profit ...)`, and a tuple comprehension for `session_profits`. This PR added two more passes (`progressive_wagered` and `progressive_won`), bringing the total to roughly 10-11 passes over the results list.

While this is largely pre-existing, the project already has `aggregate_with_seats()` that demonstrates the single-pass pattern. For 10M hands across many sessions, multiple passes over large result lists can cause unnecessary memory pressure from generator overhead and CPU cache misses.

Recommendation: Refactor `aggregate_results()` to use the single-pass accumulator pattern already established by `aggregate_with_seats()`. Consider having `aggregate_results()` delegate to `aggregate_with_seats()` and discard the seat data, or extract a shared single-pass accumulator.

### Low Severity

**L1: `_hand_rank_probability()` performs two dict lookups per call with no caching**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/progressive_analysis.py`, lines 84-99

The function does a `_RANK_TO_PROB_KEY.get(rank)` lookup followed by a `THEORETICAL_HAND_PROBS.get(key, 0.0)` lookup. Since both dictionaries are module-level constants and the FiveCardHandRank enum is finite, the probabilities could be pre-computed into a single `dict[FiveCardHandRank, float]` at module level, eliminating the two-step lookup and the intermediate string key.

This function is called from `calculate_expected_payout()` and `calculate_breakeven_jackpot()` which iterate over paytable entries, so the impact is proportional to paytable size (typically 6-8 entries). This is analytical code, not on the simulation hot path, so the impact is negligible in practice.

Recommendation: Pre-compute a `_RANK_TO_PROB: dict[FiveCardHandRank, float]` module-level constant that maps directly from rank to probability, following the project convention for module-level caching of immutable data.

**L2: `calculate_house_edge()` calls `calculate_expected_payout()` which duplicates the paytable iteration**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/progressive_analysis.py`, lines 180-213

When `calculate_house_edge()` calls `calculate_expected_payout()`, it iterates over the paytable a second time if the caller also needs the expected payout separately. This is minor since the analytical functions are not in any hot path, but if they were ever called in a tight loop (e.g., plotting house edge across many jackpot values), the redundant iteration would add up.

Recommendation: No action required unless these functions are called in batch. If batch analysis is added later, consider an internal function that returns both components (fixed EV and percentage coefficient) to allow computing expected payout, breakeven, and house edge from a single paytable pass.

### Informational

**I1: Progressive tracking adds two float additions to the `play_hand()` hot path**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py`, lines 578-579

The additions `self._total_progressive_wagered += progressive_bet` and `self._total_progressive_won += progressive_payout` are inside the `if self._progressive_jackpot is not None and progressive_bet > 0:` guard. This means the cost is only incurred when progressive betting is active and a bet is placed. Two float additions are negligible -- well within the budget for the 100K hands/second target.

**I2: `Session.__slots__` is properly maintained**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py`, line 328

The new `_total_progressive_won` attribute is correctly added to `__slots__`, maintaining the memory optimization for the frequently-instantiated `Session` class. Good practice.

**I3: Dataclass design follows project conventions**

Files: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/progressive_analysis.py`, lines 28-66

Both `BreakevenResult` and `HouseEdgeResult` use `@dataclass(frozen=True, slots=True)` consistent with the project convention for result types. The field ordering (no defaults) is correct.

**I4: `_SeatState.__slots__` properly updated in `table_session.py`**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py`, line 164

The `total_progressive_won` field is added to `__slots__` and the `reset()` method, maintaining the lightweight accumulator pattern.
