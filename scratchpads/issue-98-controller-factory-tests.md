# Issue 98: LIR-51 Unit Tests for Controller Factory Functions

**GitHub Issue:** https://github.com/ChrisHenryOC/let_it_ride/issues/98

## Summary

Add unit tests for the paytable factory functions in `src/let_it_ride/simulation/controller.py`:
- `_get_main_paytable()`
- `_get_bonus_paytable()`

Note: Tests for `create_strategy()` and `create_betting_system()` already exist in `tests/unit/simulation/test_factories.py` (added in PR #102).

## Tasks

1. [ ] Add tests for `_get_main_paytable()`:
   - Test with standard type returns correct paytable
   - Test with unsupported types (liberal, tight, custom) raises NotImplementedError

2. [ ] Add tests for `_get_bonus_paytable()`:
   - Test with bonus disabled returns None
   - Test with paytable_a, paytable_b, paytable_c
   - Test with unknown type raises ValueError

3. [ ] Run tests and verify all pass
4. [ ] Run linting and type checking
