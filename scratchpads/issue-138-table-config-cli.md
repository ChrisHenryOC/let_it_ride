# LIR-56: Table Configuration Integration with CLI

GitHub Issue: https://github.com/ChrisHenryOC/let_it_ride/issues/138

## Overview

Add `table` configuration section to `FullConfig` and integrate `TableSession` with the CLI so users can run multi-seat simulations via YAML configuration.

## Dependencies (All Complete)

- LIR-42 (Table Abstraction)
- LIR-43 (Multi-Player Session Management)
- LIR-31 (CLI Entry Point)

## Implementation Tasks

1. Add `table: TableConfig` field to `FullConfig` in models.py
2. Update CLI `run` command to use `TableSession` when `num_seats > 1`
3. Update `SimulationController` to support `TableSession`
4. Update `validate` command to show table configuration
5. Add per-seat breakdown to results output
6. Create sample multi-seat configuration file
7. Write unit tests for table config loading
8. Write integration tests for multi-seat CLI runs
9. Update documentation

## Key Design Decisions

### 1. Controller Integration

Option A: Modify `SimulationController._create_session()` to return either `Session` or `TableSession`
Option B: Create separate `_create_table_session()` method
Option C: Create factory function in utils.py

**Decision**: Option A - Minimal changes, conditional logic based on `num_seats`

### 2. Result Aggregation

For multi-seat tables, we need to aggregate `TableSessionResult` into stats.
- Each `TableSessionResult` contains multiple `SeatSessionResult` objects
- Statistics should be computed per-seat and aggregated

### 3. Backwards Compatibility

- Default `num_seats=1` preserves existing behavior
- Single-seat runs use existing `Session` for efficiency
- All existing configs work without modification

## Files to Modify

- `src/let_it_ride/config/models.py` - Add `table` to `FullConfig`
- `src/let_it_ride/simulation/controller.py` - Support `TableSession`
- `src/let_it_ride/simulation/utils.py` - Add `create_table_session_config()`
- `src/let_it_ride/cli/app.py` - Update run/validate commands
- `src/let_it_ride/cli/formatters.py` - Add per-seat output formatting

## Files to Create

- `configs/multi_seat_example.yaml` - Sample multi-seat configuration
- `tests/unit/config/test_table_config.py` - Unit tests for table config
