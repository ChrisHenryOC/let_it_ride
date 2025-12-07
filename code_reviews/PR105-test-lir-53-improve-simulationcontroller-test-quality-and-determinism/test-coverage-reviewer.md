# Test Coverage Review: PR #105

**PR Title:** test: LIR-53 Improve SimulationController test quality and determinism

**Reviewer:** Test Coverage Reviewer
**Date:** 2025-12-07

## Summary

This PR significantly improves test quality for `SimulationController` by removing a flaky test, adding deterministic stop condition tests using mock `GameEngine`, implementing RNG isolation verification, and enhancing callback testing. The changes are well-structured and address previously identified quality issues. However, there are a few gaps in coverage and some minor improvements that could strengthen the test suite further.

## Findings by Severity

### Medium

#### 1. Incomplete RNG Isolation Verification in `test_session_seeds_are_independent`

**File:** `tests/integration/test_controller.py`
**Lines:** 322-361 (diff lines 182-221)

The test `test_session_seeds_are_independent` has a limitation acknowledged in the comment: "Since we can't inspect individual hands directly, we verify that both runs complete successfully with expected session counts." This means the test does not actually verify that the first N hands of each session are identical between short and long runs, which would be the true proof of session isolation.

**Impact:** The test passes but does not definitively prove RNG isolation. If a bug caused RNG state leakage between sessions, this test might not catch it.

**Recommendation:** Consider adding a mechanism to capture per-hand results (e.g., via a hook or by examining session statistics more granularly) or document this as a known limitation with a TODO for future improvement.

#### 2. Missing Test for loss_limit vs max_hands Priority

**File:** `tests/integration/test_controller.py`
**Lines:** 477-521 (diff lines 337-381)

The test `test_stop_condition_priority_deterministic` verifies that `win_limit` takes priority over `max_hands`, but there is no corresponding test for `loss_limit` vs `max_hands` priority. This is an asymmetric gap in coverage.

**Impact:** If the priority logic for `loss_limit` differs from `win_limit`, the behavior would not be verified.

**Recommendation:** Add a test `test_loss_limit_priority_over_max_hands_deterministic` to verify consistent priority behavior.

#### 3. Missing Test for insufficient_funds vs loss_limit Priority

**File:** `tests/integration/test_controller.py`

The `TestDeterministicStopConditions` class tests each stop condition in isolation but does not test priority between `insufficient_funds` and `loss_limit` when both could trigger simultaneously.

**Impact:** Edge case where bankroll goes below minimum bet AND exceeds loss_limit at the same time is not verified.

**Recommendation:** Add a test where a single hand triggers both conditions to verify which takes priority.

### Low

#### 4. Repeated Mock Engine Creation Pattern

**File:** `tests/integration/test_controller.py`
**Lines:** 292-308, 340-356, 394-410, 445-461, 495-510

Each test in `TestDeterministicStopConditions` defines its own `create_*_engine()` function with nearly identical structure. This is repetitive and could be consolidated.

**Impact:** Code duplication increases maintenance burden. Changes to mock structure would require updates in multiple places.

**Recommendation:** Consider extracting a parameterized helper function like:
```python
def create_mock_engine(net_result: float, track_hands: bool = False) -> tuple[Mock, list[int] | None]:
    """Create a mock GameEngine with fixed net_result per hand."""
    # ... shared implementation
```

#### 5. Import Statement Placement Inside Test Methods

**File:** `tests/integration/test_controller.py`
**Lines:** 290, 340, 392, 444, 494

The `from unittest.mock import Mock` statement appears inside each test method in `TestDeterministicStopConditions`. While this works, it is inconsistent with the file's overall style where imports are at the top.

**Impact:** Minor inconsistency. The `Mock` import already exists at line 6 (`from unittest.mock import patch`).

**Recommendation:** Add `Mock` to the existing import at the top of the file: `from unittest.mock import Mock, patch`. Then remove the local imports from each test method.

#### 6. No Negative Test for Callback Argument Validation

**File:** `tests/integration/test_controller.py`

The new callback tests verify correct behavior but do not test what happens if a callback has an incorrect signature (e.g., wrong number of parameters).

**Impact:** If user provides a callback with wrong signature, the error behavior is not documented via tests.

**Recommendation:** Consider adding a test to document expected behavior when callback signature is wrong (likely a TypeError at runtime).

## Recommendations Summary

| Priority | Recommendation | Effort |
|----------|----------------|--------|
| Medium | Add RNG isolation verification using hand-level inspection or statistical analysis | High |
| Medium | Add `test_loss_limit_priority_over_max_hands_deterministic` | Low |
| Medium | Add `test_insufficient_funds_vs_loss_limit_priority` | Low |
| Low | Extract common mock engine creation helper | Medium |
| Low | Move `Mock` import to file header | Low |
| Low | Add callback signature validation test | Low |

## Positive Observations

1. **Removal of Flaky Test:** The deletion of `test_unseeded_runs_differ` (lines 140-158 in diff) eliminates a test that acknowledged it "could theoretically fail." This is a good practice.

2. **Deterministic Stop Condition Tests:** The new `TestDeterministicStopConditions` class provides guaranteed coverage of all four stop conditions (win_limit, loss_limit, max_hands, insufficient_funds) without probabilistic behavior.

3. **Excellent Documentation:** Class-level and method-level docstrings clearly explain the purpose and rationale of each test, particularly the `TestErrorHandling` class docstring explaining callback exception propagation behavior.

4. **RNG Reproducibility Tests:** The `test_reproducibility_across_different_session_counts` test verifies a subtle but important property: that session N does not affect session N+1's RNG state.

5. **Priority Testing:** The `test_stop_condition_priority_deterministic` test addresses an important edge case where multiple stop conditions could trigger simultaneously.

## Coverage Analysis

| Test Class | New Tests Added | Coverage Improvement |
|------------|-----------------|---------------------|
| `TestProgressCallback` | 2 | Callback argument verification, timing verification |
| `TestReproducibility` | 1 | Cross-session-count reproducibility |
| `TestRNGIsolation` | 3 | Session seed independence, deterministic derivation, seed variation |
| `TestDeterministicStopConditions` | 5 | All stop conditions with deterministic mocks |
| `TestErrorHandling` | 1 | Custom exception type preservation |

**Total new tests:** 12
**Tests removed:** 1 (flaky test)
**Net change:** +11 tests

## Conclusion

This PR substantially improves the quality and reliability of the `SimulationController` test suite. The key improvements are the elimination of a flaky test and the addition of deterministic stop condition tests using mocks. The identified gaps (priority testing for loss_limit, RNG isolation verification depth) are relatively minor and do not block the PR. The changes align well with the goals stated in the scratchpad document.
