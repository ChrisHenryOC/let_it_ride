# LIR-41: Dealer Discard Mechanics

**GitHub Issue:** #71
**Status:** In Progress

## Summary

Implement dealer card discard before dealing to players. The dealer takes 3 cards from the deck and discards the top card (all 3 are removed from play).

## Implementation Tasks

1. **Add DealerConfig to config/models.py**
   - Create `DealerConfig` Pydantic model with:
     - `discard_enabled: bool = False`
     - `discard_cards: int = 3` (with validation 1-10)
   - Add `dealer` field to `FullConfig`

2. **Update GameEngine**
   - Add optional `dealer_config` parameter to `__init__`
   - Modify `play_hand()` to:
     - Deal 3 cards to dealer position before player deal when enabled
     - Track discarded cards separately for statistical validation
   - Add `_discarded_cards` tracking attribute
   - Add `last_discarded_cards()` method for validation access

3. **Create unit tests**
   - Test dealer discard disabled (backwards compatibility)
   - Test dealer discard enabled removes correct number of cards
   - Test discarded cards are tracked
   - Test deck has correct remaining cards after discard
   - Integration test verifying card removal from deck

## Design Decisions

- **DealerConfig location**: Adding as new section to `FullConfig` (similar to `DeckConfig`)
- **Discarded cards tracking**: Store in GameEngine instance for validation access
- **Backwards compatibility**: Default `discard_enabled=False` ensures no behavior change

## Files Modified

- `src/let_it_ride/config/models.py` - Add DealerConfig
- `src/let_it_ride/core/game_engine.py` - Add dealer discard logic

## Files Created

- `tests/unit/core/test_dealer_mechanics.py` - Unit tests
