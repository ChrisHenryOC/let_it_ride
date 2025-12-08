# Security Review - PR #113

## Summary

This PR adds a core statistics calculator module (`src/let_it_ride/analytics/statistics.py`) with 485 lines of new code and 764 lines of tests. The code performs statistical calculations on simulation results and does not handle external/untrusted input directly. Overall security posture is good, with proper input validation for empty data cases, though there are a few minor numerical edge cases worth noting.

## Findings

### Critical

None

### High

None

### Medium

None

### Low

**L-01: Potential Division by Zero in EV Confidence Interval Scaling**

- **Location:** `src/let_it_ride/analytics/statistics.py:564-570`
- **Description:** When scaling EV confidence interval by average hands per session, there is a guard for `avg_hands > 0`, but `avg_hands` is calculated as `total_hands / total_sessions`. Since the function already validates `total_sessions > 0` at line 529, and hands can theoretically be zero if sessions completed without playing hands, this could result in a zero divisor.
- **Impact:** If a simulation produces sessions with zero hands played, the scaling division would not occur (due to the guard), but the EV CI would remain unscaled, potentially misleading the user.
- **Remediation:** The current guard is adequate for preventing division by zero, but consider logging or warning when `avg_hands == 0` to alert users that EV CI scaling was skipped.
- **CWE:** CWE-369 (Divide By Zero)

**L-02: Floating Point Precision in Kurtosis/Skewness with Extreme Values**

- **Location:** `src/let_it_ride/analytics/statistics.py:282-284` (skewness), `src/let_it_ride/analytics/statistics.py:311-316` (kurtosis)
- **Description:** The skewness and kurtosis calculations raise values to the 3rd and 4th power respectively, which can lead to floating point overflow with very large input values (beyond the tested 1e9 range). While Python floats can handle this to some extent, intermediate calculations could potentially overflow to infinity.
- **Impact:** For extreme simulation values (e.g., profits in the billions), these calculations could return `inf` or `nan`, which would propagate through the statistics.
- **Remediation:** The code already handles `data_std == 0` returning 0.0. Consider adding a check for `math.isinf()` or `math.isnan()` on the result, or document the expected value ranges. The test at line 1281-1296 tests up to 1e9 which is reasonable for this application.
- **CWE:** CWE-190 (Integer Overflow) / CWE-681 (Incorrect Conversion between Numeric Types)

**L-03: No Validation of `confidence_level` Parameter Range**

- **Location:** `src/let_it_ride/analytics/statistics.py:397-428`, `src/let_it_ride/analytics/statistics.py:505-591`, `src/let_it_ride/analytics/statistics.py:594-624`
- **Description:** The `confidence_level` parameter in `_calculate_mean_confidence_interval`, `calculate_statistics`, and `calculate_statistics_from_results` is not validated to be within (0, 1). Values outside this range would produce mathematically invalid results (e.g., `confidence_level=2.0` or negative values).
- **Impact:** Invalid confidence levels would produce nonsensical confidence intervals. This is a low risk since the parameter is not exposed to untrusted external input in typical usage.
- **Remediation:** Add validation: `if not 0 < confidence_level < 1: raise ValueError("confidence_level must be between 0 and 1")`
- **CWE:** CWE-20 (Improper Input Validation)

### Informational

**I-01: Good Practice - Empty Data Validation**

The code properly validates empty input data in multiple places:
- `_calculate_distribution_stats` raises `ValueError` for empty data (line 370-371)
- `calculate_statistics` validates `total_sessions > 0` (line 529-530)
- `calculate_statistics_from_results` validates non-empty results list (line 616-617)
- `_calculate_risk_metrics` handles None/empty inputs gracefully (lines 446-472)

**I-02: Good Practice - Frozen Dataclasses**

All dataclasses use `frozen=True` and `slots=True`, preventing accidental mutation and improving memory efficiency. This is a security-positive pattern.

**I-03: Good Practice - Edge Case Handling in Statistical Functions**

The skewness and kurtosis functions properly handle edge cases:
- Returns 0.0 when `n < 3` for skewness (line 277-278)
- Returns 0.0 when `n < 4` for kurtosis (line 305-306)
- Returns 0.0 when `data_std == 0` to avoid division by zero (lines 279-280, 309-310)

**I-04: Dependency on scipy.stats**

The module uses `scipy.stats` for t-distribution calculations. This is a well-maintained, widely-used library. Ensure scipy is kept updated to receive security patches.

## Recommendations

1. **Consider adding confidence_level validation** in public-facing functions to catch invalid inputs early:
   ```python
   if not 0 < confidence_level < 1:
       raise ValueError("confidence_level must be between 0 and 1")
   ```

2. **Document expected value ranges** for the statistics module, particularly noting that the calculations are designed for typical casino simulation values (profits in the range of -1e9 to 1e9).

3. **Add overflow protection** (optional) for skewness/kurtosis if the module might be reused in contexts with larger values:
   ```python
   result = term1 * term2 - term3
   if math.isinf(result) or math.isnan(result):
       return 0.0  # or raise an appropriate error
   ```

## Files Reviewed

- `src/let_it_ride/analytics/statistics.py` (new, 485 lines)
- `src/let_it_ride/analytics/__init__.py` (modified, exports added)
- `tests/unit/analytics/test_statistics.py` (new, 764 lines)
- `scratchpads/issue-28-core-statistics.md` (new, planning document)

## Conclusion

This PR introduces a well-structured statistics module with appropriate input validation for its primary use case (poker simulation analysis). The identified issues are low severity and relate to edge cases that are unlikely to occur in normal usage. The code demonstrates good defensive programming practices including frozen dataclasses, proper empty data handling, and edge case management in statistical calculations. No critical or high severity security issues were identified.
