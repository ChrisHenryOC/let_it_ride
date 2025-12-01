"""Unit tests for configuration loader."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from let_it_ride.config.loader import (
    ConfigFileNotFoundError,
    ConfigParseError,
    ConfigValidationError,
    load_config,
    load_config_from_string,
    validate_config,
)
from let_it_ride.config.models import FullConfig

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_minimal_config(self, tmp_path: Path) -> None:
        """Test loading a minimal (empty) configuration file."""
        config_file = tmp_path / "minimal.yaml"
        config_file.write_text("")

        config = load_config(config_file)
        assert isinstance(config, FullConfig)
        # All defaults should be applied
        assert config.simulation.num_sessions == 10000
        assert config.bankroll.starting_amount == 500.0

    def test_load_basic_config(self, tmp_path: Path) -> None:
        """Test loading a basic configuration file."""
        config_file = tmp_path / "basic.yaml"
        config_file.write_text(
            """
simulation:
  num_sessions: 50000
  hands_per_session: 100

bankroll:
  starting_amount: 1000.0
  base_bet: 10.0
"""
        )

        config = load_config(config_file)
        assert config.simulation.num_sessions == 50000
        assert config.simulation.hands_per_session == 100
        assert config.bankroll.starting_amount == 1000.0
        assert config.bankroll.base_bet == 10.0

    def test_load_full_config(self, tmp_path: Path) -> None:
        """Test loading a comprehensive configuration file."""
        config_file = tmp_path / "full.yaml"
        config_file.write_text(
            """
metadata:
  name: "Full Test Configuration"
  description: "Testing all options"
  version: "1.0"

simulation:
  num_sessions: 100000
  hands_per_session: 200
  random_seed: 42
  workers: 4
  progress_interval: 5000
  detailed_logging: true

deck:
  shuffle_algorithm: cryptographic

bankroll:
  starting_amount: 500.0
  base_bet: 5.0
  stop_conditions:
    win_limit: 250.0
    loss_limit: 200.0
    max_hands: 200
  betting_system:
    type: flat

strategy:
  type: basic

bonus_strategy:
  enabled: true
  paytable: paytable_b
  type: static
  static:
    amount: 1.0

output:
  directory: ./results/test
  prefix: full_test
"""
        )

        config = load_config(config_file)
        assert config.metadata.name == "Full Test Configuration"
        assert config.simulation.num_sessions == 100000
        assert config.simulation.random_seed == 42
        assert config.simulation.workers == 4
        assert config.simulation.detailed_logging is True
        assert config.deck.shuffle_algorithm == "cryptographic"
        assert config.bankroll.stop_conditions.win_limit == 250.0
        assert config.bonus_strategy.enabled is True
        assert config.output.directory == "./results/test"

    def test_load_with_string_path(self, tmp_path: Path) -> None:
        """Test loading with a string path."""
        config_file = tmp_path / "string_path.yaml"
        config_file.write_text("simulation:\n  num_sessions: 500")

        config = load_config(str(config_file))
        assert config.simulation.num_sessions == 500

    def test_file_not_found(self, tmp_path: Path) -> None:
        """Test loading non-existent file raises error."""
        config_file = tmp_path / "nonexistent.yaml"

        with pytest.raises(ConfigFileNotFoundError) as exc_info:
            load_config(config_file)
        assert "not found" in str(exc_info.value).lower()
        assert str(config_file) in str(exc_info.value)

    def test_directory_not_file(self, tmp_path: Path) -> None:
        """Test loading a directory raises error."""
        with pytest.raises(ConfigFileNotFoundError) as exc_info:
            load_config(tmp_path)
        assert "not a file" in str(exc_info.value).lower()

    def test_invalid_yaml_syntax(self, tmp_path: Path) -> None:
        """Test invalid YAML syntax raises error."""
        config_file = tmp_path / "invalid_yaml.yaml"
        config_file.write_text(
            """
simulation:
  num_sessions: [unclosed bracket
"""
        )

        with pytest.raises(ConfigParseError) as exc_info:
            load_config(config_file)
        assert "Invalid YAML" in str(exc_info.value)

    def test_invalid_yaml_indentation(self, tmp_path: Path) -> None:
        """Test invalid YAML indentation raises error."""
        config_file = tmp_path / "bad_indent.yaml"
        config_file.write_text(
            """
simulation:
num_sessions: 1000  # wrong indentation
"""
        )

        # This will parse but fail validation due to extra field at root
        with pytest.raises(ConfigValidationError):
            load_config(config_file)

    def test_validation_error_num_sessions(self, tmp_path: Path) -> None:
        """Test validation error for num_sessions out of range."""
        config_file = tmp_path / "bad_num_sessions.yaml"
        config_file.write_text(
            """
simulation:
  num_sessions: -1
"""
        )

        with pytest.raises(ConfigValidationError) as exc_info:
            load_config(config_file)
        assert "validation failed" in str(exc_info.value).lower()

    def test_validation_error_bankroll_insufficient(self, tmp_path: Path) -> None:
        """Test validation error for insufficient starting bankroll."""
        config_file = tmp_path / "bad_bankroll.yaml"
        config_file.write_text(
            """
bankroll:
  starting_amount: 10.0
  base_bet: 5.0
"""
        )

        with pytest.raises(ConfigValidationError) as exc_info:
            load_config(config_file)
        assert "3x base_bet" in str(exc_info.value)

    def test_validation_error_unknown_field(self, tmp_path: Path) -> None:
        """Test validation error for unknown fields."""
        config_file = tmp_path / "unknown_field.yaml"
        config_file.write_text(
            """
simulation:
  num_sessions: 1000
  unknown_option: true
"""
        )

        with pytest.raises(ConfigValidationError) as exc_info:
            load_config(config_file)
        assert "extra_forbidden" in str(exc_info.value)

    def test_validation_error_invalid_strategy_type(self, tmp_path: Path) -> None:
        """Test validation error for invalid strategy type."""
        config_file = tmp_path / "bad_strategy.yaml"
        config_file.write_text(
            """
strategy:
  type: super_aggressive
"""
        )

        with pytest.raises(ConfigValidationError):
            load_config(config_file)


class TestLoadConfigFromString:
    """Tests for load_config_from_string function."""

    def test_empty_string(self) -> None:
        """Test loading from empty string returns defaults."""
        config = load_config_from_string("")
        assert isinstance(config, FullConfig)
        assert config.simulation.num_sessions == 10000

    def test_basic_yaml_string(self) -> None:
        """Test loading from YAML string."""
        yaml_content = """
simulation:
  num_sessions: 25000
  random_seed: 123
"""
        config = load_config_from_string(yaml_content)
        assert config.simulation.num_sessions == 25000
        assert config.simulation.random_seed == 123

    def test_invalid_yaml_string(self) -> None:
        """Test invalid YAML string raises error."""
        yaml_content = "simulation: [unclosed"

        with pytest.raises(ConfigParseError):
            load_config_from_string(yaml_content)

    def test_validation_error_string(self) -> None:
        """Test validation error from YAML string."""
        yaml_content = """
simulation:
  num_sessions: 0
"""
        with pytest.raises(ConfigValidationError):
            load_config_from_string(yaml_content)


class TestValidateConfig:
    """Tests for validate_config function."""

    def test_empty_dict(self) -> None:
        """Test validating empty dictionary returns defaults."""
        config = validate_config({})
        assert isinstance(config, FullConfig)
        assert config.simulation.num_sessions == 10000

    def test_partial_dict(self) -> None:
        """Test validating partial dictionary."""
        data: dict[str, Any] = {
            "simulation": {"num_sessions": 5000},
            "bankroll": {"starting_amount": 750.0, "base_bet": 5.0},
        }
        config = validate_config(data)
        assert config.simulation.num_sessions == 5000
        assert config.bankroll.starting_amount == 750.0

    def test_nested_dict(self) -> None:
        """Test validating deeply nested dictionary."""
        data: dict[str, Any] = {
            "bankroll": {
                "starting_amount": 500.0,
                "base_bet": 5.0,
                "stop_conditions": {
                    "win_limit": 300.0,
                    "max_hands": 150,
                },
                "betting_system": {
                    "type": "martingale",
                    "martingale": {
                        "loss_multiplier": 2.0,
                        "max_bet": 500.0,
                    },
                },
            },
        }
        config = validate_config(data)
        assert config.bankroll.stop_conditions.win_limit == 300.0
        assert config.bankroll.stop_conditions.max_hands == 150
        assert config.bankroll.betting_system.type == "martingale"

    def test_validation_error_dict(self) -> None:
        """Test validation error from dictionary."""
        data: dict[str, Any] = {
            "simulation": {"num_sessions": -100},
        }
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_config(data)
        assert "validation failed" in str(exc_info.value).lower()


class TestErrorMessages:
    """Tests for error message formatting."""

    def test_file_not_found_message_has_path(self, tmp_path: Path) -> None:
        """Test file not found error includes the path."""
        config_file = tmp_path / "missing.yaml"

        with pytest.raises(ConfigFileNotFoundError) as exc_info:
            load_config(config_file)

        error = exc_info.value
        assert str(config_file) in error.message
        assert error.details is not None
        # Details should contain helpful info about the file location
        assert "ensure" in error.details.lower() or str(config_file) in error.details

    def test_parse_error_message_has_details(self, tmp_path: Path) -> None:
        """Test parse error includes YAML error details."""
        config_file = tmp_path / "bad.yaml"
        config_file.write_text("key: {invalid: yaml:")

        with pytest.raises(ConfigParseError) as exc_info:
            load_config(config_file)

        error = exc_info.value
        assert str(config_file) in error.message
        assert error.details is not None

    def test_validation_error_message_has_location(self, tmp_path: Path) -> None:
        """Test validation error includes field location."""
        config_file = tmp_path / "invalid.yaml"
        config_file.write_text(
            """
simulation:
  num_sessions: "not a number"
"""
        )

        with pytest.raises(ConfigValidationError) as exc_info:
            load_config(config_file)

        error = exc_info.value
        assert error.details is not None
        assert "num_sessions" in error.details

    def test_error_str_includes_details(self, tmp_path: Path) -> None:
        """Test error string representation includes details."""
        config_file = tmp_path / "bad.yaml"
        config_file.write_text("simulation:\n  num_sessions: 0")

        with pytest.raises(ConfigValidationError) as exc_info:
            load_config(config_file)

        error_str = str(exc_info.value)
        assert "Details:" in error_str


class TestConfigurationIntegration:
    """Integration tests for configuration loading."""

    def test_all_strategy_types_loadable(self, tmp_path: Path) -> None:
        """Test all strategy types can be loaded."""
        # Simple strategy types that don't require config sections
        for strategy in ["basic", "always_ride", "always_pull"]:
            config_file = tmp_path / f"{strategy}.yaml"
            config_file.write_text(
                f"""
strategy:
  type: {strategy}
"""
            )
            config = load_config(config_file)
            assert config.strategy.type == strategy

        # Strategy types that require config sections
        config_file = tmp_path / "conservative.yaml"
        config_file.write_text(
            """
strategy:
  type: conservative
  conservative:
    made_hands_only: true
"""
        )
        config = load_config(config_file)
        assert config.strategy.type == "conservative"

        config_file = tmp_path / "aggressive.yaml"
        config_file.write_text(
            """
strategy:
  type: aggressive
  aggressive:
    ride_on_draws: true
"""
        )
        config = load_config(config_file)
        assert config.strategy.type == "aggressive"

    def test_all_bonus_strategy_types_loadable(self, tmp_path: Path) -> None:
        """Test all bonus strategy types can be loaded."""
        for bonus_type in ["never", "always", "static"]:
            config_file = tmp_path / f"bonus_{bonus_type}.yaml"
            yaml_content = f"""
bonus_strategy:
  enabled: true
  type: {bonus_type}
"""
            if bonus_type == "always":
                yaml_content += """
  always:
    amount: 1.0
"""
            elif bonus_type == "static":
                yaml_content += """
  static:
    amount: 2.0
"""
            config_file.write_text(yaml_content)
            config = load_config(config_file)
            assert config.bonus_strategy.type == bonus_type

    def test_all_betting_system_types_loadable(self, tmp_path: Path) -> None:
        """Test all betting system types can be loaded."""
        for betting_type in ["flat", "proportional", "martingale"]:
            config_file = tmp_path / f"betting_{betting_type}.yaml"
            yaml_content = f"""
bankroll:
  starting_amount: 500.0
  base_bet: 5.0
  betting_system:
    type: {betting_type}
"""
            if betting_type == "proportional":
                yaml_content += """
    proportional:
      bankroll_percentage: 0.05
"""
            elif betting_type == "martingale":
                yaml_content += """
    martingale:
      loss_multiplier: 2.0
"""
            config_file.write_text(yaml_content)
            config = load_config(config_file)
            assert config.bankroll.betting_system.type == betting_type

    def test_round_trip_preservation(self, tmp_path: Path) -> None:
        """Test that loaded config values are preserved after serialization."""
        config_file = tmp_path / "roundtrip.yaml"
        config_file.write_text(
            """
simulation:
  num_sessions: 12345
  hands_per_session: 789
  random_seed: 999
"""
        )

        config = load_config(config_file)
        # Re-validate from the model's dict representation
        config2 = validate_config(config.model_dump())

        assert config2.simulation.num_sessions == 12345
        assert config2.simulation.hands_per_session == 789
        assert config2.simulation.random_seed == 999
