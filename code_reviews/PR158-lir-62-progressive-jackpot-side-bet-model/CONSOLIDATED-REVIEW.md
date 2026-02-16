# Consolidated Review for PR #158 — LIR-62: Progressive Jackpot Side Bet Model

## Summary

This PR adds a well-structured progressive jackpot side bet with clean separation between configuration (Pydantic), domain logic (dataclasses), and simulation integration. The core `ProgressiveJackpot` class is well-designed with `__slots__`, frozen value types, O(1) payout lookup, and strong per-session isolation. However, there are several issues to address: a validation gap where `validate_session_config` omits `progressive_bet` from minimum bankroll checks, an unhandled `KeyError` on invalid custom paytable hand rank names, missing upper-bound validation on `jackpot_percentage` values, frozen dataclass reconstruction overhead in the hot path, and no integration tests for the session-level progressive code paths. The multi-seat shared jackpot design produces order-dependent results within a round.

## Issue Matrix

| # | Severity | Issue | File:Line | Reviewer(s) | In PR Scope? | Actionable? |
|---|----------|-------|-----------|-------------|--------------|-------------|
| 1 | Critical | `validate_session_config` omits `progressive_bet` from min bankroll check | `session.py:82` | Quality, Security, Docs, Tests | Yes | Yes |
| 2 | Critical | Unhandled `KeyError` on invalid hand rank name in custom paytable | `progressive_jackpot.py:190` | Quality, Security, Tests | Yes | Yes |
| 3 | High | No upper-bound on `jackpot_percentage` value — can drive pool negative | `models.py:949` | Quality, Security, Docs | Yes | Yes |
| 4 | High | Shared mutable jackpot in multi-seat produces order-dependent results | `table_session.py:528-531` | Quality, Security | Yes | Yes |
| 5 | High | No integration tests for `Session.play_hand()` with progressive | `session.py:513-544` | Tests | Yes | Yes |
| 6 | High | No integration tests for `TableSession.play_round()` with progressive | `table_session.py:510-581` | Tests | Yes | Yes |
| 7 | High | `total_progressive_wagered` never asserted in any test | Multiple files | Tests | Yes | Yes |
| 8 | High | Frozen dataclass reconstruction every hand in hot path | `session.py:527-543`, `table_session.py:537-552` | Perf, Quality | Yes | Yes |
| 9 | High | `standard_progressive_paytable()` recreated per session (700k objects/100k sessions) | `progressive_jackpot.py:139-169` | Perf | Yes | Yes |
| 10 | High | No tests for `get_progressive_jackpot()`/`get_progressive_bet()` utilities | `utils.py:103-128` | Tests | Yes | Yes |
| 11 | Medium | DRY violation: 14-field dataclass reconstruction duplicated in two files | `session.py:527-543`, `table_session.py:537-552` | Quality | Yes | Yes |
| 12 | Medium | `GameHandResult`/`PlayerSeat` docstrings missing new fields | `game_engine.py:29-42`, `table.py:30-41` | Docs, Quality | Yes | Yes |
| 13 | Medium | `SessionConfig`/`TableSessionConfig` docstrings missing `progressive_bet`, stale min-bet formula | `session.py:148-170`, `table_session.py:37-67` | Docs | Yes | Yes |
| 14 | Medium | `ProgressivePaytable` missing `slots=True` (inconsistent with convention) | `progressive_jackpot.py:37` | Quality, Perf | Yes | Yes |
| 15 | Medium | `contribute()` accepts negative bet amounts without validation | `progressive_jackpot.py:95-101` | Quality, Security | Yes | Yes |
| 16 | Medium | Confusing coexistence of `ProgressiveJackpotConfig` and `ProgressiveSideBetConfig` — no cross-reference | `models.py:920-977` | Quality, Docs | Yes | Yes |
| 17 | Medium | Loop-invariant condition checked per-seat in table session hot path | `table_session.py:528` | Perf, Quality | Yes | Yes |
| 18 | Medium | `enhanced_seat_results` list allocated every round even when progressive disabled | `table_session.py:515` | Perf | Yes | Yes |
| 19 | Medium | `CLAUDE.md` does not mention progressive config section | `CLAUDE.md` | Docs | Yes | Yes |
| 20 | Medium | `ProgressivePayoutEntryConfig.value` docstring claims "fraction 0-1" but validator allows any `ge=0` | `models.py:943-949` | Docs | Yes | Yes |
| 21 | Medium | No test for `progressive_bet` affecting `should_stop()` insufficient funds | `session.py:402-451` | Tests | Yes | Yes |
| 22 | Medium | No test for invalid hand rank name in `create_progressive_jackpot()` | `progressive_jackpot.py:190` | Tests | Yes | Yes |
| 23 | Low | `_minimum_bet_required()` recomputes session-constant arithmetic per hand | `session.py:402-411` | Perf | Yes | Yes |
| 24 | Low | Float accumulation drift in pool (acceptable at current scale) | `progressive_jackpot.py:101` | Perf, Security | Yes | No |
| 25 | Low | No validation that `starting_jackpot >= seed_amount` | `models.py:974` | Security | Yes | Yes |

## Actionable Issues

### Must Fix (Critical)

1. **#1 — `validate_session_config` omits `progressive_bet`**: Add `progressive_bet` parameter, include in `min_bet_required` calculation, update callers in `SessionConfig.__post_init__` and `TableSessionConfig.__post_init__`.

2. **#2 — Unhandled `KeyError` on invalid hand rank**: Wrap `FiveCardHandRank[hand_name.upper()]` in try/except, re-raise as `ValueError` listing valid rank names.

### Should Fix (High)

3. **#3 — No upper-bound on `jackpot_percentage`**: Add `model_validator` on `ProgressivePayoutEntryConfig` enforcing `value <= 1.0` when `type == "jackpot_percentage"`.

4. **#4 — Shared mutable jackpot ordering in multi-seat**: Snapshot pool at round start; process all contributions first, then evaluate all payouts against snapshot. Or document as intentional if modeling sequential casino dealing.

5. **#5, #6, #7 — Missing integration tests**: Add `Session.play_hand()` and `TableSession.play_round()` tests with progressive enabled; assert `total_progressive_wagered`, `progressive_bet`, `progressive_payout`, and adjusted `net_result`.

6. **#8, #11 — Frozen dataclass reconstruction / DRY**: Use `dataclasses.replace()` in both locations (eliminates duplication and fragile field-by-field copy, cleaner than `object.__setattr__`).

7. **#9 — Paytable recreated per session**: Cache `standard_progressive_paytable()` as module-level constant.

8. **#10 — Missing utility function tests**: Test `get_progressive_jackpot()` and `get_progressive_bet()` enabled/disabled paths.

### Nice to Have (Medium)

9. **#12, #13, #20 — Docstring updates**: Add `progressive_bet`/`progressive_payout` to result dataclass docstrings; fix stale min-bet formula; fix value docstring.

10. **#14 — `ProgressivePaytable` missing `slots=True`**: Add `slots=True`.

11. **#15 — `contribute()` negative guard**: Add `if bet_amount < 0: raise ValueError(...)`.

12. **#16 — Cross-reference config classes**: Add "See Also" notes to both `ProgressiveJackpotConfig` and `ProgressiveSideBetConfig`.

13. **#17, #18 — Hot path optimizations**: Hoist loop-invariant check; guard list allocation behind progressive-enabled check.

14. **#19 — Update CLAUDE.md**: Add `progressive` to Configuration section.

15. **#21, #22 — Additional test gaps**: Test `progressive_bet` affecting insufficient funds, test invalid hand rank error.

## Deferred Issues

| # | Reason |
|---|--------|
| #24 | Float drift negligible at current session lengths (200 hands). Would need `Decimal` (100x perf hit). |
| #15 (`SessionResult` field ordering) | Constrained by frozen dataclass default rules — field must come after non-default fields. Would require adding defaults to `peak_bankroll`/`max_drawdown`/`max_drawdown_pct`, affecting all existing construction sites. |
