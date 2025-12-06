# Test Coverage Review: PR #96 - LIR-20 Simulation Controller (Sequential)

**Reviewer:** Test Coverage Specialist
**Date:** 2025-12-06
**PR:** #96
**Files Changed:** 4 (+919 lines production/test code)

## Summary

This PR implements `SimulationController` for orchestrating sequential multi-session simulations with comprehensive integration tests in `tests/integration/test_controller.py`. The integration tests provide solid coverage of happy-path scenarios including reproducibility, progress callbacks, and session isolation. However, there are significant gaps in unit test coverage for the factory functions (`create_strategy`, `create_betting_system`) and error handling paths. The test-to-production code ratio is approximately 1.03:1 (408:434 lines), which is reasonable for integration tests but indicates missing unit tests.

---

## Critical Findings

### [CRITICAL-1] No Unit Tests for `create_strategy` Factory Function

**File:** `src/let_it_ride/simulation/controller.py` (lines 89-138)
**Issue:** The `create_strategy()` function has 6 strategy type branches plus error handling but lacks dedicated unit tests. The integration tests only exercise this indirectly via `create_test_config()` which defaults to "basic" strategy.

**Missing test scenarios:**
- Direct testing of each strategy type mapping (basic, always_ride, always_pull, conservative, aggressive, custom)
- Error path: unknown strategy type raises `ValueError` (line 138)
- Error path: `custom` strategy without `config.custom` raises `ValueError` (lines 120-121)
- Custom strategy rule conversion from config strings to `Decision` enum (lines 124-136)

**Risk:** Factory function bugs could silently produce wrong strategy types without explicit unit test verification.

**Recommendation:** Add unit tests in `tests/unit/simulation/test_controller.py`:

```python
import pytest
from let_it_ride.config.models import StrategyConfig, CustomStrategyConfig, StrategyRuleConfig
from let_it_ride.simulation.controller import create_strategy
from let_it_ride.strategy import BasicStrategy, AlwaysRideStrategy, CustomStrategy

class TestCreateStrategy:
    def test_basic_strategy_type(self) -> None:
        config = StrategyConfig(type="basic")
        strategy = create_strategy(config)
        assert isinstance(strategy, BasicStrategy)

    def test_custom_strategy_without_config_raises_error(self) -> None:
        config = StrategyConfig(type="custom", custom=None)
        with pytest.raises(ValueError, match="'custom' strategy requires"):
            create_strategy(config)

    def test_custom_strategy_converts_rules(self) -> None:
        config = StrategyConfig(
            type="custom",
            custom=CustomStrategyConfig(
                bet1_rules=[StrategyRuleConfig(condition="pair >= 10", action="ride")],
                bet2_rules=[StrategyRuleConfig(condition="pair >= 10", action="ride")],
            )
        )
        strategy = create_strategy(config)
        assert isinstance(strategy, CustomStrategy)
```

---

### [CRITICAL-2] No Unit Tests for `create_betting_system` Factory Function

**File:** `src/let_it_ride/simulation/controller.py` (lines 141-224)
**Issue:** The `create_betting_system()` function handles 8 betting system types with complex configuration mapping but lacks unit tests. Integration tests only use "flat" betting via `create_test_config()`.

**Missing test scenarios:**
- Each betting system type correctly instantiated (flat, martingale, reverse_martingale, paroli, dalembert, fibonacci)
- Error paths for missing config sections:
  - `martingale` without config (line 163)
  - `reverse_martingale` without config (lines 174-175)
  - `paroli` without config (line 187)
  - `dalembert` without config (line 198)
  - `fibonacci` without config (line 210)
- `NotImplementedError` for `proportional` and `custom` types (lines 219-222)
- `ValueError` for unknown betting system types (line 224)

**Risk:** All betting system types except "flat" are completely untested.

**Recommendation:** Add comprehensive unit tests covering all 8 betting system types and all error paths.

---

## High Severity Findings

### [HIGH-1] No Tests for Paytable Factory Functions

**File:** `src/let_it_ride/simulation/controller.py`
**Lines:** 227-274

**Issue:** `_get_main_paytable()` (lines 227-246) and `_get_bonus_paytable()` (lines 249-274) are private but have no direct or indirect test coverage.

**Missing scenarios:**
- `_get_main_paytable` with non-standard paytable types raises `NotImplementedError` (lines 243-246)
- `_get_bonus_paytable` returns `None` when bonus disabled (lines 261-262)
- `_get_bonus_paytable` with paytable_a, paytable_b, paytable_c variants (lines 265-270)
- `_get_bonus_paytable` with unknown paytable type raises `ValueError` (lines 271-274)

**Recommendation:** Add tests that exercise these through the public API or consider making them public for direct testing.

---

### [HIGH-2] Insufficient Bonus Bet Calculation Testing

**File:** `src/let_it_ride/simulation/controller.py` (lines 381-395)
**Issue:** The bonus bet calculation logic in `_create_session` has 4 conditional branches that are not explicitly tested.

**Missing scenarios:**
- Bonus enabled with `always` configuration (lines 386-387)
- Bonus enabled with `static.amount` (lines 388-390)
- Bonus enabled with `static.ratio` (lines 391-395)
- Bonus disabled (bonus_bet should be 0)

All integration tests use default `bonus_strategy` which does not enable bonus.

---

### [HIGH-3] Custom Strategy with Rules Not Tested

**File:** `src/let_it_ride/simulation/controller.py` (lines 119-136)
**Issue:** The `custom` strategy type with rule conversion is not tested. The `_action_to_decision` helper function (lines 58-67) that converts "ride"/"pull" strings to `Decision` enum is not covered.

**Missing scenario:** Creating a `custom` strategy and verifying rules are properly converted and the strategy makes correct decisions.

---

## Medium Severity Findings

### [MEDIUM-1] Test `test_unseeded_runs_differ` is Non-Deterministic

**File:** `tests/integration/test_controller.py` (lines 241-257)
**Issue:** The test comment on line 256 acknowledges it "could theoretically fail" which makes it a flaky test.

```python
# This could theoretically fail but is extremely unlikely
assert profits1 != profits2
```

**Recommendation:** Either:
1. Remove this test since `test_different_seeds_produce_different_results` covers the intent
2. Use statistical approach with multiple runs and probability threshold
3. Accept flakiness with `@pytest.mark.flaky(reruns=3)`

---

### [MEDIUM-2] Stop Condition Tests Use Probabilistic Assertions

**File:** `tests/integration/test_controller.py` (lines 260-326)
**Issue:** Tests like `test_win_limit_stops_session` and `test_loss_limit_stops_session` rely on probabilistic outcomes. The comments acknowledge this:

```python
# Some sessions should stop on win limit
# (but this is not guaranteed - depends on luck)
```

**Risk:** These tests may not consistently exercise the target code paths, potentially missing regressions.

**Recommendation:** Use deterministic mock engines for stop condition tests to guarantee specific outcomes.

---

### [MEDIUM-3] No Tests for Progress Callback Exception Handling

**File:** `src/let_it_ride/simulation/controller.py` (lines 342-343)
**Issue:** If `progress_callback` raises an exception, it would crash the entire simulation. No tests verify this behavior.

```python
if self._progress_callback is not None:
    self._progress_callback(session_id + 1, num_sessions)
```

**Question:** Should exceptions be caught and logged? Should they propagate? This behavior is undefined and untested.

---

### [MEDIUM-4] Session RNG State Isolation Not Verified

**File:** `tests/integration/test_controller.py` (lines 129-138)
**Issue:** `test_session_isolation` only checks that starting bankroll is reset. It does not verify RNG state isolation between sessions.

**Missing verification:** Each session should get an independent RNG state derived from the master RNG, not inherit state from the previous session.

---

## Low Severity Findings

### [LOW-1] Missing SimulationResults Immutability Test

**Issue:** `SimulationResults` is a frozen dataclass but no test verifies immutability.

**Recommendation:**
```python
def test_simulation_results_is_frozen(self) -> None:
    config = create_test_config(num_sessions=1)
    results = SimulationController(config).run()
    with pytest.raises(dataclasses.FrozenInstanceError):
        results.total_hands = 0
```

---

### [LOW-2] No Property-Based Tests for RNG Reproducibility

**Issue:** Given the simulation nature of this code, property-based testing with `hypothesis` would improve confidence in reproducibility claims.

**Recommendation:**
```python
from hypothesis import given, strategies as st

@given(seed=st.integers(min_value=0, max_value=2**31-1))
def test_reproducibility_property(seed: int) -> None:
    """Any valid seed produces identical results across runs."""
    config = create_test_config(num_sessions=3, random_seed=seed)
    results1 = SimulationController(config).run()
    results2 = SimulationController(config).run()
    assert results1.total_hands == results2.total_hands
```

---

### [LOW-3] Test Helper Could Validate Unknown Strategy Types

**File:** `tests/integration/test_controller.py` (lines 26-45)
**Issue:** `_create_strategy_config` helper passes unknown strategy types through without validation.

```python
return StrategyConfig(type=strategy_type)  # No validation for unknown types
```

---

## Test Quality Assessment

### Strengths

1. **Well-organized test structure:** Tests are logically grouped into classes (`TestSimulationController`, `TestProgressCallback`, `TestReproducibility`, etc.)
2. **Parametrized tests:** `TestStrategyVariants` uses `@pytest.mark.parametrize` effectively for strategy type coverage
3. **Clear test naming:** Test names clearly describe expected behavior
4. **Comprehensive progress callback tests:** Verifies callback is called with correct values

### Areas for Improvement

1. **Missing unit tests:** Factory functions need dedicated unit tests
2. **Error path coverage:** Most error handling paths (ValueError, NotImplementedError) are untested
3. **Determinism:** Several tests rely on probabilistic outcomes
4. **No mocking:** Integration tests don't use mocks, limiting control over scenarios

---

## Test Coverage Metrics

| Component | Integration Tests | Unit Tests | Estimated Coverage |
|-----------|------------------|------------|-------------------|
| `SimulationController.run()` | Yes | No | ~80% |
| `SimulationController._create_session()` | Indirect | No | ~60% |
| `create_strategy()` | Indirect (basic only) | **No** | ~20% |
| `create_betting_system()` | Indirect (flat only) | **No** | ~15% |
| `_get_main_paytable()` | Indirect (standard only) | No | ~30% |
| `_get_bonus_paytable()` | No (bonus disabled) | No | ~5% |
| `_action_to_decision()` | No | No | ~0% |
| `SimulationResults` | Yes | No | ~90% |
| Progress callback | Yes | No | ~95% |
| Error handling paths | No | No | ~5% |

**Overall Estimated Coverage:** 45-55%

---

## Recommended Test Additions (Prioritized)

### Priority 1 (Must Have Before Merge)

1. **Unit tests for `create_strategy`** - All 6 strategy types + 2 error paths
2. **Unit tests for `create_betting_system`** - All 8 system types + 7 error paths

### Priority 2 (Should Have)

3. **Bonus bet calculation tests** - All 4 conditional branches
4. **Paytable factory tests** - Main and bonus variants including error cases
5. **Custom strategy with rules test**

### Priority 3 (Nice to Have)

6. **Property-based reproducibility tests** - Using hypothesis
7. **Deterministic stop condition tests** - Using mock engines
8. **Progress callback exception handling test**
9. **SimulationResults immutability test**

---

## Conclusion

The PR provides a solid foundation of integration tests that verify the happy-path behavior of `SimulationController`. The core simulation loop, reproducibility, and progress callbacks are well-tested. However, the factory functions (`create_strategy` and `create_betting_system`) represent significant untested code with multiple branches and error paths.

**Recommendation:** The critical gaps in factory function testing should be addressed before merge. These functions are public APIs exported from the simulation module and used to instantiate all strategies and betting systems - they deserve dedicated unit test coverage.

The current test coverage is estimated at 45-55%, which should be improved to 80%+ for production-quality code targeting 100,000+ hands/second simulations.
