# Test Coverage Review -- PR #160

## Summary

PR #160 adds progressive jackpot EV/breakeven analysis (`progressive_analysis.py`) with 25 new tests, plus progressive tracking fields (`total_progressive_won`) threaded through session, table session, aggregation, and export. Test coverage is generally solid with good use of exact mathematical assertions and error path testing, but there are notable gaps around boundary/edge conditions in the analysis functions, missing coverage for `_SeatState.reset` clearing the new progressive fields, and the existing `with_table_session_info` and `to_dict` tests not verifying the new `total_progressive_won` field is preserved.

## Findings

### High Severity

**H1: `with_table_session_info` test does not verify `total_progressive_won` is preserved**

The existing test at `/Users/chrishenry/source/let_it_ride/tests/unit/simulation/test_session.py:389` (`test_with_table_session_info`) constructs a `SessionResult` without `total_progressive_won` (defaults to 0.0) and does not assert that the new field is carried through. Since `with_table_session_info` manually reconstructs the dataclass field-by-field (not using `dataclasses.replace`), any missing field in that method would silently default to 0.0 and pass this test. The production code at `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py:299` does include the field, but this is a fragile pattern -- future field additions could be missed without test coverage.

Recommendation: Update the existing `test_with_table_session_info` test to set `total_progressive_won` to a non-zero value and assert it is preserved in the copy. Also set `total_progressive_wagered` to a non-zero value (currently also unchecked).

---

**H2: `to_dict` tests do not verify `total_progressive_won` key**

The tests at `/Users/chrishenry/source/let_it_ride/tests/unit/simulation/test_session.py:432` and `:455` do not assert that `total_progressive_won` appears in the dict output. The `to_dict` method at `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py:249` was updated to include the field, but no test verifies its presence or value.

Recommendation: Add assertions for `d["total_progressive_won"]` in both `test_to_dict_includes_table_session_id` and `test_to_dict_table_session_id_none`.

### Medium Severity

**M1: `_SeatState.reset` not tested for new `total_progressive_won` field**

The `_SeatState.reset()` method at `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py:208` now clears `total_progressive_won`. The existing test at `/Users/chrishenry/source/let_it_ride/tests/unit/simulation/test_table_session.py:1716` (`test_reset_clears_wagering_totals`) only checks `total_wagered` and `total_bonus_wagered` -- it does not verify that `total_progressive_wagered` or `total_progressive_won` are reset.

Recommendation: Extend `test_reset_clears_wagering_totals` to set and verify `total_progressive_wagered` and `total_progressive_won` are zeroed after reset.

---

**M2: No test for `calculate_house_edge` with `bet_amount=0`**

The function at `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/progressive_analysis.py:203` has a guard `if bet_amount > 0 else 0.0` for the division, but no test exercises this path. A `bet_amount=0` would produce `player_return=0.0` and `house_edge=1.0`, which is a valid but potentially surprising result that deserves explicit test coverage.

Recommendation: Add a test for `calculate_house_edge` with `bet_amount=0.0` verifying `player_return == 0.0` and `house_edge == 1.0`.

---

**M3: No test for negative `jackpot_amount` in analysis functions**

The functions `calculate_expected_payout` and `calculate_house_edge` accept any float for `jackpot_amount` with no validation. Negative jackpot amounts would produce nonsensical negative EV values. There are no tests covering this boundary.

Recommendation: Either add input validation (raising `ValueError` for negative jackpot) or add a test documenting the current behavior with negative inputs.

---

**M4: Breakeven scaling test is weak -- only asserts direction, not proportionality**

The test at `/Users/chrishenry/source/let_it_ride/tests/unit/analytics/test_progressive_analysis.py:122` (`test_breakeven_with_different_bet_amount`) asserts `result_5.breakeven_jackpot > result_1.breakeven_jackpot`. Given the formula `J = (bet - fixed_ev) / coeff`, the breakeven should scale linearly: `result_5 / result_1` should approximate `5.0` (not exactly, since `fixed_ev` is constant). The test only checks direction, missing an opportunity to verify mathematical correctness.

Recommendation: Assert `result_5.breakeven_jackpot == pytest.approx(result_1.breakeven_jackpot * 5 - result_1.fixed_ev * 4 / result_1.percentage_ev_coefficient)` or at least verify `result_5.breakeven_jackpot / result_1.breakeven_jackpot` is close to 5.

---

**M5: `test_standard_paytable_breakeven_range` docstring/assertion mismatch**

At `/Users/chrishenry/source/let_it_ride/tests/unit/analytics/test_progressive_analysis.py:105`, the docstring says "should be in ~$200K-$250K range" but the assertion checks `100_000 < result.breakeven_jackpot < 200_000`. The scratchpad says "~$134K". The wide range makes this test pass but reduces its ability to detect regressions in probability constants or paytable definitions.

Recommendation: Tighten the assertion range and fix the docstring to match. Based on the scratchpad value of ~$134K, something like `assert 130_000 < result.breakeven_jackpot < 140_000` would be more useful for regression detection.

### Low Severity

**L1: `contribution_rate` parameter is stored but never used in calculations**

In `calculate_breakeven_jackpot` and `calculate_house_edge`, the `contribution_rate` parameter is accepted and stored in the result dataclass but never used in any computation. No test verifies that different contribution rates produce different breakeven/edge results (because they would not). This is potentially misleading -- a user might expect contribution rate to factor into the EV calculation.

Recommendation: Either incorporate `contribution_rate` into the analysis (e.g., effective EV = payout - bet + contribution_rate * bet returned to pool) or document clearly in tests that it is metadata-only.

---

**L2: No test for `calculate_expected_payout` with negative `jackpot_amount`**

At `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/progressive_analysis.py:126`, a negative `jackpot_amount` would produce negative contributions from percentage payouts, potentially yielding a negative expected payout. No test documents this edge case.

Recommendation: Add a test or input validation.

---

**L3: `_hand_rank_probability` tests only cover 5 of 11 enum values**

Tests cover `ROYAL_FLUSH`, `STRAIGHT_FLUSH`, `HIGH_CARD`, `PAIR_BELOW_TENS`, and `PAIR_TENS_OR_BETTER`. The remaining mapped ranks (`FOUR_OF_A_KIND`, `FULL_HOUSE`, `FLUSH`, `STRAIGHT`, `THREE_OF_A_KIND`, `TWO_PAIR`) are not individually tested for correct probability values. A typo in `_RANK_TO_PROB_KEY` or `THEORETICAL_HAND_PROBS` would go undetected.

Recommendation: Add parametrized tests covering all 8 mapped ranks with their exact theoretical probabilities.

### Informational

**I1: Test class organization follows good patterns**

The test file at `/Users/chrishenry/source/let_it_ride/tests/unit/analytics/test_progressive_analysis.py` is well-organized into logical test classes (`TestHandRankProbability`, `TestCalculateExpectedPayout`, `TestCalculateBreakevenJackpot`, `TestCalculateHouseEdge`, `TestDataclassProperties`). Test names are descriptive and follow the project naming convention.

---

**I2: Good use of cross-validation between functions**

The test `test_breakeven_payout_equals_bet` at line 114 cross-validates `calculate_breakeven_jackpot` against `calculate_expected_payout`, and `test_zero_house_edge_at_breakeven` at line 208 cross-validates `calculate_house_edge` against the breakeven result. This is excellent practice for mathematical functions.

---

**I3: No property-based testing for mathematical functions**

The analysis functions are purely mathematical with well-defined algebraic properties (linearity of expected payout in jackpot amount, monotonicity of house edge). These would be good candidates for hypothesis-based property testing -- e.g., `expected_payout(paytable, j1) < expected_payout(paytable, j2)` for any `j1 < j2` with percentage payouts.

---

**I4: `aggregate_with_hand_frequencies` not tested with progressive fields**

The function `aggregate_with_hand_frequencies` at `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/aggregation.py:322` delegates to `aggregate_results` and then uses `replace`. Since progressive fields flow through `aggregate_results`, this should work correctly, but there is no explicit test confirming progressive fields survive the `replace` call.
