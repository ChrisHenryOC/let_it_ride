# Documentation Review - PR #133

## Summary

The PR introduces comprehensive risk of ruin calculation capabilities with well-structured documentation throughout. The mathematical formulas are accurately documented, and docstrings are consistent with actual implementations. Minor improvements are needed for the base bet inference documentation and threshold terminology clarity.

## Findings

### Critical

None identified.

### High

**[H1] Inaccurate base_bet Inference Documentation**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py:295-296`

The docstring states base_bet is inferred "by dividing starting bankroll by a typical multiple", but the actual implementation at lines 322-328 infers it from `total_wagered / (hands_played * 3)`:

```python
# Docstring says:
base_bet: Base bet amount. If not provided, infers from session data
    by dividing starting bankroll by a typical multiple.

# Actual implementation:
total_wagered = sum(r.total_wagered for r in session_results)
total_hands = sum(r.hands_played for r in session_results)
# Each hand has 3 base bets wagered (bet1, bet2, bet3)
estimated_base = total_wagered / (total_hands * 3) if total_hands > 0 else 1.0
```

The docstring should be updated to accurately describe the inference mechanism.

### Medium

**[M1] Inconsistent Threshold Terminology Between Code and Docstrings**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py:37-38`

The `quarter_bankroll_risk` attribute is documented as "Probability of losing 25% of bankroll", but the implementation at lines 188-189 and 203-205 defines the threshold as `bankroll * 0.75`:

```python
quarter_threshold = bankroll * 0.75

if not hit_quarter and current_bankroll <= quarter_threshold:
```

This means the risk tracks when the bankroll drops TO 75% of its value (i.e., a 25% loss has occurred). While technically correct, the phrasing could be clearer to indicate this is the probability of bankroll falling to or below 75% of starting value.

**[M2] Return Type Documentation Could Be More Specific**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py:140-141`

The docstring for `_calculate_analytical_ruin_probability` states:

```python
Returns:
    Analytical ruin probability, or None if calculation not applicable.
```

However, the implementation never returns `None` - it always returns a `float` (0.0, 1.0, or the calculated probability). The return type hint `float | None` is misleading since `None` is never returned.

**[M3] Missing Raises Documentation for `plot_risk_curves`**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/visualizations/risk_curves.py:64-65`

The function documents `ValueError: If report has no results` but does not document that the underlying `plot_risk_curves` call could also raise this error in `save_risk_curves`. The `save_risk_curves` function at line 239 only documents the format validation error, not the empty results error that propagates from `plot_risk_curves`.

### Low

**[L1] Hardcoded Confidence Level in Formatted Output**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py:406-408`

The formatted output hardcodes "95% CI" regardless of the actual confidence level used:

```python
lines.append(
    f"  Ruin Probability: {result.ruin_probability:.2%} "
    f"(95% CI: {result.confidence_interval.lower:.2%} - "
    f"{result.confidence_interval.upper:.2%})"
)
```

Should use `result.confidence_interval.level` to display the actual confidence level.

**[L2] Visualization Confidence Band Label Hardcoded**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/visualizations/risk_curves.py:128`

The confidence band label is hardcoded as "95% Confidence Band":

```python
label="95% Confidence Band",
```

This should dynamically reflect the actual confidence level from the report data.

**[L3] Missing Algorithm Complexity Documentation**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py:162-216`

The Monte Carlo simulation function `_run_monte_carlo_ruin_simulation` would benefit from documenting the time/space complexity (O(simulations * max_sessions_per_sim)) to help users understand performance implications.

**[L4] Scratchpad Task List Outdated**

File: `/Users/chrishenry/source/let_it_ride/scratchpads/issue-41-risk-of-ruin.md:17-31`

The task list in the scratchpad shows most items as unchecked even though they appear to be implemented. The scratchpad also shows a different `RiskOfRuinResult` structure (missing `quarter_bankroll_risk`) compared to the actual implementation.

### Positive

**[P1] Excellent Mathematical Formula Documentation**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py:125-141`

The analytical ruin probability function includes clear mathematical notation:

```python
"""Calculate analytical ruin probability using normal approximation.

Uses the gambler's ruin formula with normal distribution approximation.
For a random walk with drift:
P(ruin) ≈ exp(-2 * mu * B / sigma^2) when mu > 0
P(ruin) = 1 when mu <= 0
```

**[P2] Comprehensive Attribute Documentation**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py:29-47`

Both dataclass docstrings follow the Attributes style consistently and document all fields clearly:

```python
Attributes:
    bankroll_units: Bankroll as multiple of base bet.
    ruin_probability: Probability of losing entire bankroll.
    confidence_interval: Confidence interval for ruin probability.
    ...
```

**[P3] Well-Documented Visualization Components**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/visualizations/risk_curves.py:47-66`

The `plot_risk_curves` function provides excellent user documentation with a clear list of what the visualization includes:

```python
Creates a plot showing:
- Ruin probability curve across bankroll levels
- Half-bankroll (50% loss) risk curve
- Quarter-bankroll (25% loss) risk curve
- Confidence bands for ruin probability
- Optional analytical estimate comparison
- Common risk threshold lines (1%, 5%, 10%)
```

**[P4] Consistent Validation Function Documentation**

Files: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py:71-117`

All three validation helper functions (`_validate_bankroll_units`, `_validate_session_results`, `_validate_confidence_level`) follow a consistent documentation pattern with Args, Raises sections.

**[P5] Type Hints Match Docstrings Throughout**

The type hints are consistent with the documented types across all public interfaces. For example:

- `bankroll_units: Sequence[int] | None = None` matches "Bankroll levels as multiples of base bet"
- `results: tuple[RiskOfRuinResult, ...]` matches "Risk of ruin results for each bankroll level"

**[P6] Comprehensive Test Documentation**

File: `/Users/chrishenry/source/let_it_ride/tests/unit/analytics/test_risk_of_ruin.py`

Test classes and methods have clear docstrings explaining what each test validates, following consistent patterns like "Should..." or "...should raise ValueError."
