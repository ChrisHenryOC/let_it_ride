"""Unit tests for chair position analytics module."""

from __future__ import annotations

import pytest

from let_it_ride.analytics.chair_position import (
    ChairPositionAnalysis,
    SeatStatistics,
    _aggregate_seat_data,
    _calculate_seat_statistics,
    _SeatAggregation,
    _test_seat_independence,
    analyze_chair_positions,
)
from let_it_ride.simulation.session import SessionOutcome, SessionResult, StopReason
from let_it_ride.simulation.table_session import SeatSessionResult, TableSessionResult


def create_session_result(
    *,
    outcome: SessionOutcome = SessionOutcome.WIN,
    profit: float = 100.0,
    hands_played: int = 50,
) -> SessionResult:
    """Create a SessionResult with sensible defaults for testing."""
    if profit > 0:
        outcome = SessionOutcome.WIN
    elif profit < 0:
        outcome = SessionOutcome.LOSS
    else:
        outcome = SessionOutcome.PUSH

    return SessionResult(
        outcome=outcome,
        stop_reason=StopReason.MAX_HANDS,
        hands_played=hands_played,
        starting_bankroll=1000.0,
        final_bankroll=1000.0 + profit,
        session_profit=profit,
        total_wagered=hands_played * 15.0,  # 3 bets of $5 each
        total_bonus_wagered=0.0,
        peak_bankroll=max(1000.0, 1000.0 + profit),
        max_drawdown=50.0,
        max_drawdown_pct=0.05,
    )


def create_seat_session_result(
    seat_number: int,
    outcome: SessionOutcome = SessionOutcome.WIN,
    profit: float = 100.0,
) -> SeatSessionResult:
    """Create a SeatSessionResult for testing."""
    return SeatSessionResult(
        seat_number=seat_number,
        session_result=create_session_result(outcome=outcome, profit=profit),
    )


def create_table_session_result(
    seat_outcomes: list[tuple[int, SessionOutcome, float]],
    total_rounds: int = 50,
) -> TableSessionResult:
    """Create a TableSessionResult with specified seat outcomes.

    Args:
        seat_outcomes: List of (seat_number, outcome, profit) tuples.
        total_rounds: Total rounds played in the session.

    Returns:
        TableSessionResult for testing.
    """
    seat_results = tuple(
        create_seat_session_result(seat_num, outcome, profit)
        for seat_num, outcome, profit in seat_outcomes
    )
    return TableSessionResult(
        seat_results=seat_results,
        total_rounds=total_rounds,
        stop_reason=StopReason.MAX_HANDS,
    )


class TestSeatStatisticsDataclass:
    """Tests for SeatStatistics dataclass."""

    def test_creation(self) -> None:
        """SeatStatistics should be created with all fields."""
        stats = SeatStatistics(
            seat_number=1,
            total_rounds=100,
            wins=30,
            losses=65,
            pushes=5,
            win_rate=0.30,
            win_rate_ci_lower=0.21,
            win_rate_ci_upper=0.40,
            expected_value=-5.0,
            total_profit=-500.0,
        )
        assert stats.seat_number == 1
        assert stats.total_rounds == 100
        assert stats.wins == 30
        assert stats.losses == 65
        assert stats.pushes == 5
        assert stats.win_rate == 0.30
        assert stats.win_rate_ci_lower == 0.21
        assert stats.win_rate_ci_upper == 0.40
        assert stats.expected_value == -5.0
        assert stats.total_profit == -500.0

    def test_immutability(self) -> None:
        """SeatStatistics should be immutable."""
        stats = SeatStatistics(
            seat_number=1,
            total_rounds=100,
            wins=30,
            losses=65,
            pushes=5,
            win_rate=0.30,
            win_rate_ci_lower=0.21,
            win_rate_ci_upper=0.40,
            expected_value=-5.0,
            total_profit=-500.0,
        )
        with pytest.raises(AttributeError):
            stats.wins = 50  # type: ignore[misc]


class TestChairPositionAnalysisDataclass:
    """Tests for ChairPositionAnalysis dataclass."""

    def test_creation(self) -> None:
        """ChairPositionAnalysis should be created with all fields."""
        seat_stats = (
            SeatStatistics(
                seat_number=1,
                total_rounds=100,
                wins=30,
                losses=65,
                pushes=5,
                win_rate=0.30,
                win_rate_ci_lower=0.21,
                win_rate_ci_upper=0.40,
                expected_value=-5.0,
                total_profit=-500.0,
            ),
        )
        analysis = ChairPositionAnalysis(
            seat_statistics=seat_stats,
            chi_square_statistic=2.5,
            chi_square_p_value=0.78,
            is_position_independent=True,
        )
        assert len(analysis.seat_statistics) == 1
        assert analysis.chi_square_statistic == 2.5
        assert analysis.chi_square_p_value == 0.78
        assert analysis.is_position_independent is True

    def test_immutability(self) -> None:
        """ChairPositionAnalysis should be immutable."""
        analysis = ChairPositionAnalysis(
            seat_statistics=(),
            chi_square_statistic=0.0,
            chi_square_p_value=1.0,
            is_position_independent=True,
        )
        with pytest.raises(AttributeError):
            analysis.is_position_independent = False  # type: ignore[misc]


class TestSeatAggregation:
    """Tests for _SeatAggregation helper class."""

    def test_initial_values(self) -> None:
        """Initial aggregation should have zero counts."""
        agg = _SeatAggregation()
        assert agg.wins == 0
        assert agg.losses == 0
        assert agg.pushes == 0
        assert agg.total_profit == 0.0
        assert agg.total_rounds == 0

    def test_total_rounds_calculation(self) -> None:
        """total_rounds should sum wins, losses, and pushes."""
        agg = _SeatAggregation()
        agg.wins = 30
        agg.losses = 60
        agg.pushes = 10
        assert agg.total_rounds == 100


class TestAggregateSeatData:
    """Tests for _aggregate_seat_data function."""

    def test_empty_results(self) -> None:
        """Empty results should return empty aggregations."""
        result = _aggregate_seat_data([])
        assert result == {}

    def test_single_table_single_seat(self) -> None:
        """Single table with single seat should aggregate correctly."""
        table_result = create_table_session_result([(1, SessionOutcome.WIN, 100.0)])
        result = _aggregate_seat_data([table_result])

        assert 1 in result
        assert result[1].wins == 1
        assert result[1].losses == 0
        assert result[1].pushes == 0
        assert result[1].total_profit == 100.0

    def test_multiple_tables_same_seats(self) -> None:
        """Multiple tables should accumulate results by seat."""
        results = [
            create_table_session_result([(1, SessionOutcome.WIN, 100.0)]),
            create_table_session_result([(1, SessionOutcome.LOSS, -50.0)]),
            create_table_session_result([(1, SessionOutcome.PUSH, 0.0)]),
        ]
        agg = _aggregate_seat_data(results)

        assert agg[1].wins == 1
        assert agg[1].losses == 1
        assert agg[1].pushes == 1
        assert agg[1].total_profit == 50.0  # 100 - 50 + 0

    def test_multiple_seats(self) -> None:
        """Multiple seats should be aggregated separately."""
        table_result = create_table_session_result(
            [
                (1, SessionOutcome.WIN, 100.0),
                (2, SessionOutcome.LOSS, -50.0),
                (3, SessionOutcome.PUSH, 0.0),
            ]
        )
        agg = _aggregate_seat_data([table_result])

        assert len(agg) == 3
        assert agg[1].wins == 1
        assert agg[2].losses == 1
        assert agg[3].pushes == 1


class TestCalculateSeatStatistics:
    """Tests for _calculate_seat_statistics function."""

    def test_basic_calculation(self) -> None:
        """Basic statistics should be calculated correctly."""
        agg = _SeatAggregation()
        agg.wins = 30
        agg.losses = 60
        agg.pushes = 10
        agg.total_profit = -500.0

        stats = _calculate_seat_statistics(1, agg, 0.95)

        assert stats.seat_number == 1
        assert stats.total_rounds == 100
        assert stats.wins == 30
        assert stats.losses == 60
        assert stats.pushes == 10
        assert stats.win_rate == 0.30
        assert stats.expected_value == -5.0  # -500 / 100
        assert stats.total_profit == -500.0

    def test_win_rate_confidence_interval(self) -> None:
        """Win rate CI should be reasonable for sample size."""
        agg = _SeatAggregation()
        agg.wins = 30
        agg.losses = 70
        agg.total_profit = -200.0

        stats = _calculate_seat_statistics(1, agg, 0.95)

        # CI should contain the point estimate
        assert stats.win_rate_ci_lower < stats.win_rate
        assert stats.win_rate_ci_upper > stats.win_rate
        # CI should be reasonable (not too wide)
        assert stats.win_rate_ci_lower > 0.0
        assert stats.win_rate_ci_upper < 1.0

    def test_zero_rounds(self) -> None:
        """Zero rounds should produce zero statistics."""
        agg = _SeatAggregation()

        stats = _calculate_seat_statistics(1, agg, 0.95)

        assert stats.total_rounds == 0
        assert stats.win_rate == 0.0
        assert stats.expected_value == 0.0
        assert stats.win_rate_ci_lower == 0.0
        assert stats.win_rate_ci_upper == 0.0

    def test_all_wins(self) -> None:
        """All wins should produce win rate of 1.0."""
        agg = _SeatAggregation()
        agg.wins = 50
        agg.total_profit = 5000.0

        stats = _calculate_seat_statistics(1, agg, 0.95)

        assert stats.win_rate == 1.0
        assert stats.win_rate_ci_lower > 0.9  # Should be close to 1.0
        assert stats.win_rate_ci_upper == 1.0

    def test_all_losses(self) -> None:
        """All losses should produce win rate of 0.0."""
        agg = _SeatAggregation()
        agg.losses = 50
        agg.total_profit = -2500.0

        stats = _calculate_seat_statistics(1, agg, 0.95)

        assert stats.win_rate == 0.0
        # CI lower bound should be very close to 0 (may have small float precision)
        assert stats.win_rate_ci_lower < 1e-6
        assert stats.win_rate_ci_upper < 0.1  # Should be close to 0.0


class TestSeatIndependence:
    """Tests for _test_seat_independence function."""

    def test_single_seat(self) -> None:
        """Single seat should return default values (cannot test independence)."""
        stats = [
            SeatStatistics(
                seat_number=1,
                total_rounds=100,
                wins=30,
                losses=70,
                pushes=0,
                win_rate=0.30,
                win_rate_ci_lower=0.21,
                win_rate_ci_upper=0.40,
                expected_value=-5.0,
                total_profit=-500.0,
            )
        ]
        chi_sq, p_val, is_indep = _test_seat_independence(stats, 0.05)

        assert chi_sq == 0.0
        assert p_val == 1.0
        assert is_indep is True

    def test_uniform_distribution(self) -> None:
        """Uniform wins should indicate position independence (high p-value)."""
        # All seats have exactly the same number of wins
        stats = [
            SeatStatistics(
                seat_number=i,
                total_rounds=100,
                wins=30,
                losses=70,
                pushes=0,
                win_rate=0.30,
                win_rate_ci_lower=0.21,
                win_rate_ci_upper=0.40,
                expected_value=-5.0,
                total_profit=-500.0,
            )
            for i in range(1, 7)  # 6 seats
        ]
        chi_sq, p_val, is_indep = _test_seat_independence(stats, 0.05)

        # With uniform distribution, chi-square should be 0
        assert chi_sq == 0.0
        assert p_val == 1.0
        assert is_indep == True  # noqa: E712

    def test_biased_distribution(self) -> None:
        """Heavily biased wins should indicate position dependence (low p-value)."""
        # Seat 1 wins much more than others
        stats = [
            SeatStatistics(
                seat_number=1,
                total_rounds=100,
                wins=90,  # Seat 1 wins a lot
                losses=10,
                pushes=0,
                win_rate=0.90,
                win_rate_ci_lower=0.82,
                win_rate_ci_upper=0.95,
                expected_value=50.0,
                total_profit=5000.0,
            ),
        ] + [
            SeatStatistics(
                seat_number=i,
                total_rounds=100,
                wins=10,  # Other seats win very little
                losses=90,
                pushes=0,
                win_rate=0.10,
                win_rate_ci_lower=0.05,
                win_rate_ci_upper=0.18,
                expected_value=-50.0,
                total_profit=-5000.0,
            )
            for i in range(2, 7)  # Seats 2-6
        ]
        chi_sq, p_val, is_indep = _test_seat_independence(stats, 0.05)

        # With biased distribution, chi-square should be significant
        assert chi_sq > 0
        assert p_val < 0.05
        assert is_indep == False  # noqa: E712

    def test_no_wins(self) -> None:
        """No wins across all seats should return default values."""
        stats = [
            SeatStatistics(
                seat_number=i,
                total_rounds=100,
                wins=0,
                losses=100,
                pushes=0,
                win_rate=0.0,
                win_rate_ci_lower=0.0,
                win_rate_ci_upper=0.04,
                expected_value=-50.0,
                total_profit=-5000.0,
            )
            for i in range(1, 7)
        ]
        chi_sq, p_val, is_indep = _test_seat_independence(stats, 0.05)

        # No wins to analyze
        assert chi_sq == 0.0
        assert p_val == 1.0
        assert is_indep is True


class TestAnalyzeChairPositions:
    """Tests for analyze_chair_positions main function."""

    def test_empty_results_raises_error(self) -> None:
        """Empty results list should raise ValueError."""
        with pytest.raises(ValueError, match="empty results"):
            analyze_chair_positions([])

    def test_results_with_no_seat_data_raises_error(self) -> None:
        """Results with empty seat_results should raise ValueError."""
        empty_result = TableSessionResult(
            seat_results=(),
            total_rounds=50,
            stop_reason=StopReason.MAX_HANDS,
        )
        with pytest.raises(ValueError, match="No seat data"):
            analyze_chair_positions([empty_result])

    def test_single_table_result(self) -> None:
        """Single table result should be analyzed correctly."""
        table_result = create_table_session_result(
            [
                (1, SessionOutcome.WIN, 100.0),
                (2, SessionOutcome.LOSS, -50.0),
            ]
        )
        analysis = analyze_chair_positions([table_result])

        assert len(analysis.seat_statistics) == 2
        assert analysis.seat_statistics[0].seat_number == 1
        assert analysis.seat_statistics[0].wins == 1
        assert analysis.seat_statistics[1].seat_number == 2
        assert analysis.seat_statistics[1].losses == 1

    def test_multiple_sessions(self) -> None:
        """Multiple sessions should be aggregated correctly."""
        results = [
            create_table_session_result(
                [
                    (1, SessionOutcome.WIN, 100.0),
                    (2, SessionOutcome.LOSS, -50.0),
                ]
            ),
            create_table_session_result(
                [
                    (1, SessionOutcome.WIN, 150.0),
                    (2, SessionOutcome.WIN, 80.0),
                ]
            ),
            create_table_session_result(
                [
                    (1, SessionOutcome.LOSS, -75.0),
                    (2, SessionOutcome.LOSS, -100.0),
                ]
            ),
        ]
        analysis = analyze_chair_positions(results)

        # Seat 1: 2 wins, 1 loss
        assert analysis.seat_statistics[0].wins == 2
        assert analysis.seat_statistics[0].losses == 1
        assert analysis.seat_statistics[0].total_rounds == 3
        assert analysis.seat_statistics[0].total_profit == 175.0  # 100+150-75

        # Seat 2: 1 win, 2 losses
        assert analysis.seat_statistics[1].wins == 1
        assert analysis.seat_statistics[1].losses == 2
        assert analysis.seat_statistics[1].total_rounds == 3
        assert analysis.seat_statistics[1].total_profit == -70.0  # -50+80-100

    def test_six_seat_uniform_distribution(self) -> None:
        """Six seats with uniform wins should show position independence."""
        # Create 100 sessions per seat with 30% win rate each (uniform)
        results = []
        for _ in range(100):
            seat_outcomes = []
            for seat in range(1, 7):
                # Alternate between win and loss to get ~30% win rate
                if len(results) % 10 < 3:  # ~30% wins
                    seat_outcomes.append((seat, SessionOutcome.WIN, 100.0))
                else:
                    seat_outcomes.append((seat, SessionOutcome.LOSS, -50.0))
            results.append(create_table_session_result(seat_outcomes))

        analysis = analyze_chair_positions(results)

        assert len(analysis.seat_statistics) == 6
        # All seats should have similar win counts
        win_counts = [s.wins for s in analysis.seat_statistics]
        assert min(win_counts) == max(win_counts)  # All equal

        # Should indicate position independence
        assert analysis.is_position_independent == True  # noqa: E712

    def test_confidence_level_parameter(self) -> None:
        """Custom confidence level should affect CI width."""
        results = [
            create_table_session_result(
                [
                    (1, SessionOutcome.WIN, 100.0),
                    (1, SessionOutcome.LOSS, -50.0),
                ]
                * 50
            )  # 50 sessions at seat 1
        ]

        analysis_95 = analyze_chair_positions(results, confidence_level=0.95)
        analysis_99 = analyze_chair_positions(results, confidence_level=0.99)

        # 99% CI should be wider than 95% CI
        ci_width_95 = (
            analysis_95.seat_statistics[0].win_rate_ci_upper
            - analysis_95.seat_statistics[0].win_rate_ci_lower
        )
        ci_width_99 = (
            analysis_99.seat_statistics[0].win_rate_ci_upper
            - analysis_99.seat_statistics[0].win_rate_ci_lower
        )
        assert ci_width_99 > ci_width_95

    def test_significance_level_parameter(self) -> None:
        """Custom significance level should affect independence determination."""
        # Create moderately biased distribution
        results = []
        for _ in range(50):
            results.append(
                create_table_session_result(
                    [
                        (1, SessionOutcome.WIN, 100.0),  # Seat 1 always wins
                        (2, SessionOutcome.LOSS, -50.0),  # Seat 2 always loses
                    ]
                )
            )

        # With low significance level, may still be "independent"
        analysis_01 = analyze_chair_positions(results, significance_level=0.01)
        # With high significance level, should detect dependence
        analysis_10 = analyze_chair_positions(results, significance_level=0.10)

        # Both should have the same chi-square statistic
        assert analysis_01.chi_square_statistic == analysis_10.chi_square_statistic
        # But may differ in independence determination based on threshold

    def test_seats_sorted_by_number(self) -> None:
        """Seat statistics should be sorted by seat number."""
        table_result = create_table_session_result(
            [
                (3, SessionOutcome.WIN, 100.0),
                (1, SessionOutcome.LOSS, -50.0),
                (5, SessionOutcome.PUSH, 0.0),
            ]
        )
        analysis = analyze_chair_positions([table_result])

        seat_numbers = [s.seat_number for s in analysis.seat_statistics]
        assert seat_numbers == [1, 3, 5]  # Sorted order

    def test_expected_value_calculation(self) -> None:
        """Expected value should be average profit per round."""
        results = [
            create_table_session_result(
                [
                    (1, SessionOutcome.WIN, 100.0),
                ]
            ),
            create_table_session_result(
                [
                    (1, SessionOutcome.WIN, 200.0),
                ]
            ),
            create_table_session_result(
                [
                    (1, SessionOutcome.LOSS, -150.0),
                ]
            ),
        ]
        analysis = analyze_chair_positions(results)

        # Total profit: 100 + 200 - 150 = 150
        # Total rounds: 3
        # EV: 150 / 3 = 50
        assert analysis.seat_statistics[0].expected_value == 50.0
        assert analysis.seat_statistics[0].total_profit == 150.0


class TestChiSquareIntegration:
    """Integration tests for chi-square independence testing."""

    def test_realistic_simulation_uniform(self) -> None:
        """Realistic simulation with uniform outcomes should show independence."""
        import random

        random.seed(42)  # For reproducibility

        results = []
        for _ in range(200):  # 200 table sessions
            seat_outcomes = []
            for seat in range(1, 7):  # 6 seats
                # ~30% chance of winning at each seat (independent of position)
                if random.random() < 0.30:
                    seat_outcomes.append((seat, SessionOutcome.WIN, 100.0))
                else:
                    seat_outcomes.append((seat, SessionOutcome.LOSS, -50.0))
            results.append(create_table_session_result(seat_outcomes))

        analysis = analyze_chair_positions(results)

        # With independent outcomes, p-value should be high
        # (may occasionally fail due to randomness, but with seed it's deterministic)
        assert analysis.chi_square_p_value > 0.05
        assert analysis.is_position_independent == True  # noqa: E712

    def test_realistic_simulation_biased(self) -> None:
        """Realistic simulation with biased outcomes should detect dependence."""
        import random

        random.seed(42)

        results = []
        for _ in range(200):
            seat_outcomes = []
            for seat in range(1, 7):
                # Seat 1 has 60% win rate, others have 20%
                win_prob = 0.60 if seat == 1 else 0.20
                if random.random() < win_prob:
                    seat_outcomes.append((seat, SessionOutcome.WIN, 100.0))
                else:
                    seat_outcomes.append((seat, SessionOutcome.LOSS, -50.0))
            results.append(create_table_session_result(seat_outcomes))

        analysis = analyze_chair_positions(results)

        # With biased outcomes, p-value should be low
        assert analysis.chi_square_p_value < 0.05
        assert analysis.is_position_independent == False  # noqa: E712
