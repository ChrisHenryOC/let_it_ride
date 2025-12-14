# LIR-38: Risk of Ruin Calculator (GitHub #41)

**Issue:** https://github.com/ChrisHenryOC/let_it_ride/issues/41

## Summary

Implement risk of ruin calculation for various bankroll levels, including:
- Analytical risk of ruin formula (if applicable)
- Monte Carlo risk of ruin estimation
- Probability of losing X% of bankroll
- Risk curves for different bankroll multiples
- Visualization of risk curves

## Tasks

- [x] Explore codebase for patterns
- [ ] Create feature branch
- [ ] Implement `RiskOfRuinResult` and `RiskOfRuinReport` dataclasses
- [ ] Implement Monte Carlo risk of ruin estimation
- [ ] Implement analytical formula (gambler's ruin) if applicable
- [ ] Implement `calculate_risk_of_ruin()` function
- [ ] Implement risk curves visualization
- [ ] Write unit tests
- [ ] Run tests, linting, type checking
- [ ] Create PR

## Key Types (from issue)

```python
@dataclass
class RiskOfRuinResult:
    bankroll_units: int  # Bankroll as multiple of base bet
    ruin_probability: float  # Probability of losing entire bankroll
    confidence_interval: ConfidenceInterval
    half_bankroll_risk: float  # Probability of losing 50%
    sessions_simulated: int

@dataclass
class RiskOfRuinReport:
    base_bet: float
    results: list[RiskOfRuinResult]  # For each bankroll level
```

## Implementation Notes

### Existing Patterns to Follow

1. **Frozen dataclasses with slots**: `@dataclass(frozen=True, slots=True)`
2. **Confidence intervals**: Use existing `ConfidenceInterval` class from `statistics.py`
3. **Validation helpers**: Create `_validate_*` private functions
4. **TYPE_CHECKING guards**: Prevent circular imports

### Monte Carlo Approach

For each bankroll level:
1. Sample session profits from simulation results
2. Simulate bankroll trajectories
3. Count trajectories that hit ruin (bankroll <= 0)
4. Calculate ruin probability with confidence interval

### Gambler's Ruin Formula (if applicable)

For games with known win probability p and loss probability q = 1-p:
- If p = q: P(ruin) = 1 - n/N (n = starting units, N = target)
- If p != q: P(ruin) = ((q/p)^N - (q/p)^n) / ((q/p)^N - 1)

This may be useful as a comparison/validation for Monte Carlo results.

### Files to Create

1. `src/let_it_ride/analytics/risk_of_ruin.py`
2. `src/let_it_ride/analytics/visualizations/risk_curves.py`
3. `tests/unit/analytics/test_risk_of_ruin.py`

### Files to Modify

1. `src/let_it_ride/analytics/__init__.py` - Add exports
2. `src/let_it_ride/analytics/visualizations/__init__.py` - Add exports
