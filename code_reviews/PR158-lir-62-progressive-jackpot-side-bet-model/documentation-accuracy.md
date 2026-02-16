# Documentation Accuracy Review - PR #158

## Summary

The PR introduces a well-documented progressive jackpot side bet model with thorough docstrings on all new public classes and functions. The module-level docstring, class docstrings, and YAML config comments are clear and internally consistent. There are several documentation gaps where new fields were added to existing dataclasses without updating the corresponding Attributes sections, and the coexistence of the old `ProgressiveJackpotConfig` alongside the new `ProgressiveSideBetConfig` creates potential confusion.

## Findings

### Critical

No critical documentation issues found.

### High

1. **Duplicate/confusing progressive config classes -- no clarifying documentation**
   - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/config/models.py:920-935` -- The pre-existing `ProgressiveJackpotConfig` class (used by `BonusPaytableConfig.progressive` at line 993) remains alongside the new `ProgressiveSideBetConfig` at line 952. These two classes serve different purposes (3-card bonus progressive vs. 5-card side bet progressive) but their names and overlapping fields (`starting_jackpot`, `contribution_rate`) make it unclear how they relate. Neither class's docstring references the other or explains when to use which. A developer encountering both for the first time would be confused about whether they conflict, overlap, or are independent.

2. **`SessionConfig` docstring missing `progressive_bet` attribute**
   - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py:148-161` -- The `SessionConfig` Attributes docstring lists fields through `bonus_bet` but does not document the new `progressive_bet` field added at line 170. The docstring still ends with "bonus_bet: Fixed bonus bet amount per hand. 0 to disable bonus." and omits the progressive bet entirely.

3. **`TableSessionConfig` docstring missing `progressive_bet` attribute**
   - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py:40-57` -- The `TableSessionConfig` Attributes docstring documents through `table_total_rounds` but does not mention the new `progressive_bet` field added at line 67. The `stop_on_insufficient_funds` description still references "base_bet * 3 + bonus_bet" without mentioning progressive_bet, which is now also included in the minimum bet calculation (see line 293-299).

### Medium

1. **`GameHandResult` docstring missing `progressive_bet` and `progressive_payout` attributes**
   - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/game_engine.py:29-42` -- The Attributes section of `GameHandResult` lists fields through `net_result` but does not document the two new fields `progressive_bet` (line 57) and `progressive_payout` (line 58).

2. **`PlayerSeat` docstring missing `progressive_bet` and `progressive_payout` attributes**
   - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/table.py:30-41` -- Same gap as `GameHandResult`. The Attributes docstring ends at `net_result` and does not document the new `progressive_bet` (line 55) and `progressive_payout` (line 56) fields.

3. **`SessionResult` field ordering inconsistency with docstring**
   - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py:186-220` -- The `SessionResult` docstring lists `total_progressive_wagered` right after `total_bonus_wagered` (line 198), matching logical ordering. However, the actual field declaration at line 219 places `total_progressive_wagered` after `max_drawdown_pct`, far from `total_bonus_wagered` (line 214). This mismatch between docstring order and field declaration order is confusing. The field was likely placed at the end to maintain backward compatibility with positional construction, but a comment explaining this would help.

4. **`ProgressivePayoutEntryConfig.value` allows values greater than 1.0 for `jackpot_percentage` type**
   - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/config/models.py:949` -- The docstring says "fraction 0-1 for percentage" but the validator is `Field(ge=0)` with no upper bound. A user could set `type="jackpot_percentage"` with `value=5.0`, which contradicts the documented "fraction 0-1" range. Either the validator should enforce `le=1.0` for percentage types or the docstring should note that values above 1.0 are technically allowed.

5. **CLAUDE.md and README.md do not mention the progressive side bet**
   - `/Users/chrishenry/source/let_it_ride/CLAUDE.md` -- The Configuration section documents `bonus_strategy` but has no mention of the new `progressive` configuration section. The key abstractions list also lacks any reference to progressive jackpot.
   - `/Users/chrishenry/source/let_it_ride/README.md` -- No mention of progressive jackpot functionality. The test at `tests/integration/test_sample_configs.py:270-276` checks that README mentions all config files; the new `progressive_jackpot.yaml` will likely fail this test if README is not updated.

### Low

1. **YAML config comment says "Omit paytable section" but field name is just "paytable"**
   - `/Users/chrishenry/source/let_it_ride/configs/examples/progressive_jackpot.yaml:82` -- The comment says "Omit paytable to use the standard progressive paytable above" which is clear, but the heading comment at line 63 says "Standard progressive paytable (used when paytable section is omitted)" -- the word "section" might lead users to think it is a top-level YAML section rather than a nested key under `progressive:`.

2. **`ProgressiveJackpot` class docstring could clarify partial-hit behavior more precisely**
   - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/progressive_jackpot.py:284-291` -- The docstring says "A full jackpot hit (100%) resets the pool to the seed amount" but does not explicitly state what happens for partial hits (10% straight flush). The code deducts the percentage from the pool without resetting, but a reader must infer this from absence of mention.

3. **`_SeatState` new field `total_progressive_wagered` is undocumented**
   - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py:136-156` -- `_SeatState` is a private class, but its `__slots__` and `__init__` were updated to include `total_progressive_wagered` without any docstring mention. This is a minor concern given the private scope.

### Positive

1. **Excellent module-level docstring** in `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/progressive_jackpot.py:1-11` -- Clearly explains the module purpose, differentiates from the 3-card bonus, and lists key types. This is a good pattern for discoverability.

2. **Thorough `ProgressiveSideBetConfig` docstring** at `/Users/chrishenry/source/let_it_ride/src/let_it_ride/config/models.py:952-966` -- Clearly distinguishes the 5-card progressive from the 3-card bonus, documents all attributes with types and semantics, and matches the actual field definitions accurately.

3. **Well-documented YAML example** at `/Users/chrishenry/source/let_it_ride/configs/examples/progressive_jackpot.yaml` -- The header comments explain the game mechanic, contribution rate math, and expected behavior. The inline comments for the paytable section are helpful for customization.

4. **Consistent factory function documentation** -- Both `standard_progressive_paytable()` and `create_progressive_jackpot()` in the progressive_jackpot module have complete Args/Returns docstrings that match their actual signatures and behavior.

5. **Comprehensive test coverage with descriptive docstrings** -- All test classes and methods in `tests/unit/core/test_progressive_jackpot.py` and `tests/unit/config/test_progressive_config.py` have clear, specific docstrings explaining exactly what is being verified.
