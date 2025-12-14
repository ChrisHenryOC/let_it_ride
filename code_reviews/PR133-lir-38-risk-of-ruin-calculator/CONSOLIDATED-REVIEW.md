# Consolidated Review for PR #133

**PR Title:** feat: LIR-38 Risk of Ruin Calculator
**Branch:** feature/issue-41-risk-of-ruin
**Files Changed:** 6 files (+1,631 lines)

## Summary

This PR introduces a well-structured risk of ruin calculator with Monte Carlo simulation, analytical estimation, and visualization capabilities. The code follows project conventions (frozen dataclasses, TYPE_CHECKING guards, validation helpers) and includes comprehensive test coverage for the core module. However, there is a **critical performance issue** with the Monte Carlo simulation using pure Python nested loops instead of vectorized NumPy operations, and a **critical test coverage gap** for the visualization module.

## Issue Matrix

| ID | Issue | Severity | Category | In PR Scope | Actionable | Recommendation |
|----|-------|----------|----------|-------------|------------|----------------|
| P-C1 | Pure Python nested loops in Monte Carlo (100M iterations) | Critical | Performance | Yes | Yes | Vectorize with NumPy cumsum |
| T-C1 | No unit tests for risk_curves.py (260 lines) | Critical | Test Coverage | Yes | Yes | Add tests for visualization module |
| P-H1 | Redundant array allocation inside simulation loop | High | Performance | Yes | Yes | Pre-allocate all samples |
| P-H2 | Sequential processing of independent bankroll levels | High | Performance | Yes | Yes | Consider parallelization |
| D-H1 | Inaccurate base_bet inference docstring | High | Documentation | Yes | Yes | Update docstring to match implementation |
| T-H2 | Missing test for zero base_bet inference fallback | High | Test Coverage | Yes | Yes | Add edge case test |
| T-H3 | Missing test for NaN analytical estimate handling | High | Test Coverage | Yes | Yes | Add NaN handling test |
| T-H4 | Missing test for unsorted bankroll units input | High | Test Coverage | Yes | Yes | Add sorting verification test |
| S-M1 | Unbounded simulations_per_level (DoS risk) | Medium | Security | Yes | Yes | Add upper bound validation |
| S-M2 | Unbounded bankroll_units sequence length | Medium | Security | Yes | Yes | Add maximum length validation |
| C-M1 | FuncFormatter import inside function body | Medium | Code Quality | Yes | Yes | Move to module-level imports |
| C-M2 | Inconsistent std calculation (np.std vs statistics.stdev) | Medium | Code Quality | Yes | Yes | Standardize approach |
| C-M3 | Magic numbers for simulation defaults | Medium | Code Quality | Yes | Yes | Define named constants |
| C-M4 | Confusing threshold variable naming | Medium | Code Quality | Yes | Yes | Rename for clarity |
| D-M1 | quarter_bankroll_risk terminology unclear | Medium | Documentation | Yes | Yes | Clarify docstring |
| D-M2 | Return type never returns None but hints suggest it | Medium | Documentation | Yes | Yes | Update type hint |
| D-M3 | Missing Raises doc in save_risk_curves | Medium | Documentation | Yes | Yes | Add ValueError propagation doc |
| T-M1 | Missing edge case: zero mean AND zero std | Medium | Test Coverage | Yes | Yes | Add analytical formula test |
| C-L1 | Hardcoded "95% CI" in format output | Low | Code Quality | Yes | Yes | Use actual confidence level |
| C-L2 | Missing validation for simulations_per_level | Low | Code Quality | Yes | Yes | Add positive check |
| D-L1 | Hardcoded confidence band label in visualization | Low | Documentation | Yes | Yes | Use dynamic level |
| D-L2 | Missing algorithm complexity documentation | Low | Documentation | Yes | No | Nice to have |
| D-L3 | Outdated scratchpad task list | Low | Documentation | Yes | No | Cleanup optional |
| S-L1 | Directory traversal potential in save paths | Low | Security | Yes | No | Matches existing pattern |
| T-L1 | No property-based testing | Low | Test Coverage | Yes | No | Enhancement for future |

## Actionable Issues

### Critical (Must Fix)

1. **[P-C1] Vectorize Monte Carlo Simulation** (`risk_of_ruin.py:191-214`)
   - Current implementation uses pure Python nested loops with up to 100M iterations per bankroll level
   - Replace with vectorized NumPy operations:
   ```python
   all_samples = rng.choice(session_profits, size=(simulations, max_sessions_per_sim))
   trajectories = bankroll + np.cumsum(all_samples, axis=1)
   ruin_mask = np.any(trajectories <= 0, axis=1)
   ```
   - Impact: Minutes → sub-second execution time

2. **[T-C1] Add Tests for Visualization Module** (`risk_curves.py`)
   - Create unit tests for `RiskCurveConfig`, `plot_risk_curves()`, `save_risk_curves()`
   - Test empty results error, custom config, PNG/SVG output, directory creation

### High (Should Fix)

3. **[D-H1] Fix base_bet Inference Docstring** (`risk_of_ruin.py:295-296`)
   - Docstring says "dividing starting bankroll by a typical multiple"
   - Implementation uses `total_wagered / (hands_played * 3)`
   - Update docstring to match actual behavior

4. **[P-H1] Pre-allocate Sample Arrays** (`risk_of_ruin.py:196-197`)
   - Move array allocation outside the inner loop

5. **[T-H2/H3/H4] Add Missing Test Cases**
   - Zero base_bet inference when total_hands == 0
   - NaN handling in analytical estimates
   - Unsorted bankroll units producing sorted output

### Medium (Recommended)

6. **[S-M1/M2] Add Resource Limits** (`risk_of_ruin.py:424-432`)
   ```python
   MAX_SIMULATIONS_PER_LEVEL = 100_000
   MAX_BANKROLL_LEVELS = 100
   ```

7. **[C-M1] Move FuncFormatter Import** (`risk_curves.py:802-803`)
   - Move `from matplotlib.ticker import FuncFormatter` to module-level

8. **[C-M3] Define Named Constants** (`risk_of_ruin.py:315,428,461-462`)
   ```python
   DEFAULT_MAX_SESSIONS_PER_SIM: int = 10000
   DEFAULT_SIMULATIONS_PER_LEVEL: int = 10000
   DEFAULT_BANKROLL_UNITS: tuple[int, ...] = (20, 40, 60, 80, 100)
   ```

9. **[C-L1/D-L1] Fix Hardcoded Confidence Level** (`risk_of_ruin.py:555-556`, `risk_curves.py:128`)
   - Use `result.confidence_interval.level` instead of hardcoded "95%"

## Deferred Issues

| ID | Reason |
|----|--------|
| D-L2 | Algorithm complexity docs are nice-to-have, not blocking |
| D-L3 | Scratchpad cleanup is optional housekeeping |
| S-L1 | Matches existing pattern in histogram.py/trajectory.py |
| T-L1 | Property-based testing is a future enhancement |

## Positive Highlights

- Excellent adherence to project patterns (frozen dataclasses with slots, TYPE_CHECKING guards)
- Comprehensive type hints throughout
- Robust error handling with clear, actionable messages
- Good numerical stability handling (overflow prevention)
- Comprehensive test coverage for core module (874 lines of tests)
- Clean visualization implementation following existing patterns
- Proper matplotlib figure cleanup preventing memory leaks
- Strong statistical validation tests (convergence, stability)
- Good use of modern NumPy Generator API

## Verdict

**Recommend changes before merge.** The critical performance issue (P-C1) needs to be addressed as the current implementation may take minutes per report with default parameters. The missing visualization tests (T-C1) should also be added for completeness. The high-priority documentation fix (D-H1) prevents user confusion about base_bet inference.

## Summary by Severity

| Severity | Count |
|----------|-------|
| Critical | 2 |
| High | 5 |
| Medium | 10 |
| Low | 7 |
