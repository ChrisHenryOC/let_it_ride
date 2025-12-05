# LIR-43: Multi-Player Session Management

GitHub Issue: https://github.com/ChrisHenryOC/let_it_ride/issues/73

## Overview

Implement `TableSession` that manages bankrolls and stop conditions for multiple players at a table.

## Dependencies

- LIR-42 (Table Abstraction) - COMPLETE (PR #80)
- LIR-18 (Session State Management) - COMPLETE

## Key Design Decisions

### 1. Per-Seat State Management

Each seat needs independent:
- `BankrollTracker` for balance/peak/drawdown
- Stop condition tracking (win_limit, loss_limit, max_hands, insufficient_funds)
- Streak tracking for BettingContext
- Last result tracking

### 2. BettingSystem Handling

The issue shows a single `betting_system` parameter. Options:
- **Option A**: Clone the betting system for each seat (requires protocol extension)
- **Option B**: Create fresh instances for each seat (requires a factory)
- **Option C**: Share one betting system across all seats (simpler but not realistic)

Decision: Option C for now - share one betting system. This matches the "same strategy" approach of Table. Progressive betting systems will behave as if the seats are one player. This keeps it simple and matches backwards compatibility requirements.

### 3. Session End Condition

Issue says: "Session ends when all seats hit stop conditions (or configurable subset)"

Options:
- `all_seats`: Wait until every seat has hit a stop condition
- `any_seat`: Stop when any single seat hits a stop condition
- `first_n_seats`: Stop when N seats hit stop conditions

Decision: Implement `all_seats` as default (all seats must stop). Add optional `stop_mode` parameter for future extensibility.

### 4. Stop Reason Aggregation

When session ends, we need a single `StopReason` for the table.
- Use the reason from the last seat to trigger the session stop
- Or use most common reason

Decision: Use last-triggered reason (simplest, mirrors single-seat behavior).

## Data Structures

```python
@dataclass(frozen=True, slots=True)
class TableSessionConfig:
    """Configuration for a multi-player table session."""
    table_config: TableConfig
    starting_bankroll: float  # Same for all seats
    base_bet: float
    win_limit: float | None = None
    loss_limit: float | None = None
    max_hands: int | None = None
    stop_on_insufficient_funds: bool = True
    bonus_bet: float = 0.0

@dataclass(frozen=True, slots=True)
class SeatSessionResult:
    """Result for a single seat in a table session."""
    seat_number: int
    session_result: SessionResult

@dataclass(frozen=True, slots=True)
class TableSessionResult:
    """Complete results of a finished table session."""
    seat_results: tuple[SeatSessionResult, ...]
    total_rounds: int
    stop_reason: StopReason
```

## Class Design

```python
class TableSession:
    """Manages a multi-player Let It Ride table session."""

    __slots__ = (
        "_config",
        "_table",
        "_betting_system",
        "_seat_states",  # List of per-seat state
        "_rounds_played",
        "_stop_reason",
    )
```

### SeatState (internal class)

Per-seat state tracking:
```python
@dataclass
class _SeatState:
    """Internal state for a single seat."""
    bankroll: BankrollTracker
    total_wagered: float = 0.0
    total_bonus_wagered: float = 0.0
    last_result: float | None = None
    streak: int = 0
    stop_reason: StopReason | None = None
```

## Implementation Plan

1. Create `table_session.py` with:
   - `TableSessionConfig` dataclass
   - `SeatSessionResult` dataclass
   - `TableSessionResult` dataclass
   - `_SeatState` internal class
   - `TableSession` class

2. Methods:
   - `__init__`: Initialize per-seat states
   - `play_round`: Play one round for all seats, update states
   - `should_stop`: Check if table session should stop
   - `_check_seat_stop_condition`: Per-seat stop checking
   - `run_to_completion`: Run until stopped
   - Properties: `rounds_played`, `is_complete`

3. Backwards compatibility:
   - Single seat (num_seats=1) should produce same results as Session
   - Same stop condition logic
   - Same result structure per seat

## Testing Plan

1. **Configuration tests**
   - Valid configuration acceptance
   - Invalid configuration rejection
   - Validation of stop conditions

2. **Single-seat equivalence**
   - Same bankroll progression
   - Same stop conditions triggered
   - Same results structure

3. **Multi-seat functionality**
   - Independent bankroll tracking
   - Independent stop conditions
   - Correct round counting
   - Results aggregation

4. **Stop condition tests**
   - All seats reaching conditions
   - Mixed stop conditions per seat
   - Insufficient funds handling

## Files

- Create: `src/let_it_ride/simulation/table_session.py`
- Create: `tests/unit/simulation/test_table_session.py`
- Modify: `src/let_it_ride/simulation/__init__.py` (export new types)
