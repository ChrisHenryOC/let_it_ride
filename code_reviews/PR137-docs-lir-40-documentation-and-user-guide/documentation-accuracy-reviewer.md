# Documentation Accuracy Review: PR #137

## Summary

This PR adds comprehensive documentation for the Let It Ride Strategy Simulator. The documentation is well-organized and covers installation, usage, configuration, strategies, and API reference. However, there are several documentation inaccuracies where examples do not match the actual implementation, including incorrect API signatures, missing class methods, wrong field names, and references to nonexistent sample config files.

## Findings

### Critical

**1. Card.from_string() method does not exist**
- **File:** `docs/api.md:292-293`
- **Issue:** Documentation shows `Card.from_string("As")` and `Card.from_string("Th")` but this method does not exist in the Card class.
- **Actual:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/card.py` - The Card class only has `__init__(rank, suit)`, no `from_string()` factory method.
- **Impact:** Users will get AttributeError when trying to use documented examples.

**2. Card.is_high_card property does not exist**
- **File:** `docs/api.md:298`
- **Issue:** Documentation shows `print(card.is_high_card)  # True (10, J, Q, K, A)` but Card has no such property.
- **Actual:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/card.py` - Card only has `rank` and `suit` attributes.
- **Impact:** Users will get AttributeError when trying to use documented example.

**3. Deck.cards_remaining is a method, not a property**
- **File:** `docs/api.md:314`
- **Issue:** Documentation shows `print(deck.cards_remaining)` treating it as a property.
- **Actual:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/deck.py:72` - `cards_remaining()` is a method requiring parentheses.
- **Impact:** Users will get unexpected output (method object repr) instead of the count.

**4. RNGQualityResult has wrong field names in documentation**
- **File:** `docs/api.md:528-529`
- **Issue:** Documentation shows `result.chi_square_p_value` and `result.runs_test_p_value`.
- **Actual:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/rng.py:26-44` - The actual fields are `chi_square_stat`, `chi_square_passed`, `runs_test_stat`, and `runs_test_passed`. There are no p-value fields.
- **Impact:** Users will get AttributeError when trying to access documented fields.

**5. validate_rng_quality uses different parameter name**
- **File:** `docs/api.md:527`
- **Issue:** Documentation shows `validate_rng_quality(rng, num_samples=100000)`.
- **Actual:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/rng.py:260-265` - The parameter is named `sample_size`, not `num_samples`.
- **Impact:** Users will get TypeError for unexpected keyword argument.

### High

**6. SessionConfig field names mismatch**
- **File:** `docs/api.md:265-270`
- **Issue:** Documentation shows `SessionConfig(starting_bankroll=..., win_limit=..., loss_limit=..., max_hands=...)`.
- **Actual:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py:137-159` - Uses `starting_bankroll` (correct) but actual field is just that, not aliased. However, Session example uses `seed=i` in constructor.
- **Related:** At line 610, `Session(config, strategy, bonus_strategy=bonus_strategy, seed=i)` - Session class does not accept a `seed` parameter in its constructor.
- **Impact:** The Session constructor example will fail with unexpected keyword argument error.

**7. BettingSystem.record_result has wrong signature**
- **File:** `docs/api.md:562-563`
- **Issue:** Documentation shows `betting.record_result(won=False, profit=-15.0)`.
- **Actual:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/bankroll/betting_systems.py:56-65` - Method signature is `record_result(self, result: float) -> None` taking only a single `result` parameter.
- **Impact:** Users will get TypeError when using documented signature.

**8. ProportionalBetting not exported from bankroll module**
- **File:** `docs/api.md:546`
- **Issue:** Documentation lists `ProportionalBetting` in imports from `let_it_ride.bankroll`.
- **Actual:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/bankroll/__init__.py` - `ProportionalBetting` is not in `__all__` or exported. The class exists only in config/models.py as a config model, not as an actual betting system implementation.
- **Impact:** Users will get ImportError.

**9. SessionResult uses session_profit not net_profit**
- **File:** `docs/api.md:277, 465, 615`
- **Issue:** Documentation shows `result.net_profit` in multiple places.
- **Actual:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py:197` - The field is named `session_profit`, not `net_profit`.
- **Impact:** Users will get AttributeError.

### Medium

**10. CLI structure in CONTRIBUTING.md is incorrect**
- **File:** `CONTRIBUTING.md:38`
- **Issue:** Shows `cli/` as a directory directly under `src/let_it_ride/`.
- **Actual:** The structure is correct (`cli/` does exist as `/Users/chrishenry/source/let_it_ride/src/let_it_ride/cli/`), but the indentation suggests it's a standalone component. This is minor.

**11. quickstart.md references missing config files**
- **File:** `docs/quickstart.md:136-143`
- **Issue:** Sample configurations table lists `bonus_conditional.yaml` and `multi_seat.yaml`.
- **Actual:** `/Users/chrishenry/source/let_it_ride/configs/` contains: `aggressive.yaml`, `basic_strategy.yaml`, `bonus_comparison.yaml`, `conservative.yaml`, `progressive_betting.yaml`, `sample_config.yaml`. Neither `bonus_conditional.yaml` nor `multi_seat.yaml` exist.
- **Impact:** Users will get FileNotFoundError when following quickstart examples.

**12. SimulationResults.win_rate field name**
- **File:** `docs/api.md:511`
- **Issue:** Documentation shows `results.win_rate`.
- **Actual:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/aggregation.py:77` - The field is `session_win_rate` not `win_rate`.
- **Impact:** Users will get AttributeError.

**13. DeckConfig missing use_crypto field**
- **File:** `docs/configuration.md:956-966`
- **Issue:** Documentation shows `use_crypto: false` option under deck configuration.
- **Actual:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/config/models.py:63-74` - DeckConfig only has `shuffle_algorithm` field. The `use_crypto` option is part of RNGManager, not DeckConfig.
- **Impact:** Config validation will fail with "Extra inputs are not permitted".

**14. DeckConfig missing validate_rng_quality field**
- **File:** `docs/configuration.md:966`
- **Issue:** Documentation shows `validate_rng_quality: false` option under deck configuration.
- **Actual:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/config/models.py:63-74` - DeckConfig does not have this field.
- **Impact:** Config validation will fail.

### Low

**15. CONTRIBUTING.md test file path may not exist**
- **File:** `CONTRIBUTING.md:72`
- **Issue:** Shows `poetry run pytest tests/unit/strategy/test_basic.py` as example.
- **Actual:** File exists at `/Users/chrishenry/source/let_it_ride/tests/unit/strategy/test_basic.py` - this is correct.

**16. Conservative strategy config section name**
- **File:** `docs/strategies.md:287-292`
- **Issue:** Shows `min_strength_bet1` and `min_strength_bet2` options.
- **Actual:** Would need to verify against actual conservative_strategy implementation. These appear to be aspirational rather than implemented options.

### Informational

**17. Missing docs/performance.md referenced in index.md**
- **File:** `docs/index.md:19`
- **Issue:** Links to `performance.md` which is not included in this PR.
- **Impact:** Broken link in documentation navigation.

**18. Missing docs/let_it_ride_implementation_plan.md update**
- **File:** `docs/index.md:18`
- **Issue:** References implementation plan but PR only updates requirements.md.
- **Impact:** Not a direct error, just noting the reference.

**19. Deck shuffle requires rng parameter**
- **File:** `docs/api.md:308`
- **Issue:** Documentation shows `deck.shuffle()` without parameters.
- **Actual:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/deck.py:32-45` - Method signature is `shuffle(self, rng: random.Random) -> None` requiring an RNG parameter.
- **Impact:** Users will get TypeError for missing required argument.

## Recommendations

1. **Critical fixes required before merge:**
   - Add `Card.from_string()` class method or update documentation to use `Card(Rank.ACE, Suit.SPADES)` syntax
   - Fix `cards_remaining` to show as method call with parentheses
   - Update RNGQualityResult field names to match actual implementation
   - Fix validate_rng_quality parameter name to `sample_size`
   - Remove or implement `Session(seed=...)` parameter
   - Fix BettingSystem.record_result signature
   - Remove ProportionalBetting from imports or implement and export it
   - Change `net_profit` to `session_profit` throughout

2. **High priority fixes:**
   - Create `bonus_conditional.yaml` and `multi_seat.yaml` config files, or update quickstart.md table
   - Fix `win_rate` to `session_win_rate`
   - Remove `use_crypto` and `validate_rng_quality` from deck config documentation

3. **Documentation consistency:**
   - Add deck.shuffle(rng) parameter to example
   - Create performance.md or remove link
