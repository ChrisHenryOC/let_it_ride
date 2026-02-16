# Performance Review - PR #158: LIR-62 Progressive Jackpot Side Bet Model

## Summary

This PR introduces a progressive jackpot side bet evaluated on every hand in the simulation hot path. The core `ProgressiveJackpot` class is well-designed with `__slots__` and O(1) dict lookup, but the integration into `Session.play_hand()` and `TableSession.play_round()` introduces significant per-hand allocation overhead through frozen dataclass reconstruction. At the target of 100,000+ hands/second, the extra object creation on every single hand is the primary performance concern. Secondary issues include redundant paytable object creation per session, uncached method calls in the stop-condition check, and avoidable list allocations in the table session path.

## Findings

### High

**H1. Frozen dataclass reconstruction on every hand -- doubles allocation in hot path**

When progressive is enabled, every hand triggers a full reconstruction of either `GameHandResult` (14 fields) or `PlayerSeat` (14 fields) just to set two new fields (`progressive_bet`, `progressive_payout`) and adjust `net_result`. These are `@dataclass(frozen=True, slots=True)`, so regular attribute assignment is blocked. The code manually copies all fields into a new constructor call.

At 100,000 hands/second in `Session.play_hand()`, this is 100,000 extra `GameHandResult` allocations per second. In `TableSession.play_round()` with 6 seats, this becomes 600,000 extra `PlayerSeat` allocations per second. Each allocation involves constructing a new object, populating 14+ slots, and garbage-collecting the original.

Files:
- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py` lines 527-543
- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py` lines 537-552

```python
# session.py:527-543 -- full 14-field reconstruction every hand
result = GameHandResult(
    hand_id=result.hand_id,
    player_cards=result.player_cards,
    community_cards=result.community_cards,
    decision_bet1=result.decision_bet1,
    decision_bet2=result.decision_bet2,
    final_hand_rank=result.final_hand_rank,
    base_bet=result.base_bet,
    bets_at_risk=result.bets_at_risk,
    main_payout=result.main_payout,
    bonus_bet=result.bonus_bet,
    bonus_hand_rank=result.bonus_hand_rank,
    bonus_payout=result.bonus_payout,
    net_result=result.net_result + progressive_net,
    progressive_bet=progressive_bet,
    progressive_payout=progressive_payout,
)
```

There are three viable fixes, in order of preference:

1. **Use `dataclasses.replace()`**: Despite being frozen+slots, `dataclasses.replace()` works on frozen dataclasses in Python 3.10+. It uses `object.__setattr__` internally. This reduces the code to a single line and avoids the fragile field-by-field copy:
   ```python
   result = dataclasses.replace(
       result,
       net_result=result.net_result + progressive_net,
       progressive_bet=progressive_bet,
       progressive_payout=progressive_payout,
   )
   ```
   Note: `dataclasses.replace()` still creates a new object, but it reads fields via a faster internal path and eliminates the manual enumeration of all 14 fields (maintenance hazard and source of bugs if a field is added).

2. **Use `object.__setattr__` to mutate in place**: Since the result object was just created by `GameEngine.play_hand()` moments earlier and has not been shared, in-place mutation is safe:
   ```python
   object.__setattr__(result, 'net_result', result.net_result + progressive_net)
   object.__setattr__(result, 'progressive_bet', progressive_bet)
   object.__setattr__(result, 'progressive_payout', progressive_payout)
   ```
   This is the fastest option -- zero allocation, three attribute writes. The frozen invariant is preserved for downstream consumers.

3. **Move progressive evaluation into `GameEngine.play_hand()`**: Pass the `ProgressiveJackpot` to the engine so the result is constructed once with all fields populated. This eliminates the second allocation entirely but increases coupling between the engine and the progressive feature.

Option 2 is the strongest recommendation for a performance-critical simulator. It eliminates the allocation entirely with three attribute writes.

---

**H2. `standard_progressive_paytable()` recreated per session -- 100,000+ identical immutable objects**

Every session calls `get_progressive_jackpot()` which calls `create_progressive_jackpot()` which calls `standard_progressive_paytable()`. This allocates a new `ProgressivePaytable` containing 6 new `ProgressivePayout` objects every time. For 100,000 sessions, that is 100,000 identical frozen paytable instances and 600,000 identical frozen payout instances -- all with the same values.

The paytable is immutable (`frozen=True`). It should be created once and reused. The mutable pool state lives in `ProgressiveJackpot`, not in the paytable.

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/progressive_jackpot.py` lines 139-169 (the `standard_progressive_paytable()` function)

```python
# progressive_jackpot.py -- called once per session, creates 7 frozen objects
def standard_progressive_paytable() -> ProgressivePaytable:
    return ProgressivePaytable(
        name="standard_progressive",
        payouts={
            FiveCardHandRank.ROYAL_FLUSH: ProgressivePayout(type="jackpot_percentage", value=1.0),
            # ... 5 more entries
        },
    )
```

Fix: Cache as a module-level constant or use `@functools.lru_cache(maxsize=1)`:

```python
_STANDARD_PROGRESSIVE_PAYTABLE = ProgressivePaytable(
    name="standard_progressive",
    payouts={ ... },
)

def standard_progressive_paytable() -> ProgressivePaytable:
    return _STANDARD_PROGRESSIVE_PAYTABLE
```

---

### Medium

**M1. `_minimum_bet_required()` recomputed on every `should_stop()` call -- session-constant arithmetic repeated per hand**

Both `Session._minimum_bet_required()` and `TableSession._minimum_bet_required()` perform arithmetic (`base_bet * 3 + bonus_bet + progressive_bet`) on values that never change during a session. This method is called on every `should_stop()` check, which happens every hand.

While each individual call is cheap (two additions, one multiplication), at 100,000+ hands/second this is unnecessary repeated work. The result should be computed once in `__init__` and stored.

Files:
- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py` lines 402-411
- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py` lines 293-301

```python
# session.py:402-411 -- recomputed every hand
def _minimum_bet_required(self) -> float:
    return (
        (self._config.base_bet * 3)
        + self._config.bonus_bet
        + self._config.progressive_bet
    )
```

Fix: Add `self._min_bet_required` to `__slots__` and compute in `__init__`:
```python
self._min_bet_required = (config.base_bet * 3) + config.bonus_bet + config.progressive_bet
```

---

**M2. Loop-invariant `None` check repeated per seat in `TableSession.play_round()`**

The condition `if self._progressive_jackpot is not None and progressive_bet > 0` is evaluated inside the per-seat loop, but both `self._progressive_jackpot` and `progressive_bet` are invariant across all seats in a round. With 6 seats and 100,000 rounds, this is 600,000 redundant branch evaluations per session.

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py` line 528

```python
for seat_result in result.seat_results:
    # ...
    if self._progressive_jackpot is not None and progressive_bet > 0:  # loop-invariant
        self._progressive_jackpot.contribute(progressive_bet)
        # ...
```

Fix: Hoist the check outside the loop and use separate code paths, or cache the boolean once:
```python
progressive_enabled = self._progressive_jackpot is not None and progressive_bet > 0
for seat_result in result.seat_results:
    if progressive_enabled:
        ...
```

---

**M3. `enhanced_seat_results` list allocated every round even when progressive is disabled**

When progressive is disabled, the code still allocates `enhanced_seat_results: list[PlayerSeat] = []` and appends every seat result to it on every round. The list is only needed when progressive fields must be added. When disabled, the original `result.seat_results` tuple should be used directly.

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py` line 515

```python
# Always allocated, even when progressive is disabled
enhanced_seat_results: list[PlayerSeat] = []
```

For a 6-seat table running 100,000 rounds, this is 100,000 unnecessary list allocations plus 600,000 unnecessary `list.append()` calls. The conditional return at line 575 (`if self._progressive_jackpot is not None`) partially mitigates this by returning the original `result` when progressive is disabled, but the allocation and population still occur.

Fix: Guard the list creation behind the progressive-enabled check, or restructure the loop into two paths.

---

**M4. `TableRoundResult` reconstructed every round when progressive is enabled**

When progressive is enabled, a new `TableRoundResult` is constructed at line 574-579 with `tuple(enhanced_seat_results)`, converting the list to a tuple. This creates a new `TableRoundResult` and a new tuple every round. Combined with H1 (per-seat `PlayerSeat` reconstruction), a 6-seat table creates 8 new objects per round (6 `PlayerSeat` + 1 tuple + 1 `TableRoundResult`).

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py` lines 574-579

```python
if self._progressive_jackpot is not None and progressive_bet > 0:
    return TableRoundResult(
        round_id=result.round_id,
        community_cards=result.community_cards,
        dealer_discards=result.dealer_discards,
        seat_results=tuple(enhanced_seat_results),
    )
```

This compounds with H1. If H1 is fixed with `object.__setattr__` (mutating `PlayerSeat` in place), the enhanced list and `TableRoundResult` reconstruction become unnecessary.

---

### Low

**L1. `ProgressivePaytable` missing `slots=True` -- inconsistent with project conventions**

`ProgressivePayout` uses `@dataclass(frozen=True, slots=True)` but `ProgressivePaytable` uses only `@dataclass(frozen=True)`. While `ProgressivePaytable` is instantiated infrequently (once per session, or ideally once total if H2 is fixed), the inconsistency with project conventions is worth correcting. The `slots=True` flag reduces per-instance memory by eliminating the `__dict__` and provides marginally faster attribute access.

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/progressive_jackpot.py` line 37

```python
@dataclass(frozen=True)  # Missing slots=True
class ProgressivePaytable:
```

---

**L2. Float accumulation drift in jackpot pool over long sessions**

The pool accumulates via `self._pool += self._contribution_rate * bet_amount` using IEEE 754 doubles. For current session lengths (200 hands), drift is negligible (on the order of 1e-14). This would only become a practical concern if session lengths grew significantly or if the pool were shared across sessions. The current `float` approach is the correct performance trade-off; `Decimal` would be approximately 100x slower.

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/progressive_jackpot.py` line 101

---

## Impact Assessment

Estimated per-hand overhead when progressive is enabled (versus disabled):

| Operation | Cost per hand | At 100k hands/s |
|-----------|--------------|-----------------|
| `GameHandResult` reconstruction (H1) | ~1-2 us (alloc + 14 slot writes + GC) | 100-200 ms/s |
| `ProgressiveJackpot.contribute()` | ~50 ns (float multiply + add) | 5 ms/s |
| `ProgressiveJackpot.evaluate_payout()` | ~100 ns (dict lookup + branch) | 10 ms/s |
| `_minimum_bet_required()` repeat (M1) | ~30 ns (2 adds + multiply) | 3 ms/s |

The dataclass reconstruction (H1) dominates. For a 6-seat `TableSession`, multiply by 6 for `PlayerSeat` plus the `TableRoundResult` reconstruction (M4). The combined overhead could reduce throughput by 10-20% when progressive is enabled.

## Positive Observations

- **`ProgressiveJackpot` uses `__slots__`** with only 5 attributes, minimizing memory footprint for the object that persists for the entire session lifetime.
- **O(1) `dict.get()` for payout lookup** avoids any linear scan of payout rules.
- **Early return for non-qualifying hands** (`if payout_rule is None: return 0.0`) ensures the common case (most hands do not qualify for progressive payouts) exits immediately with minimal work.
- **Per-session jackpot isolation** avoids shared mutable state across parallel workers, which is correct for both correctness and thread safety. No GIL concerns since each worker gets its own instance.
- **Zero overhead when disabled**: The `if self._progressive_jackpot is not None` guard at the top of the progressive block ensures zero work when the feature is off.
- **`ProgressivePayout` uses `frozen=True, slots=True`**: Immutable value objects with slots is the correct pattern for paytable entries that are looked up frequently.
