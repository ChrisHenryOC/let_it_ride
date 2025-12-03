# LIR-16: Flat Betting System

Issue: https://github.com/ChrisHenryOC/let_it_ride/issues/19

## Overview

Implement the flat (constant) betting system as the baseline, plus the betting system protocol.

## Dependencies (Completed)

- LIR-12: Custom Strategy Configuration Parser (GitHub #15) - CLOSED

## Existing Code Analysis

The `BankrollTracker` class already exists in `src/let_it_ride/bankroll/tracker.py` with:
- Balance tracking
- Peak balance (high water mark)
- Drawdown calculations
- Session profit

The `StrategyContext` dataclass in `src/let_it_ride/strategy/base.py` has similar fields:
- `session_profit`, `hands_played`, `streak`, `bankroll`

This issue creates a new `BettingContext` dataclass specifically for betting systems.

## Implementation Plan

### 1. Create betting_systems.py

**File**: `src/let_it_ride/bankroll/betting_systems.py`

#### BettingContext Dataclass

```python
@dataclass
class BettingContext:
    bankroll: float           # Current bankroll
    starting_bankroll: float  # Starting bankroll
    session_profit: float     # Current profit/loss
    last_result: float | None # Last hand result (None if first hand)
    streak: int               # Positive = wins, negative = losses
    hands_played: int         # Number of hands played
```

#### BettingSystem Protocol

```python
class BettingSystem(Protocol):
    def get_bet(self, context: BettingContext) -> float
        """Return bet amount given current context. Should not exceed bankroll."""

    def record_result(self, result: float) -> None
        """Record the result of a hand for systems that track state."""

    def reset(self) -> None
        """Reset system state for a new session."""
```

#### FlatBetting Implementation

```python
class FlatBetting:
    def __init__(self, base_bet: float) -> None
        """Initialize with base bet amount."""

    def get_bet(self, context: BettingContext) -> float
        """Return base bet, reduced if bankroll insufficient."""
        # If bankroll < base_bet, return max(0, bankroll)
        # If bankroll >= base_bet, return base_bet

    def record_result(self, result: float) -> None
        """No-op for flat betting (no state to track)."""

    def reset(self) -> None
        """No-op for flat betting (no state to reset)."""
```

### 2. Key Design Decisions

1. **Bet capping**: If bankroll is less than base bet, return remaining bankroll (not 0).
   - Allows playing final hands with reduced bets
   - Returns 0 only if bankroll is 0 or negative

2. **Validation**: Base bet must be positive (> 0)

3. **Stateless**: FlatBetting doesn't need to track results or streak internally

4. **Protocol design**: Methods match the signature in the issue spec exactly

### 3. Unit Tests

**File**: `tests/unit/bankroll/test_betting_systems.py`

Test categories:
- **BettingContext**: Creation with various values
- **FlatBetting initialization**: Valid base bet, invalid (zero/negative)
- **FlatBetting.get_bet() normal**: Returns base bet when bankroll sufficient
- **FlatBetting.get_bet() reduced**: Returns bankroll when less than base bet
- **FlatBetting.get_bet() zero**: Returns 0 when bankroll is 0 or negative
- **FlatBetting.record_result()**: No-op verification
- **FlatBetting.reset()**: No-op verification

## Acceptance Criteria Checklist

- [ ] `BettingSystem` protocol definition
- [ ] `BettingContext` dataclass with bankroll state info
- [ ] `FlatBetting` implementation returning constant base bet
- [ ] Validation that bet does not exceed available bankroll
- [ ] Returns reduced bet if bankroll insufficient for full bet
- [ ] Unit tests for normal operation
- [ ] Unit tests for insufficient bankroll scenarios
