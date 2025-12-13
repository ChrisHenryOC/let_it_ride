# LIR-34: End-to-End Integration Tests

**GitHub Issue:** https://github.com/USERNAME/let_it_ride/issues/37

## Overview

Implement comprehensive end-to-end tests validating the complete simulation pipeline.

## Acceptance Criteria

- [ ] Test running 10,000 sessions with known seed
- [ ] Verify session win rate within expected range
- [ ] Verify hand frequency distribution passes chi-square test
- [ ] Test all output formats generated correctly (CSV, JSON)
- [ ] Test parallel and sequential produce statistically equivalent results
- [ ] Test configuration validation catches all documented error types
- [ ] Test CLI invocation end-to-end
- [ ] Test with each sample configuration file
- [ ] Performance assertion (minimum hands/second)
- [ ] Memory usage validation

## Deferred Items from Code Reviews

### From PR #78 (LIR-41: Dealer Discard Mechanics)
- [ ] DeckEmptyError edge case test
- [ ] YAML loader test for dealer section

### From PR #111 (LIR-22: Simulation Results Aggregation)
- [ ] Integration test connecting aggregate_results() to SimulationController.run()

## Files to Create

- `tests/e2e/__init__.py`
- `tests/e2e/test_full_simulation.py`
- `tests/e2e/test_output_formats.py`
- `tests/e2e/test_cli_e2e.py`
- `tests/e2e/test_sample_configs.py`

## Implementation Plan

1. Create E2E test directory structure
2. Implement test_full_simulation.py:
   - test_basic_strategy_simulation (10K sessions)
   - test_reproducibility (same seed = same results)
   - test_parallel_equivalence (parallel vs sequential)
   - test_statistical_validity (chi-square test for hand frequencies)
3. Implement test_output_formats.py:
   - test_csv_output_generation
   - test_json_output_generation
   - test_output_content_validity
4. Implement test_cli_e2e.py:
   - test_cli_run_full_simulation
   - test_cli_output_files_created
   - test_cli_with_all_options
5. Implement test_sample_configs.py:
   - test_all_sample_configs_run_successfully
   - Verify each config executes without error
6. Add deferred items:
   - DeckEmptyError edge case
   - YAML dealer section loading
   - aggregate_results() integration test
7. Add performance and memory tests:
   - test_performance_threshold (>=100K hands/sec)
   - test_memory_usage (< 4GB for 10M hands baseline)

## Key Dependencies

- `let_it_ride.analytics.validation` - Statistical validation utilities
- `let_it_ride.simulation.aggregation` - aggregate_results function
- `let_it_ride.cli.app` - CLI app for E2E CLI tests
- Sample configs in `configs/` directory

## Notes

- Existing integration tests provide good patterns to follow
- Use `create_test_config()` helper pattern from test_parallel.py
- Leverage existing validation.py for chi-square tests
- Memory test can use tracemalloc module
- Performance test should measure actual throughput
