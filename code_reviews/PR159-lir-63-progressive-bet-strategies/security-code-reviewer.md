# Security Review: PR #159 -- LIR-63 Progressive Bet Strategies

## Summary

This PR introduces progressive jackpot side bet strategies that dynamically decide whether a player places the optional progressive bet based on jackpot size and/or bankroll conditions. The code is well-structured with good input validation at the Pydantic config layer (`extra="forbid"`, `Literal` type constraints, `ge`/`gt` field validators). The primary security concerns relate to data integrity in a gambling simulation context: a division-by-zero guard that silently permits betting when it should arguably deny it, the `_minimum_bet_required` method not accounting for dynamic progressive bets, and the absence of a negative return value guard on strategy outputs.

## Findings

### Medium Severity

#### M1: Zero `starting_bankroll` bypasses bankroll ratio check, silently allowing bets

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/strategy/progressive.py:195`
**CWE:** CWE-369 (Divide By Zero), CWE-697 (Incorrect Comparison)
**In PR Scope:** Yes
**Actionable:** Yes

```python
if self._min_bankroll_ratio is not None and context.starting_bankroll > 0:
    current_ratio = context.bankroll / context.starting_bankroll
    if current_ratio < self._min_bankroll_ratio:
        return 0.0
```

When `starting_bankroll` is 0 (or negative), the ratio check is skipped entirely and the strategy returns the bet amount. This is the correct approach to avoid division by zero, but the fail-open behavior means a misconfigured session with `starting_bankroll=0` will always place the progressive bet regardless of the `min_bankroll_ratio` constraint. In a gambling simulator where bankroll integrity matters, this should fail-closed (return 0.0) when the ratio cannot be computed. The test `test_zero_starting_bankroll_skips_ratio_check` explicitly encodes the current fail-open behavior, suggesting this was intentional, but it undermines the purpose of the guard.

**Recommendation:** When `starting_bankroll <= 0` and `min_bankroll_ratio` is set, return `0.0` instead of allowing the bet. This is the conservative (fail-closed) approach.

---

#### M2: `_minimum_bet_required` uses static config value, not dynamic strategy output

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py:420-424`
**CWE:** CWE-682 (Incorrect Calculation)
**In PR Scope:** Yes (indirectly -- the PR introduces dynamic progressive bets but does not update this method)
**Actionable:** Yes

```python
def _minimum_bet_required(self) -> float:
    return (
        (self._config.base_bet * 3)
        + self._config.bonus_bet
        + self._config.progressive_bet  # always uses static config value
    )
```

The `_minimum_bet_required` method determines the insufficient-funds stop condition. It always uses `self._config.progressive_bet` (the static configured amount), but after this PR the actual progressive bet may be `0` (if the strategy decides not to bet). This means the session may stop prematurely, declaring "insufficient funds" when the player actually has enough to play (since the dynamic strategy would return 0 for the progressive bet). While this is a conservative error (stops too early rather than allowing negative bankroll), it produces inaccurate simulation results -- a data integrity concern for a statistical simulator.

**Recommendation:** Consider whether `_minimum_bet_required` should account for the possibility that the progressive strategy might return 0. At minimum, document this interaction.

---

### Low Severity

#### L1: No validation that strategy `get_progressive_bet` returns non-negative values

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py:546-547`
**CWE:** CWE-20 (Improper Input Validation)
**In PR Scope:** Yes
**Actionable:** Yes

```python
progressive_bet = self._progressive_strategy.get_progressive_bet(
    progressive_context
)
```

The `ProgressiveStrategy` protocol specifies that `get_progressive_bet` returns a `float`, but there is no runtime validation that the returned value is non-negative. All built-in strategy implementations return either `0.0` or `context.progressive_bet_amount` (which comes from the validated config), so this is safe with current code. However, the `Protocol`-based design explicitly invites custom implementations. A custom strategy returning a negative value would create a negative `progressive_bet`, which would then be contributed to the jackpot pool as a negative contribution (draining it) and produce incorrect `net_result` calculations.

**Recommendation:** Add a guard after calling `get_progressive_bet`: `progressive_bet = max(0.0, progressive_bet)` or raise on negative values.

---

#### L2: `BankrollConditionalProgressiveStrategy` accepts arbitrary `min_session_profit` without validation

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/strategy/progressive.py:164-178`
**CWE:** CWE-20 (Improper Input Validation)
**In PR Scope:** Yes
**Actionable:** Yes

The `BankrollConditionalProgressiveStrategy.__init__` does not validate its parameters (unlike `JackpotThresholdStrategy` which validates `min_jackpot >= 0`). While there is Pydantic validation at the config layer (`min_bankroll_ratio` has `gt=0`), the strategy class itself can be instantiated directly with invalid values. For example, a negative `min_bankroll_ratio` would invert the guard logic. This is a minor concern since normal flow goes through the validated config, but the inconsistency with `JackpotThresholdStrategy` (which does validate) suggests this was an oversight.

**Recommendation:** Add validation in `__init__` that `min_bankroll_ratio` is positive (if provided), consistent with the `JackpotThresholdStrategy` pattern.

---

#### L3: Progressive bet evaluated after hand result is determined -- timing is correct but worth noting

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py:529-547`
**CWE:** N/A (informational)
**In PR Scope:** Yes
**Actionable:** No

The progressive bet decision and contribution happen after `self._engine.play_hand()` returns the hand result. The `ProgressiveContext` includes `self._bankroll.balance` which has not yet been updated with the current hand's main game result. This means the strategy sees the bankroll state from before the current hand's main game outcome, which is the correct real-world behavior (you place your side bet before knowing the hand result). This is noted as informational since the ordering is sound.

---

### No Issues Found In

- **Injection/Deserialization:** No user-supplied strings are evaluated, deserialized, or used in shell commands. The strategy type is constrained by Pydantic `Literal`.
- **Config validation:** `extra="forbid"` on all config models prevents injection of unexpected fields from YAML. The `model_validator` correctly ensures required sub-configs are present.
- **Type safety:** Frozen dataclass with `slots=True` for `ProgressiveContext` prevents attribute injection or mutation.
- **Factory function:** The `create_progressive_strategy` function has proper fallthrough to `raise ValueError` for unknown types, preventing silent misconfiguration.

## Overall Assessment

**Risk Level:** Low

The PR follows established patterns in the codebase (matches the bonus strategy architecture). The security posture is good with proper Pydantic validation, frozen dataclasses, and constrained type literals. The findings are primarily about data integrity edge cases in the simulation domain rather than traditional security vulnerabilities. The most actionable item is M1 (fail-open on zero starting bankroll) which could produce subtly incorrect simulation results.
