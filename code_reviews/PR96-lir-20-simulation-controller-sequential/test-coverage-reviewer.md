# Test Coverage Review: PR #96 - LIR-20 Simulation Controller (Sequential)

## Summary

This PR implements `SimulationController` for orchestrating sequential multi-session simulations with +919 lines across 4 files. While the integration tests (`tests/integration/test_controller.py`) provide solid coverage of the controller's main functionality, there are significant gaps in unit test coverage for the factory functions (`create_strategy`, `create_betting_system`) and several error handling paths. The test-to-production code ratio is approximately 1.03:1 (408:395 lines), which is reasonable for integration tests but indicates missing unit tests for the factory functions.

---

## Critical Findings

### [CRITICAL-1] No Unit Tests for `create_strategy` Factory Function

**File:** `src/let_it_ride/simulation/controller.py` (lines 233-288)
**Issue:** The `create_strategy()` function has 7 strategy type branches plus error handling but lacks dedicated unit tests.

**Missing test scenarios:**
- Direct testing of each strategy type mapping
- Error path: unknown strategy type raises `ValueError`
- Error path: `custom` strategy without `config.custom` raises `ValueError`
- Custom strategy rule conversion from config strings to `Decision` enum

**Recommendation:** Add unit tests in `tests/unit/simulation/test_controller.py`:

```python
class TestCreateStrategy:
    def test_basic_strategy_type(self) -> None:
        config = StrategyConfig(type="basic")
        strategy = create_strategy(config)
        assert isinstance(strategy, BasicStrategy)

    def test_custom_strategy_without_config_raises_error(self) -> None:
        config = StrategyConfig(type="custom", custom=None)
        with pytest.raises(ValueError, match="'custom' strategy requires"):
            create_strategy(config)

    def test_unknown_strategy_type_raises_error(self) -> None:
        # Would need to bypass Pydantic validation or use mock
        ...
```

### [CRITICAL-2] No Unit Tests for `create_betting_system` Factory Function

**File:** `src/let_it_ride/simulation/controller.py` (lines 290-373)
**Issue:** The `create_betting_system()` function handles 8 betting system types with complex configuration mapping but lacks unit tests.

**Missing test scenarios:**
- Each betting system type correctly instantiated
- Error paths for missing config sections (martingale, reverse_martingale, paroli, dalembert, fibonacci)
- `NotImplementedError` for `proportional` and `custom` types
- `ValueError` for unknown betting system types

**Recommendation:** Add comprehensive unit tests:

```python
class TestCreateBettingSystem:
    def test_flat_betting_system(self) -> None:
        config = BankrollConfig(
            base_bet=10.0,
            betting_system=BettingSystemConfig(type="flat")
        )
        system = create_betting_system(config)
        assert isinstance(system, FlatBetting)
        assert system.base_bet == 10.0

    def test_martingale_without_config_raises_error(self) -> None:
        config = BankrollConfig(
            betting_system=BettingSystemConfig(type="martingale", martingale=None)
        )
        with pytest.raises(ValueError, match="'martingale' betting requires"):
            create_betting_system(config)
```

---

## High Severity Findings

### [HIGH-1] Missing Error Handling Tests for Invalid Configuration States

**File:** `tests/integration/test_controller.py`
**Issue:** No tests verify error handling when the controller receives invalid or malformed configurations.

**Missing scenarios:**
- Zero sessions configuration
- Negative values that bypass Pydantic validation (via mocks)
- Exception handling during session execution
- Memory exhaustion scenarios (for performance target validation)

### [HIGH-2] No Tests for Paytable Factory Functions

**File:** `src/let_it_ride/simulation/controller.py` (lines 376-413)
**Issue:** `_get_main_paytable()` and `_get_bonus_paytable()` are private but untested.

**Missing scenarios:**
- `_get_main_paytable` with different paytable types (standard, liberal, tight, custom)
- `_get_bonus_paytable` with bonus disabled (should return None)
- `_get_bonus_paytable` with paytable_a, paytable_b, paytable_c variants

**Recommendation:** Either:
1. Add unit tests for these via the public `_create_session` indirectly, OR
2. Make them public and add direct unit tests

### [HIGH-3] Insufficient Bonus Bet Calculation Testing

**File:** `src/let_it_ride/simulation/controller.py` (lines 499-513)
**Issue:** The bonus bet calculation logic in `_create_session` has multiple conditional branches that are not explicitly tested.

**Missing scenarios:**
- Bonus enabled with `always` configuration
- Bonus enabled with `static.amount`
- Bonus enabled with `static.ratio`
- Bonus disabled (bonus_bet should be 0)

---

## Medium Severity Findings

### [MEDIUM-1] Test `test_unseeded_runs_differ` is Non-Deterministic

**File:** `tests/integration/test_controller.py` (lines 799-815)
**Issue:** The test comment acknowledges it "could theoretically fail" which makes it a flaky test.

**Recommendation:** Use a statistical approach with multiple runs, or remove this test since `test_different_seeds_produce_different_results` already covers the intent.

### [MEDIUM-2] Missing RNG State Isolation Tests

**File:** `tests/integration/test_controller.py`
**Issue:** While `test_session_isolation` checks starting bankroll is reset, it does not verify RNG state isolation between sessions.

**Missing scenario:** Verify that session N+1 does not inherit RNG state from session N (which could cause correlation in results).

### [MEDIUM-3] Stop Condition Tests May Not Exercise All Code Paths

**File:** `tests/integration/test_controller.py` (lines 818-884)
**Issue:** Tests use probabilistic assertions ("Some sessions should stop...") which may not consistently exercise the target code paths.

**Recommendation:** Use deterministic mock engines for stop condition tests:

```python
def test_win_limit_stops_session_deterministic(self) -> None:
    """Use mock engine to guarantee win limit trigger."""
    # Mock GameEngine to return specific winning results
```

### [MEDIUM-4] No Tests for Progress Callback Exception Handling

**File:** `src/let_it_ride/simulation/controller.py` (lines 469-470)
**Issue:** If `progress_callback` raises an exception, it would crash the entire simulation. No tests verify this behavior or that exceptions are handled gracefully.

---

## Low Severity Findings

### [LOW-1] Missing Type Hint Verification Tests

**Issue:** No tests verify that `SimulationResults` is properly typed and frozen.

**Recommendation:** Add test for immutability:

```python
def test_simulation_results_is_frozen(self) -> None:
    results = controller.run()
    with pytest.raises(FrozenInstanceError):
        results.total_hands = 0
```

### [LOW-2] No Tests for Empty Session Results Edge Case

**Issue:** What happens if num_sessions=0 is passed? The Pydantic model allows ge=1, but the controller code assumes at least 1 session.

### [LOW-3] Missing `__slots__` Verification Tests

**File:** `src/let_it_ride/simulation/controller.py` (line 422)
**Issue:** `SimulationController` uses `__slots__` for memory efficiency but no test verifies this constraint.

### [LOW-4] No Property-Based Tests for RNG Reproducibility

**Issue:** Given the simulation nature of this code, property-based testing with `hypothesis` would improve confidence in reproducibility claims.

**Recommendation:**

```python
from hypothesis import given, strategies as st

@given(seed=st.integers(min_value=0, max_value=2**31-1))
def test_reproducibility_property(seed: int) -> None:
    """Any valid seed produces identical results across runs."""
    config = create_test_config(num_sessions=5, random_seed=seed)
    results1 = SimulationController(config).run()
    results2 = SimulationController(config).run()
    assert results1.total_hands == results2.total_hands
```

---

## Test Quality Assessment

### Strengths

1. **Good integration test structure:** Tests are well-organized into logical classes (`TestSimulationController`, `TestProgressCallback`, `TestReproducibility`, etc.)
2. **Parametrized tests:** `TestStrategyVariants` uses `@pytest.mark.parametrize` effectively
3. **Clear test naming:** Test names clearly describe expected behavior
4. **Progress callback verification:** Tests verify callback is called with correct values

### Areas for Improvement

1. **Missing unit tests:** Factory functions need dedicated unit tests separate from integration tests
2. **Error path coverage:** Most error handling paths are untested
3. **Determinism:** Several tests rely on probabilistic outcomes which could be flaky
4. **Mocking:** No use of mocks for GameEngine in integration tests limits control over test scenarios

---

## Recommended Test Additions (Prioritized)

### Priority 1 (Must Have)

1. **Unit tests for `create_strategy`** - All 7 strategy types + 2 error paths
2. **Unit tests for `create_betting_system`** - All 8 system types + 6 error paths
3. **Error handling tests** - Invalid config, exception during session

### Priority 2 (Should Have)

4. **Bonus bet calculation tests** - All 4 conditional branches
5. **Paytable factory tests** - All variants for main and bonus
6. **Deterministic stop condition tests** - Using mock engines

### Priority 3 (Nice to Have)

7. **Property-based reproducibility tests** - Using hypothesis
8. **Progress callback exception handling test**
9. **Memory/performance validation tests**

---

## Test Coverage Metrics

| Component | Integration Tests | Unit Tests | Coverage Estimate |
|-----------|------------------|------------|-------------------|
| `SimulationController.run()` | Yes | No | ~80% |
| `SimulationController._create_session()` | Indirect | No | ~60% |
| `create_strategy()` | Indirect | **No** | ~40% |
| `create_betting_system()` | Indirect (flat only) | **No** | ~20% |
| `_get_main_paytable()` | Indirect | No | ~30% |
| `_get_bonus_paytable()` | No | No | ~10% |
| `SimulationResults` | Yes | No | ~90% |
| Progress callback | Yes | No | ~95% |
| Error handling | No | No | ~10% |

**Overall Estimated Coverage:** 50-60%

---

## Files Changed in This PR

1. `scratchpads/issue-23-simulation-controller.md` - Documentation (no tests needed)
2. `src/let_it_ride/simulation/__init__.py` - Export updates (covered by import tests)
3. `src/let_it_ride/simulation/controller.py` - **Main implementation (needs more tests)**
4. `tests/integration/test_controller.py` - Test file (good coverage of happy paths)

---

## Conclusion

The PR provides a solid foundation of integration tests that verify the happy-path behavior of `SimulationController`. However, to achieve the code quality standards expected for a simulation framework with 100,000+ hands/second performance targets, the test suite should be expanded to include:

1. Dedicated unit tests for factory functions
2. Comprehensive error handling tests
3. Deterministic tests for edge cases
4. Property-based tests for statistical validation

The current test coverage is estimated at 50-60%, which should be improved to 80%+ before merging for production use.
