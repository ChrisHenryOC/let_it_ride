# Code Quality Review - PR #158

## Summary

This PR adds a well-structured progressive jackpot side bet model with clean separation between configuration (Pydantic), domain logic (dataclasses), and simulation integration. The core module (`progressive_jackpot.py`) is particularly well-written with good use of `__slots__`, frozen dataclasses, and clear documentation. However, there are a few issues around missing error handling, code duplication in result reconstruction, a shared-mutable-state concern in multi-seat play, and a naming collision with the pre-existing `ProgressiveJackpotConfig`.

## Findings

### Critical

**1. Shared mutable jackpot across multi-seat table contributes per-seat, inflating pool incorrectly**

In `TableSession.play_round()`, the single `ProgressiveJackpot` instance is shared across all seats in a round. Each seat calls `contribute()` and `evaluate_payout()` sequentially, meaning seat 2's payout is evaluated against a pool that already includes seat 1's contribution from the same round, and the pool mutates between seats. In a real casino, each seat's $1 bet contributes to the pool, but payouts for a single round should arguably be evaluated against the pool state at the start of that round (before any contributions or payouts from the current round).

With 6 seats, the pool receives 6 contributions per round instead of 1, which dramatically accelerates pool growth and creates ordering-dependent payouts. If seat 1 hits a royal flush and resets the pool, seat 3 hitting a straight flush would only get 10% of the seed amount rather than the accumulated pool.

- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py:529-531`

### High

**2. Missing error handling for invalid hand rank names in custom paytable**

`create_progressive_jackpot()` uses `FiveCardHandRank[hand_name.upper()]` which will raise a raw `KeyError` if the config contains an invalid hand rank name. This should be caught and re-raised as a `ValueError` with a descriptive message listing valid hand ranks.

```python
# progressive_jackpot.py:190
hand_rank = FiveCardHandRank[hand_name.upper()]
```

- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/progressive_jackpot.py:190`

**3. No validation that `jackpot_percentage` values are between 0 and 1**

The `ProgressivePayoutEntryConfig` model constrains `value` to `ge=0` but does not cap it at `le=1.0` for `jackpot_percentage` type entries. A value of 2.0 with type `jackpot_percentage` would pay 200% of the pool and drive it negative. Cross-field validation (e.g., a Pydantic `model_validator`) should enforce that percentage values fall within [0, 1].

- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/config/models.py:948-949`

**4. Two progressive config classes with overlapping purposes create confusion**

The pre-existing `ProgressiveJackpotConfig` (line 920) and the new `ProgressiveSideBetConfig` (line 952) both model progressive jackpot configuration but with different fields and semantics. `ProgressiveJackpotConfig` has `trigger: Literal["mini_royal"]` and `reset_amount`, while `ProgressiveSideBetConfig` has `reset_to_seed`, `paytable`, etc. This creates naming confusion and maintenance risk. The relationship between these two models should be clarified -- is the old one deprecated?

- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/config/models.py:920-936` (old)
- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/config/models.py:952-977` (new)

### Medium

**5. Verbose result reconstruction duplicated in two places**

Both `Session.play_hand()` and `TableSession.play_round()` manually reconstruct frozen dataclass instances field-by-field to add progressive fields. This is a DRY violation and is fragile -- if `GameHandResult` or `PlayerSeat` gains a new field, both locations must be updated. Consider adding a helper method like `with_progressive()` on `GameHandResult` and `PlayerSeat`, or using `dataclasses.replace()` since these are dataclasses.

```python
# session.py:527-543 -- 17 lines of field-by-field copy
result = GameHandResult(
    hand_id=result.hand_id,
    player_cards=result.player_cards,
    ...
)
```

- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py:527-543`
- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py:537-552`

**6. `ProgressivePaytable` dataclass missing `slots=True`**

`ProgressivePayout` uses `@dataclass(frozen=True, slots=True)` but `ProgressivePaytable` only uses `@dataclass(frozen=True)`. For consistency and the stated project convention of using `__slots__` on frequently instantiated classes, `slots=True` should be added.

- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/progressive_jackpot.py:37`

**7. `GameHandResult` docstring not updated for new fields**

The class docstring for `GameHandResult` lists all attributes but does not include the new `progressive_bet` and `progressive_payout` fields. The same applies to `PlayerSeat` in `table.py`.

- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/game_engine.py:26-42`
- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/table.py:52-53`

**8. `SessionResult.total_progressive_wagered` field ordering breaks positional construction**

The new `total_progressive_wagered` field with a default value is inserted between `max_drawdown_pct` and `table_session_id` (which also has a default). This works but positions a financial tracking field away from its related field `total_bonus_wagered`. For readability and logical grouping, it should be placed adjacent to `total_bonus_wagered`.

- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py:216`

### Low

**9. `contribute()` does not validate negative bet amounts**

The `contribute()` method accepts any float, including negative values, which would decrease the pool. A guard clause or assertion would prevent accidental misuse.

- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/progressive_jackpot.py:95-101`

**10. Magic numbers for bonus bet bounds**

In `session.py:493-494`, the values `min_bonus_bet=1.0` and `max_bonus_bet=100.0` are hardcoded magic numbers. This is pre-existing but worth noting as context for the progressive bet integration.

- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py:493-494`

**11. Missing test for invalid hand rank name in custom paytable**

There is no test covering the error case where `create_progressive_jackpot` receives an invalid hand rank string in the custom paytable config. This is related to finding #2.

### Positive

- The core `ProgressiveJackpot` class is well-designed with clear single responsibility, `__slots__`, and clean encapsulation of pool mutation logic.
- Excellent use of `frozen=True` dataclasses for immutable value types (`ProgressivePayout`, `ProgressivePaytable`).
- `TYPE_CHECKING` guard for the config import avoids circular dependency cleanly.
- The factory function pattern (`create_progressive_jackpot`, `standard_progressive_paytable`) provides good separation between config parsing and domain construction.
- Comprehensive test coverage with well-organized test classes covering contributions, fixed payouts, percentage payouts, non-qualifying hands, reset mechanics, and factory functions.
- The `ProgressiveSideBetConfig` Pydantic model uses `extra="forbid"` and `Annotated` field constraints appropriately.
- Per-session jackpot instantiation in the controller and parallel modules is correctly done to avoid shared state across sessions.
- The YAML example config includes thorough inline documentation.
