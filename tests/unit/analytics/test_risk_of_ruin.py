"""Unit tests for risk of ruin calculator module."""

from __future__ import annotations

import math
from statistics import mean, stdev

import numpy as np
import pytest

from let_it_ride.analytics.risk_of_ruin import (
    RiskOfRuinReport,
    RiskOfRuinResult,
    _calculate_analytical_ruin_probability,
    _calculate_ruin_for_bankroll_level,
    _run_monte_carlo_ruin_simulation,
    _validate_bankroll_units,
    _validate_confidence_level,
    _validate_session_results,
    calculate_risk_of_ruin,
    format_risk_of_ruin_report,
)
from let_it_ride.analytics.statistics import ConfidenceInterval
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


def create_session_results(
    profits: list[float],
    starting_bankroll: float = 1000.0,
    hands_per_session: int = 100,
    base_bet: float = 10.0,
) -> list[SessionResult]:
    """Create a list of SessionResult objects from profit values."""
    results = []
    for profit in profits:
        outcome = (
            SessionOutcome.WIN
            if profit > 0
            else SessionOutcome.LOSS
            if profit < 0
            else SessionOutcome.PUSH
        )
        results.append(
            create_session_result(
                outcome=outcome,
                session_profit=profit,
                starting_bankroll=starting_bankroll,
                final_bankroll=starting_bankroll + profit,
                hands_played=hands_per_session,
                total_wagered=base_bet * hands_per_session * 3,  # 3 bets per hand
            )
        )
    return results


class TestRiskOfRuinResultDataclass:
    """Tests for RiskOfRuinResult dataclass."""

    def test_create_result(self) -> None:
        """Should create result with all fields."""
        ci = ConfidenceInterval(lower=0.05, upper=0.15, level=0.95)
        result = RiskOfRuinResult(
            bankroll_units=100,
            ruin_probability=0.10,
            confidence_interval=ci,
            half_bankroll_risk=0.25,
            quarter_bankroll_risk=0.40,
            sessions_simulated=10000,
        )
        assert result.bankroll_units == 100
        assert result.ruin_probability == 0.10
        assert result.half_bankroll_risk == 0.25
        assert result.quarter_bankroll_risk == 0.40
        assert result.sessions_simulated == 10000

    def test_result_is_frozen(self) -> None:
        """RiskOfRuinResult should be immutable."""
        ci = ConfidenceInterval(lower=0.05, upper=0.15, level=0.95)
        result = RiskOfRuinResult(
            bankroll_units=100,
            ruin_probability=0.10,
            confidence_interval=ci,
            half_bankroll_risk=0.25,
            quarter_bankroll_risk=0.40,
            sessions_simulated=10000,
        )
        with pytest.raises(AttributeError):
            result.ruin_probability = 0.20  # type: ignore[misc]


class TestRiskOfRuinReportDataclass:
    """Tests for RiskOfRuinReport dataclass."""

    def test_create_report(self) -> None:
        """Should create report with all fields."""
        ci = ConfidenceInterval(lower=0.05, upper=0.15, level=0.95)
        result = RiskOfRuinResult(
            bankroll_units=100,
            ruin_probability=0.10,
            confidence_interval=ci,
            half_bankroll_risk=0.25,
            quarter_bankroll_risk=0.40,
            sessions_simulated=10000,
        )
        report = RiskOfRuinReport(
            base_bet=10.0,
            starting_bankroll=1000.0,
            results=(result,),
            mean_session_profit=-5.0,
            session_profit_std=50.0,
            analytical_estimates=(0.12,),
        )
        assert report.base_bet == 10.0
        assert report.starting_bankroll == 1000.0
        assert len(report.results) == 1
        assert report.mean_session_profit == -5.0
        assert report.session_profit_std == 50.0

    def test_report_is_frozen(self) -> None:
        """RiskOfRuinReport should be immutable."""
        report = RiskOfRuinReport(
            base_bet=10.0,
            starting_bankroll=1000.0,
            results=(),
            mean_session_profit=0.0,
            session_profit_std=0.0,
            analytical_estimates=None,
        )
        with pytest.raises(AttributeError):
            report.base_bet = 20.0  # type: ignore[misc]


class TestValidateBankrollUnits:
    """Tests for _validate_bankroll_units."""

    def test_valid_bankroll_units(self) -> None:
        """Valid bankroll units should not raise."""
        _validate_bankroll_units([20, 40, 60, 80, 100])

    def test_single_unit(self) -> None:
        """Single unit should be valid."""
        _validate_bankroll_units([50])

    def test_empty_raises_error(self) -> None:
        """Empty list should raise ValueError."""
        with pytest.raises(ValueError, match="must not be empty"):
            _validate_bankroll_units([])

    def test_zero_raises_error(self) -> None:
        """Zero value should raise ValueError."""
        with pytest.raises(ValueError, match="must be positive"):
            _validate_bankroll_units([20, 0, 60])

    def test_negative_raises_error(self) -> None:
        """Negative value should raise ValueError."""
        with pytest.raises(ValueError, match="must be positive"):
            _validate_bankroll_units([20, -10, 60])


class TestValidateSessionResults:
    """Tests for _validate_session_results."""

    def test_valid_results(self) -> None:
        """Valid session results should not raise."""
        results = create_session_results([10.0] * 20)
        _validate_session_results(results)

    def test_minimum_results(self) -> None:
        """Exactly 10 results should be valid."""
        results = create_session_results([10.0] * 10)
        _validate_session_results(results)

    def test_empty_raises_error(self) -> None:
        """Empty list should raise ValueError."""
        with pytest.raises(ValueError, match="must not be empty"):
            _validate_session_results([])

    def test_insufficient_data_raises_error(self) -> None:
        """Less than 10 results should raise ValueError."""
        results = create_session_results([10.0] * 9)
        with pytest.raises(ValueError, match="At least 10 session results"):
            _validate_session_results(results)


class TestValidateConfidenceLevel:
    """Tests for _validate_confidence_level."""

    def test_valid_confidence_level(self) -> None:
        """Valid confidence levels should not raise."""
        _validate_confidence_level(0.95)
        _validate_confidence_level(0.90)
        _validate_confidence_level(0.99)

    def test_zero_raises_error(self) -> None:
        """Zero should raise ValueError."""
        with pytest.raises(ValueError, match="must be between 0 and 1"):
            _validate_confidence_level(0.0)

    def test_one_raises_error(self) -> None:
        """One should raise ValueError."""
        with pytest.raises(ValueError, match="must be between 0 and 1"):
            _validate_confidence_level(1.0)

    def test_negative_raises_error(self) -> None:
        """Negative value should raise ValueError."""
        with pytest.raises(ValueError, match="must be between 0 and 1"):
            _validate_confidence_level(-0.5)


class TestAnalyticalRuinProbability:
    """Tests for _calculate_analytical_ruin_probability."""

    def test_positive_ev_low_ruin(self) -> None:
        """Positive expected value should have low ruin probability."""
        # With positive EV, ruin probability should decrease with bankroll
        ruin_small = _calculate_analytical_ruin_probability(
            mean_profit=10.0, std_profit=50.0, bankroll=100.0
        )
        ruin_large = _calculate_analytical_ruin_probability(
            mean_profit=10.0, std_profit=50.0, bankroll=1000.0
        )
        assert ruin_small is not None
        assert ruin_large is not None
        assert ruin_large < ruin_small

    def test_negative_ev_certain_ruin(self) -> None:
        """Negative expected value should have certain ruin."""
        ruin = _calculate_analytical_ruin_probability(
            mean_profit=-10.0, std_profit=50.0, bankroll=1000.0
        )
        assert ruin == 1.0

    def test_zero_ev_certain_ruin(self) -> None:
        """Zero expected value should have certain ruin."""
        ruin = _calculate_analytical_ruin_probability(
            mean_profit=0.0, std_profit=50.0, bankroll=1000.0
        )
        assert ruin == 1.0

    def test_zero_std_positive_ev(self) -> None:
        """Zero std with positive EV should have zero ruin."""
        ruin = _calculate_analytical_ruin_probability(
            mean_profit=10.0, std_profit=0.0, bankroll=1000.0
        )
        assert ruin == 0.0

    def test_zero_std_negative_ev(self) -> None:
        """Zero std with negative EV should have certain ruin."""
        ruin = _calculate_analytical_ruin_probability(
            mean_profit=-10.0, std_profit=0.0, bankroll=1000.0
        )
        assert ruin == 1.0

    def test_very_large_bankroll_approaches_zero(self) -> None:
        """Very large bankroll should approach zero ruin probability."""
        ruin = _calculate_analytical_ruin_probability(
            mean_profit=10.0, std_profit=50.0, bankroll=100000.0
        )
        assert ruin is not None
        assert ruin < 0.0001


class TestMonteCarloSimulation:
    """Tests for _run_monte_carlo_ruin_simulation."""

    def test_high_positive_profits_low_ruin(self) -> None:
        """High positive profits should result in very low ruin."""
        rng = np.random.default_rng(42)
        profits = np.array([100.0] * 100)  # All wins

        ruin, half, quarter, total = _run_monte_carlo_ruin_simulation(
            session_profits=profits,
            bankroll=1000.0,
            simulations=1000,
            rng=rng,
            max_sessions_per_sim=100,
        )

        assert ruin == 0  # No ruin with constant wins
        assert half == 0  # Never hit 50% loss
        assert quarter == 0  # Never hit 25% loss
        assert total == 1000

    def test_high_negative_profits_high_ruin(self) -> None:
        """High negative profits should result in high ruin."""
        rng = np.random.default_rng(42)
        profits = np.array([-100.0] * 100)  # All losses

        ruin, half, quarter, total = _run_monte_carlo_ruin_simulation(
            session_profits=profits,
            bankroll=1000.0,
            simulations=1000,
            rng=rng,
            max_sessions_per_sim=100,
        )

        assert ruin == total  # All simulations hit ruin

    def test_mixed_profits_intermediate_ruin(self) -> None:
        """Mixed profits should have intermediate ruin probability."""
        rng = np.random.default_rng(42)
        # Slightly negative EV on average but with some large wins
        # Mean = (-50 -50 -50 + 100 -50)/5 = -100/5 = -20
        profits = np.array([-50.0, -50.0, -50.0, 100.0, -50.0] * 20)

        ruin, half, quarter, total = _run_monte_carlo_ruin_simulation(
            session_profits=profits,
            bankroll=2000.0,  # Larger bankroll to allow some survival
            simulations=1000,
            rng=rng,
            max_sessions_per_sim=50,  # Fewer sessions per sim
        )

        # Should have some ruined simulations
        ruin_rate = ruin / total
        # With negative EV and limited sessions, expect high but not 100% ruin
        assert ruin_rate > 0  # Some ruin expected

    def test_reproducibility_with_seed(self) -> None:
        """Same seed should produce same results."""
        profits = np.array([-20.0, -10.0, 50.0, -30.0, 20.0] * 20)

        rng1 = np.random.default_rng(12345)
        result1 = _run_monte_carlo_ruin_simulation(
            session_profits=profits,
            bankroll=500.0,
            simulations=100,
            rng=rng1,
        )

        rng2 = np.random.default_rng(12345)
        result2 = _run_monte_carlo_ruin_simulation(
            session_profits=profits,
            bankroll=500.0,
            simulations=100,
            rng=rng2,
        )

        assert result1 == result2


class TestCalculateRuinForBankrollLevel:
    """Tests for _calculate_ruin_for_bankroll_level."""

    def test_returns_valid_result(self) -> None:
        """Should return valid RiskOfRuinResult."""
        rng = np.random.default_rng(42)
        profits = np.array([-10.0, 20.0, -15.0, 30.0, -5.0] * 20)

        result = _calculate_ruin_for_bankroll_level(
            session_profits=profits,
            base_bet=10.0,
            bankroll_units=50,
            simulations_per_level=1000,
            confidence_level=0.95,
            rng=rng,
        )

        assert isinstance(result, RiskOfRuinResult)
        assert result.bankroll_units == 50
        assert 0.0 <= result.ruin_probability <= 1.0
        assert 0.0 <= result.half_bankroll_risk <= 1.0
        assert 0.0 <= result.quarter_bankroll_risk <= 1.0
        assert result.sessions_simulated == 1000

    def test_confidence_interval_bounds(self) -> None:
        """Confidence interval should bound the point estimate reasonably."""
        rng = np.random.default_rng(42)
        # Use negative EV profits to get non-zero ruin probability
        profits = np.array([-30.0, -20.0, 10.0, -25.0, 5.0] * 20)

        result = _calculate_ruin_for_bankroll_level(
            session_profits=profits,
            base_bet=10.0,
            bankroll_units=30,  # Smaller bankroll for higher ruin chance
            simulations_per_level=2000,
            confidence_level=0.95,
            rng=rng,
        )

        # CI should be valid (lower < upper)
        assert result.confidence_interval.lower <= result.confidence_interval.upper
        assert result.confidence_interval.level == 0.95
        # With Wilson CI, when ruin=0, lower can be tiny positive value
        # Just verify CI is reasonable
        assert result.confidence_interval.lower >= 0.0
        assert result.confidence_interval.upper <= 1.0

    def test_larger_bankroll_lower_ruin(self) -> None:
        """Larger bankroll should have lower ruin probability."""
        # Use negative EV profits for meaningful comparison
        profits = np.array([-30.0, -10.0, 50.0, -20.0, -15.0] * 20)

        result_small = _calculate_ruin_for_bankroll_level(
            session_profits=profits,
            base_bet=10.0,
            bankroll_units=20,
            simulations_per_level=2000,
            confidence_level=0.95,
            rng=np.random.default_rng(42),
        )

        result_large = _calculate_ruin_for_bankroll_level(
            session_profits=profits,
            base_bet=10.0,
            bankroll_units=100,
            simulations_per_level=2000,
            confidence_level=0.95,
            rng=np.random.default_rng(42),
        )

        # Larger bankroll should have lower or equal ruin probability
        assert result_large.ruin_probability <= result_small.ruin_probability


class TestCalculateRiskOfRuin:
    """Tests for main calculate_risk_of_ruin function."""

    def test_basic_calculation(self) -> None:
        """Should calculate risk of ruin for all bankroll levels."""
        results = create_session_results(
            profits=[-10.0, 20.0, -5.0, 15.0, -20.0, 30.0, -10.0, 5.0, -15.0, 25.0] * 5
        )

        report = calculate_risk_of_ruin(
            session_results=results,
            bankroll_units=[20, 40, 60],
            base_bet=10.0,
            simulations_per_level=500,
            random_seed=42,
        )

        assert isinstance(report, RiskOfRuinReport)
        assert report.base_bet == 10.0
        assert len(report.results) == 3
        # Results should be sorted by bankroll units
        assert report.results[0].bankroll_units == 20
        assert report.results[1].bankroll_units == 40
        assert report.results[2].bankroll_units == 60

    def test_default_bankroll_units(self) -> None:
        """Should use default bankroll units when not specified."""
        results = create_session_results(profits=[10.0] * 50)

        report = calculate_risk_of_ruin(
            session_results=results,
            simulations_per_level=100,
            random_seed=42,
        )

        # Default is [20, 40, 60, 80, 100]
        assert len(report.results) == 5
        units = [r.bankroll_units for r in report.results]
        assert units == [20, 40, 60, 80, 100]

    def test_auto_infer_base_bet(self) -> None:
        """Should infer base bet from session data."""
        results = create_session_results(
            profits=[10.0] * 20,
            base_bet=15.0,  # 15 * 100 hands * 3 bets = 4500 per session
        )

        report = calculate_risk_of_ruin(
            session_results=results,
            bankroll_units=[50],
            simulations_per_level=100,
            random_seed=42,
        )

        # Should infer base_bet from total_wagered / (hands * 3)
        assert report.base_bet > 0

    def test_includes_analytical_estimates(self) -> None:
        """Should include analytical estimates when requested."""
        results = create_session_results(profits=[-5.0, 10.0] * 25)

        report = calculate_risk_of_ruin(
            session_results=results,
            bankroll_units=[50, 100],
            simulations_per_level=100,
            include_analytical=True,
            random_seed=42,
        )

        assert report.analytical_estimates is not None
        assert len(report.analytical_estimates) == 2

    def test_excludes_analytical_estimates(self) -> None:
        """Should exclude analytical estimates when not requested."""
        results = create_session_results(profits=[10.0] * 20)

        report = calculate_risk_of_ruin(
            session_results=results,
            bankroll_units=[50],
            simulations_per_level=100,
            include_analytical=False,
            random_seed=42,
        )

        assert report.analytical_estimates is None

    def test_reproducibility(self) -> None:
        """Same seed should produce same results."""
        results = create_session_results(profits=[-10.0, 20.0, -5.0, 15.0] * 10)

        report1 = calculate_risk_of_ruin(
            session_results=results,
            bankroll_units=[50],
            simulations_per_level=500,
            random_seed=12345,
        )

        report2 = calculate_risk_of_ruin(
            session_results=results,
            bankroll_units=[50],
            simulations_per_level=500,
            random_seed=12345,
        )

        assert (
            report1.results[0].ruin_probability == report2.results[0].ruin_probability
        )

    def test_empty_results_raises_error(self) -> None:
        """Empty results should raise ValueError."""
        with pytest.raises(ValueError, match="must not be empty"):
            calculate_risk_of_ruin(session_results=[])

    def test_insufficient_results_raises_error(self) -> None:
        """Less than 10 results should raise ValueError."""
        results = create_session_results(profits=[10.0] * 9)
        with pytest.raises(ValueError, match="At least 10 session results"):
            calculate_risk_of_ruin(session_results=results)

    def test_invalid_bankroll_units_raises_error(self) -> None:
        """Invalid bankroll units should raise ValueError."""
        results = create_session_results(profits=[10.0] * 20)
        with pytest.raises(ValueError, match="must be positive"):
            calculate_risk_of_ruin(
                session_results=results,
                bankroll_units=[-10, 50],
            )

    def test_invalid_confidence_level_raises_error(self) -> None:
        """Invalid confidence level should raise ValueError."""
        results = create_session_results(profits=[10.0] * 20)
        with pytest.raises(ValueError, match="must be between 0 and 1"):
            calculate_risk_of_ruin(
                session_results=results,
                confidence_level=1.5,
            )

    def test_negative_base_bet_raises_error(self) -> None:
        """Negative base bet should raise ValueError."""
        results = create_session_results(profits=[10.0] * 20)
        with pytest.raises(ValueError, match="base_bet must be positive"):
            calculate_risk_of_ruin(
                session_results=results,
                base_bet=-10.0,
            )

    def test_statistics_calculation(self) -> None:
        """Should calculate correct mean and std of session profits."""
        profits = [-100.0, 50.0, -30.0, 80.0, -20.0, 60.0, -40.0, 90.0, -10.0, 70.0]
        results = create_session_results(profits=profits)

        report = calculate_risk_of_ruin(
            session_results=results,
            bankroll_units=[50],
            simulations_per_level=100,
            random_seed=42,
        )

        expected_mean = mean(profits)
        expected_std = stdev(profits)

        assert abs(report.mean_session_profit - expected_mean) < 0.001
        assert abs(report.session_profit_std - expected_std) < 0.001


class TestFormatRiskOfRuinReport:
    """Tests for format_risk_of_ruin_report."""

    def test_basic_formatting(self) -> None:
        """Should format report as human-readable text."""
        ci = ConfidenceInterval(lower=0.05, upper=0.15, level=0.95)
        result = RiskOfRuinResult(
            bankroll_units=100,
            ruin_probability=0.10,
            confidence_interval=ci,
            half_bankroll_risk=0.25,
            quarter_bankroll_risk=0.40,
            sessions_simulated=10000,
        )
        report = RiskOfRuinReport(
            base_bet=10.0,
            starting_bankroll=1000.0,
            results=(result,),
            mean_session_profit=-5.0,
            session_profit_std=50.0,
            analytical_estimates=(0.12,),
        )

        formatted = format_risk_of_ruin_report(report)

        assert "Risk of Ruin Analysis" in formatted
        assert "Base Bet: $10.00" in formatted
        assert "100 units" in formatted
        assert "10.00%" in formatted
        assert "Analytical Estimate" in formatted

    def test_multiple_results(self) -> None:
        """Should format multiple bankroll levels."""
        ci = ConfidenceInterval(lower=0.05, upper=0.15, level=0.95)
        results = (
            RiskOfRuinResult(
                bankroll_units=50,
                ruin_probability=0.20,
                confidence_interval=ci,
                half_bankroll_risk=0.40,
                quarter_bankroll_risk=0.60,
                sessions_simulated=10000,
            ),
            RiskOfRuinResult(
                bankroll_units=100,
                ruin_probability=0.10,
                confidence_interval=ci,
                half_bankroll_risk=0.25,
                quarter_bankroll_risk=0.40,
                sessions_simulated=10000,
            ),
        )
        report = RiskOfRuinReport(
            base_bet=10.0,
            starting_bankroll=1000.0,
            results=results,
            mean_session_profit=-5.0,
            session_profit_std=50.0,
            analytical_estimates=None,
        )

        formatted = format_risk_of_ruin_report(report)

        assert "50 units" in formatted
        assert "100 units" in formatted

    def test_no_analytical_estimates(self) -> None:
        """Should handle missing analytical estimates."""
        ci = ConfidenceInterval(lower=0.05, upper=0.15, level=0.95)
        result = RiskOfRuinResult(
            bankroll_units=100,
            ruin_probability=0.10,
            confidence_interval=ci,
            half_bankroll_risk=0.25,
            quarter_bankroll_risk=0.40,
            sessions_simulated=10000,
        )
        report = RiskOfRuinReport(
            base_bet=10.0,
            starting_bankroll=1000.0,
            results=(result,),
            mean_session_profit=-5.0,
            session_profit_std=50.0,
            analytical_estimates=None,
        )

        formatted = format_risk_of_ruin_report(report)

        assert "Analytical Estimate" not in formatted


class TestConvergenceOfMonteCarloEstimates:
    """Tests for convergence of Monte Carlo estimates."""

    def test_more_simulations_narrower_ci(self) -> None:
        """More simulations should produce narrower confidence intervals."""
        results = create_session_results(
            profits=[-10.0, 20.0, -5.0, 15.0, -20.0, 30.0] * 10
        )

        report_small = calculate_risk_of_ruin(
            session_results=results,
            bankroll_units=[50],
            simulations_per_level=100,
            random_seed=42,
        )

        report_large = calculate_risk_of_ruin(
            session_results=results,
            bankroll_units=[50],
            simulations_per_level=5000,
            random_seed=42,
        )

        ci_width_small = (
            report_small.results[0].confidence_interval.upper
            - report_small.results[0].confidence_interval.lower
        )
        ci_width_large = (
            report_large.results[0].confidence_interval.upper
            - report_large.results[0].confidence_interval.lower
        )

        # Larger sample should have narrower CI
        assert ci_width_large < ci_width_small

    def test_estimate_stability(self) -> None:
        """Estimates should be relatively stable with large sample sizes."""
        results = create_session_results(
            profits=[-20.0, 10.0, -10.0, 30.0, -15.0, 25.0] * 10
        )

        # Run multiple times with different seeds
        estimates = []
        for seed in range(5):
            report = calculate_risk_of_ruin(
                session_results=results,
                bankroll_units=[50],
                simulations_per_level=2000,
                random_seed=seed * 100,
            )
            estimates.append(report.results[0].ruin_probability)

        # All estimates should be within reasonable range of each other
        estimate_std = np.std(estimates)
        assert estimate_std < 0.05  # Standard deviation should be small


class TestKnownRiskScenarios:
    """Tests with known risk scenarios for validation."""

    def test_guaranteed_loss_scenario(self) -> None:
        """Sessions that always lose should have 100% ruin."""
        # All sessions lose exactly $100
        results = create_session_results(profits=[-100.0] * 20)

        report = calculate_risk_of_ruin(
            session_results=results,
            bankroll_units=[20],  # 200 bankroll
            base_bet=10.0,
            simulations_per_level=500,
            random_seed=42,
        )

        # Should be very high ruin probability (close to 100%)
        assert report.results[0].ruin_probability > 0.99

    def test_guaranteed_win_scenario(self) -> None:
        """Sessions that always win should have 0% ruin."""
        # All sessions win exactly $100
        results = create_session_results(profits=[100.0] * 20)

        report = calculate_risk_of_ruin(
            session_results=results,
            bankroll_units=[20],
            base_bet=10.0,
            simulations_per_level=500,
            random_seed=42,
        )

        # Should be zero ruin probability
        assert report.results[0].ruin_probability == 0.0
        assert report.results[0].half_bankroll_risk == 0.0
        assert report.results[0].quarter_bankroll_risk == 0.0

    def test_break_even_high_variance(self) -> None:
        """Break-even with high variance should have moderate ruin."""
        # Balanced wins and losses with high variance
        profits = [-500.0, 500.0] * 25
        results = create_session_results(profits=profits)

        report = calculate_risk_of_ruin(
            session_results=results,
            bankroll_units=[50],
            base_bet=10.0,
            simulations_per_level=1000,
            random_seed=42,
        )

        # Should have some ruin risk due to variance
        assert report.results[0].ruin_probability > 0


class TestNumericalStability:
    """Tests for numerical stability with edge cases."""

    def test_very_small_profits(self) -> None:
        """Should handle very small profit values."""
        profits = [0.01, -0.01, 0.02, -0.02, 0.01] * 10
        results = create_session_results(profits=profits)

        report = calculate_risk_of_ruin(
            session_results=results,
            bankroll_units=[100],
            base_bet=0.01,
            simulations_per_level=100,
            random_seed=42,
        )

        assert not math.isnan(report.results[0].ruin_probability)

    def test_very_large_profits(self) -> None:
        """Should handle very large profit values."""
        profits = [1e6, -1e6, 2e6, -0.5e6, 1e6] * 10
        results = create_session_results(profits=profits, starting_bankroll=1e7)

        report = calculate_risk_of_ruin(
            session_results=results,
            bankroll_units=[100],
            base_bet=1000.0,
            simulations_per_level=100,
            random_seed=42,
        )

        assert not math.isnan(report.results[0].ruin_probability)

    def test_all_same_profit(self) -> None:
        """Should handle constant profit values."""
        results = create_session_results(profits=[50.0] * 20)

        report = calculate_risk_of_ruin(
            session_results=results,
            bankroll_units=[50],
            simulations_per_level=100,
            random_seed=42,
        )

        # All positive constant should mean no ruin
        assert report.results[0].ruin_probability == 0.0

    def test_all_same_loss(self) -> None:
        """Should handle constant loss values."""
        results = create_session_results(profits=[-50.0] * 20)

        report = calculate_risk_of_ruin(
            session_results=results,
            bankroll_units=[50],  # 500 bankroll
            base_bet=10.0,
            simulations_per_level=100,
            random_seed=42,
        )

        # Constant loss should mean certain ruin
        assert report.results[0].ruin_probability == 1.0
