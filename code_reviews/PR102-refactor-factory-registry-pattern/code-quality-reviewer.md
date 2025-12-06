# Code Quality Review: PR #102 - Refactor Factory Functions to Registry Pattern

**Reviewer:** Code Quality Reviewer
**Date:** 2025-12-07
**PR:** #102
**Files Changed:** controller.py (refactored), test_factories.py (new), test_controller.py (formatting)

## Summary

This PR successfully refactors the `create_strategy()` and `create_betting_system()` factory functions from if-elif chains to a dict-based registry pattern. This addresses finding H1 from PR #96 review, improving adherence to the Open-Closed Principle. The implementation is well-structured with comprehensive unit tests covering all strategy and betting system types, including error paths. The refactoring maintains full backward compatibility while improving extensibility and reducing cyclomatic complexity.

---

## Findings by Severity

### Critical

*None identified.*

### High

*None identified.*

### Medium

#### M1: Registry Pattern Type Hint Inconsistency

**File:** `src/let_it_ride/simulation/controller.py`
**Lines:** 222-224

The betting system registry uses a union type with `None` to indicate unimplemented types:

```python
_BETTING_SYSTEM_FACTORIES: dict[
    str, Callable[[BankrollConfig], BettingSystem] | None
] = {
    # ...
    "proportional": None,  # Not yet implemented
    "custom": None,  # Not yet implemented
}
```

While this works, it creates a two-step lookup pattern in `create_betting_system()` (lines 250-258):
1. Check if key exists in registry
2. Check if factory is not None

**Consideration:** An alternative approach would be to use sentinel factory functions that raise `NotImplementedError`, keeping the registry uniformly callable:

```python
def _not_implemented(name: str) -> Callable[[BankrollConfig], BettingSystem]:
    def factory(config: BankrollConfig) -> BettingSystem:
        raise NotImplementedError(f"Betting system type '{name}' is not yet implemented")
    return factory

_BETTING_SYSTEM_FACTORIES: dict[str, Callable[[BankrollConfig], BettingSystem]] = {
    # ...
    "proportional": _not_implemented("proportional"),
    "custom": _not_implemented("custom"),
}
```

This would simplify `create_betting_system()` and ensure the registry type is uniform. However, the current implementation is functionally correct and the explicit `None` values clearly communicate "not implemented" status.

**Impact:** Minor maintainability concern; current implementation is acceptable.

---

#### M2: Test Bypasses Pydantic Validation Using `__new__`

**File:** `tests/unit/simulation/test_factories.py`
**Lines:** 136-146, 151-160, 249-280

Multiple tests bypass Pydantic validation using `__new__` and `object.__setattr__`:

```python
# Bypass Pydantic validation to test factory's own validation
config = StrategyConfig.__new__(StrategyConfig)
object.__setattr__(config, "type", "custom")
object.__setattr__(config, "custom", None)
# ...
```

While this is a valid testing technique to test the factory's own validation (separate from Pydantic's), it:
1. Creates a tight coupling to internal Pydantic implementation
2. Could break if Pydantic changes how model initialization works
3. Is somewhat fragile and non-obvious

**Recommendation:** The tests clearly document why this approach is used (comments on lines 133-135, 150-151, etc.), which mitigates readability concerns. Consider adding a helper function to centralize this pattern:

```python
def _create_invalid_strategy_config(type_: str, **attrs: Any) -> StrategyConfig:
    """Create a StrategyConfig bypassing Pydantic validation for testing factory logic."""
    config = StrategyConfig.__new__(StrategyConfig)
    object.__setattr__(config, "type", type_)
    for name, value in attrs.items():
        object.__setattr__(config, name, value)
    return config
```

**Impact:** Test maintainability; current implementation is adequately documented.

---

### Low

#### L1: Minor Code Duplication in Betting Factory Functions

**File:** `src/let_it_ride/simulation/controller.py`
**Lines:** 62-96

The betting system factory functions follow a repetitive pattern:
1. Check if config section is None
2. Raise ValueError if missing
3. Extract config section to local variable
4. Return instantiated object

**Impact:** No action needed - the duplication is acceptable because each factory has distinct parameter mappings, and extracting a common validation pattern would likely reduce clarity.

---

## Positive Observations

1. **Addresses Prior Review Finding:** This PR directly addresses H1 from PR #96, implementing the recommended registry pattern for factory functions.

2. **Clean Registry Implementation:** The strategy registry (lines 97-106) is well-organized:
   ```python
   _STRATEGY_FACTORIES: dict[str, Callable[[StrategyConfig], Strategy]] = {
       "basic": lambda _: BasicStrategy(),
       "always_ride": lambda _: AlwaysRideStrategy(),
       # ...
   }
   ```

3. **Proper Helper Function Extraction:** The `_create_custom_strategy()` function (lines 70-94) is cleanly extracted to handle the complex custom strategy creation logic.

4. **Individual Betting System Factory Functions:** Each betting system has its own factory function (lines 147-216), making the code easier to maintain and test:
   - `_create_flat_betting()`
   - `_create_martingale_betting()`
   - `_create_reverse_martingale_betting()`
   - `_create_paroli_betting()`
   - `_create_dalembert_betting()`
   - `_create_fibonacci_betting()`

5. **Comprehensive Test Coverage:** The test file covers:
   - All strategy types (basic, always_ride, always_pull, conservative, aggressive, custom)
   - All implemented betting systems (flat, martingale, reverse_martingale, paroli, dalembert, fibonacci)
   - Not-implemented betting systems (proportional, custom)
   - Unknown type error handling
   - Missing config section error handling
   - Protocol compliance verification

6. **Registry Exports for Testing:** The registries are exported for direct testing:
   ```python
   from let_it_ride.simulation.controller import (
       _BETTING_SYSTEM_FACTORIES,
       _STRATEGY_FACTORIES,
       # ...
   )
   ```

7. **Clear Error Messages:** Factory functions provide descriptive error messages:
   ```python
   raise ValueError(f"Unknown strategy type: {config.type}")
   raise NotImplementedError(f"Betting system type '{system_type}' is not yet implemented")
   ```

8. **Type Annotations Throughout:** All functions have complete type annotations, following project standards.

9. **Documentation:** Helper functions have clear docstrings explaining their purpose.

10. **Test Method Naming:** Test method names are descriptive and follow a consistent pattern (e.g., `test_create_basic_strategy`, `test_unknown_strategy_type_raises`).

---

## Backward Compatibility Analysis

The refactoring maintains full backward compatibility:

1. **Public API Unchanged:** `create_strategy()` and `create_betting_system()` signatures are identical
2. **Error Types Preserved:** Same `ValueError` and `NotImplementedError` exceptions raised
3. **Error Message Format:** Error messages are consistent with pre-refactor behavior
4. **Return Types:** Factory functions return the same strategy/betting system instances

---

## Code Metrics

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Cyclomatic Complexity (create_strategy) | ~7 | 2 | -71% |
| Cyclomatic Complexity (create_betting_system) | ~10 | 3 | -70% |
| Lines of Code (controller.py) | ~310 | ~340 | +30 |
| Test Coverage | Existing | +502 lines | Comprehensive |

---

## Recommendations (Prioritized by Impact)

### Medium Priority

1. **Consider centralizing Pydantic bypass pattern** - Create a test helper for bypassing Pydantic validation if this pattern is used elsewhere in the test suite.

### Low Priority

2. **Optional: Use sentinel factories** - Could convert `None` entries to factory functions that raise `NotImplementedError` for cleaner type uniformity (but current approach is acceptable).

---

## Files Reviewed

| File | Assessment |
|------|------------|
| `src/let_it_ride/simulation/controller.py` | Excellent - clean registry pattern implementation |
| `tests/unit/simulation/test_factories.py` | Excellent - comprehensive test coverage |
| `tests/integration/test_controller.py` | Minor formatting change only |

---

## Conclusion

This is an excellent refactoring that successfully converts if-elif chains to a registry pattern, addressing the maintainability concern raised in PR #96. The implementation follows Python best practices with proper type hints, clear error handling, and comprehensive tests. The code is well-organized with appropriate separation between simple (lambda-based) and complex (function-based) factory implementations.

The PR improves adherence to the Open-Closed Principle - adding new strategy or betting system types now requires:
1. Adding an entry to the appropriate registry dict
2. Optionally creating a helper factory function if initialization is complex

This is significantly cleaner than modifying if-elif chains.

**Recommendation:** Approve for merge. No blocking issues identified.
