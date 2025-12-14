# Security Review - PR #133

## Summary

This PR introduces risk of ruin calculation functionality with Monte Carlo simulation and visualization capabilities. The implementation demonstrates good security practices overall, with proper input validation and no major vulnerabilities. There are a few medium and low-severity findings related to resource exhaustion potential and path handling that could be addressed.

## Findings

### Critical

None identified.

### High

None identified.

### Medium

**M1. Denial of Service via Resource Exhaustion - Unbounded Simulation Parameters**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py`
Lines: 424-432, 310-316

The `calculate_risk_of_ruin` function accepts `simulations_per_level` without upper bound validation. Combined with the default `max_sessions_per_sim=10000` in `_run_monte_carlo_ruin_simulation`, a malicious or careless user could cause memory exhaustion or CPU denial of service:

```python
def calculate_risk_of_ruin(
    session_results: Sequence[SessionResult],
    bankroll_units: Sequence[int] | None = None,
    base_bet: float | None = None,
    simulations_per_level: int = 10000,  # No upper bound validation
    ...
)
```

The inner simulation allocates large arrays via `rng.choice(session_profits, size=max_sessions_per_sim)` (line 345). With default values of 10,000 simulations and 10,000 sessions per simulation across 5 bankroll levels, this could process 500 million iterations.

**Recommendation:** Add upper bound validation for `simulations_per_level` and consider documenting/exposing `max_sessions_per_sim` with validation:

```python
MAX_SIMULATIONS_PER_LEVEL = 100_000
MAX_SESSIONS_PER_SIM = 50_000

if simulations_per_level > MAX_SIMULATIONS_PER_LEVEL:
    raise ValueError(f"simulations_per_level exceeds maximum of {MAX_SIMULATIONS_PER_LEVEL}")
```

**CWE Reference:** CWE-400 (Uncontrolled Resource Consumption)

---

**M2. Unbounded Array Allocation in Bankroll Units**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py`
Lines: 219-231, 461-463

The `bankroll_units` parameter accepts sequences of arbitrary length without validation. A very large sequence would cause linear resource consumption:

```python
def _validate_bankroll_units(bankroll_units: Sequence[int]) -> None:
    if not bankroll_units:
        raise ValueError("bankroll_units must not be empty")
    if any(units <= 0 for units in bankroll_units):
        raise ValueError("All bankroll units must be positive integers")
    # No upper bound on length
```

**Recommendation:** Add maximum length validation:

```python
MAX_BANKROLL_LEVELS = 100
if len(bankroll_units) > MAX_BANKROLL_LEVELS:
    raise ValueError(f"bankroll_units exceeds maximum of {MAX_BANKROLL_LEVELS} levels")
```

**CWE Reference:** CWE-400 (Uncontrolled Resource Consumption)

### Low

**L1. Directory Traversal - Weak Path Validation in save_risk_curves**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/visualizations/risk_curves.py`
Lines: 835-871

The `save_risk_curves` function creates parent directories automatically without validating the path:

```python
def save_risk_curves(
    report: RiskOfRuinReport,
    path: Path,
    ...
) -> None:
    ...
    path = Path(path)
    if path.suffix.lower() != f".{output_format}":
        path = path.with_suffix(f".{output_format}")

    # Creates arbitrary directory structure
    path.parent.mkdir(parents=True, exist_ok=True)
```

While this matches the existing pattern in `histogram.py` and `trajectory.py`, it allows writing to arbitrary filesystem locations if user-controlled paths are passed. This is a low risk since the application is a CLI tool where file paths are typically trusted, but worth noting.

**Recommendation:** Consider validating paths are within an expected output directory when user-controlled paths are involved, or document that paths should be validated by calling code.

**CWE Reference:** CWE-22 (Path Traversal)

---

**L2. No Integer Overflow Protection for Extremely Large Bankroll Values**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py`
Lines: 388, 507

The bankroll calculation multiplies base_bet by bankroll_units without overflow protection:

```python
bankroll = base_bet * bankroll_units
```

Python handles arbitrary precision integers, but when converted to NumPy arrays or used in floating-point operations, extremely large values could cause unexpected behavior or precision loss.

**Recommendation:** Add reasonable upper bounds for `bankroll_units` values (e.g., 1,000,000 units maximum).

**CWE Reference:** CWE-190 (Integer Overflow)

---

**L3. Potential Information Disclosure in Formatted Reports**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py`
Lines: 529-567

The `format_risk_of_ruin_report` function outputs financial details including exact bankroll amounts. While this is expected functionality, it is worth noting that reports should be handled carefully to avoid unintended disclosure of sensitive financial simulation data.

**Recommendation:** Document that output should be treated as potentially sensitive if used with real financial data.

---

**L4. RNG Seed Not Validated for Cryptographic Context**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py`
Lines: 488

The `random_seed` parameter uses NumPy's default RNG which is not cryptographically secure:

```python
rng = np.random.default_rng(random_seed)
```

For a gambling simulation context, while Monte Carlo simulations do not require cryptographic randomness, the application documentation should clarify this is for statistical analysis only, not for actual gambling decisions.

**Recommendation:** This is acceptable for simulation purposes. Consider adding a docstring note that this is for statistical analysis, not cryptographic applications.

### Positive

**P1. Comprehensive Input Validation**

The code demonstrates good validation practices with dedicated validation functions:
- `_validate_bankroll_units()` - Validates non-empty and positive values
- `_validate_session_results()` - Validates minimum sample size (10 results)
- `_validate_confidence_level()` - Validates range (0, 1)
- `base_bet` positive check at line 478-479

**P2. Immutable Data Structures**

Use of `@dataclass(frozen=True, slots=True)` for `RiskOfRuinResult` and `RiskOfRuinReport` prevents accidental mutation and provides memory efficiency.

**P3. Numerical Stability Handling**

Good handling of edge cases in `_calculate_analytical_ruin_probability()`:
- Zero standard deviation case (lines 291-293)
- Overflow prevention for very negative exponents (lines 304-305)

```python
if exponent < -700:
    return 0.0
```

**P4. Safe Division Practices**

The code properly handles potential division by zero scenarios:
- Line 475: `if total_hands > 0 else 1.0`

**P5. Consistent Path Handling Pattern**

The `save_risk_curves` function follows the established pattern from `histogram.py` and `trajectory.py`, ensuring consistency and maintainability.

**P6. Proper Resource Cleanup**

The visualization code properly closes matplotlib figures in a `finally` block (lines 868-871):

```python
try:
    fig.savefig(path, format=output_format, dpi=config.dpi, bbox_inches="tight")
finally:
    plt.close(fig)
```

**P7. Type Safety**

Strong typing throughout with proper use of `TYPE_CHECKING` guards to prevent circular imports while maintaining type hints.

## Summary Table

| Severity | Count | Action Required |
|----------|-------|-----------------|
| Critical | 0 | - |
| High | 0 | - |
| Medium | 2 | Recommended |
| Low | 4 | Optional |
| Positive | 7 | - |

## Recommendation

This PR is **safe to merge** from a security perspective. The medium-severity findings around resource exhaustion are worth considering for future hardening, especially if the API becomes exposed to less trusted inputs. The code follows good security practices and is consistent with existing patterns in the codebase.
