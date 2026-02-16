# Consolidated Review for PR #159 -- LIR-63: Progressive Bet Strategies

## Summary

This PR adds four progressive jackpot side bet strategies (never, always, jackpot_threshold, bankroll_conditional) following the established bonus strategy pattern. The implementation is clean and well-structured with proper use of frozen dataclasses, Protocol-based interfaces, Pydantic config validation, and a factory function. The 40 unit tests provide good coverage of the strategy logic itself. The most significant gap is that progressive strategies are only wired into the single-seat `Session` path -- multi-seat `TableSession` simulations silently ignore the configured strategy and fall back to the static config value. Additionally, there are no integration tests verifying the new `Session.play_hand()` code path that invokes the progressive strategy.

## Issue Matrix

| # | Severity | Issue | File:Line | Reviewer(s) | In PR Scope? | Actionable? |
|---|----------|-------|-----------|-------------|--------------|-------------|
| 1 | High | Progressive strategy not passed to TableSession (multi-seat gap) | `controller.py:432-455` | Code Quality, Test Coverage, Docs | Yes | Yes |
| 2 | High | No session-level integration test for progressive strategy in `play_hand()` | `session.py:531-548` | Test Coverage | Yes | Yes |
| 3 | High | No bankroll sufficiency check before placing progressive bet | `session.py:531-550` | Code Quality | Yes | Yes |
| 4 | Medium | Zero `starting_bankroll` bypasses bankroll ratio check (fail-open) | `progressive.py:195` | Security, Code Quality, Test Coverage | Yes | Yes |
| 5 | Medium | `_minimum_bet_required` uses static config, not dynamic strategy output | `session.py:420-424` | Security | Yes | Yes |
| 6 | Medium | Duplicated validation between Pydantic model and factory function | `models.py:1038-1050`, `progressive.py:222-237` | Code Quality | Yes | Yes |
| 7 | Medium | Per-hand ProgressiveContext allocation on hot path | `session.py:535-545` | Performance | Yes | No (systemic -- defer to holistic refactor of all context types) |
| 8 | Medium | CLAUDE.md missing ProgressiveStrategy protocol, config section, and strategy dir entry | `CLAUDE.md:44,54,77` | Docs | Yes | Yes |
| 9 | Medium | Example YAML config does not demonstrate `progressive_strategy` | `progressive_jackpot.yaml` | Docs | Yes | Yes |
| 10 | Medium | No test for `ProgressiveJackpot.seed_amount` property | `progressive_jackpot.py:96-98` | Test Coverage | Yes | Yes |
| 11 | Medium | No config model tests for `JackpotThresholdConfig` and `BankrollConditionalProgressiveConfig` validation | `models.py:988-1011` | Test Coverage | Yes | Yes |
| 12 | Medium | Progressive bet timing comment should clarify pre-result state semantics | `session.py:529-550` | Code Quality, Test Coverage | Yes | Yes |
| 13 | Low | No validation that `get_progressive_bet` returns non-negative values | `session.py:546-547` | Security | Yes | Yes |
| 14 | Low | `BankrollConditionalProgressiveStrategy.__init__` missing parameter validation | `progressive.py:164-178` | Security | Yes | Yes |
| 15 | Low | Docstrings use "exceeds" where code uses `>=` (meets or exceeds) | `models.py:1013-1014`, `progressive.py:115` | Docs | Yes | Yes |
| 16 | Low | `progressive_strategy_factory` creates new instance per session unnecessarily (strategies are stateless) | `controller.py:409-412` | Performance | Yes | Yes |
| 17 | Low | Inline comment "fresh state per session" misleading for stateless strategies | `controller.py:552` | Docs | Yes | Yes |
| 18 | Low | Module docstring missing factory function mention | `progressive.py:1-13` | Docs | Yes | Yes |
| 19 | Low | `ProgressiveContext` docstring "Extends" could imply inheritance | `progressive.py:25` | Docs | Yes | Yes |
| 20 | Low | Test fixtures could use `dataclasses.replace` to reduce boilerplate | `test_progressive.py:87-113` | Code Quality | Yes | Yes |

## Actionable Issues

Issues where both **In PR Scope = Yes** and **Actionable = Yes**:

### High Severity (fix before merge)

1. **#1 -- TableSession multi-seat gap**: Wire `progressive_strategy_factory` into `_create_table_session` the same way it's wired into `_create_session`. Multi-seat progressive simulations currently silently ignore the configured strategy.

2. **#2 -- Missing integration test**: Add a session-level test that constructs a `Session` with a `progressive_strategy` and verifies the strategy's return value (not the config's static `progressive_bet`) determines the actual bet placed. Verify `ProgressiveContext` fields are populated correctly.

3. **#3 -- Bankroll sufficiency check**: Add a check that the player can afford the progressive bet before placing it, or clamp the bet to available funds.

### Medium Severity (strongly recommended)

4. **#4 -- Fail-open on zero starting_bankroll**: Change to fail-closed behavior -- return `0.0` when `starting_bankroll <= 0` and `min_bankroll_ratio` is set. Update corresponding test.

5. **#5 -- `_minimum_bet_required` stale calculation**: Update to account for dynamic progressive bets, or at minimum add a comment documenting that sessions may stop prematurely when a strategy would have returned 0.

6. **#6 -- DRY validation**: Add a comment in the factory function explaining why it re-validates (defensive against `model_construct`), or extract shared validation constants.

8. **#8 -- CLAUDE.md updates**: Add `ProgressiveStrategy` to Key abstractions, `progressive_strategy` to Configuration section, and "progressive" to strategy directory description.

9. **#9 -- Example YAML**: Add a commented `progressive_strategy` section to `progressive_jackpot.yaml`.

10. **#10 -- seed_amount property test**: Add a unit test for `ProgressiveJackpot.seed_amount`.

11. **#11 -- Config validation tests**: Add tests for negative value rejection on `JackpotThresholdConfig` and `BankrollConditionalProgressiveConfig`.

12. **#12 -- Timing comment**: Add a brief comment clarifying that `ProgressiveContext` uses pre-result bankroll state.

## Deferred Issues

| # | Reason |
|---|--------|
| 7 | Systemic issue affecting all context types (BonusContext, StrategyContext, ProgressiveContext). Should be addressed holistically in a follow-up, not in isolation. |

## Performance Assessment

This PR is unlikely to threaten the 100,000 hands/second throughput target. Strategy logic is O(1) per hand. The main overhead is the per-hand `ProgressiveContext` allocation which adds ~5-10% to existing allocation budget. The frozen dataclass with `__slots__` is the correct pattern.

## Security Assessment

**Risk Level: Low.** Good input validation via Pydantic `extra="forbid"`, `Literal` constraints, and `ge`/`gt` field validators. Frozen dataclasses prevent mutation. Factory function rejects unknown types. Primary concerns are data integrity edge cases (fail-open on zero bankroll, premature session stops) rather than traditional vulnerabilities.
