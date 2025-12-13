"""End-to-end tests for CLI invocation.

These tests validate complete CLI workflows:
- Running simulations via CLI and verifying output files
- CLI with various options and flags
- Error handling for invalid inputs
- Reproducibility via CLI seed option
"""

from __future__ import annotations

import csv
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
def e2e_config_file() -> Generator[Path, None, None]:
    """Create a configuration file for E2E CLI testing.

    Configuration settings:
    - 100 sessions, 50 hands per session, seed 42
    - Starting bankroll: $500, base bet: $5
    - Stop conditions: win $200, lose $150
    - Strategy: basic, betting system: flat
    - Output: CSV and JSON enabled

    Yields:
        Path to the temporary config file. The file and its directory
        are automatically cleaned up after the test completes.
    """
    config_content = """
metadata:
  name: "E2E CLI Test"
  description: "Configuration for E2E CLI testing"

simulation:
  num_sessions: 100
  hands_per_session: 50
  random_seed: 42

bankroll:
  starting_amount: 500.0
  base_bet: 5.0
  stop_conditions:
    win_limit: 200.0
    loss_limit: 150.0
    stop_on_insufficient_funds: true
  betting_system:
    type: flat

strategy:
  type: basic

output:
  directory: "{output_dir}"
  prefix: e2e_test
  formats:
    csv:
      enabled: true
      include_sessions: true
      include_aggregate: true
    json:
      enabled: true
      pretty: true
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "e2e_config.yaml"
        output_dir = Path(tmpdir) / "output"
        config_path.write_text(config_content.format(output_dir=output_dir))
        yield config_path


@pytest.fixture
def large_e2e_config_file() -> Generator[Path, None, None]:
    """Create a configuration file for large-scale E2E CLI testing.

    Configuration settings:
    - 1000 sessions, 100 hands per session, seed 12345
    - 4 parallel workers
    - Starting bankroll: $500, base bet: $5
    - Stop conditions: win $250, lose $200
    - Strategy: basic, betting system: flat

    Yields:
        Path to the temporary config file. The file and its directory
        are automatically cleaned up after the test completes.
    """
    config_content = """
metadata:
  name: "Large E2E CLI Test"

simulation:
  num_sessions: 1000
  hands_per_session: 100
  random_seed: 12345
  workers: 4

bankroll:
  starting_amount: 500.0
  base_bet: 5.0
  stop_conditions:
    win_limit: 250.0
    loss_limit: 200.0
    stop_on_insufficient_funds: true
  betting_system:
    type: flat

strategy:
  type: basic
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "large_e2e_config.yaml"
        config_path.write_text(config_content)
        yield config_path


class TestCLIRunCommand:
    """Tests for CLI run command execution."""

    def test_run_creates_output_files(self, e2e_config_file: Path) -> None:
        """Verify run command creates expected output files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "results"

            result = runner.invoke(
                app,
                ["run", str(e2e_config_file), "--output", str(output_dir), "--quiet"],
            )

            assert result.exit_code == 0

            # Verify output files exist
            assert output_dir.exists()
            csv_files = list(output_dir.glob("*.csv"))
            assert len(csv_files) >= 2  # sessions and aggregate

    def test_run_sessions_csv_has_correct_count(self, e2e_config_file: Path) -> None:
        """Verify sessions CSV contains correct number of rows."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "results"

            result = runner.invoke(
                app,
                ["run", str(e2e_config_file), "--output", str(output_dir), "--quiet"],
            )

            assert result.exit_code == 0

            # Find and verify sessions CSV
            sessions_csv = list(output_dir.glob("*_sessions.csv"))
            assert len(sessions_csv) == 1

            with sessions_csv[0].open(encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert len(rows) == 100  # num_sessions from config

    def test_run_with_session_override(self, e2e_config_file: Path) -> None:
        """Verify --sessions option overrides config value."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "results"

            result = runner.invoke(
                app,
                [
                    "run",
                    str(e2e_config_file),
                    "--sessions",
                    "25",
                    "--output",
                    str(output_dir),
                    "--quiet",
                ],
            )

            assert result.exit_code == 0

            # Verify session count in output
            sessions_csv = list(output_dir.glob("*_sessions.csv"))
            with sessions_csv[0].open(encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert len(rows) == 25

    def test_run_with_seed_override(self) -> None:
        """Verify --seed option produces reproducible results."""
        config_content = """
simulation:
  num_sessions: 10
  hands_per_session: 20
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text(config_content)
            output1 = Path(tmpdir) / "output1"
            output2 = Path(tmpdir) / "output2"

            # Run twice with same seed
            result1 = runner.invoke(
                app,
                [
                    "run",
                    str(config_path),
                    "--seed",
                    "99999",
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
                    "99999",
                    "--output",
                    str(output2),
                    "--quiet",
                ],
            )

            assert result1.exit_code == 0
            assert result2.exit_code == 0

            # Compare output files
            csv1 = next(iter(output1.glob("*_sessions.csv"))).read_text()
            csv2 = next(iter(output2.glob("*_sessions.csv"))).read_text()

            assert csv1 == csv2

    def test_run_quiet_vs_normal_output(self, e2e_config_file: Path) -> None:
        """Verify quiet mode produces minimal output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "results"

            # Run with normal output
            result_normal = runner.invoke(
                app,
                ["run", str(e2e_config_file), "--output", str(output_dir)],
            )

            # Run with quiet output
            output_dir_quiet = Path(tmpdir) / "results_quiet"
            result_quiet = runner.invoke(
                app,
                [
                    "run",
                    str(e2e_config_file),
                    "--output",
                    str(output_dir_quiet),
                    "--quiet",
                ],
            )

            assert result_normal.exit_code == 0
            assert result_quiet.exit_code == 0

            # Quiet output should be shorter
            assert len(result_quiet.stdout) < len(result_normal.stdout)

    def test_run_verbose_output(self, e2e_config_file: Path) -> None:
        """Verify verbose mode provides session details."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "results"

            result = runner.invoke(
                app,
                ["run", str(e2e_config_file), "--output", str(output_dir), "--verbose"],
            )

            assert result.exit_code == 0
            assert "Session Details" in result.stdout

    def test_run_large_simulation(self, large_e2e_config_file: Path) -> None:
        """Verify CLI handles large simulations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "results"

            result = runner.invoke(
                app,
                [
                    "run",
                    str(large_e2e_config_file),
                    "--output",
                    str(output_dir),
                    "--quiet",
                ],
            )

            assert result.exit_code == 0

            # Verify correct session count
            sessions_csv = list(output_dir.glob("*_sessions.csv"))
            with sessions_csv[0].open(encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert len(rows) == 1000


class TestCLIValidateCommand:
    """Tests for CLI validate command."""

    def test_validate_valid_config(self, e2e_config_file: Path) -> None:
        """Verify validate accepts valid config."""
        result = runner.invoke(app, ["validate", str(e2e_config_file)])

        assert result.exit_code == 0
        assert "Configuration valid" in result.stdout

    def test_validate_invalid_config(self) -> None:
        """Verify validate rejects invalid config."""
        config_content = """
simulation:
  num_sessions: -1  # Invalid: must be positive
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "invalid.yaml"
            config_path.write_text(config_content)

            result = runner.invoke(app, ["validate", str(config_path)])

            assert result.exit_code == 1
            assert "validation error" in result.stdout.lower()


class TestCLIErrorHandling:
    """Tests for CLI error handling."""

    def test_run_nonexistent_config(self) -> None:
        """Verify run handles missing config file."""
        result = runner.invoke(app, ["run", "nonexistent_config.yaml"])

        assert result.exit_code == 1
        assert "error" in result.stdout.lower()

    def test_run_invalid_yaml(self) -> None:
        """Verify run handles invalid YAML syntax."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "invalid.yaml"
            config_path.write_text("invalid: yaml: syntax: [")

            result = runner.invoke(app, ["run", str(config_path)])

            assert result.exit_code == 1
            assert "parse error" in result.stdout.lower()

    def test_run_invalid_config_values(self) -> None:
        """Verify run handles invalid config values."""
        config_content = """
simulation:
  num_sessions: 100
bankroll:
  starting_amount: -500  # Invalid: must be positive
  base_bet: 5
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "invalid.yaml"
            config_path.write_text(config_content)

            result = runner.invoke(app, ["run", str(config_path)])

            assert result.exit_code == 1
            assert "validation error" in result.stdout.lower()


class TestCLIReproducibility:
    """Tests for CLI reproducibility with seeds."""

    def test_same_seed_same_results_different_runs(self) -> None:
        """Verify same seed produces identical results across CLI runs."""
        config_content = """
simulation:
  num_sessions: 50
  hands_per_session: 30
  random_seed: 77777
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text(config_content)

            # Run three times
            outputs = []
            for i in range(3):
                output_dir = Path(tmpdir) / f"output{i}"
                result = runner.invoke(
                    app,
                    ["run", str(config_path), "--output", str(output_dir), "--quiet"],
                )
                assert result.exit_code == 0

                csv_file = next(iter(output_dir.glob("*_sessions.csv")))
                outputs.append(csv_file.read_text())

            # All outputs should be identical
            assert outputs[0] == outputs[1]
            assert outputs[1] == outputs[2]

    def test_different_seeds_different_results(self) -> None:
        """Verify different seeds produce different results."""
        config_content = """
simulation:
  num_sessions: 50
  hands_per_session: 30
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text(config_content)
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

            csv1 = next(iter(output1.glob("*_sessions.csv"))).read_text()
            csv2 = next(iter(output2.glob("*_sessions.csv"))).read_text()

            # Headers same but data different
            assert csv1 != csv2


class TestCLIOutputFormats:
    """Tests for CLI output format generation."""

    def test_csv_output_format(self) -> None:
        """Verify CSV format is generated correctly."""
        config_content = """
simulation:
  num_sessions: 20
  hands_per_session: 20
  random_seed: 42

output:
  formats:
    csv:
      enabled: true
    json:
      enabled: false
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text(config_content)
            output_dir = Path(tmpdir) / "output"

            result = runner.invoke(
                app,
                ["run", str(config_path), "--output", str(output_dir), "--quiet"],
            )

            assert result.exit_code == 0

            # Verify CSV files exist
            csv_files = list(output_dir.glob("*.csv"))
            assert len(csv_files) >= 2

    def test_cli_output_directory_creation(self) -> None:
        """Verify CLI creates output directory if it doesn't exist."""
        config_content = """
simulation:
  num_sessions: 10
  hands_per_session: 10
  random_seed: 42
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text(config_content)
            output_dir = Path(tmpdir) / "deep" / "nested" / "output"

            result = runner.invoke(
                app,
                ["run", str(config_path), "--output", str(output_dir), "--quiet"],
            )

            assert result.exit_code == 0
            assert output_dir.exists()


class TestCLIIntegration:
    """Integration tests combining CLI with various configurations."""

    def test_cli_with_progressive_betting(self) -> None:
        """Verify CLI handles progressive betting configuration."""
        config_content = """
simulation:
  num_sessions: 50
  hands_per_session: 50
  random_seed: 42

bankroll:
  starting_amount: 1000.0
  base_bet: 10.0
  stop_conditions:
    win_limit: 300.0
    loss_limit: 400.0
    stop_on_insufficient_funds: true
  betting_system:
    type: martingale
    martingale:
      loss_multiplier: 2.0
      max_bet: 160.0

strategy:
  type: basic
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text(config_content)
            output_dir = Path(tmpdir) / "output"

            result = runner.invoke(
                app,
                ["run", str(config_path), "--output", str(output_dir), "--quiet"],
            )

            assert result.exit_code == 0

            # Verify sessions were completed
            sessions_csv = list(output_dir.glob("*_sessions.csv"))
            assert len(sessions_csv) == 1

    def test_cli_with_bonus_strategy(self) -> None:
        """Verify CLI handles bonus strategy configuration."""
        config_content = """
simulation:
  num_sessions: 50
  hands_per_session: 50
  random_seed: 42

bankroll:
  starting_amount: 500.0
  base_bet: 5.0
  stop_conditions:
    win_limit: 200.0
    loss_limit: 150.0
  betting_system:
    type: flat

strategy:
  type: basic

bonus_strategy:
  enabled: true
  type: always
  always:
    amount: 5.0
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text(config_content)
            output_dir = Path(tmpdir) / "output"

            result = runner.invoke(
                app,
                ["run", str(config_path), "--output", str(output_dir), "--quiet"],
            )

            assert result.exit_code == 0

    def test_cli_with_dealer_discard(self) -> None:
        """Verify CLI handles dealer discard configuration.

        This addresses the deferred item from PR #78.
        """
        config_content = """
simulation:
  num_sessions: 50
  hands_per_session: 50
  random_seed: 42

dealer:
  discard_enabled: true
  discard_cards: 3

bankroll:
  starting_amount: 500.0
  base_bet: 5.0
  stop_conditions:
    win_limit: 200.0
    loss_limit: 150.0
  betting_system:
    type: flat

strategy:
  type: basic
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text(config_content)
            output_dir = Path(tmpdir) / "output"

            result = runner.invoke(
                app,
                ["run", str(config_path), "--output", str(output_dir), "--quiet"],
            )

            assert result.exit_code == 0

            # Verify sessions completed
            sessions_csv = list(output_dir.glob("*_sessions.csv"))
            with sessions_csv[0].open(encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert len(rows) == 50
