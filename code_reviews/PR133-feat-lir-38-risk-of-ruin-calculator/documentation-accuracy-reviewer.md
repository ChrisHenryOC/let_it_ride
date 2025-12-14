# Documentation Accuracy Review - PR #133

## Summary

This PR introduces a well-documented risk of ruin calculator with comprehensive docstrings for public functions and dataclasses. The mathematical formulas are accurately documented, and most docstrings correctly describe their implementations. However, there are several documentation inaccuracies including a misleading docstring for base_bet inference, a return type hint that suggests None can be returned when it never is, hardcoded confidence level strings in output, and outdated scratchpad documentation.

## Findings

### High

#### [H1] Inaccurate base_bet Inference Docstring

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py:295-296`

The docstring for the `base_bet` parameter in `calculate_risk_of_ruin()` states:

```python
base_bet: Base bet amount. If not provided, infers from session data
    by dividing starting bankroll by a typical multiple.
```

However, the actual implementation at lines 322-328 uses a completely different approach:

```python
# Estimate base bet from total wagered / hands played
total_wagered = sum(r.total_wagered for r in session_results)
total_hands = sum(r.hands_played for r in session_results)
# Each hand has 3 base bets wagered (bet1, bet2, bet3)
estimated_base = total_wagered / (total_hands * 3) if total_hands > 0 else 1.0
```

The docstring describes "dividing starting bankroll by a typical multiple" but the implementation calculates `total_wagered / (hands_played * 3)`. This discrepancy could mislead users about how base_bet inference works.

**Recommendation:** Update the docstring to accurately describe the inference mechanism:
```python
base_bet: Base bet amount. If not provided, infers from session data
    by dividing total wagered by (total hands * 3), since each hand
    involves 3 base bets.
```

---

### Medium

#### [M1] Return Type Hint Suggests None When Never Returned

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py:124, 140-141`

The function `_calculate_analytical_ruin_probability` has return type `float | None` and docstring stating:

```python
Returns:
    Analytical ruin probability, or None if calculation not applicable.
```

However, reviewing the implementation (lines 143-159), the function always returns a `float`:
- Returns `0.0` if `std_profit == 0` and `mean_profit > 0`
- Returns `1.0` if `std_profit == 0` and `mean_profit <= 0`
- Returns `1.0` if `mean_profit <= 0`
- Returns `0.0` if `exponent < -700`
- Returns `math.exp(exponent)` otherwise

The function never returns `None`. The type hint and docstring are misleading.

**Recommendation:** Update the return type to `float` and remove "or None if calculation not applicable" from the docstring.

---

#### [M2] Unclear quarter_bankroll_risk Terminology

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py:38`

The `RiskOfRuinResult` dataclass documents:

```python
quarter_bankroll_risk: Probability of losing 25% of bankroll.
```

While technically accurate, this terminology could be confusing because the implementation at lines 189 and 203-205 uses:

```python
quarter_threshold = bankroll * 0.75

if not hit_quarter and current_bankroll <= quarter_threshold:
```

The threshold is "75% of bankroll remaining" (25% loss). The docstring correctly describes the meaning but the naming `quarter_bankroll_risk` combined with "Probability of losing 25%" could be misread as "probability of losing a quarter (25%) of bankroll" which IS what it means, but without the context of the threshold calculation.

**Recommendation:** Consider clarifying: "Probability of bankroll dropping to 75% of starting value (i.e., 25% cumulative loss)."

---

#### [M3] Missing Raises Documentation for save_risk_curves

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/visualizations/risk_curves.py:238-239`

The `save_risk_curves` function docstring lists:

```python
Raises:
    ValueError: If report has no results or format is invalid.
```

However, the function calls `plot_risk_curves(report, config)` at line 256, which can also raise `ValueError` for empty results. While the error is mentioned, it is not clear that it propagates from the internal `plot_risk_curves` call. The "format is invalid" error is directly raised at line 241-242.

**Recommendation:** The Raises section is mostly accurate but could clarify the error propagation chain for completeness.

---

### Low

#### [L1] Hardcoded "95% CI" in Formatted Report Output

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py:406-408`

The `format_risk_of_ruin_report` function hardcodes "95% CI" in the output:

```python
lines.append(
    f"  Ruin Probability: {result.ruin_probability:.2%} "
    f"(95% CI: {result.confidence_interval.lower:.2%} - "
    f"{result.confidence_interval.upper:.2%})"
)
```

The actual confidence level is stored in `result.confidence_interval.level` and could differ from 95% if the user specifies a different `confidence_level` parameter in `calculate_risk_of_ruin`.

**Recommendation:** Use the actual confidence level:
```python
f"({result.confidence_interval.level:.0%} CI: ..."
```

---

#### [L2] Hardcoded "95% Confidence Band" in Visualization

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/visualizations/risk_curves.py:128`

Similar to the report formatting issue, the visualization label is hardcoded:

```python
label="95% Confidence Band",
```

This should use the actual confidence level from the report data for consistency.

---

#### [L3] Outdated Scratchpad Task List

**File:** `/Users/chrishenry/source/let_it_ride/scratchpads/issue-41-risk-of-ruin.md:17-25`

The scratchpad task list shows most items as unchecked (e.g., "Implement RiskOfRuinResult and RiskOfRuinReport dataclasses") when the implementation is complete. This is misleading for anyone reviewing the work-in-progress state.

Additionally, the scratchpad shows a different `RiskOfRuinResult` structure at lines 31-36 that is missing the `quarter_bankroll_risk` field which exists in the actual implementation.

---

#### [L4] Module Docstring in analytics/__init__.py Not Updated

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/__init__.py:1-10`

The module docstring lists capabilities but does not mention risk of ruin:

```python
"""Statistics and reporting.

This module contains analytics and export functionality:
- Core statistics calculator
- Statistical validation
- Chair position analytics
- Strategy comparison analytics
- Export formats (CSV, JSON, HTML)
- Visualizations (histograms, trajectories)
"""
```

The exports and `__all__` list correctly include risk of ruin components, but the docstring does not mention this new capability.

**Recommendation:** Add "- Risk of ruin analysis" to the bullet list.

---

### Informational

#### [I1] Excellent Mathematical Formula Documentation

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py:125-133`

The analytical ruin probability function includes clear mathematical notation:

```python
"""Calculate analytical ruin probability using normal approximation.

Uses the gambler's ruin formula with normal distribution approximation.
For a random walk with drift:
P(ruin) = exp(-2 * mu * B / sigma^2) when mu > 0
P(ruin) = 1 when mu <= 0
```

This is an excellent example of documenting mathematical formulas in code.

---

#### [I2] Comprehensive Visualization Docstring

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/visualizations/risk_curves.py:47-55`

The `plot_risk_curves` function provides excellent documentation of what the visualization includes:

```python
Creates a plot showing:
- Ruin probability curve across bankroll levels
- Half-bankroll (50% loss) risk curve
- Quarter-bankroll (25% loss) risk curve
- Confidence bands for ruin probability
- Optional analytical estimate comparison
- Common risk threshold lines (1%, 5%, 10%)
```

This gives users a clear understanding of the output without needing to read the implementation.

---

#### [I3] Consistent Attribute Documentation Style

**Files:**
- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py:33-40, 54-61`
- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/visualizations/risk_curves.py:22-31`

All dataclasses use the `Attributes:` documentation style consistently, matching project patterns and providing clear descriptions of each field.

---

#### [I4] Well-Documented Validation Functions

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py:71-117`

All three validation helper functions (`_validate_bankroll_units`, `_validate_session_results`, `_validate_confidence_level`) follow a consistent documentation pattern with Args and Raises sections, making the code self-documenting.

---

#### [I5] Type Hints Consistent with Documentation

Throughout the PR, type hints match the documented types. For example:
- `bankroll_units: Sequence[int] | None = None` matches the docstring "Bankroll levels as multiples of base bet"
- `results: tuple[RiskOfRuinResult, ...]` matches "Risk of ruin results for each bankroll level"

---

## Summary by Severity

| Severity | Count |
|----------|-------|
| Critical | 0 |
| High | 1 |
| Medium | 3 |
| Low | 4 |
| Informational | 5 |

## Verdict

The documentation is generally comprehensive and well-structured, following project conventions. The high-severity finding (H1 - inaccurate base_bet inference docstring) should be fixed before merge as it could mislead users about the base_bet inference behavior. The medium and low severity findings are recommended improvements that would enhance documentation accuracy and consistency.
