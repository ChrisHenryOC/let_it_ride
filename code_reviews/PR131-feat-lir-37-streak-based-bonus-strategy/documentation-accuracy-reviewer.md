# Documentation Accuracy Review: PR #131 - LIR-37 Streak-Based Bonus Strategy

## Summary

This PR implements the `StreakBasedBonusStrategy` class for adjusting bonus bets based on win/loss streaks. The documentation quality is generally good with clear docstrings on the class and methods. However, there are inconsistencies between the strategy's validation behavior and the config model validation, and the sample configuration file lacks an example for the streak_based bonus strategy type.

## Findings

### Medium Severity

#### 1. Inconsistency between Strategy Validation and Config Model Validation

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/strategy/bonus.py:362-365`

The docstring and implementation state:
```python
Raises:
    ValueError: If base_amount is negative or streak_length < 1.
```

However, the actual validation is:
```python
if base_amount < 0:
    raise ValueError("base_amount must be non-negative")
```

This allows `base_amount=0`, but the config model at `/Users/chrishenry/source/let_it_ride/src/let_it_ride/config/models.py:620` uses `Field(gt=0)` which requires `base_amount > 0`. This creates an inconsistency where:
- Direct instantiation of `StreakBasedBonusStrategy` accepts `base_amount=0`
- Creation via config/factory requires `base_amount > 0`

The docstring should clarify this difference or the validations should be aligned.

#### 2. Missing Configuration Example in sample_config.yaml

**File:** `/Users/chrishenry/source/let_it_ride/configs/sample_config.yaml:146-148`

The sample config file lists `streak_based` as a valid strategy type in the comment:
```yaml
# Strategy type: never, always, static, bankroll_conditional,
#                streak_based, session_conditional, combined, custom
```

But unlike `static` and `bankroll_conditional` which have commented example configurations, there is no example for `streak_based`. This is inconsistent with the documentation approach taken for other bonus strategy types.

The requirements document at `/Users/chrishenry/source/let_it_ride/docs/let_it_ride_requirements.md:843-882` provides a complete example that should be mirrored in sample_config.yaml.

#### 3. BonusStrategy Protocol Does Not Document Optional Methods

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/strategy/bonus.py:50-67`

The `BonusStrategy` protocol only defines `get_bonus_bet()`. The new `StreakBasedBonusStrategy` adds `record_result()` and `reset()` methods that are not part of the protocol. This means:
- Callers using the protocol type hint will not see these methods
- The class does not explicitly note that it extends beyond the protocol

The class docstring should document that this strategy has additional methods for state management:
```python
"""Strategy that adjusts bonus bets based on win/loss streaks.

...

Note:
    This strategy maintains internal state and provides additional methods
    beyond the BonusStrategy protocol:
    - record_result(): Must be called after each hand to update streak state
    - reset(): Resets the strategy to initial state
"""
```

#### 4. README Does Not Document streak_based Bonus Strategy

**File:** `/Users/chrishenry/source/let_it_ride/README.md:162`

The README lists bonus strategy types:
```markdown
- `bonus_strategy`: Three Card Bonus betting (never, always, static, bankroll_conditional)
```

This list is now incomplete - it should include `streak_based` as a newly implemented option.

#### 5. configs/README.md Missing streak_based Strategy Description

**File:** `/Users/chrishenry/source/let_it_ride/configs/README.md:108`

The bonus_strategy section in the table only mentions "Three Card Bonus betting (never, always, conditional, etc.)". With the implementation of streak_based, this should be more specific or the list should be updated.

### Notes on Docstring Quality (No Issues Found)

The following documentation aspects are well-implemented:

1. **Class docstring** (`bonus.py:315-321`): Clearly describes the purpose and capability of the strategy
2. **`__init__` docstring** (`bonus.py:345-362`): Complete Args documentation with valid values listed
3. **`get_bonus_bet` docstring** (`bonus.py:382-390`): Clear Args and Returns
4. **`record_result` docstring** (`bonus.py:253-259`): Documents parameters including the `None` case for `bonus_won`
5. **`current_multiplier` property** (`bonus.py:327-356`): Well-documented return value semantics for different action types
6. **Config model docstring** (`models.py:606-616`): Has complete Attributes list

## Recommendations

1. Align validation between the strategy class and config model (either both allow 0 or neither does)
2. Add a commented example for `streak_based` configuration in sample_config.yaml
3. Update README.md to include `streak_based` in the bonus strategy list
4. Add a note to the class docstring about the additional state management methods
5. Consider whether `record_result()` and `reset()` should be added to the `BonusStrategy` protocol as optional methods, or if a separate `StatefulBonusStrategy` protocol should be created
