"""Core statistics calculator for simulation results.

This module calculates detailed statistics from simulation results:
- Session win rate with confidence interval
- Expected value per hand with confidence interval
- Distribution statistics (variance, skewness, kurtosis)
- Percentile calculations
- Risk metrics (probability of specific loss levels)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import mean, quantiles, stdev, variance
from typing import TYPE_CHECKING

from scipy import stats

from let_it_ride.analytics.validation import calculate_wilson_confidence_interval

if TYPE_CHECKING:
    from let_it_ride.simulation.aggregation import AggregateStatistics
    from let_it_ride.simulation.session import SessionResult


# Default percentiles to calculate
DEFAULT_PERCENTILES: tuple[int, ...] = (5, 25, 50, 75, 95)


@dataclass(frozen=True, slots=True)
class ConfidenceInterval:
    """Confidence interval for a statistic.

    Attributes:
        lower: Lower bound of the interval.
        upper: Upper bound of the interval.
        level: Confidence level (e.g., 0.95 for 95% CI).
    """

    lower: float
    upper: float
    level: float


@dataclass(frozen=True, slots=True)
class DistributionStats:
    """Descriptive statistics for a distribution.

    Attributes:
        mean: Arithmetic mean.
        std: Standard deviation (sample).
        variance: Variance (sample).
        skewness: Fisher-Pearson skewness coefficient.
        kurtosis: Excess kurtosis (Fisher's definition).
        min: Minimum value.
        max: Maximum value.
        percentiles: Dictionary mapping percentile (int) to value.
        iqr: Interquartile range (75th - 25th percentile).
    """

    mean: float
    std: float
    variance: float
    skewness: float
    kurtosis: float
    min: float
    max: float
    percentiles: dict[int, float]
    iqr: float


@dataclass(frozen=True, slots=True)
class RiskMetrics:
    """Risk-related metrics for session outcomes.

    Attributes:
        prob_any_loss: Probability of any loss (profit < 0).
        prob_loss_50pct: Probability of losing 50%+ of starting bankroll.
        prob_loss_100pct: Probability of losing entire bankroll (ruin).
        max_drawdown_mean: Mean maximum drawdown across sessions.
        max_drawdown_std: Standard deviation of maximum drawdowns.
    """

    prob_any_loss: float
    prob_loss_50pct: float
    prob_loss_100pct: float
    max_drawdown_mean: float
    max_drawdown_std: float


@dataclass(frozen=True, slots=True)
class DetailedStatistics:
    """Complete detailed statistics for simulation results.

    Attributes:
        session_win_rate: Fraction of sessions with positive profit.
        session_win_rate_ci: Confidence interval for session win rate.
        ev_per_hand: Expected value (profit) per hand.
        ev_per_hand_ci: Confidence interval for EV per hand.
        session_profit_distribution: Distribution statistics for session profits.
        main_game_ev: Expected value per hand for main game only.
        bonus_ev: Expected value per hand for bonus bets.
        risk_metrics: Risk-related metrics.
        total_sessions: Total number of sessions analyzed.
        total_hands: Total number of hands played.
    """

    session_win_rate: float
    session_win_rate_ci: ConfidenceInterval
    ev_per_hand: float
    ev_per_hand_ci: ConfidenceInterval
    session_profit_distribution: DistributionStats
    main_game_ev: float
    bonus_ev: float
    risk_metrics: RiskMetrics
    total_sessions: int
    total_hands: int


def _calculate_skewness(
    data: tuple[float, ...], data_mean: float, data_std: float
) -> float:
    """Calculate Fisher-Pearson skewness coefficient.

    Uses the adjusted Fisher-Pearson standardized moment coefficient:
    g1 = (n / ((n-1)(n-2))) * sum((xi - mean)^3) / std^3

    Args:
        data: Tuple of values.
        data_mean: Pre-calculated mean of data.
        data_std: Pre-calculated sample standard deviation of data.

    Returns:
        Skewness coefficient. Positive = right skewed, negative = left skewed.
    """
    n = len(data)
    if n < 3:
        return 0.0
    if data_std == 0:
        return 0.0

    sum_cubed = sum((x - data_mean) ** 3 for x in data)
    adjustment = n / ((n - 1) * (n - 2))
    return adjustment * sum_cubed / (data_std**3)


def _calculate_kurtosis(
    data: tuple[float, ...], data_mean: float, data_std: float
) -> float:
    """Calculate excess kurtosis (Fisher's definition).

    Uses the adjusted formula for sample excess kurtosis:
    g2 = ((n(n+1)) / ((n-1)(n-2)(n-3))) * sum((xi - mean)^4) / std^4
         - 3*(n-1)^2 / ((n-2)(n-3))

    Args:
        data: Tuple of values.
        data_mean: Pre-calculated mean of data.
        data_std: Pre-calculated sample standard deviation of data.

    Returns:
        Excess kurtosis. Normal distribution has excess kurtosis of 0.
        Positive = heavy tails (leptokurtic), negative = light tails (platykurtic).
    """
    n = len(data)
    if n < 4:
        return 0.0
    if data_std == 0:
        return 0.0

    sum_fourth = sum((x - data_mean) ** 4 for x in data)
    term1 = (n * (n + 1)) / ((n - 1) * (n - 2) * (n - 3))
    term2 = sum_fourth / (data_std**4)
    term3 = (3 * (n - 1) ** 2) / ((n - 2) * (n - 3))

    return term1 * term2 - term3


def _calculate_percentiles(
    data: tuple[float, ...], percentile_list: tuple[int, ...] = DEFAULT_PERCENTILES
) -> dict[int, float]:
    """Calculate specified percentiles from data.

    Args:
        data: Tuple of values (must have at least 2 elements).
        percentile_list: Tuple of percentiles to calculate (0-100).

    Returns:
        Dictionary mapping percentile to value.
    """
    if len(data) < 2:
        # With 1 element, all percentiles are that value
        if len(data) == 1:
            return {p: data[0] for p in percentile_list}
        return {p: 0.0 for p in percentile_list}

    # Use statistics.quantiles which returns n-1 cut points for n groups
    # For percentiles, we need 100 groups (99 cut points)
    all_quantiles = quantiles(data, n=100)

    result: dict[int, float] = {}
    for p in percentile_list:
        if p == 0:
            result[p] = min(data)
        elif p == 100:
            result[p] = max(data)
        else:
            # quantiles returns 99 values for n=100
            # Index 0 = 1st percentile, index 4 = 5th percentile, etc.
            result[p] = all_quantiles[p - 1]

    return result


def _calculate_distribution_stats(
    data: tuple[float, ...], percentile_list: tuple[int, ...] = DEFAULT_PERCENTILES
) -> DistributionStats:
    """Calculate distribution statistics for a dataset.

    Args:
        data: Tuple of values.
        percentile_list: Tuple of percentiles to calculate.

    Returns:
        DistributionStats with all computed statistics.

    Raises:
        ValueError: If data is empty.
    """
    if not data:
        raise ValueError("Cannot calculate distribution statistics for empty data")

    data_mean = mean(data)
    data_variance = variance(data) if len(data) > 1 else 0.0
    data_std = stdev(data) if len(data) > 1 else 0.0

    percentiles = _calculate_percentiles(data, percentile_list)

    # Calculate IQR
    p25 = percentiles.get(25, 0.0)
    p75 = percentiles.get(75, 0.0)
    iqr = p75 - p25

    return DistributionStats(
        mean=data_mean,
        std=data_std,
        variance=data_variance,
        skewness=_calculate_skewness(data, data_mean, data_std),
        kurtosis=_calculate_kurtosis(data, data_mean, data_std),
        min=min(data),
        max=max(data),
        percentiles=percentiles,
        iqr=iqr,
    )


def _calculate_mean_confidence_interval(
    data: tuple[float, ...], confidence_level: float = 0.95
) -> ConfidenceInterval:
    """Calculate confidence interval for the mean using t-distribution.

    CI = mean +/- t(a/2, n-1) * (std / sqrt(n))

    Args:
        data: Tuple of values.
        confidence_level: Confidence level (default 0.95 for 95% CI).

    Returns:
        ConfidenceInterval for the mean.
    """
    n = len(data)
    if n < 2:
        # With insufficient data, return point estimate with no interval
        value = data[0] if n == 1 else 0.0
        return ConfidenceInterval(lower=value, upper=value, level=confidence_level)

    data_mean = mean(data)
    data_std = stdev(data)

    # Get t critical value for two-tailed test
    alpha = 1 - confidence_level
    t_critical = stats.t.ppf(1 - alpha / 2, df=n - 1)

    margin = t_critical * (data_std / math.sqrt(n))

    return ConfidenceInterval(
        lower=data_mean - margin, upper=data_mean + margin, level=confidence_level
    )


def _calculate_risk_metrics(
    session_results: list[SessionResult] | None = None,
    session_profits: tuple[float, ...] | None = None,
    starting_bankroll: float = 0.0,
) -> RiskMetrics:
    """Calculate risk-related metrics from session results.

    Args:
        session_results: List of SessionResult objects (preferred if available).
        session_profits: Tuple of session profits (used if session_results not provided).
        starting_bankroll: Starting bankroll for loss percentage calculations.

    Returns:
        RiskMetrics with calculated risk statistics.
    """
    if session_results is not None:
        profits = tuple(r.session_profit for r in session_results)
        drawdowns = tuple(r.max_drawdown for r in session_results)
        # Get starting bankroll from first result if not provided
        if starting_bankroll == 0.0 and session_results:
            starting_bankroll = session_results[0].starting_bankroll
    elif session_profits is not None:
        profits = session_profits
        drawdowns = ()  # Not available without SessionResult
    else:
        return RiskMetrics(
            prob_any_loss=0.0,
            prob_loss_50pct=0.0,
            prob_loss_100pct=0.0,
            max_drawdown_mean=0.0,
            max_drawdown_std=0.0,
        )

    n = len(profits)
    if n == 0:
        return RiskMetrics(
            prob_any_loss=0.0,
            prob_loss_50pct=0.0,
            prob_loss_100pct=0.0,
            max_drawdown_mean=0.0,
            max_drawdown_std=0.0,
        )

    # Probability of any loss
    losses = sum(1 for p in profits if p < 0)
    prob_any_loss = losses / n

    # Probability of losing 50% or more of starting bankroll
    if starting_bankroll > 0:
        loss_50pct_threshold = -0.5 * starting_bankroll
        loss_100pct_threshold = -starting_bankroll
        prob_loss_50pct = sum(1 for p in profits if p <= loss_50pct_threshold) / n
        prob_loss_100pct = sum(1 for p in profits if p <= loss_100pct_threshold) / n
    else:
        prob_loss_50pct = 0.0
        prob_loss_100pct = 0.0

    # Max drawdown statistics
    if drawdowns:
        max_drawdown_mean = mean(drawdowns)
        max_drawdown_std = stdev(drawdowns) if len(drawdowns) > 1 else 0.0
    else:
        max_drawdown_mean = 0.0
        max_drawdown_std = 0.0

    return RiskMetrics(
        prob_any_loss=prob_any_loss,
        prob_loss_50pct=prob_loss_50pct,
        prob_loss_100pct=prob_loss_100pct,
        max_drawdown_mean=max_drawdown_mean,
        max_drawdown_std=max_drawdown_std,
    )


def calculate_statistics(
    aggregate_stats: AggregateStatistics,
    session_results: list[SessionResult] | None = None,
    confidence_level: float = 0.95,
) -> DetailedStatistics:
    """Calculate detailed statistics from simulation results.

    This is the main entry point for statistics calculation. It takes
    aggregate statistics and optionally raw session results to compute
    comprehensive statistics including confidence intervals, distribution
    metrics, and risk analysis.

    Args:
        aggregate_stats: Aggregate statistics from simulation.
        session_results: Optional list of SessionResult for additional metrics.
            If provided, enables risk metric calculations with drawdown data.
        confidence_level: Confidence level for intervals (default 0.95).

    Returns:
        DetailedStatistics with all computed metrics.

    Raises:
        ValueError: If aggregate_stats has no sessions.
    """
    if aggregate_stats.total_sessions <= 0:
        raise ValueError("Cannot calculate statistics with zero sessions")

    # Session win rate with Wilson CI
    win_rate_ci_tuple = calculate_wilson_confidence_interval(
        successes=aggregate_stats.winning_sessions,
        total=aggregate_stats.total_sessions,
        confidence_level=confidence_level,
    )
    session_win_rate_ci = ConfidenceInterval(
        lower=win_rate_ci_tuple[0],
        upper=win_rate_ci_tuple[1],
        level=confidence_level,
    )

    # Session profit distribution
    session_profits = aggregate_stats.session_profits
    if not session_profits:
        raise ValueError("No session profit data available for statistics calculation")

    session_profit_distribution = _calculate_distribution_stats(session_profits)

    # EV per hand confidence interval
    # Calculate per-session EV values for CI estimation
    if session_results:
        per_session_evs = tuple(
            r.session_profit / r.hands_played if r.hands_played > 0 else 0.0
            for r in session_results
        )
        ev_ci = _calculate_mean_confidence_interval(per_session_evs, confidence_level)
    else:
        # Without per-session data, use session profits as proxy
        # This is less accurate but still provides useful bounds
        ev_ci = _calculate_mean_confidence_interval(session_profits, confidence_level)
        # Scale by average hands per session
        avg_hands = aggregate_stats.total_hands / aggregate_stats.total_sessions
        if avg_hands > 0:
            ev_ci = ConfidenceInterval(
                lower=ev_ci.lower / avg_hands,
                upper=ev_ci.upper / avg_hands,
                level=confidence_level,
            )

    # Risk metrics
    starting_bankroll = session_results[0].starting_bankroll if session_results else 0.0
    risk_metrics = _calculate_risk_metrics(
        session_results=session_results,
        session_profits=session_profits,
        starting_bankroll=starting_bankroll,
    )

    return DetailedStatistics(
        session_win_rate=aggregate_stats.session_win_rate,
        session_win_rate_ci=session_win_rate_ci,
        ev_per_hand=aggregate_stats.expected_value_per_hand,
        ev_per_hand_ci=ev_ci,
        session_profit_distribution=session_profit_distribution,
        main_game_ev=aggregate_stats.main_ev_per_hand,
        bonus_ev=aggregate_stats.bonus_ev_per_hand,
        risk_metrics=risk_metrics,
        total_sessions=aggregate_stats.total_sessions,
        total_hands=aggregate_stats.total_hands,
    )


def calculate_statistics_from_results(
    results: list[SessionResult],
    confidence_level: float = 0.95,
) -> DetailedStatistics:
    """Calculate detailed statistics directly from session results.

    Convenience function that aggregates results and calculates statistics
    in one step. This is useful when you have raw SessionResult objects
    and want comprehensive statistics.

    Args:
        results: List of SessionResult objects.
        confidence_level: Confidence level for intervals (default 0.95).

    Returns:
        DetailedStatistics with all computed metrics.

    Raises:
        ValueError: If results list is empty.
    """
    from let_it_ride.simulation.aggregation import aggregate_results

    if not results:
        raise ValueError("Cannot calculate statistics from empty results list")

    aggregate_stats = aggregate_results(results)
    return calculate_statistics(
        aggregate_stats=aggregate_stats,
        session_results=results,
        confidence_level=confidence_level,
    )
