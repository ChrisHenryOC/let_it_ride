# Test Coverage Review - PR #78

## Summary

PR #78 adds dealer discard mechanics to the GameEngine with a new `DealerConfig` model. The test suite is comprehensive with 15 unit tests covering the `DealerConfig` model validation, backwards compatibility, enabled discard functionality, and integration scenarios. Test quality is high with good isolation, deterministic seeds, and meaningful assertions. However, there are a few edge cases and error conditions that should be tested to ensure robustness.

## Findings

### Critical

None identified.

### High

1. **Missing test for DeckEmptyError when excessive discards are configured**
   - **File:** `tests/unit/core/test_dealer_mechanics.py`
   - **Issue:** When `discard_cards` is set high (e.g., 10) combined with the 5 cards needed for player/community (total 15), this still fits in a 52-card deck. However, there is no test verifying behavior when the deck cannot satisfy the discard request. While the current max of 10 makes this unlikely with a single deck, multi-deck support or future changes could expose this gap.
   - **Impact:** Could lead to unhandled exceptions in edge cases.

### Medium

1. **No test for FullConfig integration with DealerConfig**
   - **File:** `tests/unit/config/test_models.py`
   - **Issue:** The PR adds `dealer: DealerConfig` to `FullConfig`, but there is no test in `test_models.py` verifying that `FullConfig` properly initializes and validates the `dealer` section. The existing `TestFullConfig.test_default_config` test does not assert on `config.dealer`.
   - **Impact:** Could miss configuration loading issues in production.

2. **Missing test for invalid type for discard_cards**
   - **File:** `tests/unit/core/test_dealer_mechanics.py`
   - **Issue:** Tests cover boundary values (0, 1, 10, 11) but do not test invalid types (e.g., float, string, None). Pydantic will handle these, but explicit tests document expected behavior.
   - **Impact:** Low, as Pydantic validation handles this, but documentation value is reduced.

3. **No test for YAML configuration loading with dealer section**
   - **File:** `tests/unit/config/test_loader.py` (missing)
   - **Issue:** The PR adds `DealerConfig` to the configuration model but does not include integration tests verifying that YAML files with a `dealer:` section are correctly parsed and loaded.
   - **Impact:** Configuration errors may not be caught until runtime.

### Low

1. **Test uses hasattr for Card validation instead of type check**
   - **File:** `tests/unit/core/test_dealer_mechanics.py:343`
   - **Issue:** `test_discarded_cards_tracked_for_validation` uses `hasattr(card, "rank")` instead of `isinstance(card, Card)` for validation.
   - **Impact:** Minor; hasattr check is weaker but still functional.

2. **Duplicate fixture definition for `rng`**
   - **File:** `tests/unit/core/test_dealer_mechanics.py`
   - **Issue:** The test file uses the `rng` fixture from `conftest.py` but also imports `random` directly for the `test_reproducible_with_same_seed` test. This is correct behavior, but the pattern could be more consistent.
   - **Impact:** Negligible; code style preference.

## Missing Tests

1. **FullConfig.dealer default value test**
   - Add to `tests/unit/config/test_models.py::TestFullConfig::test_default_config`:
   ```python
   assert config.dealer is not None
   assert config.dealer.discard_enabled is False
   assert config.dealer.discard_cards == 3
   ```

2. **FullConfig.dealer custom value test**
   - Add a test verifying `FullConfig(dealer=DealerConfig(discard_enabled=True, discard_cards=5))` works correctly.

3. **YAML loader test with dealer section**
   - Add test in `test_loader.py` loading a YAML with:
   ```yaml
   dealer:
     discard_enabled: true
     discard_cards: 5
   ```

4. **Deck exhaustion edge case test**
   - Test behavior when deck cannot satisfy discard + deal requirements (even if currently impossible with constraints).

5. **GameEngine with dealer discard + bonus bet integration**
   - No test combines dealer discard with bonus betting to ensure they interact correctly.

## Recommendations

1. **Add FullConfig.dealer assertion to test_default_config**
   - **File:** `/Users/chrishenry/source/let_it_ride/tests/unit/config/test_models.py:627-637`
   - Add `assert config.dealer is not None` to verify the new field is properly initialized.

2. **Add isinstance check for Card validation**
   - **File:** `/Users/chrishenry/source/let_it_ride/tests/unit/core/test_dealer_mechanics.py:343`
   - Replace `hasattr(card, "rank") and hasattr(card, "suit")` with `isinstance(card, Card)` for stronger type validation.

3. **Add integration test for dealer discard + bonus bet**
   - **File:** `/Users/chrishenry/source/let_it_ride/tests/unit/core/test_dealer_mechanics.py`
   - Add test verifying that bonus bet evaluation still works correctly when dealer discard is enabled.

4. **Consider property-based testing for discard counts**
   - Use hypothesis library to test arbitrary valid discard_cards values (1-10) ensure consistent behavior.

## Test Coverage Analysis

| Component | Tests Added | Coverage Assessment |
|-----------|-------------|---------------------|
| DealerConfig model | 5 tests | Good - covers defaults, custom values, boundaries |
| Discard disabled | 3 tests | Good - covers backwards compatibility |
| Discard enabled | 4 tests | Good - covers core functionality |
| Integration | 4 tests | Good - covers card uniqueness, reset behavior, reproducibility |
| FullConfig integration | 0 tests | Gap - needs assertion in existing test |
| YAML loading | 0 tests | Gap - needs new test |

## Conclusion

The test suite for PR #78 is well-structured and covers the primary functionality thoroughly. The main gaps are in configuration integration (FullConfig and YAML loading) rather than the core game mechanics. The test quality is high with good use of fixtures, clear naming, and meaningful assertions. Addressing the medium-severity findings would bring test coverage to production-ready quality.
