"""End-to-end tests for full simulation pipeline.

These tests validate:
- Running 10,000+ sessions with known seed
- Statistical validity (chi-square test for hand frequencies)
- Session win rate within expected range
- Reproducibility (same seed = same results)
- Parallel vs sequential equivalence
"""

from __future__ import annotations

from typing import Literal

from let_it_ride.analytics.validation import (
    calculate_chi_square,
    calculate_wilson_confidence_interval,
    validate_simulation,
)
from let_it_ride.config.models import (
    BankrollConfig,
    BettingSystemConfig,
    FullConfig,
    SimulationConfig,
    StopConditionsConfig,
    StrategyConfig,
)
from let_it_ride.core.game_engine import GameHandResult
from let_it_ride.simulation import SimulationController
from let_it_ride.simulation.aggregation import (
    aggregate_results,
    aggregate_with_hand_frequencies,
)


def create_e2e_config(
    num_sessions: int = 1000,
    hands_per_session: int = 100,
    random_seed: int | None = 42,
    workers: int | Literal["auto"] = 1,
) -> FullConfig:
    """Create a configuration for E2E testing.

    Args:
        num_sessions: Number of sessions to run.
        hands_per_session: Maximum hands per session.
        random_seed: Optional seed for reproducibility.
        workers: Number of workers or "auto".

    Returns:
        A FullConfig instance ready for simulation.
    """
    return FullConfig(
        simulation=SimulationConfig(
            num_sessions=num_sessions,
            hands_per_session=hands_per_session,
            random_seed=random_seed,
            workers=workers,
        ),
        bankroll=BankrollConfig(
            starting_amount=500.0,
            base_bet=5.0,
            stop_conditions=StopConditionsConfig(
                win_limit=250.0,
                loss_limit=200.0,
                stop_on_insufficient_funds=True,
            ),
            betting_system=BettingSystemConfig(type="flat"),
        ),
        strategy=StrategyConfig(type="basic"),
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

        # Win rate should be between 20% and 60% (very wide bounds for stability)
        # Actual rate depends heavily on stop conditions
        assert (
            0.20 <= win_rate <= 0.60
        ), f"Win rate {win_rate:.2%} outside expected range"

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

        # Track hand frequencies manually via hand callback
        hand_frequencies: dict[str, int] = {}

        def track_hands(
            session_id: int,  # noqa: ARG001
            hand_id: int,  # noqa: ARG001
            result: GameHandResult,
        ) -> None:
            # Convert enum to lowercase string (e.g., FiveCardHandRank.ROYAL_FLUSH -> "royal_flush")
            hand_rank = result.final_hand_rank.name.lower()
            hand_frequencies[hand_rank] = hand_frequencies.get(hand_rank, 0) + 1

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

        hand_frequencies: dict[str, int] = {}

        def track_hands(
            session_id: int,  # noqa: ARG001
            hand_id: int,  # noqa: ARG001
            result: GameHandResult,
        ) -> None:
            # Convert enum to lowercase string
            hand_rank = result.final_hand_rank.name.lower()
            hand_frequencies[hand_rank] = hand_frequencies.get(hand_rank, 0) + 1

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

        # All should have identical profits
        profits_seq = [r.session_profit for r in results_seq.session_results]
        profits_par2 = [r.session_profit for r in results_par2.session_results]
        profits_par4 = [r.session_profit for r in results_par4.session_results]

        assert profits_seq == profits_par2
        assert profits_seq == profits_par4

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

        # Compare aggregates
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

        hand_frequencies: dict[str, int] = {}

        def track_hands(
            session_id: int,  # noqa: ARG001
            hand_id: int,  # noqa: ARG001
            result: GameHandResult,
        ) -> None:
            # Convert enum to lowercase string
            hand_rank = result.final_hand_rank.name.lower()
            hand_frequencies[hand_rank] = hand_frequencies.get(hand_rank, 0) + 1

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


def _normalize_frequencies(frequencies: dict[str, int]) -> dict[str, int]:
    """Normalize hand frequencies by combining pair types.

    The simulator distinguishes pair_tens_or_better and pair_below_tens,
    but theoretical probabilities use a single 'pair' category.
    """
    normalized = dict(frequencies)

    # Combine pair types
    tens_or_better = normalized.pop("pair_tens_or_better", 0)
    below_tens = normalized.pop("pair_below_tens", 0)
    if tens_or_better > 0 or below_tens > 0:
        normalized["pair"] = tens_or_better + below_tens

    return normalized
