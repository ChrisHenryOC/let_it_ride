# Consolidated Review for PR #143

**PR Title:** feat: LIR-58 Multi-Seat Stop Condition Behavior Options

## Summary

This PR introduces "seat replacement mode" for multi-seat table sessions, allowing seats that hit individual stop conditions to be reset with fresh bankroll rather than sitting out. The implementation is well-structured with comprehensive unit tests (540+ lines), maintains backward compatibility with classic mode, and follows established codebase patterns. The main gap is that the `table_total_rounds` parameter is not yet exposed through YAML configuration, limiting the feature to programmatic use only.

## Issue Matrix

| # | Severity | Issue | File:Line | Reviewer(s) | In PR Scope? | Actionable? |
|---|----------|-------|-----------|-------------|--------------|-------------|
| 1 | High | Redundant stop condition checks (before AND after each round in seat replacement mode) | table_session.py:460-462, 522-524 | Code Quality, Performance | Yes | Yes |
| 2 | High | No integration tests for seat replacement mode | test_multi_seat.py | Test Coverage | Yes | Yes |
| 3 | High | `table_total_rounds` not exposed in YAML config or `create_table_session_config()` | models.py, utils.py | Test Coverage, Docs | No | No |
| 4 | Medium | `IN_PROGRESS` as StopReason is semantically confusing | session.py:118-119 | Code Quality | Yes | Yes |
| 5 | Medium | Implicit dict iteration ordering for seat_results | table_session.py:593-596 | Code Quality | Yes | Yes |
| 6 | Medium | BankrollTracker object recreation on every seat reset | table_session.py:195 | Performance | Yes | No |
| 7 | Medium | List copy in `_build_seat_replacement_result` | table_session.py:581 | Performance | Yes | Yes |
| 8 | Medium | Repeated property access for `seat_replacement_mode` | table_session.py:460, 522, 540 | Performance | Yes | Yes |
| 9 | Medium | No property-based testing for seat replacement invariants | test_table_session.py | Test Coverage | Yes | No |
| 10 | Medium | Missing test for concurrent stop condition triggers | test_table_session.py | Test Coverage | Yes | Yes |
| 11 | Low | Type annotation could be more precise for `completed_sessions` | table_session.py:133-143 | Code Quality | Yes | Yes |
| 12 | Low | Assertion duplicates semantic check from `seat_replacement_mode` | table_session.py:420 | Code Quality | Yes | No |
| 13 | Low | Test uses `type: ignore` instead of proper mock | test_table_session.py:1300 | Code Quality | Yes | Yes |
| 14 | Low | `completed_sessions` list grows unbounded | table_session.py:159 | Performance, Security | Yes | No |
| 15 | Low | Floating-point comparison for profit | table_session.py:302-307 | Security | No | No |
| 16 | Low | Scratchpad could document test strategy | issue-142-multi-seat-stop-condition.md | Docs | Yes | Yes |
| 17 | Low | Minor docstring enhancement for IN_PROGRESS | session.py:118-119 | Docs | Yes | Yes |

## Actionable Issues

Issues where both "In PR Scope" AND "Actionable" are Yes:

### High Severity

**#1: Redundant stop condition checks**
- **Location:** `table_session.py:460-462, 522-524`
- **Issue:** In seat replacement mode, `_check_seat_stop_condition()` is called for every seat both before AND after playing each round, doubling check overhead unnecessarily.
- **Recommendation:** Remove the pre-round check (lines 460-462). Stop conditions are checked at the end of the previous round, making the pre-round check redundant. Verify no edge cases with `max_hands` counting.

**#2: No integration tests for seat replacement mode**
- **Location:** `tests/integration/test_multi_seat.py`
- **Issue:** The new functionality lacks end-to-end testing through the full simulation stack.
- **Recommendation:** Add a `TestSeatReplacementIntegration` test class with tests for full config, reproducibility with seed, and results in simulation results.

### Medium Severity

**#4: `IN_PROGRESS` as StopReason is semantically awkward**
- **Location:** `session.py:118-119`
- **Issue:** A session "in progress" hasn't stopped, yet it's assigned a "stop reason."
- **Recommendation:** Consider using `Optional[StopReason]` with `None` for in-progress, or add a separate `is_complete: bool` field.

**#5: Implicit dict iteration ordering**
- **Location:** `table_session.py:593-596`
- **Issue:** `seat_results` population relies on dict insertion order rather than explicit seat number ordering.
- **Recommendation:** Iterate explicitly: `for seat_number in sorted(seat_sessions.keys()):`

**#7: List copy in result building**
- **Location:** `table_session.py:581`
- **Issue:** `list(seat_state.completed_sessions)` creates unnecessary copy.
- **Recommendation:** If mutation is not needed, iterate directly or use slice `[:]` for shallow copy.

**#8: Cache `seat_replacement_mode`**
- **Location:** `table_session.py:460, 522, 540`
- **Issue:** Property accessed multiple times per round.
- **Recommendation:** Cache in `__init__`: `self._seat_replacement_mode = config.table_total_rounds is not None`

**#10: Missing concurrent stop condition test**
- **Location:** `test_table_session.py`
- **Issue:** No test covers multiple seats hitting stop conditions in the same round.
- **Recommendation:** Add test where multiple seats hit win_limit simultaneously.

### Low Severity

**#11, #13, #16, #17:** Minor improvements to type annotations, test mocks, and documentation. See individual reviewer files for details.

## Deferred Issues

Issues where "In PR Scope" OR "Actionable" is No:

| # | Issue | Reason for Deferral |
|---|-------|---------------------|
| 3 | `table_total_rounds` not in YAML config | Requires changes to models.py and utils.py (not in PR). Should be a follow-up PR or documented as limitation. |
| 6 | BankrollTracker object recreation | Would require adding `reset()` method to BankrollTracker class (architectural change). |
| 9 | No property-based testing | Requires adding hypothesis dependency and new testing patterns. |
| 12 | Assertion duplicates check | Acceptable for type narrowing; no change needed. |
| 14 | Unbounded list growth | Edge case in extreme configurations; document as known limitation. |
| 15 | Floating-point comparison | Pre-existing pattern in codebase, not introduced by this PR. |

## Reviewer Recommendations

### Security Review: **APPROVE**
No critical or high-severity security issues. Low-severity items are edge cases.

### Overall Assessment
The PR is well-implemented with good test coverage and documentation. Recommend addressing the High and Medium actionable issues before merge, particularly:
1. Removing redundant stop condition checks (performance)
2. Adding integration tests (confidence)
3. Explicitly sorting seat iteration (correctness)

The missing YAML configuration support (#3) should either be addressed in a follow-up PR or explicitly documented as a known limitation that the feature is currently API-only.
