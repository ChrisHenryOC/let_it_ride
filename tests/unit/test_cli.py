"""Unit tests for CLI functionality.

Tests CLI structure, help messages, and basic command parsing.
For full integration tests, see tests/integration/test_cli.py.
"""

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
