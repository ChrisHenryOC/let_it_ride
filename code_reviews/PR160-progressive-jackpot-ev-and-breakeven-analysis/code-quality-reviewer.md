# Code Quality Review -- PR #160

## Summary

This PR adds progressive jackpot EV and breakeven analysis as a standalone analytical module, threads `total_progressive_won` tracking through the session/table-session/aggregation pipeline, and updates CSV export. The code is well-structured, follows project conventions (frozen dataclasses with slots, module-level caching patterns), and has thorough test coverage. There are a few areas worth addressing around DRY violations in aggregation, string-based type discrimination, input validation gaps, and a method that should use `dataclasses.replace()`.

## Findings

### High Severity

None

### Medium Severity

**M1: `with_table_session_info` uses manual field-by-field construction instead of `dataclasses.replace()`**

The project memory explicitly states: "Use `dataclasses.replace()` to create modified copies -- never manual field-by-field reconstruction." The `with_table_session_info` method at `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py:289-305` manually reconstructs the entire `SessionResult` instead of using `replace()`. Every time a new field is added (like `total_progressive_won` in this PR), this method must be updated. This is fragile and violates the project's own convention.

Recommendation: Refactor to `return replace(self, table_session_id=table_session_id, seat_number=seat_number)`.

**M2: DRY violation -- progressive EV calculation repeated in three aggregation functions**

The exact same block of code computing `progressive_wagered`, `progressive_won`, `progressive_profit`, and `progressive_ev_per_hand` is repeated verbatim in `aggregate_results()`, `merge_aggregates()`, and `aggregate_with_seats()` in `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/aggregation.py`. The same pattern already existed for main/bonus but adding progressive makes it a growing maintenance burden. Similarly, the `total_wagered = main + bonus + progressive` and `main_won = total_won - bonus_won - progressive_won` formulas are duplicated three times.

Recommendation: Extract a helper function (e.g., `_compute_ev_per_hand(won, wagered, total_hands)`) to reduce duplication, or consider a `_FinancialBreakdown` dataclass that encapsulates the main/bonus/progressive split computation.

**M3: String-based type discrimination on `payout.type` instead of using enum or structural pattern**

In `/Users/chrishenry/source/let_it_ride/analytics/progressive_analysis.py:122` and `:158`, the code branches on `payout.type == "fixed"` using raw string comparison. The `ProgressivePayout.type` field is typed as `Literal["fixed", "jackpot_percentage"]`, which provides some safety, but the `else` branch in the analysis module silently assumes anything non-"fixed" is `jackpot_percentage`. If a third payout type were added, it would be silently treated as a percentage payout.

Recommendation: Use explicit matching for both types with an `else` clause that raises `ValueError` for unknown types:
```python
if payout.type == "fixed":
    ...
elif payout.type == "jackpot_percentage":
    ...
else:
    raise ValueError(f"Unknown payout type: {payout.type}")
```

### Low Severity

**L1: `contribution_rate` parameter accepted but unused in calculations**

Both `calculate_breakeven_jackpot()` and `calculate_house_edge()` in `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/progressive_analysis.py:133` and `:184` accept a `contribution_rate` parameter that is stored in the result but never used in the actual EV/breakeven/house-edge computation. This is misleading -- a caller might expect that changing `contribution_rate` affects the result, but it does not. The contribution rate is relevant to how fast a jackpot grows, but its inclusion as a function parameter suggests it factors into the EV calculation itself.

Recommendation: Either remove `contribution_rate` from the function signatures and result dataclasses (it is a simulation concern, not an EV calculation concern), or document explicitly that it is stored as metadata only and does not affect the computed values.

**L2: No input validation on `bet_amount` and `jackpot_amount`**

The functions `calculate_breakeven_jackpot()` and `calculate_house_edge()` in `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/progressive_analysis.py` do not validate that `bet_amount > 0` or `jackpot_amount >= 0`. A `bet_amount` of 0 would cause a division by zero in `calculate_house_edge()` (currently guarded by `if bet_amount > 0 else 0.0`, but returning 0.0 for player_return when bet is 0 silently hides a likely caller error). A negative `jackpot_amount` would produce nonsensical results.

Recommendation: Add explicit validation raising `ValueError` for `bet_amount <= 0` and `jackpot_amount < 0`.

**L3: `_RANK_TO_PROB_KEY` mapping could drift from `THEORETICAL_HAND_PROBS`**

The mapping in `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/progressive_analysis.py:72-81` manually maps `FiveCardHandRank` enum values to string keys in `THEORETICAL_HAND_PROBS`. If a key name changes in `validation.py`, this mapping silently returns 0.0 (via the `.get()` fallback) instead of failing, which would produce incorrect EV calculations.

Recommendation: Consider either using `FiveCardHandRank` as keys in `THEORETICAL_HAND_PROBS` directly (upstream change), or adding a module-level assertion/test that verifies all values in `_RANK_TO_PROB_KEY` exist in `THEORETICAL_HAND_PROBS`.

**L4: `AggregateStatistics` docstring for `total_wagered` is stale**

In `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/aggregation.py:46`, the docstring says `total_wagered: Total amount wagered (main game only).` This is now incorrect -- `total_wagered` includes main + bonus + progressive.

Recommendation: Update the docstring to reflect the actual semantics: "Total amount wagered across main game, bonus, and progressive bets."

### Informational

**I1: Good use of `TYPE_CHECKING` block for `ProgressivePaytable` import**

The `from __future__ import annotations` combined with `TYPE_CHECKING` guard in `progressive_analysis.py` correctly avoids a runtime import cycle while keeping type hints functional. This is noted in the scratchpad and follows the established pattern in `progressive_jackpot.py`.

**I2: Test coverage is thorough**

The test suite covers standard paytable calculations, edge cases (empty paytable, all-fixed paytable), error conditions (ValueError for no percentage payouts), dataclass immutability, and the full pipeline from session through aggregation. The breakeven verification test (`test_breakeven_payout_equals_bet`) that round-trips through `calculate_expected_payout` is a particularly good correctness check.

**I3: Consistent integration of progressive tracking across session, table_session, and aggregation**

The `total_progressive_won` field was added consistently to `SessionResult`, `_SeatState`, `Session`, `TableSession`, `to_dict()`, `with_table_session_info()`, `_build_session_result_for_seat()`, `export_csv.py SESSION_RESULT_FIELDS`, and all three aggregation functions. This shows good attention to the project's layered architecture.

**I4: Magic number `0.71` for default contribution rate**

The default `contribution_rate=0.71` appears in both `calculate_breakeven_jackpot()` and `calculate_house_edge()` as well as in `config/models.py`. Consider extracting this as a named constant (e.g., `DEFAULT_CONTRIBUTION_RATE = 0.71`) to make the domain meaning clear and avoid drift if the default changes.
