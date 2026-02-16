# Performance Review - PR #158

## Summary

The progressive jackpot implementation is generally well-structured with good use of `__slots__` on the hot-path `ProgressiveJackpot` class and frozen dataclasses with slots on `ProgressivePayout`. The main performance concerns are (1) unnecessary per-hand reconstruction of frozen dataclass objects in the hot loop, (2) redundant paytable object creation on every session, and (3) a shared-jackpot design in `TableSession` that introduces a subtle correctness-coupled performance issue with multi-seat contribution scaling.

## Findings

### Critical

No critical performance issues found.

### High

**H1. Unnecessary frozen dataclass reconstruction on every hand (hot path)**
- Files: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py:527-543`, `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py:537-552`
- When progressive is enabled, every single hand creates a brand-new `GameHandResult` (or `PlayerSeat`) by copying all 14+ fields from the original just to add the two progressive fields. These are frozen `slots=True` dataclasses, so `dataclasses.replace()` is not available without unfreezing. At 100,000+ hands/second, this means 100,000+ extra object allocations per second in `Session.play_hand()`, and up to 6x that in multi-seat `TableSession.play_round()`.

```python
# session.py:527-543 -- full reconstruction every hand
result = GameHandResult(
    hand_id=result.hand_id,
    player_cards=result.player_cards,
    community_cards=result.community_cards,
    decision_bet1=result.decision_bet1,
    ...
    progressive_bet=progressive_bet,
    progressive_payout=progressive_payout,
)
```

Consider one of:
  - Move progressive evaluation into `GameEngine.play_hand()` so the result is constructed once with progressive fields already populated, avoiding the second allocation entirely.
  - Use `object.__setattr__` on the frozen dataclass to mutate in place (acceptable for internal hot-path code).
  - Use `dataclasses.replace()` by switching to a non-frozen dataclass with a custom `__hash__` if immutability is needed downstream.

**H2. Paytable and jackpot objects recreated per session (100,000+ times)**
- File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/progressive_jackpot.py:172-202` via `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/utils.py:103-114`
- `get_progressive_jackpot()` is called once per session. It calls `create_progressive_jackpot()`, which calls `standard_progressive_paytable()`, allocating a new `ProgressivePaytable` with a new dict of 6 `ProgressivePayout` objects every time. For 100,000 sessions, that is 100,000 identical `ProgressivePaytable` instances and 600,000 `ProgressivePayout` instances.

```python
# progressive_jackpot.py:194 -- called per session
paytable = standard_progressive_paytable()
```

The paytable is immutable (frozen dataclass with frozen payout entries). It should be created once and shared. The mutable `ProgressiveJackpot` can hold a reference to a shared paytable while still having per-session pool state. Consider caching `standard_progressive_paytable()` as a module-level constant or using `functools.lru_cache`.

### Medium

**M1. Redundant condition check on every seat iteration in table session**
- File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py:528`
- The condition `if self._progressive_jackpot is not None and progressive_bet > 0` is checked inside the per-seat loop, but both values are loop-invariant. The branch should be hoisted outside the loop or the progressive path should be a separate method entirely to avoid the repeated branch prediction miss on the hot path.

```python
# table_session.py:528 -- checked per seat, per round
if self._progressive_jackpot is not None and progressive_bet > 0:
```

**M2. `enhanced_seat_results` list always allocated even when progressive is disabled**
- File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py:515`
- When progressive is disabled, the code still allocates `enhanced_seat_results: list[PlayerSeat] = []` and appends to it on every round for every seat. This is wasted work when the original `result.seat_results` tuple could be used directly. The conditional return at line 575 partially addresses this, but the list allocation and append operations still occur.

**M3. `_minimum_bet_required()` recomputes every call**
- Files: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py:402-410`, `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py:293-301`
- This method is called on every `should_stop()` check (i.e., every hand). It performs 2 additions and a multiplication. While cheap individually, the values (`base_bet`, `bonus_bet`, `progressive_bet`) never change during a session. This could be computed once during `__init__` and cached.

### Low

**L1. `ProgressivePaytable` does not use `__slots__`**
- File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/progressive_jackpot.py:271`
- `ProgressivePaytable` is `@dataclass(frozen=True)` but does not specify `slots=True`. While this object is not frequently instantiated (once per session, or ideally once total if H2 is fixed), it is inconsistent with the project's pattern of using `slots=True` on all frozen dataclasses in the hot path (`ProgressivePayout`, `GameHandResult`, `PlayerSeat` all use it).

```python
@dataclass(frozen=True)  # Missing slots=True
class ProgressivePaytable:
```

**L2. Float arithmetic for jackpot pool may drift over millions of hands**
- File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/progressive_jackpot.py:101`
- The pool is incremented by `contribution_rate * bet_amount` on every hand. Over a 200-hand session this is negligible, but if session lengths grow or the jackpot is ever shared across sessions, accumulated floating-point drift could become noticeable. Not a performance issue per se, but worth noting for correctness at scale. Using `decimal.Decimal` would be more accurate but slower; the current float approach is the right trade-off for performance.

### Positive

- **Good use of `__slots__` on `ProgressiveJackpot`** (`/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/progressive_jackpot.py:293-299`): The main mutable class that exists for the lifetime of a session correctly uses `__slots__`, reducing memory overhead and improving attribute access speed.
- **`ProgressivePayout` is `frozen=True, slots=True`** (`/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/progressive_jackpot.py:258`): Immutable value objects with slots is the correct pattern for paytable entries.
- **Dict lookup for payout evaluation is O(1)** (`/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/progressive_jackpot.py:117`): Using `dict.get(hand_rank)` for the paytable lookup is efficient and avoids any linear scan.
- **Early return for non-qualifying hands** (`/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/progressive_jackpot.py:118`): The fast path for the common case (most hands do not qualify) returns `0.0` immediately.
- **Per-session jackpot isolation**: Each session gets its own `ProgressiveJackpot` instance, avoiding shared mutable state across parallel workers. This is correct for both correctness and thread safety.
- **`None` return when disabled**: `get_progressive_jackpot()` returns `None` when progressive is disabled, and the `if self._progressive_jackpot is not None` guard skips all progressive logic, ensuring zero overhead when the feature is off.
