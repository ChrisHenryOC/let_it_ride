"""End-to-end tests for full simulation pipeline.

These tests validate:
- Running 10,000+ sessions with known seed
- Statistical validity (chi-square test for hand frequencies)
- Session win rate within expected range
- Reproducibility (same seed = same results)
- Parallel vs sequential equivalence
- Streak-based bonus strategy integration
"""

from __future__ import annotations

from let_it_ride.analytics.validation import (
    calculate_chi_square,
    calculate_wilson_confidence_interval,
    validate_simulation,
)
from let_it_ride.config.models import (
    BonusStrategyConfig,
    StreakActionConfig,
    StreakBasedBonusConfig,
)
from let_it_ride.simulation import SimulationController
from let_it_ride.simulation.aggregation import (
    aggregate_results,
    aggregate_with_hand_frequencies,
)

from .conftest import (
    MAX_SESSION_WIN_RATE,
    MIN_SESSION_WIN_RATE,
    create_e2e_config,
    create_hand_frequency_tracker,
)


class TestLargeScaleSimulation:
    """Tests running large-scale simulations (10,000 sessions)."""

    def test_ten_thousand_sessions_basic_strategy(self) -> None:
        """Run 10,000 sessions with basic strategy and verify completion.

        This is the primary acceptance test for LIR-34.
        """
        config = create_e2e_config(
            num_sessions=10_000,
            hands_per_session=100,
            random_seed=42,
            workers=4,
        )

        controller = SimulationController(config)
        results = controller.run()

        # Verify correct number of sessions completed
        assert len(results.session_results) == 10_000

        # Verify all sessions have valid data
        for session in results.session_results:
            assert session.hands_played >= 1
            assert session.hands_played <= 100
            assert session.starting_bankroll == 500.0
            assert session.final_bankroll >= 0
            assert session.stop_reason is not None
            assert session.outcome is not None

        # Verify timing metadata
        assert results.start_time is not None
        assert results.end_time is not None
        assert results.start_time <= results.end_time

    def test_session_win_rate_within_expected_range(self) -> None:
        """Verify session win rate falls within statistically expected bounds.

        With basic strategy and standard paytable, expect approximately
        30-50% session win rate depending on stop conditions.
        """
        config = create_e2e_config(
            num_sessions=10_000,
            hands_per_session=100,
            random_seed=12345,
            workers=4,
        )

        results = SimulationController(config).run()

        # Calculate win rate
        winning = sum(1 for r in results.session_results if r.session_profit > 0)
        win_rate = winning / len(results.session_results)

        # Calculate confidence interval
        ci_lower, ci_upper = calculate_wilson_confidence_interval(
            successes=winning,
            total=len(results.session_results),
            confidence_level=0.99,
        )

        # Win rate should be within expected bounds (see conftest.py for rationale)
        assert (
            MIN_SESSION_WIN_RATE <= win_rate <= MAX_SESSION_WIN_RATE
        ), f"Win rate {win_rate:.2%} outside expected range [{MIN_SESSION_WIN_RATE:.0%}, {MAX_SESSION_WIN_RATE:.0%}]"

        # Confidence interval should be reasonably narrow with 10K samples
        ci_width = ci_upper - ci_lower
        assert ci_width < 0.03, f"CI width {ci_width:.4f} unexpectedly wide"


class TestStatisticalValidity:
    """Tests validating simulation statistical properties."""

    def test_hand_frequency_chi_square_passes(self) -> None:
        """Verify hand frequency distribution passes chi-square test.

        This requires collecting hand frequency data during simulation,
        which comes from hand records.

        Note: hand_callback only works in sequential mode (workers=1).
        """
        # Run enough hands to get reliable frequency data
        # Use workers=1 because hand_callback only works in sequential mode
        config = create_e2e_config(
            num_sessions=2_000,
            hands_per_session=50,  # ~100K hands total
            random_seed=77777,
            workers=1,  # Required for hand_callback
        )

        # Track hand frequencies using shared callback factory
        hand_frequencies, track_hands = create_hand_frequency_tracker()

        controller = SimulationController(config, hand_callback=track_hands)
        controller.run()

        # Verify we collected data
        total_hands = sum(hand_frequencies.values())
        assert total_hands > 50_000, f"Only {total_hands} hands collected"

        # Normalize pair types for chi-square test
        normalized = _normalize_frequencies(hand_frequencies)

        # Perform chi-square test with lenient significance level
        # (0.01 to avoid false failures)
        chi_result = calculate_chi_square(normalized, significance_level=0.01)

        # Should pass the test (p-value > 0.01)
        assert chi_result.is_valid, (
            f"Chi-square test failed: statistic={chi_result.statistic:.2f}, "
            f"p_value={chi_result.p_value:.6f}"
        )

    def test_chi_square_rejects_biased_distribution(self) -> None:
        """Verify chi-square test correctly rejects a significantly biased distribution.

        This test ensures the statistical validation actually catches problems
        by providing an intentionally skewed frequency distribution.
        """
        # Create a heavily biased distribution where all hands are "high_card"
        # This should definitely fail chi-square against theoretical probabilities
        biased_frequencies = {
            "royal_flush": 0,
            "straight_flush": 0,
            "four_of_a_kind": 0,
            "full_house": 0,
            "flush": 0,
            "straight": 0,
            "three_of_a_kind": 0,
            "two_pair": 0,
            "pair": 0,  # Normalized pair category
            "high_card": 100_000,  # All hands are high card - obviously biased
        }

        # Chi-square should reject this biased distribution
        chi_result = calculate_chi_square(biased_frequencies, significance_level=0.01)

        # This heavily biased distribution should NOT pass
        assert not chi_result.is_valid, (
            f"Chi-square should have rejected biased distribution: "
            f"statistic={chi_result.statistic:.2f}, p_value={chi_result.p_value:.6f}"
        )

        # The p-value should be extremely small for such a biased distribution
        assert (
            chi_result.p_value < 0.001
        ), f"P-value {chi_result.p_value:.6f} unexpectedly high for biased distribution"

    def test_aggregate_results_integration(self) -> None:
        """Test aggregate_results() with actual SimulationController output.

        This addresses the deferred item from PR #111.
        """
        config = create_e2e_config(
            num_sessions=1_000,
            hands_per_session=50,
            random_seed=54321,
            workers=2,
        )

        controller = SimulationController(config)
        results = controller.run()

        # Aggregate the results
        aggregate = aggregate_results(results.session_results)

        # Verify aggregate matches individual results
        assert aggregate.total_sessions == 1_000
        assert aggregate.total_sessions == len(results.session_results)

        # Verify win/loss/push counts sum to total
        assert (
            aggregate.winning_sessions
            + aggregate.losing_sessions
            + aggregate.push_sessions
            == aggregate.total_sessions
        )

        # Verify total hands match
        expected_hands = sum(r.hands_played for r in results.session_results)
        assert aggregate.total_hands == expected_hands

        # Verify net result calculation
        expected_net = sum(r.session_profit for r in results.session_results)
        assert abs(aggregate.net_result - expected_net) < 0.01

        # Verify session profit statistics
        profits = [r.session_profit for r in results.session_results]
        assert aggregate.session_profit_min == min(profits)
        assert aggregate.session_profit_max == max(profits)

    def test_aggregate_with_hand_frequencies_integration(self) -> None:
        """Test aggregate_with_hand_frequencies() with simulation data.

        Note: hand_callback only works in sequential mode (workers=1).
        """
        config = create_e2e_config(
            num_sessions=500,
            hands_per_session=30,
            random_seed=11111,
            workers=1,  # Required for hand_callback
        )

        hand_frequencies, track_hands = create_hand_frequency_tracker()

        controller = SimulationController(config, hand_callback=track_hands)
        sim_results = controller.run()

        # Aggregate with collected frequencies
        aggregate = aggregate_with_hand_frequencies(
            sim_results.session_results, hand_frequencies
        )

        # Verify frequencies are included
        assert aggregate.hand_frequencies == hand_frequencies
        assert len(aggregate.hand_frequency_pct) > 0

        # Verify percentages sum to ~1.0
        total_pct = sum(aggregate.hand_frequency_pct.values())
        assert abs(total_pct - 1.0) < 0.001


class TestReproducibility:
    """Tests for simulation reproducibility."""

    def test_same_seed_identical_results(self) -> None:
        """Same seed should produce identical results."""
        seed = 98765
        config1 = create_e2e_config(num_sessions=100, random_seed=seed, workers=1)
        config2 = create_e2e_config(num_sessions=100, random_seed=seed, workers=1)

        results1 = SimulationController(config1).run()
        results2 = SimulationController(config2).run()

        # Verify identical session profits
        for r1, r2 in zip(
            results1.session_results, results2.session_results, strict=True
        ):
            assert r1.final_bankroll == r2.final_bankroll
            assert r1.hands_played == r2.hands_played
            assert r1.session_profit == r2.session_profit
            assert r1.stop_reason == r2.stop_reason

    def test_different_seeds_different_results(self) -> None:
        """Different seeds should produce different results."""
        config1 = create_e2e_config(num_sessions=100, random_seed=111, workers=1)
        config2 = create_e2e_config(num_sessions=100, random_seed=222, workers=1)

        results1 = SimulationController(config1).run()
        results2 = SimulationController(config2).run()

        profits1 = [r.session_profit for r in results1.session_results]
        profits2 = [r.session_profit for r in results2.session_results]

        # Should be different
        assert profits1 != profits2


class TestParallelSequentialEquivalence:
    """Tests verifying parallel and sequential produce identical results."""

    def test_parallel_vs_sequential_same_results(self) -> None:
        """Parallel and sequential should produce identical results with same seed."""
        seed = 33333
        num_sessions = 100

        # Sequential
        config_seq = create_e2e_config(
            num_sessions=num_sessions, random_seed=seed, workers=1
        )
        results_seq = SimulationController(config_seq).run()

        # Parallel with 2 workers
        config_par2 = create_e2e_config(
            num_sessions=num_sessions, random_seed=seed, workers=2
        )
        results_par2 = SimulationController(config_par2).run()

        # Parallel with 4 workers
        config_par4 = create_e2e_config(
            num_sessions=num_sessions, random_seed=seed, workers=4
        )
        results_par4 = SimulationController(config_par4).run()

        # All should have identical results across multiple fields
        for seq, par2, par4 in zip(
            results_seq.session_results,
            results_par2.session_results,
            results_par4.session_results,
            strict=True,
        ):
            # Compare key result fields
            assert seq.session_profit == par2.session_profit == par4.session_profit
            assert seq.hands_played == par2.hands_played == par4.hands_played
            assert seq.final_bankroll == par2.final_bankroll == par4.final_bankroll
            assert seq.stop_reason == par2.stop_reason == par4.stop_reason

    def test_parallel_equivalence_large_scale(self) -> None:
        """Test parallel/sequential equivalence at larger scale."""
        seed = 55555
        num_sessions = 1000

        config_seq = create_e2e_config(
            num_sessions=num_sessions, random_seed=seed, workers=1
        )
        results_seq = SimulationController(config_seq).run()

        config_par = create_e2e_config(
            num_sessions=num_sessions, random_seed=seed, workers=4
        )
        results_par = SimulationController(config_par).run()

        # Compare totals
        assert results_seq.total_hands == results_par.total_hands

        # Compare all session results in detail
        for seq, par in zip(
            results_seq.session_results, results_par.session_results, strict=True
        ):
            assert seq.session_profit == par.session_profit
            assert seq.hands_played == par.hands_played
            assert seq.final_bankroll == par.final_bankroll
            assert seq.stop_reason == par.stop_reason

        # Also verify aggregate counts
        seq_winning = sum(
            1 for r in results_seq.session_results if r.session_profit > 0
        )
        par_winning = sum(
            1 for r in results_par.session_results if r.session_profit > 0
        )
        assert seq_winning == par_winning


class TestValidationIntegration:
    """Tests for validation module integration with simulation results."""

    def test_validate_simulation_integration(self) -> None:
        """Test validate_simulation() with actual simulation aggregate stats.

        Note: hand_callback only works in sequential mode (workers=1).
        """
        config = create_e2e_config(
            num_sessions=1000,
            hands_per_session=50,
            random_seed=66666,
            workers=1,  # Required for hand_callback
        )

        hand_frequencies, track_hands = create_hand_frequency_tracker()

        controller = SimulationController(config, hand_callback=track_hands)
        sim_results = controller.run()

        # Create aggregate with frequencies
        aggregate = aggregate_with_hand_frequencies(
            sim_results.session_results, hand_frequencies
        )

        # Run validation
        report = validate_simulation(aggregate, base_bet=5.0)

        # Validation should complete without error
        assert report is not None
        assert isinstance(report.chi_square_result.statistic, float)
        assert isinstance(report.chi_square_result.p_value, float)
        assert isinstance(report.session_win_rate, float)
        assert len(report.session_win_rate_ci) == 2


class TestStreakBasedBonusIntegration:
    """Tests for streak-based bonus strategy integration with simulation."""

    def test_streak_based_bonus_strategy_executes(self) -> None:
        """Verify streak-based bonus strategy runs without error in simulation.

        This is the primary integration test for LIR-37 (issue #40).
        """
        # Create config with streak-based bonus strategy
        config = create_e2e_config(
            num_sessions=100,
            hands_per_session=50,
            random_seed=42,
            workers=1,  # Sequential for simplicity
        )

        # Override bonus strategy to streak_based
        config = config.model_copy(
            update={
                "bonus_strategy": BonusStrategyConfig(
                    enabled=True,
                    type="streak_based",
                    streak_based=StreakBasedBonusConfig(
                        base_amount=5.0,
                        trigger="main_loss",
                        streak_length=3,
                        action=StreakActionConfig(type="multiply", value=2.0),
                        reset_on="main_win",
                        max_multiplier=8.0,
                    ),
                ),
            }
        )

        controller = SimulationController(config)
        results = controller.run()

        # Verify sessions completed
        assert len(results.session_results) == 100

        # Verify bonus wagered is non-zero (strategy was used)
        total_bonus_wagered = sum(
            r.total_bonus_wagered for r in results.session_results
        )
        assert total_bonus_wagered > 0, "No bonus bets were placed"

    def test_streak_based_bonus_with_parallel_execution(self) -> None:
        """Verify streak-based bonus strategy works with parallel execution."""
        config = create_e2e_config(
            num_sessions=100,
            hands_per_session=50,
            random_seed=12345,
            workers=4,  # Parallel
        )

        config = config.model_copy(
            update={
                "bonus_strategy": BonusStrategyConfig(
                    enabled=True,
                    type="streak_based",
                    streak_based=StreakBasedBonusConfig(
                        base_amount=2.0,
                        trigger="bonus_loss",
                        streak_length=2,
                        action=StreakActionConfig(type="increase", value=1.0),
                        reset_on="bonus_win",
                        max_multiplier=10.0,
                    ),
                ),
            }
        )

        controller = SimulationController(config)
        results = controller.run()

        assert len(results.session_results) == 100
        total_bonus_wagered = sum(
            r.total_bonus_wagered for r in results.session_results
        )
        assert total_bonus_wagered > 0

    def test_streak_based_bonus_sequential_parallel_equivalence(self) -> None:
        """Verify streak-based bonus produces same results in sequential vs parallel."""
        seed = 77777
        bonus_config = BonusStrategyConfig(
            enabled=True,
            type="streak_based",
            streak_based=StreakBasedBonusConfig(
                base_amount=3.0,
                trigger="any_loss",
                streak_length=2,
                action=StreakActionConfig(type="multiply", value=1.5),
                reset_on="any_win",
                max_multiplier=4.0,
            ),
        )

        # Sequential
        config_seq = create_e2e_config(num_sessions=50, random_seed=seed, workers=1)
        config_seq = config_seq.model_copy(update={"bonus_strategy": bonus_config})
        results_seq = SimulationController(config_seq).run()

        # Parallel
        config_par = create_e2e_config(num_sessions=50, random_seed=seed, workers=2)
        config_par = config_par.model_copy(update={"bonus_strategy": bonus_config})
        results_par = SimulationController(config_par).run()

        # Compare results
        for seq, par in zip(
            results_seq.session_results, results_par.session_results, strict=True
        ):
            assert seq.session_profit == par.session_profit
            assert seq.hands_played == par.hands_played
            assert seq.total_bonus_wagered == par.total_bonus_wagered


def _normalize_frequencies(frequencies: dict[str, int]) -> dict[str, int]:
    """Normalize hand frequencies by combining pair types.

    The simulator distinguishes pair_tens_or_better and pair_below_tens,
    but theoretical probabilities use a single 'pair' category. This function
    combines the two pair types to enable comparison with theoretical values.

    Args:
        frequencies: Dictionary mapping hand rank names (lowercase) to counts.
            Expected keys include standard poker ranks like 'royal_flush',
            'straight_flush', etc., plus the simulator's split pair categories.

    Returns:
        A new dictionary with pair_tens_or_better and pair_below_tens combined
        into a single 'pair' key. Other entries are copied unchanged.
    """
    normalized = dict(frequencies)

    # Combine pair types
    tens_or_better = normalized.pop("pair_tens_or_better", 0)
    below_tens = normalized.pop("pair_below_tens", 0)
    if tens_or_better > 0 or below_tens > 0:
        normalized["pair"] = tens_or_better + below_tens

    return normalized
