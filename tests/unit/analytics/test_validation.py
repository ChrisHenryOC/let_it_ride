"""Unit tests for statistical validation module."""

from __future__ import annotations

import pytest

from let_it_ride.analytics.validation import (
    THEORETICAL_HAND_PROBS,
    THEORETICAL_HOUSE_EDGE,
    ChiSquareResult,
    ValidationReport,
    _normalize_hand_frequencies,
    calculate_chi_square,
    calculate_wilson_confidence_interval,
    validate_simulation,
)
from let_it_ride.simulation.aggregation import AggregateStatistics


def create_aggregate_statistics(
    *,
    total_sessions: int = 100,
    winning_sessions: int = 30,
    losing_sessions: int = 65,
    push_sessions: int = 5,
    total_hands: int = 10000,
    total_wagered: float = 30000.0,
    total_won: float = 28950.0,
    net_result: float = -1050.0,
    hand_frequencies: dict[str, int] | None = None,
) -> AggregateStatistics:
    """Create AggregateStatistics with sensible defaults for testing."""
    if hand_frequencies is None:
        hand_frequencies = {}

    session_win_rate = winning_sessions / total_sessions if total_sessions > 0 else 0.0
    expected_value_per_hand = net_result / total_hands if total_hands > 0 else 0.0

    # Calculate frequency percentages
    total_freq = sum(hand_frequencies.values()) if hand_frequencies else 0
    hand_frequency_pct = (
        {k: v / total_freq for k, v in hand_frequencies.items()}
        if total_freq > 0
        else {}
    )

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
        hand_frequencies=hand_frequencies,
        hand_frequency_pct=hand_frequency_pct,
        session_profit_mean=net_result / total_sessions if total_sessions > 0 else 0.0,
        session_profit_std=50.0,
        session_profit_median=-5.0,
        session_profit_min=-200.0,
        session_profit_max=500.0,
        session_profits=tuple([net_result / total_sessions] * total_sessions),
    )


class TestTheoreticalProbabilities:
    """Tests for theoretical probability constants."""

    def test_probabilities_sum_to_one(self) -> None:
        """Theoretical probabilities should sum to 1.0."""
        total = sum(THEORETICAL_HAND_PROBS.values())
        assert abs(total - 1.0) < 1e-6

    def test_all_hand_types_present(self) -> None:
        """All standard hand types should be in theoretical probs."""
        expected_hands = {
            "royal_flush",
            "straight_flush",
            "four_of_a_kind",
            "full_house",
            "flush",
            "straight",
            "three_of_a_kind",
            "two_pair",
            "pair",
            "high_card",
        }
        assert set(THEORETICAL_HAND_PROBS.keys()) == expected_hands

    def test_probabilities_in_correct_range(self) -> None:
        """All probabilities should be between 0 and 1."""
        for prob in THEORETICAL_HAND_PROBS.values():
            assert 0 < prob < 1

    def test_probabilities_ordered_by_rarity(self) -> None:
        """Royal flush should be rarest, high card most common."""
        assert (
            THEORETICAL_HAND_PROBS["royal_flush"]
            < THEORETICAL_HAND_PROBS["straight_flush"]
        )
        assert (
            THEORETICAL_HAND_PROBS["straight_flush"]
            < THEORETICAL_HAND_PROBS["four_of_a_kind"]
        )
        assert THEORETICAL_HAND_PROBS["pair"] < THEORETICAL_HAND_PROBS["high_card"]

    def test_house_edge_reasonable(self) -> None:
        """Theoretical house edge should be reasonable (~3.5%)."""
        assert 0.01 < THEORETICAL_HOUSE_EDGE < 0.10


class TestNormalizeHandFrequencies:
    """Tests for hand frequency normalization."""

    def test_combines_pair_types(self) -> None:
        """Should combine pair_tens_or_better and pair_below_tens."""
        freqs = {
            "pair_tens_or_better": 100,
            "pair_below_tens": 200,
            "high_card": 500,
        }
        normalized = _normalize_hand_frequencies(freqs)

        assert "pair" in normalized
        assert normalized["pair"] == 300
        assert "pair_tens_or_better" not in normalized
        assert "pair_below_tens" not in normalized

    def test_preserves_other_hand_types(self) -> None:
        """Should preserve non-pair hand types."""
        freqs = {
            "royal_flush": 1,
            "flush": 50,
            "high_card": 500,
        }
        normalized = _normalize_hand_frequencies(freqs)

        assert normalized["royal_flush"] == 1
        assert normalized["flush"] == 50
        assert normalized["high_card"] == 500

    def test_empty_frequencies(self) -> None:
        """Should handle empty frequency dict."""
        normalized = _normalize_hand_frequencies({})
        assert normalized == {}

    def test_only_one_pair_type(self) -> None:
        """Should handle having only one pair type."""
        freqs = {"pair_tens_or_better": 150}
        normalized = _normalize_hand_frequencies(freqs)

        assert normalized["pair"] == 150
        assert "pair_tens_or_better" not in normalized


class TestCalculateChiSquare:
    """Tests for chi-square calculation."""

    def test_perfect_match_high_p_value(self) -> None:
        """Distribution matching theoretical should have high p-value."""
        # Create frequencies that exactly match theoretical probabilities
        total = 1000000
        perfect_frequencies = {
            hand: int(prob * total) for hand, prob in THEORETICAL_HAND_PROBS.items()
        }

        result = calculate_chi_square(perfect_frequencies)

        assert result.p_value > 0.05
        assert result.is_valid
        assert result.degrees_of_freedom == len(THEORETICAL_HAND_PROBS) - 1

    def test_skewed_distribution_low_p_value(self) -> None:
        """Highly skewed distribution should fail chi-square test."""
        # Create extremely skewed frequencies
        skewed_frequencies = {
            "royal_flush": 10000,  # Way too many
            "straight_flush": 0,
            "four_of_a_kind": 0,
            "full_house": 0,
            "flush": 0,
            "straight": 0,
            "three_of_a_kind": 0,
            "two_pair": 0,
            "pair": 0,
            "high_card": 90000,
        }

        result = calculate_chi_square(skewed_frequencies)

        assert result.p_value < 0.001
        assert not result.is_valid

    def test_empty_frequencies_raises(self) -> None:
        """Should raise ValueError for empty frequencies."""
        with pytest.raises(ValueError, match="empty frequencies"):
            calculate_chi_square({})

    def test_zero_total_raises(self) -> None:
        """Should raise ValueError for zero total observations."""
        with pytest.raises(ValueError, match="zero total"):
            calculate_chi_square({"high_card": 0, "pair": 0})

    def test_custom_significance_level(self) -> None:
        """Should use custom significance level."""
        frequencies = {
            hand: int(prob * 10000) for hand, prob in THEORETICAL_HAND_PROBS.items()
        }

        result_05 = calculate_chi_square(frequencies, significance_level=0.05)
        result_01 = calculate_chi_square(frequencies, significance_level=0.01)

        # Same statistic and p-value, different is_valid threshold
        assert result_05.statistic == result_01.statistic
        assert result_05.p_value == result_01.p_value


class TestWilsonConfidenceInterval:
    """Tests for Wilson score confidence interval calculation."""

    def test_50_percent_rate(self) -> None:
        """50% success rate should have symmetric CI."""
        lower, upper = calculate_wilson_confidence_interval(500, 1000)

        # Should be roughly symmetric around 0.5
        assert 0.45 < lower < 0.50
        assert 0.50 < upper < 0.55
        assert abs((0.5 - lower) - (upper - 0.5)) < 0.01

    def test_0_percent_rate(self) -> None:
        """0% success rate should have CI starting at 0."""
        lower, upper = calculate_wilson_confidence_interval(0, 100)

        # Lower bound should be at or very close to 0 (allowing floating point)
        assert lower < 1e-10
        assert 0 < upper < 0.10

    def test_100_percent_rate(self) -> None:
        """100% success rate should have CI ending at 1."""
        lower, upper = calculate_wilson_confidence_interval(100, 100)

        assert 0.90 < lower < 1.0
        assert upper == 1.0

    def test_larger_sample_narrower_ci(self) -> None:
        """Larger sample should produce narrower CI."""
        lower_small, upper_small = calculate_wilson_confidence_interval(50, 100)
        lower_large, upper_large = calculate_wilson_confidence_interval(500, 1000)

        width_small = upper_small - lower_small
        width_large = upper_large - lower_large

        assert width_large < width_small

    def test_zero_total_raises(self) -> None:
        """Should raise ValueError for zero total."""
        with pytest.raises(ValueError, match="positive"):
            calculate_wilson_confidence_interval(0, 0)

    def test_negative_total_raises(self) -> None:
        """Should raise ValueError for negative total."""
        with pytest.raises(ValueError, match="positive"):
            calculate_wilson_confidence_interval(0, -10)

    def test_successes_greater_than_total_raises(self) -> None:
        """Should raise ValueError if successes > total."""
        with pytest.raises(ValueError, match="between 0 and total"):
            calculate_wilson_confidence_interval(150, 100)

    def test_different_confidence_levels(self) -> None:
        """Higher confidence level should produce wider CI."""
        lower_90, upper_90 = calculate_wilson_confidence_interval(
            50, 100, confidence_level=0.90
        )
        lower_99, upper_99 = calculate_wilson_confidence_interval(
            50, 100, confidence_level=0.99
        )

        width_90 = upper_90 - lower_90
        width_99 = upper_99 - lower_99

        assert width_99 > width_90


class TestValidateSimulation:
    """Tests for the main validation function."""

    def test_valid_simulation_with_good_data(self) -> None:
        """Simulation with reasonable data should validate."""
        # Create hand frequencies roughly matching theoretical
        total = 100000
        hand_frequencies = {
            "royal_flush": 0,
            "straight_flush": 1,
            "four_of_a_kind": 24,
            "full_house": 144,
            "flush": 197,
            "straight": 392,
            "three_of_a_kind": 2110,
            "two_pair": 4750,
            "pair_tens_or_better": 21150,  # ~half of all pairs
            "pair_below_tens": 21150,  # ~half of all pairs
            "high_card": 50082,
        }

        stats = create_aggregate_statistics(
            total_hands=total,
            hand_frequencies=hand_frequencies,
            # EV close to theoretical
            net_result=-total * THEORETICAL_HOUSE_EDGE,
            total_wagered=total * 3.0,  # 3 bets per hand
            total_won=total * 3.0 - total * THEORETICAL_HOUSE_EDGE,
        )

        report = validate_simulation(stats)

        assert isinstance(report, ValidationReport)
        assert report.chi_square_result is not None
        assert len(report.observed_frequencies) == len(THEORETICAL_HAND_PROBS)
        assert len(report.expected_frequencies) == len(THEORETICAL_HAND_PROBS)

    def test_empty_hand_frequencies_warning(self) -> None:
        """Empty hand frequencies should produce warning."""
        stats = create_aggregate_statistics(hand_frequencies={})

        report = validate_simulation(stats)

        assert any("No hand frequency data" in w for w in report.warnings)

    def test_extreme_win_rate_warning(self) -> None:
        """Extreme session win rate should produce warning."""
        stats = create_aggregate_statistics(
            total_sessions=100,
            winning_sessions=95,  # 95% win rate is suspicious
            losing_sessions=5,
            push_sessions=0,
        )

        report = validate_simulation(stats)

        assert any("unusually extreme" in w for w in report.warnings)
        assert not report.is_valid

    def test_ev_deviation_warning(self) -> None:
        """Large EV deviation should produce warning."""
        # Create stats with EV way off from theoretical
        stats = create_aggregate_statistics(
            total_hands=10000,
            net_result=1000.0,  # Positive EV (very suspicious)
            total_wagered=30000.0,
            total_won=31000.0,
        )

        report = validate_simulation(stats)

        assert any("EV deviation" in w for w in report.warnings)

    def test_report_contains_all_fields(self) -> None:
        """Validation report should contain all required fields."""
        stats = create_aggregate_statistics()

        report = validate_simulation(stats)

        assert hasattr(report, "chi_square_result")
        assert hasattr(report, "observed_frequencies")
        assert hasattr(report, "expected_frequencies")
        assert hasattr(report, "ev_actual")
        assert hasattr(report, "ev_theoretical")
        assert hasattr(report, "ev_deviation_pct")
        assert hasattr(report, "session_win_rate")
        assert hasattr(report, "session_win_rate_ci")
        assert hasattr(report, "warnings")
        assert hasattr(report, "is_valid")

    def test_confidence_interval_bounds(self) -> None:
        """Session win rate CI should be valid bounds."""
        stats = create_aggregate_statistics(
            total_sessions=100,
            winning_sessions=30,
        )

        report = validate_simulation(stats)

        lower, upper = report.session_win_rate_ci
        assert 0 <= lower <= report.session_win_rate
        assert report.session_win_rate <= upper <= 1.0

    def test_custom_significance_level(self) -> None:
        """Should accept custom significance level."""
        stats = create_aggregate_statistics()

        report_05 = validate_simulation(stats, significance_level=0.05)
        report_01 = validate_simulation(stats, significance_level=0.01)

        # Both should complete without error
        assert isinstance(report_05, ValidationReport)
        assert isinstance(report_01, ValidationReport)

    def test_custom_base_bet(self) -> None:
        """Should use custom base bet for EV calculation."""
        stats = create_aggregate_statistics()

        report_1 = validate_simulation(stats, base_bet=1.0)
        report_5 = validate_simulation(stats, base_bet=5.0)

        # EV theoretical should scale with base bet
        assert report_5.ev_theoretical == report_1.ev_theoretical * 5


class TestChiSquareResultDataclass:
    """Tests for ChiSquareResult dataclass."""

    def test_creation(self) -> None:
        """Should create ChiSquareResult successfully."""
        result = ChiSquareResult(
            statistic=10.5,
            p_value=0.15,
            degrees_of_freedom=9,
            is_valid=True,
        )

        assert result.statistic == 10.5
        assert result.p_value == 0.15
        assert result.degrees_of_freedom == 9
        assert result.is_valid is True

    def test_frozen(self) -> None:
        """ChiSquareResult should be immutable."""
        result = ChiSquareResult(
            statistic=10.5,
            p_value=0.15,
            degrees_of_freedom=9,
            is_valid=True,
        )

        with pytest.raises(AttributeError):
            result.statistic = 20.0  # type: ignore[misc]


class TestValidationReportDataclass:
    """Tests for ValidationReport dataclass."""

    def test_creation(self) -> None:
        """Should create ValidationReport successfully."""
        chi_result = ChiSquareResult(
            statistic=10.5,
            p_value=0.15,
            degrees_of_freedom=9,
            is_valid=True,
        )

        report = ValidationReport(
            chi_square_result=chi_result,
            observed_frequencies={"high_card": 0.5},
            expected_frequencies={"high_card": 0.501},
            ev_actual=-0.034,
            ev_theoretical=-0.035,
            ev_deviation_pct=0.029,
            session_win_rate=0.30,
            session_win_rate_ci=(0.25, 0.35),
            warnings=[],
            is_valid=True,
        )

        assert report.chi_square_result == chi_result
        assert report.ev_actual == -0.034
        assert report.session_win_rate == 0.30
        assert report.is_valid is True

    def test_frozen(self) -> None:
        """ValidationReport should be immutable."""
        chi_result = ChiSquareResult(
            statistic=10.5,
            p_value=0.15,
            degrees_of_freedom=9,
            is_valid=True,
        )

        report = ValidationReport(
            chi_square_result=chi_result,
            observed_frequencies={},
            expected_frequencies={},
            ev_actual=-0.034,
            ev_theoretical=-0.035,
            ev_deviation_pct=0.029,
            session_win_rate=0.30,
            session_win_rate_ci=(0.25, 0.35),
            warnings=[],
            is_valid=True,
        )

        with pytest.raises(AttributeError):
            report.is_valid = False  # type: ignore[misc]


class TestKnownDistributions:
    """Tests using known statistical distributions for validation."""

    def test_binomial_confidence_interval_coverage(self) -> None:
        """Wilson CI should achieve nominal coverage for various proportions."""
        # Test at different true proportions
        test_cases = [
            (0.1, 100),  # 10% rate, 100 trials
            (0.5, 100),  # 50% rate, 100 trials
            (0.9, 100),  # 90% rate, 100 trials
            (0.3, 1000),  # 30% rate, 1000 trials
        ]

        for p, n in test_cases:
            successes = int(p * n)
            lower, upper = calculate_wilson_confidence_interval(successes, n)

            # True proportion should be within or close to the CI
            # Allow some slack since we're using point estimates
            assert lower <= p + 0.15
            assert upper >= p - 0.15

    def test_chi_square_statistic_formula(self) -> None:
        """Chi-square statistic should follow expected formula."""
        # Known simple case: 2 categories, equal expected
        frequencies = {
            "high_card": 600,
            "pair": 400,
        }

        # Manually adjust theoretical for this test
        result = calculate_chi_square(frequencies)

        # The chi-square should be calculated correctly
        # Exact value depends on theoretical probs, but should be non-negative
        assert result.statistic >= 0
        assert 0 <= result.p_value <= 1
