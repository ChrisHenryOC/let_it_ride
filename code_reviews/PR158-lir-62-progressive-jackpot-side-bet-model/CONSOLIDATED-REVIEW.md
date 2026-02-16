# Consolidated Review for PR #158 — LIR-62: Progressive Jackpot Side Bet Model

## Summary

This PR adds a well-structured progressive jackpot side bet model with clean separation between configuration (Pydantic), domain logic (dataclasses), and simulation integration. The core `ProgressiveJackpot` class is particularly well-designed with `__slots__`, frozen value types, O(1) payout lookup, and strong per-session isolation. However, there is one critical correctness issue (shared mutable jackpot state in multi-seat mode produces order-dependent results), significant test coverage gaps at the integration level, and several missing input validations that could corrupt simulation results.

## Issue Matrix

| # | Issue | Severity | Category | In PR Scope | Actionable | Notes |
|---|-------|----------|----------|-------------|------------|-------|
| 1 | Shared mutable jackpot across seats produces order-dependent payouts | Critical | Code Quality, Security | Yes | Yes | Pool should be snapshotted before processing seats in a round |
| 2 | No integration tests for `Session.play_hand()` progressive path | Critical | Test Coverage | Yes | Yes | 30-line block with bankroll/net_result logic is completely untested |
| 3 | No integration tests for `TableSession.play_round()` progressive path | Critical | Test Coverage | Yes | Yes | Multi-seat progressive loop untested; ordering dependency untested |
| 4 | `total_progressive_wagered` never asserted in any test | Critical | Test Coverage | Yes | Yes | Field added in 5 locations, verified in none |
| 5 | Missing error handling for invalid hand rank names in custom paytable | High | Code Quality, Security | Yes | Yes | Raw `KeyError` at `progressive_jackpot.py:190` |
| 6 | No validation that `jackpot_percentage` values are between 0 and 1 | High | Code Quality, Security | Yes | Yes | Values >1.0 drive pool negative; docstring says "0-1" but validator allows any `ge=0` |
| 7 | Two progressive config classes with overlapping names, no documentation | High | Code Quality, Docs | Yes | Yes | `ProgressiveJackpotConfig` vs `ProgressiveSideBetConfig` — unclear relationship |
| 8 | `validate_session_config` missing `progressive_bet` in minimum bankroll check | High | Test Coverage | Yes | Yes | Config validation uses `base_bet*3 + bonus_bet` but runtime uses `+ progressive_bet` |
| 9 | No tests for `get_progressive_jackpot()` / `get_progressive_bet()` utils | High | Test Coverage | Yes | Yes | Factory functions called from controller and parallel are untested |
| 10 | Frozen dataclass reconstruction on every hand (hot path) | High | Performance | Yes | Yes | 100k+ extra allocations/sec; use `object.__setattr__` or move into GameEngine |
| 11 | Paytable objects recreated per session (100k+ times) | High | Performance | Yes | Yes | Immutable paytable should be cached/shared; only pool state is per-session |
| 12 | Verbose result reconstruction duplicated in two places | Medium | Code Quality | Yes | Yes | DRY violation in `session.py:527-543` and `table_session.py:537-552` |
| 13 | `ProgressivePaytable` missing `slots=True` | Medium | Code Quality, Perf | Yes | Yes | Inconsistent with project convention |
| 14 | `GameHandResult` / `PlayerSeat` docstrings missing new fields | Medium | Documentation | Yes | Yes | `progressive_bet` and `progressive_payout` undocumented |
| 15 | `SessionConfig` / `TableSessionConfig` docstrings missing `progressive_bet` | Medium | Documentation | Yes | Yes | |
| 16 | `SessionResult` field ordering mismatch with docstring | Medium | Code Quality, Docs | Yes | Yes | Declared after `max_drawdown_pct`, documented after `total_bonus_wagered` |
| 17 | CLAUDE.md and README.md don't mention progressive side bet | Medium | Documentation | Yes | Yes | Integration test may fail for missing `progressive_jackpot.yaml` mention |
| 18 | Loop-invariant condition check per seat in table session | Medium | Performance | Yes | Yes | `if self._progressive_jackpot is not None` checked per-seat, per-round |
| 19 | `enhanced_seat_results` list allocated even when progressive disabled | Medium | Performance | Yes | Yes | |
| 20 | `_minimum_bet_required()` recomputes on every call | Medium | Performance | Yes | Yes | Values are session-constant; cache in `__init__` |
| 21 | No test for `progressive_bet` affecting `should_stop()` | Medium | Test Coverage | Yes | Yes | |
| 22 | No test for `jackpot_percentage` > 1.0 boundary | Medium | Test Coverage | Yes | Yes | |
| 23 | `contribute()` does not validate negative bet amounts | Low | Code Quality | Yes | Yes | |
| 24 | No validation `starting_jackpot >= seed_amount` | Low | Security | Yes | Yes | Confusing but not technically wrong |
| 25 | Float accumulation drift in pool over long sessions | Low | Security, Perf | Yes | No | Acceptable at current scale (200 hands/session) |
| 26 | Progressive bet not in `bets_at_risk` | Low | Documentation | Yes | No | Consistent with bonus bet handling; document the convention |

## Actionable Issues

These issues are in PR scope and should be addressed before merge:

### Critical (must fix)
1. **Shared mutable jackpot in multi-seat mode** — Snapshot pool state at round start before processing seats. All contributions should be applied, then all payouts evaluated against the pre-contribution pool value.
2. **Add integration tests for Session progressive path** — Test `play_hand()` with progressive enabled: verify contribution, payout, net_result adjustment, and bankroll impact.
3. **Add integration tests for TableSession progressive path** — Test `play_round()` with progressive enabled across multiple seats; verify ordering behavior.
4. **Assert `total_progressive_wagered`** — Add assertions in session result tests, `to_dict()` tests, and CSV export tests.

### High (should fix)
5. **Wrap `FiveCardHandRank[hand_name.upper()]` in try/except** — Catch `KeyError` and re-raise as `ValueError` with valid rank names listed.
6. **Add Pydantic `model_validator` for percentage upper bound** — Enforce `value <= 1.0` when `type == "jackpot_percentage"`.
7. **Clarify progressive config class relationship** — Add docstring cross-references between `ProgressiveJackpotConfig` (3-card bonus) and `ProgressiveSideBetConfig` (5-card side bet).
8. **Add `progressive_bet` to `validate_session_config`** — Include in `min_bet_required` calculation at `session.py:82`.
9. **Add tests for utility functions** — Cover `get_progressive_jackpot()` enabled/disabled and `get_progressive_bet()`.
10. **Optimize hot-path dataclass reconstruction** — Use `object.__setattr__` on frozen dataclass or restructure to avoid second allocation.
11. **Cache immutable paytable** — Use `@functools.lru_cache` or module-level constant for `standard_progressive_paytable()`.

### Medium (nice to have)
12-22. DRY up result reconstruction, add `slots=True` to `ProgressivePaytable`, update docstrings, update CLAUDE.md/README.md, hoist loop-invariant checks, cache `_minimum_bet_required()`, add boundary tests.

## Deferred Issues

| # | Issue | Reason |
|---|-------|--------|
| 25 | Float accumulation drift | Acceptable at current session scale (200 hands). Would need `Decimal` for cross-session pools — not in scope. |
| 26 | Progressive bet not in `bets_at_risk` | Consistent with existing bonus bet convention. Document rather than change. |
