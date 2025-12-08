# Issue #25: LIR-22 Simulation Results Aggregation

**GitHub Issue:** https://github.com/ChrisHenryOC/let_it_ride/issues/25
**PR:** https://github.com/ChrisHenryOC/let_it_ride/pull/111
**Status:** Completed

## Implementation Summary

Created `src/let_it_ride/simulation/aggregation.py` with:

1. **AggregateStatistics dataclass** - Frozen, slotted dataclass with:
   - Session metrics: total_sessions, winning/losing/push counts, win_rate
   - Hand metrics: total_hands
   - Financial metrics: total_wagered, total_won, net_result, expected_value_per_hand
   - Main/bonus breakdown: wagered, won, EV per hand (bonus assumes break-even)
   - Hand distribution: frequencies dict and percentages
   - Session profit stats: mean, std, median, min, max
   - session_profits tuple preserved for merge support

2. **aggregate_results(results: list[SessionResult])** - Aggregates multiple session results
   - Raises ValueError for empty list
   - Note: Main/bonus breakdown assumes bonus is break-even since SessionResult doesn't track payouts separately

3. **merge_aggregates(agg1, agg2)** - Combines two aggregates for parallel execution support
   - Sums counts and financial totals
   - Recalculates rates and percentages
   - Merges hand frequencies
   - Recomputes profit statistics from combined session_profits

4. **aggregate_with_hand_frequencies(results, hand_frequencies)** - Includes hand distribution data from HandRecords

## Tests Created

`tests/unit/simulation/test_aggregation.py` - 25 tests covering:
- Empty results error
- Single session (win/loss/push)
- Multiple sessions with mixed outcomes
- Win rate calculation
- Expected value per hand
- Total wagered calculation
- Session profit statistics
- Merge operations
- Hand frequencies
- Known dataset verification
- Parallel merge equivalence

## Key Decisions

1. **Bonus tracking limitation**: SessionResult doesn't track main vs bonus payouts separately. The implementation assumes bonus is break-even (bonus_won = bonus_wagered) and attributes all profit/loss to the main game. This is documented in the function docstring.

2. **session_profits tuple**: Preserved in the dataclass to enable accurate statistics recalculation after merge operations.

3. **Immutability**: Uses `@dataclass(frozen=True, slots=True)` consistent with project patterns.
