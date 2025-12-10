# Test Coverage Review: PR117 - LIR-54 Enhanced RNG Isolation Verification

## Summary

This PR introduces hand-level callback infrastructure (`HandCallback`, `ControllerHandCallback`) to enable precise verification of RNG isolation between sessions. The implementation adds callback support to `Session` and `SimulationController`, and significantly enhances the `TestRNGIsolation` test class with hand-level verification. The test coverage is comprehensive for the new callback functionality, though a few gaps exist in unit-level testing and edge case coverage.

## Findings by Severity

### High

**H1: Missing unit tests for `HandCallback` in Session class**
- **File:** `tests/unit/simulation/test_session.py`
- **Issue:** The unit test file for Session has no tests for the new `hand_callback` parameter and its invocation behavior. All callback testing is done at the integration level in `test_controller.py`.
- **Impact:** Unit-level bugs in callback invocation (e.g., wrong hand_id, callback timing relative to state updates) may go undetected.
- **Recommendation:** Add unit tests to `tests/unit/simulation/test_session.py` covering:
  1. Callback is invoked after each hand with correct `(hand_id, GameHandResult)`
  2. Callback is not invoked when `hand_callback=None`
  3. Callback invocation order relative to state updates (called after bankroll/streak updates)
  4. Exception propagation from callback

**H2: No test for exception handling in hand callback**
- **File:** `src/let_it_ride/simulation/session.py:358-360`
- **Issue:** Unlike `progress_callback`, there is no test documenting the behavior when `hand_callback` raises an exception. The error handling test class (`TestErrorHandling` in `test_controller.py`) only covers progress callback exceptions.
- **Impact:** Unclear whether callback exceptions propagate correctly or interrupt simulation.
- **Recommendation:** Add a test `test_hand_callback_exception_propagates` following the pattern of `test_progress_callback_exception_propagates`.

### Medium

**M1: `_hands_are_identical` helper does not compare `bonus_payout`**
- **File:** `tests/integration/test_controller.py:345-369`
- **Issue:** The comparison helper checks `main_payout` but not `bonus_payout`. If RNG isolation affects bonus calculations differently, this would not be detected.
- **Impact:** Partial verification of hand equivalence; bonus-related RNG issues could slip through.
- **Recommendation:** Add `hand1.bonus_payout == hand2.bonus_payout` to the comparison and include it in the error messages.

**M2: No test for hand callback behavior in parallel mode**
- **File:** `src/let_it_ride/simulation/controller.py:323-325`
- **Issue:** The docstring states hand_callback is "Only available in sequential mode" but there is no test verifying that hand_callback is ignored/not called when running in parallel mode.
- **Impact:** Undocumented behavior could lead to silent data loss if users expect callbacks in parallel mode.
- **Recommendation:** Add a test that configures parallel execution with a hand_callback and verifies either: (a) callback is not invoked, or (b) an appropriate warning/error is raised.

**M3: Missing test for callback with `bonus_bet > 0` scenario**
- **File:** `tests/integration/test_controller.py`
- **Issue:** All RNG isolation tests use the default bonus configuration (no bonus). There's no verification that hand-level callbacks work correctly when bonus bets are active and bonus payouts are included in `GameHandResult`.
- **Impact:** Integration gap between bonus betting and hand callback features.
- **Recommendation:** Add a test case in `TestRNGIsolation` or `TestBonusBetCalculation` that uses hand callbacks with bonus enabled and verifies bonus-related fields are captured correctly.

### Low

**L1: Closure variable shadowing in `session_hand_callback`**
- **File:** `src/let_it_ride/simulation/controller.py:477-481`
- **Issue:** The variable `sid = session_id` is used to capture the session_id in a closure, but then `session_hand_callback` is also named identically to the parameter in `__init__`. While this works, the `# type: ignore[misc]` suggests type checker confusion.
- **Impact:** Minor code clarity issue; no functional bug.
- **Recommendation:** Consider a clearer name like `_session_hand_callback` or using `functools.partial` for cleaner closure creation.

**L2: Test helper `_hands_are_identical` could be a method with better assertion messages**
- **File:** `tests/integration/test_controller.py:345-369`
- **Issue:** The helper returns `bool` which loses specific mismatch information. Tests using it construct their own error messages, leading to duplication.
- **Impact:** Verbose test code; harder to identify exactly which field mismatched on failure.
- **Recommendation:** Consider a helper that raises `AssertionError` with detailed diff, or returns a tuple of `(bool, mismatch_details)`.

**L3: `hand_id` validation not tested**
- **File:** `src/let_it_ride/simulation/session.py:359-360`
- **Issue:** The callback receives `result.hand_id` which should equal the loop counter. There's no explicit assertion that `hand_id` values are sequential starting from 0.
- **Impact:** Minor; hand_id sequencing bugs would likely be caught by other assertions.
- **Recommendation:** Add explicit assertion `assert short_hand.hand_id == hand_id` in the verification loop.

## Specific Recommendations

### 1. Add Session Unit Tests for HandCallback

```python
# tests/unit/simulation/test_session.py

class TestHandCallback:
    """Tests for hand callback functionality."""

    def test_callback_invoked_after_each_hand(self) -> None:
        """Verify hand callback is called with correct arguments."""
        config = SessionConfig(starting_bankroll=1000.0, base_bet=25.0, max_hands=3)
        engine = create_mock_engine([50.0, -25.0, 100.0])
        betting = FlatBetting(25.0)

        captured_calls: list[tuple[int, float]] = []
        def callback(hand_id: int, result: GameHandResult) -> None:
            captured_calls.append((hand_id, result.net_result))

        session = Session(config, engine, betting, hand_callback=callback)
        session.run_to_completion()

        assert len(captured_calls) == 3
        assert captured_calls[0] == (0, 50.0)
        assert captured_calls[1] == (1, -25.0)
        assert captured_calls[2] == (2, 100.0)

    def test_no_callback_when_none(self) -> None:
        """Verify session works without callback."""
        config = SessionConfig(starting_bankroll=1000.0, base_bet=25.0, max_hands=2)
        engine = create_mock_engine([50.0, -25.0])
        betting = FlatBetting(25.0)

        session = Session(config, engine, betting, hand_callback=None)
        result = session.run_to_completion()

        assert result.hands_played == 2  # No exception
```

### 2. Add Exception Propagation Test for Hand Callback

```python
# tests/integration/test_controller.py - in TestErrorHandling class

def test_hand_callback_exception_propagates(self) -> None:
    """Test that exceptions in hand callback propagate up."""
    config = create_test_config(num_sessions=1, hands_per_session=5)

    def failing_callback(session_id: int, hand_id: int, result: GameHandResult) -> None:
        if hand_id == 2:
            raise RuntimeError("Hand callback failed")

    controller = SimulationController(config, hand_callback=failing_callback)

    with pytest.raises(RuntimeError, match="Hand callback failed"):
        controller.run()
```

### 3. Enhance `_hands_are_identical` to include bonus_payout

```python
def _hands_are_identical(hand1: GameHandResult, hand2: GameHandResult) -> bool:
    return (
        hand1.player_cards == hand2.player_cards
        and hand1.community_cards == hand2.community_cards
        and hand1.decision_bet1 == hand2.decision_bet1
        and hand1.decision_bet2 == hand2.decision_bet2
        and hand1.final_hand_rank == hand2.final_hand_rank
        and hand1.main_payout == hand2.main_payout
        and hand1.bonus_payout == hand2.bonus_payout  # Add this
    )
```

## Coverage Analysis

| Component | Coverage Status | Notes |
|-----------|-----------------|-------|
| `HandCallback` type alias | Tested indirectly | Used in integration tests |
| `ControllerHandCallback` type alias | Tested directly | `TestRNGIsolation` uses it |
| `Session.hand_callback` parameter | Integration only | Missing unit tests |
| `Session.play_hand()` callback invocation | Integration only | Missing unit test |
| `SimulationController.hand_callback` | Good | Multiple integration tests |
| `_create_session` callback wrapper | Good | Tested via integration |
| RNG isolation at hand level | Excellent | 3 comprehensive tests |
| Callback exception handling | Missing | No test coverage |
| Parallel mode callback behavior | Missing | Not documented or tested |

## Overall Assessment

**Test Quality:** Good to Excellent

The PR demonstrates strong test-driven development with the enhanced `TestRNGIsolation` class providing definitive proof of session-level RNG isolation through hand-level comparison. The tests are well-structured, use meaningful assertions with detailed error messages, and cover the primary use case thoroughly.

**Gaps to Address:**
1. Unit tests for the new callback infrastructure in Session class (High priority)
2. Exception handling tests for hand callback (High priority)
3. Bonus payout inclusion in hand comparison (Medium priority)

The integration tests are comprehensive, but the lack of corresponding unit tests creates a testing gap at the component level that should be addressed before merge.
