# Test Coverage Review - PR #158

## Summary

The PR adds two new test files with solid unit-level coverage of the `ProgressiveJackpot` core class and the `ProgressiveSideBetConfig` Pydantic model. However, there are significant integration-level gaps: the `Session.play_hand()` progressive integration path has zero test coverage, the `TableSession.play_round()` progressive path is untested, the utility functions `get_progressive_jackpot` and `get_progressive_bet` have no tests, and the new `total_progressive_wagered` field is never asserted anywhere in the test suite.

## Findings

### Critical

1. **No integration tests for `Session` with progressive jackpot enabled**
   - File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py:516-544`
   - The `play_hand()` method has a 30-line block that contributes to the jackpot, evaluates payout, reconstructs a `GameHandResult` with adjusted `net_result`, and accumulates `_total_progressive_wagered`. None of this logic is exercised by any test. A grep for "progressive" in `tests/unit/simulation/test_session.py` returns zero matches.
   - This is where the progressive bet actually affects bankroll, net result, and stop conditions. Bugs here (e.g., incorrect net_result adjustment, double-counting the bet cost) would go undetected.

2. **No integration tests for `TableSession` with progressive jackpot enabled**
   - File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py:513-581`
   - The `play_round()` method has a complex loop that per-seat contributes to a shared jackpot, evaluates payouts, creates enhanced `PlayerSeat` objects, and adjusts bankroll with `adjusted_net`. This entire multi-seat progressive flow is untested.
   - The shared jackpot design means order of seat evaluation matters (seat 1's contribution inflates the pool before seat 2's payout evaluation). This ordering dependency is a prime candidate for integration testing but is not covered.

3. **`total_progressive_wagered` never asserted in any test**
   - The field is added to `SessionResult` (`session.py:219`), `SessionResult.to_dict()` (`session.py:242`), `SessionResult.with_table_session_info()` (`session.py:292`), CSV export headers (`export_csv.py:43`), and `_SeatState` (`table_session.py:159`). No test verifies that this field is correctly populated, exported, or propagated through `with_table_session_info()`.

### High

4. **No tests for `get_progressive_jackpot()` and `get_progressive_bet()` utility functions**
   - File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/utils.py:103-128`
   - These factory functions are called from both `controller.py` and `parallel.py` to create per-session jackpot instances. The disabled-returns-None and disabled-returns-0.0 paths, as well as the enabled path, have no coverage.

5. **`validate_session_config` does not account for `progressive_bet` in minimum bankroll check**
   - File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py:82`
   - The validation at line 82 computes `min_bet_required = (base_bet * 3) + bonus_bet` but does not include `progressive_bet`. However, `_minimum_bet_required()` at line 402 does include it. This means a session could pass config validation but immediately stop on insufficient funds if the progressive bet pushes the total past the bankroll. No test exposes this inconsistency.

6. **No test for `create_progressive_jackpot` with invalid hand rank name**
   - File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/progressive_jackpot.py:190`
   - `FiveCardHandRank[hand_name.upper()]` will raise `KeyError` if the config contains an unrecognized hand rank string (e.g., "INVALID_RANK"). There is no test verifying that this error path produces a useful error message, and the code does not wrap it with a more descriptive exception.

### Medium

7. **No test for `ProgressivePayout` with `jackpot_percentage` value greater than 1.0**
   - File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/progressive_jackpot.py:129`
   - The `evaluate_payout` method checks `payout_rule.value >= 1.0` to decide whether to reset. A percentage value like 1.5 would pass this check and attempt to pay out 150% of the pool, resulting in a negative pool balance before reset. Neither the `ProgressivePayout` dataclass nor `ProgressivePayoutEntryConfig` validates that percentage values are between 0 and 1 (the config uses `ge=0` with no upper bound). No test explores this boundary.

8. **No test for `progressive_bet` affecting `should_stop()` via insufficient funds**
   - File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py:447-451`
   - When `progressive_bet` is added to `_minimum_bet_required()`, a player could run out of funds earlier than without the progressive. No test verifies that a session correctly stops due to insufficient funds when the progressive bet is the marginal cost that triggers it.

9. **No test for `SessionConfig.progressive_bet` validation**
   - The `progressive_bet` field on `SessionConfig` (line 170) and `TableSessionConfig` (line 67) accepts any float, including negative values. There is no validation in `validate_session_config` for `progressive_bet` and no test exercising negative progressive bet rejection.

10. **Missing test for `run_to_completion` with progressive jackpot populating `total_progressive_wagered` in `SessionResult`**
    - File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py:625`
    - The full session lifecycle (run multiple hands, accumulate progressive wagered, produce final result) is untested for the progressive path.

### Low

11. **No test for multiple percentage payouts depleting the pool across hands**
    - While `test_straight_flush_deducts_from_pool` verifies a single deduction, there is no test showing the pool shrinking over successive straight flush hits (e.g., 10% of 10000, then 10% of 9000, etc.), which would validate the compounding pool reduction math.

12. **Standard paytable test only checks count and one entry**
    - File: `/Users/chrishenry/source/let_it_ride/tests/unit/core/test_progressive_jackpot.py:191-207`
    - `TestStandardProgressivePaytable` checks the paytable has 6 entries and that `ROYAL_FLUSH` is `jackpot_percentage`, but does not verify the specific values of the other 5 entries. The individual payout tests in `TestProgressiveJackpotFixedPayout` implicitly cover this but through the jackpot object rather than the paytable directly.

13. **No test for `ProgressivePaytable` with an empty payouts dict**
    - An empty paytable is a valid edge case (all hands return 0.0 payout) but is never tested.

### Positive

- **Thorough unit tests for the `ProgressiveJackpot` class**: The test file at `/Users/chrishenry/source/let_it_ride/tests/unit/core/test_progressive_jackpot.py` is well-organized with clear class groupings (`TestProgressiveJackpotContribution`, `TestProgressiveJackpotFixedPayout`, `TestProgressiveJackpotPercentagePayout`, `TestProgressiveJackpotNonQualifying`, `TestProgressiveJackpotReset`). Each test follows arrange-act-assert and has a descriptive docstring.

- **Good coverage of Pydantic validation boundaries**: The config tests at `/Users/chrishenry/source/let_it_ride/tests/unit/config/test_progressive_config.py` test zero values, negative values, out-of-range contribution rates, extra fields, and the `FullConfig` integration -- covering the key validation constraints.

- **`reset_to_seed=False` path is tested**: The `test_reset_to_seed_false` test at line 175 verifies the alternative behavior where the pool goes to zero after a royal flush rather than resetting to seed, which is a non-obvious behavioral branch.

- **`create_progressive_jackpot` factory has reasonable coverage**: Both the standard paytable default path and the custom paytable path are tested, including verifying that the contribution rate and starting pool from config are applied correctly.

- **Use of `pytest.approx` for float comparisons**: All monetary assertions correctly use `pytest.approx()` to avoid floating-point comparison issues.
