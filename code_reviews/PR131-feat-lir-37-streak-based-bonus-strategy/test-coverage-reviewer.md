# Test Coverage Review: PR #131 - LIR-37 Streak-Based Bonus Strategy

## Summary

The PR adds comprehensive unit tests for `StreakBasedBonusStrategy` with 48 new tests covering all trigger types, action types, reset behaviors, max_multiplier capping, and validation errors. The test suite follows good patterns with clear arrange-act-assert structure and descriptive names. However, critical gaps exist: there is no integration with the Session class (the `record_result()` method is never called by the simulation engine), no property-based testing for probability edge cases, and missing tests for concurrent streak tracking and trigger-reset conflict scenarios.

---

## Findings by Severity

### Critical

#### 1. Missing Integration: Session Does Not Call record_result()
**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py`
**Lines:** 328-385
**Impact:** The `StreakBasedBonusStrategy.record_result()` method is central to the strategy's functionality, but the `Session` class never calls it. The strategy will never update its streak state during actual simulation runs, rendering the strategy non-functional in production.

**Session.play_hand() at line 378-379:**
```python
# Record result in betting system
self._betting_system.record_result(result.net_result)
```

The session records results in the betting system but not in the bonus strategy. The `StreakBasedBonusStrategy` requires explicit `record_result()` calls to function.

**Recommendation:** Either:
1. Add integration test that verifies `record_result()` is called during session execution (and fix the Session class to call it), OR
2. Document that `StreakBasedBonusStrategy` is designed for manual use only and cannot be used with `SimulationController`

---

#### 2. Missing Integration Test: StreakBasedBonusStrategy with SimulationController
**File:** `/Users/chrishenry/source/let_it_ride/tests/e2e/test_full_simulation.py`
**Impact:** No end-to-end test validates the streak-based bonus strategy works in a real simulation. Given the missing `record_result()` integration above, an e2e test would immediately catch this gap.

**Recommendation:** Add integration test:
```python
def test_streak_based_bonus_strategy_in_simulation() -> None:
    """Verify streak-based bonus strategy updates during simulation."""
    config = create_e2e_config(
        num_sessions=10,
        hands_per_session=20,
        random_seed=42,
        workers=1,
    )
    # Override bonus strategy to streak_based
    # Verify streak state changes during session execution
```

---

### High

#### 3. Missing Test: Invalid Trigger Type String
**File:** `/Users/chrishenry/source/let_it_ride/tests/unit/strategy/test_bonus.py`
**Lines:** 1024-1059 (validation tests section)
**Impact:** The `trigger` parameter accepts a `str` but only certain values are valid. Invalid trigger strings like "invalid_trigger" will silently return `False` from `_matches_trigger()` without raising an error.

**Code Path (bonus.py:456-470):**
```python
def _matches_trigger(self, main_won: bool, bonus_won: bool | None) -> bool:
    if self._trigger == "main_win":
        return main_won
    # ... other valid triggers ...
    return False  # Silent failure for invalid trigger
```

**Recommendation:** Add test:
```python
def test_invalid_trigger_type_never_increments_streak(self) -> None:
    """Test that invalid trigger type never increments streak."""
    strategy = StreakBasedBonusStrategy(
        base_amount=5.0,
        trigger="invalid_trigger",  # Should this raise ValueError?
        streak_length=3,
        action_type="multiply",
        action_value=2.0,
        reset_on="main_win",
    )
    strategy.record_result(main_won=True, bonus_won=True)
    strategy.record_result(main_won=False, bonus_won=False)
    assert strategy.current_streak == 0  # Never increments
```

---

#### 4. Missing Test: Invalid Action Type String
**File:** `/Users/chrishenry/source/let_it_ride/tests/unit/strategy/test_bonus.py`
**Impact:** Similar to trigger, invalid `action_type` strings silently default to returning `_base_amount` in `_calculate_bet()`.

**Code Path (bonus.py:425-426):**
```python
# "stop" and "start" are handled in get_bonus_bet via _is_betting flag
return self._base_amount
```

**Recommendation:** Add test for behavior with invalid action type.

---

#### 5. Missing Test: Invalid reset_on Type String
**File:** `/Users/chrishenry/source/let_it_ride/tests/unit/strategy/test_bonus.py`
**Impact:** Invalid `reset_on` strings like "invalid" will silently return `False` from `_should_reset()`, meaning the streak never resets.

**Code Path (bonus.py:488):**
```python
return False  # Falls through for unknown reset_on values
```

**Recommendation:** Add test verifying behavior with invalid reset_on value.

---

#### 6. Missing Test: Trigger and Reset Same Event Conflict
**File:** `/Users/chrishenry/source/let_it_ride/tests/unit/strategy/test_bonus.py`
**Impact:** When `trigger` and `reset_on` are the same event (e.g., both "main_loss"), the code checks reset first (bonus.py:436), so the streak resets and never increments. This edge case behavior is not tested or documented.

**Code Path (bonus.py:434-447):**
```python
def record_result(self, main_won: bool, bonus_won: bool | None) -> None:
    # Check for reset condition first
    if self._should_reset(main_won, bonus_won):
        self._current_streak = 0
        # ...
        return  # <-- Never reaches _matches_trigger

    if self._matches_trigger(main_won, bonus_won):
        self._current_streak += 1
```

**Recommendation:** Add test:
```python
def test_same_trigger_and_reset_event_always_resets(self) -> None:
    """Test that when trigger and reset_on are same event, streak always resets."""
    strategy = StreakBasedBonusStrategy(
        base_amount=5.0,
        trigger="main_loss",
        streak_length=3,
        action_type="multiply",
        action_value=2.0,
        reset_on="main_loss",  # Same as trigger!
    )
    strategy.record_result(main_won=False, bonus_won=None)
    assert strategy.current_streak == 0  # Reset takes priority
    strategy.record_result(main_won=False, bonus_won=None)
    assert strategy.current_streak == 0  # Still 0
```

---

#### 7. Missing Test: action_value of Zero
**File:** `/Users/chrishenry/source/let_it_ride/tests/unit/strategy/test_bonus.py`
**Impact:** With `action_value=0.0` and `action_type="multiply"`, the result would be `base_amount * 0^n = 0`. With `action_type="increase"`, it would stay at base_amount. These behaviors are not explicitly tested.

**Recommendation:** Add tests for `action_value=0.0` with each action type.

---

#### 8. Missing Test: Negative action_value
**File:** `/Users/chrishenry/source/let_it_ride/tests/unit/strategy/test_bonus.py`
**Impact:** The constructor does not validate `action_value`. A negative value with "multiply" could cause unexpected behavior (negative bets clamped to 0). A negative value with "increase" would effectively decrease.

**Recommendation:** Add test or add validation:
```python
def test_negative_action_value_multiply(self, default_context: BonusContext) -> None:
    """Test behavior with negative action_value and multiply."""
    strategy = StreakBasedBonusStrategy(
        base_amount=5.0,
        trigger="main_loss",
        streak_length=1,
        action_type="multiply",
        action_value=-2.0,
        reset_on="never",
    )
    strategy.record_result(main_won=False, bonus_won=None)
    # base * (-2)^1 = -10, clamped to 0
    assert strategy.get_bonus_bet(default_context) == 0.0
```

---

### Medium

#### 9. Missing Test: any_loss and any_win with bonus_won=None
**File:** `/Users/chrishenry/source/let_it_ride/tests/unit/strategy/test_bonus.py`
**Lines:** 1070-1102 (test_any_loss_trigger, test_any_win_trigger)
**Impact:** Tests exist for `any_loss` and `any_win` triggers, but none explicitly test the case where `bonus_won=None` (no bonus bet placed). The logic `bonus_won is True` and `bonus_won is False` behave differently than `bonus_won is None`.

**Code Path (bonus.py:466-469):**
```python
if self._trigger == "any_win":
    return main_won or bonus_won is True  # bonus_won=None returns False
if self._trigger == "any_loss":
    return not main_won or bonus_won is False  # bonus_won=None returns False
```

**Recommendation:** Add explicit tests:
```python
def test_any_win_with_no_bonus_bet(self) -> None:
    """Test any_win trigger with bonus_won=None."""
    strategy = StreakBasedBonusStrategy(
        base_amount=5.0,
        trigger="any_win",
        streak_length=1,
        action_type="multiply",
        action_value=2.0,
        reset_on="never",
    )
    strategy.record_result(main_won=False, bonus_won=None)
    assert strategy.current_streak == 0  # No bonus, main lost
```

---

#### 10. Missing Test: Very Large Streak Length
**File:** `/Users/chrishenry/source/let_it_ride/tests/unit/strategy/test_bonus.py`
**Impact:** No test for `streak_length` with very large values (e.g., 1000000). While unlikely in practice, could reveal integer overflow or performance issues.

**Recommendation:** Add boundary test with large streak_length.

---

#### 11. Missing Test: Multiple Trigger Activations in Single Call
**File:** `/Users/chrishenry/source/let_it_ride/tests/unit/strategy/test_bonus.py`
**Impact:** With `any_loss` trigger, both main loss AND bonus loss in the same hand should only increment the streak by 1, not 2. This is currently untested.

**Code Path (bonus.py:468-469):**
```python
if self._trigger == "any_loss":
    return not main_won or bonus_won is False  # OR, not counting separately
```

**Recommendation:** Add test:
```python
def test_any_loss_both_lose_increments_once(self) -> None:
    """Test any_loss with both main and bonus loss only increments once."""
    strategy = StreakBasedBonusStrategy(
        base_amount=5.0,
        trigger="any_loss",
        streak_length=2,
        action_type="multiply",
        action_value=2.0,
        reset_on="never",
    )
    strategy.record_result(main_won=False, bonus_won=False)  # Both lose
    assert strategy.current_streak == 1  # Only +1, not +2
```

---

#### 12. Missing Property-Based Test: Streak Monotonicity
**File:** `/Users/chrishenry/source/let_it_ride/tests/unit/strategy/test_bonus.py`
**Impact:** No property-based tests using hypothesis library to verify invariants like: "streak should never go negative" or "streak should only increase when trigger matches".

**Recommendation:** Add hypothesis tests:
```python
from hypothesis import given, strategies as st

@given(
    wins=st.lists(st.booleans(), min_size=1, max_size=100)
)
def test_streak_never_negative(self, wins: list[bool]) -> None:
    """Property: streak counter should never be negative."""
    strategy = StreakBasedBonusStrategy(
        base_amount=5.0,
        trigger="main_win",
        streak_length=3,
        action_type="multiply",
        action_value=2.0,
        reset_on="main_loss",
    )
    for won in wins:
        strategy.record_result(main_won=won, bonus_won=None)
        assert strategy.current_streak >= 0
```

---

#### 13. Missing Test: current_multiplier for stop/start Actions
**File:** `/Users/chrishenry/source/let_it_ride/tests/unit/strategy/test_bonus.py`
**Lines:** 1269-1331 (TestStreakBasedBonusStrategyMultiplierCalculations)
**Impact:** Tests exist for multiply, increase, decrease actions but not for stop/start. The `current_multiplier` property returns `1.0` for these (bonus.py:531), which is tested implicitly but not explicitly.

**Code Path (bonus.py:531):**
```python
return 1.0  # Default for stop/start
```

**Recommendation:** Add explicit test:
```python
def test_multiplier_for_stop_action_is_one(self) -> None:
    """Test current_multiplier is 1.0 for stop action."""
    strategy = StreakBasedBonusStrategy(
        base_amount=5.0,
        trigger="main_loss",
        streak_length=2,
        action_type="stop",
        action_value=0.0,
        reset_on="never",
    )
    for _ in range(5):
        strategy.record_result(main_won=False, bonus_won=None)
    assert strategy.current_multiplier == 1.0
```

---

#### 14. Missing Test: Factory with Config Model Validation
**File:** `/Users/chrishenry/source/let_it_ride/tests/unit/strategy/test_bonus.py`
**Lines:** 1097-1167 (TestStreakBasedBonusStrategyFactory)
**Impact:** Tests use manually constructed `StreakBasedBonusConfig` but do not test that invalid config values are caught by Pydantic validation before reaching the strategy.

**Recommendation:** Add test verifying Pydantic validation:
```python
def test_config_validation_rejects_invalid_trigger(self) -> None:
    """Test that StreakBasedBonusConfig rejects invalid trigger values."""
    with pytest.raises(ValidationError):
        StreakBasedBonusConfig(
            base_amount=5.0,
            trigger="invalid_trigger",  # Not in Literal
            streak_length=3,
            action=StreakActionConfig(type="multiply", value=2.0),
            reset_on="main_win",
        )
```

---

#### 15. Missing Test: State Persistence Across Multiple get_bonus_bet Calls
**File:** `/Users/chrishenry/source/let_it_ride/tests/unit/strategy/test_bonus.py`
**Impact:** No test verifies that calling `get_bonus_bet()` multiple times without calling `record_result()` returns consistent values (i.e., `get_bonus_bet` is pure and does not modify state).

**Recommendation:** Add test:
```python
def test_get_bonus_bet_is_pure(self, default_context: BonusContext) -> None:
    """Test that get_bonus_bet does not modify state."""
    strategy = StreakBasedBonusStrategy(
        base_amount=5.0,
        trigger="main_loss",
        streak_length=2,
        action_type="multiply",
        action_value=2.0,
        reset_on="never",
    )
    strategy.record_result(main_won=False, bonus_won=None)
    strategy.record_result(main_won=False, bonus_won=None)

    result1 = strategy.get_bonus_bet(default_context)
    result2 = strategy.get_bonus_bet(default_context)
    result3 = strategy.get_bonus_bet(default_context)

    assert result1 == result2 == result3
    assert strategy.current_streak == 2  # Unchanged
```

---

## Coverage Summary

| Component | Tests | Coverage Assessment |
|-----------|-------|---------------------|
| StreakBasedBonusStrategy - Triggers | 6 | Good - all trigger types tested |
| StreakBasedBonusStrategy - Actions | 8 | Good - all action types tested |
| StreakBasedBonusStrategy - Reset | 9 | Good - all reset_on values tested |
| StreakBasedBonusStrategy - Validation | 3 | Moderate - missing invalid string tests |
| StreakBasedBonusStrategy - Max Multiplier | 3 | Good |
| StreakBasedBonusStrategy - Clamping | 2 | Good |
| Factory - streak_based | 3 | Good |
| Protocol Conformance | 4 | Good |
| Multiplier Calculations | 5 | Good - missing stop/start |
| Integration with Session | 0 | **Missing** |
| E2E with SimulationController | 0 | **Missing** |
| Property-Based Tests | 0 | **Missing** |

**Total New Tests:** 48
**Estimated Missing Critical Tests:** 2 (Session integration, E2E test)
**Estimated Missing High Tests:** 6
**Estimated Missing Medium Tests:** 7

---

## Recommendations Summary

### Priority 1 (Critical - Should Block Merge)
1. Add integration test verifying `record_result()` is called during session execution
2. Fix `Session` class to call `bonus_strategy.record_result()` after each hand, OR document that StreakBasedBonusStrategy cannot be used with SimulationController

### Priority 2 (High - Should Add Before Merge)
3. Test invalid trigger/action_type/reset_on string values
4. Test trigger == reset_on conflict scenario
5. Test action_value of 0 and negative values
6. Test any_loss/any_win with bonus_won=None explicitly

### Priority 3 (Medium - Should Add Soon)
7. Add property-based tests with hypothesis for invariant verification
8. Test multiple trigger activations in single call
9. Test current_multiplier for stop/start actions
10. Test state purity of get_bonus_bet()
11. Add Pydantic validation tests for config

---

## Code Quality Notes

The test file is well-organized with separate test classes for different aspects:
- `TestStreakBasedBonusStrategy` - Core functionality
- `TestStreakBasedBonusStrategyFactory` - Factory creation
- `TestStreakBasedBonusStrategyProtocolConformance` - Protocol compliance
- `TestStreakBasedBonusStrategyMultiplierCalculations` - Property calculations

Test names are descriptive and follow good patterns. The use of fixtures is appropriate but could be reduced by using parameterized tests more extensively.

The most significant gap is the lack of integration testing - the unit tests thoroughly validate the strategy in isolation, but never verify it works within the actual simulation pipeline.
