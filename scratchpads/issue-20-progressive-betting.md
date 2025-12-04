# LIR-17: Progressive Betting Systems (GitHub #20)

**Issue Link**: https://github.com/ChrisHenryOC/let_it_ride/issues/20

## Overview

Implement 5 progressive betting systems that follow the existing `BettingSystem` protocol.

## Implementation Plan

### 1. MartingaleBetting
- **Logic**: Double bet after loss, reset to base after win
- **Parameters**: base_bet, loss_multiplier (2.0), max_bet (500), max_progressions (6)
- **State**: Current progression level (0 = base bet)
- **Edge cases**: Cap at max_bet, cap at max_progressions

### 2. ReverseMartingaleBetting
- **Logic**: Double bet after win, reset to base after loss
- **Parameters**: base_bet, win_multiplier (2.0), profit_target_streak (3), max_bet (500)
- **State**: Current win streak count
- **Edge cases**: Reset after reaching profit_target_streak

### 3. ParoliBetting
- **Logic**: Increase bet after win (by multiplier), reset after N consecutive wins
- **Parameters**: base_bet, win_multiplier (2.0), wins_before_reset (3), max_bet (500)
- **State**: Consecutive win count, current bet level
- **Edge cases**: Cap at max_bet

### 4. DAlembertBetting
- **Logic**: Add unit after loss, subtract unit after win
- **Parameters**: base_bet, unit (5.0), min_bet (5.0), max_bet (500)
- **State**: Current bet level (starts at base_bet)
- **Edge cases**: Never go below min_bet, never exceed max_bet

### 5. FibonacciBetting
- **Logic**: Progress through Fibonacci sequence on losses, regress on wins
- **Parameters**: base_unit (5.0), win_regression (2), max_bet (500), max_position (10)
- **State**: Current position in Fibonacci sequence
- **Sequence**: [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, ...] * base_unit
- **Edge cases**: Position 0 minimum, cap at max_position, cap at max_bet

## Testing Strategy

For each system:
1. Initialization tests (valid params, invalid params)
2. Progression logic tests (win sequence, loss sequence, mixed)
3. Bet cap enforcement (max_bet respected)
4. Bankroll insufficient tests
5. Reset behavior tests
6. Protocol compliance tests

## Files to Modify

- `src/let_it_ride/bankroll/betting_systems.py` - Add 5 new classes
- `src/let_it_ride/bankroll/__init__.py` - Export new classes
- `tests/unit/bankroll/test_betting_systems.py` - Add comprehensive tests

## Dependencies

- Blocked by LIR-16 (FlatBetting) - COMPLETE
