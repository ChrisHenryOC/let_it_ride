# Test Coverage Review: PR #85 - Extract Shared Hand Processing Logic (LIR-46)

## Summary

This refactoring PR extracts duplicated hand processing logic from `GameEngine.play_hand()` and `Table._process_seat()` into a shared `process_hand_decisions_and_payouts()` function in a new `hand_processing.py` module. While the existing integration tests for `GameEngine` and `Table` provide indirect coverage of the extracted logic, there are **no direct unit tests for the new `hand_processing.py` module**. This is a significant coverage gap for a core module that handles critical game logic.

## Findings by Severity

### High

#### H1: Missing Unit Tests for `hand_processing.py` Module
- **Location**: `src/let_it_ride/core/hand_processing.py` (entire file - lines 203-334 in diff)
- **Issue**: The new `HandProcessingResult` dataclass and `process_hand_decisions_and_payouts()` function have no dedicated unit tests. The module is only tested indirectly through `GameEngine` and `Table` integration tests.
- **Risk**:
  - Future modifications to `hand_processing.py` may introduce bugs not caught by integration tests
  - Edge cases specific to the processing logic are not explicitly verified
  - The dataclass's `frozen=True` and `slots=True` behavior is not tested
- **Recommendation**: Create `tests/unit/core/test_hand_processing.py` with dedicated tests for:
  1. `HandProcessingResult` dataclass immutability and field access
  2. `process_hand_decisions_and_payouts()` with controlled card inputs and mock strategy
  3. All four bet decision combinations (RIDE/RIDE, RIDE/PULL, PULL/RIDE, PULL/PULL)
  4. Bonus bet edge cases (bonus_bet=0 with paytable, bonus_bet>0 without paytable, etc.)
  5. Net result calculation correctness for winning and losing hands

### Medium

#### M1: No Tests for `HandProcessingResult` Dataclass
- **Location**: `src/let_it_ride/core/hand_processing.py:22-47` (diff lines 225-250)
- **Issue**: The `HandProcessingResult` dataclass uses `frozen=True, slots=True` but there are no tests verifying these properties work as expected.
- **Recommendation**: Add tests verifying:
  ```python
  def test_hand_processing_result_is_frozen():
      result = HandProcessingResult(...)
      with pytest.raises(FrozenInstanceError):
          result.net_result = 100.0
  ```

#### M2: Indirect Coverage May Miss Edge Cases
- **Location**: `src/let_it_ride/core/hand_processing.py:50-131` (diff lines 253-334)
- **Issue**: The integration tests use `random.Random(seed)` to generate cards, making it difficult to test specific edge cases like:
  - Exact boundary conditions for bets_at_risk calculation
  - Zero bonus_bet with non-None bonus_paytable
  - Specific hand ranks to verify payout multipliers
- **Recommendation**: Create unit tests with fixed card inputs to verify specific scenarios deterministically.

### Low

#### L1: No Direct Test for Strategy Context Propagation
- **Location**: `src/let_it_ride/core/hand_processing.py:86,91` (diff lines 289,294)
- **Issue**: While `GameEngine` tests verify context is passed to strategy, there is no direct test that `process_hand_decisions_and_payouts` correctly forwards the context to `strategy.decide_bet1()` and `strategy.decide_bet2()`.
- **Recommendation**: Add a unit test with a mock strategy that captures and verifies the context object.

## Coverage Analysis

### Current Coverage Status

| Component | Test File | Coverage Type | Coverage Level |
|-----------|-----------|---------------|----------------|
| `hand_processing.py` | None | Unit | **None** |
| `hand_processing.py` (via GameEngine) | `test_game_engine.py` | Integration | High |
| `hand_processing.py` (via Table) | `test_table.py` | Integration | High |

### Coverage Strengths

1. **Behavioral Equivalence Tests**: `test_table.py` includes `test_single_seat_matches_game_engine_with_same_seed()` and `test_single_seat_matches_game_engine_with_bonus()` which verify that both callers of the extracted function produce identical results.

2. **Comprehensive Integration Tests**: The existing `test_game_engine.py` covers:
   - Bet validation
   - Decision recording
   - Bets at risk calculations (all 4 combinations)
   - Main game payout calculations
   - Net result calculations
   - Bonus bet handling
   - Strategy context propagation

3. **Multi-seat Coverage**: `test_table.py` tests multi-seat scenarios that exercise the extracted code path.

### Coverage Gaps

1. **No direct unit tests** for `process_hand_decisions_and_payouts()`
2. **No property-based tests** using hypothesis for statistical validation
3. **No explicit edge case tests** for:
   - `bonus_bet = 0.0` with a valid `bonus_paytable`
   - Very large bet amounts (overflow concerns)
   - Floating-point precision in payout calculations

## Recommendations

### Priority 1: Create Unit Tests for `hand_processing.py`

Create `tests/unit/core/test_hand_processing.py`:

```python
"""Unit tests for shared hand processing logic."""

import pytest
from let_it_ride.core.card import Card, Rank, Suit
from let_it_ride.core.hand_processing import (
    HandProcessingResult,
    process_hand_decisions_and_payouts,
)
from let_it_ride.strategy.base import Decision, StrategyContext


class AlwaysRideStrategy:
    """Strategy that always rides."""
    def decide_bet1(self, analysis, context):
        return Decision.RIDE
    def decide_bet2(self, analysis, context):
        return Decision.RIDE


class AlwaysPullStrategy:
    """Strategy that always pulls."""
    def decide_bet1(self, analysis, context):
        return Decision.PULL
    def decide_bet2(self, analysis, context):
        return Decision.PULL


class TestHandProcessingResultDataclass:
    """Tests for HandProcessingResult dataclass."""

    def test_is_frozen(self):
        """Verify HandProcessingResult is immutable."""
        # Create a result with valid data
        result = HandProcessingResult(
            decision_bet1=Decision.RIDE,
            decision_bet2=Decision.RIDE,
            final_hand_rank=FiveCardHandRank.HIGH_CARD,
            bets_at_risk=15.0,
            main_payout=0.0,
            bonus_hand_rank=None,
            bonus_payout=0.0,
            net_result=-15.0,
        )
        with pytest.raises(AttributeError):
            result.net_result = 100.0


class TestBetsAtRiskCalculation:
    """Tests for bets_at_risk calculation in process_hand_decisions_and_payouts."""

    def test_all_ride_three_bets_at_risk(self):
        """RIDE/RIDE = 3 bets at risk."""
        # Use fixed cards and AlwaysRideStrategy
        ...

    def test_all_pull_one_bet_at_risk(self):
        """PULL/PULL = 1 bet at risk."""
        ...

    def test_ride_pull_two_bets_at_risk(self):
        """RIDE/PULL = 2 bets at risk."""
        ...

    def test_pull_ride_two_bets_at_risk(self):
        """PULL/RIDE = 2 bets at risk."""
        ...


class TestBonusBetEdgeCases:
    """Tests for bonus bet handling."""

    def test_zero_bonus_bet_with_paytable_no_evaluation(self):
        """bonus_bet=0 with paytable should not evaluate bonus hand."""
        ...

    def test_positive_bonus_bet_evaluates_three_card_hand(self):
        """bonus_bet>0 evaluates 3-card hand."""
        ...
```

### Priority 2: Add Property-Based Tests

Consider adding hypothesis-based tests to verify statistical properties:

```python
from hypothesis import given, strategies as st

@given(base_bet=st.floats(min_value=1.0, max_value=1000.0))
def test_bets_at_risk_proportional_to_base_bet(base_bet):
    """bets_at_risk should always be between 1x and 3x base_bet."""
    ...
```

### Priority 3: Verify Refactoring Did Not Change Behavior

The existing `test_single_seat_matches_game_engine_with_same_seed()` test provides good coverage here, but consider adding a few more rounds to increase statistical confidence:

```python
def test_behavioral_equivalence_multiple_rounds():
    """Verify Table and GameEngine produce identical results over many rounds."""
    for seed in range(100):
        # Compare results
        ...
```

## Conclusion

The refactoring is well-executed and the code quality is good. However, the lack of direct unit tests for the new `hand_processing.py` module represents a coverage gap. The existing integration tests provide behavioral coverage, but direct unit tests would:

1. Make the module's contract explicit and testable
2. Enable faster feedback during future modifications
3. Document edge case behavior
4. Improve overall test maintainability

**Recommendation**: Approve the PR but create a follow-up issue to add dedicated unit tests for `hand_processing.py`.
