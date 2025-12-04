# Performance Review - PR #78

## Summary

This PR adds dealer discard mechanics to the game engine with minimal performance impact. The implementation is efficient for the common case (discard disabled) and introduces only one additional conditional check and one list reassignment per hand in the hot path. However, there are two areas worth addressing: (1) an unnecessary list allocation in `last_discarded_cards()` that could impact validation workflows, and (2) an object instantiation of `DealerConfig()` in the constructor fallback that could be avoided.

## Findings

### Critical

None identified.

### High

None identified.

### Medium

**M1: Unnecessary DealerConfig instantiation in constructor fallback**

- **File:** `src/let_it_ride/core/game_engine.py`
- **Line:** 89 (diff line 129)
- **Issue:** The expression `dealer_config or DealerConfig()` creates a new Pydantic model instance every time the `GameEngine` constructor is called with `dealer_config=None`. Pydantic model instantiation involves validation overhead.

- **Impact:** When simulating 100k+ hands/second with session-level engine reuse, this is negligible (one-time cost per session). However, if engines are created per-hand or frequently, this adds unnecessary overhead.

- **Recommendation:** Use a module-level singleton for the default config:
  ```python
  # At module level
  _DEFAULT_DEALER_CONFIG = DealerConfig()

  # In __init__
  self._dealer_config = dealer_config if dealer_config is not None else _DEFAULT_DEALER_CONFIG
  ```

**M2: List copy in `last_discarded_cards()` accessor**

- **File:** `src/let_it_ride/core/game_engine.py`
- **Line:** 221 (diff line 165)
- **Issue:** The method returns `self._last_discarded_cards.copy()` which allocates a new list on every call. While this is defensive programming (good for correctness), it adds allocation overhead if called frequently during validation or analytics.

- **Impact:** If this method is called in a tight loop during statistical validation (e.g., checking all discarded cards across millions of hands), the repeated list allocations will create GC pressure.

- **Recommendation:** Consider one of these approaches:
  1. Return a tuple instead (immutable, no need to copy): `return tuple(self._last_discarded_cards)`
  2. Document that the returned list should not be modified and return directly (trading safety for performance)
  3. Store as tuple internally from the start

### Low

**L1: Empty list reassignment in hot path**

- **File:** `src/let_it_ride/core/game_engine.py`
- **Line:** 136 (diff line 140)
- **Issue:** `self._last_discarded_cards = []` creates a new empty list object on every `play_hand()` call, regardless of whether discard is enabled.

- **Impact:** Minimal - a single empty list allocation per hand is negligible at 100k hands/second. However, it could be avoided when discard is disabled.

- **Recommendation:** Move inside the conditional:
  ```python
  if self._dealer_config.discard_enabled:
      self._last_discarded_cards = self._deck.deal(
          self._dealer_config.discard_cards
      )
  elif self._last_discarded_cards:
      self._last_discarded_cards = []
  ```
  This only clears the list when necessary.

**L2: Missing `__slots__` on DealerConfig**

- **File:** `src/let_it_ride/config/models.py`
- **Line:** 77 (diff line 61)
- **Issue:** The `DealerConfig` class does not use `__slots__`. While Pydantic v2 models have their own memory optimizations, adding `__slots__` can reduce memory footprint for frequently instantiated objects.

- **Impact:** Negligible for this use case since `DealerConfig` is typically instantiated once per session.

- **Recommendation:** Not critical, but for consistency with other performance-optimized classes in the codebase, consider adding `__slots__` if Pydantic supports it for this model type.

## Recommendations

### Priority 1 (Should Fix)

1. **Use a singleton for default DealerConfig** (M1)
   - File: `src/let_it_ride/core/game_engine.py:89`
   - Avoids Pydantic validation overhead on every engine instantiation

### Priority 2 (Consider Fixing)

2. **Return tuple from `last_discarded_cards()`** (M2)
   - File: `src/let_it_ride/core/game_engine.py:221`
   - Avoids list allocation, provides immutability guarantee

3. **Conditional list clearing** (L1)
   - File: `src/let_it_ride/core/game_engine.py:136`
   - Micro-optimization, only if profiling shows hot path allocation issues

## Performance Impact Assessment

The overall performance impact of this PR is **LOW**. The changes are well-designed with the hot path in mind:

1. **Branch prediction friendly**: The `if self._dealer_config.discard_enabled` check will predict false for the default case, adding minimal overhead
2. **No additional allocations in disabled case**: When discard is disabled, only the empty list assignment occurs
3. **Efficient deck operations**: Uses existing `deck.deal()` which is already O(1) per card

Estimated overhead per hand when discard is disabled: ~10-50ns (one boolean check + one list assignment)
Estimated overhead per hand when discard is enabled: ~100-200ns additional (dealing 3 cards from deck)

**The 100k hands/second target is not at risk from these changes.**
