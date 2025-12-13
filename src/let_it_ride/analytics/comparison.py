"""Strategy comparison analytics.

This module provides statistical comparison between different strategies:
- Two-sample t-test for session profits
- Mann-Whitney U test for non-normal distributions
- Cohen's d effect size calculation
- Side-by-side metrics comparison
- Multi-strategy comparison support
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import mean, stdev
from typing import TYPE_CHECKING

from scipy import stats

if TYPE_CHECKING:
    from let_it_ride.simulation.session import SessionResult

# Cohen's d effect size thresholds (per Cohen, 1988)
COHENS_D_SMALL_THRESHOLD = 0.2
COHENS_D_MEDIUM_THRESHOLD = 0.5
COHENS_D_LARGE_THRESHOLD = 0.8

# Report formatting constants
REPORT_SEPARATOR_WIDTH = 60


@dataclass(frozen=True, slots=True)
class SignificanceTest:
    """Results of a statistical significance test.

    Attributes:
        test_name: Name of the test performed ("t-test" or "mann-whitney").
        statistic: The test statistic value.
        p_value: The p-value from the test.
        is_significant: Whether the result is statistically significant.
    """

    test_name: str
    statistic: float
    p_value: float
    is_significant: bool


@dataclass(frozen=True, slots=True)
class EffectSize:
    """Effect size measurement using Cohen's d.

    Attributes:
        cohens_d: Cohen's d effect size value.
        interpretation: Qualitative interpretation of effect size.
            One of: "negligible", "small", "medium", "large".
    """

    cohens_d: float
    interpretation: str


@dataclass(frozen=True, slots=True)
class StrategyComparison:
    """Complete comparison results between two strategies.

    Attributes:
        strategy_a_name: Name of the first strategy.
        strategy_b_name: Name of the second strategy.
        sessions_a: Number of sessions for strategy A.
        sessions_b: Number of sessions for strategy B.
        win_rate_a: Session win rate for strategy A.
        win_rate_b: Session win rate for strategy B.
        win_rate_diff: Difference in win rates (A - B).
        ev_a: Expected value per hand for strategy A.
        ev_b: Expected value per hand for strategy B.
        ev_diff: Difference in EV (A - B).
        ev_pct_diff: Percentage difference in EV relative to B ((ev_diff / |ev_b|) * 100).
            None if ev_b is zero (percentage undefined).
        profit_mean_a: Mean session profit for strategy A.
        profit_mean_b: Mean session profit for strategy B.
        profit_std_a: Std deviation of session profit for strategy A.
        profit_std_b: Std deviation of session profit for strategy B.
        ttest: T-test results for session profits.
        mann_whitney: Mann-Whitney U test results for session profits.
        effect_size: Cohen's d effect size.
        better_strategy: Name of better strategy, or None if not significant.
        confidence: Confidence level in recommendation ("high", "medium", "low").
    """

    strategy_a_name: str
    strategy_b_name: str
    sessions_a: int
    sessions_b: int
    win_rate_a: float
    win_rate_b: float
    win_rate_diff: float
    ev_a: float
    ev_b: float
    ev_diff: float
    ev_pct_diff: float | None
    profit_mean_a: float
    profit_mean_b: float
    profit_std_a: float
    profit_std_b: float
    ttest: SignificanceTest
    mann_whitney: SignificanceTest
    effect_size: EffectSize
    better_strategy: str | None
    confidence: str


def _interpret_cohens_d(d: float) -> str:
    """Interpret Cohen's d effect size using standard thresholds.

    Uses thresholds defined by Cohen (1988):
    - |d| < 0.2: negligible
    - 0.2 <= |d| < 0.5: small
    - 0.5 <= |d| < 0.8: medium
    - |d| >= 0.8: large

    Args:
        d: Cohen's d value (can be negative).

    Returns:
        Interpretation string: "negligible", "small", "medium", or "large".
    """
    abs_d = abs(d)
    if abs_d < COHENS_D_SMALL_THRESHOLD:
        return "negligible"
    elif abs_d < COHENS_D_MEDIUM_THRESHOLD:
        return "small"
    elif abs_d < COHENS_D_LARGE_THRESHOLD:
        return "medium"
    else:
        return "large"


def _calculate_cohens_d(
    data_a: tuple[float, ...], data_b: tuple[float, ...]
) -> EffectSize:
    """Calculate Cohen's d effect size between two groups.

    Uses the pooled standard deviation formula:
    d = (mean_a - mean_b) / pooled_std

    Args:
        data_a: Tuple of values for group A.
        data_b: Tuple of values for group B.

    Returns:
        EffectSize with Cohen's d and interpretation.
    """
    n_a = len(data_a)
    n_b = len(data_b)

    if n_a == 0 or n_b == 0:
        return EffectSize(cohens_d=0.0, interpretation="negligible")

    mean_a = mean(data_a)
    mean_b = mean(data_b)

    # Calculate pooled standard deviation
    var_a = stdev(data_a) ** 2 if n_a > 1 else 0.0
    var_b = stdev(data_b) ** 2 if n_b > 1 else 0.0

    # Pooled variance: weighted average by degrees of freedom
    if n_a + n_b <= 2:
        pooled_std = 0.0
    else:
        pooled_var = ((n_a - 1) * var_a + (n_b - 1) * var_b) / (n_a + n_b - 2)
        pooled_std = math.sqrt(pooled_var)

    if math.isclose(pooled_std, 0.0, abs_tol=1e-10):
        # If no variance, effect size is undefined; return 0
        return EffectSize(cohens_d=0.0, interpretation="negligible")

    cohens_d = (mean_a - mean_b) / pooled_std
    interpretation = _interpret_cohens_d(cohens_d)

    return EffectSize(cohens_d=cohens_d, interpretation=interpretation)


def _perform_ttest(
    data_a: tuple[float, ...],
    data_b: tuple[float, ...],
    significance_level: float = 0.05,
) -> SignificanceTest:
    """Perform independent samples t-test.

    Uses Welch's t-test (unequal variance assumption) for robustness.

    Args:
        data_a: Tuple of values for group A.
        data_b: Tuple of values for group B.
        significance_level: Threshold for significance (default 0.05).

    Returns:
        SignificanceTest with t-test results.
    """
    if len(data_a) < 2 or len(data_b) < 2:
        return SignificanceTest(
            test_name="t-test",
            statistic=0.0,
            p_value=1.0,
            is_significant=False,
        )

    result = stats.ttest_ind(data_a, data_b, equal_var=False)
    p_value = float(result.pvalue)

    return SignificanceTest(
        test_name="t-test",
        statistic=float(result.statistic),
        p_value=p_value,
        is_significant=p_value < significance_level,
    )


def _perform_mannwhitney(
    data_a: tuple[float, ...],
    data_b: tuple[float, ...],
    significance_level: float = 0.05,
) -> SignificanceTest:
    """Perform Mann-Whitney U test (non-parametric alternative to t-test).

    Args:
        data_a: Tuple of values for group A.
        data_b: Tuple of values for group B.
        significance_level: Threshold for significance (default 0.05).

    Returns:
        SignificanceTest with Mann-Whitney U test results.
    """
    if len(data_a) < 1 or len(data_b) < 1:
        return SignificanceTest(
            test_name="mann-whitney",
            statistic=0.0,
            p_value=1.0,
            is_significant=False,
        )

    # Handle case where all values are identical (short-circuit to avoid set creation)
    if (
        all(x == data_a[0] for x in data_a)
        and all(x == data_b[0] for x in data_b)
        and data_a[0] == data_b[0]
    ):
        return SignificanceTest(
            test_name="mann-whitney",
            statistic=0.0,
            p_value=1.0,
            is_significant=False,
        )

    result = stats.mannwhitneyu(data_a, data_b, alternative="two-sided")
    p_value = float(result.pvalue)

    return SignificanceTest(
        test_name="mann-whitney",
        statistic=float(result.statistic),
        p_value=p_value,
        is_significant=p_value < significance_level,
    )


def _determine_confidence(
    ttest: SignificanceTest,
    mann_whitney: SignificanceTest,
    effect_size: EffectSize,
) -> str:
    """Determine confidence level in the comparison result.

    Confidence levels are determined by combining statistical significance
    (p-values) with practical significance (effect size):

    - "high": Both parametric and non-parametric tests agree at high
      significance (p < 0.001), OR both are significant with at least
      medium effect size (Cohen's d >= 0.5)
    - "medium": At least one test is significant with practical effect
      size (small or larger), OR both tests are significant (p < 0.05)
    - "low": Insufficient statistical evidence for a reliable recommendation

    Args:
        ttest: T-test results.
        mann_whitney: Mann-Whitney U test results.
        effect_size: Cohen's d effect size.

    Returns:
        Confidence level: "high", "medium", or "low".
    """
    # Both tests highly significant (p < 0.001) - high confidence even without effect size
    # This handles the edge case where variance is 0 but means clearly differ
    if (
        ttest.is_significant
        and mann_whitney.is_significant
        and ttest.p_value < 0.001
        and mann_whitney.p_value < 0.001
    ):
        return "high"

    # Both tests significant with at least medium effect
    if (
        ttest.is_significant
        and mann_whitney.is_significant
        and effect_size.interpretation in ("medium", "large")
    ):
        return "high"

    # At least one test significant with at least small effect
    if (
        ttest.is_significant or mann_whitney.is_significant
    ) and effect_size.interpretation in (
        "small",
        "medium",
        "large",
    ):
        return "medium"

    # Both tests significant (p < 0.05) - medium confidence
    if ttest.is_significant and mann_whitney.is_significant:
        return "medium"

    return "low"


def _extract_metrics(
    results: list[SessionResult],
) -> tuple[tuple[float, ...], int, float, int]:
    """Extract all needed metrics from session results in a single pass.

    Args:
        results: List of SessionResult to extract metrics from.

    Returns:
        Tuple of (profits, winning_count, total_profit, total_hands).
    """
    profits: list[float] = []
    winning_count = 0
    total_profit = 0.0
    total_hands = 0

    for r in results:
        profits.append(r.session_profit)
        if r.session_profit > 0:
            winning_count += 1
        total_profit += r.session_profit
        total_hands += r.hands_played

    return tuple(profits), winning_count, total_profit, total_hands


def compare_strategies(
    results_a: list[SessionResult],
    results_b: list[SessionResult],
    name_a: str,
    name_b: str,
    significance_level: float = 0.05,
) -> StrategyComparison:
    """Compare two strategies using statistical tests.

    Performs comprehensive comparison including:
    - Session win rate comparison
    - Expected value per hand comparison
    - Two-sample t-test on session profits
    - Mann-Whitney U test on session profits
    - Cohen's d effect size calculation

    Args:
        results_a: List of SessionResult for strategy A.
        results_b: List of SessionResult for strategy B.
        name_a: Name for strategy A.
        name_b: Name for strategy B.
        significance_level: P-value threshold for significance (default 0.05).

    Returns:
        StrategyComparison with complete comparison results.

    Raises:
        ValueError: If either results list is empty or significance_level invalid.
    """
    if not results_a:
        raise ValueError("results_a cannot be empty")
    if not results_b:
        raise ValueError("results_b cannot be empty")
    if not 0 < significance_level < 1:
        raise ValueError(
            f"significance_level must be between 0 and 1, got {significance_level}"
        )

    # Extract all metrics in single pass per results list
    profits_a, winning_a, total_profit_a, total_hands_a = _extract_metrics(results_a)
    profits_b, winning_b, total_profit_b, total_hands_b = _extract_metrics(results_b)

    # Calculate basic metrics
    n_a = len(results_a)
    n_b = len(results_b)

    win_rate_a = winning_a / n_a
    win_rate_b = winning_b / n_b
    win_rate_diff = win_rate_a - win_rate_b

    # Calculate EV per hand
    ev_a = total_profit_a / total_hands_a if total_hands_a > 0 else 0.0
    ev_b = total_profit_b / total_hands_b if total_hands_b > 0 else 0.0

    ev_diff = ev_a - ev_b
    ev_pct_diff = (
        (ev_diff / abs(ev_b) * 100)
        if not math.isclose(ev_b, 0.0, abs_tol=1e-10)
        else None
    )

    # Calculate profit statistics
    profit_mean_a = mean(profits_a)
    profit_mean_b = mean(profits_b)
    profit_std_a = stdev(profits_a) if n_a > 1 else 0.0
    profit_std_b = stdev(profits_b) if n_b > 1 else 0.0

    # Perform statistical tests
    ttest = _perform_ttest(profits_a, profits_b, significance_level)
    mann_whitney = _perform_mannwhitney(profits_a, profits_b, significance_level)
    effect_size = _calculate_cohens_d(profits_a, profits_b)

    # Determine better strategy
    confidence = _determine_confidence(ttest, mann_whitney, effect_size)

    if confidence in ("high", "medium"):
        better_strategy = name_a if profit_mean_a > profit_mean_b else name_b
    else:
        better_strategy = None

    return StrategyComparison(
        strategy_a_name=name_a,
        strategy_b_name=name_b,
        sessions_a=n_a,
        sessions_b=n_b,
        win_rate_a=win_rate_a,
        win_rate_b=win_rate_b,
        win_rate_diff=win_rate_diff,
        ev_a=ev_a,
        ev_b=ev_b,
        ev_diff=ev_diff,
        ev_pct_diff=ev_pct_diff,
        profit_mean_a=profit_mean_a,
        profit_mean_b=profit_mean_b,
        profit_std_a=profit_std_a,
        profit_std_b=profit_std_b,
        ttest=ttest,
        mann_whitney=mann_whitney,
        effect_size=effect_size,
        better_strategy=better_strategy,
        confidence=confidence,
    )


def compare_multiple_strategies(
    results_dict: dict[str, list[SessionResult]],
    significance_level: float = 0.05,
) -> list[StrategyComparison]:
    """Compare multiple strategies pairwise.

    Generates comparisons between all pairs of strategies.

    Args:
        results_dict: Dictionary mapping strategy names to their SessionResult lists.
        significance_level: P-value threshold for significance (default 0.05).

    Returns:
        List of StrategyComparison for each pair of strategies.

    Raises:
        ValueError: If fewer than 2 strategies provided or any results list is empty.
    """
    strategy_names = list(results_dict.keys())

    if len(strategy_names) < 2:
        raise ValueError("At least 2 strategies required for comparison")

    for name, results in results_dict.items():
        if not results:
            raise ValueError(f"Results for strategy '{name}' cannot be empty")

    comparisons: list[StrategyComparison] = []

    for i, name_a in enumerate(strategy_names):
        for name_b in strategy_names[i + 1 :]:
            comparison = compare_strategies(
                results_a=results_dict[name_a],
                results_b=results_dict[name_b],
                name_a=name_a,
                name_b=name_b,
                significance_level=significance_level,
            )
            comparisons.append(comparison)

    return comparisons


def format_comparison_report(comparison: StrategyComparison) -> str:
    """Generate a human-readable comparison report.

    Args:
        comparison: StrategyComparison to format.

    Returns:
        Formatted string report.
    """
    lines = [
        f"Strategy Comparison: {comparison.strategy_a_name} vs {comparison.strategy_b_name}",
        "=" * REPORT_SEPARATOR_WIDTH,
        "",
        "Sample Sizes:",
        f"  {comparison.strategy_a_name}: {comparison.sessions_a} sessions",
        f"  {comparison.strategy_b_name}: {comparison.sessions_b} sessions",
        "",
        "Win Rates:",
        f"  {comparison.strategy_a_name}: {comparison.win_rate_a:.1%}",
        f"  {comparison.strategy_b_name}: {comparison.win_rate_b:.1%}",
        f"  Difference: {comparison.win_rate_diff:+.1%}",
        "",
        "Expected Value per Hand:",
        f"  {comparison.strategy_a_name}: ${comparison.ev_a:.4f}",
        f"  {comparison.strategy_b_name}: ${comparison.ev_b:.4f}",
        f"  Difference: ${comparison.ev_diff:+.4f}",
    ]

    if comparison.ev_pct_diff is not None:
        lines.append(f"  Relative Difference: {comparison.ev_pct_diff:+.1f}%")

    lines.extend(
        [
            "",
            "Session Profit Statistics:",
            f"  {comparison.strategy_a_name}: "
            f"mean=${comparison.profit_mean_a:.2f}, std=${comparison.profit_std_a:.2f}",
            f"  {comparison.strategy_b_name}: "
            f"mean=${comparison.profit_mean_b:.2f}, std=${comparison.profit_std_b:.2f}",
            "",
            "Statistical Tests:",
            f"  T-test: t={comparison.ttest.statistic:.3f}, "
            f"p={comparison.ttest.p_value:.4f} "
            f"({'significant' if comparison.ttest.is_significant else 'not significant'})",
            f"  Mann-Whitney U: U={comparison.mann_whitney.statistic:.1f}, "
            f"p={comparison.mann_whitney.p_value:.4f} "
            f"({'significant' if comparison.mann_whitney.is_significant else 'not significant'})",
            "",
            "Effect Size:",
            f"  Cohen's d: {comparison.effect_size.cohens_d:.3f} "
            f"({comparison.effect_size.interpretation})",
            "",
            "Conclusion:",
        ]
    )

    if comparison.better_strategy:
        lines.append(
            f"  {comparison.better_strategy} appears to be the better strategy "
            f"(confidence: {comparison.confidence})"
        )
    else:
        lines.append("  No statistically significant difference detected")

    return "\n".join(lines)
