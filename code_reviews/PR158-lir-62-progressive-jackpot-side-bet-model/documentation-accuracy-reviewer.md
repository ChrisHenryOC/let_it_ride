# Documentation Accuracy Review for PR #158

## Summary

The PR introduces a progressive jackpot side bet with generally well-written docstrings on all new public classes and factory functions. However, there are several documentation gaps: new fields added to existing dataclasses lack corresponding docstring updates, the `SessionConfig` and `TableSessionConfig` docstrings omit the new `progressive_bet` attribute, the `contribution_rate` docstring on `ProgressivePayoutEntryConfig` claims a "fraction 0-1" constraint that the validator does not enforce, and neither `CLAUDE.md` nor `README.md` has been updated to mention the progressive side bet feature. The `reset_to_seed` behavior is accurately documented in the `ProgressiveJackpot` docstring but under-documented in the `ProgressiveSideBetConfig` attribute description, which omits what happens when `reset_to_seed=False`.

## Findings

### Critical

No critical documentation issues found.

### High

**1. `SessionConfig` docstring missing `progressive_bet` attribute** - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py:148-170` - The `SessionConfig` Attributes docstring (lines 151-161) lists fields through `bonus_bet` but does not document the new `progressive_bet` field declared at line 170. The `stop_on_insufficient_funds` description at line 158-159 still reads "cover the minimum bet (base_bet * 3)" without mentioning that the minimum now includes `progressive_bet`. The actual `_minimum_bet_required()` method at line 402-410 does include `progressive_bet` in the calculation, making the docstring misleading about when insufficient-funds stopping triggers.

```python
# Line 158-159 in docstring (stale):
#   stop_on_insufficient_funds: If True, stop when bankroll cannot
#       cover the minimum bet (base_bet * 3).

# Line 402-410 in actual code (correct):
def _minimum_bet_required(self) -> float:
    return (
        (self._config.base_bet * 3)
        + self._config.bonus_bet
        + self._config.progressive_bet
    )
```

Recommendation: Add `progressive_bet: Fixed progressive side bet amount per hand. 0 to disable.` to the Attributes docstring, and update the `stop_on_insufficient_funds` description to reference `base_bet * 3 + bonus_bet + progressive_bet`.

**2. `TableSessionConfig` docstring missing `progressive_bet` attribute and has stale minimum-bet description** - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py:37-67` - The docstring at lines 42-57 documents attributes through `table_total_rounds` but omits the new `progressive_bet` field at line 67. More importantly, the `stop_on_insufficient_funds` description at line 51-52 explicitly states "base_bet * 3 + bonus_bet" as the minimum, which is now incorrect -- the runtime method `_minimum_bet_required()` at lines 293-299 includes `progressive_bet` in the sum.

```python
# Line 51-52 in docstring (stale):
#   stop_on_insufficient_funds: If True, stop seat when bankroll cannot
#       cover the minimum bet (base_bet * 3 + bonus_bet).

# Line 293-299 in actual code:
def _minimum_bet_required(self) -> float:
    return (
        (self._config.base_bet * 3)
        + self._config.bonus_bet
        + self._config.progressive_bet
    )
```

Recommendation: Add `progressive_bet` to the Attributes section and update the parenthetical to `(base_bet * 3 + bonus_bet + progressive_bet)`.

**3. `validate_session_config` does not accept or validate `progressive_bet`, creating a doc/behavior mismatch** - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py:29-87` - The validation function's signature and docstring include `bonus_bet` but not `progressive_bet`. The minimum bankroll check at line 82 computes `min_bet_required = (base_bet * 3) + bonus_bet` without accounting for `progressive_bet`. However, the runtime `_minimum_bet_required()` does include it. This means a session could pass config validation but immediately stop on its first hand due to insufficient funds when the progressive bet pushes the total cost past the bankroll. The error message at line 86 also omits `progressive_bet`:

```python
# Line 82-87 (config validation - missing progressive_bet):
min_bet_required = (base_bet * 3) + bonus_bet
if starting_bankroll < min_bet_required:
    raise ValueError(
        f"starting_bankroll ({starting_bankroll}) must be at least "
        f"base_bet * 3 + bonus_bet ({min_bet_required})"
    )
```

Recommendation: Add `progressive_bet` as a parameter to `validate_session_config`, include it in the minimum bankroll check, and update the error message. Both `SessionConfig.__post_init__` and `TableSessionConfig.__post_init__` should pass `progressive_bet` through to the validator.

**4. Confusing coexistence of `ProgressiveJackpotConfig` and `ProgressiveSideBetConfig` with no cross-referencing documentation** - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/config/models.py:920-977` - The pre-existing `ProgressiveJackpotConfig` (line 920) and the new `ProgressiveSideBetConfig` (line 952) both model progressive jackpot configuration but for different game mechanics. `ProgressiveJackpotConfig` is for a 3-card bonus progressive (triggered by `mini_royal`), while `ProgressiveSideBetConfig` is for a 5-card side bet progressive with a full paytable. Neither docstring references the other, and a developer encountering both would not understand their relationship without reading the code paths that consume them. The field names overlap (`starting_jackpot`, `contribution_rate`) with different defaults (0.15 vs 0.71 for `contribution_rate`), compounding the confusion.

Recommendation: Add a "See Also" or "Note" line to each docstring explicitly referencing the other class and explaining which game mechanic it serves. For example, `ProgressiveSideBetConfig` should note: "Not to be confused with ProgressiveJackpotConfig, which models the 3-card bonus progressive triggered by mini royal."

### Medium

**5. `GameHandResult` docstring missing `progressive_bet` and `progressive_payout` attributes** - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/game_engine.py:25-58` - The Attributes docstring (lines 28-42) enumerates all fields through `net_result` but does not document the two new fields `progressive_bet` (line 57) and `progressive_payout` (line 58). These are defaulted to 0.0 so they do not break construction, but any consumer reading the docstring to understand the data model will not know these fields exist.

Recommendation: Add to the Attributes section:
- `progressive_bet: Progressive side bet amount (0 if not playing progressive).`
- `progressive_payout: Payout from progressive side bet (0 if no qualifying hand).`

**6. `PlayerSeat` docstring missing `progressive_bet` and `progressive_payout` attributes** - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/table.py:25-56` - Same gap as `GameHandResult`. The Attributes docstring (lines 28-41) ends at `net_result` and does not mention `progressive_bet` (line 55) or `progressive_payout` (line 56).

Recommendation: Add the same two attribute descriptions as for `GameHandResult`.

**7. `SessionResult` docstring field ordering does not match field declaration ordering** - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py:186-221` - The docstring at line 198 lists `total_progressive_wagered` immediately after `total_bonus_wagered`, which is the logical grouping. However, the actual field declaration at line 219 places `total_progressive_wagered` after `max_drawdown_pct` (line 218) and before `table_session_id` (line 220), separated from `total_bonus_wagered` (line 215) by three fields (`peak_bankroll`, `max_drawdown`, `max_drawdown_pct`). This inconsistency between docstring order and declaration order is confusing. The field was placed at the end to avoid breaking positional construction, but the docstring presents them as logically adjacent.

Recommendation: Either reorder the docstring to match the actual declaration order, or add a brief comment at the field declaration explaining why it is positioned at the end (backward compatibility with positional construction).

**8. `ProgressivePayoutEntryConfig.value` docstring claims "fraction 0-1 for percentage" but the validator allows any non-negative value** - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/config/models.py:938-949` - The docstring at line 943 says `value: The payout value (dollars for fixed, fraction 0-1 for percentage).` However, the actual field constraint at line 949 is `Field(ge=0)` with no upper bound. A user could set `type="jackpot_percentage"` with `value=5.0`, which contradicts the documented "fraction 0-1" range and would pay out 500% of the pool. Similarly, the `ProgressivePayout` dataclass docstring at `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/progressive_jackpot.py:27` says "0-1 fraction for percentage" but has no validation.

Recommendation: Either add a Pydantic `model_validator` that enforces `value <= 1.0` when `type == "jackpot_percentage"`, or update the docstring to say "non-negative float for percentage (values > 1.0 pay more than the full pool)" to accurately reflect the actual behavior.

**9. `CLAUDE.md` does not mention the progressive side bet configuration section** - `/Users/chrishenry/source/let_it_ride/CLAUDE.md` - The Configuration section documents YAML config sections including `bonus_strategy` but has no mention of the new `progressive` top-level configuration section. The key abstractions list also lacks any reference to `ProgressiveJackpot`. Since `CLAUDE.md` serves as the primary onboarding document for AI-assisted development, this omission means future sessions will not know about the progressive feature.

Recommendation: Add `progressive` to the Configuration bullet list with a description like: `progressive: enabled, bet_amount, seed_amount, starting_jackpot, contribution_rate, reset_to_seed, custom paytable`. Also add `ProgressiveJackpot` to the key abstractions with a brief description.

**10. `README.md` does not mention progressive jackpot** - `/Users/chrishenry/source/let_it_ride/README.md` - No mention of the progressive jackpot feature or the new `progressive_jackpot.yaml` example config. The integration test at `tests/integration/test_sample_configs.py:255-258` checks that `README.md` mentions all config files in the `configs/examples/` directory, so the new `progressive_jackpot.yaml` will likely cause that test to fail.

Recommendation: Add a mention of the progressive jackpot feature and the `progressive_jackpot.yaml` config to `README.md`.

**11. `ProgressiveSideBetConfig.reset_to_seed` docstring is incomplete** - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/config/models.py:965` - The attribute description says "If True, reset pool to seed_amount after jackpot hit" but does not describe the `False` behavior. The actual code at `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/progressive_jackpot.py:128-130` shows that when `reset_to_seed=False` and a 100% jackpot hit occurs, the pool is set to 0.0 (since `pool -= pool * 1.0` leaves zero). This is a non-obvious behavior that users should understand before configuring.

```python
# progressive_jackpot.py:124-130
payout_amount = self._pool * payout_rule.value
self._pool -= payout_amount  # pool goes to 0 for 100% hit
if payout_rule.value >= 1.0 and self._reset_to_seed:
    self._pool = self._seed_amount  # only if reset_to_seed=True
```

Recommendation: Update to: "If True, reset pool to seed_amount after a full jackpot hit (100%). If False, pool remains at 0 after full payout."

**12. `ProgressiveJackpot` class docstring does not explain partial-hit pool behavior** - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/progressive_jackpot.py:50-57` - The docstring says "A full jackpot hit (100%) resets the pool to the seed amount" but does not state what happens for partial percentage hits (e.g., 10% straight flush). A reader must infer from the code that the percentage is deducted from the pool without resetting. Since this is the core domain class, the two distinct behaviors (fixed: no pool change; percentage: deduct from pool, optionally reset) should be explicitly stated.

Recommendation: Expand the docstring to: "Fixed-dollar payouts do not affect the pool. Percentage payouts deduct the paid fraction from the pool. A full jackpot hit (value >= 1.0) resets the pool to the seed amount if reset_to_seed is True; otherwise the pool drops to zero."

### Low

**13. YAML config comment uses ambiguous term "section"** - `/Users/chrishenry/source/let_it_ride/configs/examples/progressive_jackpot.yaml:63` - The comment says "Standard progressive paytable (used when paytable section is omitted)" -- the word "section" might lead users to think it refers to a top-level YAML section rather than the nested `paytable` key under `progressive:`. The comment at line 82 clarifies with "Omit paytable to use the standard progressive paytable above" which is clearer.

**14. `_SeatState` new field `total_progressive_wagered` is undocumented** - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py:136-156` - The private `_SeatState` class had its `__slots__` and `__init__` updated to include `total_progressive_wagered` without any docstring mention. Minor concern given private scope.

### Positive

- The module-level docstring in `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/progressive_jackpot.py:1-11` is excellent, clearly explaining the module purpose, differentiating from the 3-card bonus, and listing key types.
- The `ProgressiveSideBetConfig` docstring at `/Users/chrishenry/source/let_it_ride/src/let_it_ride/config/models.py:952-966` clearly distinguishes the 5-card progressive from the 3-card bonus and documents all attributes with types and semantics.
- The YAML example config at `/Users/chrishenry/source/let_it_ride/configs/examples/progressive_jackpot.yaml` includes thorough header comments explaining the game mechanic, contribution rate math, and expected behavior. The inline comments for the paytable customization section are helpful.
- Factory functions `standard_progressive_paytable()` and `create_progressive_jackpot()` have complete Args/Returns docstrings that accurately match their signatures and behavior.
- The `Session.__init__` docstring at `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py:333-344` accurately documents the new `progressive_jackpot` parameter including the important note about per-session isolation.
- The `contribute()` docstring accurately describes the parameter and matches the implementation.
- The `evaluate_payout()` docstring at `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/progressive_jackpot.py:103-115` accurately describes the return value and the reset behavior for 100% hits with `reset_to_seed=True`.
