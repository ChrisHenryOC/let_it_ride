# LIR-53: Test Quality Improvements for SimulationController

**GitHub Issue:** #100
**Status:** In Progress

## Summary

Improve test quality and determinism for `SimulationController` integration tests, addressing findings from PR #96 code review.

## Analysis

### Current State

The integration tests in `tests/integration/test_controller.py` have several quality issues:

1. **Flaky Test**: `test_unseeded_runs_differ` (line 250) - comment acknowledges it "could theoretically fail"
2. **Probabilistic Assertions**: Stop condition tests don't guarantee code path execution
3. **No RNG Isolation Tests**: Session N+1 should not inherit state from session N
4. **Incomplete Callback Tests**: Exception handling for callbacks documented but not fully tested

### Existing Mock Patterns

From `tests/unit/simulation/test_session.py`:

```python
def create_mock_engine(results: list[float]) -> Mock:
    """Create a mock GameEngine that returns predetermined results."""
    mock = Mock()
    result_iter = iter(results)

    def play_hand_side_effect(hand_id, base_bet, bonus_bet=0.0, context=None):
        result = Mock()
        result.net_result = next(result_iter)
        result.bets_at_risk = base_bet * 3
        result.bonus_bet = bonus_bet
        return result

    mock.play_hand.side_effect = play_hand_side_effect
    return mock
```

## Implementation Plan

### 1. Fix Flaky Tests
- [x] Remove `test_unseeded_runs_differ` - it's redundant with `test_different_seeds_produce_different_results`

### 2. Deterministic Stop Condition Tests
- [x] Created `TestDeterministicStopConditions` class with:
  - `test_win_limit_triggers_deterministically` - mock engine returns $60 profit
  - `test_loss_limit_triggers_deterministically` - mock engine returns -$30 loss
  - `test_max_hands_triggers_exactly` - mock engine returns $0 (break-even)
  - `test_insufficient_funds_triggers_deterministically` - mock engine returns -$50 loss
  - `test_stop_condition_priority_deterministic` - verifies win_limit priority over max_hands

### 3. RNG State Isolation Tests
- [x] Created `TestRNGIsolation` class with:
  - `test_session_seeds_are_independent` - verifies sessions don't share RNG state
  - `test_deterministic_session_seed_derivation` - verifies same seed = same results
  - `test_different_base_seeds_produce_different_sessions` - sanity check
- [x] Added `test_reproducibility_across_different_session_counts` to `TestReproducibility`

### 4. Progress Callback Edge Case Tests
- [x] Added docstring to `TestErrorHandling` class documenting expected behavior:
  - Callback exceptions propagate up (intentional design)
  - Partial results may be lost if callback fails mid-simulation
  - Caller is responsible for error handling
- [x] Added `test_callback_exception_type_preserved` - verifies exception types preserved
- [x] Added `test_callback_receives_correct_arguments` to `TestProgressCallback`
- [x] Added `test_callback_called_after_session_completes` to `TestProgressCallback`

## Files Modified

- `tests/integration/test_controller.py` - Added new test classes and tests

## Acceptance Criteria

- [x] No flaky tests in CI (removed `test_unseeded_runs_differ`)
- [x] All stop condition code paths exercised deterministically (5 new tests)
- [x] RNG isolation verified with explicit tests (4 new tests)
- [x] Clear documentation of callback error handling behavior (class docstring added)
