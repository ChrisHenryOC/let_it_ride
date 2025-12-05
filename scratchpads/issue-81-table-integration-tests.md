# LIR-45: Table Integration Tests

**GitHub Issue**: #81
**Status**: In Progress

## Summary

Add integration tests for the `Table` class to verify correct interaction with Session management, various strategies, and bankroll tracking.

## Acceptance Criteria

- [x] Integration tests for Table + Session management
- [x] Tests for Table with different strategy types:
  - BasicStrategy
  - AlwaysRideStrategy / AlwaysPullStrategy
  - CustomStrategy with seat-specific conditions
- [x] Multi-round table gameplay tests with bankroll tracking
- [x] Verify Table integrates correctly with future simulation infrastructure

## Context

The Table class (from LIR-42) has comprehensive unit tests but lacks integration tests. The TableSession class (from LIR-43) also has unit tests, but we need integration tests that verify the full flow with real components (not mocks).

## Test Plan

### 1. Table + TableSession Integration
- Test complete TableSession lifecycle with real Table
- Verify session tracking works correctly with multi-seat tables
- Test win/loss limit triggering with actual gameplay

### 2. Strategy Integration Tests
- **BasicStrategy**: Verify it integrates correctly and produces expected decision patterns
- **AlwaysRideStrategy**: Verify all bets ride (max variance behavior)
- **AlwaysPullStrategy**: Verify all bets pull (min variance behavior)
- **CustomStrategy**: Verify rule-based decisions work with Table

### 3. Multi-Round Bankroll Tracking
- Test bankroll accumulation over multiple rounds
- Verify peak_bankroll and max_drawdown tracking with real gameplay
- Test session profit/loss calculation accuracy

### 4. Simulation Infrastructure Integration
- Verify Table/TableSession works with the simulation patterns
- Test reproducibility with seeded RNG
- Verify bonus bet handling across multi-seat tables

## Files to Create

- `tests/integration/test_table.py`
