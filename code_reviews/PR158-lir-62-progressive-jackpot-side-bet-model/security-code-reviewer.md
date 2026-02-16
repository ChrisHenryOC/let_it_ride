# Security Code Review for PR #158

## Summary

This PR adds a progressive jackpot side bet model with configuration via Pydantic, domain logic in dataclasses, and integration into session/table-session simulation loops. The code avoids classic Python security pitfalls (no `eval`, `exec`, `pickle`, `subprocess`, or dynamic code execution). The primary security-relevant findings concern input validation gaps that can corrupt simulation integrity: an unhandled `KeyError` on user-supplied hand rank names, a missing upper-bound constraint on `jackpot_percentage` values that can drive the pool negative, a `validate_session_config` bypass that omits the progressive bet from minimum bankroll checks, and lack of negative-value guards on the `contribute()` method.

## Findings

### Critical

**1. Unhandled `KeyError` from user-supplied hand rank names in custom paytable (CWE-20: Improper Input Validation)**

`/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/progressive_jackpot.py:190` (line in diff context)

When a user provides a custom paytable in YAML config, hand rank keys are free-form strings (`dict[str, ProgressivePayoutEntryConfig]`). The factory function performs a raw enum lookup without error handling:

```python
hand_rank = FiveCardHandRank[hand_name.upper()]
```

If the user supplies a typo or invalid rank name (e.g., `"ROYAL_FLUSHH"`, `"FIVE_OF_A_KIND"`), this raises an unhandled `KeyError` that propagates as an opaque traceback rather than a clear validation error. Because this occurs at jackpot construction time (called from `get_progressive_jackpot()` in `utils.py`), it crashes during session setup with no indication of which key was invalid or what valid keys exist.

The Pydantic model at `/Users/chrishenry/source/let_it_ride/src/let_it_ride/config/models.py:696` (the `paytable` field) does not constrain the dictionary keys to valid `FiveCardHandRank` member names -- it accepts any string. This means Pydantic validation passes, but the application crashes later during domain object construction.

Recommendation: Wrap the lookup in a `try/except KeyError` and re-raise as `ValueError` listing valid hand rank names, or add a Pydantic `model_validator` on `ProgressiveSideBetConfig` that validates paytable keys against `FiveCardHandRank` member names at config parse time.

### High

**2. Missing upper-bound validation on `jackpot_percentage` value allows negative pool state (CWE-20: Improper Input Validation)**

`/Users/chrishenry/source/let_it_ride/src/let_it_ride/config/models.py:949` (new code in diff)

The `ProgressivePayoutEntryConfig.value` field uses `Field(ge=0)` with no upper bound. The docstring states "fraction 0-1 for percentage" but the validator does not enforce this for `jackpot_percentage` type entries:

```python
class ProgressivePayoutEntryConfig(BaseModel):
    type: Literal["fixed", "jackpot_percentage"]
    value: Annotated[float, Field(ge=0)]  # No upper bound for percentage type
```

A user could configure `type="jackpot_percentage"` with `value=5.0`. In `evaluate_payout()` at `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/progressive_jackpot.py:125-126`:

```python
payout_amount = self._pool * payout_rule.value  # 5.0 * 10000 = 50000
self._pool -= payout_amount                     # 10000 - 50000 = -40000
```

The pool goes to -40,000. Subsequent percentage payouts would then produce negative values (paying money back to the house from the player's perspective), silently corrupting all downstream simulation results including bankroll tracking, session outcomes, and statistical analysis. Since the pool value check at line 129 (`if payout_rule.value >= 1.0`) would trigger a reset to seed, but only after the invalid payout of 50,000 has already been returned, the damage to the current hand's result persists.

Recommendation: Add a Pydantic `model_validator` (mode `"after"`) on `ProgressivePayoutEntryConfig` that enforces `0 <= value <= 1.0` when `type == "jackpot_percentage"`.

**3. `validate_session_config` does not include `progressive_bet` in minimum bankroll check (CWE-20: Improper Input Validation)**

`/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py:82`

The shared validation function computes:

```python
min_bet_required = (base_bet * 3) + bonus_bet
```

But the runtime `_minimum_bet_required()` method (updated in this PR at line 402-410) correctly includes `progressive_bet`:

```python
return (self._config.base_bet * 3) + self._config.bonus_bet + self._config.progressive_bet
```

This means a config with `starting_bankroll=16.0`, `base_bet=5.0`, `bonus_bet=0.0`, `progressive_bet=2.0` would pass validation (min required = 15.0) but the session would immediately stop on the first hand because `_minimum_bet_required()` returns 17.0 > 16.0. The `validate_session_config` function signature does not even accept a `progressive_bet` parameter, so it was not updated in this PR.

This is a validation bypass: users get no error at config load time for an unplayable configuration.

Recommendation: Add `progressive_bet` parameter to `validate_session_config()` and include it in the `min_bet_required` calculation.

**4. Shared mutable jackpot state across seats in multi-seat mode produces order-dependent simulation bias (CWE-362 analog: Ordering-Dependent State Mutation)**

`/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py:528-531` (new code in diff)

In `TableSession.play_round()`, a single `ProgressiveJackpot` instance is shared across all seats. Each seat sequentially calls `contribute()` then `evaluate_payout()` within the same round:

```python
for seat_result in result.seat_results:
    # ...
    if self._progressive_jackpot is not None and progressive_bet > 0:
        self._progressive_jackpot.contribute(progressive_bet)
        prog_payout = self._progressive_jackpot.evaluate_payout(
            seat_result.final_hand_rank
        )
```

This causes two integrity issues:
- Seat 2's payout is evaluated against a pool that already includes seat 1's contribution from the same round, inflating payouts.
- If seat 1 hits a royal flush and resets the pool, seat 2 hitting a straight flush receives only 10% of the seed amount instead of 10% of the pre-round accumulated pool.

While not a traditional concurrent race condition, the shared mutable state within a sequential loop produces analogous ordering-dependent behavior. Simulation results become dependent on seat iteration order, which undermines statistical validity. For a tool designed to produce accurate simulation statistics, this is a simulation integrity violation.

Recommendation: Snapshot the pool value at round start. Process all contributions first, then evaluate all payouts against the snapshot (or the pre-payout pool). Apply pool mutations after all seat evaluations.

### Medium

**5. No validation that `progressive_bet` is non-negative in `SessionConfig`/`TableSessionConfig`**

`/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py:170` and `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py:67`

The `progressive_bet` field is added as `float = 0.0` with no validation in `__post_init__`. The existing `validate_session_config` validates `bonus_bet >= 0` but is never called with `progressive_bet` at all. A negative `progressive_bet` would reduce `_minimum_bet_required()`, potentially allowing play with insufficient bankroll, and would cause `contribute()` to decrease the pool (since `contribution_rate * negative_bet` is negative).

While the Pydantic model `ProgressiveSideBetConfig.bet_amount` uses `Field(gt=0)`, the `SessionConfig` dataclass is constructed separately and does not inherit those constraints. A code path that constructs `SessionConfig` directly (e.g., in tests or future integrations) could pass a negative value.

**6. `contribute()` accepts negative bet amounts without validation (CWE-20)**

`/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/progressive_jackpot.py:95-101`

```python
def contribute(self, bet_amount: float) -> None:
    self._pool += self._contribution_rate * bet_amount
```

No guard against negative `bet_amount`. If called with a negative value (e.g., due to upstream bug or future misuse), it would silently drain the pool. Adding an assertion or raising `ValueError` for negative amounts would provide defense-in-depth.

**7. Float arithmetic accumulation drift in jackpot pool (CWE-681: Incorrect Conversion between Numeric Types)**

`/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/progressive_jackpot.py:101`

The pool accumulates via `self._pool += self._contribution_rate * bet_amount` using IEEE 754 float64. For 200-hand sessions this is negligible (max ~0.001 cent drift). However, if session sizes grow or multi-seat tables run 6 contributions per round for 200 rounds (1,200 accumulations), drift could affect payout calculations at the margin. This is acceptable at current scale but worth documenting as a known limitation.

### Low

**8. No validation that `starting_jackpot >= seed_amount`**

`/Users/chrishenry/source/let_it_ride/src/let_it_ride/config/models.py:974`

A user could configure `starting_jackpot=100.0` with `seed_amount=50000.0`. After a royal flush hit, the pool resets to 50,000 -- far above the starting value. While not technically a bug, this is a potentially confusing configuration that could produce misleading simulation results without user awareness. A Pydantic `model_validator` warning (or at least a docstring note) would help.

**9. Fixed payouts not sourced from pool -- unlimited payout potential**

`/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/progressive_jackpot.py:121-122`

Fixed payouts (e.g., $500 for Four of a Kind) are returned without any pool deduction. In a realistic progressive model, fixed payouts come from the house, not the pool. This is likely correct modeling, but there is no documentation clarifying this design decision. If a user configures very large fixed payouts in a custom paytable, the simulation has no mechanism to bound them.

## Positive Observations

- The code correctly avoids all classic Python security anti-patterns: no `eval()`, `exec()`, `pickle`, `subprocess`, or dynamic code execution anywhere in the new code.
- YAML config is loaded through Pydantic with `extra="forbid"`, which prevents unexpected field injection and provides safe, typed deserialization.
- `ProgressiveJackpot` uses `__slots__`, which prevents dynamic attribute injection on the mutable pool manager class.
- Per-session jackpot isolation is correctly implemented: each session gets a fresh `ProgressiveJackpot` instance via `get_progressive_jackpot()`, preventing state leakage across sessions or parallel workers.
- Immutable data structures (`frozen=True` dataclasses) are used for `ProgressivePayout` and `ProgressivePaytable`, preventing accidental mutation of paytable rules.
- The progressive jackpot evaluation is post-hand and does not influence RNG state (deck shuffling or card dealing), preserving simulation randomness integrity.
- The `TYPE_CHECKING` guard for the config import avoids circular dependency cleanly.
