# LIR-26: Strategy Comparison Analytics

**GitHub Issue:** https://github.com/ChrisHenryOC/let_it_ride/issues/29

## Overview

Implement statistical comparison between different strategies, allowing users to determine if one strategy significantly outperforms another.

## Key Requirements

1. Side-by-side metrics comparison dataclass
2. Statistical significance testing (two-sample t-test for session profits)
3. Mann-Whitney U test for non-normal distributions
4. Effect size calculation (Cohen's d)
5. Relative performance metrics (% improvement)
6. Comparison report generation
7. Support comparing 2+ strategies

## Implementation Plan

### Files to Create
- `src/let_it_ride/analytics/comparison.py`
- `tests/unit/analytics/test_comparison.py`

### Data Classes

1. **SignificanceTest** - Results of a statistical significance test
   - test_name: str (e.g., "t-test", "mann-whitney")
   - statistic: float
   - p_value: float
   - is_significant: bool

2. **EffectSize** - Effect size measurement
   - cohens_d: float
   - interpretation: str ("negligible", "small", "medium", "large")

3. **StrategyComparison** - Complete comparison between two strategies
   - strategy_a_name, strategy_b_name
   - Win rate comparison (win_rate_a, win_rate_b, win_rate_diff)
   - EV comparison (ev_a, ev_b, ev_diff, ev_pct_diff)
   - significance: SignificanceTest
   - effect_size: EffectSize
   - better_strategy: str | None
   - confidence: str ("high", "medium", "low")

### Functions

1. **compare_strategies()** - Main comparison function
   - Takes two lists of SessionResult
   - Performs t-test and Mann-Whitney U
   - Calculates Cohen's d
   - Returns StrategyComparison

2. **compare_multiple_strategies()** - Compare multiple strategies
   - Takes dict of strategy_name -> list[SessionResult]
   - Returns list of pairwise StrategyComparison

3. **_perform_ttest()** - Independent samples t-test
   - Uses scipy.stats.ttest_ind

4. **_perform_mannwhitney()** - Mann-Whitney U test
   - Uses scipy.stats.mannwhitneyu

5. **_calculate_cohens_d()** - Effect size calculation
   - Cohen's d = (mean1 - mean2) / pooled_std

### Effect Size Interpretation (Cohen's Guidelines)
- |d| < 0.2: negligible
- 0.2 <= |d| < 0.5: small
- 0.5 <= |d| < 0.8: medium
- |d| >= 0.8: large

### Confidence Levels
- "high": p < 0.01 and large effect size
- "medium": p < 0.05 and at least small effect size
- "low": otherwise

## Testing Strategy

1. Test with identical distributions (no difference expected)
2. Test with known effect sizes (create synthetic data)
3. Test with clearly different distributions
4. Test edge cases (empty lists, single session, etc.)
5. Test multiple strategy comparison
