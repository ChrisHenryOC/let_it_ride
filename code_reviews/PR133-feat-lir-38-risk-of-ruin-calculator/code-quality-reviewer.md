# Code Quality Review - PR #133

## Summary

This PR implements a risk of ruin calculator with Monte Carlo simulation, analytical estimation, and visualization capabilities. The code demonstrates strong adherence to project conventions including frozen dataclasses with slots, TYPE_CHECKING guards, and comprehensive type hints. The module structure is clean and the test coverage is thorough. Several medium-severity issues related to naming clarity, DRY violations, and missing validation were identified.

## Findings

### Critical

None identified.

### High

None identified.

### Medium

**1. Confusing variable naming for threshold calculations**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py` (lines 162-163 in diff, approx lines 335-336 in actual file)

```python
half_threshold = bankroll * 0.5
quarter_threshold = bankroll * 0.75
```

The naming `quarter_threshold` for `bankroll * 0.75` is semantically incorrect. This value represents the bankroll level at which a 25% loss has occurred (75% remaining), not a quarter of the bankroll. This creates cognitive dissonance when reading the code.

**Recommendation:** Rename for clarity:
```python
loss_50pct_threshold = bankroll * 0.50  # 50% loss = 50% remaining
loss_25pct_threshold = bankroll * 0.75  # 25% loss = 75% remaining
```

---

**2. Magic numbers without named constants**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py`

Multiple magic numbers appear throughout the code:

- Line 141 (diff): `max_sessions_per_sim: int = 10000`
- Line 248 (diff): `simulations_per_level: int = 10000`
- Line 281-282 (diff): `bankroll_units = [20, 40, 60, 80, 100]`

**Recommendation:** Define module-level constants:
```python
DEFAULT_MAX_SESSIONS_PER_SIM: int = 10_000
DEFAULT_SIMULATIONS_PER_LEVEL: int = 10_000
DEFAULT_BANKROLL_UNITS: tuple[int, ...] = (20, 40, 60, 80, 100)
```

---

**3. Import inside function body violates convention**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/visualizations/risk_curves.py` (lines 190-191 in diff, approx lines 175-176 in actual file)

```python
from matplotlib.ticker import FuncFormatter

ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y:.0%}"))
```

The import is placed inside the function body. While `histogram.py` and `trajectory.py` place all matplotlib imports at module level, this one is embedded in the function. This is inconsistent and adds a small overhead on each function call.

**Recommendation:** Move to module-level imports alongside other matplotlib imports.

---

**4. Inconsistent standard deviation calculation approach**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py` (lines 302-304 in diff)

```python
std_profit = (
    float(np.std(session_profits, ddof=1)) if len(session_profits) > 1 else 0.0
)
```

The code uses `np.std(..., ddof=1)` for sample standard deviation, but the existing `statistics.py` module uses Python's `statistics.stdev()`. While both produce identical results, using different approaches for the same operation reduces consistency.

**Recommendation:** Use `statistics.stdev()` for consistency with existing code, or add a comment explaining why numpy is preferred (e.g., performance with numpy arrays).

---

**5. Hardcoded confidence level in formatted output**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py` (lines 372-374 in diff, approx lines 406-408 in actual file)

```python
lines.append(
    f"  Ruin Probability: {result.ruin_probability:.2%} "
    f"(95% CI: {result.confidence_interval.lower:.2%} - "
    f"{result.confidence_interval.upper:.2%})"
)
```

The string "95% CI" is hardcoded even though `result.confidence_interval.level` contains the actual confidence level. If a different confidence level is used, the output would be misleading.

**Recommendation:**
```python
f"({result.confidence_interval.level:.0%} CI: {result.confidence_interval.lower:.2%} - "
```

---

**6. Duplicate array iteration pattern in visualization**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/visualizations/risk_curves.py` (lines 73-79 in diff)

```python
bankroll_units = np.array([r.bankroll_units for r in report.results])
ruin_probs = np.array([r.ruin_probability for r in report.results])
half_risks = np.array([r.half_bankroll_risk for r in report.results])
quarter_risks = np.array([r.quarter_bankroll_risk for r in report.results])
ci_lowers = np.array([r.confidence_interval.lower for r in report.results])
ci_uppers = np.array([r.confidence_interval.upper for r in report.results])
```

Six separate iterations over `report.results` to extract different attributes. While performance impact is minimal for small result sets, this violates DRY principles.

**Recommendation:** Consider a single-pass extraction:
```python
bankroll_units, ruin_probs, half_risks, quarter_risks, ci_lowers, ci_uppers = [], [], [], [], [], []
for r in report.results:
    bankroll_units.append(r.bankroll_units)
    ruin_probs.append(r.ruin_probability)
    # ... etc
```
Or accept the current approach with a comment noting it prioritizes readability.

### Low

**1. Missing validation for `simulations_per_level`**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py` (line 248 in diff)

The function validates `session_results`, `bankroll_units`, `confidence_level`, and `base_bet`, but does not validate that `simulations_per_level` is a positive integer. Passing zero or negative values would cause runtime errors.

**Recommendation:**
```python
if simulations_per_level <= 0:
    raise ValueError("simulations_per_level must be a positive integer")
```

---

**2. Test file imports private functions**

File: `/Users/chrishenry/source/let_it_ride/tests/unit/analytics/test_risk_of_ruin.py` (lines 11-22 in diff)

```python
from let_it_ride.analytics.risk_of_ruin import (
    _calculate_analytical_ruin_probability,
    _calculate_ruin_for_bankroll_level,
    _run_monte_carlo_ruin_simulation,
    _validate_bankroll_units,
    _validate_confidence_level,
    _validate_session_results,
    ...
)
```

The test file imports and tests multiple private functions (prefixed with `_`). While this provides thorough coverage, it couples tests to implementation details, making refactoring more difficult.

**Recommendation:** This is acceptable given the comprehensive coverage provided. Consider adding a comment noting these are implementation tests.

---

**3. Docstring states return type as Optional but never returns None**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py` (lines 108-109 in diff)

```python
def _calculate_analytical_ruin_probability(
    mean_profit: float,
    std_profit: float,
    bankroll: float,
) -> float | None:
    """...
    Returns:
        Analytical ruin probability, or None if calculation not applicable.
    """
```

The function signature indicates it may return `None`, but examining the implementation, it always returns a `float` (0.0, 1.0, or the calculated probability). The `None` branch was likely planned but not implemented.

**Recommendation:** Either update the return type to just `float`, or document when `None` would be returned if planned for future use.

---

**4. Hardcoded visualization confidence band label**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/visualizations/risk_curves.py` (line 128 in diff)

```python
label="95% Confidence Band",
```

Similar to the report formatting issue, this hardcodes "95%" when the actual confidence level could be different.

**Recommendation:** Use the actual confidence level from the report data.

---

**5. Color values as magic strings**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/visualizations/risk_curves.py` (lines 87-135 in diff)

```python
color="#ffd93d"
color="#ff9f43"
color="#e74c3c"
color="#3498db"
color="#2ecc71"
color="#f39c12"
```

Multiple hardcoded color hex values are used throughout the visualization code without named constants.

**Recommendation:** Define a color palette at module level:
```python
COLORS = {
    "quarter_loss": "#ffd93d",
    "half_loss": "#ff9f43",
    "ruin": "#e74c3c",
    "analytical": "#3498db",
    "threshold_1pct": "#2ecc71",
    "threshold_5pct": "#f39c12",
}
```

### Informational

**1. Positive: Excellent adherence to project patterns**

The code correctly uses:
- `@dataclass(frozen=True, slots=True)` for result/report dataclasses
- `@dataclass(slots=True)` for mutable config classes (matching `HistogramConfig` and `TrajectoryConfig`)
- `TYPE_CHECKING` guards for conditional imports
- Private validation functions (`_validate_*`) following the pattern in `statistics.py`
- Consistent docstring format with Args, Returns, and Raises sections

---

**2. Positive: Comprehensive type hints**

All function signatures have complete type annotations:
- Return types for all functions
- Generic numpy array types (`NDArray[np.floating[Any]]`)
- Optional types using modern union syntax (`Sequence[int] | None`)
- Tuple types for immutable collections in dataclasses

---

**3. Positive: Robust numerical stability handling**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py` (lines 125-127 in diff)

```python
# Prevent overflow for very negative exponents
if exponent < -700:
    return 0.0
```

Good attention to potential floating-point overflow in exponential calculations.

---

**4. Positive: Clean module organization**

The code cleanly separates concerns:
- Data structures (`RiskOfRuinResult`, `RiskOfRuinReport`)
- Validation (`_validate_*` functions)
- Core algorithms (`_run_monte_carlo_ruin_simulation`, `_calculate_analytical_ruin_probability`)
- Public API (`calculate_risk_of_ruin`, `format_risk_of_ruin_report`)

---

**5. Positive: Proper resource cleanup in visualization**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/visualizations/risk_curves.py` (lines 256-260 in diff)

```python
fig = plot_risk_curves(report, config)
try:
    fig.savefig(path, format=output_format, dpi=config.dpi, bbox_inches="tight")
finally:
    plt.close(fig)
```

Using `try/finally` ensures matplotlib figures are properly closed, preventing memory leaks.

---

**6. Positive: Thorough test coverage**

The test file covers:
- Dataclass creation and immutability verification
- All validation functions with edge cases
- Monte Carlo simulation behavior (guaranteed win/loss scenarios)
- Convergence properties with different simulation counts
- Reproducibility with random seeds
- Numerical stability with extreme values

## Summary Table

| Severity | Count |
|----------|-------|
| Critical | 0 |
| High | 0 |
| Medium | 6 |
| Low | 5 |
| Informational | 6 |
