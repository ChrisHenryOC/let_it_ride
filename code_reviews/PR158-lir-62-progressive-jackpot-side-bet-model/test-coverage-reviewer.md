# Test Coverage Review for PR #158

## Summary

The PR adds 27 unit tests for the core `ProgressiveJackpot` class and 16 unit tests for the `ProgressiveSideBetConfig` Pydantic model. These tests are well-structured, follow the project's arrange-act-assert convention, and cover the main happy paths for contributions, fixed payouts, percentage payouts, non-qualifying hands, reset mechanics, and the factory function. However, there are critical integration-level gaps: the `Session.play_hand()` progressive code path (30 lines of bankroll/net_result logic) and the `TableSession.play_round()` progressive code path (50+ lines including shared-jackpot multi-seat iteration) have zero test coverage. The `total_progressive_wagered` field is never asserted in any test despite being wired into 5 locations across the codebase. Several boundary conditions and error paths are also untested.

## Findings

### Critical

**1. No integration tests for `Session.play_hand()` with progressive enabled**
- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py:513-544`
- The `play_hand()` method has a 30-line block that: (a) calls `contribute()`, (b) calls `evaluate_payout()`, (c) computes `progressive_net = progressive_payout - progressive_bet`, (d) reconstructs the `GameHandResult` with adjusted `net_result`, and (e) accumulates `_total_progressive_wagered`. None of this logic is exercised by any test. A grep for "progressive" in `/Users/chrishenry/source/let_it_ride/tests/unit/simulation/test_session.py` returns zero matches. This is the code path where progressive actually affects bankroll and session outcomes -- bugs here (e.g., sign error in `progressive_net`, double-counting the bet cost, or incorrect `net_result` adjustment) would be invisible.
- Recommendation: Add tests that create a `Session` with a `ProgressiveJackpot` instance and verify: (a) bankroll decreases by the progressive bet cost when no payout occurs, (b) bankroll reflects correct net when a payout occurs (e.g., mock a hand with a flush rank to trigger the $75 fixed payout), (c) `result.progressive_bet` and `result.progressive_payout` fields are populated on the returned `GameHandResult`, and (d) `result.net_result` includes the progressive net.

**2. No integration tests for `TableSession.play_round()` with progressive enabled**
- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py:510-581`
- The `play_round()` method has a complex progressive loop: for each seat, it calls `contribute()` and `evaluate_payout()` on a shared `ProgressiveJackpot` instance, creates enhanced `PlayerSeat` objects, and adjusts bankroll with `adjusted_net`. The existing `TestProgressiveBettingIntegration` class at line 1190 of the test file tests Martingale betting progression, not the progressive jackpot. A grep for "progressive_jackpot" in the table session test file returns zero matches.
- The shared-jackpot design means seat evaluation order matters: seat 1's contribution inflates the pool before seat 2's payout is evaluated. If seat 1 hits a royal flush and resets the pool, seat 2 evaluating next would get payouts against the reset pool. This ordering dependency is a prime candidate for testing but is completely uncovered.
- Recommendation: Add tests with a 2+ seat `TableSession` that: (a) verify each seat's contribution reaches the shared pool, (b) verify ordering effects when one seat hits a jackpot (pool resets before next seat evaluates), (c) verify per-seat `total_progressive_wagered` tracking.

**3. `total_progressive_wagered` is never asserted in any test**
- The field `total_progressive_wagered` is added to `SessionResult` (`/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py:219`), `SessionResult.to_dict()` (line 242), `SessionResult.with_table_session_info()` (line 292), CSV export headers (`/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/export_csv.py:43`), `_SeatState` (`/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py:139,159`), and `_build_session_result_for_seat()` (line 343). A grep for `total_progressive_wagered` across the entire `/Users/chrishenry/source/let_it_ride/tests/` directory returns zero matches.
- Recommendation: Assert `total_progressive_wagered` in at least: (a) a `Session.run_to_completion()` test with progressive enabled, (b) a `SessionResult.to_dict()` test to verify serialization, (c) a `SessionResult.with_table_session_info()` test to verify propagation, and (d) a CSV export test to verify the column is populated.

### High

**4. No tests for `get_progressive_jackpot()` and `get_progressive_bet()` utility functions**
- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/utils.py:103-128`
- These factory functions are the integration point between configuration and session creation. `get_progressive_jackpot()` returns `None` when disabled and a `ProgressiveJackpot` when enabled. `get_progressive_bet()` returns `0.0` when disabled and `config.progressive.bet_amount` when enabled. Both are called from `controller.py` and `parallel.py`. A grep for "progressive" in `/Users/chrishenry/source/let_it_ride/tests/unit/simulation/test_factories.py` shows only a single line setting a mock attribute, not testing the actual utility functions.
- Recommendation: Add tests covering: (a) `get_progressive_jackpot()` returns `None` when `enabled=False`, (b) returns a configured `ProgressiveJackpot` instance when `enabled=True`, (c) `get_progressive_bet()` returns `0.0` when disabled, (d) returns the configured bet amount when enabled.

**5. `validate_session_config` does not include `progressive_bet` in minimum bankroll check -- no test exposes this**
- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py:82`
- The validation function computes `min_bet_required = (base_bet * 3) + bonus_bet` but does not add `progressive_bet`. However, `_minimum_bet_required()` at line 402 does include it: `(base_bet * 3) + bonus_bet + progressive_bet`. This means a session could pass config validation with a bankroll of exactly `base_bet * 3 + bonus_bet` but then immediately stop on insufficient funds because the runtime check also requires `progressive_bet`. No test exercises this inconsistency.
- Recommendation: Add a test that creates a `SessionConfig` with `starting_bankroll` exactly equal to `base_bet * 3 + bonus_bet` (no room for `progressive_bet`), and verify that the session's `should_stop()` returns `True` immediately while config validation passes -- or fix `validate_session_config` to include `progressive_bet` and add a test for the rejection.

**6. No test for `create_progressive_jackpot` with invalid hand rank name**
- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/progressive_jackpot.py:190`
- The line `hand_rank = FiveCardHandRank[hand_name.upper()]` will raise a raw `KeyError` if a user provides an invalid hand rank string like `"ROYAL_FLUSHH"` in the custom paytable config. There is no test verifying this error path, and the code does not wrap it with a descriptive `ValueError`.
- Recommendation: Add a test that calls `create_progressive_jackpot()` with a config containing an invalid hand rank key and verifies that a useful error (not a bare `KeyError`) is raised.

**7. No test for `progressive_bet` affecting `should_stop()` via insufficient funds**
- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py:402-410,447-451`
- When `progressive_bet` is added to `_minimum_bet_required()`, a player with a bankroll just above `base_bet * 3 + bonus_bet` but below `base_bet * 3 + bonus_bet + progressive_bet` should stop. No existing test verifies this boundary -- all `TestStopOnInsufficientFunds` tests in `/Users/chrishenry/source/let_it_ride/tests/unit/simulation/test_session.py` use `SessionConfig` without `progressive_bet`.
- Recommendation: Add a test with `progressive_bet > 0` where the bankroll is sufficient for the base game but insufficient once the progressive bet is included, and verify the session stops with `insufficient_funds`.

### Medium

**8. No test for `jackpot_percentage` value greater than 1.0**
- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/progressive_jackpot.py:125-129`
- The `evaluate_payout` method checks `payout_rule.value >= 1.0` to decide whether to reset the pool. A percentage value of `1.5` would pass this check, pay out 150% of the pool (which is more money than exists in the pool), then reset. This drives the pool negative before reset. Neither `ProgressivePayoutEntryConfig` (which uses `ge=0` with no upper bound for `jackpot_percentage` type) nor `ProgressivePayout` validates this. No test explores values above 1.0.
- Recommendation: Add at least a boundary test with `value=1.0` (exact jackpot hit) and `value=0.999` (partial hit, no reset) to verify the `>= 1.0` threshold behavior. Consider also testing `value > 1.0` to document the current behavior or to verify rejection.

**9. Standard paytable test does not verify all 6 entries**
- `/Users/chrishenry/source/let_it_ride/tests/unit/core/test_progressive_jackpot.py:188-207`
- `TestStandardProgressivePaytable` checks that the paytable has 6 entries and verifies that `ROYAL_FLUSH` is `jackpot_percentage` with `value=1.0`, but does not verify the other 5 entries (`STRAIGHT_FLUSH=0.10`, `FOUR_OF_A_KIND=500`, `FULL_HOUSE=100`, `FLUSH=75`, `STRAIGHT=50`). The individual payout tests in `TestProgressiveJackpotFixedPayout` and `TestProgressiveJackpotPercentagePayout` indirectly cover these through the jackpot fixture, but a paytable-level test verifying all entries would catch regressions if the standard paytable values change.
- Recommendation: Add assertions for each of the 6 entries' type and value in the standard paytable.

**10. No test for `ProgressivePaytable` with an empty payouts dict**
- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/progressive_jackpot.py:37-44`
- An empty paytable (no qualifying hands) is a valid edge case. A `ProgressiveJackpot` with an empty paytable should return `0.0` for all hand ranks. No test verifies this.
- Recommendation: Add a test creating a `ProgressiveJackpot` with an empty `ProgressivePaytable` and verify all hand ranks return `0.0`.

**11. No test for `SessionConfig` with `progressive_bet` field**
- `/Users/chrishenry/source/let_it_ride/tests/unit/simulation/test_session.py:91-137`
- `TestSessionConfigInitialization.test_create_minimal_config` asserts `config.bonus_bet == 0.0` but does not assert `config.progressive_bet == 0.0`. `test_create_full_config` creates a config with `bonus_bet=5.0` but does not include `progressive_bet`. Neither test verifies the new field exists or defaults correctly.
- Recommendation: Add `assert config.progressive_bet == 0.0` to the minimal config test, and include `progressive_bet=2.0` in the full config test.

**12. No test for `contribute()` with negative or zero bet amounts**
- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/progressive_jackpot.py:95-101`
- The `contribute()` method accepts any float including negative values and zero. A negative contribution would decrease the pool, which is logically incorrect. No test documents the current behavior for these edge cases.
- Recommendation: Add boundary tests for `contribute(0.0)` and `contribute(-1.0)` to document expected behavior.

**13. No test for multiple consecutive percentage payouts depleting the pool**
- While `test_straight_flush_deducts_from_pool` verifies a single 10% deduction, no test verifies the compounding effect over multiple hits (e.g., 10% of 10000 = 1000, then 10% of 9000 = 900, etc.). This would validate the pool shrinkage math across iterations.
- Recommendation: Add a test calling `evaluate_payout(STRAIGHT_FLUSH)` multiple times and verifying the pool and payout values decrease geometrically.

**14. `run_to_completion()` not tested with progressive -- `SessionResult` population gap**
- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py:600-625`
- The full session lifecycle (`run_to_completion()`) wires `_total_progressive_wagered` into the final `SessionResult` at line 625. The existing `TestRunToCompletion` class at line 843 of the test file does not pass a `progressive_jackpot` to any `Session`. The `SessionResult` returned by `run_to_completion()` is never checked for `total_progressive_wagered`.
- Recommendation: Add a `run_to_completion()` test with progressive enabled and verify `result.total_progressive_wagered == progressive_bet * hands_played`.

### Positive Observations

- **Well-organized test classes**: Both test files follow the project's pattern of grouping tests by behavior (`TestProgressiveJackpotContribution`, `TestProgressiveJackpotFixedPayout`, etc.) with descriptive class and method docstrings.
- **Correct use of `pytest.approx`**: All monetary float assertions use `pytest.approx()`, which is consistent with the project's existing test patterns and avoids brittle floating-point comparisons.
- **Good coverage of the `reset_to_seed=False` branch**: The `test_reset_to_seed_false` test at `/Users/chrishenry/source/let_it_ride/tests/unit/core/test_progressive_jackpot.py:175` covers a non-obvious behavioral branch where the pool zeroes out instead of resetting to seed.
- **Fixture reuse**: The `standard_paytable` and `jackpot` fixtures are well-designed for reuse across test classes, following the project's fixture patterns.
- **Pydantic validation boundary coverage**: The config tests cover zero values (`test_zero_bet_amount_rejected`, `test_zero_contribution_rate_rejected`), negative values (`test_negative_seed_amount_rejected`, `test_negative_value_rejected`), out-of-range values (`test_contribution_rate_over_one_rejected`), and the `extra="forbid"` behavior (`test_extra_fields_rejected`).
- **Factory function coverage for happy paths**: Both `standard_progressive_paytable()` default path and `create_progressive_jackpot()` custom paytable path are tested.
