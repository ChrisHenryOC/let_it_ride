# Code Quality Review for PR #131

## Summary

This PR implements a `StreakBasedBonusStrategy` class for adjusting bonus bets based on win/loss streaks. The implementation follows project conventions with `__slots__`, comprehensive docstrings, and thorough test coverage (48 new tests). While the code is well-structured and functional, there are code duplication issues between `_calculate_bet()` and `current_multiplier`, and the use of string literals for trigger/action types instead of type-safe enums reduces maintainability.

## Findings

### Critical

None identified.

### High

None identified.

### Medium

#### M-1: Code Duplication Between _calculate_bet() and current_multiplier
**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/strategy/bonus.py:399-427` and `501-531`

The bet calculation logic is duplicated between `_calculate_bet()` and `current_multiplier`. Both methods contain identical conditional chains for handling `multiply`, `increase`, and `decrease` action types with the same max_multiplier capping logic.

```python
# In _calculate_bet() (lines 408-423)
if self._action_type == "multiply":
    multiplier = self._action_value**triggers
    if self._max_multiplier is not None:
        multiplier = min(multiplier, self._max_multiplier)
    return self._base_amount * multiplier
...

# In current_multiplier (lines 513-529) - nearly identical logic
if self._action_type == "multiply":
    multiplier = self._action_value**triggers
    if self._max_multiplier is not None:
        multiplier = min(multiplier, self._max_multiplier)
    return multiplier
```

**Recommendation:** Extract the multiplier calculation into a private `_calculate_multiplier()` method and have both `_calculate_bet()` and `current_multiplier` use it.

#### M-2: Code Duplication Between _matches_trigger() and _should_reset()
**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/strategy/bonus.py:456-488`

The methods `_matches_trigger()` and `_should_reset()` contain nearly identical conditional chains for checking trigger/reset conditions. The only difference is the attribute being checked (`_trigger` vs `_reset_on`) and the handling of the "never" case.

```python
# _matches_trigger (lines 458-470)
if self._trigger == "main_win":
    return main_won
if self._trigger == "main_loss":
    return not main_won
...

# _should_reset (lines 474-488)
if self._reset_on == "main_win":
    return main_won
if self._reset_on == "main_loss":
    return not main_won
...
```

**Recommendation:** Extract a private helper method `_matches_event(event_type: str, main_won: bool, bonus_won: bool | None) -> bool` that both methods can call.

#### M-3: String Literals Instead of Type-Safe Enums for Trigger and Action Types
**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/strategy/bonus.py:337-340`

The constructor accepts `trigger: str`, `action_type: str`, and `reset_on: str` parameters without validation. Invalid values like `trigger="invalid"` would silently be accepted and cause `_matches_trigger()` to always return `False`.

```python
def __init__(
    self,
    base_amount: float,
    trigger: str,  # No validation of allowed values
    streak_length: int,
    action_type: str,  # No validation of allowed values
    ...
)
```

**Recommendation:** Either:
1. Add validation in `__init__` that checks values against allowed sets, raising `ValueError` for invalid inputs, or
2. Use `Literal` types for better IDE support: `trigger: Literal["main_win", "main_loss", "bonus_win", "bonus_loss", "any_win", "any_loss"]`

The config models (`StreakBasedBonusConfig`) likely already have validation, but the strategy class itself should be defensive.

#### M-4: Missing Validation for action_value Parameter
**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/strategy/bonus.py:363-369`

While `base_amount`, `streak_length`, and `max_multiplier` are validated in `__init__`, `action_value` has no validation. A negative `action_value` with `action_type="decrease"` would effectively become an increase action, which may be unexpected.

```python
if base_amount < 0:
    raise ValueError("base_amount must be non-negative")
if streak_length < 1:
    raise ValueError("streak_length must be at least 1")
if max_multiplier is not None and max_multiplier < 1:
    raise ValueError("max_multiplier must be at least 1")
# No validation for action_value
```

**Recommendation:** Add validation for `action_value` - at minimum ensure it is non-negative, or validate based on action_type (e.g., multiply action should have value > 0).

---

## Positive Observations

### Strong Adherence to Project Standards

1. **`__slots__` usage:** Properly defined on line 323 for memory efficiency
2. **Comprehensive docstrings:** All public methods have Args/Returns documentation
3. **Type annotations:** All methods have complete type hints

### Clean Code Principles

1. **Single Responsibility:** The class focuses solely on streak-based bonus betting logic
2. **Descriptive naming:** Methods like `_matches_trigger()`, `_should_reset()`, and `record_result()` clearly convey intent
3. **State management:** Clear separation between mutable state (`_current_streak`, `_is_betting`) and configuration

### Excellent Test Coverage

- 48 new tests covering all trigger types, action types, reset behaviors, and edge cases
- Tests organized into logical classes (`TestStreakBasedBonusStrategy`, `TestStreakBasedBonusStrategyFactory`, etc.)
- Good edge case coverage including zero base amount and max_multiplier capping

### Proper Factory Integration

The `create_bonus_strategy()` factory was cleanly extended (lines 587-601) following the existing pattern for other strategy types.

---

## Recommendations Summary

| Priority | Item | Effort |
|----------|------|--------|
| Medium | Extract shared multiplier calculation logic (M-1) | 15 min |
| Medium | Extract shared event matching logic (M-2) | 10 min |
| Medium | Add validation or Literal types for trigger/action/reset_on (M-3) | 15 min |
| Medium | Add validation for action_value parameter (M-4) | 5 min |

---

## Files Reviewed

- `src/let_it_ride/strategy/bonus.py` (220 lines added)
- `src/let_it_ride/strategy/__init__.py` (exports added)
- `tests/unit/strategy/test_bonus.py` (870 lines added)
- `scratchpads/issue-40-streak-based-bonus.md` (implementation notes)

---

## Verdict

**APPROVE** - The implementation is well-designed and thoroughly tested. The identified issues are maintainability improvements that do not block merging. The code correctly implements the streak-based bonus strategy requirements and integrates cleanly with the existing bonus strategy system.
