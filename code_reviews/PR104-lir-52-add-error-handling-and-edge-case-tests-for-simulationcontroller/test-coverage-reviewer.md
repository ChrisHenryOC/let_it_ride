# Test Coverage Review - PR #104

## Summary

This PR adds comprehensive error handling and edge case tests for `SimulationController`, covering callback exception propagation, bonus bet calculation branches, and configuration edge cases. The tests are well-structured and cover the identified code paths from the scratchpad analysis. However, the tests primarily verify that operations complete without errors rather than asserting specific expected values, which limits their effectiveness for catching regressions.

## Findings

### Critical

None

### High

1. **Missing Direct Verification of Bonus Bet Calculation Values**
   - **Location**: `tests/integration/test_controller.py:448-574` (TestBonusBetCalculation class)
   - **Issue**: All bonus bet calculation tests only verify that the simulation completes successfully and hands are played. They do not verify that the correct bonus bet amount was actually used. The tests document the expected calculations in comments (e.g., `ratio = 0.5  # Expected bonus_bet = 5.0`) but never assert these values.
   - **Impact**: If the bonus bet calculation logic regresses or produces incorrect values, these tests would still pass as long as the simulation runs without errors.
   - **Recommendation**: Add assertions that verify the actual bonus bet amounts used. This could be done by:
     - Exposing bonus bet info in SessionResult
     - Using a mock or spy to capture the bonus_bet parameter passed to SessionConfig
     - Adding a test that verifies total wagered includes expected bonus amounts

2. **Missing Coverage for `bankroll_conditional` Bonus Strategy**
   - **Location**: `src/let_it_ride/simulation/controller.py:425-437`
   - **Issue**: The controller's `_create_session` method only handles `always` and `static` bonus configurations. The `bankroll_conditional` strategy type exists in the config models but has no corresponding handling in the controller, and no test coverage for this gap.
   - **Impact**: If a user configures `bankroll_conditional` bonus strategy, it will silently result in a 0.0 bonus bet, which may not be the intended behavior.
   - **Recommendation**: Either add handling for `bankroll_conditional` in the controller, or add a test that explicitly documents this limitation/behavior.

### Medium

1. **Untested Branch: enabled=True with Neither always nor static Set**
   - **Location**: `src/let_it_ride/simulation/controller.py:425-437`
   - **Issue**: The bonus bet calculation has an implicit branch where `enabled=True` but neither `always` nor `static` configs are provided. In this case, `bonus_bet` remains 0.0. While Pydantic validation may prevent this in practice, the controller code does not guard against it.
   - **Recommendation**: Add a test that documents this edge case behavior, or add explicit handling/validation.

2. **Test for Precedence is Not Actually Testing Precedence**
   - **Location**: `tests/integration/test_controller.py:620-653`
   - **Issue**: The test `test_always_takes_precedence_over_static_when_both_configured` acknowledges in its docstring that Pydantic prevents testing this case, then proceeds to just test the `always` configuration works correctly. This provides no additional value beyond `test_bonus_enabled_with_always_config`.
   - **Recommendation**: Either remove this test (it is redundant), refactor it to mock the config bypassing Pydantic validation, or rename it to clarify its actual purpose.

3. **Parametrized Test Would Be More Maintainable**
   - **Location**: `tests/integration/test_controller.py:576-618`
   - **Issue**: The `test_bonus_ratio_with_various_base_bets` test uses a for-loop over test cases. Using `@pytest.mark.parametrize` would provide better test isolation, clearer failure messages, and follows the existing pattern used elsewhere in the test file.
   - **Recommendation**: Convert to a parametrized test for consistency.

### Low

1. **Inconsistent Use of Helper Function**
   - **Location**: `tests/integration/test_controller.py:448-653`
   - **Issue**: The `TestBonusBetCalculation` and `TestEdgeCases` classes create `FullConfig` objects directly, while the `TestErrorHandling` class uses the `create_test_config` helper. This inconsistency is reasonable since bonus tests need custom bonus configs, but the helper could be extended.
   - **Recommendation**: Consider extending `create_test_config` to accept optional `bonus_strategy` parameter for consistency, or document why direct config creation is preferred for bonus tests.

2. **Unused Variable in test_bonus_ratio_with_various_base_bets**
   - **Location**: `tests/integration/test_controller.py:579`
   - **Issue**: The `expected_bonus` variable in the test case tuples is never used for assertions. It is calculated and documented but not verified.
   - **Recommendation**: Either remove the unused variable or add assertions that use it.

3. **Missing Test for Zero-Session Edge Case**
   - **Location**: N/A (not in diff)
   - **Issue**: No test verifies behavior when `num_sessions=0`. While Pydantic likely validates this, it could be worth documenting expected behavior.
   - **Recommendation**: Add a test that verifies appropriate validation error for `num_sessions=0`.

## Recommendations

### Priority 1: Add Value Verification to Bonus Tests

The most impactful improvement would be adding actual value verification to the bonus bet tests. Example approach:

```python
def test_bonus_enabled_with_static_ratio_calculates_correctly(self) -> None:
    """Test that static.ratio correctly calculates bonus bet."""
    base_bet = 10.0
    ratio = 0.5
    expected_bonus = 5.0  # base_bet * ratio

    config = FullConfig(
        simulation=SimulationConfig(num_sessions=1, hands_per_session=1, random_seed=42),
        bankroll=BankrollConfig(starting_amount=500.0, base_bet=base_bet, ...),
        bonus_strategy=BonusStrategyConfig(
            enabled=True,
            type="static",
            static=StaticBonusConfig(amount=None, ratio=ratio),
        ),
    )

    # Option A: Mock SessionConfig creation to capture bonus_bet
    with patch.object(SessionConfig, '__init__', wraps=SessionConfig.__init__) as mock_init:
        controller = SimulationController(config)
        controller.run()
        # Verify bonus_bet parameter
        call_kwargs = mock_init.call_args.kwargs
        assert call_kwargs.get('bonus_bet') == expected_bonus

    # Option B: If SessionResult exposes bonus wagered
    # assert result.session_results[0].total_bonus_wagered == expected_bonus
```

### Priority 2: Add Test Coverage for Missing Bonus Strategy Types

Document or test behavior for unsupported bonus strategies:

```python
def test_bankroll_conditional_bonus_not_yet_supported(self) -> None:
    """Verify that bankroll_conditional bonus results in zero bonus bet.

    Note: This strategy type exists in config but is not yet implemented
    in the controller. This test documents the current behavior.
    """
    config = FullConfig(
        ...
        bonus_strategy=BonusStrategyConfig(
            enabled=True,
            type="bankroll_conditional",
            bankroll_conditional=BankrollConditionalBonusConfig(base_amount=5.0),
        ),
    )

    controller = SimulationController(config)
    results = controller.run()

    # Current behavior: bonus_bet = 0.0 since bankroll_conditional not handled
    assert len(results.session_results) == 1
    # TODO: Once implemented, verify bonus bets are applied
```

### Priority 3: Convert Loop-Based Test to Parametrized

```python
@pytest.mark.parametrize(
    "base_bet,ratio,expected_bonus",
    [
        (5.0, 0.5, 2.5),
        (10.0, 0.25, 2.5),
        (20.0, 1.0, 20.0),
        (1.0, 0.1, 0.1),
    ],
)
def test_bonus_ratio_with_various_base_bets(
    self, base_bet: float, ratio: float, expected_bonus: float
) -> None:
    """Test ratio calculation with different base_bet values."""
    ...
```

## Coverage Analysis

### Branches Covered by This PR

| Branch | Test Coverage |
|--------|--------------|
| Progress callback exception (mid-simulation) | Covered |
| Progress callback exception (first session) | Covered |
| Bonus disabled | Covered |
| Bonus always config | Covered |
| Bonus static.amount | Covered |
| Bonus static.ratio | Covered |
| Single hand session | Covered |
| High limits (never trigger) | Covered |
| Minimal win/loss limits | Covered |
| Deterministic with bonus | Covered |

### Branches NOT Covered

| Branch | Current Status |
|--------|---------------|
| Bonus bankroll_conditional | Not tested (not implemented in controller) |
| Bonus streak_based | Not tested (not implemented in controller) |
| Bonus session_conditional | Not tested (not implemented in controller) |
| Bonus combined | Not tested (not implemented in controller) |
| Bonus custom | Not tested (not implemented in controller) |
| enabled=True with no sub-config | Not tested |
| Session raises exception during run | Not tested |
| zero hands_per_session | Not tested (likely validation error) |

## Test Quality Assessment

- **Structure**: Good - tests follow arrange-act-assert pattern and are well-organized into logical test classes
- **Isolation**: Good - each test creates fresh controller and config instances
- **Determinism**: Good - uses fixed random seeds for reproducibility
- **Naming**: Good - descriptive test names that document expected behavior
- **Assertions**: Weak - most tests only assert completion rather than specific values
- **Edge Cases**: Moderate - covers some edge cases but misses several bonus strategy types

## Files Reviewed

- `/tmp/pr104.diff` - PR diff
- `/Users/chrishenry/source/let_it_ride/tests/integration/test_controller.py` - Full test file (lines 1-812)
- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/controller.py` - Controller implementation
- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/config/models.py` - Configuration models
