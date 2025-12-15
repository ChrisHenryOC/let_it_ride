# Consolidated Review for PR #140

**PR Title:** feat: LIR-56 Table Configuration Integration with CLI

## Summary

This PR integrates multi-seat table configuration into `FullConfig` and enables `TableSession` usage via the CLI when `num_seats > 1`. The implementation follows existing patterns well, maintains backwards compatibility with `num_seats=1` default, and includes solid integration tests. The main concerns are: (1) missing bonus strategy support in multi-seat mode, (2) test coverage gaps for parallel execution and utility functions, and (3) minor documentation updates needed for the configs README.

## Issue Matrix

| # | Severity | Issue | File:Line | Reviewer(s) | In PR Scope? | Actionable? |
|---|----------|-------|-----------|-------------|--------------|-------------|
| 1 | High | Missing bonus strategy in multi-seat table sessions | controller.py:527-570, parallel.py:134-178 | Code Quality | Yes | Yes |
| 2 | High | No unit tests for `create_table_session_config()` | utils.py:123-147 | Test Coverage | Yes | Yes |
| 3 | High | No tests for parallel multi-seat execution path | parallel.py:134-178 | Test Coverage | Yes | Yes |
| 4 | Medium | Code duplication between sequential and parallel multi-seat handling | controller.py:416-441, parallel.py:216-243 | Code Quality | Yes | No (refactoring) |
| 5 | Medium | Composite ID calculation lacks documentation | parallel.py:228-229 | Code Quality | Yes | Yes |
| 6 | Medium | No tests for formatter multi-seat display logic | formatters.py:162-166 | Test Coverage | Yes | Yes |
| 7 | Medium | Missing edge case tests (stop conditions, parallel workers, bonus) | test_multi_seat.py | Test Coverage | Yes | Partial |
| 8 | Medium | Missing multi_seat_example.yaml entry in configs/README.md | configs/README.md | Documentation | No | Yes |
| 9 | Medium | Missing `table` section in configs/README.md Key Sections | configs/README.md | Documentation | No | Yes |
| 10 | Medium | Potential resource exhaustion with max sessions * seats | parallel.py:474-475 | Security | Yes | Yes (add validation) |
| 11 | Medium | Redundant `calculate_bonus_bet()` calls per session | controller.py:547-548, parallel.py:157-158 | Performance | Yes | Yes |
| 12 | Low | Magic numbers in seat validation tests | test_models.py:885-886 | Code Quality | Yes | Yes |
| 13 | Low | Result list could be pre-allocated in multi-seat mode | controller.py:430-432 | Performance | Yes | Yes |
| 14 | Low | Minor docstring detail omission in `_create_table_session` | controller.py:527-545 | Documentation | Yes | Yes |

## Actionable Issues

Issues where **In PR Scope = Yes** AND **Actionable = Yes**:

### High Priority

1. **#1 - Missing bonus strategy in multi-seat mode**
   - The `_create_table_session` and `_run_single_table_session` don't accept `bonus_strategy_factory`
   - Single-seat sessions properly create fresh bonus strategies per session
   - Multi-seat ignores dynamic bonus strategies like `bankroll_conditional`
   - **Fix:** Either add `bonus_strategy_factory` parameter or add validation that rejects incompatible configs

2. **#2 - No unit tests for `create_table_session_config()`**
   - New utility function lacks dedicated unit tests
   - Should test all field mappings, various bonus_bet values, None for limits

3. **#3 - No tests for parallel multi-seat execution**
   - `_run_single_table_session()` untested
   - `run_worker_sessions()` multi-seat branch untested
   - No reproducibility test for parallel + multi-seat

### Medium Priority

4. **#5 - Document composite ID scheme**
   - Add comment explaining `session_id * num_seats + seat_idx` formula
   - Or extract to helper function with docstring

5. **#6 - Add formatter tests for multi-seat display**
   - Verify "Table Seats" row appears when `num_seats > 1`
   - Verify row is absent when `num_seats == 1`

6. **#10 - Add validation for max results**
   - `num_sessions * num_seats` could create 600M entry list
   - Add validation or document memory implications

7. **#11 - Hoist redundant computations**
   - Move `calculate_bonus_bet()` and `create_table_session_config()` outside session loops
   - Pass pre-computed values to session creation methods

### Low Priority

8. **#12 - Use constants for seat limits in tests**
   - Define `MIN_SEATS = 1`, `MAX_SEATS = 6` constants

9. **#13 - Pre-allocate result list for multi-seat**
   - Minor optimization: pre-allocate based on `num_sessions * num_seats`

10. **#14 - Enhance `_create_table_session` docstring**
    - Add note about RNG seed source for reproducibility

## Deferred Issues

| # | Issue | Reason |
|---|-------|--------|
| 4 | Code duplication between sequential/parallel paths | Requires refactoring beyond scope |
| 8 | Missing README entry for multi_seat_example.yaml | File not in PR scope |
| 9 | Missing `table` section in README | File not in PR scope |

**Note:** Issues #8 and #9 are documentation updates to `configs/README.md` which was not modified by this PR. These could be added to this PR or handled separately.

## Positive Observations

- Backwards compatibility properly maintained with `num_seats=1` default
- Single-seat optimization path preserved (no regression for common case)
- Excellent inline documentation in `multi_seat_example.yaml`
- Good use of existing factory patterns for stateful components
- Proper input validation via Pydantic with `Field(ge=1, le=6)`
- Security-conscious YAML handling with `yaml.safe_load()`
- Integration tests verify multi-seat simulation basics
- All new functions have accurate docstrings

## Recommendation

**Approve with changes** - The core implementation is solid. Recommend addressing:
1. **Must fix:** #1 (bonus strategy support) - could cause incorrect behavior
2. **Should fix:** #2, #3 (test coverage for new code paths)
3. **Nice to have:** #5, #11 (documentation and performance)
