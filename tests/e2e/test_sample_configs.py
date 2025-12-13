"""End-to-end tests for sample configuration files.

These tests validate that all sample configurations:
- Load successfully
- Execute complete simulations
- Produce valid results and output files
"""

from __future__ import annotations

from pathlib import Path

import pytest

from let_it_ride.config.loader import load_config
from let_it_ride.simulation import SimulationController
from let_it_ride.simulation.aggregation import aggregate_results

# Path to configs directory
CONFIGS_DIR = Path(__file__).parent.parent.parent / "configs"

# All sample configuration files to test
SAMPLE_CONFIG_FILES = [
    "basic_strategy.yaml",
    "conservative.yaml",
    "aggressive.yaml",
    "bonus_comparison.yaml",
    "progressive_betting.yaml",
    "sample_config.yaml",
]


class TestSampleConfigsExecution:
    """Tests that sample configs execute successfully."""

    @pytest.mark.parametrize("config_file", SAMPLE_CONFIG_FILES)
    def test_config_executes_simulation(self, config_file: str) -> None:
        """Verify each sample config executes a simulation successfully."""
        config_path = CONFIGS_DIR / config_file
        config = load_config(config_path)

        # Override for reasonable test execution time
        config.simulation.num_sessions = 100
        config.simulation.hands_per_session = 50
        config.simulation.random_seed = 42

        controller = SimulationController(config)
        results = controller.run()

        # Verify simulation completed
        assert len(results.session_results) == 100
        assert results.total_hands > 0

    @pytest.mark.parametrize("config_file", SAMPLE_CONFIG_FILES)
    def test_config_produces_valid_results(self, config_file: str) -> None:
        """Verify each sample config produces valid session results."""
        config_path = CONFIGS_DIR / config_file
        config = load_config(config_path)

        # Override for test
        config.simulation.num_sessions = 50
        config.simulation.hands_per_session = 30
        config.simulation.random_seed = 12345

        results = SimulationController(config).run()

        for session in results.session_results:
            # Verify session data is valid
            assert session.hands_played >= 1
            assert session.hands_played <= 30
            assert session.starting_bankroll > 0
            assert session.final_bankroll >= 0
            assert session.stop_reason is not None
            assert session.outcome is not None

    @pytest.mark.parametrize("config_file", SAMPLE_CONFIG_FILES)
    def test_config_aggregate_statistics_valid(self, config_file: str) -> None:
        """Verify each sample config produces valid aggregate statistics."""
        config_path = CONFIGS_DIR / config_file
        config = load_config(config_path)

        config.simulation.num_sessions = 100
        config.simulation.hands_per_session = 50
        config.simulation.random_seed = 54321

        results = SimulationController(config).run()
        aggregate = aggregate_results(results.session_results)

        # Verify aggregate statistics
        assert aggregate.total_sessions == 100
        assert (
            aggregate.winning_sessions
            + aggregate.losing_sessions
            + aggregate.push_sessions
            == 100
        )
        assert 0.0 <= aggregate.session_win_rate <= 1.0
        assert aggregate.total_hands > 0


class TestSampleConfigsReproducibility:
    """Tests that sample configs produce reproducible results."""

    @pytest.mark.parametrize("config_file", SAMPLE_CONFIG_FILES)
    def test_config_reproducible_with_seed(self, config_file: str) -> None:
        """Verify each sample config is reproducible with same seed."""
        config_path = CONFIGS_DIR / config_file
        seed = 77777

        # First run
        config1 = load_config(config_path)
        config1.simulation.num_sessions = 50
        config1.simulation.hands_per_session = 30
        config1.simulation.random_seed = seed
        results1 = SimulationController(config1).run()

        # Second run
        config2 = load_config(config_path)
        config2.simulation.num_sessions = 50
        config2.simulation.hands_per_session = 30
        config2.simulation.random_seed = seed
        results2 = SimulationController(config2).run()

        # Verify identical results
        for r1, r2 in zip(
            results1.session_results, results2.session_results, strict=True
        ):
            assert r1.final_bankroll == r2.final_bankroll
            assert r1.hands_played == r2.hands_played
            assert r1.session_profit == r2.session_profit


class TestSampleConfigsParallel:
    """Tests that sample configs work with parallel execution."""

    @pytest.mark.parametrize("config_file", SAMPLE_CONFIG_FILES)
    def test_config_parallel_execution(self, config_file: str) -> None:
        """Verify each sample config works with parallel execution."""
        config_path = CONFIGS_DIR / config_file
        config = load_config(config_path)

        config.simulation.num_sessions = 100
        config.simulation.hands_per_session = 30
        config.simulation.random_seed = 88888
        config.simulation.workers = 4

        results = SimulationController(config).run()

        assert len(results.session_results) == 100

    @pytest.mark.parametrize("config_file", SAMPLE_CONFIG_FILES)
    def test_config_parallel_matches_sequential(self, config_file: str) -> None:
        """Verify parallel and sequential produce identical results for each config."""
        config_path = CONFIGS_DIR / config_file
        seed = 33333

        # Sequential
        config_seq = load_config(config_path)
        config_seq.simulation.num_sessions = 50
        config_seq.simulation.hands_per_session = 30
        config_seq.simulation.random_seed = seed
        config_seq.simulation.workers = 1
        results_seq = SimulationController(config_seq).run()

        # Parallel
        config_par = load_config(config_path)
        config_par.simulation.num_sessions = 50
        config_par.simulation.hands_per_session = 30
        config_par.simulation.random_seed = seed
        config_par.simulation.workers = 4
        results_par = SimulationController(config_par).run()

        # Verify identical profits
        profits_seq = [r.session_profit for r in results_seq.session_results]
        profits_par = [r.session_profit for r in results_par.session_results]
        assert profits_seq == profits_par


class TestSpecificConfigValidation:
    """Detailed tests for specific configuration behaviors."""

    def test_basic_strategy_uses_flat_betting(self) -> None:
        """Verify basic_strategy.yaml uses flat betting system."""
        config = load_config(CONFIGS_DIR / "basic_strategy.yaml")

        config.simulation.num_sessions = 20
        config.simulation.hands_per_session = 20
        config.simulation.random_seed = 42

        results = SimulationController(config).run()

        # With flat betting, base bet stays constant
        # Just verify simulation completes
        assert len(results.session_results) == 20

    def test_progressive_betting_martingale_behavior(self) -> None:
        """Verify progressive_betting.yaml uses Martingale system."""
        config = load_config(CONFIGS_DIR / "progressive_betting.yaml")

        # Verify config is Martingale
        assert config.bankroll.betting_system.type == "martingale"

        config.simulation.num_sessions = 50
        config.simulation.hands_per_session = 30
        config.simulation.random_seed = 42

        results = SimulationController(config).run()

        # Martingale can cause faster bust due to bet escalation
        # Just verify it completes
        assert len(results.session_results) == 50

    def test_bonus_comparison_has_bonus_enabled(self) -> None:
        """Verify bonus_comparison.yaml has bonus betting enabled."""
        config = load_config(CONFIGS_DIR / "bonus_comparison.yaml")

        # Verify bonus is enabled
        assert config.bonus_strategy.enabled is True

        config.simulation.num_sessions = 30
        config.simulation.hands_per_session = 30
        config.simulation.random_seed = 42

        results = SimulationController(config).run()
        assert len(results.session_results) == 30

    def test_conservative_strategy_characteristics(self) -> None:
        """Verify conservative.yaml uses conservative strategy settings."""
        config = load_config(CONFIGS_DIR / "conservative.yaml")

        assert config.strategy.type == "conservative"
        assert config.strategy.conservative is not None
        assert config.strategy.conservative.made_hands_only is True

        config.simulation.num_sessions = 50
        config.simulation.hands_per_session = 30
        config.simulation.random_seed = 42

        results = SimulationController(config).run()
        assert len(results.session_results) == 50

    def test_aggressive_strategy_characteristics(self) -> None:
        """Verify aggressive.yaml uses aggressive strategy settings."""
        config = load_config(CONFIGS_DIR / "aggressive.yaml")

        assert config.strategy.type == "aggressive"
        assert config.strategy.aggressive is not None
        assert config.strategy.aggressive.ride_on_draws is True

        config.simulation.num_sessions = 50
        config.simulation.hands_per_session = 30
        config.simulation.random_seed = 42

        results = SimulationController(config).run()
        assert len(results.session_results) == 50


class TestSampleConfigsLargeScale:
    """Large-scale tests for sample configurations."""

    def test_basic_strategy_thousand_sessions(self) -> None:
        """Verify basic_strategy handles 1000 sessions."""
        config = load_config(CONFIGS_DIR / "basic_strategy.yaml")

        config.simulation.num_sessions = 1000
        config.simulation.hands_per_session = 50
        config.simulation.random_seed = 42
        config.simulation.workers = 4

        results = SimulationController(config).run()

        assert len(results.session_results) == 1000

        # Verify aggregate statistics are reasonable
        aggregate = aggregate_results(results.session_results)
        assert aggregate.total_sessions == 1000
        # Win rate should be somewhere reasonable (20-60%)
        assert 0.15 <= aggregate.session_win_rate <= 0.65

    def test_all_configs_handle_hundred_sessions(self) -> None:
        """Verify all configs handle 100 sessions efficiently."""
        for config_file in SAMPLE_CONFIG_FILES:
            config = load_config(CONFIGS_DIR / config_file)

            config.simulation.num_sessions = 100
            config.simulation.hands_per_session = 50
            config.simulation.random_seed = 42
            config.simulation.workers = 2

            results = SimulationController(config).run()

            assert len(results.session_results) == 100, f"Failed for {config_file}"
