"""Tests for CLI functionality."""

from typer.testing import CliRunner

from let_it_ride import __version__
from let_it_ride.cli import app

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


def test_run_command_help() -> None:
    """Test that run command shows help."""
    result = runner.invoke(app, ["run", "--help"])
    assert result.exit_code == 0
    assert "Run a simulation" in result.stdout
    assert "CONFIG" in result.stdout


def test_validate_command_help() -> None:
    """Test that validate command shows help."""
    result = runner.invoke(app, ["validate", "--help"])
    assert result.exit_code == 0
    assert "Validate a configuration" in result.stdout
    assert "CONFIG" in result.stdout


def test_run_command_with_config() -> None:
    """Test run command accepts a config path."""
    result = runner.invoke(app, ["run", "test_config.yaml"])
    assert result.exit_code == 0
    assert "Running simulation with config" in result.stdout
    assert "test_config.yaml" in result.stdout


def test_validate_command_with_config() -> None:
    """Test validate command accepts a config path."""
    result = runner.invoke(app, ["validate", "test_config.yaml"])
    assert result.exit_code == 0
    assert "Validating config" in result.stdout
    assert "test_config.yaml" in result.stdout
