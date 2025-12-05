# Test Coverage Review: PR #92 - Table Integration Tests (LIR-45)

## Summary

This PR adds comprehensive integration tests for the Table and TableSession classes with 1,118 lines of well-structured test code. The tests cover lifecycle management, strategy integration, multi-round bankroll tracking, bonus bets, dealer discards, betting systems, reproducibility, edge cases, and strategy context handling. The test suite demonstrates good coverage breadth, but has a few areas where edge case coverage could be strengthened.

---

## Findings by Severity

### High

#### H1: Peak Bankroll Assertion Logic May Allow False Positives
**File:** `tests/integration/test_table.py:504-507`

The assertion for peak bankroll uses an `or` condition that is logically always true when peak_bankroll is positive:

```python
assert (
    sr.peak_bankroll >= sr.starting_bankroll
    or sr.peak_bankroll >= sr.final_bankroll
)
```

This condition is satisfied if peak equals starting bankroll OR peak equals final bankroll, which means it does not actually verify that peak_bankroll was correctly tracked as the maximum value seen during the session. A session that incorrectly sets `peak_bankroll = starting_bankroll` would pass this test even if the bankroll went higher during play.

**Recommendation:** The assertion should be:
```python
assert sr.peak_bankroll >= sr.starting_bankroll
assert sr.peak_bankroll >= sr.final_bankroll
```

---

### Medium

#### M1: Win Limit Test Uses Seed Search Pattern with pytest.skip
**File:** `tests/integration/test_table.py:129-155`

The test `test_single_seat_session_to_win_limit` searches through 100 seeds looking for one that produces a win limit condition. If none is found, it skips the test. This is a reasonable approach for integration tests with randomness, but:

1. The skip message does not indicate the range of seeds tried
2. If the seed search consistently fails (e.g., due to code changes affecting RNG), the test silently becomes a no-op
3. The 1000-1100 seed range is hardcoded without documentation explaining why this range was chosen

**Recommendation:** Consider using a fixed seed known to produce the desired outcome, or document why the search is necessary. Adding a warning log when the search fails multiple times in CI would help catch regressions.

#### M2: Test Names Suggest Determinism but Use Random Outcomes
**File:** `tests/integration/test_table.py:883-919`

The test `test_different_seeds_produce_different_results` has a comment acknowledging:
```python
# Note: Theoretically could be same, but extremely unlikely
```

This introduces a small but non-zero chance of test flakiness. While 50 hands with different seeds is very unlikely to produce identical results, it is not impossible.

**Recommendation:** Consider strengthening this assertion by checking multiple independent variables (cards dealt, decisions made, etc.) in addition to profit, or increase the number of hands to make collision probability truly negligible.

#### M3: Missing Test for Exact Loss Limit Boundary
**File:** `tests/integration/test_table.py:157-186`

The loss limit test verifies the session stops when losses occur, but does not specifically verify the boundary condition where `session_profit == -loss_limit` exactly (as opposed to `< -loss_limit`). The source code uses `<=` comparison:

```python
if seat_state.bankroll.session_profit <= -self._config.loss_limit:
```

A test should verify that hitting exactly the loss limit (not going past it) triggers the stop condition.

**Recommendation:** Add a test case with a controlled mock that produces exactly the loss limit value:
```python
def test_loss_limit_triggered_on_exact_boundary(self):
    # Verify session stops when session_profit == -loss_limit exactly
```

---

### Low

#### L1: Incomplete Verification of Context Evolution
**File:** `tests/integration/test_table.py:1071-1131`

The test `test_session_provides_updated_context_each_round` verifies that `hands_played` increments correctly, but does not verify that other context fields (`session_profit`, `streak`, `bankroll`) are updated correctly between rounds.

**Recommendation:** Extend assertions to verify all context fields evolve correctly:
```python
# Verify session_profit changes based on results
# Verify streak tracking follows win/loss pattern
# Verify bankroll reflects cumulative results
```

#### L2: No Test for Zero Bonus Bet with Bonus Paytable Configured
**File:** `tests/integration/test_table.py:615-673`

The tests verify bonus bets work correctly when `bonus_bet > 0`, but there is no integration test verifying behavior when a bonus paytable is configured but `bonus_bet = 0` is passed. This edge case exists in the Table.play_round method.

**Recommendation:** Add a test verifying that `bonus_bet=0` with a configured bonus paytable works correctly and results in no bonus evaluation.

#### L3: MartingaleBetting Test Does Not Verify Bet Progression Values
**File:** `tests/integration/test_table.py:789-817`

The Martingale betting test verifies the session completes and hands are played, but does not verify that the bet amounts actually doubled after losses. The test description says "adjusts bet size" but the assertions only check `total_wagered > 0` and `hands_played == 20`.

**Recommendation:** Capture and verify the actual bet amounts used in each round, either through a mock or by analyzing total_wagered patterns.

#### L4: No Tests for Concurrent Stop Conditions at Different Thresholds
**File:** `tests/integration/test_table.py:922-1010`

While edge cases test maximum values, there is no test for scenarios where:
- Win limit and max hands are configured, and max hands is reached while under win limit
- Multiple stop conditions are set, and the first to trigger determines the outcome

The unit tests cover this, but integration tests with real game flow would add confidence.

**Recommendation:** Add an integration test with multiple stop conditions configured to verify priority/behavior.

#### L5: Missing Error Scenario Integration Tests
**File:** `tests/integration/test_table.py` (general)

The integration tests focus on successful execution paths. There are no integration tests for:
- What happens if the deck runs out of cards (theoretical with maximum configuration)
- Recovery behavior after exceptions in strategy.decide methods

These are edge cases that may be acceptable to skip for integration tests if covered in unit tests.

---

## Coverage Analysis

### Strengths

1. **Comprehensive Lifecycle Testing**: Complete coverage of session lifecycle from initialization through completion with all stop condition types (win limit, loss limit, max hands, insufficient funds)

2. **Multi-Seat Verification**: Good coverage of multi-seat scenarios including independent outcomes, shared community cards, and unique player cards

3. **Strategy Integration**: Tests for BasicStrategy, AlwaysRideStrategy, AlwaysPullStrategy, and CustomStrategy with complex rule conditions

4. **Reproducibility**: Solid tests for RNG seed-based reproducibility and verification that different seeds produce different results

5. **Bankroll Tracking**: Thorough testing of bankroll accumulation, peak tracking, drawdown calculation, and wagering totals

6. **Bonus Bet Handling**: Coverage of multi-seat bonus evaluation and session-level bonus wagering tracking

7. **Dealer Discard**: Tests verify discard mechanics work correctly across sessions

8. **Strategy Context**: Custom strategy classes capture and verify context propagation

### Areas for Improvement

1. **Boundary Conditions**: Some exact boundary tests (e.g., exact loss limit) are missing
2. **Error Paths**: No integration tests for error scenarios
3. **Bet Progression Verification**: Martingale test does not verify actual bet values
4. **Statistical Distribution**: No tests verify that hand outcomes follow expected statistical distributions (could use hypothesis for property-based testing)

---

## Test Quality Assessment

### Positive Patterns Observed

- **Clear Test Organization**: Logical grouping into classes by functionality
- **Descriptive Names**: Test names clearly indicate what is being verified
- **Fixture Usage**: Appropriate use of fixtures for shared setup
- **Assertion Quality**: Most assertions are specific and meaningful
- **Independence**: Tests are independent and can run in isolation
- **Reproducibility**: Seeded RNG ensures deterministic test behavior

### Patterns to Consider

- **Avoid pytest.skip for expected conditions**: The seed search pattern could mask failures
- **Verify intermediate state**: Some tests only check final results without verifying the journey

---

## Recommendations

1. **Fix High Severity Issue**: Correct the peak bankroll assertion logic (H1)
2. **Strengthen Boundary Tests**: Add exact boundary condition tests for stop conditions (M3)
3. **Consider Property-Based Testing**: For statistical validation, the hypothesis library could verify hand distributions
4. **Add Bet Progression Verification**: Ensure betting systems are actually changing bet values (L3)
5. **Document Seed Selection**: Explain why specific seed ranges are used (M1)

---

## Conclusion

This is a well-structured and comprehensive integration test suite that significantly improves confidence in the Table and TableSession components. The 1,118 lines of test code cover the major integration scenarios effectively. The identified issues are primarily refinements rather than critical gaps, with the exception of the peak bankroll assertion logic which should be corrected to ensure it provides meaningful verification.
