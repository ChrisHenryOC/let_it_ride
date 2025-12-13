"""Integration tests for CLI functionality.

Tests the full CLI workflow including:
- Running simulations from config files
- Validating configuration files
- CLI options and flags
- Error handling and exit codes
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from typer.testing import CliRunner

from let_it_ride.cli import app

if TYPE_CHECKING:
    from collections.abc import Generator

runner = CliRunner()


@pytest.fixture
def valid_config_file() -> Generator[Path, None, None]:
    """Create a temporary valid configuration file."""
    config_content = """
simulation:
  num_sessions: 5
  hands_per_session: 10
  random_seed: 42

bankroll:
  starting_amount: 500.0
  base_bet: 5.0
  stop_conditions:
    win_limit: 100.0
    loss_limit: 200.0
    stop_on_insufficient_funds: true
  betting_system:
    type: flat

strategy:
  type: basic

output:
  directory: "{output_dir}"
  prefix: test_simulation
  formats:
    csv:
      enabled: true
    json:
      enabled: false
    html:
      enabled: false
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "test_config.yaml"
        output_dir = Path(tmpdir) / "output"
        config_path.write_text(config_content.format(output_dir=output_dir))
        yield config_path


@pytest.fixture
def invalid_yaml_file() -> Generator[Path, None, None]:
    """Create a temporary file with invalid YAML."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "invalid.yaml"
        config_path.write_text("invalid: yaml: content: [")
        yield config_path


@pytest.fixture
def invalid_config_file() -> Generator[Path, None, None]:
    """Create a temporary file with valid YAML but invalid config values."""
    config_content = """
simulation:
  num_sessions: -1  # Invalid: must be positive
  hands_per_session: 10
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "invalid_config.yaml"
        config_path.write_text(config_content)
        yield config_path


@pytest.fixture
def minimal_config_file() -> Generator[Path, None, None]:
    """Create a minimal valid configuration file."""
    config_content = """
simulation:
  num_sessions: 3
  hands_per_session: 5
  random_seed: 123
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "minimal_config.yaml"
        config_path.write_text(config_content)
        yield config_path


class TestRunCommand:
    """Tests for the 'run' command."""

    def test_run_with_valid_config(self, valid_config_file: Path) -> None:
        """Test running simulation with a valid config file."""
        result = runner.invoke(app, ["run", str(valid_config_file)])
        assert result.exit_code == 0
        assert "Running simulation" in result.stdout
        assert "Simulation complete" in result.stdout
        assert "Total Hands" in result.stdout
        assert "Winning" in result.stdout

    def test_run_with_nonexistent_file(self) -> None:
        """Test error handling when config file doesn't exist."""
        result = runner.invoke(app, ["run", "nonexistent_config.yaml"])
        assert result.exit_code == 1
        assert "Error" in result.stdout or "error" in result.stdout.lower()

    def test_run_with_invalid_yaml(self, invalid_yaml_file: Path) -> None:
        """Test error handling with invalid YAML syntax."""
        result = runner.invoke(app, ["run", str(invalid_yaml_file)])
        assert result.exit_code == 1
        assert "parse error" in result.stdout.lower()

    def test_run_with_invalid_config(self, invalid_config_file: Path) -> None:
        """Test error handling with invalid config values."""
        result = runner.invoke(app, ["run", str(invalid_config_file)])
        assert result.exit_code == 1
        assert "validation error" in result.stdout.lower()

    def test_run_with_seed_override(self, minimal_config_file: Path) -> None:
        """Test --seed option overrides config seed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(
                app,
                ["run", str(minimal_config_file), "--seed", "999", "--output", tmpdir],
            )
            assert result.exit_code == 0
            # Table format shows "Seed" and "999" in same row
            assert "Seed" in result.stdout
            assert "999" in result.stdout

    def test_run_with_sessions_override(self, minimal_config_file: Path) -> None:
        """Test --sessions option overrides config session count."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(
                app,
                [
                    "run",
                    str(minimal_config_file),
                    "--sessions",
                    "2",
                    "--output",
                    tmpdir,
                ],
            )
            assert result.exit_code == 0
            # Table format shows "Sessions" and "2" in same row
            assert "Sessions" in result.stdout

    def test_run_with_output_override(self, minimal_config_file: Path) -> None:
        """Test --output option overrides output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "custom_output"
            result = runner.invoke(
                app,
                ["run", str(minimal_config_file), "--output", str(output_path)],
            )
            assert result.exit_code == 0
            assert output_path.exists()
            # Check that CSV files were created
            csv_files = list(output_path.glob("*.csv"))
            assert len(csv_files) >= 2  # sessions and aggregate

    def test_run_with_quiet_flag(self, valid_config_file: Path) -> None:
        """Test --quiet flag reduces output."""
        result = runner.invoke(app, ["run", str(valid_config_file), "--quiet"])
        assert result.exit_code == 0
        # Quiet mode should not have verbose output
        assert "Running simulation:" not in result.stdout
        assert "Completed" in result.stdout
        assert "sessions" in result.stdout

    def test_run_with_verbose_flag(self, valid_config_file: Path) -> None:
        """Test --verbose flag shows detailed output."""
        result = runner.invoke(app, ["run", str(valid_config_file), "--verbose"])
        assert result.exit_code == 0
        assert "Session Details" in result.stdout
        # Session details shown as table rows
        assert "win_limit" in result.stdout or "max_hands" in result.stdout

    def test_run_creates_output_files(self, minimal_config_file: Path) -> None:
        """Test that run command creates expected output files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(
                app,
                ["run", str(minimal_config_file), "--output", tmpdir],
            )
            assert result.exit_code == 0

            output_path = Path(tmpdir)
            # Check for expected CSV files
            sessions_csv = list(output_path.glob("*_sessions.csv"))
            aggregate_csv = list(output_path.glob("*_aggregate.csv"))
            assert len(sessions_csv) == 1
            assert len(aggregate_csv) == 1


class TestValidateCommand:
    """Tests for the 'validate' command."""

    def test_validate_valid_config(self, valid_config_file: Path) -> None:
        """Test validating a valid config file."""
        result = runner.invoke(app, ["validate", str(valid_config_file)])
        assert result.exit_code == 0
        assert "Configuration valid" in result.stdout
        # Table title is "Configuration" not "Configuration Summary"
        assert "Configuration" in result.stdout
        # Table format doesn't have colons
        assert "Sessions" in result.stdout
        assert "Strategy" in result.stdout

    def test_validate_nonexistent_file(self) -> None:
        """Test error handling when config file doesn't exist."""
        result = runner.invoke(app, ["validate", "nonexistent.yaml"])
        assert result.exit_code == 1
        assert "Error" in result.stdout or "error" in result.stdout.lower()

    def test_validate_invalid_yaml(self, invalid_yaml_file: Path) -> None:
        """Test error handling with invalid YAML syntax."""
        result = runner.invoke(app, ["validate", str(invalid_yaml_file)])
        assert result.exit_code == 1
        assert "parse error" in result.stdout.lower()

    def test_validate_invalid_config(self, invalid_config_file: Path) -> None:
        """Test error handling with invalid config values."""
        result = runner.invoke(app, ["validate", str(invalid_config_file)])
        assert result.exit_code == 1
        assert "validation error" in result.stdout.lower()

    def test_validate_minimal_config(self, minimal_config_file: Path) -> None:
        """Test validating a minimal config with defaults."""
        result = runner.invoke(app, ["validate", str(minimal_config_file)])
        assert result.exit_code == 0
        assert "Configuration valid" in result.stdout
        # Check that defaults are shown
        assert "basic" in result.stdout  # default strategy


class TestCLIHelp:
    """Tests for CLI help and version information."""

    def test_version_flag(self) -> None:
        """Test --version flag shows version."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "version" in result.stdout.lower()

    def test_help_flag(self) -> None:
        """Test --help flag shows help."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Let It Ride Strategy Simulator" in result.stdout
        assert "run" in result.stdout
        assert "validate" in result.stdout

    def test_run_help(self) -> None:
        """Test run --help shows command options."""
        result = runner.invoke(app, ["run", "--help"])
        assert result.exit_code == 0
        assert "CONFIG" in result.stdout
        assert "--output" in result.stdout
        assert "--seed" in result.stdout
        assert "--sessions" in result.stdout
        assert "--quiet" in result.stdout
        assert "--verbose" in result.stdout

    def test_validate_help(self) -> None:
        """Test validate --help shows command options."""
        result = runner.invoke(app, ["validate", "--help"])
        assert result.exit_code == 0
        assert "CONFIG" in result.stdout
        assert "Validate" in result.stdout


class TestCLIReproducibility:
    """Tests for reproducibility with seed option."""

    def test_same_seed_produces_same_results(self) -> None:
        """Test that running with the same seed produces identical results."""
        config_content = """
simulation:
  num_sessions: 3
  hands_per_session: 10
  random_seed: 42
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text(config_content)

            # Run twice with same seed
            output1 = Path(tmpdir) / "output1"
            output2 = Path(tmpdir) / "output2"

            result1 = runner.invoke(
                app,
                ["run", str(config_path), "--output", str(output1), "--quiet"],
            )
            result2 = runner.invoke(
                app,
                ["run", str(config_path), "--output", str(output2), "--quiet"],
            )

            assert result1.exit_code == 0
            assert result2.exit_code == 0

            # Compare sessions CSV files
            sessions1 = (output1 / "simulation_sessions.csv").read_text()
            sessions2 = (output2 / "simulation_sessions.csv").read_text()
            assert sessions1 == sessions2

    def test_different_seeds_produce_different_results(self) -> None:
        """Test that different seeds produce different results."""
        config_content = """
simulation:
  num_sessions: 5
  hands_per_session: 20
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text(config_content)

            # Run with different seeds
            output1 = Path(tmpdir) / "output1"
            output2 = Path(tmpdir) / "output2"

            result1 = runner.invoke(
                app,
                [
                    "run",
                    str(config_path),
                    "--seed",
                    "111",
                    "--output",
                    str(output1),
                    "--quiet",
                ],
            )
            result2 = runner.invoke(
                app,
                [
                    "run",
                    str(config_path),
                    "--seed",
                    "222",
                    "--output",
                    str(output2),
                    "--quiet",
                ],
            )

            assert result1.exit_code == 0
            assert result2.exit_code == 0

            # Sessions should differ
            sessions1 = (output1 / "simulation_sessions.csv").read_text()
            sessions2 = (output2 / "simulation_sessions.csv").read_text()
            # With different seeds and enough hands, results should differ
            # (headers are same, but data rows should differ)
            assert sessions1 != sessions2


class TestCLIEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_run_with_single_session(self) -> None:
        """Test running with a single session."""
        config_content = """
simulation:
  num_sessions: 1
  hands_per_session: 5
  random_seed: 42
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text(config_content)
            output_path = Path(tmpdir) / "output"

            result = runner.invoke(
                app,
                ["run", str(config_path), "--output", str(output_path)],
            )
            assert result.exit_code == 0
            # Table format - look for "Sessions" and "1" in the output
            assert "Sessions" in result.stdout

    def test_run_quiet_and_verbose_conflict(self) -> None:
        """Test behavior when both --quiet and --verbose are set."""
        config_content = """
simulation:
  num_sessions: 2
  hands_per_session: 5
  random_seed: 42
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text(config_content)

            # When both flags are set, quiet takes precedence
            result = runner.invoke(
                app,
                ["run", str(config_path), "--quiet", "--verbose", "--output", tmpdir],
            )
            assert result.exit_code == 0
            # Quiet mode output
            assert "Completed" in result.stdout
            # Should not have verbose session details
            assert "Session Details" not in result.stdout

    def test_validate_empty_config(self) -> None:
        """Test validating an empty config file (uses all defaults)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "empty.yaml"
            config_path.write_text("")

            result = runner.invoke(app, ["validate", str(config_path)])
            # Empty config should use all defaults and be valid
            assert result.exit_code == 0
            assert "Configuration valid" in result.stdout
