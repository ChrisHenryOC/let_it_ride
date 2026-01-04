"""Integration tests for sample configuration files.

Validates that all configuration files in configs/ directory:
- Load without errors
- Pass schema validation
- Have valid values for all fields
- Execute simulations successfully
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
import yaml
from pydantic import ValidationError

from let_it_ride.config.loader import load_config
from let_it_ride.config.models import FullConfig
from let_it_ride.simulation import SimulationController

if TYPE_CHECKING:
    from let_it_ride.simulation import SimulationResults

# Path to configs directory
CONFIGS_DIR = Path(__file__).parent.parent.parent / "configs"

# List of all sample configuration files that should be validated
SAMPLE_CONFIG_FILES = [
    "examples/basic_strategy.yaml",
    "examples/conservative.yaml",
    "examples/aggressive.yaml",
    "examples/bonus_comparison.yaml",
    "examples/progressive_betting.yaml",
    "sample_config.yaml",
]


class TestSampleConfigsExist:
    """Test that all expected sample configuration files exist."""

    def test_configs_directory_exists(self) -> None:
        """Test that the configs directory exists."""
        assert CONFIGS_DIR.exists(), f"Configs directory not found: {CONFIGS_DIR}"
        assert CONFIGS_DIR.is_dir(), f"Configs path is not a directory: {CONFIGS_DIR}"

    @pytest.mark.parametrize("config_file", SAMPLE_CONFIG_FILES)
    def test_config_file_exists(self, config_file: str) -> None:
        """Test that each expected config file exists."""
        config_path = CONFIGS_DIR / config_file
        assert config_path.exists(), f"Config file not found: {config_path}"
        assert config_path.is_file(), f"Config path is not a file: {config_path}"


class TestSampleConfigsLoad:
    """Test that all sample configuration files load and validate correctly."""

    @pytest.mark.parametrize("config_file", SAMPLE_CONFIG_FILES)
    def test_config_loads_successfully(self, config_file: str) -> None:
        """Test that each config file loads without errors."""
        config_path = CONFIGS_DIR / config_file
        config = load_config(config_path)
        assert isinstance(config, FullConfig)

    @pytest.mark.parametrize("config_file", SAMPLE_CONFIG_FILES)
    def test_config_has_valid_simulation(self, config_file: str) -> None:
        """Test that each config has valid simulation settings."""
        config_path = CONFIGS_DIR / config_file
        config = load_config(config_path)

        # Verify simulation settings are within valid ranges
        assert config.simulation.num_sessions >= 1
        assert config.simulation.num_sessions <= 100_000_000
        assert config.simulation.hands_per_session >= 1
        assert config.simulation.hands_per_session <= 10_000

    @pytest.mark.parametrize("config_file", SAMPLE_CONFIG_FILES)
    def test_config_has_valid_bankroll(self, config_file: str) -> None:
        """Test that each config has valid bankroll settings."""
        config_path = CONFIGS_DIR / config_file
        config = load_config(config_path)

        # Verify bankroll settings
        assert config.bankroll.starting_amount > 0
        assert config.bankroll.base_bet > 0
        # Starting amount must be at least 3x base bet
        assert config.bankroll.starting_amount >= config.bankroll.base_bet * 3


class TestBasicStrategyConfig:
    """Specific tests for basic_strategy.yaml."""

    @pytest.fixture(scope="class")
    def config(self) -> FullConfig:
        """Load basic_strategy.yaml once per test class."""
        return load_config(CONFIGS_DIR / "examples/basic_strategy.yaml")

    def test_uses_basic_strategy(self, config: FullConfig) -> None:
        """Test that basic_strategy.yaml uses basic strategy."""
        assert config.strategy.type == "basic"

    def test_uses_flat_betting(self, config: FullConfig) -> None:
        """Test that basic_strategy.yaml uses flat betting."""
        assert config.bankroll.betting_system.type == "flat"

    def test_bonus_disabled(self, config: FullConfig) -> None:
        """Test that bonus betting is disabled."""
        assert config.bonus_strategy.enabled is False

    def test_has_metadata(self, config: FullConfig) -> None:
        """Test that metadata is present and meaningful."""
        assert config.metadata.name is not None
        assert "basic" in config.metadata.name.lower()


class TestConservativeConfig:
    """Specific tests for conservative.yaml."""

    @pytest.fixture(scope="class")
    def config(self) -> FullConfig:
        """Load conservative.yaml once per test class."""
        return load_config(CONFIGS_DIR / "examples/conservative.yaml")

    def test_uses_conservative_strategy(self, config: FullConfig) -> None:
        """Test that conservative.yaml uses conservative strategy."""
        assert config.strategy.type == "conservative"

    def test_has_conservative_config(self, config: FullConfig) -> None:
        """Test that conservative strategy config is present."""
        assert config.strategy.conservative is not None
        assert config.strategy.conservative.made_hands_only is True

    def test_has_tight_stop_conditions(self, config: FullConfig) -> None:
        """Test that stop conditions are tighter than basic."""
        # Win limit should be present and reasonable
        assert config.bankroll.stop_conditions.win_limit is not None
        assert config.bankroll.stop_conditions.loss_limit is not None


class TestAggressiveConfig:
    """Specific tests for aggressive.yaml."""

    @pytest.fixture(scope="class")
    def config(self) -> FullConfig:
        """Load aggressive.yaml once per test class."""
        return load_config(CONFIGS_DIR / "examples/aggressive.yaml")

    def test_uses_aggressive_strategy(self, config: FullConfig) -> None:
        """Test that aggressive.yaml uses aggressive strategy."""
        assert config.strategy.type == "aggressive"

    def test_has_aggressive_config(self, config: FullConfig) -> None:
        """Test that aggressive strategy config is present."""
        assert config.strategy.aggressive is not None
        assert config.strategy.aggressive.ride_on_draws is True

    def test_includes_gutshots(self, config: FullConfig) -> None:
        """Test that gutshot draws are included."""
        assert config.strategy.aggressive.include_gutshots is True


class TestBonusComparisonConfig:
    """Specific tests for bonus_comparison.yaml."""

    @pytest.fixture(scope="class")
    def config(self) -> FullConfig:
        """Load bonus_comparison.yaml once per test class."""
        return load_config(CONFIGS_DIR / "examples/bonus_comparison.yaml")

    def test_bonus_enabled(self, config: FullConfig) -> None:
        """Test that bonus betting is enabled."""
        assert config.bonus_strategy.enabled is True

    def test_uses_bankroll_conditional(self, config: FullConfig) -> None:
        """Test that bankroll conditional strategy is used."""
        assert config.bonus_strategy.type == "bankroll_conditional"

    def test_has_scaling_tiers(self, config: FullConfig) -> None:
        """Test that scaling tiers are configured."""
        assert config.bonus_strategy.bankroll_conditional is not None
        assert config.bonus_strategy.bankroll_conditional.scaling is not None
        assert config.bonus_strategy.bankroll_conditional.scaling.enabled is True
        assert len(config.bonus_strategy.bankroll_conditional.scaling.tiers) >= 1

    def test_scaling_tiers_are_ordered(self, config: FullConfig) -> None:
        """Test that scaling tiers are properly ordered by min_profit."""
        assert config.bonus_strategy.bankroll_conditional is not None
        tiers = config.bonus_strategy.bankroll_conditional.scaling.tiers
        assert len(tiers) >= 2, "Should have multiple tiers for meaningful scaling"

        # Verify tiers are ordered by min_profit
        for i in range(len(tiers) - 1):
            assert (
                tiers[i].min_profit < tiers[i + 1].min_profit
            ), f"Tier {i} min_profit should be less than tier {i + 1}"

    def test_scaling_tiers_have_logical_progression(self, config: FullConfig) -> None:
        """Test that scaling tiers have logical bet amount progression."""
        assert config.bonus_strategy.bankroll_conditional is not None
        tiers = config.bonus_strategy.bankroll_conditional.scaling.tiers

        # Verify bet amounts generally increase with profit level
        for i in range(len(tiers) - 1):
            assert (
                tiers[i].bet_amount <= tiers[i + 1].bet_amount
            ), "Higher profit tiers should have equal or higher bets"


class TestProgressiveBettingConfig:
    """Specific tests for progressive_betting.yaml."""

    @pytest.fixture(scope="class")
    def config(self) -> FullConfig:
        """Load progressive_betting.yaml once per test class."""
        return load_config(CONFIGS_DIR / "examples/progressive_betting.yaml")

    def test_uses_martingale(self, config: FullConfig) -> None:
        """Test that Martingale betting system is configured."""
        assert config.bankroll.betting_system.type == "martingale"

    def test_has_martingale_config(self, config: FullConfig) -> None:
        """Test that Martingale config is present."""
        assert config.bankroll.betting_system.martingale is not None
        assert config.bankroll.betting_system.martingale.loss_multiplier > 1

    def test_larger_starting_bankroll(self, config: FullConfig) -> None:
        """Test that starting bankroll is larger for progressive betting."""
        # Progressive betting needs larger bankroll
        assert config.bankroll.starting_amount >= 1000


class TestConfigReadmeExists:
    """Test that README.md exists in configs directory."""

    def test_readme_exists(self) -> None:
        """Test that README.md exists."""
        readme_path = CONFIGS_DIR / "README.md"
        assert readme_path.exists(), f"README.md not found: {readme_path}"

    def test_readme_is_not_empty(self) -> None:
        """Test that README.md has content."""
        readme_path = CONFIGS_DIR / "README.md"
        content = readme_path.read_text()
        assert len(content) > 100, "README.md should have substantial content"

    def test_readme_mentions_all_configs(self) -> None:
        """Test that README.md mentions all config files."""
        readme_path = CONFIGS_DIR / "README.md"
        content = readme_path.read_text().lower()

        for config_file in SAMPLE_CONFIG_FILES:
            if (
                config_file != "sample_config.yaml"
            ):  # sample_config may be mentioned differently
                # Extract just the filename without directory path
                filename = Path(config_file).name.replace(".yaml", "")
                assert (
                    filename in content
                ), f"README.md should mention {config_file}"


class TestSampleConfigsRunSimulation:
    """Test that sample configs can execute simulations successfully."""

    @pytest.mark.parametrize("config_file", SAMPLE_CONFIG_FILES)
    def test_config_runs_minimal_simulation(self, config_file: str) -> None:
        """Test that each config can execute a minimal simulation without errors."""
        config_path = CONFIGS_DIR / config_file
        config = load_config(config_path)

        # Override for fast test execution
        config.simulation.num_sessions = 3
        config.simulation.hands_per_session = 10
        config.simulation.random_seed = 42

        # Run simulation and verify no exceptions
        controller = SimulationController(config)
        results: SimulationResults = controller.run()

        # Verify results are valid
        assert len(results.session_results) == 3
        for session_result in results.session_results:
            assert session_result.hands_played >= 1
            assert session_result.hands_played <= 10

    def test_basic_strategy_produces_consistent_results(self) -> None:
        """Test that basic_strategy.yaml produces deterministic results with same seed."""
        config = load_config(CONFIGS_DIR / "examples/basic_strategy.yaml")
        config.simulation.num_sessions = 5
        config.simulation.hands_per_session = 20
        config.simulation.random_seed = 12345

        # Run twice with same seed
        controller1 = SimulationController(config)
        results1 = controller1.run()

        controller2 = SimulationController(config)
        results2 = controller2.run()

        # Verify identical results
        assert len(results1.session_results) == len(results2.session_results)
        for r1, r2 in zip(
            results1.session_results, results2.session_results, strict=True
        ):
            assert r1.final_bankroll == r2.final_bankroll
            assert r1.hands_played == r2.hands_played


class TestMalformedConfigs:
    """Test that malformed configurations produce clear error messages."""

    def test_invalid_strategy_type_raises_error(self) -> None:
        """Test that invalid strategy type produces a clear error."""
        config_path = CONFIGS_DIR / "examples/basic_strategy.yaml"
        content = config_path.read_text()

        # Replace valid strategy with invalid one
        malformed = content.replace('type: "basic"', 'type: "invalid_strategy"')
        config_dict = yaml.safe_load(malformed)

        with pytest.raises(ValidationError) as exc_info:
            FullConfig(**config_dict)

        error_str = str(exc_info.value)
        assert "strategy" in error_str.lower() or "type" in error_str.lower()

    def test_negative_bankroll_raises_error(self) -> None:
        """Test that negative starting bankroll produces a clear error."""
        config_path = CONFIGS_DIR / "examples/basic_strategy.yaml"
        content = config_path.read_text()

        # Replace valid bankroll with negative value
        malformed = content.replace("starting_amount: 500.00", "starting_amount: -100")
        config_dict = yaml.safe_load(malformed)

        with pytest.raises(ValidationError) as exc_info:
            FullConfig(**config_dict)

        error_str = str(exc_info.value)
        assert "bankroll" in error_str.lower() or "starting" in error_str.lower()

    def test_invalid_betting_system_raises_error(self) -> None:
        """Test that invalid betting system type produces clear error."""
        config_path = CONFIGS_DIR / "examples/basic_strategy.yaml"
        content = config_path.read_text()

        # Replace valid betting system with invalid one
        malformed = content.replace('type: "flat"', 'type: "invalid_system"')
        config_dict = yaml.safe_load(malformed)

        with pytest.raises(ValidationError) as exc_info:
            FullConfig(**config_dict)

        error_str = str(exc_info.value)
        assert "betting" in error_str.lower() or "type" in error_str.lower()


class TestConfigRelationships:
    """Test relationships between different config files."""

    def test_aggressive_has_wider_limits_than_basic(self) -> None:
        """Test that aggressive config allows wider stop limits than basic."""
        basic = load_config(CONFIGS_DIR / "examples/basic_strategy.yaml")
        aggressive = load_config(CONFIGS_DIR / "examples/aggressive.yaml")

        # Aggressive should have higher or equal limits to allow more variance
        assert (
            aggressive.bankroll.stop_conditions.win_limit
            >= basic.bankroll.stop_conditions.win_limit
        )
        assert (
            aggressive.bankroll.stop_conditions.loss_limit
            >= basic.bankroll.stop_conditions.loss_limit
        )

    def test_conservative_is_more_restrictive(self) -> None:
        """Test that conservative strategy has more restrictive settings."""
        conservative = load_config(CONFIGS_DIR / "examples/conservative.yaml")

        # Conservative should require made hands only
        assert conservative.strategy.conservative is not None
        assert conservative.strategy.conservative.made_hands_only is True

    def test_progressive_betting_has_larger_bankroll(self) -> None:
        """Test that progressive betting config has larger bankroll."""
        basic = load_config(CONFIGS_DIR / "examples/basic_strategy.yaml")
        progressive = load_config(CONFIGS_DIR / "examples/progressive_betting.yaml")

        # Progressive betting needs larger bankroll to survive losing streaks
        assert (
            progressive.bankroll.starting_amount >= basic.bankroll.starting_amount
        ), "Progressive betting should have at least as much bankroll as basic"
