# LIR-37: Streak-Based Bonus Strategy

GitHub Issue: https://github.com/ChrisHenryOC/let_it_ride/issues/40

## Overview

Implement bonus betting that adjusts based on win/loss streaks.

## Analysis

### Existing Infrastructure
- `BonusContext` already has `main_streak` and `bonus_streak` fields (positive = wins, negative = losses)
- `StreakBasedBonusConfig` already exists in config/models.py with:
  - `base_amount`: Base bonus bet
  - `trigger`: What event to track (main_loss, main_win, bonus_loss, bonus_win, any_loss, any_win)
  - `streak_length`: Consecutive events to trigger action
  - `action`: StreakActionConfig with type (increase, decrease, stop, start, multiply) and value
  - `reset_on`: Event that resets the streak counter
  - `max_multiplier`: Cap on streak multiplier

### Key Insight
The issue mentions tracking streaks INTERNALLY with `record_result()`, but `BonusContext` already provides streak info externally. Looking at the config, the strategy should use the context's streak values directly without needing internal state. However, the issue specifically asks for `record_result()` and `reset()` methods.

**Decision**: Implement a stateful strategy that tracks its own streak count, which allows for more flexibility (e.g., tracking bonus-specific streaks even when session doesn't track them the same way).

## Implementation Plan

### 1. StreakBasedBonusStrategy class
```python
class StreakBasedBonusStrategy:
    """Strategy that adjusts bonus bets based on win/loss streaks."""

    def __init__(
        self,
        base_amount: float,
        trigger: Literal["main_loss", "main_win", "bonus_loss", "bonus_win", "any_loss", "any_win"],
        streak_length: int,
        action_type: Literal["increase", "decrease", "multiply", "stop", "start"],
        action_value: float,
        reset_on: Literal["main_loss", "main_win", "bonus_loss", "bonus_win", "any_loss", "any_win", "never"],
        max_multiplier: float = 5.0,
    )

    def get_bonus_bet(self, context: BonusContext) -> float
    def record_result(self, main_won: bool, bonus_won: bool | None) -> None
    def reset(self) -> None

    @property
    def current_streak(self) -> int
    @property
    def current_multiplier(self) -> float
```

### 2. Trigger Logic
The trigger determines which outcomes increment the streak counter:
- `main_win`: Main game win (payout > 0)
- `main_loss`: Main game loss (payout = 0)
- `bonus_win`: Bonus bet win (payout > 0)
- `bonus_loss`: Bonus bet loss (payout = 0)
- `any_win`: Either main or bonus wins
- `any_loss`: Either main or bonus loses

### 3. Action Logic
When streak reaches `streak_length`:
- `increase`: Add `action_value` to current bet
- `decrease`: Subtract `action_value` from current bet
- `multiply`: Multiply base by `action_value`
- `stop`: Return 0 (stop betting)
- `start`: Start betting (for use when normally not betting)

### 4. Reset Logic
When reset event occurs, streak counter resets to 0.

## Tasks

1. [x] Implement StreakBasedBonusStrategy class
2. [x] Add factory support in create_bonus_strategy()
3. [x] Write comprehensive unit tests
4. [x] Test edge cases (reset behavior, max multiplier cap)
5. [x] Run full test suite
6. [x] Format and lint
7. [x] Type check

## Implementation Notes

### StreakBasedBonusStrategy Class
- Uses `__slots__` for memory efficiency
- Tracks internal streak counter (`_current_streak`)
- `_is_betting` flag controls stop/start actions
- Implements all trigger types: main_loss, main_win, bonus_loss, bonus_win, any_loss, any_win
- Implements all action types: increase, decrease, multiply, stop, start
- `record_result()` updates streak state and handles reset conditions
- `reset()` restores strategy to initial state
- `current_streak` and `current_multiplier` properties for introspection

### Test Coverage
- 48 new tests for StreakBasedBonusStrategy
- Tests all trigger types
- Tests all action types
- Tests all reset behaviors
- Tests max_multiplier capping
- Tests bet clamping to min/max
- Tests validation errors
- Tests factory creation
