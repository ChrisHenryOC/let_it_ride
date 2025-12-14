# Code Quality Review - PR #133

## Summary

This PR introduces a well-structured risk of ruin calculator with Monte Carlo simulation and analytical estimation capabilities. The code follows project conventions (frozen dataclasses with slots, TYPE_CHECKING guards, validation helpers) and includes comprehensive test coverage. However, there are a few code quality issues related to consistency with existing patterns, potential improvements to error handling, and minor naming concerns.

## Findings

### Critical

None identified.

### High

None identified.

### Medium

**1. Missing `frozen=True` on RiskCurveConfig dataclass** - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/visualizations/risk_curves.py:629-630`

The `RiskCurveConfig` dataclass uses only `slots=True` but not `frozen=True`, which is inconsistent with other config classes in the project. Looking at the existing patterns:
- `HistogramConfig` uses `@dataclass(slots=True)` (line 18 in histogram.py)
- `TrajectoryConfig` uses `@dataclass(slots=True)` (line 24 in trajectory.py)

However, the `RiskOfRuinResult` and `RiskOfRuinReport` dataclasses in the main module correctly use `@dataclass(frozen=True, slots=True)`. For domain objects (results/reports), immutability is important; for configuration objects, mutability is acceptable. The current approach is consistent with other visualization config classes.

**Recommendation:** This is actually consistent with existing visualization config patterns. No change needed.

**2. Import inside function body** - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/visualizations/risk_curves.py:802-803`

```python
from matplotlib.ticker import FuncFormatter

ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y:.0%}"))
```

The `FuncFormatter` is imported inside the `plot_risk_curves` function rather than at the top of the module. While this avoids a top-level import, it is inconsistent with the existing pattern in `histogram.py` and `trajectory.py` where all matplotlib imports are at module level.

**Recommendation:** Move `from matplotlib.ticker import FuncFormatter` to the top-level imports for consistency and slight performance benefit on repeated calls.

**3. Inconsistent standard deviation calculation** - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py:483-485`

```python
std_profit = (
    float(np.std(session_profits, ddof=1)) if len(session_profits) > 1 else 0.0
)
```

The code uses `np.std(..., ddof=1)` for sample standard deviation, but the existing `statistics.py` module uses Python's `statistics.stdev()` for the same calculation. While both produce the same result, using different approaches for the same operation across the codebase reduces consistency.

**Recommendation:** Consider using `statistics.stdev()` for consistency with `statistics.py`, or document why numpy is preferred here (performance with numpy arrays).

**4. Magic numbers for simulation defaults** - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py:315,428,461-462`

Several magic numbers appear in the code without named constants:

- Line 315: `max_sessions_per_sim: int = 10000`
- Line 428: `simulations_per_level: int = 10000`
- Line 461-462: `bankroll_units = [20, 40, 60, 80, 100]`

**Recommendation:** Define these as module-level constants with descriptive names:

```python
DEFAULT_MAX_SESSIONS_PER_SIM: int = 10000
DEFAULT_SIMULATIONS_PER_LEVEL: int = 10000
DEFAULT_BANKROLL_UNITS: tuple[int, ...] = (20, 40, 60, 80, 100)
```

**5. Potential floating-point precision issue in threshold calculation** - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py:335-336`

```python
half_threshold = bankroll * 0.5
quarter_threshold = bankroll * 0.75
```

The naming `quarter_threshold` for `bankroll * 0.75` is confusing since this represents "75% of bankroll remaining" (i.e., 25% loss), not a quarter of the bankroll. This naming confusion could lead to maintenance issues.

**Recommendation:** Rename for clarity:
```python
loss_25pct_threshold = bankroll * 0.75  # 25% loss = 75% remaining
loss_50pct_threshold = bankroll * 0.50  # 50% loss = 50% remaining
```

### Low

**1. Unused type import** - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py:163`

```python
from typing import TYPE_CHECKING, Any
```

The `Any` import is used only in the numpy type hint `NDArray[np.floating[Any]]`. This is correct usage for numpy array typing.

**2. Docstring inconsistency for `quarter_bankroll_risk`** - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py:186`

The docstring says "Probability of losing 25% of bankroll" but the implementation tracks when bankroll drops to 75% of starting (which is indeed a 25% loss). The docstring is technically correct but could be clearer to match the threshold variable naming pattern used elsewhere.

**Recommendation:** Consider clarifying: "Probability of bankroll dropping to 75% of starting value (25% loss)."

**3. Consider adding validation for `simulations_per_level`** - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py:428`

The function validates `session_results`, `bankroll_units`, `confidence_level`, and `base_bet`, but does not validate that `simulations_per_level` is positive.

**Recommendation:** Add validation:
```python
if simulations_per_level <= 0:
    raise ValueError("simulations_per_level must be positive")
```

**4. Test file imports private functions** - `/Users/chrishenry/source/let_it_ride/tests/unit/analytics/test_risk_of_ruin.py:888-896`

The test file imports and tests private functions (prefixed with `_`):
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

While testing private functions provides good coverage, it couples tests to implementation details. This is a minor concern as the practice is common and the functions are well-documented.

**5. Hardcoded confidence level in format output** - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py:555-556`

```python
f"(95% CI: {result.confidence_interval.lower:.2%} - "
```

The formatted output hardcodes "95% CI" but the actual confidence level is stored in `result.confidence_interval.level`. If a different confidence level is used, the output would be misleading.

**Recommendation:** Use the actual confidence level:
```python
f"({result.confidence_interval.level:.0%} CI: {result.confidence_interval.lower:.2%} - "
```

### Positive

**1. Excellent adherence to project patterns** - The code correctly uses:
- `@dataclass(frozen=True, slots=True)` for result/report dataclasses
- `TYPE_CHECKING` guards for conditional imports
- Private validation functions (`_validate_*`) following the established pattern in `statistics.py` and `validation.py`
- Consistent docstring format with Args, Returns, and Raises sections

**2. Comprehensive type hints** - All function signatures have complete type annotations including:
- Return types for all functions
- Generic numpy array types (`NDArray[np.floating[Any]]`)
- Optional types properly annotated (`Sequence[int] | None`)
- Tuple types for immutable collections in dataclasses

**3. Robust error handling** - The validation functions provide clear, actionable error messages:
- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py:229-231`: Clear message for empty bankroll_units
- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py:248-250`: Informative minimum data requirement
- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py:263-265`: Specific bounds in confidence level error

**4. Numerical stability considerations** - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py:303-305`
```python
# Prevent overflow for very negative exponents
if exponent < -700:
    return 0.0
```
Good attention to potential overflow in exponential calculations.

**5. Thorough test coverage** - The test file covers:
- Dataclass creation and immutability
- All validation functions
- Edge cases (guaranteed win/loss, numerical stability)
- Convergence properties of Monte Carlo estimation
- Reproducibility with random seeds

**6. Clean visualization implementation** - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/visualizations/risk_curves.py`:
- Follows the existing pattern from `histogram.py` and `trajectory.py`
- Proper resource cleanup with `plt.close(fig)` in finally block
- Consistent color scheme with other visualizations

**7. Well-organized module structure** - The code cleanly separates:
- Data structures (`RiskOfRuinResult`, `RiskOfRuinReport`)
- Validation (`_validate_*` functions)
- Core algorithms (`_run_monte_carlo_ruin_simulation`, `_calculate_analytical_ruin_probability`)
- Public API (`calculate_risk_of_ruin`, `format_risk_of_ruin_report`)
