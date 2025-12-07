# Code Quality Review - PR #105

## Summary

This PR significantly improves test quality and determinism for `SimulationController` integration tests by removing a flaky test, adding deterministic stop condition tests using mock engines, introducing RNG isolation verification, and enhancing callback test coverage. The code follows existing patterns well, though there is notable repetition in mock engine factory functions that could benefit from consolidation using the existing pattern from `tests/unit/simulation/test_session.py`.

## Findings

### Critical

None

### High

None

### Medium

1. **Repeated mock engine factory pattern violates DRY** (`tests/integration/test_controller.py:292-510`)

   The `TestDeterministicStopConditions` class defines four nearly identical mock engine factory functions (`create_winning_engine`, `create_losing_engine`, `create_breakeven_engine`, `create_busting_engine`). Each differs only in the `net_result` value. The scratchpad notes that `tests/unit/simulation/test_session.py` already has a reusable `create_mock_engine(results: list[float])` pattern that accepts a list of results.

   Consider refactoring to:
   ```python
   def create_mock_engine(net_result: float) -> Mock:
       """Create a mock GameEngine returning a fixed net_result per hand."""
       mock = Mock()

       def play_hand(hand_id: int, base_bet: float, bonus_bet: float = 0.0, context=None):
           result = Mock()
           result.net_result = net_result
           result.bets_at_risk = base_bet * 3
           result.bonus_bet = bonus_bet
           return result

       mock.play_hand.side_effect = play_hand
       return mock
   ```

   Then each test simply calls `create_mock_engine(60.0)`, `create_mock_engine(-30.0)`, etc.

   **Files:** `tests/integration/test_controller.py:292-310`, `341-358`, `394-410`, `445-461`, `494-510`

2. **Repeated import of `unittest.mock.Mock` inside test methods** (`tests/integration/test_controller.py:290`, `340`, `390`, `444`, `492`)

   The `from unittest.mock import Mock` statement is repeated at the beginning of each test method in `TestDeterministicStopConditions`. This import already exists at the module level (line 6: `from unittest.mock import patch`), so `Mock` should be added to that import statement rather than importing locally multiple times.

   **Location:** Lines 290, 340, 390, 444, 492 in the diff (approximately lines 290, 340, 390, 444, 492 in the actual file)

### Low

1. **Inconsistent use of `noqa: ARG001` comments** (`tests/integration/test_controller.py:123`, `295-300`, `345-350`)

   Some callback functions use `noqa: ARG001` comments to suppress unused argument warnings (e.g., line 123: `total: int) -> None:  # noqa: ARG001`), while the mock engine `play_hand` functions also use them. This is acceptable, but consider the more Pythonic underscore prefix convention (`_hand_id`, `_context`) which is self-documenting and does not require linter annotations.

2. **Magic number for hands_played_count tracking** (`tests/integration/test_controller.py:392`)

   The test uses a mutable list `hands_played_count = [0]` as a closure to track hand count. While this is a common Python pattern for mutating closure variables, a simple `nonlocal` declaration or a dataclass/SimpleNamespace would be clearer:

   ```python
   @dataclass
   class Counter:
       value: int = 0
   hands_played = Counter()
   # Then: hands_played.value += 1
   ```

   This is a minor style preference.

3. **Test class docstrings could include test counts** (`tests/integration/test_controller.py:173-180`, `265-271`)

   The `TestRNGIsolation` and `TestDeterministicStopConditions` class docstrings are well-written and explain the purpose. Consider adding the number of tests each class contains for easier navigation:

   ```python
   """Tests for stop conditions using deterministic mock GameEngine (5 tests).
   ```

4. **Variable naming: `r3`, `r5` in zip loop** (`tests/integration/test_controller.py:163-170`)

   The variable names `r3` and `r5` in the zip loop are terse. More descriptive names like `result_from_3` and `result_from_5` or `short_result` and `long_result` would improve readability:

   ```python
   for short_result, long_result in zip(
       results_3.session_results, results_5.session_results[:3], strict=True
   ):
   ```

## Recommendations

### Priority 1: Extract shared mock engine factory (Medium)

Consolidate the five identical mock engine factory functions into a single reusable function. This reduces code duplication from approximately 100 lines to approximately 15 lines and makes the test intent clearer.

**File:** `tests/integration/test_controller.py`

**Suggested location:** Near the top of the file, after `create_test_config()`, or within the `TestDeterministicStopConditions` class as a class method.

### Priority 2: Fix duplicate imports (Medium)

Move `Mock` to the module-level import:

```python
from unittest.mock import Mock, patch
```

Remove the five `from unittest.mock import Mock` statements inside test methods.

**File:** `tests/integration/test_controller.py:6`

### Priority 3: Consider underscore convention for unused parameters (Low)

Replace `# noqa: ARG001` comments with underscore-prefixed parameter names where appropriate:

```python
def play_hand(_hand_id: int, base_bet: float, bonus_bet: float = 0.0, _context=None):
```

**File:** Various locations in `TestDeterministicStopConditions`

## Positive Aspects

1. **Excellent test design**: The removal of `test_unseeded_runs_differ` (which was explicitly flaky) and replacement with deterministic tests is a significant quality improvement.

2. **Comprehensive RNG isolation coverage**: The `TestRNGIsolation` class provides thorough verification that sessions do not share RNG state, which is critical for simulation reproducibility.

3. **Clear docstrings**: Each test method has a descriptive docstring explaining both what is being tested and why, which aids future maintenance.

4. **Well-documented design decisions**: The `TestErrorHandling` class docstring now clearly documents the callback exception propagation behavior and the design rationale behind it.

5. **Good use of scratchpad**: The scratchpad file provides excellent traceability between the implementation plan and the actual code changes.

6. **Consistent style**: The new tests follow the existing patterns in the file (type hints, naming conventions, assertion style).

7. **Proper type annotations**: All test methods include `-> None` return type annotations per project standards.

8. **Thorough stop condition coverage**: The five deterministic stop condition tests cover all major stop reasons (win_limit, loss_limit, max_hands, insufficient_funds) plus priority testing.

9. **Good callback testing expansion**: The new callback tests verify argument correctness and timing, not just that the callback is called.

10. **Reproducibility test enhancement**: The `test_reproducibility_across_different_session_counts` test verifies an important property - that running more sessions does not affect the results of earlier sessions.
