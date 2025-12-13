"""End-to-end tests for output format generation.

These tests validate complete simulation-to-export workflows:
- CSV output file generation and content validity
- JSON output file generation and content validity
- Both formats generated together correctly
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from let_it_ride.analytics.export_csv import CSVExporter
from let_it_ride.analytics.export_json import JSONExporter, load_json
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
from let_it_ride.simulation.aggregation import aggregate_results
from let_it_ride.simulation.results import HandRecord


def create_output_test_config(
    num_sessions: int = 100,
    hands_per_session: int = 50,
    random_seed: int = 42,
    workers: int = 1,
) -> FullConfig:
    """Create a configuration for output format testing.

    Args:
        num_sessions: Number of sessions to run.
        hands_per_session: Maximum hands per session.
        random_seed: Seed for reproducibility.
        workers: Number of workers.

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
                win_limit=200.0,
                loss_limit=150.0,
                stop_on_insufficient_funds=True,
            ),
            betting_system=BettingSystemConfig(type="flat"),
        ),
        strategy=StrategyConfig(type="basic"),
    )


class TestCSVOutputGeneration:
    """Tests for CSV output generation from full simulation runs."""

    def test_csv_sessions_file_created(self, tmp_path: Path) -> None:
        """Verify sessions CSV file is created after simulation."""
        config = create_output_test_config(num_sessions=50)
        results = SimulationController(config).run()

        exporter = CSVExporter(tmp_path, prefix="test")
        path = exporter.export_sessions(results.session_results)

        assert path.exists()
        assert path.suffix == ".csv"
        assert "sessions" in path.name

    def test_csv_aggregate_file_created(self, tmp_path: Path) -> None:
        """Verify aggregate CSV file is created after simulation."""
        config = create_output_test_config(num_sessions=50)
        results = SimulationController(config).run()
        aggregate = aggregate_results(results.session_results)

        exporter = CSVExporter(tmp_path, prefix="test")
        path = exporter.export_aggregate(aggregate)

        assert path.exists()
        assert path.suffix == ".csv"
        assert "aggregate" in path.name

    def test_csv_session_count_matches(self, tmp_path: Path) -> None:
        """Verify CSV contains correct number of sessions."""
        num_sessions = 75
        config = create_output_test_config(num_sessions=num_sessions)
        results = SimulationController(config).run()

        exporter = CSVExporter(tmp_path, prefix="test")
        path = exporter.export_sessions(results.session_results)

        with path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == num_sessions

    def test_csv_session_data_matches_results(self, tmp_path: Path) -> None:
        """Verify CSV session data matches simulation results."""
        config = create_output_test_config(num_sessions=10)
        results = SimulationController(config).run()

        exporter = CSVExporter(tmp_path, prefix="test")
        path = exporter.export_sessions(results.session_results)

        with path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Verify each row matches corresponding result
        for row, session in zip(rows, results.session_results, strict=True):
            assert row["outcome"] == session.outcome.value
            assert row["stop_reason"] == session.stop_reason.value
            assert int(row["hands_played"]) == session.hands_played
            assert float(row["starting_bankroll"]) == session.starting_bankroll
            assert float(row["final_bankroll"]) == session.final_bankroll
            assert float(row["session_profit"]) == session.session_profit

    def test_csv_aggregate_statistics_valid(self, tmp_path: Path) -> None:
        """Verify aggregate CSV contains valid statistics."""
        config = create_output_test_config(num_sessions=100)
        results = SimulationController(config).run()
        aggregate = aggregate_results(results.session_results)

        exporter = CSVExporter(tmp_path, prefix="test")
        path = exporter.export_aggregate(aggregate)

        with path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1
        row = rows[0]

        # Verify key aggregate fields
        assert int(row["total_sessions"]) == 100
        assert (
            int(row["winning_sessions"])
            + int(row["losing_sessions"])
            + int(row["push_sessions"])
            == 100
        )

        # Verify win rate is reasonable
        win_rate = float(row["session_win_rate"])
        assert 0.0 <= win_rate <= 1.0

    def test_csv_export_all_creates_multiple_files(self, tmp_path: Path) -> None:
        """Verify export_all creates sessions and aggregate files."""
        config = create_output_test_config(num_sessions=50)
        results = SimulationController(config).run()

        exporter = CSVExporter(tmp_path, prefix="sim")
        paths = exporter.export_all(results, include_hands=False)

        assert len(paths) == 2
        assert (tmp_path / "sim_sessions.csv").exists()
        assert (tmp_path / "sim_aggregate.csv").exists()

    def test_csv_with_hand_records(self, tmp_path: Path) -> None:
        """Verify hands CSV is created when hand data is collected.

        Note: hand_callback only works in sequential mode (workers=1).
        """
        config = create_output_test_config(num_sessions=10, hands_per_session=20)
        config.simulation.workers = 1  # Required for hand_callback

        # Collect hand records
        hand_records: list[HandRecord] = []

        def collect_hands(
            session_id: int,
            hand_id: int,  # noqa: ARG001
            result: GameHandResult,
        ) -> None:
            # Convert cards to string representation
            player_cards = " ".join(str(c) for c in result.player_cards)
            community_cards = " ".join(str(c) for c in result.community_cards)

            # Convert enums to strings for HandRecord
            final_rank = result.final_hand_rank.name.lower()
            bonus_rank = (
                result.bonus_hand_rank.name.lower()
                if result.bonus_hand_rank is not None
                else None
            )

            hand_records.append(
                HandRecord(
                    hand_id=len(hand_records),
                    session_id=session_id,
                    shoe_id=None,
                    cards_player=player_cards,
                    cards_community=community_cards,
                    decision_bet1=result.decision_bet1.value,
                    decision_bet2=result.decision_bet2.value,
                    final_hand_rank=final_rank,
                    base_bet=result.base_bet,
                    bets_at_risk=result.bets_at_risk,
                    main_payout=result.main_payout,
                    bonus_bet=result.bonus_bet,
                    bonus_hand_rank=bonus_rank,
                    bonus_payout=result.bonus_payout,
                    bankroll_after=0.0,  # Not available from GameHandResult
                )
            )

        controller = SimulationController(config, hand_callback=collect_hands)
        sim_results = controller.run()

        # Export with hands
        exporter = CSVExporter(tmp_path, prefix="test")
        paths = exporter.export_all(
            sim_results, include_hands=True, hands=hand_records
        )

        assert len(paths) == 3
        assert (tmp_path / "test_hands.csv").exists()

        # Verify hands file has data
        with (tmp_path / "test_hands.csv").open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) > 0
        assert len(rows) == len(hand_records)


class TestJSONOutputGeneration:
    """Tests for JSON output generation from full simulation runs."""

    def test_json_file_created(self, tmp_path: Path) -> None:
        """Verify JSON file is created after simulation."""
        config = create_output_test_config(num_sessions=50)
        results = SimulationController(config).run()

        exporter = JSONExporter(tmp_path, prefix="test")
        path = exporter.export(results)

        assert path.exists()
        assert path.suffix == ".json"

    def test_json_is_valid(self, tmp_path: Path) -> None:
        """Verify output is valid JSON."""
        config = create_output_test_config(num_sessions=50)
        results = SimulationController(config).run()

        exporter = JSONExporter(tmp_path, prefix="test")
        path = exporter.export(results)

        with path.open() as f:
            data = json.load(f)

        assert isinstance(data, dict)

    def test_json_contains_all_sections(self, tmp_path: Path) -> None:
        """Verify JSON contains all required sections."""
        config = create_output_test_config(num_sessions=50)
        results = SimulationController(config).run()

        exporter = JSONExporter(tmp_path, prefix="test")
        path = exporter.export(results, include_config=True)

        data = load_json(path)

        assert "metadata" in data
        assert "simulation_timing" in data
        assert "aggregate_statistics" in data
        assert "session_results" in data
        assert "config" in data

    def test_json_session_count_matches(self, tmp_path: Path) -> None:
        """Verify JSON contains correct number of sessions."""
        num_sessions = 75
        config = create_output_test_config(num_sessions=num_sessions)
        results = SimulationController(config).run()

        exporter = JSONExporter(tmp_path, prefix="test")
        path = exporter.export(results)

        data = load_json(path)
        assert len(data["session_results"]) == num_sessions

    def test_json_session_data_matches_results(self, tmp_path: Path) -> None:
        """Verify JSON session data matches simulation results."""
        config = create_output_test_config(num_sessions=10)
        results = SimulationController(config).run()

        exporter = JSONExporter(tmp_path, prefix="test")
        path = exporter.export(results)

        data = load_json(path)

        # Verify each session matches
        for json_session, sim_session in zip(
            data["session_results"], results.session_results, strict=True
        ):
            assert json_session["outcome"] == sim_session.outcome.value
            assert json_session["stop_reason"] == sim_session.stop_reason.value
            assert json_session["hands_played"] == sim_session.hands_played
            assert json_session["starting_bankroll"] == sim_session.starting_bankroll
            assert json_session["final_bankroll"] == sim_session.final_bankroll
            assert json_session["session_profit"] == sim_session.session_profit

    def test_json_aggregate_statistics_valid(self, tmp_path: Path) -> None:
        """Verify JSON aggregate statistics are valid."""
        config = create_output_test_config(num_sessions=100)
        results = SimulationController(config).run()

        exporter = JSONExporter(tmp_path, prefix="test")
        path = exporter.export(results)

        data = load_json(path)
        stats = data["aggregate_statistics"]

        assert stats["total_sessions"] == 100
        assert (
            stats["winning_sessions"]
            + stats["losing_sessions"]
            + stats["push_sessions"]
            == 100
        )

        # Verify win rate is reasonable
        assert 0.0 <= stats["session_win_rate"] <= 1.0

    def test_json_config_round_trip(self, tmp_path: Path) -> None:
        """Verify config in JSON matches original config."""
        config = create_output_test_config(num_sessions=50)
        results = SimulationController(config).run()

        exporter = JSONExporter(tmp_path, prefix="test")
        path = exporter.export(results, include_config=True)

        data = load_json(path)
        json_config = data["config"]

        # Verify key config values
        assert json_config["simulation"]["num_sessions"] == 50
        assert json_config["bankroll"]["starting_amount"] == 500.0
        assert json_config["bankroll"]["base_bet"] == 5.0
        assert json_config["strategy"]["type"] == "basic"

    def test_json_with_hands(self, tmp_path: Path) -> None:
        """Verify hands are included in JSON when requested.

        Note: hand_callback only works in sequential mode (workers=1).
        """
        config = create_output_test_config(num_sessions=10, hands_per_session=20)
        config.simulation.workers = 1  # Required for hand_callback

        # Collect hand records
        hand_records: list[HandRecord] = []

        def collect_hands(
            session_id: int,
            hand_id: int,  # noqa: ARG001
            result: GameHandResult,
        ) -> None:
            player_cards = " ".join(str(c) for c in result.player_cards)
            community_cards = " ".join(str(c) for c in result.community_cards)

            # Convert enums to strings for HandRecord
            final_rank = result.final_hand_rank.name.lower()
            bonus_rank = (
                result.bonus_hand_rank.name.lower()
                if result.bonus_hand_rank is not None
                else None
            )

            hand_records.append(
                HandRecord(
                    hand_id=len(hand_records),
                    session_id=session_id,
                    shoe_id=None,
                    cards_player=player_cards,
                    cards_community=community_cards,
                    decision_bet1=result.decision_bet1.value,
                    decision_bet2=result.decision_bet2.value,
                    final_hand_rank=final_rank,
                    base_bet=result.base_bet,
                    bets_at_risk=result.bets_at_risk,
                    main_payout=result.main_payout,
                    bonus_bet=result.bonus_bet,
                    bonus_hand_rank=bonus_rank,
                    bonus_payout=result.bonus_payout,
                    bankroll_after=0.0,
                )
            )

        controller = SimulationController(config, hand_callback=collect_hands)
        sim_results = controller.run()

        exporter = JSONExporter(tmp_path, prefix="test")
        path = exporter.export(sim_results, include_hands=True, hands=hand_records)

        data = load_json(path)
        assert "hands" in data
        assert len(data["hands"]) == len(hand_records)


class TestBothFormats:
    """Tests for generating both CSV and JSON outputs."""

    def test_both_formats_generated(self, tmp_path: Path) -> None:
        """Verify both CSV and JSON can be generated from same results."""
        config = create_output_test_config(num_sessions=50)
        results = SimulationController(config).run()

        # Export CSV
        csv_exporter = CSVExporter(tmp_path, prefix="sim")
        csv_paths = csv_exporter.export_all(results, include_hands=False)

        # Export JSON
        json_exporter = JSONExporter(tmp_path, prefix="sim")
        json_path = json_exporter.export(results)

        # Verify all files exist
        assert len(csv_paths) == 2
        assert json_path.exists()
        assert (tmp_path / "sim_sessions.csv").exists()
        assert (tmp_path / "sim_aggregate.csv").exists()
        assert (tmp_path / "sim_results.json").exists()

    def test_formats_have_consistent_data(self, tmp_path: Path) -> None:
        """Verify CSV and JSON contain consistent data."""
        config = create_output_test_config(num_sessions=25)
        results = SimulationController(config).run()

        # Export both formats
        csv_exporter = CSVExporter(tmp_path, prefix="sim")
        csv_exporter.export_all(results, include_hands=False)

        json_exporter = JSONExporter(tmp_path, prefix="sim")
        json_exporter.export(results)

        # Load CSV sessions
        with (tmp_path / "sim_sessions.csv").open(
            encoding="utf-8-sig", newline=""
        ) as f:
            csv_reader = csv.DictReader(f)
            csv_rows = list(csv_reader)

        # Load JSON
        json_data = load_json(tmp_path / "sim_results.json")
        json_sessions = json_data["session_results"]

        # Verify counts match
        assert len(csv_rows) == len(json_sessions)

        # Verify key data matches
        for csv_row, json_session in zip(csv_rows, json_sessions, strict=True):
            assert csv_row["outcome"] == json_session["outcome"]
            assert int(csv_row["hands_played"]) == json_session["hands_played"]
            assert float(csv_row["session_profit"]) == json_session["session_profit"]


class TestOutputDirectoryHandling:
    """Tests for output directory creation and handling."""

    def test_creates_output_directory(self, tmp_path: Path) -> None:
        """Verify output directory is created if it doesn't exist."""
        output_dir = tmp_path / "results" / "csv"
        config = create_output_test_config(num_sessions=10)
        results = SimulationController(config).run()

        exporter = CSVExporter(output_dir, prefix="test")
        exporter.export_sessions(results.session_results)

        assert output_dir.exists()

    def test_handles_existing_directory(self, tmp_path: Path) -> None:
        """Verify existing directory is used without error."""
        output_dir = tmp_path / "existing"
        output_dir.mkdir(parents=True)

        config = create_output_test_config(num_sessions=10)
        results = SimulationController(config).run()

        exporter = CSVExporter(output_dir, prefix="test")
        path = exporter.export_sessions(results.session_results)

        assert path.exists()

    def test_overwrites_existing_files(self, tmp_path: Path) -> None:
        """Verify existing files are overwritten."""
        config = create_output_test_config(num_sessions=10, random_seed=111)
        results1 = SimulationController(config).run()

        # Export first time
        exporter = CSVExporter(tmp_path, prefix="test")
        path = exporter.export_sessions(results1.session_results)

        # Get first content
        with path.open() as f:
            content1 = f.read()

        # Run again with different seed
        config2 = create_output_test_config(num_sessions=10, random_seed=222)
        results2 = SimulationController(config2).run()

        # Export second time (overwrite)
        exporter.export_sessions(results2.session_results)

        # Verify content changed
        with path.open() as f:
            content2 = f.read()

        # Headers same, but data should differ
        assert content1 != content2


class TestLargeScaleOutput:
    """Tests for output generation with large datasets."""

    def test_large_session_csv_export(self, tmp_path: Path) -> None:
        """Verify CSV export handles many sessions."""
        config = create_output_test_config(num_sessions=5000, workers=4)
        results = SimulationController(config).run()

        exporter = CSVExporter(tmp_path, prefix="large")
        path = exporter.export_sessions(results.session_results)

        # Verify file created
        assert path.exists()
        assert path.stat().st_size > 0

        # Count rows
        with path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            row_count = sum(1 for _ in reader)

        assert row_count == 5000

    def test_large_session_json_export(self, tmp_path: Path) -> None:
        """Verify JSON export handles many sessions."""
        config = create_output_test_config(num_sessions=5000, workers=4)
        results = SimulationController(config).run()

        exporter = JSONExporter(tmp_path, prefix="large")
        path = exporter.export(results)

        # Verify file created and valid
        assert path.exists()
        data = load_json(path)

        assert len(data["session_results"]) == 5000
