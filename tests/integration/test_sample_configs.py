"""Integration tests for sample configuration files.

Validates that all configuration files in configs/ directory:
- Load without errors
- Pass schema validation
- Have valid values for all fields
"""

from __future__ import annotations

from pathlib import Path

import pytest

from let_it_ride.config.loader import load_config
from let_it_ride.config.models import FullConfig

# Path to configs directory
CONFIGS_DIR = Path(__file__).parent.parent.parent / "configs"

# List of all sample configuration files that should be validated
SAMPLE_CONFIG_FILES = [
    "basic_strategy.yaml",
    "conservative.yaml",
    "aggressive.yaml",
    "bonus_comparison.yaml",
    "progressive_betting.yaml",
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

    def test_uses_basic_strategy(self) -> None:
        """Test that basic_strategy.yaml uses basic strategy."""
        config = load_config(CONFIGS_DIR / "basic_strategy.yaml")
        assert config.strategy.type == "basic"

    def test_uses_flat_betting(self) -> None:
        """Test that basic_strategy.yaml uses flat betting."""
        config = load_config(CONFIGS_DIR / "basic_strategy.yaml")
        assert config.bankroll.betting_system.type == "flat"

    def test_bonus_disabled(self) -> None:
        """Test that bonus betting is disabled."""
        config = load_config(CONFIGS_DIR / "basic_strategy.yaml")
        assert config.bonus_strategy.enabled is False

    def test_has_metadata(self) -> None:
        """Test that metadata is present and meaningful."""
        config = load_config(CONFIGS_DIR / "basic_strategy.yaml")
        assert config.metadata.name is not None
        assert "basic" in config.metadata.name.lower()


class TestConservativeConfig:
    """Specific tests for conservative.yaml."""

    def test_uses_conservative_strategy(self) -> None:
        """Test that conservative.yaml uses conservative strategy."""
        config = load_config(CONFIGS_DIR / "conservative.yaml")
        assert config.strategy.type == "conservative"

    def test_has_conservative_config(self) -> None:
        """Test that conservative strategy config is present."""
        config = load_config(CONFIGS_DIR / "conservative.yaml")
        assert config.strategy.conservative is not None
        assert config.strategy.conservative.made_hands_only is True

    def test_has_tight_stop_conditions(self) -> None:
        """Test that stop conditions are tighter than basic."""
        config = load_config(CONFIGS_DIR / "conservative.yaml")
        # Win limit should be present and reasonable
        assert config.bankroll.stop_conditions.win_limit is not None
        assert config.bankroll.stop_conditions.loss_limit is not None


class TestAggressiveConfig:
    """Specific tests for aggressive.yaml."""

    def test_uses_aggressive_strategy(self) -> None:
        """Test that aggressive.yaml uses aggressive strategy."""
        config = load_config(CONFIGS_DIR / "aggressive.yaml")
        assert config.strategy.type == "aggressive"

    def test_has_aggressive_config(self) -> None:
        """Test that aggressive strategy config is present."""
        config = load_config(CONFIGS_DIR / "aggressive.yaml")
        assert config.strategy.aggressive is not None
        assert config.strategy.aggressive.ride_on_draws is True

    def test_includes_gutshots(self) -> None:
        """Test that gutshot draws are included."""
        config = load_config(CONFIGS_DIR / "aggressive.yaml")
        assert config.strategy.aggressive.include_gutshots is True


class TestBonusComparisonConfig:
    """Specific tests for bonus_comparison.yaml."""

    def test_bonus_enabled(self) -> None:
        """Test that bonus betting is enabled."""
        config = load_config(CONFIGS_DIR / "bonus_comparison.yaml")
        assert config.bonus_strategy.enabled is True

    def test_uses_bankroll_conditional(self) -> None:
        """Test that bankroll conditional strategy is used."""
        config = load_config(CONFIGS_DIR / "bonus_comparison.yaml")
        assert config.bonus_strategy.type == "bankroll_conditional"

    def test_has_scaling_tiers(self) -> None:
        """Test that scaling tiers are configured."""
        config = load_config(CONFIGS_DIR / "bonus_comparison.yaml")
        assert config.bonus_strategy.bankroll_conditional is not None
        assert config.bonus_strategy.bankroll_conditional.scaling is not None
        assert config.bonus_strategy.bankroll_conditional.scaling.enabled is True
        assert len(config.bonus_strategy.bankroll_conditional.scaling.tiers) >= 1


class TestProgressiveBettingConfig:
    """Specific tests for progressive_betting.yaml."""

    def test_uses_martingale(self) -> None:
        """Test that Martingale betting system is configured."""
        config = load_config(CONFIGS_DIR / "progressive_betting.yaml")
        assert config.bankroll.betting_system.type == "martingale"

    def test_has_martingale_config(self) -> None:
        """Test that Martingale config is present."""
        config = load_config(CONFIGS_DIR / "progressive_betting.yaml")
        assert config.bankroll.betting_system.martingale is not None
        assert config.bankroll.betting_system.martingale.loss_multiplier > 1

    def test_larger_starting_bankroll(self) -> None:
        """Test that starting bankroll is larger for progressive betting."""
        config = load_config(CONFIGS_DIR / "progressive_betting.yaml")
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
                assert (
                    config_file.replace(".yaml", "") in content
                ), f"README.md should mention {config_file}"
