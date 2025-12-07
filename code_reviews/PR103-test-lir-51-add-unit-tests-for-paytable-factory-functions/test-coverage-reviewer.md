# Test Coverage Review: PR #103 - LIR-51 Unit Tests for Paytable Factory Functions

## Summary

This PR adds comprehensive unit tests for `_get_main_paytable()` and `_get_bonus_paytable()` factory functions. The tests effectively cover all implemented code paths including happy paths for all paytable types, error conditions for unimplemented features, and proper validation of return types. Test organization follows established patterns in the codebase with good helper function reuse.

## Findings by Severity

### Critical

None identified.

### High

None identified.

### Medium

**M1: Missing test for paytable name attribute verification**
- File: `tests/unit/simulation/test_factories.py`
- Lines: 689-695 (test_standard_paytable_matches_expected_instance)
- Issue: The test verifies `payouts` match but does not verify the `name` attribute matches. If the factory returned a paytable with correct payouts but wrong name, this could cause issues in logging/debugging.
- Recommendation: Add assertion `assert paytable.name == expected.name` to complement the payouts check.

**M2: Missing test for paytable_c progressive parameter handling**
- File: `tests/unit/simulation/test_factories.py`
- Lines: 277-286 (test_paytable_c_matches_expected_instance)
- Issue: The `bonus_paytable_c()` factory function accepts an optional `progressive_payout` parameter (default 1000). The test only verifies the default behavior. If the `_get_bonus_paytable()` function were later updated to pass a custom progressive payout from config, this test would not catch regressions.
- Context: Looking at `controller.py:302-308`, the current implementation calls `bonus_paytable_c()` without arguments, so this is currently correct but worth noting for future-proofing.

### Low

**L1: Helper function attribute completeness for BonusStrategyConfig**
- File: `tests/unit/simulation/test_factories.py`
- Lines: 149-154 (in `_create_full_config_bypassing_validation`)
- Issue: The helper sets `type="never"` and `paytable` attributes on BonusStrategyConfig but does not set `always`, `static`, or `bankroll_conditional` attributes. While these are not accessed by the functions under test, incomplete object construction could mask issues if the implementation changes.
- Recommendation: Consider adding `object.__setattr__(bonus_strategy, "always", None)` etc. for completeness, or document this is intentionally minimal.

**L2: No test for boundary case where bonus is enabled but config.paytables.bonus is None**
- File: `tests/unit/simulation/test_factories.py`
- Issue: The `_get_bonus_paytable()` function accesses `config.paytables.bonus.type` (line 302 in controller.py). If `bonus` were None but `enabled` were True, this would raise AttributeError. While Pydantic validation likely prevents this, a defensive test could catch issues if validation is bypassed elsewhere.
- Note: This is an edge case that Pydantic validation handles, but given the pattern of bypassing validation for testing factory logic, consistency would suggest testing this scenario.

**L3: Consider parametrized tests for paytable variants**
- File: `tests/unit/simulation/test_factories.py`
- Lines: 218-270 (paytable_a, paytable_b, paytable_c tests)
- Issue: The tests for paytable_a, paytable_b, and paytable_c follow an identical pattern (returns correct type, matches expected instance). Using `pytest.mark.parametrize` would reduce code duplication and make it easier to add new paytable variants.
- Note: This is a style suggestion, not a bug. The current approach is clear and readable.

## Specific Recommendations

### 1. Add name attribute verification (Medium priority)

In `test_standard_paytable_matches_expected_instance`:
```python
def test_standard_paytable_matches_expected_instance(self) -> None:
    """Test that standard paytable returns the same values as standard_main_paytable()."""
    config = _create_full_config(main_paytable_type="standard")
    paytable = _get_main_paytable(config)
    expected = standard_main_paytable()
    assert paytable.name == expected.name  # Add this line
    assert paytable.payouts == expected.payouts
```

Apply similar changes to bonus paytable tests.

### 2. Consider adding integration-style test (Optional)

A test that exercises both paytable factories together as they would be used in `SimulationController.run()`:
```python
def test_paytables_integrate_with_game_engine(self) -> None:
    """Test that factory-created paytables work with GameEngine."""
    config = _create_full_config(
        main_paytable_type="standard",
        bonus_enabled=True,
        bonus_paytable_type="paytable_b"
    )
    main = _get_main_paytable(config)
    bonus = _get_bonus_paytable(config)

    # Verify paytables are valid (can calculate payouts)
    from let_it_ride.core.hand_evaluator import FiveCardHandRank
    from let_it_ride.core.three_card_evaluator import ThreeCardHandRank

    # These should not raise
    main.calculate_payout(FiveCardHandRank.PAIR_TENS_OR_BETTER, 10.0)
    bonus.calculate_payout(ThreeCardHandRank.PAIR, 5.0)
```

## Coverage Analysis

### Code Paths Tested

| Function | Code Path | Tested |
|----------|-----------|--------|
| `_get_main_paytable` | type="standard" | Yes |
| `_get_main_paytable` | type="liberal" (NotImplementedError) | Yes |
| `_get_main_paytable` | type="tight" (NotImplementedError) | Yes |
| `_get_main_paytable` | type="custom" (NotImplementedError) | Yes |
| `_get_bonus_paytable` | bonus disabled | Yes |
| `_get_bonus_paytable` | type="paytable_a" | Yes |
| `_get_bonus_paytable` | type="paytable_b" | Yes |
| `_get_bonus_paytable` | type="paytable_c" | Yes |
| `_get_bonus_paytable` | unknown type (ValueError) | Yes |
| `_get_bonus_paytable` | type="custom" (ValueError) | Yes |

### Edge Cases

| Edge Case | Tested |
|-----------|--------|
| Return type verification | Yes |
| Payout values match expected | Yes |
| Name attribute matches | No (see M1) |
| Error message content verification | Yes |
| Progressive paytable custom payout | No (see M2) |

## Quality Assessment

### Strengths

1. **Good test isolation**: Each test focuses on a single behavior
2. **Clear test naming**: Names describe what is being tested and expected outcome
3. **Proper use of helper functions**: `_create_full_config()` and `_create_full_config_bypassing_validation()` reduce duplication
4. **Validation bypass pattern**: Correctly tests factory validation independent of Pydantic
5. **Consistent with existing patterns**: Follows the same structure as `TestCreateBettingSystem` and `TestCreateStrategy`
6. **Error message matching**: Uses `match=` parameter to verify specific error messages

### Areas for Improvement

1. **Parametrized tests**: Could reduce code duplication for similar paytable tests
2. **Attribute completeness**: Name attribute verification would improve thoroughness
3. **Documentation**: Consider adding class-level docstrings explaining the validation bypass pattern

## Conclusion

The test coverage for the paytable factory functions is **comprehensive and well-structured**. All main code paths are tested, error conditions are properly validated, and the tests follow established patterns in the codebase. The identified issues are minor enhancements rather than gaps that could lead to bugs. The PR is ready for merge with optional consideration of the medium-priority suggestions.
