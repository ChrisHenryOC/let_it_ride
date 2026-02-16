# Security Review - PR #158

## Summary

This PR adds a progressive jackpot side bet model to the Let It Ride simulator. The code is well-structured with strong input validation via Pydantic models (`extra="forbid"`, constrained fields). There are no injection, deserialization, or authentication concerns -- this is a local simulation tool. The primary findings relate to financial calculation integrity: floating-point accumulation drift in the jackpot pool, a shared mutable jackpot state across seats in multi-seat mode that can produce order-dependent simulation results, and missing validation on custom paytable hand rank names that could cause unhandled exceptions.

## Findings

### Critical

None.

### High

**H1: Shared mutable jackpot state across seats introduces order-dependent simulation bias**
- Files: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py:528-531`
- In multi-seat table sessions, a single `ProgressiveJackpot` instance is shared across all seats at the table. Each seat's `contribute()` and `evaluate_payout()` calls mutate the same pool within a single round. This means:
  1. Seat 1's contribution inflates the pool before Seat 2's payout is evaluated.
  2. If Seat 1 hits a royal flush, the pool resets before Seat 2's hand is evaluated, dramatically changing Seat 2's potential payout.
  3. Simulation results depend on seat iteration order, which is a form of simulation integrity issue.
- In a real casino, all progressive bets at a table reference the same pool, but payouts for a single round should be evaluated against the pool state at the start of the round (before any payouts in that round are applied). The current implementation does not snapshot the pool before processing seats.
- CWE-362 (Race Condition / Concurrent Execution) -- while not multi-threaded, the shared mutable state within a loop produces analogous ordering effects.

### Medium

**M1: Floating-point accumulation drift in jackpot pool over long simulations**
- File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/progressive_jackpot.py:101`
- The pool uses `float` and accumulates via `self._pool += self._contribution_rate * bet_amount` over potentially millions of hands. Standard IEEE 754 double-precision accumulation will introduce drift. For a simulation targeting 100,000 sessions x 200 hands, individual session pools are short-lived (200 contributions max), so drift is minimal per session. However, if session sizes grow or if the pool were ever shared across sessions, this could become significant.
- For a financial simulation, `Decimal` or periodic rounding would provide more reliable results, though this is a low practical risk at current scale.
- CWE-681 (Incorrect Conversion between Numeric Types).

**M2: Unvalidated hand rank names in custom paytable cause unhandled KeyError**
- File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/progressive_jackpot.py:190`
- `FiveCardHandRank[hand_name.upper()]` will raise a `KeyError` if a user provides an invalid hand rank name in their YAML config (e.g., `"ROYAL_FLUSHH"` or `"FIVE_OF_A_KIND"`). While Pydantic validates the structure of each entry, the paytable keys are `dict[str, ProgressivePayoutEntryConfig]` with free-form string keys -- no enum validation is performed at the config layer.
- This results in an unhandled exception at runtime rather than a clear validation error at config load time.
- CWE-20 (Improper Input Validation).

**M3: No upper bound on `jackpot_percentage` value in `ProgressivePayoutEntryConfig`**
- File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/config/models.py:949`
- The `value` field for `ProgressivePayoutEntryConfig` uses `Field(ge=0)` with no upper bound. A user could configure `type="jackpot_percentage"` with `value=5.0` (500%), which would result in a payout of 5x the pool and drive the pool negative. The `ProgressiveJackpot.evaluate_payout()` method at line 125-126 computes `payout_amount = self._pool * payout_rule.value` and then `self._pool -= payout_amount`, which would leave the pool at a negative value.
- A negative pool would then cause subsequent percentage payouts to be negative (paying money back), corrupting simulation results.
- CWE-20 (Improper Input Validation).

### Low

**L1: Fixed payouts not deducted from pool -- unlimited payout source**
- File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/progressive_jackpot.py:121-122`
- Fixed payouts (e.g., $500 for Four of a Kind) are returned without any pool deduction. In a real progressive system, fixed payouts typically come from the house, not the pool, so this is likely correct modeling. However, there is no documentation clarifying this design decision, which could lead to confusion about where the money comes from in simulation accounting.

**L2: No validation that `starting_jackpot >= seed_amount`**
- File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/config/models.py:974`
- A user could configure `starting_jackpot=100.0` with `seed_amount=10000.0`. After a royal flush, the pool would reset to 10,000 (seed) which is higher than where it started. While not technically a bug, it represents a potentially confusing configuration that could skew simulation results without the user realizing it.

**L3: Progressive bet not included in `bets_at_risk` tracking**
- File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py:554`
- The `total_wagered` accumulates `result.bets_at_risk` (which includes main game bets), and `total_bonus_wagered` tracks bonus bets separately. The progressive bet is tracked in `total_progressive_wagered` but is not included in `bets_at_risk` on the `GameHandResult`. This is consistent with how bonus bets are handled, but users analyzing total money at risk per hand should be aware that the progressive bet is excluded from `bets_at_risk`.

### Positive

- **Strong input validation**: Pydantic models use `extra="forbid"`, preventing unexpected config fields. Numeric fields have appropriate constraints (`gt=0`, `le=1.0` for contribution_rate). The `type` field is constrained to a `Literal["fixed", "jackpot_percentage"]` union.
- **Per-session jackpot isolation**: Each session creates a fresh `ProgressiveJackpot` instance via `get_progressive_jackpot()`, preventing state leakage across sessions. This is explicitly noted in comments ("Progressive jackpot needs fresh state per session").
- **No injection surfaces**: The code does not use `eval()`, `exec()`, `subprocess`, `pickle`, or any dynamic code execution. YAML config is loaded through Pydantic which provides safe deserialization.
- **Immutable data structures**: `ProgressivePayout` and `ProgressivePaytable` use `frozen=True` dataclasses, preventing accidental mutation of paytable rules.
- **No RNG impact**: The progressive jackpot is evaluated post-hand and does not influence deck shuffling or card dealing, preserving RNG integrity.
- **Slots usage**: `ProgressiveJackpot` uses `__slots__`, preventing dynamic attribute injection on the mutable pool manager.
