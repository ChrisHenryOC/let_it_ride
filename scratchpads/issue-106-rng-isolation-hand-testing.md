# LIR-54: Enhanced RNG Isolation Verification with Hand-Level Testing

**GitHub Issue:** https://github.com/ChrisHenryOC/let_it_ride/issues/106

## Problem Statement

The current `test_session_seeds_are_independent` test in `TestRNGIsolation` has a documented limitation:

> "Since we can't inspect individual hands directly, we verify that both runs complete successfully with expected session counts."

This means the test passes but does not definitively prove RNG isolation at the hand level.

## Solution Design

### Approach: Hand Callback Infrastructure

Add a callback mechanism to capture per-hand results during simulation. This follows the existing pattern of `ProgressCallback` already in use.

### Implementation Plan

1. **Define HandCallback type alias** in `controller.py`:
   ```python
   HandCallback = Callable[[int, GameHandResult], None]  # (session_id, result)
   ```

2. **Add hand_callback parameter to Session class**:
   - Modify `SessionConfig` to optionally accept a hand callback
   - Call the callback after each hand in `play_hand()`
   - Pass session_id and GameHandResult to callback

3. **Wire through SimulationController**:
   - Accept optional `hand_callback` in constructor
   - Pass to session creation

4. **Enhance test_session_seeds_are_independent**:
   - Use hand callback to collect all hands
   - Compare first N hands between short and long session runs
   - Verify cards, decisions, and payouts match exactly

### Key Files to Modify

- `src/let_it_ride/simulation/session.py` - Add callback support
- `src/let_it_ride/simulation/controller.py` - Wire callback through controller
- `tests/integration/test_controller.py` - Enhance RNG isolation tests

### Data to Compare

For hand-level verification, we need to compare:
- `player_cards` - The 3 dealt cards
- `community_cards` - The 2 community cards
- `decision_bet1` and `decision_bet2` - Strategy decisions
- `final_hand_rank` - Evaluated hand rank
- `main_payout` and `bonus_payout` - Payouts (depend on bets, which should be identical)

### Test Strategy

1. Create callback that collects hands in dict keyed by (session_id, hand_id)
2. Run simulation with 3 sessions × 5 hands (short)
3. Run simulation with 3 sessions × 50 hands (long)
4. Compare hands 0-4 of each session between runs
5. Assert all cards, decisions, ranks are identical

This definitively proves that:
- Session N gets the same starting RNG state regardless of how many hands session N-1 played
- The first K hands of session N are identical regardless of total hands_per_session

## Tasks

- [ ] Add HandCallback type and support to Session
- [ ] Wire callback through SimulationController
- [ ] Enhance test_session_seeds_are_independent
- [ ] Add helper function for comparing GameHandResult objects
- [ ] Update documentation to reflect enhanced verification
