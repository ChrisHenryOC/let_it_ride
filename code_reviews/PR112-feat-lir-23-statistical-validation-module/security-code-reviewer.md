# Security Code Review: PR #112 - LIR-23 Statistical Validation Module

## Summary

This PR introduces a statistical validation module for comparing simulation results against theoretical poker hand probabilities. The code is well-structured with appropriate input validation for the statistical functions. No critical or high-severity security vulnerabilities were identified. Two low-severity issues and several informational observations are noted below.

## Findings by Severity

### Critical

None identified.

### High

None identified.

### Medium

None identified.

### Low

#### L-1: Missing Input Validation for `significance_level` Parameter

**Location:** `src/let_it_ride/analytics/validation.py:119`, `src/let_it_ride/analytics/validation.py:296`

**Description:** The `significance_level` parameter in `calculate_chi_square()` and `validate_simulation()` accepts any float value without validation. While not exploitable for security attacks, invalid values (negative numbers, values > 1.0) could produce meaningless results or unexpected behavior.

**Impact:** Low - Statistical results could be misleading if callers pass invalid significance levels.

**Remediation:** Add bounds checking for the parameter:

```python
def calculate_chi_square(
    observed_frequencies: dict[str, int],
    significance_level: float = 0.05,
) -> ChiSquareResult:
    if not 0.0 < significance_level < 1.0:
        raise ValueError("significance_level must be between 0 and 1 (exclusive)")
    # ... rest of function
```

**CWE Reference:** CWE-20 (Improper Input Validation)

---

#### L-2: Missing Input Validation for `confidence_level` Parameter

**Location:** `src/let_it_ride/analytics/validation.py:170`

**Description:** The `confidence_level` parameter in `calculate_wilson_confidence_interval()` accepts any float without validation. Values outside (0, 1) would produce undefined mathematical results (e.g., `stats.norm.ppf()` with extreme values).

**Impact:** Low - Could produce NaN or infinite values in confidence interval calculations.

**Remediation:** Add bounds checking:

```python
def calculate_wilson_confidence_interval(
    successes: int,
    total: int,
    confidence_level: float = 0.95,
) -> tuple[float, float]:
    if not 0.0 < confidence_level < 1.0:
        raise ValueError("confidence_level must be between 0 and 1 (exclusive)")
    # ... rest of function
```

**CWE Reference:** CWE-20 (Improper Input Validation)

---

#### L-3: Missing Input Validation for `base_bet` Parameter

**Location:** `src/let_it_ride/analytics/validation.py:297`

**Description:** The `base_bet` parameter in `validate_simulation()` accepts any float, including zero or negative values. While unlikely to cause security issues, negative base bets would flip the sign of theoretical EV calculations, potentially producing incorrect validation warnings.

**Impact:** Low - Could produce misleading validation results.

**Remediation:** Add validation for positive base bet:

```python
if base_bet <= 0:
    raise ValueError("base_bet must be positive")
```

**CWE Reference:** CWE-20 (Improper Input Validation)

---

### Informational

#### I-1: Division Operations Protected Against Zero

**Location:** `src/let_it_ride/analytics/validation.py:279-282`

**Observation:** The code properly guards against division by zero when calculating EV deviation percentage using `abs(ev_theoretical) > 1e-10`. This is good defensive programming.

---

#### I-2: Proper Use of Frozen Dataclasses

**Location:** `src/let_it_ride/analytics/validation.py:46`, `src/let_it_ride/analytics/validation.py:63`

**Observation:** Both `ChiSquareResult` and `ValidationReport` use `frozen=True`, ensuring immutability of results. This prevents accidental modification of statistical results after computation.

---

#### I-3: No External Input Sources

**Observation:** This module only processes data from internal `AggregateStatistics` objects, which are themselves computed from simulation results. There are no external input vectors (files, network, user input) that could introduce injection vulnerabilities. The attack surface is minimal.

---

#### I-4: scipy Dependency Security Note

**Location:** `pyproject.toml:10`

**Observation:** The PR adds `scipy.*` to mypy ignore list, indicating use of scipy for statistical calculations. scipy is a mature, well-maintained scientific library. Ensure the project uses a pinned version to avoid supply chain risks. Review `pyproject.toml` or `poetry.lock` to confirm version pinning.

---

#### I-5: Integer Overflow Consideration

**Location:** `src/let_it_ride/analytics/validation.py:136`, `src/let_it_ride/analytics/validation.py:260`

**Observation:** The code sums hand frequency counts using `sum(observed_frequencies.values())`. With Python's arbitrary-precision integers, integer overflow is not a concern even for millions of hands. No action needed.

---

#### I-6: Resource Exhaustion - Bounded by Design

**Observation:** The validation functions operate on aggregate statistics rather than raw hand data. Memory usage is bounded by the number of hand types (10 categories), not the number of simulated hands. This design inherently prevents memory exhaustion attacks, aligning with the project's <4GB RAM target.

---

## Positive Security Practices Observed

1. **Type hints throughout:** Full type annotations enable static analysis tools to catch type-related bugs.

2. **Explicit ValueError exceptions:** Functions raise descriptive exceptions for invalid inputs (empty frequencies, zero totals, invalid success counts).

3. **Bounds clamping on output:** The Wilson CI calculation clamps results to [0, 1] using `max(0.0, ...)` and `min(1.0, ...)`, preventing impossible proportion values.

4. **No dangerous operations:** No use of `eval()`, `exec()`, `pickle`, subprocess calls, or file I/O.

5. **Internal-only data flow:** All inputs come from other internal modules (`AggregateStatistics`), not from untrusted external sources.

## Recommendations

1. Add input validation for `significance_level`, `confidence_level`, and `base_bet` parameters as described in L-1, L-2, and L-3.

2. Consider adding type validation for numeric parameters to reject `NaN` and `Inf` values:
   ```python
   import math
   if not math.isfinite(significance_level):
       raise ValueError("significance_level must be a finite number")
   ```

## Files Reviewed

- `src/let_it_ride/analytics/validation.py` (new file, 320 lines)
- `tests/unit/analytics/test_validation.py` (new file, 541 lines)
- `pyproject.toml` (1 line change)
- `scratchpads/issue-26-statistical-validation.md` (new file, design notes)

## Conclusion

The statistical validation module is well-implemented from a security perspective. The code follows good defensive programming practices with proper exception handling for edge cases. The identified low-severity issues around parameter validation should be addressed for robustness but do not represent exploitable security vulnerabilities in the context of a casino simulation tool.
