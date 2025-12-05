# Test Coverage Review: PR #88 - LIR-43 Multi-Player Session Management

## Summary

The test suite for TableSession is comprehensive with good coverage of configuration validation, single-seat equivalence, multi-seat functionality, and state management. However, there are several gaps in edge case coverage, missing tests for the internal `_SeatState` class, and opportunities for property-based testing. The tests follow good practices (arrange-act-assert, clear naming, appropriate mocking) but would benefit from additional integration tests with progressive betting systems.

## Findings by Severity

### High Priority

#### 1. Missing Tests for `_SeatState.update_streak()` Edge Cases
**File:** `src/let_it_ride/simulation/table_session.py` (lines 357-375)
**Issue:** The `_SeatState.update_streak()` method is tested indirectly through `TableSession` but lacks direct unit tests. The streak logic for push (result == 0) during various streak states is not explicitly verified.

**Recommendation:** Add direct tests for `_SeatState`:
```python
class TestSeatStateStreakTracking:
    def test_streak_win_after_loss(self) -> None:
        """Verify streak resets to +1 after a loss."""
        state = _SeatState(1000.0)
        state.update_streak(-50.0)  # -1
        state.update_streak(50.0)   # Should be +1
        assert state.streak == 1

    def test_push_preserves_negative_streak(self) -> None:
        """Verify push does not reset negative streak."""
        state = _SeatState(1000.0)
        state.update_streak(-50.0)
        state.update_streak(-50.0)  # -2
        state.update_streak(0.0)    # Push
        assert state.streak == -2
```

#### 2. Missing Test for Stopped Seat Behavior During Rounds
**File:** `src/let_it_ride/simulation/table_session.py` (lines 583-589)
**Issue:** The logic that skips stopped seats during `play_round()` is not explicitly tested. The test `test_multi_seat_waits_for_all_to_stop` partially covers this, but does not verify that stopped seats are not updated with results from subsequent rounds.

**Recommendation:** Add test verifying stopped seats are not modified:
```python
def test_stopped_seat_not_updated_in_subsequent_rounds(self) -> None:
    """Verify stopped seats do not receive updates from rounds after stopping."""
    # Seat 1 stops after round 1, verify its final_bankroll doesn't change
```

#### 3. No Tests for `total_bonus_wagered` Tracking in Multi-Seat
**File:** `tests/unit/simulation/test_table_session.py`
**Issue:** While `total_wagered` is tested via `test_total_wagered_tracked`, there are no tests verifying `total_bonus_wagered` is correctly accumulated per-seat when `bonus_bet > 0`.

**Recommendation:** Add test:
```python
def test_total_bonus_wagered_tracked_per_seat(self) -> None:
    """Verify total_bonus_wagered is accumulated correctly for each seat."""
    config = TableSessionConfig(
        table_config=TableConfig(num_seats=2),
        starting_bankroll=1000.0,
        base_bet=25.0,
        bonus_bet=5.0,
        max_hands=3,
    )
    # ... verify seat_results[i].session_result.total_bonus_wagered == 15.0
```

### Medium Priority

#### 4. Missing Test for Betting System `reset()` Being Called
**File:** `src/let_it_ride/simulation/table_session.py` (line 430)
**Issue:** The constructor calls `self._betting_system.reset()` but no test verifies this behavior.

**Recommendation:** Add test with a mock betting system to verify `reset()` is called on initialization.

#### 5. No Tests for `max_drawdown_pct` in TableSession
**File:** `tests/unit/simulation/test_table_session.py`
**Issue:** `test_max_drawdown_tracked` exists but there's no test for `max_drawdown_pct` accuracy in the TableSession context.

**Recommendation:** Add test similar to `test_max_drawdown_percentage` in test_session.py:
```python
def test_max_drawdown_percentage_tracked(self) -> None:
    """Verify max drawdown percentage is calculated correctly per seat."""
```

#### 6. Missing Test for `StopReason` Selection When Multiple Seats Stop Simultaneously
**File:** `src/let_it_ride/simulation/table_session.py` (lines 519-527)
**Issue:** The code uses `reversed()` to find the last seat's stop reason, but no test verifies behavior when all seats stop in the same round with the same reason.

**Recommendation:** Add test:
```python
def test_stop_reason_when_all_seats_stop_simultaneously(self) -> None:
    """Verify stop_reason selection when all seats hit max_hands together."""
```

#### 7. No Test for Progressive Betting System Integration
**File:** `tests/unit/simulation/test_table_session.py`
**Issue:** All tests use `FlatBetting`. The design decision states betting system is shared across seats, but there's no test verifying this behavior with a progressive system like `MartingaleBetting`.

**Recommendation:** Add integration test:
```python
def test_shared_betting_system_with_martingale(self) -> None:
    """Verify progressive betting system is shared correctly across seats."""
    # Use MartingaleBetting and verify all seats use the same progression
```

### Low Priority

#### 8. Missing Test for `TableConfig` with Maximum Seats (6)
**File:** `tests/unit/simulation/test_table_session.py`
**Issue:** Tests cover 1-4 seats but not the maximum of 6 seats as mentioned in `PlayerSeat` docstring.

**Recommendation:** Add boundary test with `num_seats=6`.

#### 9. No Test for Exact Win/Loss Limit Boundary with Floating Point
**File:** `tests/unit/simulation/test_table_session.py`
**Issue:** Unlike `test_session.py`, the TableSession tests don't verify behavior with floating-point edge cases near limits.

**Recommendation:** Consider adding:
```python
def test_win_limit_floating_point_boundary(self) -> None:
    """Verify win limit check handles floating-point precision."""
```

#### 10. Missing Property-Based Tests for Statistical Properties
**Issue:** The simulation-specific testing guidelines suggest using hypothesis for property-based testing, which would be valuable for verifying:
- Seat results sum to expected total
- Independent bankroll tracking properties
- Stop condition invariants

## Specific Recommendations with File/Line References

| Finding | File | Line | Priority |
|---------|------|------|----------|
| _SeatState direct tests | table_session.py | 328-380 | High |
| Stopped seat skip verification | table_session.py | 588 | High |
| total_bonus_wagered tracking | test_table_session.py | - | High |
| betting_system.reset() called | table_session.py | 430 | Medium |
| max_drawdown_pct verification | test_table_session.py | - | Medium |
| Simultaneous stop handling | table_session.py | 523-527 | Medium |
| Progressive betting integration | test_table_session.py | - | Medium |
| 6-seat boundary test | test_table_session.py | - | Low |

## Test Quality Assessment

### Strengths
1. **Clear test organization**: Tests are well-organized into logical classes by feature area
2. **Good use of fixtures**: The `create_mock_table()` helper is well-designed and reusable
3. **Comprehensive validation tests**: All config validation paths are covered
4. **Integration tests present**: Tests with real `Table` and components exist
5. **Consistent naming**: Test names clearly describe expected behavior
6. **Appropriate assertions**: Tests verify specific values, not just type checks

### Areas for Improvement
1. **Mock verification**: Mocks are created but their call patterns are not always verified
2. **Edge case coverage**: Floating-point boundaries and extreme values need more testing
3. **Error message testing**: Tests verify exceptions are raised but don't always check message content
4. **Determinism**: Integration tests use `rng` fixture but could benefit from more seed variations

## Summary Statistics

- **New production lines**: ~450 lines in `table_session.py`
- **New test lines**: ~817 lines in `test_table_session.py`
- **Test-to-code ratio**: ~1.8:1 (good coverage)
- **Test classes**: 12
- **Test methods**: 42
- **Estimated coverage**: ~85-90% line coverage (gaps in _SeatState, some edge cases)
