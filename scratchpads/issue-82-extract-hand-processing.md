# LIR-46: Extract Shared Hand Processing Logic

**GitHub Issue**: [#82](https://github.com/ChrisHenryOC/let_it_ride/issues/82)

## Background

This issue was identified during code review of PR #80 (LIR-42: Table Abstraction). The `Table._process_seat()` method duplicates logic from `GameEngine.play_hand()`.

## Analysis

### Duplicated Logic (Lines 161-203 in game_engine.py, Lines 229-268 in table.py)

1. **3-card hand analysis and Bet 1 decision**
2. **4-card hand analysis and Bet 2 decision**
3. **5-card hand evaluation**
4. **Bets-at-risk calculation**
5. **Main payout calculation**
6. **Bonus evaluation**
7. **Net result calculation**

### Minor Differences

- `game_engine.py`: Uses list unpacking `[*player_cards, community_cards[0]]`
- `table.py`: Uses tuple unpacking `(*player_cards, community_cards[0])`

Both are functionally equivalent since the analysis/evaluation functions accept `Sequence[Card]`.

## Implementation Plan

1. Create `src/let_it_ride/core/hand_processing.py` with:
   - `HandProcessingResult` dataclass (frozen, 8 fields)
   - `process_hand_decisions_and_payouts()` function

2. Refactor `GameEngine.play_hand()` to:
   - Call `process_hand_decisions_and_payouts()`
   - Construct `GameHandResult` from the result

3. Refactor `Table._process_seat()` to:
   - Call `process_hand_decisions_and_payouts()`
   - Construct `PlayerSeat` from the result

4. Update `core/__init__.py` to export new types

5. Run tests to verify no behavioral changes

## Tasks

- [x] Create scratchpad
- [ ] Create feature branch
- [ ] Create `hand_processing.py` module
- [ ] Refactor `GameEngine.play_hand()`
- [ ] Refactor `Table._process_seat()`
- [ ] Update exports
- [ ] Run tests
- [ ] Run linting/formatting
- [ ] Run type checking
- [ ] Create PR
