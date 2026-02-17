# LIR-64: Progressive Jackpot EV and Breakeven Analysis

## Summary
Added analytical layer for progressive jackpot: standalone breakeven calculator, house edge computation, progressive statistics tracking through session/table/aggregation pipeline, and export integration.

## Key Decisions
- Breakeven jackpot for standard paytable: ~$134K (for $1 bet)
- Progressive wagered/won now included in `total_wagered`/`total_won` in AggregateStatistics
- `main_won` calculation adjusted to subtract `progressive_won` (previously only subtracted `bonus_won`)
- `ProgressivePaytable` import uses `TYPE_CHECKING` block since `from __future__ import annotations` makes type hints strings

## Files Changed
- `src/let_it_ride/analytics/progressive_analysis.py` — NEW: BreakevenResult, HouseEdgeResult, calculation functions
- `src/let_it_ride/simulation/session.py` — Added `total_progressive_won` field + tracking
- `src/let_it_ride/simulation/table_session.py` — Added `total_progressive_won` to _SeatState
- `src/let_it_ride/simulation/aggregation.py` — Added progressive breakdown fields
- `src/let_it_ride/analytics/export_csv.py` — Updated SESSION_RESULT_FIELDS
- `tests/unit/analytics/test_progressive_analysis.py` — NEW: 25 tests
- `tests/unit/simulation/test_session.py` — Added progressive_won tracking tests
- `tests/unit/simulation/test_aggregation.py` — Added progressive aggregation tests
- `tests/unit/simulation/test_table_session.py` — Added progressive_won table test
- `tests/unit/cli/test_formatters.py` — Updated AggregateStatistics construction
- `tests/unit/analytics/test_statistics.py` — Updated AggregateStatistics construction
- `tests/unit/analytics/test_validation.py` — Updated AggregateStatistics construction

## Verification
- 2116 unit tests pass
- mypy: no issues
- ruff: all checks passed
