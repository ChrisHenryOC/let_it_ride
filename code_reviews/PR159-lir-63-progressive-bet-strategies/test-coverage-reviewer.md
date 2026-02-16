# Test Coverage Review: PR #159 -- LIR-63 Progressive Bet Strategies

## Summary

The PR adds 40 well-structured unit tests in `tests/unit/strategy/test_progressive.py` covering all four strategy implementations, the factory function, and Pydantic config validation. The strategy-level unit tests are thorough with good boundary coverage. However, there are no integration-level tests verifying that `Session.play_hand()` actually invokes the progressive strategy (the new code path at session.py:531-548), no test for the new `ProgressiveJackpot.seed_amount` property, and the multi-seat `TableSession` path in the controller is not wired to progressive strategies at all (a functional gap that also lacks test coverage).

---

## Findings

### HIGH Severity

#### H1: No session-level integration test for progressive strategy in `play_hand()`

The new code in `Session.play_hand()` (lines 531-548 of `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py`) builds a `ProgressiveContext` and calls `self._progressive_strategy.get_progressive_bet()` to dynamically determine the progressive bet. This entire code path has zero test coverage. The existing progressive session tests in `TestSessionProgressiveSideBet` (test_session.py:1443) all use the static `config.progressive_bet` fallback because they never pass a `progressive_strategy` to `Session.__init__`.

A test should verify that when a `Session` is constructed with a `progressive_strategy`, the strategy's return value (not the config's `progressive_bet`) determines the actual bet placed. This should also verify the `ProgressiveContext` fields are populated correctly from session state.

- **File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py:531-548`
- **In PR Scope:** Yes
- **Actionable:** Yes

#### H2: Multi-seat `TableSession` path does not receive progressive strategy

In `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/controller.py`, the `progressive_strategy_factory` is passed to `_create_session` (line 466) but NOT to `_create_table_session` (lines 435-441). Multi-seat simulations with progressive enabled will silently fall back to the static config bet amount. There are no tests covering this gap because the table session path was not updated.

- **File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/controller.py:435-442`
- **In PR Scope:** Yes (the controller was modified in this PR)
- **Actionable:** Yes

---

### MEDIUM Severity

#### M1: No test for `ProgressiveJackpot.seed_amount` property

The PR adds a new public `seed_amount` property to `ProgressiveJackpot` at `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/progressive_jackpot.py:96-98`. This property is used by `Session.play_hand()` to populate `ProgressiveContext.seed_amount`. There is no unit test in `tests/unit/core/test_progressive_jackpot.py` verifying this property returns the correct value.

- **File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/progressive_jackpot.py:96-98`
- **In PR Scope:** Yes
- **Actionable:** Yes

#### M2: `BankrollConditionalProgressiveStrategy` with `starting_bankroll=0` silently skips ratio check

When `context.starting_bankroll == 0` and `min_bankroll_ratio` is set, the strategy skips the ratio check entirely (line 195 of progressive.py: `if self._min_bankroll_ratio is not None and context.starting_bankroll > 0`), meaning the bet is placed. While there IS a test for this (`test_zero_starting_bankroll_skips_ratio_check` at test_progressive.py:285), the test only asserts the bet IS placed. There is no test verifying the behavior is intentional vs. accidental division-by-zero avoidance. A negative `starting_bankroll` value is also untested -- it would cause the ratio check to invert its logic (e.g., bankroll=100, starting=-100 gives ratio=-1.0, which is < 1.1, so the bet is blocked, which may be correct but is undocumented).

- **File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/strategy/progressive.py:195-197`
- **In PR Scope:** Yes
- **Actionable:** Yes

#### M3: No config model tests for `JackpotThresholdConfig` and `BankrollConditionalProgressiveConfig` in the config test module

The `ProgressiveStrategyConfig` validation is tested in `test_progressive.py` under `TestProgressiveStrategyConfig`, but the sub-config models `JackpotThresholdConfig` and `BankrollConditionalProgressiveConfig` have no dedicated tests in the config test directory (`tests/unit/config/`). Specifically:
- `JackpotThresholdConfig` has `min_jackpot: ge=0` validation -- no test for negative value rejection.
- `BankrollConditionalProgressiveConfig` has `min_bankroll_ratio: gt=0` validation -- no test for zero or negative value rejection.
- `BankrollConditionalProgressiveConfig` allows `min_session_profit` and `min_bankroll_ratio` to both be `None` -- no test verifying this edge case at the config level.

- **File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/config/models.py:988-1011`
- **In PR Scope:** Yes
- **Actionable:** Yes

#### M4: Progressive strategy context uses pre-result bankroll state but post-engine-call timing

The `ProgressiveContext` at session.py:535-544 reads `self._bankroll.balance` and `self._bankroll.session_profit` AFTER `engine.play_hand()` returns but BEFORE `self._bankroll.apply_result()` is called (line 578). This means the progressive strategy sees the bankroll from BEFORE the current hand's main/bonus result is applied. This is consistent with the bonus strategy behavior but is a subtle invariant that should be documented with a test asserting the context values match pre-hand state.

- **File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py:535-544`
- **In PR Scope:** Yes
- **Actionable:** Yes

---

### LOW Severity

#### L1: Protocol compliance tests use `hasattr` instead of `isinstance` with `runtime_checkable`

Tests like `test_satisfies_protocol` (e.g., test_progressive.py:122, 154, 200, 300) check protocol conformance via `hasattr(strategy, "get_progressive_bet")`. This only verifies the attribute exists, not that the signature matches. Since `ProgressiveStrategy` is a `Protocol`, it could be decorated with `@runtime_checkable` and tested with `isinstance()` for stronger validation.

- **File:** `/Users/chrishenry/source/let_it_ride/tests/unit/strategy/test_progressive.py:122`
- **In PR Scope:** Yes
- **Actionable:** Yes

#### L2: No parameterized tests for boundary values across strategies

The test suite tests individual boundary values (e.g., jackpot exactly at threshold) but does not use `@pytest.mark.parametrize` for systematic boundary testing. For example, `JackpotThresholdStrategy` could benefit from a parameterized test covering `(jackpot_below, jackpot_at, jackpot_above)` x `(threshold_zero, threshold_normal, threshold_very_large)` combinations.

- **File:** `/Users/chrishenry/source/let_it_ride/tests/unit/strategy/test_progressive.py`
- **In PR Scope:** Yes
- **Actionable:** Yes

#### L3: `FullConfig` integration with `progressive_strategy` field not tested

The `FullConfig` model now includes `progressive_strategy: ProgressiveStrategyConfig`. There is no test verifying that a full YAML config with a `progressive_strategy` section parses correctly end-to-end, or that the default `ProgressiveStrategyConfig` (type="never") is correctly applied when the section is omitted.

- **File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/config/models.py:1274-1276`
- **In PR Scope:** Yes
- **Actionable:** Yes

#### L4: Missing test for `create_progressive_strategy` passing correct parameters to strategy constructors

The factory function tests (`TestCreateProgressiveStrategy`) verify the returned type via `isinstance` but do not verify that constructor parameters are correctly forwarded. For example, `test_create_jackpot_threshold_strategy` does not assert that the created strategy's internal `_min_jackpot` matches the config value of `30000.0`. A behavioral test (calling `get_progressive_bet` with a context at the threshold boundary) would provide stronger verification.

- **File:** `/Users/chrishenry/source/let_it_ride/tests/unit/strategy/test_progressive.py:323-329`
- **In PR Scope:** Yes
- **Actionable:** Yes
