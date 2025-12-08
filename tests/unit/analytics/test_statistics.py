"""Unit tests for core statistics calculator module."""

from __future__ import annotations

import math

import pytest

from let_it_ride.analytics.statistics import (
    DEFAULT_PERCENTILES,
    ConfidenceInterval,
    DetailedStatistics,
    DistributionStats,
    _calculate_distribution_stats,
    _calculate_kurtosis,
    _calculate_mean_confidence_interval,
    _calculate_percentiles,
    _calculate_risk_metrics,
    _calculate_skewness,
    calculate_statistics,
    calculate_statistics_from_results,
)
from let_it_ride.simulation.aggregation import AggregateStatistics
from let_it_ride.simulation.session import SessionOutcome, SessionResult, StopReason


def create_aggregate_statistics(
    *,
    total_sessions: int = 100,
    winning_sessions: int = 30,
    losing_sessions: int = 65,
    push_sessions: int = 5,
    total_hands: int = 10000,
    total_wagered: float = 30000.0,
    net_result: float = -1050.0,
    session_profits: tuple[float, ...] | None = None,
) -> AggregateStatistics:
    """Create AggregateStatistics with sensible defaults for testing."""
    session_win_rate = winning_sessions / total_sessions if total_sessions > 0 else 0.0
    expected_value_per_hand = net_result / total_hands if total_hands > 0 else 0.0
    total_won = net_result + total_wagered

    if session_profits is None:
        # Generate varied profits for realistic testing
        session_profits = tuple([net_result / total_sessions] * total_sessions)

    from statistics import mean, median, stdev

    session_profit_mean = mean(session_profits) if session_profits else 0.0
    session_profit_std = stdev(session_profits) if len(session_profits) > 1 else 0.0
    session_profit_median = median(session_profits) if session_profits else 0.0
    session_profit_min = min(session_profits) if session_profits else 0.0
    session_profit_max = max(session_profits) if session_profits else 0.0

    return AggregateStatistics(
        total_sessions=total_sessions,
        winning_sessions=winning_sessions,
        losing_sessions=losing_sessions,
        push_sessions=push_sessions,
        session_win_rate=session_win_rate,
        total_hands=total_hands,
        total_wagered=total_wagered,
        total_won=total_won,
        net_result=net_result,
        expected_value_per_hand=expected_value_per_hand,
        main_wagered=total_wagered,
        main_won=total_won,
        main_ev_per_hand=expected_value_per_hand,
        bonus_wagered=0.0,
        bonus_won=0.0,
        bonus_ev_per_hand=0.0,
        hand_frequencies={},
        hand_frequency_pct={},
        session_profit_mean=session_profit_mean,
        session_profit_std=session_profit_std,
        session_profit_median=session_profit_median,
        session_profit_min=session_profit_min,
        session_profit_max=session_profit_max,
        session_profits=session_profits,
    )


def create_session_result(
    *,
    outcome: SessionOutcome = SessionOutcome.LOSS,
    stop_reason: StopReason = StopReason.MAX_HANDS,
    hands_played: int = 100,
    starting_bankroll: float = 1000.0,
    final_bankroll: float = 950.0,
    session_profit: float = -50.0,
    total_wagered: float = 300.0,
    total_bonus_wagered: float = 0.0,
    peak_bankroll: float = 1050.0,
    max_drawdown: float = 100.0,
    max_drawdown_pct: float = 0.0952,
) -> SessionResult:
    """Create SessionResult with sensible defaults for testing."""
    return SessionResult(
        outcome=outcome,
        stop_reason=stop_reason,
        hands_played=hands_played,
        starting_bankroll=starting_bankroll,
        final_bankroll=final_bankroll,
        session_profit=session_profit,
        total_wagered=total_wagered,
        total_bonus_wagered=total_bonus_wagered,
        peak_bankroll=peak_bankroll,
        max_drawdown=max_drawdown,
        max_drawdown_pct=max_drawdown_pct,
    )


class TestConfidenceIntervalDataclass:
    """Tests for ConfidenceInterval dataclass."""

    def test_create_confidence_interval(self) -> None:
        """Should create confidence interval with all fields."""
        ci = ConfidenceInterval(lower=0.25, upper=0.35, level=0.95)
        assert ci.lower == 0.25
        assert ci.upper == 0.35
        assert ci.level == 0.95

    def test_confidence_interval_is_frozen(self) -> None:
        """ConfidenceInterval should be immutable."""
        ci = ConfidenceInterval(lower=0.1, upper=0.2, level=0.95)
        with pytest.raises(AttributeError):
            ci.lower = 0.15  # type: ignore[misc]


class TestDistributionStatsDataclass:
    """Tests for DistributionStats dataclass."""

    def test_create_distribution_stats(self) -> None:
        """Should create distribution stats with all fields."""
        stats = DistributionStats(
            mean=100.0,
            std=25.0,
            variance=625.0,
            skewness=0.5,
            kurtosis=0.2,
            min=-50.0,
            max=250.0,
            percentiles={5: 50, 25: 75, 50: 100, 75: 125, 95: 150},
            iqr=50.0,
        )
        assert stats.mean == 100.0
        assert stats.std == 25.0
        assert stats.iqr == 50.0

    def test_distribution_stats_is_frozen(self) -> None:
        """DistributionStats should be immutable."""
        stats = DistributionStats(
            mean=0.0,
            std=1.0,
            variance=1.0,
            skewness=0.0,
            kurtosis=0.0,
            min=-5.0,
            max=5.0,
            percentiles={},
            iqr=1.0,
        )
        with pytest.raises(AttributeError):
            stats.mean = 1.0  # type: ignore[misc]


class TestSkewnessCalculation:
    """Tests for skewness calculation."""

    def test_symmetric_data_zero_skewness(self) -> None:
        """Symmetric data should have skewness near zero."""
        # Symmetric data around 0
        data = (-3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0)
        from statistics import mean, stdev

        data_mean = mean(data)
        data_std = stdev(data)
        skewness = _calculate_skewness(data, data_mean, data_std)
        assert abs(skewness) < 0.01

    def test_right_skewed_data_positive_skewness(self) -> None:
        """Right-skewed data should have positive skewness."""
        # Most values small, few large values
        data = (1.0, 2.0, 2.0, 3.0, 3.0, 3.0, 10.0, 20.0)
        from statistics import mean, stdev

        data_mean = mean(data)
        data_std = stdev(data)
        skewness = _calculate_skewness(data, data_mean, data_std)
        assert skewness > 0.5  # Definitely positive

    def test_left_skewed_data_negative_skewness(self) -> None:
        """Left-skewed data should have negative skewness."""
        # Most values large, few small values
        data = (1.0, 10.0, 17.0, 18.0, 18.0, 19.0, 19.0, 20.0)
        from statistics import mean, stdev

        data_mean = mean(data)
        data_std = stdev(data)
        skewness = _calculate_skewness(data, data_mean, data_std)
        assert skewness < -0.5  # Definitely negative

    def test_insufficient_data_returns_zero(self) -> None:
        """Less than 3 data points should return 0."""
        data = (1.0, 2.0)
        skewness = _calculate_skewness(data, 1.5, 0.707)
        assert skewness == 0.0

    def test_zero_std_returns_zero(self) -> None:
        """Zero standard deviation should return 0."""
        data = (5.0, 5.0, 5.0, 5.0, 5.0)
        skewness = _calculate_skewness(data, 5.0, 0.0)
        assert skewness == 0.0


class TestKurtosisCalculation:
    """Tests for kurtosis calculation."""

    def test_normal_like_data_near_zero_kurtosis(self) -> None:
        """Approximately normal data should have kurtosis near zero."""
        # Use a moderately sized sample from normal-like distribution
        # These values are chosen to approximate normal
        data = (
            -2.5,
            -1.8,
            -1.2,
            -0.8,
            -0.4,
            0.0,
            0.4,
            0.8,
            1.2,
            1.8,
            2.5,
        )
        from statistics import mean, stdev

        data_mean = mean(data)
        data_std = stdev(data)
        kurtosis = _calculate_kurtosis(data, data_mean, data_std)
        # Normal distribution has excess kurtosis of 0
        assert abs(kurtosis) < 1.5  # Reasonable range

    def test_heavy_tailed_positive_kurtosis(self) -> None:
        """Data with outliers should have positive excess kurtosis."""
        # Mostly clustered with extreme outliers
        data = (0.0, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 5.0, -5.0)
        from statistics import mean, stdev

        data_mean = mean(data)
        data_std = stdev(data)
        kurtosis = _calculate_kurtosis(data, data_mean, data_std)
        assert kurtosis > 0  # Leptokurtic (heavy tails)

    def test_insufficient_data_returns_zero(self) -> None:
        """Less than 4 data points should return 0."""
        data = (1.0, 2.0, 3.0)
        kurtosis = _calculate_kurtosis(data, 2.0, 1.0)
        assert kurtosis == 0.0

    def test_zero_std_returns_zero(self) -> None:
        """Zero standard deviation should return 0."""
        data = (5.0, 5.0, 5.0, 5.0, 5.0)
        kurtosis = _calculate_kurtosis(data, 5.0, 0.0)
        assert kurtosis == 0.0


class TestPercentileCalculation:
    """Tests for percentile calculation."""

    def test_default_percentiles(self) -> None:
        """Should calculate default percentiles (5, 25, 50, 75, 95)."""
        assert DEFAULT_PERCENTILES == (5, 25, 50, 75, 95)

    def test_ordered_data_percentiles(self) -> None:
        """Percentiles on ordered data should be accurate."""
        # 101 values from 0 to 100
        data = tuple(range(101))
        percentiles = _calculate_percentiles(tuple(float(x) for x in data))

        # With 101 values, percentiles should be approximately the value
        assert abs(percentiles[5] - 5.0) <= 1.0
        assert abs(percentiles[25] - 25.0) <= 1.0
        assert abs(percentiles[50] - 50.0) <= 1.0
        assert abs(percentiles[75] - 75.0) <= 1.0
        assert abs(percentiles[95] - 95.0) <= 1.0

    def test_single_value_all_same(self) -> None:
        """Single value should return that value for all percentiles."""
        data = (42.0,)
        percentiles = _calculate_percentiles(data)

        for p in DEFAULT_PERCENTILES:
            assert percentiles[p] == 42.0

    def test_two_values(self) -> None:
        """Two values should still calculate percentiles."""
        data = (10.0, 20.0)
        percentiles = _calculate_percentiles(data)

        # Should have all default percentiles
        assert len(percentiles) == len(DEFAULT_PERCENTILES)

    def test_custom_percentiles(self) -> None:
        """Should support custom percentile list."""
        data = tuple(float(x) for x in range(101))
        custom = (10, 90)
        percentiles = _calculate_percentiles(data, custom)

        assert 10 in percentiles
        assert 90 in percentiles
        assert 50 not in percentiles

    def test_empty_data(self) -> None:
        """Empty data should return zeros."""
        data: tuple[float, ...] = ()
        percentiles = _calculate_percentiles(data)

        for p in DEFAULT_PERCENTILES:
            assert percentiles[p] == 0.0


class TestDistributionStats:
    """Tests for distribution statistics calculation."""

    def test_known_dataset(self) -> None:
        """Verify calculations against manually computed values."""
        # Simple dataset with known statistics
        data = (10.0, 20.0, 30.0, 40.0, 50.0)

        stats = _calculate_distribution_stats(data)

        assert stats.mean == 30.0
        assert abs(stats.variance - 250.0) < 0.01  # Sample variance
        assert abs(stats.std - 15.811) < 0.01  # sqrt(250)
        assert stats.min == 10.0
        assert stats.max == 50.0

    def test_single_value(self) -> None:
        """Single value should have zero variance."""
        data = (42.0,)
        stats = _calculate_distribution_stats(data)

        assert stats.mean == 42.0
        assert stats.variance == 0.0
        assert stats.std == 0.0
        assert stats.min == 42.0
        assert stats.max == 42.0

    def test_all_same_values(self) -> None:
        """All same values should have zero variance."""
        data = (100.0,) * 10
        stats = _calculate_distribution_stats(data)

        assert stats.mean == 100.0
        assert stats.variance == 0.0
        assert stats.std == 0.0
        assert stats.skewness == 0.0
        assert stats.kurtosis == 0.0

    def test_empty_data_raises_error(self) -> None:
        """Empty data should raise ValueError."""
        with pytest.raises(ValueError, match="Cannot calculate distribution"):
            _calculate_distribution_stats(())

    def test_iqr_calculation(self) -> None:
        """IQR should be 75th - 25th percentile."""
        # Uniform-ish data
        data = tuple(float(x) for x in range(101))
        stats = _calculate_distribution_stats(data)

        expected_iqr = stats.percentiles[75] - stats.percentiles[25]
        assert abs(stats.iqr - expected_iqr) < 0.01


class TestMeanConfidenceInterval:
    """Tests for mean confidence interval calculation."""

    def test_known_dataset_95_ci(self) -> None:
        """Verify CI calculation with known dataset."""
        # 10 values with mean=50, std~15.81
        data = tuple(float(x) for x in range(10, 100, 10))  # 10,20,...,90
        ci = _calculate_mean_confidence_interval(data, confidence_level=0.95)

        assert ci.level == 0.95
        # Mean should be in interval
        from statistics import mean

        data_mean = mean(data)
        assert ci.lower < data_mean < ci.upper

    def test_single_value_point_estimate(self) -> None:
        """Single value should give point estimate (lower == upper)."""
        data = (100.0,)
        ci = _calculate_mean_confidence_interval(data)

        assert ci.lower == 100.0
        assert ci.upper == 100.0

    def test_higher_confidence_wider_interval(self) -> None:
        """99% CI should be wider than 95% CI."""
        data = tuple(float(x) for x in range(1, 11))

        ci_95 = _calculate_mean_confidence_interval(data, confidence_level=0.95)
        ci_99 = _calculate_mean_confidence_interval(data, confidence_level=0.99)

        width_95 = ci_95.upper - ci_95.lower
        width_99 = ci_99.upper - ci_99.lower
        assert width_99 > width_95

    def test_more_data_narrower_interval(self) -> None:
        """More data points should give narrower interval (same std)."""
        # Use repeated values to maintain same standard deviation
        # but increase sample size
        base_values = [1.0, 2.0, 3.0, 4.0, 5.0]
        data_small = tuple(base_values)  # n=5
        data_large = tuple(base_values * 20)  # n=100, same distribution

        ci_small = _calculate_mean_confidence_interval(data_small)
        ci_large = _calculate_mean_confidence_interval(data_large)

        width_small = ci_small.upper - ci_small.lower
        width_large = ci_large.upper - ci_large.lower
        # With same std but more data, CI should be narrower
        assert width_large < width_small


class TestRiskMetrics:
    """Tests for risk metrics calculation."""

    def test_with_session_results(self) -> None:
        """Should calculate risk metrics from SessionResult objects."""
        results = [
            create_session_result(
                session_profit=-100.0,  # Loss
                max_drawdown=150.0,
                starting_bankroll=1000.0,
            ),
            create_session_result(
                outcome=SessionOutcome.WIN,
                session_profit=50.0,  # Win
                max_drawdown=50.0,
                starting_bankroll=1000.0,
            ),
            create_session_result(
                session_profit=-600.0,  # 60% loss
                max_drawdown=700.0,
                starting_bankroll=1000.0,
            ),
        ]

        risk = _calculate_risk_metrics(session_results=results)

        # 2 out of 3 sessions had losses
        assert abs(risk.prob_any_loss - 2 / 3) < 0.01

        # 1 out of 3 lost 50%+ (the -600 one)
        assert abs(risk.prob_loss_50pct - 1 / 3) < 0.01

        # No complete ruin
        assert risk.prob_loss_100pct == 0.0

        # Drawdown mean = (150 + 50 + 700) / 3
        expected_dd_mean = (150 + 50 + 700) / 3
        assert abs(risk.max_drawdown_mean - expected_dd_mean) < 0.01

    def test_with_session_profits_only(self) -> None:
        """Should calculate basic risk metrics from profits tuple."""
        profits = (-50.0, 100.0, -75.0, 25.0, -10.0)

        risk = _calculate_risk_metrics(
            session_profits=profits, starting_bankroll=1000.0
        )

        # 3 out of 5 are negative
        assert risk.prob_any_loss == 0.6

        # No drawdown data without SessionResult
        assert risk.max_drawdown_mean == 0.0
        assert risk.max_drawdown_std == 0.0

    def test_no_data_returns_zeros(self) -> None:
        """No data should return all zeros."""
        risk = _calculate_risk_metrics()

        assert risk.prob_any_loss == 0.0
        assert risk.prob_loss_50pct == 0.0
        assert risk.prob_loss_100pct == 0.0

    def test_all_wins_zero_loss_probability(self) -> None:
        """All winning sessions should have zero loss probability."""
        profits = (100.0, 50.0, 200.0, 75.0)
        risk = _calculate_risk_metrics(session_profits=profits)

        assert risk.prob_any_loss == 0.0


class TestCalculateStatistics:
    """Tests for main calculate_statistics function."""

    def test_basic_calculation(self) -> None:
        """Should calculate all statistics from aggregate data."""
        # Create varied session profits
        profits = (
            -100.0,
            -50.0,
            -25.0,
            0.0,
            25.0,
            50.0,
            75.0,
            100.0,
            150.0,
            200.0,
        )
        agg = create_aggregate_statistics(
            total_sessions=10,
            winning_sessions=6,
            losing_sessions=3,
            push_sessions=1,
            total_hands=1000,
            session_profits=profits,
        )

        stats = calculate_statistics(agg)

        assert isinstance(stats, DetailedStatistics)
        assert stats.total_sessions == 10
        assert stats.total_hands == 1000
        assert stats.session_win_rate == 0.6

    def test_includes_confidence_intervals(self) -> None:
        """Should include confidence intervals for win rate and EV."""
        agg = create_aggregate_statistics()
        stats = calculate_statistics(agg)

        assert isinstance(stats.session_win_rate_ci, ConfidenceInterval)
        assert stats.session_win_rate_ci.level == 0.95
        assert stats.session_win_rate_ci.lower < stats.session_win_rate_ci.upper

        assert isinstance(stats.ev_per_hand_ci, ConfidenceInterval)

    def test_includes_distribution_stats(self) -> None:
        """Should include distribution statistics."""
        profits = tuple(float(x) for x in range(-50, 51, 10))
        agg = create_aggregate_statistics(session_profits=profits)

        stats = calculate_statistics(agg)

        dist = stats.session_profit_distribution
        assert isinstance(dist, DistributionStats)
        assert 5 in dist.percentiles
        assert 95 in dist.percentiles

    def test_with_session_results_enables_risk_metrics(self) -> None:
        """Providing SessionResults should enable detailed risk metrics."""
        results = [
            create_session_result(
                session_profit=-50.0,
                max_drawdown=100.0,
            ),
            create_session_result(
                outcome=SessionOutcome.WIN,
                session_profit=100.0,
                max_drawdown=20.0,
            ),
        ]

        from let_it_ride.simulation.aggregation import aggregate_results

        agg = aggregate_results(results)
        stats = calculate_statistics(agg, session_results=results)

        assert stats.risk_metrics.max_drawdown_mean > 0

    def test_zero_sessions_raises_error(self) -> None:
        """Zero sessions should raise ValueError."""
        agg = create_aggregate_statistics(
            total_sessions=0,
            winning_sessions=0,
            losing_sessions=0,
            push_sessions=0,
            session_profits=(),
        )

        with pytest.raises(ValueError, match="zero sessions"):
            calculate_statistics(agg)

    def test_custom_confidence_level(self) -> None:
        """Should support custom confidence level."""
        agg = create_aggregate_statistics()

        stats_90 = calculate_statistics(agg, confidence_level=0.90)
        stats_99 = calculate_statistics(agg, confidence_level=0.99)

        assert stats_90.session_win_rate_ci.level == 0.90
        assert stats_99.session_win_rate_ci.level == 0.99

        # 99% CI should be wider than 90% CI
        width_90 = (
            stats_90.session_win_rate_ci.upper - stats_90.session_win_rate_ci.lower
        )
        width_99 = (
            stats_99.session_win_rate_ci.upper - stats_99.session_win_rate_ci.lower
        )
        assert width_99 > width_90


class TestCalculateStatisticsFromResults:
    """Tests for convenience function that aggregates and calculates."""

    def test_basic_usage(self) -> None:
        """Should aggregate results and calculate statistics."""
        results = [
            create_session_result(
                outcome=SessionOutcome.WIN,
                session_profit=100.0,
                hands_played=50,
            ),
            create_session_result(
                outcome=SessionOutcome.LOSS,
                session_profit=-50.0,
                hands_played=50,
            ),
        ]

        stats = calculate_statistics_from_results(results)

        assert stats.total_sessions == 2
        assert stats.total_hands == 100
        assert stats.session_win_rate == 0.5

    def test_empty_results_raises_error(self) -> None:
        """Empty results should raise ValueError."""
        with pytest.raises(ValueError, match="empty results"):
            calculate_statistics_from_results([])

    def test_single_result(self) -> None:
        """Single result should work correctly."""
        results = [create_session_result(session_profit=50.0, hands_played=100)]

        stats = calculate_statistics_from_results(results)

        assert stats.total_sessions == 1
        assert stats.total_hands == 100


class TestNumericalStability:
    """Tests for numerical stability with edge cases."""

    def test_very_large_values(self) -> None:
        """Should handle very large profit values."""
        profits = (1e9, 2e9, 1.5e9, 1.8e9, 2.2e9)
        agg = create_aggregate_statistics(
            total_sessions=5,
            winning_sessions=5,
            losing_sessions=0,
            push_sessions=0,
            session_profits=profits,
        )

        stats = calculate_statistics(agg)

        assert not math.isnan(stats.session_profit_distribution.mean)
        assert not math.isnan(stats.session_profit_distribution.std)
        assert not math.isnan(stats.session_profit_distribution.skewness)

    def test_very_small_values(self) -> None:
        """Should handle very small profit values."""
        profits = (1e-9, 2e-9, 1.5e-9, 1.8e-9, 2.2e-9)
        agg = create_aggregate_statistics(
            total_sessions=5,
            winning_sessions=5,
            losing_sessions=0,
            push_sessions=0,
            session_profits=profits,
        )

        stats = calculate_statistics(agg)

        assert not math.isnan(stats.session_profit_distribution.mean)
        assert not math.isnan(stats.session_profit_distribution.std)

    def test_mixed_positive_negative(self) -> None:
        """Should handle mixed positive and negative values."""
        profits = (-1000.0, 500.0, -200.0, 800.0, -100.0, 0.0)
        agg = create_aggregate_statistics(
            total_sessions=6,
            winning_sessions=2,
            losing_sessions=3,
            push_sessions=1,
            session_profits=profits,
        )

        stats = calculate_statistics(agg)

        assert not math.isnan(stats.session_profit_distribution.mean)
        dist = stats.session_profit_distribution
        assert dist.min == -1000.0
        assert dist.max == 800.0


class TestIntegrationWithAggregation:
    """Integration tests with the aggregation module."""

    def test_round_trip_from_session_results(self) -> None:
        """Should work correctly through full pipeline."""
        from let_it_ride.simulation.aggregation import aggregate_results

        # Create realistic session results
        results = [
            create_session_result(
                outcome=SessionOutcome.WIN,
                session_profit=150.0,
                hands_played=100,
                max_drawdown=50.0,
            ),
            create_session_result(
                outcome=SessionOutcome.LOSS,
                session_profit=-80.0,
                hands_played=100,
                max_drawdown=120.0,
            ),
            create_session_result(
                outcome=SessionOutcome.LOSS,
                session_profit=-40.0,
                hands_played=100,
                max_drawdown=70.0,
            ),
            create_session_result(
                outcome=SessionOutcome.WIN,
                session_profit=200.0,
                hands_played=100,
                max_drawdown=30.0,
            ),
            create_session_result(
                outcome=SessionOutcome.PUSH,
                session_profit=0.0,
                hands_played=100,
                max_drawdown=40.0,
            ),
        ]

        # Aggregate
        agg = aggregate_results(results)

        # Calculate statistics
        stats = calculate_statistics(agg, session_results=results)

        # Verify consistency
        assert stats.session_win_rate == agg.session_win_rate
        assert stats.ev_per_hand == agg.expected_value_per_hand
        assert stats.total_sessions == 5
        assert stats.total_hands == 500

        # Verify win rate CI contains observed rate
        assert stats.session_win_rate_ci.lower <= stats.session_win_rate
        assert stats.session_win_rate_ci.upper >= stats.session_win_rate

        # Verify distribution stats match
        assert stats.session_profit_distribution.mean == agg.session_profit_mean
        assert (
            abs(stats.session_profit_distribution.std - agg.session_profit_std) < 0.01
        )


class TestEmptySessionProfits:
    """Tests for empty session_profits edge case."""

    def test_empty_session_profits_raises_error(self) -> None:
        """Empty session_profits with positive total_sessions should raise ValueError."""
        agg = create_aggregate_statistics(
            total_sessions=10,
            winning_sessions=3,
            losing_sessions=7,
            push_sessions=0,
            session_profits=(),  # Empty tuple
        )

        with pytest.raises(ValueError, match="No session profit data"):
            calculate_statistics(agg)


class TestScipyReferenceValidation:
    """Tests validating skewness and kurtosis match scipy implementations."""

    def test_skewness_matches_scipy(self) -> None:
        """Verify skewness matches scipy.stats.skew with bias=False."""
        from statistics import mean as stats_mean
        from statistics import stdev

        from scipy import stats as scipy_stats

        # Right-skewed data
        data = (1.0, 2.0, 2.0, 3.0, 3.0, 3.0, 10.0, 20.0)
        data_mean = stats_mean(data)
        data_std = stdev(data)

        expected = scipy_stats.skew(data, bias=False)
        actual = _calculate_skewness(data, data_mean, data_std)

        assert abs(actual - expected) < 0.001

    def test_kurtosis_matches_scipy(self) -> None:
        """Verify kurtosis matches scipy.stats.kurtosis with fisher=True, bias=False."""
        from statistics import mean as stats_mean
        from statistics import stdev

        from scipy import stats as scipy_stats

        # Heavy-tailed data
        data = (1.0, 2.0, 3.0, 4.0, 5.0, 100.0)
        data_mean = stats_mean(data)
        data_std = stdev(data)

        expected = scipy_stats.kurtosis(data, fisher=True, bias=False)
        actual = _calculate_kurtosis(data, data_mean, data_std)

        assert abs(actual - expected) < 0.001

    def test_skewness_symmetric_data(self) -> None:
        """Symmetric data should have skewness near zero."""
        from statistics import mean as stats_mean
        from statistics import stdev

        data = (1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0)
        data_mean = stats_mean(data)
        data_std = stdev(data)

        skew = _calculate_skewness(data, data_mean, data_std)
        assert abs(skew) < 0.01

    def test_kurtosis_normal_like_data(self) -> None:
        """Normal-like data should have excess kurtosis near zero."""
        from statistics import mean as stats_mean
        from statistics import stdev

        from scipy import stats as scipy_stats

        # Generate normal-like data using known values
        data = tuple(scipy_stats.norm.ppf(i / 101) for i in range(1, 101))
        data_mean = stats_mean(data)
        data_std = stdev(data)

        kurt = _calculate_kurtosis(data, data_mean, data_std)
        # Normal distribution has excess kurtosis of 0
        # With sample adjustment and finite data, should be close
        assert abs(kurt) < 0.5


class TestConfidenceIntervalValidation:
    """Tests validating CI t-distribution critical value calculations."""

    def test_ci_bounds_known_dataset(self) -> None:
        """Verify CI bounds with manually calculable values."""
        from scipy import stats as scipy_stats

        # Known dataset where we can verify the math
        data = (10.0, 12.0, 14.0, 16.0, 18.0)  # mean=14, std~=3.162
        n = 5

        ci = _calculate_mean_confidence_interval(data, confidence_level=0.95)

        # Manual calculation
        from statistics import mean as stats_mean
        from statistics import stdev

        data_mean = stats_mean(data)
        data_std = stdev(data)
        t_critical = scipy_stats.t.ppf(0.975, df=n - 1)  # ~2.776
        margin = t_critical * (data_std / math.sqrt(n))

        expected_lower = data_mean - margin
        expected_upper = data_mean + margin

        assert abs(ci.lower - expected_lower) < 0.001
        assert abs(ci.upper - expected_upper) < 0.001

    def test_ci_contains_mean(self) -> None:
        """CI should always contain the sample mean."""
        from statistics import mean as stats_mean

        data = (5.0, 10.0, 15.0, 20.0, 25.0, 30.0)
        data_mean = stats_mean(data)

        ci = _calculate_mean_confidence_interval(data, confidence_level=0.95)

        assert ci.lower <= data_mean <= ci.upper


class TestRiskMetricsBoundaryConditions:
    """Tests for risk metrics boundary conditions."""

    def test_loss_threshold_boundary_exact_50pct(self) -> None:
        """Exactly 50% loss should count toward prob_loss_50pct."""
        # -500 is exactly 50% of 1000
        profits = (-500.0, -499.99, 100.0)
        risk = _calculate_risk_metrics(
            session_profits=profits, starting_bankroll=1000.0
        )
        # Only -500.0 is <= -500 (50% threshold)
        assert abs(risk.prob_loss_50pct - 1 / 3) < 0.001

    def test_loss_threshold_boundary_exact_100pct(self) -> None:
        """Exactly 100% loss should count toward prob_loss_100pct."""
        # -1000 is exactly 100% of 1000
        profits = (-1000.0, -999.99, -500.0, 100.0)
        risk = _calculate_risk_metrics(
            session_profits=profits, starting_bankroll=1000.0
        )
        # Only -1000.0 is <= -1000 (100% threshold)
        assert abs(risk.prob_loss_100pct - 1 / 4) < 0.001
        # -1000.0, -999.99, and -500.0 are all <= -500 (50% threshold)
        assert abs(risk.prob_loss_50pct - 3 / 4) < 0.001

    def test_zero_starting_bankroll_disables_loss_thresholds(self) -> None:
        """Zero starting bankroll should result in 0.0 for loss threshold probs."""
        profits = (-1000.0, -500.0, 100.0)
        risk = _calculate_risk_metrics(session_profits=profits, starting_bankroll=0.0)
        assert risk.prob_loss_50pct == 0.0
        assert risk.prob_loss_100pct == 0.0
        # But prob_any_loss should still work
        assert abs(risk.prob_any_loss - 2 / 3) < 0.001


class TestPercentileEdgeValues:
    """Tests for percentile edge cases 0 and 100."""

    def test_percentile_0_returns_min(self) -> None:
        """Percentile 0 should return min value."""
        data = (5.0, 10.0, 15.0, 20.0, 25.0)
        percentiles = _calculate_percentiles(data, (0, 50, 100))
        assert percentiles[0] == 5.0

    def test_percentile_100_returns_max(self) -> None:
        """Percentile 100 should return max value."""
        data = (5.0, 10.0, 15.0, 20.0, 25.0)
        percentiles = _calculate_percentiles(data, (0, 50, 100))
        assert percentiles[100] == 25.0

    def test_all_extreme_percentiles(self) -> None:
        """Test 0, 50, and 100 percentiles together."""
        data = (1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0)
        percentiles = _calculate_percentiles(data, (0, 50, 100))

        assert percentiles[0] == 1.0  # min
        assert percentiles[100] == 9.0  # max
        # Median should be 5.0
        assert percentiles[50] == 5.0


class TestConfidenceLevelValidation:
    """Tests for confidence_level parameter validation."""

    def test_confidence_level_zero_raises_error(self) -> None:
        """confidence_level of 0 should raise ValueError."""
        data = (1.0, 2.0, 3.0, 4.0, 5.0)
        with pytest.raises(
            ValueError, match="confidence_level must be between 0 and 1"
        ):
            _calculate_mean_confidence_interval(data, confidence_level=0.0)

    def test_confidence_level_one_raises_error(self) -> None:
        """confidence_level of 1 should raise ValueError."""
        data = (1.0, 2.0, 3.0, 4.0, 5.0)
        with pytest.raises(
            ValueError, match="confidence_level must be between 0 and 1"
        ):
            _calculate_mean_confidence_interval(data, confidence_level=1.0)

    def test_confidence_level_negative_raises_error(self) -> None:
        """Negative confidence_level should raise ValueError."""
        data = (1.0, 2.0, 3.0, 4.0, 5.0)
        with pytest.raises(
            ValueError, match="confidence_level must be between 0 and 1"
        ):
            _calculate_mean_confidence_interval(data, confidence_level=-0.5)

    def test_confidence_level_greater_than_one_raises_error(self) -> None:
        """confidence_level > 1 should raise ValueError."""
        data = (1.0, 2.0, 3.0, 4.0, 5.0)
        with pytest.raises(
            ValueError, match="confidence_level must be between 0 and 1"
        ):
            _calculate_mean_confidence_interval(data, confidence_level=2.0)

    def test_calculate_statistics_invalid_confidence_level(self) -> None:
        """calculate_statistics should validate confidence_level."""
        agg = create_aggregate_statistics()
        with pytest.raises(
            ValueError, match="confidence_level must be between 0 and 1"
        ):
            calculate_statistics(agg, confidence_level=0.0)

    def test_calculate_statistics_from_results_invalid_confidence_level(self) -> None:
        """calculate_statistics_from_results should validate confidence_level."""
        results = [create_session_result()]
        with pytest.raises(
            ValueError, match="confidence_level must be between 0 and 1"
        ):
            calculate_statistics_from_results(results, confidence_level=1.5)
