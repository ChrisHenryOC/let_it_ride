# Test Coverage Review: PR #129 - LIR-34 End-to-End Integration Tests

**Reviewer:** Test Coverage Reviewer
**Date:** 2025-12-13
**PR:** #129 - feat: LIR-34 End-to-End Integration Tests

## Summary

This PR introduces a comprehensive E2E test suite with ~2,900 new lines of test code across 7 new test files (`tests/e2e/`). The tests provide good coverage for full simulation pipelines, CLI workflows, output format validation, and performance benchmarks. However, there are several gaps related to missing negative test scenarios, test isolation concerns, and insufficient edge case coverage for statistical validation.

## Findings by Severity

### High Severity

**#H1** - Missing Tests for Extreme Discard Card Scenarios
**File:** `tests/e2e/test_deferred_items.py`

The dealer discard tests cover values 1, 2, 5, and 10, but do not test boundary conditions like maximum allowable discard cards (deck has 52 cards, hand needs 5), value of 0 with `discard_enabled=True`, or negative values.

**Recommendation:** Add boundary tests for extreme discard values to verify DeckEmptyError is raised appropriately.

---

**#H2** - Chi-Square Test Has No Failure Path Coverage
**File:** `tests/e2e/test_full_simulation.py`

The test `test_hand_frequency_chi_square_passes` only verifies the test passes. There is no test verifying the chi-square test correctly rejects a biased distribution, leaving no assurance the statistical validation actually catches problems.

**Recommendation:** Add a complementary test with intentionally skewed frequencies to ensure the validation catches problems.

---

### Medium Severity

**#M1** - Performance Tests Use Reduced Thresholds
**File:** `tests/e2e/test_performance.py`

The throughput test uses a 10K hands/sec threshold vs the documented 100K requirement. While coverage overhead is mentioned, this makes the test unable to catch significant regressions.

**Recommendation:** Consider environment-based thresholds for production builds vs lenient thresholds under coverage.

---

**#M2** - Test Isolation Risk with Shared Config Mutations
**File:** `tests/e2e/test_sample_configs.py`

Tests modify config objects in-place (`config.simulation.num_sessions = 100`). If Pydantic models are cached at class level, this could cause cross-test contamination.

**Recommendation:** Use `config.model_copy(deep=True)` before mutation to ensure test independence.

---

**#M3** - Output Format Tests Don't Verify All CSV Columns
**File:** `tests/e2e/test_output_formats.py`

The test `test_csv_session_data_matches_results` verifies only 6 columns (`outcome`, `stop_reason`, `hands_played`, `starting_bankroll`, `final_bankroll`, `session_profit`) but likely misses `session_id`, `total_wagered`, `total_won`, and bonus columns.

**Recommendation:** Expand column verification to cover all expected output fields.

---

**#M4** - Parallel vs Sequential Equivalence Tests Use Only Profit Comparison
**File:** `tests/e2e/test_full_simulation.py`

The parallel equivalence test compares only `session_profit` values. This could mask subtle differences in hand counts, stop reasons, or bonus payouts.

**Recommendation:** Also compare `hands_played`, `stop_reason`, and `final_bankroll` to ensure truly identical results.

---

**#M5** - Memory Tests Don't Account for GC Timing
**File:** `tests/e2e/test_performance.py`

Memory growth test measures peak memory without forcing garbage collection between runs, potentially leading to false positives.

**Recommendation:** Add `gc.collect()` calls before memory measurements.

---

### Low Severity

**#L1** - Duplicate Test Coverage with Integration Tests
**Files:** `tests/e2e/test_sample_configs.py` vs `tests/integration/test_sample_configs.py`

The E2E sample config tests significantly overlap with existing integration tests (both test all 6 configs load, execute, and are reproducible).

**Recommendation:** Consider consolidating or clearly differentiating the scope of each test file.

---

**#L2** - Hardcoded Magic Numbers in Win Rate Assertions
**File:** `tests/e2e/test_full_simulation.py`

The range `[0.20, 0.60]` for win rate appears arbitrary. Consider deriving from theoretical house edge or documenting rationale.

---

**#L3** - Hand Records Collection Is Fragile
**File:** `tests/e2e/test_output_formats.py`

The `collect_hands` callback manually constructs `HandRecord` objects with hardcoded field mappings. Schema changes would break these tests silently.

---

**#L4** - Missing Test for Invalid Bonus Configuration
**File:** `tests/e2e/test_cli_e2e.py`

Tests valid bonus config but no corresponding test for invalid configurations (negative amounts, missing required fields).

---

**#L5** - No Test for Empty Session Results Edge Case
**File:** `tests/e2e/test_full_simulation.py`

No test verifying behavior when a session completes with 0 hands played (e.g., starting bankroll below minimum bet).

---

## Positive Observations

1. **Comprehensive E2E Coverage:** Tests cover full simulation pipelines, CLI workflows, output formats, and performance.

2. **Deferred Items Addressed:** The PR properly addresses deferred code review items from PRs #78 and #111.

3. **Statistical Validation:** Chi-square tests for hand frequency validation add confidence in simulation correctness.

4. **Reproducibility Testing:** Tests verify that seeded simulations produce identical results.

5. **Performance Baselines:** Throughput and memory tests establish baselines for regression detection.

---

## Overall Assessment

**Approve with suggestions.** The test coverage is comprehensive and addresses key acceptance criteria. The identified gaps are important to address for long-term maintainability but do not block the PR.
