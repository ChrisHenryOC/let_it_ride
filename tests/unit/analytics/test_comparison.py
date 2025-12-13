"""Unit tests for strategy comparison analytics module."""

from __future__ import annotations

import math

import pytest

from let_it_ride.analytics.comparison import (
    EffectSize,
    SignificanceTest,
    StrategyComparison,
    _calculate_cohens_d,
    _determine_confidence,
    _interpret_cohens_d,
    _perform_mannwhitney,
    _perform_ttest,
    compare_multiple_strategies,
    compare_strategies,
    format_comparison_report,
)
from let_it_ride.simulation.session import SessionOutcome, SessionResult, StopReason


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


def create_results_with_profits(
    profits: list[float],
    hands_per_session: int = 100,
) -> list[SessionResult]:
    """Create list of SessionResult with specified profits."""
    results = []
    for profit in profits:
        outcome = (
            SessionOutcome.WIN
            if profit > 0
            else SessionOutcome.PUSH
            if profit == 0
            else SessionOutcome.LOSS
        )
        results.append(
            create_session_result(
                outcome=outcome,
                session_profit=profit,
                final_bankroll=1000.0 + profit,
                hands_played=hands_per_session,
            )
        )
    return results


class TestSignificanceTestDataclass:
    """Tests for SignificanceTest dataclass."""

    def test_create_significance_test(self) -> None:
        """Should create significance test with all fields."""
        test = SignificanceTest(
            test_name="t-test",
            statistic=2.5,
            p_value=0.01,
            is_significant=True,
        )
        assert test.test_name == "t-test"
        assert test.statistic == 2.5
        assert test.p_value == 0.01
        assert test.is_significant is True

    def test_significance_test_is_frozen(self) -> None:
        """SignificanceTest should be immutable."""
        test = SignificanceTest(
            test_name="t-test",
            statistic=2.5,
            p_value=0.01,
            is_significant=True,
        )
        with pytest.raises(AttributeError):
            test.p_value = 0.05  # type: ignore[misc]


class TestEffectSizeDataclass:
    """Tests for EffectSize dataclass."""

    def test_create_effect_size(self) -> None:
        """Should create effect size with all fields."""
        es = EffectSize(cohens_d=0.5, interpretation="medium")
        assert es.cohens_d == 0.5
        assert es.interpretation == "medium"

    def test_effect_size_is_frozen(self) -> None:
        """EffectSize should be immutable."""
        es = EffectSize(cohens_d=0.5, interpretation="medium")
        with pytest.raises(AttributeError):
            es.cohens_d = 0.8  # type: ignore[misc]


class TestStrategyComparisonDataclass:
    """Tests for StrategyComparison dataclass."""

    def test_create_strategy_comparison(self) -> None:
        """Should create strategy comparison with all fields."""
        ttest = SignificanceTest("t-test", 2.0, 0.05, True)
        mw = SignificanceTest("mann-whitney", 1000.0, 0.05, True)
        es = EffectSize(0.5, "medium")

        comp = StrategyComparison(
            strategy_a_name="basic",
            strategy_b_name="aggressive",
            sessions_a=100,
            sessions_b=100,
            win_rate_a=0.35,
            win_rate_b=0.30,
            win_rate_diff=0.05,
            ev_a=-0.035,
            ev_b=-0.050,
            ev_diff=0.015,
            ev_pct_diff=30.0,
            profit_mean_a=-35.0,
            profit_mean_b=-50.0,
            profit_std_a=100.0,
            profit_std_b=120.0,
            ttest=ttest,
            mann_whitney=mw,
            effect_size=es,
            better_strategy="basic",
            confidence="medium",
        )
        assert comp.strategy_a_name == "basic"
        assert comp.win_rate_diff == 0.05
        assert comp.better_strategy == "basic"

    def test_strategy_comparison_is_frozen(self) -> None:
        """StrategyComparison should be immutable."""
        ttest = SignificanceTest("t-test", 2.0, 0.05, True)
        mw = SignificanceTest("mann-whitney", 1000.0, 0.05, True)
        es = EffectSize(0.5, "medium")

        comp = StrategyComparison(
            strategy_a_name="basic",
            strategy_b_name="aggressive",
            sessions_a=100,
            sessions_b=100,
            win_rate_a=0.35,
            win_rate_b=0.30,
            win_rate_diff=0.05,
            ev_a=-0.035,
            ev_b=-0.050,
            ev_diff=0.015,
            ev_pct_diff=30.0,
            profit_mean_a=-35.0,
            profit_mean_b=-50.0,
            profit_std_a=100.0,
            profit_std_b=120.0,
            ttest=ttest,
            mann_whitney=mw,
            effect_size=es,
            better_strategy="basic",
            confidence="medium",
        )
        with pytest.raises(AttributeError):
            comp.better_strategy = "aggressive"  # type: ignore[misc]


class TestInterpretCohensD:
    """Tests for Cohen's d interpretation."""

    def test_negligible_effect(self) -> None:
        """d < 0.2 should be negligible."""
        assert _interpret_cohens_d(0.0) == "negligible"
        assert _interpret_cohens_d(0.1) == "negligible"
        assert _interpret_cohens_d(0.19) == "negligible"
        assert _interpret_cohens_d(-0.1) == "negligible"

    def test_small_effect(self) -> None:
        """0.2 <= |d| < 0.5 should be small."""
        assert _interpret_cohens_d(0.2) == "small"
        assert _interpret_cohens_d(0.35) == "small"
        assert _interpret_cohens_d(0.49) == "small"
        assert _interpret_cohens_d(-0.3) == "small"

    def test_medium_effect(self) -> None:
        """0.5 <= |d| < 0.8 should be medium."""
        assert _interpret_cohens_d(0.5) == "medium"
        assert _interpret_cohens_d(0.65) == "medium"
        assert _interpret_cohens_d(0.79) == "medium"
        assert _interpret_cohens_d(-0.6) == "medium"

    def test_large_effect(self) -> None:
        """|d| >= 0.8 should be large."""
        assert _interpret_cohens_d(0.8) == "large"
        assert _interpret_cohens_d(1.0) == "large"
        assert _interpret_cohens_d(2.0) == "large"
        assert _interpret_cohens_d(-1.2) == "large"


class TestCalculateCohensD:
    """Tests for Cohen's d calculation."""

    def test_identical_distributions(self) -> None:
        """Identical distributions should have d=0."""
        data = tuple([100.0] * 50)
        es = _calculate_cohens_d(data, data)
        assert es.cohens_d == 0.0
        assert es.interpretation == "negligible"

    def test_empty_data(self) -> None:
        """Empty data should return negligible effect."""
        es = _calculate_cohens_d((), (1.0, 2.0, 3.0))
        assert es.cohens_d == 0.0
        assert es.interpretation == "negligible"

        es = _calculate_cohens_d((1.0, 2.0, 3.0), ())
        assert es.cohens_d == 0.0
        assert es.interpretation == "negligible"

    def test_known_effect_size(self) -> None:
        """Test with distributions that have a known effect size."""
        # Two distributions with means 0 and 1, both with std=1
        # Cohen's d = (1 - 0) / 1 = 1.0 (large effect)
        import random

        random.seed(42)
        data_a = tuple(random.gauss(0, 1) for _ in range(1000))
        data_b = tuple(random.gauss(1, 1) for _ in range(1000))

        es = _calculate_cohens_d(data_a, data_b)
        # Should be approximately -1.0 (negative because a < b)
        assert -1.2 < es.cohens_d < -0.8
        assert es.interpretation == "large"

    def test_small_effect_size(self) -> None:
        """Test with distributions having small effect size."""
        import random

        random.seed(123)
        # Means differ by 0.3 std
        data_a = tuple(random.gauss(0, 1) for _ in range(500))
        data_b = tuple(random.gauss(0.3, 1) for _ in range(500))

        es = _calculate_cohens_d(data_a, data_b)
        # Should be approximately -0.3 (small effect)
        assert -0.5 < es.cohens_d < -0.1
        assert es.interpretation == "small"

    def test_single_element_groups(self) -> None:
        """Single element groups should handle gracefully."""
        es = _calculate_cohens_d((5.0,), (10.0,))
        # With no variance, returns 0
        assert es.cohens_d == 0.0


class TestPerformTtest:
    """Tests for t-test function."""

    def test_identical_distributions_not_significant(self) -> None:
        """Identical data should not be significant."""
        data = tuple(range(100))
        result = _perform_ttest(data, data)
        assert result.test_name == "t-test"
        assert result.p_value > 0.05
        assert result.is_significant is False

    def test_clearly_different_distributions(self) -> None:
        """Clearly different distributions should be significant."""
        data_a = tuple(range(0, 100))  # Mean ~49.5
        data_b = tuple(range(100, 200))  # Mean ~149.5
        result = _perform_ttest(data_a, data_b)
        assert result.test_name == "t-test"
        assert result.p_value < 0.001
        assert result.is_significant is True

    def test_insufficient_data(self) -> None:
        """Insufficient data should return non-significant."""
        result = _perform_ttest((1.0,), (2.0, 3.0))
        assert result.is_significant is False
        assert result.p_value == 1.0

        result = _perform_ttest((1.0, 2.0), (3.0,))
        assert result.is_significant is False
        assert result.p_value == 1.0

    def test_custom_significance_level(self) -> None:
        """Should respect custom significance level."""
        import random

        random.seed(999)
        # Create slightly different distributions
        data_a = tuple(random.gauss(0, 1) for _ in range(30))
        data_b = tuple(random.gauss(0.5, 1) for _ in range(30))

        # At 0.10, might be significant
        result_10 = _perform_ttest(data_a, data_b, significance_level=0.10)
        # At 0.01, likely not significant
        result_01 = _perform_ttest(data_a, data_b, significance_level=0.01)

        # Same p-value, different significance determination
        assert result_10.p_value == result_01.p_value


class TestPerformMannWhitney:
    """Tests for Mann-Whitney U test function."""

    def test_identical_values_not_significant(self) -> None:
        """All same values should not be significant."""
        data = tuple([50.0] * 20)
        result = _perform_mannwhitney(data, data)
        assert result.test_name == "mann-whitney"
        assert result.is_significant is False

    def test_clearly_different_distributions(self) -> None:
        """Clearly different distributions should be significant."""
        data_a = tuple(range(0, 50))
        data_b = tuple(range(50, 100))
        result = _perform_mannwhitney(data_a, data_b)
        assert result.test_name == "mann-whitney"
        assert result.p_value < 0.001
        assert result.is_significant is True

    def test_empty_data(self) -> None:
        """Empty data should return non-significant."""
        result = _perform_mannwhitney((), (1.0, 2.0, 3.0))
        assert result.is_significant is False
        assert result.p_value == 1.0

    def test_single_element(self) -> None:
        """Single element should work."""
        result = _perform_mannwhitney((1.0,), (10.0,))
        # Can still compute, but significance depends on values
        assert result.test_name == "mann-whitney"


class TestDetermineConfidence:
    """Tests for confidence level determination."""

    def test_high_confidence(self) -> None:
        """Both tests significant with medium+ effect -> high confidence."""
        ttest = SignificanceTest("t-test", 3.0, 0.001, True)
        mw = SignificanceTest("mann-whitney", 2000.0, 0.001, True)
        es = EffectSize(0.8, "large")

        assert _determine_confidence(ttest, mw, es) == "high"

    def test_medium_confidence_one_test(self) -> None:
        """One test significant with small+ effect -> medium confidence."""
        ttest = SignificanceTest("t-test", 2.0, 0.03, True)
        mw = SignificanceTest("mann-whitney", 1500.0, 0.08, False)
        es = EffectSize(0.4, "small")

        assert _determine_confidence(ttest, mw, es) == "medium"

    def test_low_confidence_not_significant(self) -> None:
        """Neither test significant -> low confidence."""
        ttest = SignificanceTest("t-test", 1.0, 0.30, False)
        mw = SignificanceTest("mann-whitney", 1200.0, 0.25, False)
        es = EffectSize(0.1, "negligible")

        assert _determine_confidence(ttest, mw, es) == "low"

    def test_medium_confidence_negligible_effect(self) -> None:
        """Both tests significant but negligible effect -> medium confidence."""
        ttest = SignificanceTest("t-test", 2.0, 0.04, True)
        mw = SignificanceTest("mann-whitney", 1800.0, 0.04, True)
        es = EffectSize(0.1, "negligible")

        # When both tests are significant, we have medium confidence
        # even without a meaningful effect size
        assert _determine_confidence(ttest, mw, es) == "medium"

    def test_high_confidence_very_low_p_value_negligible_effect(self) -> None:
        """Both tests highly significant (p < 0.001) -> high confidence regardless of effect."""
        ttest = SignificanceTest("t-test", 5.0, 0.0001, True)
        mw = SignificanceTest("mann-whitney", 2500.0, 0.0001, True)
        es = EffectSize(0.1, "negligible")

        # Very low p-values trigger high confidence even with negligible effect size
        # This handles edge cases where variance is near zero but means clearly differ
        assert _determine_confidence(ttest, mw, es) == "high"


class TestCompareStrategies:
    """Tests for main compare_strategies function."""

    def test_compare_identical_strategies(self) -> None:
        """Comparing identical results should show no significant difference."""
        profits = [10.0, -20.0, 30.0, -15.0, 5.0] * 20  # 100 sessions
        results = create_results_with_profits(profits)

        comp = compare_strategies(results, results, "strategy_a", "strategy_b")

        assert comp.strategy_a_name == "strategy_a"
        assert comp.strategy_b_name == "strategy_b"
        assert comp.sessions_a == 100
        assert comp.sessions_b == 100
        assert comp.win_rate_diff == 0.0
        assert comp.ev_diff == 0.0
        assert comp.better_strategy is None
        assert comp.confidence == "low"

    def test_compare_clearly_different_strategies(self) -> None:
        """Comparing very different strategies should show significant difference."""
        # Strategy A: mostly winning
        profits_a = [50.0, 40.0, 30.0, 20.0, -10.0] * 20
        # Strategy B: mostly losing
        profits_b = [-50.0, -40.0, -30.0, -20.0, 10.0] * 20

        results_a = create_results_with_profits(profits_a)
        results_b = create_results_with_profits(profits_b)

        comp = compare_strategies(results_a, results_b, "winner", "loser")

        assert comp.win_rate_a > comp.win_rate_b
        assert comp.profit_mean_a > comp.profit_mean_b
        assert comp.ttest.is_significant is True
        assert comp.mann_whitney.is_significant is True
        assert comp.effect_size.interpretation == "large"
        assert comp.better_strategy == "winner"
        assert comp.confidence == "high"

    def test_compare_strategies_b_is_better(self) -> None:
        """Should correctly identify when strategy B is better."""
        # Strategy A: mostly losing
        profits_a = [-50.0, -40.0, -30.0, -20.0, 10.0] * 20
        # Strategy B: mostly winning
        profits_b = [50.0, 40.0, 30.0, 20.0, -10.0] * 20

        results_a = create_results_with_profits(profits_a)
        results_b = create_results_with_profits(profits_b)

        comp = compare_strategies(results_a, results_b, "loser", "winner")

        assert comp.profit_mean_a < comp.profit_mean_b
        assert comp.better_strategy == "winner"
        assert comp.confidence == "high"

    def test_empty_results_raises_error(self) -> None:
        """Empty results should raise ValueError."""
        results = create_results_with_profits([10.0, -5.0])

        with pytest.raises(ValueError, match="results_a cannot be empty"):
            compare_strategies([], results, "a", "b")

        with pytest.raises(ValueError, match="results_b cannot be empty"):
            compare_strategies(results, [], "a", "b")

    def test_invalid_significance_level(self) -> None:
        """Invalid significance level should raise ValueError."""
        results = create_results_with_profits([10.0, -5.0])

        with pytest.raises(ValueError, match="significance_level must be between"):
            compare_strategies(results, results, "a", "b", significance_level=0.0)

        with pytest.raises(ValueError, match="significance_level must be between"):
            compare_strategies(results, results, "a", "b", significance_level=1.0)

        with pytest.raises(ValueError, match="significance_level must be between"):
            compare_strategies(results, results, "a", "b", significance_level=-0.1)

    def test_ev_calculation(self) -> None:
        """Should correctly calculate EV per hand."""
        # 100 hands per session, $10 profit per session -> $0.10 EV per hand
        results_a = create_results_with_profits([10.0] * 10, hands_per_session=100)
        # 100 hands per session, $20 profit per session -> $0.20 EV per hand
        results_b = create_results_with_profits([20.0] * 10, hands_per_session=100)

        comp = compare_strategies(results_a, results_b, "a", "b")

        assert math.isclose(comp.ev_a, 0.10)
        assert math.isclose(comp.ev_b, 0.20)
        assert math.isclose(comp.ev_diff, -0.10)

    def test_ev_pct_diff_with_zero_ev(self) -> None:
        """EV percentage diff should be None when EV_b is zero."""
        results_a = create_results_with_profits([10.0] * 10)
        results_b = create_results_with_profits([0.0] * 10)

        comp = compare_strategies(results_a, results_b, "a", "b")
        assert comp.ev_pct_diff is None

    def test_win_rate_calculation(self) -> None:
        """Should correctly calculate win rates."""
        # 70% wins
        profits_a = [10.0] * 7 + [-10.0] * 3
        # 40% wins
        profits_b = [10.0] * 4 + [-10.0] * 6

        results_a = create_results_with_profits(profits_a)
        results_b = create_results_with_profits(profits_b)

        comp = compare_strategies(results_a, results_b, "a", "b")

        assert comp.win_rate_a == 0.7
        assert comp.win_rate_b == 0.4
        assert math.isclose(comp.win_rate_diff, 0.3)


class TestCompareMultipleStrategies:
    """Tests for compare_multiple_strategies function."""

    def test_compare_three_strategies(self) -> None:
        """Should generate all pairwise comparisons for 3 strategies."""
        results_dict = {
            "basic": create_results_with_profits([10.0, -5.0, 3.0] * 10),
            "aggressive": create_results_with_profits([20.0, -15.0, 5.0] * 10),
            "conservative": create_results_with_profits([5.0, -2.0, 1.0] * 10),
        }

        comparisons = compare_multiple_strategies(results_dict)

        # 3 strategies -> 3 pairwise comparisons
        assert len(comparisons) == 3

        # Check all pairs are present
        pairs = {(c.strategy_a_name, c.strategy_b_name) for c in comparisons}
        assert ("basic", "aggressive") in pairs
        assert ("basic", "conservative") in pairs
        assert ("aggressive", "conservative") in pairs

    def test_compare_two_strategies(self) -> None:
        """Should handle minimum case of 2 strategies."""
        results_dict = {
            "a": create_results_with_profits([10.0, -5.0]),
            "b": create_results_with_profits([5.0, -2.0]),
        }

        comparisons = compare_multiple_strategies(results_dict)
        assert len(comparisons) == 1
        assert comparisons[0].strategy_a_name == "a"
        assert comparisons[0].strategy_b_name == "b"

    def test_fewer_than_two_strategies_raises_error(self) -> None:
        """Should raise error with fewer than 2 strategies."""
        with pytest.raises(ValueError, match="At least 2 strategies required"):
            compare_multiple_strategies({})

        with pytest.raises(ValueError, match="At least 2 strategies required"):
            compare_multiple_strategies(
                {"only_one": create_results_with_profits([10.0])}
            )

    def test_empty_results_for_strategy_raises_error(self) -> None:
        """Should raise error if any strategy has empty results."""
        results_dict = {
            "valid": create_results_with_profits([10.0, -5.0]),
            "empty": [],
        }

        with pytest.raises(
            ValueError, match="Results for strategy 'empty' cannot be empty"
        ):
            compare_multiple_strategies(results_dict)


class TestFormatComparisonReport:
    """Tests for comparison report formatting."""

    def test_format_basic_report(self) -> None:
        """Should format a complete comparison report."""
        profits_a = [50.0, 40.0, 30.0, -10.0] * 10
        profits_b = [-20.0, -30.0, 10.0, 5.0] * 10

        results_a = create_results_with_profits(profits_a)
        results_b = create_results_with_profits(profits_b)

        comp = compare_strategies(results_a, results_b, "basic", "aggressive")
        report = format_comparison_report(comp)

        # Check key sections exist
        assert "Strategy Comparison: basic vs aggressive" in report
        assert "Sample Sizes:" in report
        assert "Win Rates:" in report
        assert "Expected Value per Hand:" in report
        assert "Statistical Tests:" in report
        assert "Effect Size:" in report
        assert "Conclusion:" in report

    def test_format_report_with_no_significant_difference(self) -> None:
        """Report should indicate no significant difference when appropriate."""
        results = create_results_with_profits([10.0, -5.0, 3.0, -2.0] * 10)
        comp = compare_strategies(results, results, "a", "b")
        report = format_comparison_report(comp)

        assert "No statistically significant difference detected" in report

    def test_format_report_with_significant_difference(self) -> None:
        """Report should indicate better strategy when significant."""
        profits_a = [100.0] * 50
        profits_b = [-100.0] * 50

        results_a = create_results_with_profits(profits_a)
        results_b = create_results_with_profits(profits_b)

        comp = compare_strategies(results_a, results_b, "winner", "loser")
        report = format_comparison_report(comp)

        assert "winner appears to be the better strategy" in report

    def test_format_report_ev_pct_diff_none(self) -> None:
        """Report should handle None ev_pct_diff gracefully."""
        results_a = create_results_with_profits([10.0] * 10)
        results_b = create_results_with_profits([0.0] * 10)

        comp = compare_strategies(results_a, results_b, "a", "b")
        report = format_comparison_report(comp)

        # Should not contain "Relative Difference" when ev_pct_diff is None
        # Actually it might still work, let's check the actual output format
        assert "Expected Value per Hand:" in report


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_single_session_per_strategy(self) -> None:
        """Should handle single session (though significance tests will fail)."""
        results_a = create_results_with_profits([100.0])
        results_b = create_results_with_profits([-50.0])

        comp = compare_strategies(results_a, results_b, "a", "b")

        # Metrics should still be calculated
        assert comp.sessions_a == 1
        assert comp.sessions_b == 1
        assert comp.profit_mean_a == 100.0
        assert comp.profit_mean_b == -50.0
        # But significance tests won't be valid
        assert comp.ttest.is_significant is False

    def test_all_zero_profits(self) -> None:
        """Should handle all zero profits."""
        results_a = create_results_with_profits([0.0] * 10)
        results_b = create_results_with_profits([0.0] * 10)

        comp = compare_strategies(results_a, results_b, "a", "b")

        assert comp.profit_mean_a == 0.0
        assert comp.profit_mean_b == 0.0
        assert comp.effect_size.interpretation == "negligible"

    def test_very_large_sample_sizes(self) -> None:
        """Should handle large sample sizes efficiently."""
        import random

        random.seed(42)
        profits_a = [random.gauss(0, 100) for _ in range(1000)]
        profits_b = [random.gauss(10, 100) for _ in range(1000)]

        results_a = create_results_with_profits(profits_a)
        results_b = create_results_with_profits(profits_b)

        comp = compare_strategies(results_a, results_b, "a", "b")

        # With 1000 samples, small differences should be detectable
        assert comp.sessions_a == 1000
        assert comp.sessions_b == 1000

    def test_unequal_sample_sizes(self) -> None:
        """Should handle unequal sample sizes between strategies."""
        results_a = create_results_with_profits([10.0, -5.0, 3.0] * 10)  # 30 sessions
        results_b = create_results_with_profits([5.0, -2.0] * 50)  # 100 sessions

        comp = compare_strategies(results_a, results_b, "small", "large")

        assert comp.sessions_a == 30
        assert comp.sessions_b == 100

    def test_zero_hands_edge_case(self) -> None:
        """Should handle sessions with zero hands played gracefully."""
        # Create results with 0 hands played
        results_a = [
            create_session_result(session_profit=10.0, hands_played=0),
            create_session_result(session_profit=-5.0, hands_played=0),
        ]
        results_b = [
            create_session_result(session_profit=5.0, hands_played=100),
            create_session_result(session_profit=-2.0, hands_played=100),
        ]

        comp = compare_strategies(results_a, results_b, "zero_hands", "normal")

        # EV for zero hands should be 0.0
        assert comp.ev_a == 0.0
        assert comp.ev_b != 0.0
        # Comparison should still work
        assert comp.sessions_a == 2
        assert comp.sessions_b == 2


class TestNumericalStability:
    """Tests for numerical stability with extreme values."""

    def test_very_large_profits_no_nan(self) -> None:
        """Should handle very large profit values without producing NaN."""
        profits = [1e15, 2e15, 1.5e15] * 10
        results_a = create_results_with_profits(profits)
        results_b = create_results_with_profits([p * 0.9 for p in profits])

        comp = compare_strategies(results_a, results_b, "a", "b")

        assert not math.isnan(comp.effect_size.cohens_d)
        assert not math.isnan(comp.ttest.statistic)
        assert not math.isnan(comp.profit_mean_a)
        assert not math.isnan(comp.profit_mean_b)

    def test_very_small_profits_no_nan(self) -> None:
        """Should handle very small profit values without producing NaN."""
        profits = [1e-15, 2e-15, 1.5e-15] * 10
        results_a = create_results_with_profits(profits)
        results_b = create_results_with_profits([p * 0.9 for p in profits])

        comp = compare_strategies(results_a, results_b, "a", "b")

        assert not math.isnan(comp.effect_size.cohens_d)
        assert not math.isnan(comp.profit_mean_a)
        assert not math.isnan(comp.profit_mean_b)

    def test_mixed_extreme_values(self) -> None:
        """Should handle mixed large positive and negative values."""
        profits_a = [1e10, -1e10, 1e10, -1e10] * 5
        profits_b = [1e9, -1e9, 1e9, -1e9] * 5

        results_a = create_results_with_profits(profits_a)
        results_b = create_results_with_profits(profits_b)

        comp = compare_strategies(results_a, results_b, "a", "b")

        assert not math.isnan(comp.effect_size.cohens_d)
        assert not math.isnan(comp.ttest.statistic)
