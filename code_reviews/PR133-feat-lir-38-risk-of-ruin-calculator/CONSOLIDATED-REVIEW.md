# Consolidated Review for PR #133: LIR-38 Risk of Ruin Calculator

## Summary

This PR introduces a risk of ruin calculator with Monte Carlo simulation, analytical estimation, and visualization capabilities. The implementation demonstrates strong adherence to project conventions with comprehensive test coverage for the core module. However, a **critical performance bottleneck** was identified: the Monte Carlo simulation uses pure Python nested loops that could take minutes to complete with default parameters, directly blocking the project's 100K hands/second performance target. Additionally, the visualization module lacks test coverage.

## Issue Matrix

| ID | Category | Severity | Description | File:Line | In PR Scope | Actionable |
|----|----------|----------|-------------|-----------|-------------|------------|
| C1 | Performance | Critical | Pure Python nested loops in Monte Carlo simulation - 500M iterations with defaults | risk_of_ruin.py:191-214 | Yes | Yes |
| T1 | Test Coverage | Critical | No tests for risk_curves.py visualization module (260 lines) | risk_curves.py | Yes | Yes |
| H1 | Performance | High | Redundant array allocation inside simulation loop (~800MB churn per level) | risk_of_ruin.py:196-197 | Yes | Yes |
| H2 | Performance | High | Sequential processing of independent bankroll levels | risk_of_ruin.py:346-354 | Yes | Yes |
| H3 | Documentation | High | Inaccurate base_bet inference docstring | risk_of_ruin.py:295-296 | Yes | Yes |
| H4 | Test Coverage | High | Missing test for zero base_bet inference fallback | risk_of_ruin.py:327 | Yes | Yes |
| H5 | Test Coverage | High | Missing test for NaN analytical estimate formatting | risk_of_ruin.py:414-417 | Yes | Yes |
| H6 | Test Coverage | High | Missing test for unsorted bankroll units input | risk_of_ruin.py:346 | Yes | Yes |
| H7 | Test Coverage | High | Missing test for zero mean AND zero std analytical calc | risk_of_ruin.py:143-145 | Yes | Yes |
| M1 | Code Quality | Medium | Confusing variable naming (quarter_threshold = 0.75) | risk_of_ruin.py:162-163 | Yes | Yes |
| M2 | Code Quality | Medium | Magic numbers without named constants | risk_of_ruin.py:various | Yes | Yes |
| M3 | Code Quality | Medium | Import inside function body (FuncFormatter) | risk_curves.py:190-191 | Yes | Yes |
| M4 | Code Quality | Medium | Inconsistent std calculation (np.std vs statistics.stdev) | risk_of_ruin.py:302-304 | Yes | Yes |
| M5 | Code Quality | Medium | Hardcoded "95% CI" in formatted output | risk_of_ruin.py:406-408 | Yes | Yes |
| M6 | Code Quality | Medium | Duplicate array iteration in visualization | risk_curves.py:73-79 | Yes | Yes |
| M7 | Performance | Medium | Using Python stdlib mean() on NumPy array | risk_of_ruin.py:333-334 | Yes | Yes |
| M8 | Documentation | Medium | Return type float|None but never returns None | risk_of_ruin.py:124 | Yes | Yes |
| M9 | Documentation | Medium | Unclear quarter_bankroll_risk terminology | risk_of_ruin.py:38 | Yes | Yes |
| M10 | Security | Medium | DoS - Unbounded simulations_per_level parameter | risk_of_ruin.py:280 | Yes | Yes |
| M11 | Security | Medium | DoS - Unbounded bankroll_units sequence length | risk_of_ruin.py:71-83 | Yes | Yes |
| M12 | Test Coverage | Medium | Missing boundary tests for confidence levels (0.001, 0.999) | tests | Yes | Yes |
| M13 | Test Coverage | Medium | Missing test for single simulation count | tests | Yes | Yes |
| L1 | Code Quality | Low | Missing validation for simulations_per_level | risk_of_ruin.py:248 | Yes | Yes |
| L2 | Code Quality | Low | Test file imports private functions | test_risk_of_ruin.py | Yes | No (acceptable) |
| L3 | Code Quality | Low | Hardcoded visualization confidence band label | risk_curves.py:128 | Yes | Yes |
| L4 | Code Quality | Low | Color values as magic strings | risk_curves.py:87-135 | Yes | Yes |
| L5 | Documentation | Low | Hardcoded "95% Confidence Band" in visualization | risk_curves.py:128 | Yes | Yes |
| L6 | Documentation | Low | Outdated scratchpad task list | scratchpads/issue-41 | Yes | No (cleanup) |
| L7 | Documentation | Low | Module docstring not updated in analytics/__init__.py | analytics/__init__.py | Yes | Yes |
| L8 | Security | Low | Directory traversal in save path | risk_curves.py:248-253 | Yes | No (matches pattern) |
| L9 | Test Coverage | Low | Missing integration test for full workflow | tests | Yes | Yes |

## Actionable Issues

### Critical (Must Fix Before Merge)

**C1. Performance: Pure Python nested loops in Monte Carlo simulation**
- Location: `risk_of_ruin.py:191-214`
- Impact: With defaults (10K simulations × 10K sessions × 5 levels = 500M iterations), execution could take minutes
- Fix: Vectorize using NumPy cumsum and array operations for 100-1000x speedup:
```python
all_samples = rng.choice(session_profits, size=(simulations, max_sessions_per_sim))
trajectories = bankroll + np.cumsum(all_samples, axis=1)
ruin_mask = np.any(trajectories <= 0, axis=1)
```

**T1. Test Coverage: No tests for risk_curves.py**
- Location: `risk_curves.py` (260 lines, 0 test coverage)
- Impact: Similar visualization modules have comprehensive tests; this creates inconsistency
- Fix: Add tests following `test_visualizations.py` pattern for histogram/trajectory

### High Priority

| ID | Description | Recommended Fix |
|----|-------------|-----------------|
| H1 | Array allocation in loop | Pre-allocate all samples in single call (addressed by C1 fix) |
| H2 | Sequential bankroll levels | Consider parallelization after vectorization |
| H3 | Inaccurate docstring | Update to describe actual `total_wagered / (hands * 3)` logic |
| H4-H7 | Missing edge case tests | Add specific test cases for each scenario |

### Medium Priority

| ID | Description | Recommended Fix |
|----|-------------|-----------------|
| M1 | Confusing naming | Rename to `loss_25pct_threshold` |
| M2 | Magic numbers | Define module-level constants |
| M5 | Hardcoded 95% CI | Use `result.confidence_interval.level` |
| M10-M11 | DoS parameters | Add upper bound validation |

## Deferred Issues

| ID | Reason for Deferral |
|----|---------------------|
| L2 | Testing private functions is acceptable for comprehensive coverage |
| L6 | Scratchpad cleanup is non-functional |
| L8 | Matches existing codebase pattern for CLI tools |

## Positive Highlights

- Excellent adherence to project patterns (frozen dataclasses, TYPE_CHECKING guards, slots)
- Comprehensive type hints throughout
- Robust numerical stability handling for overflow prevention
- Clean module organization separating concerns
- Proper matplotlib resource cleanup preventing memory leaks
- Strong statistical validation tests with convergence verification
- Immutable data structures with proper input validation

## Verdict

**Request Changes** - The critical performance issue (C1) blocks meeting the project's 100K hands/second target. After vectorizing the Monte Carlo simulation, this will be ready for approval with remaining issues addressed as time permits.
