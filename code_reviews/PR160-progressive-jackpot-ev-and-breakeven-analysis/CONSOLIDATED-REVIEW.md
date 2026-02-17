# Consolidated Review for PR #160

## Summary

This PR adds progressive jackpot EV and breakeven analysis capabilities including a new `progressive_analysis` module, `total_progressive_won` tracking through the session pipeline, and progressive breakdown in `AggregateStatistics`. The code is generally well-structured and follows project conventions, but has documentation inaccuracies (stale docstrings), a fragile manual field copy that should use `dataclasses.replace()`, and some missing test coverage for new fields in existing test methods.

## Issue Matrix

| # | Severity | Issue | File:Line | Reviewer(s) | In PR Scope? | Actionable? |
|---|----------|-------|-----------|-------------|--------------|-------------|
| 1 | High | `test_with_table_session_info` doesn't verify `total_progressive_won` is preserved through manual field copy | `tests/unit/simulation/test_session.py:389` | Test | Yes | Yes |
| 2 | High | `to_dict` tests don't assert new `total_progressive_won` key | `tests/unit/simulation/test_session.py:432` | Test | Yes | Yes |
| 3 | High | Stale `total_wagered` docstring says "main game only" but code includes bonus+progressive | `simulation/aggregation.py:46` | Docs, Quality | Yes | Yes |
| 4 | High | Missing `total_progressive_won` from `SessionResult` docstring Attributes section | `simulation/session.py:192-213` | Docs | Yes | Yes |
| 5 | Medium | `with_table_session_info` uses manual field-by-field reconstruction instead of `dataclasses.replace()` | `simulation/session.py:289-305` | Quality | Yes | Yes |
| 6 | Medium | Progressive EV calculation logic copy-pasted across `aggregate_results()`, `merge_aggregates()`, and `aggregate_with_seats()` | `simulation/aggregation.py` | Quality | Yes | Yes |
| 7 | Medium | String-based type discrimination (`payout.type == "fixed"`) with silent else for percentage type | `analytics/progressive_analysis.py:122,158` | Quality | Yes | Yes |
| 8 | Medium | `_SeatState.reset` test doesn't check `total_progressive_wagered`/`total_progressive_won` are cleared | `tests/unit/simulation/test_table_session.py:1716` | Test | Yes | Yes |
| 9 | Medium | No test for `calculate_house_edge` with `bet_amount=0` (guard clause uncovered) | `analytics/progressive_analysis.py:203` | Test | Yes | Yes |
| 10 | Medium | `contribution_rate` param accepted but never used in calculations -- misleading | `analytics/progressive_analysis.py` | Quality, Docs, Security | Yes | Yes |
| 11 | Medium | `HouseEdgeResult.house_edge` docstring says range "(0-1)" but also "Negative means player advantage" -- contradictory | `analytics/progressive_analysis.py:57` | Docs | Yes | Yes |
| 12 | Medium | New module not exported from `analytics/__init__.py` -- breaks discoverability pattern | `analytics/__init__.py` | Docs | Yes | Yes |
| 13 | Medium | Multi-pass aggregation worsened -- now 10-11 separate passes over results list | `simulation/aggregation.py` | Perf | No (pre-existing) | No |
| 14 | Low | No input validation on `bet_amount`/`jackpot_amount` for zero/negative values | `analytics/progressive_analysis.py` | Security, Quality, Test | Yes | Yes |
| 15 | Low | `_RANK_TO_PROB_KEY` mapping could silently drift from `THEORETICAL_HAND_PROBS` keys, returning 0.0 | `analytics/progressive_analysis.py` | Quality | Yes | Yes |
| 16 | Low | Test docstring says "$200K-$250K" but assertion checks `100_000 < x < 200_000` | `tests/unit/analytics/test_progressive_analysis.py:105` | Test, Docs | Yes | Yes |
| 17 | Low | `_hand_rank_probability` tests only cover 5 of 11 enum values | `tests/unit/analytics/test_progressive_analysis.py` | Test | Yes | Yes |
| 18 | Low | Breakeven scaling test only checks direction, not mathematical proportionality | `tests/unit/analytics/test_progressive_analysis.py:122` | Test | Yes | Yes |
| 19 | Low | `aggregate_results()` docstring doesn't mention new progressive breakdown | `simulation/aggregation.py` | Docs | Yes | Yes |
| 20 | Low | Negative breakeven jackpot possible when fixed payouts exceed bet amount | `analytics/progressive_analysis.py:168` | Security | Yes | Yes |
| 21 | Low | `_hand_rank_probability` does two dict lookups via intermediate string key | `analytics/progressive_analysis.py` | Perf | Yes | Yes |
| 22 | Low | `calculate_house_edge` redundantly calls `calculate_expected_payout` | `analytics/progressive_analysis.py` | Perf | Yes | Yes |

## Actionable Issues

**High Severity (4 issues)**
1. **#1**: Add assertion for `total_progressive_won` in `test_with_table_session_info` -- set a non-zero value and verify it survives the copy
2. **#2**: Add assertion for `total_progressive_won` key/value in `to_dict` test
3. **#3**: Fix `total_wagered` docstring to accurately reflect it includes main + bonus + progressive
4. **#4**: Add `total_progressive_won` to `SessionResult` docstring Attributes section

**Medium Severity (8 issues)**
5. **#5**: Replace manual field-by-field copy in `with_table_session_info` with `dataclasses.replace()`
6. **#6**: Extract progressive aggregation logic into a helper to DRY up the 3 aggregation functions
7. **#7**: Use explicit enum or raise on unknown payout type instead of silent else
8. **#8**: Add assertions for progressive fields in `_SeatState.reset` test
9. **#9**: Add test for `calculate_house_edge(bet_amount=0)` to cover the guard clause
10. **#10**: Either use `contribution_rate` in calculations or document clearly why it's metadata-only
11. **#11**: Fix `house_edge` docstring to use consistent range description (e.g., "typically positive; negative means player advantage")
12. **#12**: Export new `progressive_analysis` module from `analytics/__init__.py`

**Low Severity (9 issues)**
13-22: Input validation, test docstring mismatch, expanded parametrized tests, docstring updates, and minor performance improvements

## Deferred Issues

| # | Issue | Reason |
|---|-------|--------|
| 13 | Multi-pass aggregation (10-11 passes) | Pre-existing pattern; refactoring all aggregation functions is beyond PR scope |
