# Code Quality Review for PR #158

## Summary

This PR introduces a progressive jackpot side bet with generally clean architecture: a well-encapsulated `ProgressiveJackpot` class with `__slots__`, frozen dataclass value types, and proper factory separation. However, there are several code quality issues that should be addressed before merge: a DRY violation where frozen dataclass reconstruction is duplicated across two files, a shared mutable state design flaw in multi-seat mode that produces order-dependent results, missing input validation in `validate_session_config`, an unhandled `KeyError` on invalid hand rank names, and inconsistent use of `slots=True` on dataclasses.

## Findings

### Critical

**1. Shared mutable jackpot state in multi-seat mode produces order-dependent simulation results**

In `TableSession.play_round()`, the single `ProgressiveJackpot` instance is mutated sequentially per seat within a round. Seat 1's `contribute()` inflates the pool before seat 2's `evaluate_payout()` runs, and if seat 1 hits a royal flush and resets the pool, seat 3's straight flush payout drops to 10% of the seed rather than 10% of the accumulated pool. This means simulation results depend on seat iteration order, which is a correctness defect that invalidates statistical analysis of multi-seat progressive games.

- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py:528-531`

Recommendation: Snapshot the pool value at the start of each round. Process all contributions first, then evaluate all payouts against the snapshotted pool value.

**2. `validate_session_config` does not include `progressive_bet` in minimum bankroll check**

The validation function at line 82 computes `min_bet_required = (base_bet * 3) + bonus_bet` but omits `progressive_bet`. Meanwhile, `_minimum_bet_required()` at line 402 correctly includes it. This means a session can pass config validation but immediately stop on insufficient funds if the progressive bet pushes the total cost past the bankroll.

```python
# session.py:82 -- missing progressive_bet
min_bet_required = (base_bet * 3) + bonus_bet
```

- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py:82`

Recommendation: Add `progressive_bet` parameter to `validate_session_config` and include it in the minimum bankroll calculation.

### High

**3. Unhandled `KeyError` on invalid hand rank name in custom paytable**

`create_progressive_jackpot()` uses `FiveCardHandRank[hand_name.upper()]` which raises a bare `KeyError` if the YAML config contains a typo like `"ROYAL_FLUSHH"`. The string keys in the `paytable` dict are free-form -- Pydantic validates structure but not enum membership.

```python
# progressive_jackpot.py:190
hand_rank = FiveCardHandRank[hand_name.upper()]
```

- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/progressive_jackpot.py:190`

Recommendation: Wrap in try/except and re-raise as `ValueError` listing valid rank names.

**4. No upper-bound validation on `jackpot_percentage` values**

`ProgressivePayoutEntryConfig.value` uses `Field(ge=0)` with no upper bound. A user could set `type="jackpot_percentage"` with `value=5.0`, causing `evaluate_payout()` to pay 500% of the pool and drive it negative. Subsequent percentage payouts would then be negative, silently corrupting simulation results.

```python
# config/models.py:948-949
type: Literal["fixed", "jackpot_percentage"]
value: Annotated[float, Field(ge=0)]  # no upper bound for percentage
```

- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/config/models.py:948-949`

Recommendation: Add a `model_validator` that enforces `value <= 1.0` when `type == "jackpot_percentage"`.

**5. Two progressive config classes with overlapping names create confusion**

The pre-existing `ProgressiveJackpotConfig` (line 920, used by `BonusPaytableConfig.progressive`) and the new `ProgressiveSideBetConfig` (line 952) both deal with progressive jackpots but serve different purposes (3-card bonus vs. 5-card side bet). Neither class documents its relationship to the other. A developer encountering both would not know whether they conflict, overlap, or are independent.

- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/config/models.py:920-936` (existing)
- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/config/models.py:952-977` (new)

Recommendation: Add cross-reference docstrings to both classes clarifying their distinct purposes.

### Medium

**6. DRY violation: frozen dataclass reconstruction duplicated in two files**

Both `Session.play_hand()` and `TableSession.play_round()` manually reconstruct frozen dataclass instances field-by-field (14+ fields each) to add two progressive fields. This is fragile -- any new field added to `GameHandResult` or `PlayerSeat` must be updated in both locations. The duplication spans ~17 lines per site.

```python
# session.py:527-543 -- 14-field manual copy
result = GameHandResult(
    hand_id=result.hand_id,
    player_cards=result.player_cards,
    ...
    progressive_bet=progressive_bet,
    progressive_payout=progressive_payout,
)
```

- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py:527-543`
- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py:537-552`

Recommendation: Use `dataclasses.replace()` (which works on frozen dataclasses) instead of manual field-by-field reconstruction:
```python
result = replace(result, progressive_bet=progressive_bet, progressive_payout=progressive_payout, net_result=result.net_result + progressive_net)
```

**7. `ProgressivePaytable` missing `slots=True`**

`ProgressivePayout` correctly uses `@dataclass(frozen=True, slots=True)` but `ProgressivePaytable` uses only `@dataclass(frozen=True)`. This is inconsistent with the project convention where frozen dataclasses use `slots=True` (see `GameHandResult`, `PlayerSeat`, `ProgressivePayout`).

```python
# progressive_jackpot.py:37
@dataclass(frozen=True)  # missing slots=True
class ProgressivePaytable:
```

- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/progressive_jackpot.py:37`

**8. `GameHandResult` and `PlayerSeat` docstrings not updated for new fields**

The `Attributes` sections of both `GameHandResult` (line 29-42) and `PlayerSeat` (line 30-41) list all fields but omit the new `progressive_bet` and `progressive_payout` fields. The `SessionConfig`, `TableSessionConfig`, and `SessionResult` docstrings also omit the new `progressive_bet` / `total_progressive_wagered` fields.

- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/game_engine.py:29-42`
- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/table.py:30-41`
- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py:148-161`

**9. `SessionResult.total_progressive_wagered` placed far from related field**

The new `total_progressive_wagered` field is declared after `max_drawdown_pct` (line 219), far from the logically related `total_bonus_wagered` (line 214). The docstring correctly groups them together (line 198), but the actual field ordering is inconsistent. This makes the dataclass harder to read and maintain.

- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py:216-219`

**10. `contribute()` accepts negative bet amounts without validation**

The `contribute()` method takes any float, including negative values, which would decrease the pool. While the Pydantic config constrains `bet_amount` to `gt=0`, a programmatic caller could pass a negative value.

```python
# progressive_jackpot.py:95-101
def contribute(self, bet_amount: float) -> None:
    self._pool += self._contribution_rate * bet_amount
```

- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/progressive_jackpot.py:95-101`

Recommendation: Add a guard: `if bet_amount < 0: raise ValueError(...)`.

**11. Loop-invariant condition checked per seat in table session hot path**

The condition `if self._progressive_jackpot is not None and progressive_bet > 0` is evaluated inside the per-seat loop, but both values are constant for the entire round. This should be hoisted outside the loop.

- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py:528`

**12. `enhanced_seat_results` list allocated even when progressive is disabled**

When progressive is disabled, the code still allocates an empty list and appends to it on every seat of every round, only to discard it at line 575 where it returns the original `result`. This is unnecessary overhead on the hot path.

- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py:515`

Recommendation: Guard the list allocation behind the progressive-enabled check, or restructure to avoid the list entirely when progressive is off.

### Positive Observations

- The core `ProgressiveJackpot` class demonstrates strong single-responsibility design with clean encapsulation of pool mutation logic, `__slots__` for memory efficiency, and O(1) dict-based payout lookup.
- Excellent use of `frozen=True, slots=True` on `ProgressivePayout` for immutable value semantics.
- The `TYPE_CHECKING` guard for the config import avoids circular dependencies cleanly.
- Factory function pattern (`create_progressive_jackpot`, `standard_progressive_paytable`) provides good separation between config parsing and domain construction.
- Per-session jackpot instantiation in `controller.py` and `parallel.py` correctly avoids shared mutable state across parallel workers.
- The `ProgressiveSideBetConfig` Pydantic model uses `extra="forbid"` and `Annotated` field constraints appropriately, following existing project patterns.
- Comprehensive unit test coverage of the `ProgressiveJackpot` class with well-organized test classes and consistent use of `pytest.approx()` for float comparisons.
- The YAML example config includes thorough inline documentation explaining contribution rate math and expected behavior.
