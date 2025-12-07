# LIR-52: Error Handling and Edge Case Tests for SimulationController

**GitHub Issue:** [#99](https://github.com/ChrisHenryOC/let_it_ride/issues/99)

## Summary

Add comprehensive error handling and edge case tests for `SimulationController` and related components.

## Analysis

### Source Code Location

- **SimulationController:** `src/let_it_ride/simulation/controller.py`
- **Key method:** `_create_session()` lines 399-464, specifically bonus bet calculation at lines 423-437

### Bonus Bet Calculation Logic (lines 423-437)

```python
bonus_bet = 0.0
if self._config.bonus_strategy.enabled:
    if self._config.bonus_strategy.always is not None:
        bonus_bet = self._config.bonus_strategy.always.amount
    elif self._config.bonus_strategy.static is not None:
        if self._config.bonus_strategy.static.amount is not None:
            bonus_bet = self._config.bonus_strategy.static.amount
        elif self._config.bonus_strategy.static.ratio is not None:
            bonus_bet = bankroll_config.base_bet * self._config.bonus_strategy.static.ratio
```

### Conditional Branches to Test

1. **Bonus disabled** (`enabled=False`) → `bonus_bet = 0.0`
2. **Bonus enabled with `always` config** → Use `always.amount`
3. **Bonus enabled with `static.amount`** → Use `static.amount`
4. **Bonus enabled with `static.ratio`** → Calculate `base_bet * ratio`

## Implementation Plan

### 1. Error Handling Tests

- [ ] Test progress callback that raises an exception
- [ ] Test with mocked session that raises during execution

### 2. Bonus Bet Calculation Tests

- [ ] Test bonus disabled (bonus_bet should be 0)
- [ ] Test bonus enabled with `always` configuration
- [ ] Test bonus enabled with `static.amount`
- [ ] Test bonus enabled with `static.ratio`
- [ ] Test ratio calculation with various base_bet values

### 3. Configuration Edge Cases

- [ ] Test with max_hands=1 (single hand session)
- [ ] Test with very high win/loss limits (never triggered)
- [ ] Test with zero win/loss limits (always triggered immediately)

## Test File Location

Tests will be added to: `tests/integration/test_controller.py`

New test classes:
- `TestBonusBetCalculation` - All bonus bet calculation branches
- `TestErrorHandling` - Error scenarios
- `TestEdgeCases` - Configuration edge cases
