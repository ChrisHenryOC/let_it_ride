# LIR-15: Bankroll Tracker

Issue: https://github.com/ChrisHenryOC/let_it_ride/issues/18

## Overview

Implement bankroll tracking with high water mark and drawdown calculation.

## Dependencies (Completed)

- LIR-1: Project Scaffolding - provides the bankroll module structure

## Implementation Plan

### 1. Create BankrollTracker class

**File**: `src/let_it_ride/bankroll/tracker.py`

Key design decisions:
- `BankrollTracker` initialized with starting amount (float)
- `apply_result()` method updates balance and tracks metrics
- Properties for current state: `balance`, `peak_balance`, `session_profit`
- Drawdown calculations: `max_drawdown`, `max_drawdown_pct`, `current_drawdown`
- History tracking via `history` property returning list of balances

### 2. Core Properties and Methods

```python
class BankrollTracker:
    def __init__(self, starting_amount: float) -> None
        """Initialize tracker with starting bankroll."""

    def apply_result(self, amount: float) -> None
        """Apply hand result (positive = win, negative = loss)."""

    @property
    def balance(self) -> float
        """Current bankroll balance."""

    @property
    def starting_balance(self) -> float
        """Original starting balance."""

    @property
    def session_profit(self) -> float
        """Current balance - starting balance."""

    @property
    def peak_balance(self) -> float
        """Highest balance achieved (high water mark)."""

    @property
    def max_drawdown(self) -> float
        """Largest peak-to-trough decline as absolute value."""

    @property
    def max_drawdown_pct(self) -> float
        """Largest peak-to-trough decline as percentage of peak."""

    @property
    def current_drawdown(self) -> float
        """Current decline from peak (0 if at or above peak)."""

    @property
    def history(self) -> list[float]
        """Balance after each transaction (copy of internal list)."""
```

### 3. Implementation Details

**Balance tracking:**
- Store starting amount as immutable property
- Track current balance as internal float
- Update after each `apply_result()` call

**Peak tracking:**
- Initialize peak to starting amount
- Update peak after each positive balance change
- Peak = max(peak, current_balance)

**Drawdown calculations:**
- Current drawdown = peak - current balance (if positive, else 0)
- Max drawdown = largest current drawdown ever observed
- Max drawdown pct = max_drawdown / peak_at_max_drawdown * 100

**History:**
- List of balances after each transaction
- Return copy to prevent external modification

### 4. Edge Cases

- Zero starting amount: Should work (unusual but valid)
- Negative starting amount: Should raise ValueError
- Large wins/losses: Handle properly with float arithmetic
- No transactions: history is empty, all metrics based on starting amount

### 5. Unit Tests

**File**: `tests/unit/bankroll/test_tracker.py`

Test categories:
- Initialization tests
- Balance tracking (wins, losses, breakeven)
- Peak balance tracking
- Drawdown calculations (max and current)
- Session profit calculation
- History tracking
- Edge cases and error conditions

## File Structure

```
src/let_it_ride/bankroll/
├── __init__.py        # Update exports
└── tracker.py         # NEW - BankrollTracker

tests/unit/bankroll/
├── __init__.py        # NEW
└── test_tracker.py    # NEW
```

## Acceptance Criteria Checklist

- [ ] `BankrollTracker` class initialized with starting amount
- [ ] `apply_result()` method updating balance
- [ ] `balance` property for current bankroll
- [ ] `peak_balance` (high water mark) tracking
- [ ] `max_drawdown` calculation (largest decline from peak)
- [ ] `current_drawdown` (current decline from peak)
- [ ] `history` property returning balance after each hand
- [ ] `session_profit` property (current - starting)
- [ ] Unit tests for all tracking scenarios
- [ ] Tests for drawdown calculation accuracy
