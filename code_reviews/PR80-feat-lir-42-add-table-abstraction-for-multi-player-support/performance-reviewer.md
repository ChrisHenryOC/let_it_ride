# Performance Review - PR #80

## Summary

This PR introduces the `Table` abstraction for multi-player Let It Ride support. The implementation is well-structured with appropriate use of frozen dataclasses and module-level singleton defaults. However, there are several performance considerations: (1) list-to-tuple conversions in the hot path create unnecessary object allocations, (2) the `_process_seat` method creates intermediate lists that could be avoided, and (3) the `seat_results` list in `TableRoundResult` is mutable which requires defensive copying. These issues will scale linearly with the number of seats (up to 6x overhead).

## Findings

### Critical

None identified.

### High

None identified.

### Medium

**M1: Repeated list-to-tuple conversion in hot path seat dealing loop**

- **File:** `src/let_it_ride/core/table.py`
- **Lines:** 163-165 (diff lines 439-441)
- **Issue:** In the `play_round` method, each seat's cards are converted from a list to a tuple:
  ```python
  cards = self._deck.deal(3)
  seat_cards.append((cards[0], cards[1], cards[2]))
  ```
  The `deal()` method returns a list, and the tuple construction via indexing creates a new tuple object per seat. With 6 seats, this results in 6 tuple allocations per round.

- **Impact:** At 100k+ hands/second with 6 seats, this means 600k tuple allocations per second in the dealing phase alone. While individual allocations are cheap, the cumulative GC pressure can impact throughput.

- **Recommendation:** Consider modifying the `Deck.deal()` method to optionally return a tuple, or accept the overhead as the cost of type safety. Alternatively, use tuple unpacking which is marginally faster:
  ```python
  cards = self._deck.deal(3)
  seat_cards.append(tuple(cards))
  ```
  However, the current explicit indexing approach is slightly faster than `tuple()` for 3 elements.

**M2: Intermediate list creation in `_process_seat` for hand evaluation**

- **File:** `src/let_it_ride/core/table.py`
- **Lines:** 233-238 (diff lines 509-515)
- **Issue:** Two intermediate lists are created per seat:
  ```python
  four_cards = [*player_cards, community_cards[0]]  # Line 509
  ...
  final_cards = list(player_cards) + list(community_cards)  # Line 514
  ```
  Both use list operations that allocate new list objects. The `list(player_cards)` call is particularly wasteful since `player_cards` is already a tuple of cards.

- **Impact:** With 6 seats, this creates 12 list allocations per round (2 per seat). At 100k hands/second, that's 1.2M list allocations per second in the processing phase.

- **Recommendation:** The existing `analyze_four_cards` and `evaluate_five_card_hand` functions accept `Sequence[Card]`, so you can pass tuples directly:
  ```python
  four_cards = (*player_cards, community_cards[0])  # tuple unpacking, no list
  ...
  final_cards = (*player_cards, *community_cards)  # tuple unpacking
  ```
  This avoids list allocations entirely. Profile to confirm benefit.

**M3: `seat_results` stored as mutable list in frozen dataclass**

- **File:** `src/let_it_ride/core/table.py`
- **Lines:** 72-74 (diff lines 348-350)
- **Issue:** The `TableRoundResult` dataclass is frozen but contains `seat_results: list[PlayerSeat]`. While the dataclass attribute cannot be reassigned, the list itself is mutable, allowing:
  ```python
  result.seat_results.append(malicious_seat)  # This works despite frozen=True
  ```
  This means any code receiving a `TableRoundResult` could modify the seat results list.

- **Impact:** This is primarily a correctness/defensive programming issue. However, if the Session or analytics code stores references and later the list is modified, it could cause data corruption. More critically, if defensive copying is added later, it will add allocation overhead.

- **Recommendation:** Store as tuple instead:
  ```python
  seat_results: tuple[PlayerSeat, ...]
  ```
  And construct with `tuple(seat_results)` at line 203 (diff line 479). This provides immutability and avoids the need for defensive copying downstream.

### Low

**L1: Empty list reassignment in hot path regardless of discard state**

- **File:** `src/let_it_ride/core/table.py`
- **Line:** 170 (diff line 446)
- **Issue:** Similar to the issue identified in PR #78 for GameEngine:
  ```python
  self._last_discarded_cards = []
  ```
  This creates a new empty list object on every `play_round()` call, regardless of whether discard is enabled.

- **Impact:** Minimal - single empty list allocation per round is negligible at 100k rounds/second.

- **Recommendation:** Move inside the conditional block or use `self._last_discarded_cards.clear()` if reusing the list:
  ```python
  if self._dealer_config.discard_enabled:
      self._last_discarded_cards = self._deck.deal(
          self._dealer_config.discard_cards
      )
  else:
      self._last_discarded_cards = []
  ```

**L2: Module-level singleton pattern correctly applied**

- **File:** `src/let_it_ride/core/table.py`
- **Lines:** 23-24 (diff lines 299-300)
- **Observation:** Good implementation of the module-level singleton pattern for default configs:
  ```python
  _DEFAULT_DEALER_CONFIG = DealerConfig()
  _DEFAULT_TABLE_CONFIG = TableConfig()
  ```
  This follows the recommendation from PR #78 review and avoids repeated Pydantic validation overhead. **This is a positive pattern to acknowledge.**

**L3: Tuple conversion in `last_discarded_cards()` is appropriate**

- **File:** `src/let_it_ride/core/table.py`
- **Lines:** 287-293 (diff lines 563-569)
- **Observation:** The method returns `tuple(self._last_discarded_cards)` which addresses the issue identified in PR #78. The tuple provides immutability and is efficient for the typical 0-3 card case. **Good practice.**

## Recommendations

### Priority 1 (Should Consider)

1. **Change `seat_results` to tuple** (M3)
   - File: `src/let_it_ride/core/table.py:72`
   - Provides true immutability for the frozen dataclass
   - Prevents accidental mutation by downstream code
   - No performance cost (tuple construction is same as list)

2. **Use tuple unpacking for intermediate card collections** (M2)
   - File: `src/let_it_ride/core/table.py:233-238`
   - Avoids 12 list allocations per round with 6 seats
   - Functions already accept `Sequence[Card]` so tuples work

### Priority 2 (Minor Optimizations)

3. **Conditional list clearing** (L1)
   - File: `src/let_it_ride/core/table.py:170`
   - Micro-optimization, only if profiling shows hot path allocation issues

## Performance Impact Assessment

The overall performance impact of this PR is **LOW to MODERATE** depending on seat count. The implementation is sound for the primary use case (single-seat, backwards compatible with GameEngine).

**Scaling analysis by seat count:**

| Seats | Player Cards | Allocations per Round | Estimated Overhead |
|-------|-------------|----------------------|-------------------|
| 1     | 3           | ~5 (minimal)         | ~50-100ns         |
| 3     | 9           | ~15                  | ~150-300ns        |
| 6     | 18          | ~30                  | ~300-600ns        |

**Key observations:**

1. **Linear scaling with seats**: Overhead grows linearly with seat count, which is acceptable for the 1-6 seat range
2. **Hand evaluation dominates**: The `analyze_three_cards`, `analyze_four_cards`, and `evaluate_five_card_hand` functions are called once per seat and likely dominate runtime
3. **Memory is bounded**: Even with 6 seats, memory per round is small (~2KB including all Card references)
4. **GC-friendly**: Using frozen dataclasses and tuples minimizes mutation tracking overhead

**Estimated throughput impact:**

- Single seat: ~1-2% overhead vs GameEngine (negligible)
- Six seats: ~15-20% overhead per round due to allocation scaling

**The 100k hands/second target is not at risk from these changes for single-seat operation. For multi-seat (6 players), expect ~80-90k rounds/second which represents 480-540k individual hands per second.** This exceeds the target when counting per-seat hands.

## Positive Patterns

The implementation demonstrates several good performance practices:

1. **Module-level singleton defaults** - Avoids repeated Pydantic validation
2. **Frozen dataclasses** - Immutability enables potential optimizations
3. **Reuses existing deck/evaluator infrastructure** - No redundant computation
4. **Single deck shuffle per round** - Amortizes shuffle cost across all seats
5. **Tuple return from `last_discarded_cards()`** - Follows PR #78 recommendation
