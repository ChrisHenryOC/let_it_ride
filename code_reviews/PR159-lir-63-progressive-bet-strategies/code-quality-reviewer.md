# Code Quality Review for PR #159

## Summary

This PR adds progressive jackpot side bet strategies following the established bonus strategy pattern closely, resulting in clean, consistent code. The implementation is well-structured with proper use of `__slots__`, frozen dataclasses, Protocol-based interfaces, and a factory function. The main concerns are duplicated validation logic between the Pydantic model validator and the factory function, a missing bankroll sufficiency check before placing progressive bets, and the progressive strategy not being wired into `TableSession` for multi-seat play.

## Findings

### Critical

No critical findings.

### High

**H1 - Progressive strategy not passed to TableSession (multi-seat gap)** - `src/let_it_ride/simulation/controller.py:432-455` - The `progressive_strategy_factory` is only wired into the single-seat `_create_session` path. The `_create_table_session` path (used when `num_seats > 1`) does not receive or forward the progressive strategy. This means multi-seat simulations will silently ignore the user's progressive strategy configuration and fall back to the static config value.
- In PR Scope: Yes
- Actionable: Yes

**H2 - No bankroll sufficiency check before placing progressive bet** - `src/let_it_ride/simulation/session.py:531-550` - The progressive strategy can return a non-zero bet amount even when the player cannot afford it. The bonus bet path does not appear to have this check either, but since this is new code, it is worth noting. If `progressive_bet > 0` but the bankroll is insufficient, the simulation proceeds with a bet the player cannot cover, which could produce negative bankroll values.
- In PR Scope: Yes
- Actionable: Yes

### Medium

**M1 - Duplicated validation between Pydantic model and factory function** - `src/let_it_ride/config/models.py:1038-1050` and `src/let_it_ride/strategy/progressive.py:222-237` - The `validate_type_config_match` model validator in `ProgressiveStrategyConfig` checks that the required sub-config is present for `jackpot_threshold` and `bankroll_conditional` types. The `create_progressive_strategy` factory function performs the exact same None checks and raises the same error messages. This is a DRY violation. The factory checks are defensive (guarding against `model_construct` bypassing validation), which is reasonable, but the duplicated error messages should at least reference a shared constant or the factory should document why it re-validates.
- In PR Scope: Yes
- Actionable: Yes

**M2 - BankrollConditionalProgressiveStrategy silently passes when starting_bankroll is zero** - `src/let_it_ride/strategy/progressive.py:192-197` - When `starting_bankroll == 0` and `min_bankroll_ratio` is set, the ratio check is skipped entirely, and the bet is placed. This is tested (see `test_zero_starting_bankroll_skips_ratio_check`), so it is intentional, but it is a questionable default. A zero starting bankroll is likely a misconfiguration, and silently allowing the bet could mask bugs. Consider logging a warning or raising a `ValueError` during context creation if `starting_bankroll <= 0` and a ratio check is configured.
- In PR Scope: Yes
- Actionable: Yes

**M3 - ProgressiveContext shares many fields with BonusContext but has no shared base** - `src/let_it_ride/strategy/progressive.py:19-47` vs `src/let_it_ride/strategy/bonus.py:18-47` - `ProgressiveContext` and `BonusContext` share 6 of their fields (`bankroll`, `starting_bankroll`, `session_profit`, `hands_played`, `main_streak`, `base_bet`). This is not a blocking issue now, but as more context types are added, extracting a shared `SessionContext` base dataclass would reduce duplication in both the context definitions and the construction sites in `session.py`.
- In PR Scope: Yes
- Actionable: Yes (but could be deferred)

**M4 - Progressive bet evaluation happens after hand is played** - `src/let_it_ride/simulation/session.py:529-550` - The progressive bet decision uses `self._bankroll.balance` and `self._bankroll.session_profit` which reflect the state *before* the current hand's main result is applied (since `apply_result` is called later at line 578). This is consistent with how the bonus bet is decided before the hand. However, the progressive context also uses `self._streak` which has not yet been updated for the current hand. The comment says "Evaluate progressive side bet if enabled" but the decision is made post-deal. This ordering is fine for game mechanics (the bet is placed before cards are dealt in real life), but the code placement after `play_hand()` could confuse future maintainers. A brief comment clarifying the timing semantics would help.
- In PR Scope: Yes
- Actionable: Yes

### Low

**L1 - Magic numbers for min/max bonus bet** - `src/let_it_ride/simulation/session.py:506-507` - The values `1.0` and `100.0` for `min_bonus_bet` and `max_bonus_bet` are hardcoded. This is pre-existing code, not introduced in this PR, but the progressive strategy avoids this pattern (it does not have min/max clamping), which is an inconsistency to note.
- In PR Scope: No
- Actionable: No (pre-existing)

**L2 - Variable abbreviation `bc` in factory** - `src/let_it_ride/strategy/progressive.py:239` - The variable `bc = config.bankroll_conditional` uses a short abbreviation. This matches the pattern in `bonus.py:592`, so it is consistent with the codebase, but a more descriptive name like `bankroll_config` would improve readability.
- In PR Scope: Yes
- Actionable: Yes

**L3 - Test fixtures could use `dataclasses.replace` to reduce boilerplate** - `tests/unit/strategy/test_progressive.py:87-113` - Several test methods create full `ProgressiveContext` instances inline when they could use `dataclasses.replace(default_context, current_jackpot=25000.0)` on the fixture. This would make tests more concise and highlight which fields are relevant to each test case.
- In PR Scope: Yes
- Actionable: Yes
