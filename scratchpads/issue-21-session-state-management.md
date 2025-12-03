# LIR-18: Session State Management

**GitHub Issue**: #21 - https://github.com/ChrisHenryOC/let_it_ride/issues/21

## Overview

Implement session lifecycle management with stop conditions. A Session manages the execution of multiple hands until a stop condition is met.

## Dependencies (Completed)

- LIR-13 (GameEngine) ✅ - `src/let_it_ride/core/game_engine.py`
- LIR-15 (BettingSystem) ✅ - `src/let_it_ride/bankroll/betting_systems.py`
- BankrollTracker ✅ - `src/let_it_ride/bankroll/tracker.py`

## Files to Create

- `src/let_it_ride/simulation/session.py` (~250 lines)
- `tests/unit/simulation/__init__.py`
- `tests/unit/simulation/test_session.py`

## Key Design Decisions

### 1. SessionConfig (frozen dataclass with slots)
Following the pattern from `BettingContext`, use `@dataclass(frozen=True, slots=True)` for:
- Memory efficiency (important for high-volume simulations)
- Thread safety (immutable configs can be shared)

### 2. StopReason Enum
```python
class StopReason(Enum):
    WIN_LIMIT = "win_limit"
    LOSS_LIMIT = "loss_limit"
    MAX_HANDS = "max_hands"
    INSUFFICIENT_FUNDS = "insufficient_funds"
    COMPLETED = "completed"  # Added for explicit completion
```

### 3. SessionOutcome Enum
```python
class SessionOutcome(Enum):
    WIN = "win"    # session_profit > 0
    LOSS = "loss"  # session_profit < 0
    PUSH = "push"  # session_profit == 0
```

### 4. SessionResult (frozen dataclass)
Captures the final state when a session completes.

### 5. Session Class Design

Key responsibilities:
- Owns the BankrollTracker (creates internally from config)
- Uses GameEngine for hand execution
- Uses BettingSystem for bet sizing
- Tracks streak for strategy context
- Accumulates statistics (hands played, total wagered)

The Session does NOT own:
- GameEngine (passed in - allows reuse across sessions)
- BettingSystem (passed in - allows different systems)

### 6. Bonus Strategy Consideration

The issue mentions `bonus_strategy: BonusStrategy` but no Protocol exists yet.
For this implementation, I'll use a simple approach:
- Accept an optional `bonus_bet: float = 0.0` in SessionConfig
- A proper BonusStrategy protocol can be added in a future issue

## Implementation Plan

### Phase 1: Types and Config
1. `StopReason` enum
2. `SessionOutcome` enum
3. `SessionConfig` frozen dataclass
4. `SessionResult` frozen dataclass

### Phase 2: Session Class Core
1. `__init__` - setup state, create BankrollTracker
2. Properties: `hands_played`, `is_complete`, `session_profit`, etc.
3. `_update_streak()` helper method

### Phase 3: Session Methods
1. `should_stop()` - check all stop conditions
2. `stop_reason()` - return why stopped (None if not stopped)
3. `play_hand()` - execute single hand, update state
4. `run_to_completion()` - loop until stop condition

### Phase 4: Tests
1. SessionConfig validation tests
2. Stop condition tests (win_limit, loss_limit, max_hands, insufficient_funds)
3. Session statistics accuracy tests
4. SessionResult correctness tests

## Code Patterns to Follow

From existing codebase:
- Frozen dataclasses for configs: `@dataclass(frozen=True, slots=True)`
- Use `__slots__` for regular classes with mutable state
- Type hints on all parameters and returns
- Docstrings with Args/Returns/Raises sections
- Import protocols from typing module

## Testing Strategy

Use pytest with class-based organization:
```python
class TestSessionConfig:
    def test_create_session_config(self) -> None: ...
    def test_session_config_is_frozen(self) -> None: ...

class TestStopConditions:
    def test_stop_on_win_limit(self) -> None: ...
    def test_stop_on_loss_limit(self) -> None: ...
    # etc.
```

Mock the GameEngine for deterministic testing.
