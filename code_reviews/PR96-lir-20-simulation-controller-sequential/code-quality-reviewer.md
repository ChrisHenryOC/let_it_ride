# Code Quality Review: PR #96 - LIR-20 Simulation Controller (Sequential)

**Reviewer:** Code Quality Reviewer
**Date:** 2025-12-06
**PR:** #96
**Files Changed:** controller.py (+433 lines), test_controller.py (+408 lines), __init__.py (+19 lines)

## Summary

This PR implements a well-structured `SimulationController` that orchestrates sequential multi-session simulations with proper RNG seeding for reproducibility. The implementation follows good separation of concerns with factory functions for strategy and betting system instantiation. The code demonstrates excellent adherence to project standards including `__slots__` usage, comprehensive type hints, and proper error handling. Previous review findings (H1, M1, M2, M3) have been addressed. Remaining issues are primarily around maintainability and test robustness.

---

## Findings by Severity

### Critical

*None identified.*

### High

#### H1: Factory Functions Not Easily Extensible (Open-Closed Principle)

**File:** `src/let_it_ride/simulation/controller.py`
**Lines:** 89-138 (`create_strategy`) and 141-224 (`create_betting_system`)

Both factory functions use long if-elif chains that require modification whenever new strategy or betting system types are added. This violates the Open-Closed Principle.

```python
# Current pattern (6 branches for strategies, 8 for betting systems):
if strategy_type == "basic":
    return BasicStrategy()
if strategy_type == "always_ride":
    return AlwaysRideStrategy()
# ... 4 more branches
```

**Recommendation:** Refactor to registry pattern:

```python
STRATEGY_FACTORIES: dict[str, Callable[[StrategyConfig], Strategy]] = {
    "basic": lambda _: BasicStrategy(),
    "always_ride": lambda _: AlwaysRideStrategy(),
    # ...
}

def create_strategy(config: StrategyConfig) -> Strategy:
    factory = STRATEGY_FACTORIES.get(config.type)
    if factory is None:
        raise ValueError(f"Unknown strategy type: {config.type}")
    return factory(config)
```

**Impact:** Maintainability - each new type requires modifying multiple files instead of adding to a registry.

---

### Medium

#### M1: Closure Over Config in `betting_system_factory`

**File:** `src/let_it_ride/simulation/controller.py`
**Lines:** 322-323

The inline closure captures `self._config.bankroll` which is evaluated on each call but could be simplified:

```python
def betting_system_factory() -> BettingSystem:
    return create_betting_system(self._config.bankroll)
```

While functionally correct, this creates a new function object each call to `run()`. Since `run()` is typically called once per controller instance, this is a minor concern, but moving to an instance method or pre-computing the config would be cleaner.

**Impact:** Minor code clarity issue.

---

#### M2: Test `test_unseeded_runs_differ` is Non-Deterministic

**File:** `tests/integration/test_controller.py`
**Lines:** 241-257

```python
def test_unseeded_runs_differ(self) -> None:
    """Test that runs without seed produce different results."""
    # ...
    # This could theoretically fail but is extremely unlikely
    assert profits1 != profits2
```

The test acknowledges it "could theoretically fail" which makes it a potentially flaky test. While extremely unlikely, this violates the principle of deterministic tests.

**Recommendation:** Either:
1. Remove this test since `test_different_seeds_produce_different_results` already covers the intent
2. Use a statistical approach with multiple runs and probability thresholds
3. Mock the system entropy source for deterministic behavior

---

#### M3: Complex Bonus Bet Calculation Logic

**File:** `src/let_it_ride/simulation/controller.py`
**Lines:** 381-395

The bonus bet calculation has nested conditionals that could be simplified:

```python
bonus_bet = 0.0
if self._config.bonus_strategy.enabled:
    if self._config.bonus_strategy.always is not None:
        bonus_bet = self._config.bonus_strategy.always.amount
    elif self._config.bonus_strategy.static is not None:
        if self._config.bonus_strategy.static.amount is not None:
            bonus_bet = self._config.bonus_strategy.static.amount
        elif self._config.bonus_strategy.static.ratio is not None:
            bonus_bet = (
                bankroll_config.base_bet
                * self._config.bonus_strategy.static.ratio
            )
```

**Recommendation:** Extract to a helper method `_calculate_bonus_bet()` for clarity and testability.

---

#### M4: Missing Unit Tests for Factory Functions

**File:** `tests/integration/test_controller.py`

The factory functions `create_strategy()` and `create_betting_system()` are only tested indirectly through integration tests. Error paths (unknown types, missing config sections) lack dedicated unit tests.

**Missing test scenarios:**
- `create_strategy()` with unknown type raises `ValueError`
- `create_strategy()` with `custom` type but no `config.custom` raises `ValueError`
- `create_betting_system()` with `proportional` type raises `NotImplementedError`
- `create_betting_system()` with missing sub-config (e.g., martingale without martingale config)

---

### Low

#### L1: Magic Number in RNG Seed Range

**File:** `src/let_it_ride/simulation/controller.py`
**Line:** 333

```python
session_seed = master_rng.randint(0, 2**31 - 1)
```

The magic number `2**31 - 1` (2147483647) represents the maximum 32-bit signed integer but lacks documentation.

**Recommendation:**
```python
_MAX_SEED = 2**31 - 1  # Maximum seed for 32-bit compatibility
```

---

#### L2: Test Helper Could Validate Strategy Types

**File:** `tests/integration/test_controller.py`
**Lines:** 26-45

The `_create_strategy_config` helper accepts any string without validation:

```python
def _create_strategy_config(strategy_type: str) -> StrategyConfig:
    if strategy_type == "conservative":
        return StrategyConfig(type="conservative", conservative=ConservativeStrategyConfig())
    if strategy_type == "aggressive":
        return StrategyConfig(type="aggressive", aggressive=AggressiveStrategyConfig())
    return StrategyConfig(type=strategy_type)  # No validation
```

Passing an invalid type would create a config that fails later, making debugging harder.

---

#### L3: Docstring Says "Raises" But Implementation Changed

**File:** `src/let_it_ride/simulation/controller.py`
**Lines:** 227-237

The `_get_main_paytable` docstring documents `NotImplementedError` which is now correctly raised, but `_get_bonus_paytable` (lines 249-274) documents `ValueError` for unknown types - verify this matches the implementation (it does raise `ValueError`).

---

## Positive Observations

1. **Fixed Previous Review Findings:**
   - `SimulationResults` now uses `slots=True` (line 70)
   - `_action_to_decision` moved to module level (line 58)
   - `_session_id` parameter removed from `_create_session`
   - `_get_main_paytable` now raises `NotImplementedError` instead of silent fallback

2. **Excellent Type Hints:** All function signatures have proper type annotations including `TYPE_CHECKING` imports.

3. **Clean Separation of Concerns:** Factory functions properly encapsulate instantiation logic.

4. **Comprehensive Integration Tests:** Tests cover single/multiple sessions, reproducibility, progress callbacks, stop conditions, and strategy variants.

5. **Proper `__slots__` Usage:** Both `SimulationController` and `SimulationResults` use `__slots__`.

6. **Reproducibility Design:** Master RNG deriving session seeds ensures deterministic behavior.

7. **Good Error Messages:** Exception messages are descriptive (e.g., lines 243-245).

---

## Recommendations (Prioritized by Impact)

### High Priority

1. Consider creating follow-up issue for registry pattern refactoring (LIR-50 already tracked)
2. Add unit tests for factory function error paths (LIR-51 already tracked)

### Medium Priority

3. Extract `_calculate_bonus_bet()` helper method
4. Address non-deterministic test or add skip marker

### Low Priority

5. Add constant for max seed value
6. Enhance test helper validation

---

## Files Reviewed

| File | Lines Changed | Assessment |
|------|---------------|------------|
| `src/let_it_ride/simulation/controller.py` | +433 | Good - addresses prior findings, minor improvements suggested |
| `src/let_it_ride/simulation/__init__.py` | +19 | Good - proper exports |
| `tests/integration/test_controller.py` | +408 | Good - comprehensive coverage, one flaky test concern |
| `scratchpads/issue-23-simulation-controller.md` | +104 | N/A - planning document |

---

## Conclusion

This is a solid implementation that addresses all previously identified issues and follows project standards. The code is well-organized, properly typed, and thoroughly tested. The remaining suggestions are refinements around maintainability (registry pattern) and test robustness (non-deterministic test). Follow-up issues LIR-50 through LIR-53 are appropriately tracked for post-merge improvements. The implementation is **ready for merge**.
