"""Unit tests for CLI functionality.

Tests CLI structure, help messages, and basic command parsing.
For full integration tests, see tests/integration/test_cli.py.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from let_it_ride import __version__
from let_it_ride.cli import _load_config_with_errors, app

runner = CliRunner()


def test_version_flag() -> None:
    """Test that --version flag displays correct version."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_help_flag() -> None:
    """Test that --help flag displays help message."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Let It Ride Strategy Simulator" in result.stdout
    assert "run" in result.stdout
    assert "validate" in result.stdout


def test_no_args_shows_help() -> None:
    """Test that running with no arguments shows help."""
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "Let It Ride Strategy Simulator" in result.stdout


def test_run_command_help() -> None:
    """Test that run command shows help."""
    result = runner.invoke(app, ["run", "--help"])
    assert result.exit_code == 0
    assert "Run a simulation" in result.stdout
    assert "CONFIG" in result.stdout
    assert "--output" in result.stdout
    assert "--seed" in result.stdout
    assert "--sessions" in result.stdout
    assert "--quiet" in result.stdout
    assert "--verbose" in result.stdout


def test_validate_command_help() -> None:
    """Test that validate command shows help."""
    result = runner.invoke(app, ["validate", "--help"])
    assert result.exit_code == 0
    assert "Validate a configuration" in result.stdout
    assert "CONFIG" in result.stdout


def test_run_missing_config_argument() -> None:
    """Test that run command requires config argument."""
    result = runner.invoke(app, ["run"])
    assert result.exit_code == 2  # Typer returns 2 for missing required args
    assert "CONFIG" in result.stdout or "Missing argument" in result.stdout


def test_validate_missing_config_argument() -> None:
    """Test that validate command requires config argument."""
    result = runner.invoke(app, ["validate"])
    assert result.exit_code == 2  # Typer returns 2 for missing required args
    assert "CONFIG" in result.stdout or "Missing argument" in result.stdout


def test_run_nonexistent_config() -> None:
    """Test that run command fails gracefully with nonexistent file."""
    result = runner.invoke(app, ["run", "nonexistent_config_file.yaml"])
    assert result.exit_code == 1
    # Should show error about file not found
    assert "error" in result.stdout.lower() or "not found" in result.stdout.lower()


def test_validate_nonexistent_config() -> None:
    """Test that validate command fails gracefully with nonexistent file."""
    result = runner.invoke(app, ["validate", "nonexistent_config_file.yaml"])
    assert result.exit_code == 1
    # Should show error about file not found
    assert "error" in result.stdout.lower() or "not found" in result.stdout.lower()


def test_run_sessions_zero_rejected() -> None:
    """Test that --sessions 0 is rejected by Typer's min=1 constraint."""
    result = runner.invoke(app, ["run", "config.yaml", "--sessions", "0"])
    assert result.exit_code == 2  # Typer validation error


def test_run_sessions_negative_rejected() -> None:
    """Test that negative --sessions is rejected."""
    result = runner.invoke(app, ["run", "config.yaml", "--sessions", "-1"])
    assert result.exit_code == 2  # Typer validation error


class TestLoadConfigWithErrors:
    """Unit tests for _load_config_with_errors helper."""

    def test_file_not_found_error(self) -> None:
        """Test handling of ConfigFileNotFoundError."""
        import typer

        with pytest.raises(typer.Exit) as exc_info:
            _load_config_with_errors(Path("nonexistent_file.yaml"))
        assert exc_info.value.exit_code == 1

    def test_parse_error(self) -> None:
        """Test handling of ConfigParseError with details."""
        import typer

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [unclosed")
            f.flush()

            with pytest.raises(typer.Exit) as exc_info:
                _load_config_with_errors(Path(f.name))
            assert exc_info.value.exit_code == 1

    def test_validation_error(self) -> None:
        """Test handling of ConfigValidationError."""
        import typer

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            # Valid YAML but invalid config (missing required fields)
            f.write("simulation:\n  num_sessions: -1")
            f.flush()

            with pytest.raises(typer.Exit) as exc_info:
                _load_config_with_errors(Path(f.name))
            assert exc_info.value.exit_code == 1


class TestSimulationErrorHandling:
    """Tests for simulation and export error handling."""

    def test_simulation_runtime_error(self) -> None:
        """Test that simulation errors are caught and reported."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(
                """
simulation:
  num_sessions: 1
  hands_per_session: 100
  random_seed: 42
bankroll:
  starting_amount: 1000
  base_bet: 10
strategy:
  type: basic
"""
            )
            f.flush()

            with patch("let_it_ride.cli.SimulationController") as mock_controller:
                mock_instance = MagicMock()
                mock_instance.run.side_effect = RuntimeError("Simulation failed")
                mock_controller.return_value = mock_instance

                result = runner.invoke(app, ["run", f.name, "--quiet"])

            assert result.exit_code == 1
            assert "simulation error" in result.stdout.lower()

    def test_export_error(self) -> None:
        """Test that export errors are caught and reported."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(
                """
simulation:
  num_sessions: 1
  hands_per_session: 100
  random_seed: 42
bankroll:
  starting_amount: 1000
  base_bet: 10
strategy:
  type: basic
"""
            )
            f.flush()

            # Mock successful simulation but failed export
            with (
                patch("let_it_ride.cli.SimulationController") as mock_controller,
                patch("let_it_ride.cli.CSVExporter") as mock_exporter,
            ):
                mock_sim_instance = MagicMock()
                mock_results = MagicMock()
                mock_results.total_hands = 100
                mock_results.start_time = MagicMock()
                mock_results.end_time = MagicMock()
                mock_results.end_time.__sub__ = MagicMock(
                    return_value=MagicMock(total_seconds=MagicMock(return_value=1.0))
                )
                mock_results.session_results = [MagicMock(session_profit=10.0)]
                mock_sim_instance.run.return_value = mock_results
                mock_controller.return_value = mock_sim_instance

                mock_export_instance = MagicMock()
                mock_export_instance.export_all.side_effect = OSError(
                    "Permission denied"
                )
                mock_exporter.return_value = mock_export_instance

                result = runner.invoke(app, ["run", f.name, "--quiet"])

            assert result.exit_code == 1
            assert "export error" in result.stdout.lower()
