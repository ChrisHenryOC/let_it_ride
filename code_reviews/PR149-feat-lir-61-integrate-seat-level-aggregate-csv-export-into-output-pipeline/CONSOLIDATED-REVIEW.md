# Consolidated Review for PR #149

## Summary

This PR integrates seat-level aggregate CSV export into the Let It Ride simulation output pipeline by adding `analyze_session_results_by_seat()` for flattened `SessionResult` objects, a new `include_seat_aggregate` config option, and updating `CSVExporter.export_all()`. The implementation follows existing patterns, has good test coverage for happy paths, and introduces no security vulnerabilities. Key concerns are code duplication between analysis functions, missing direct unit tests for `export_seat_aggregate()`, and redundant iteration over session results in the export phase.

## Issue Matrix

| ID | Description | Severity | In PR Scope | Actionable | File:Line |
|----|-------------|----------|-------------|------------|-----------|
| CQ-1 | Code duplication between `analyze_chair_positions()` and `analyze_session_results_by_seat()` | Medium | Yes | Yes | `chair_position.py:307-358` |
| CQ-2 | Missing error handling context when `analyze_session_results_by_seat()` raises in `export_all()` | Medium | Yes | Yes | `export_csv.py:379-382` |
| CQ-3 | `num_seats` param not validated against actual results data | Medium | Yes | Deferred | `export_csv.py:327-334` |
| PERF-1 | Redundant full iteration of session_results in `export_all()` (3 passes) | High | Yes | Deferred | `export_csv.py:361-381` |
| PERF-2 | Function-level imports inside `export_all()` | Medium | Yes | Yes | `export_csv.py:352-355` |
| TEST-1 | Missing direct unit tests for `CSVExporter.export_seat_aggregate()` | High | Yes | Yes | `export_csv.py:313-325` |
| TEST-2 | No test for error propagation from `analyze_session_results_by_seat()` in `export_all()` | High | Yes | Yes | `export_csv.py:378-381` |
| TEST-3 | PUSH outcome not tested in `_aggregate_session_results_by_seat()` | Medium | Yes | Yes | `test_chair_position.py:672-709` |
| TEST-4 | `confidence_level` and `significance_level` params not tested for new function | Medium | Yes | Yes | `chair_position.py:307-311` |
| TEST-5 | Integration tests verify structure but not computed statistical values | Medium | Yes | Deferred | `test_export_csv.py:1463-1470` |
| DOC-1 | Module docstring does not list new public function | Medium | Yes | Yes | `chair_position.py:1-12` |
| DOC-2 | `export_seat_aggregate_csv()` docstring only references `analyze_chair_positions()` | Medium | Partial | Yes | `export_csv.py:440-441` |
| SEC-1 | Path traversal via prefix (pre-existing pattern) | Low | No | No | `export_csv.py:323-324` |
| SEC-2 | Default file permissions on created CSVs (pre-existing pattern) | Low | No | No | `export_csv.py:461` |

## Actionable Issues

Issues where both "In PR Scope" AND "Actionable" are Yes:

### High Priority

1. **TEST-1**: Add direct unit tests for `CSVExporter.export_seat_aggregate()` method similar to existing tests for `export_sessions()`, `export_aggregate()`, and `export_hands()`.

2. **TEST-2**: Add tests for error propagation when `analyze_session_results_by_seat()` raises `ValueError` in `export_all()`.

### Medium Priority

3. **CQ-1**: Extract common logic from `analyze_chair_positions()` and `analyze_session_results_by_seat()` into a shared private function `_build_analysis_from_aggregations()`.

4. **CQ-2**: Either document `ValueError` as a possible exception in `export_all()` docstring, or wrap with a more descriptive error message.

5. **PERF-2**: Move deferred imports to the top of the function or consolidate them.

6. **TEST-3**: Add test case with `SessionOutcome.PUSH` to verify all outcome branches.

7. **TEST-4**: Add tests for `confidence_level` and `significance_level` parameters.

8. **DOC-1**: Update module docstring to list both `analyze_chair_positions()` and `analyze_session_results_by_seat()` as main functions.

9. **DOC-2**: Update `export_seat_aggregate_csv()` docstring to reference both source functions.

## Deferred Issues

Issues where either "In PR Scope" OR "Actionable" is No:

| ID | Reason for Deferral |
|----|---------------------|
| CQ-3 | Design decision: deriving `num_seats` from results would change the API contract; current approach follows existing patterns |
| PERF-1 | Export happens once at simulation end, not in hot path; address if profiling shows bottleneck |
| TEST-5 | Statistical value verification requires deterministic test data; add as follow-up enhancement |
| SEC-1 | Pre-existing pattern throughout codebase; address as separate hardening effort |
| SEC-2 | Pre-existing pattern; output data is not sensitive |

## Recommendation

**Approve with minor changes.** The PR is well-implemented and follows existing patterns. Address the high-priority test gaps (TEST-1, TEST-2) before merge. Medium-priority items can be addressed in this PR or as follow-up.
