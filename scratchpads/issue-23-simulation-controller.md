# LIR-20: Simulation Controller (Sequential)

**GitHub Issue:** #23
**Status:** In Progress

## Overview

Implement the main simulation controller for running multiple sessions sequentially.

## Acceptance Criteria

- [x] `SimulationController` class orchestrating session execution
- [x] `run()` method executing configured number of sessions
- [x] Progress reporting via callback function
- [x] Results aggregation into `SimulationResults`
- [x] Support for seeded RNG ensuring reproducibility
- [x] Session isolation (each session gets fresh state)
- [ ] Integration tests for multi-session runs
- [ ] Test that same seed produces identical results

## Dependencies

- Session management (LIR-18): Complete
- TableSession (LIR-43/GitHub #73): Complete - but controller focuses on single-player Session first

## Files to Create

1. `src/let_it_ride/simulation/controller.py`
2. `tests/integration/test_controller.py`

## Implementation Plan

### 1. SimulationResults Dataclass

```python
@dataclass(frozen=True)
class SimulationResults:
    config: FullConfig
    session_results: list[SessionResult]
    start_time: datetime
    end_time: datetime
    total_hands: int
```

### 2. SimulationController Class

Key methods:
- `__init__(config: FullConfig, progress_callback: ProgressCallback | None = None)`
- `run() -> SimulationResults` - main entry point
- `_create_session(session_id: int, rng: random.Random) -> Session` - factory method
- `_run_session(session: Session) -> SessionResult` - executes a single session

### 3. Strategy Instantiation

Need a factory function `create_strategy(config: StrategyConfig) -> Strategy`:
- `basic` -> BasicStrategy()
- `always_ride` -> AlwaysRideStrategy()
- `always_pull` -> AlwaysPullStrategy()
- `conservative` -> conservative_strategy()
- `aggressive` -> aggressive_strategy()
- `custom` -> CustomStrategy(config.custom.bet1_rules, config.custom.bet2_rules)

### 4. Betting System Instantiation

Need a factory function `create_betting_system(config: BankrollConfig) -> BettingSystem`:
- `flat` -> FlatBetting(base_bet)
- `martingale` -> MartingaleBetting(...)
- `paroli` -> ParoliBetting(...)
- `dalembert` -> DAlembertBetting(...)
- `fibonacci` -> FibonacciBetting(...)
- `reverse_martingale` -> ReverseMartingaleBetting(...)

### 5. RNG Seeding Strategy

- If `config.simulation.random_seed` is provided, use it as base
- Derive session seeds: `base_seed + session_id` for reproducibility
- Each session gets its own RNG instance to ensure isolation

### 6. Progress Callback

```python
ProgressCallback = Callable[[int, int], None]  # (completed, total)
```

Called after each session completes.

## Testing Plan

### Integration Tests (`tests/integration/test_controller.py`)

1. **test_run_single_session**: Run 1 session, verify result structure
2. **test_run_multiple_sessions**: Run 10 sessions, verify aggregation
3. **test_reproducibility_with_seed**: Same seed = identical results
4. **test_different_seeds_different_results**: Different seeds differ
5. **test_progress_callback**: Verify callback is called with correct values
6. **test_session_isolation**: Each session starts fresh
7. **test_total_hands_aggregation**: Verify total_hands sums correctly
8. **test_timing_recorded**: start_time < end_time

## Notes

- Focus on single-player Session first
- TableSession multi-player support can be added later via `config.table.num_seats`
- Controller should work with existing SessionConfig conversion from FullConfig
