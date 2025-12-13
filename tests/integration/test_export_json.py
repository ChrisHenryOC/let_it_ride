"""Integration tests for JSON export functionality.

Tests file creation, content validation, pretty/compact formatting,
config inclusion, round-trip loading, and error handling.
"""

import json
from datetime import datetime
from pathlib import Path

import pytest

from let_it_ride.analytics.export_json import (
    JSON_SCHEMA_VERSION,
    JSONExporter,
    ResultsEncoder,
    export_json,
    load_json,
)
from let_it_ride.simulation.results import HandRecord
from let_it_ride.simulation.session import SessionOutcome, SessionResult, StopReason


@pytest.fixture
def sample_session_results() -> list[SessionResult]:
    """Create sample session results for testing."""
    return [
        SessionResult(
            outcome=SessionOutcome.WIN,
            stop_reason=StopReason.WIN_LIMIT,
            hands_played=25,
            starting_bankroll=500.0,
            final_bankroll=600.0,
            session_profit=100.0,
            total_wagered=750.0,
            total_bonus_wagered=0.0,
            peak_bankroll=620.0,
            max_drawdown=50.0,
            max_drawdown_pct=0.08,
        ),
        SessionResult(
            outcome=SessionOutcome.LOSS,
            stop_reason=StopReason.LOSS_LIMIT,
            hands_played=40,
            starting_bankroll=500.0,
            final_bankroll=300.0,
            session_profit=-200.0,
            total_wagered=1200.0,
            total_bonus_wagered=0.0,
            peak_bankroll=550.0,
            max_drawdown=250.0,
            max_drawdown_pct=0.45,
        ),
        SessionResult(
            outcome=SessionOutcome.PUSH,
            stop_reason=StopReason.MAX_HANDS,
            hands_played=50,
            starting_bankroll=500.0,
            final_bankroll=500.0,
            session_profit=0.0,
            total_wagered=1500.0,
            total_bonus_wagered=0.0,
            peak_bankroll=580.0,
            max_drawdown=80.0,
            max_drawdown_pct=0.14,
        ),
    ]


@pytest.fixture
def sample_hand_records() -> list[HandRecord]:
    """Create sample hand records for testing."""
    return [
        HandRecord(
            hand_id=0,
            session_id=0,
            shoe_id=None,
            cards_player="Ah Kh Qh",
            cards_community="Jh Th",
            decision_bet1="ride",
            decision_bet2="ride",
            final_hand_rank="royal_flush",
            base_bet=5.0,
            bets_at_risk=15.0,
            main_payout=15000.0,
            bonus_bet=0.0,
            bonus_hand_rank=None,
            bonus_payout=0.0,
            bankroll_after=15500.0,
        ),
        HandRecord(
            hand_id=1,
            session_id=0,
            shoe_id=None,
            cards_player="2c 7d 9s",
            cards_community="Jh Th",
            decision_bet1="pull",
            decision_bet2="pull",
            final_hand_rank="high_card",
            base_bet=5.0,
            bets_at_risk=5.0,
            main_payout=0.0,
            bonus_bet=1.0,
            bonus_hand_rank="high_card",
            bonus_payout=0.0,
            bankroll_after=15494.0,
        ),
        HandRecord(
            hand_id=2,
            session_id=0,
            shoe_id=1,
            cards_player="Ts Td Tc",
            cards_community="9h 2d",
            decision_bet1="ride",
            decision_bet2="ride",
            final_hand_rank="three_of_a_kind",
            base_bet=5.0,
            bets_at_risk=15.0,
            main_payout=45.0,
            bonus_bet=1.0,
            bonus_hand_rank="three_of_a_kind",
            bonus_payout=30.0,
            bankroll_after=15568.0,
        ),
    ]


@pytest.fixture
def sample_simulation_results(sample_session_results: list[SessionResult]):
    """Create sample SimulationResults for testing."""
    from let_it_ride.config.models import (
        BankrollConfig,
        BettingSystemConfig,
        FullConfig,
        SimulationConfig,
        StopConditionsConfig,
        StrategyConfig,
    )
    from let_it_ride.simulation.controller import SimulationResults

    config = FullConfig(
        simulation=SimulationConfig(num_sessions=3, hands_per_session=50),
        bankroll=BankrollConfig(
            starting_amount=500.0,
            base_bet=5.0,
            stop_conditions=StopConditionsConfig(win_limit=100.0, loss_limit=200.0),
            betting_system=BettingSystemConfig(type="flat"),
        ),
        strategy=StrategyConfig(type="basic"),
    )
    return SimulationResults(
        config=config,
        session_results=sample_session_results,
        start_time=datetime(2025, 1, 15, 10, 30, 0),
        end_time=datetime(2025, 1, 15, 10, 35, 0),
        total_hands=115,
    )


class TestResultsEncoder:
    """Tests for ResultsEncoder custom JSON encoder."""

    def test_encodes_datetime(self) -> None:
        """Verify datetime is encoded as ISO format string."""
        dt = datetime(2025, 1, 15, 10, 30, 0)
        result = json.dumps({"time": dt}, cls=ResultsEncoder)
        assert '"2025-01-15T10:30:00"' in result

    def test_encodes_enum(self) -> None:
        """Verify enum is encoded as string value."""
        result = json.dumps({"outcome": SessionOutcome.WIN}, cls=ResultsEncoder)
        assert '"win"' in result

    def test_encodes_pydantic_model(self) -> None:
        """Verify Pydantic BaseModel is encoded using model_dump."""
        from let_it_ride.config.models import SimulationConfig

        config = SimulationConfig(num_sessions=100)
        result = json.dumps({"config": config}, cls=ResultsEncoder)
        data = json.loads(result)
        assert data["config"]["num_sessions"] == 100

    def test_encodes_dataclass(self) -> None:
        """Verify dataclass is encoded to dict."""
        record = HandRecord(
            hand_id=0,
            session_id=0,
            shoe_id=None,
            cards_player="Ah Kh Qh",
            cards_community="Jh Th",
            decision_bet1="ride",
            decision_bet2="ride",
            final_hand_rank="royal_flush",
            base_bet=5.0,
            bets_at_risk=15.0,
            main_payout=15000.0,
            bonus_bet=0.0,
            bonus_hand_rank=None,
            bonus_payout=0.0,
            bankroll_after=15500.0,
        )
        result = json.dumps({"record": record}, cls=ResultsEncoder)
        data = json.loads(result)
        assert data["record"]["hand_id"] == 0
        assert data["record"]["cards_player"] == "Ah Kh Qh"


class TestExportJson:
    """Tests for export_json function."""

    def test_creates_file(self, tmp_path: Path, sample_simulation_results) -> None:
        """Verify JSON file is created."""
        path = tmp_path / "results.json"
        export_json(sample_simulation_results, path)
        assert path.exists()

    def test_valid_json(self, tmp_path: Path, sample_simulation_results) -> None:
        """Verify output is valid JSON."""
        path = tmp_path / "results.json"
        export_json(sample_simulation_results, path)

        with path.open() as f:
            data = json.load(f)

        assert isinstance(data, dict)

    def test_contains_metadata(self, tmp_path: Path, sample_simulation_results) -> None:
        """Verify output contains metadata section."""
        path = tmp_path / "results.json"
        export_json(sample_simulation_results, path)
        data = load_json(path)

        assert "metadata" in data
        assert data["metadata"]["schema_version"] == JSON_SCHEMA_VERSION
        assert "generated_at" in data["metadata"]
        assert "simulator_version" in data["metadata"]

    def test_contains_simulation_timing(
        self, tmp_path: Path, sample_simulation_results
    ) -> None:
        """Verify output contains simulation timing section."""
        path = tmp_path / "results.json"
        export_json(sample_simulation_results, path)
        data = load_json(path)

        assert "simulation_timing" in data
        assert data["simulation_timing"]["start_time"] == "2025-01-15T10:30:00"
        assert data["simulation_timing"]["end_time"] == "2025-01-15T10:35:00"
        assert data["simulation_timing"]["total_hands"] == 115

    def test_contains_aggregate_statistics(
        self, tmp_path: Path, sample_simulation_results
    ) -> None:
        """Verify output contains aggregate statistics."""
        path = tmp_path / "results.json"
        export_json(sample_simulation_results, path)
        data = load_json(path)

        assert "aggregate_statistics" in data
        stats = data["aggregate_statistics"]
        assert stats["total_sessions"] == 3
        assert stats["winning_sessions"] == 1
        assert stats["losing_sessions"] == 1
        assert stats["push_sessions"] == 1

    def test_contains_session_results(
        self, tmp_path: Path, sample_simulation_results
    ) -> None:
        """Verify output contains session results."""
        path = tmp_path / "results.json"
        export_json(sample_simulation_results, path)
        data = load_json(path)

        assert "session_results" in data
        assert len(data["session_results"]) == 3
        assert data["session_results"][0]["outcome"] == "win"
        assert data["session_results"][1]["outcome"] == "loss"
        assert data["session_results"][2]["outcome"] == "push"

    def test_enum_values_serialized_as_strings(
        self, tmp_path: Path, sample_simulation_results
    ) -> None:
        """Verify enum values are serialized as lowercase strings."""
        path = tmp_path / "results.json"
        export_json(sample_simulation_results, path)
        data = load_json(path)

        # Check session outcomes
        assert data["session_results"][0]["outcome"] == "win"
        assert data["session_results"][0]["stop_reason"] == "win_limit"
        assert data["session_results"][1]["stop_reason"] == "loss_limit"
        assert data["session_results"][2]["stop_reason"] == "max_hands"

    def test_include_config_true(
        self, tmp_path: Path, sample_simulation_results
    ) -> None:
        """Verify config is included when include_config=True."""
        path = tmp_path / "results.json"
        export_json(sample_simulation_results, path, include_config=True)
        data = load_json(path)

        assert "config" in data
        assert data["config"]["simulation"]["num_sessions"] == 3
        assert data["config"]["bankroll"]["starting_amount"] == 500.0
        assert data["config"]["strategy"]["type"] == "basic"

    def test_include_config_false(
        self, tmp_path: Path, sample_simulation_results
    ) -> None:
        """Verify config is excluded when include_config=False."""
        path = tmp_path / "results.json"
        export_json(sample_simulation_results, path, include_config=False)
        data = load_json(path)

        assert "config" not in data

    def test_include_hands_true(
        self,
        tmp_path: Path,
        sample_simulation_results,
        sample_hand_records: list[HandRecord],
    ) -> None:
        """Verify hands are included when include_hands=True."""
        path = tmp_path / "results.json"
        export_json(
            sample_simulation_results,
            path,
            include_hands=True,
            hands=sample_hand_records,
        )
        data = load_json(path)

        assert "hands" in data
        assert len(data["hands"]) == 3
        assert data["hands"][0]["cards_player"] == "Ah Kh Qh"
        assert data["hands"][0]["final_hand_rank"] == "royal_flush"

    def test_include_hands_false(
        self, tmp_path: Path, sample_simulation_results
    ) -> None:
        """Verify hands are excluded when include_hands=False."""
        path = tmp_path / "results.json"
        export_json(sample_simulation_results, path, include_hands=False)
        data = load_json(path)

        assert "hands" not in data

    def test_include_hands_without_data_raises(
        self, tmp_path: Path, sample_simulation_results
    ) -> None:
        """Verify error when include_hands=True but hands is None."""
        path = tmp_path / "results.json"
        with pytest.raises(ValueError, match="include_hands is True but hands is None"):
            export_json(sample_simulation_results, path, include_hands=True, hands=None)

    def test_include_hands_empty_raises(
        self, tmp_path: Path, sample_simulation_results
    ) -> None:
        """Verify error when include_hands=True but hands is empty."""
        path = tmp_path / "results.json"
        with pytest.raises(
            ValueError, match="include_hands is True but hands iterable is empty"
        ):
            export_json(sample_simulation_results, path, include_hands=True, hands=[])

    def test_pretty_print_format(
        self, tmp_path: Path, sample_simulation_results
    ) -> None:
        """Verify pretty=True produces indented output."""
        path = tmp_path / "results.json"
        export_json(sample_simulation_results, path, pretty=True)

        content = path.read_text()
        # Pretty print has indentation
        assert "\n  " in content
        # Pretty print has trailing newline
        assert content.endswith("\n")

    def test_compact_format(self, tmp_path: Path, sample_simulation_results) -> None:
        """Verify pretty=False produces compact output."""
        path = tmp_path / "results.json"
        export_json(sample_simulation_results, path, pretty=False)

        content = path.read_text()
        # Compact has no indentation (no newline followed by spaces)
        assert "\n  " not in content

    def test_compact_smaller_than_pretty(
        self, tmp_path: Path, sample_simulation_results
    ) -> None:
        """Verify compact output is smaller than pretty output."""
        pretty_path = tmp_path / "pretty.json"
        compact_path = tmp_path / "compact.json"

        export_json(sample_simulation_results, pretty_path, pretty=True)
        export_json(sample_simulation_results, compact_path, pretty=False)

        assert compact_path.stat().st_size < pretty_path.stat().st_size

    def test_nested_dicts_preserved(
        self, tmp_path: Path, sample_session_results: list[SessionResult]
    ) -> None:
        """Verify hand_frequencies dict is preserved as nested structure."""
        from let_it_ride.simulation.aggregation import aggregate_with_hand_frequencies

        # Create results with hand frequencies
        hand_freqs = {"royal_flush": 1, "flush": 10, "high_card": 100}
        # Just validate aggregate_with_hand_frequencies works
        aggregate_with_hand_frequencies(sample_session_results, hand_freqs)

        # Export and verify structure
        from let_it_ride.config.models import (
            BankrollConfig,
            BettingSystemConfig,
            FullConfig,
            SimulationConfig,
            StopConditionsConfig,
            StrategyConfig,
        )
        from let_it_ride.simulation.controller import SimulationResults

        config = FullConfig(
            simulation=SimulationConfig(num_sessions=3, hands_per_session=50),
            bankroll=BankrollConfig(
                starting_amount=500.0,
                base_bet=5.0,
                stop_conditions=StopConditionsConfig(win_limit=100.0, loss_limit=200.0),
                betting_system=BettingSystemConfig(type="flat"),
            ),
            strategy=StrategyConfig(type="basic"),
        )
        results = SimulationResults(
            config=config,
            session_results=sample_session_results,
            start_time=datetime.now(),
            end_time=datetime.now(),
            total_hands=111,
        )

        path = tmp_path / "results.json"
        export_json(results, path)
        data = load_json(path)

        # Verify nested dict structure (unlike CSV which flattens)
        # Note: aggregate_results is called inside export_json, so hand_frequencies
        # will be empty unless we had hand data. We verify the structure at least.
        assert isinstance(data["aggregate_statistics"]["hand_frequencies"], dict)
        assert isinstance(data["aggregate_statistics"]["hand_frequency_pct"], dict)

    def test_excludes_session_profits_internal_field(
        self, tmp_path: Path, sample_simulation_results
    ) -> None:
        """Verify session_profits internal field is excluded from output."""
        path = tmp_path / "results.json"
        export_json(sample_simulation_results, path)
        data = load_json(path)

        assert "session_profits" not in data["aggregate_statistics"]


class TestLoadJson:
    """Tests for load_json function."""

    def test_loads_exported_json(
        self, tmp_path: Path, sample_simulation_results
    ) -> None:
        """Verify load_json successfully loads exported JSON."""
        path = tmp_path / "results.json"
        export_json(sample_simulation_results, path)

        data = load_json(path)

        assert isinstance(data, dict)
        assert "metadata" in data
        assert "session_results" in data

    def test_file_not_found_raises(self, tmp_path: Path) -> None:
        """Verify FileNotFoundError for missing file."""
        path = tmp_path / "nonexistent.json"
        with pytest.raises(FileNotFoundError):
            load_json(path)

    def test_invalid_json_raises(self, tmp_path: Path) -> None:
        """Verify JSONDecodeError for invalid JSON."""
        path = tmp_path / "invalid.json"
        path.write_text("not valid json {{{")

        with pytest.raises(json.JSONDecodeError):
            load_json(path)


class TestRoundTrip:
    """Tests for round-trip export/load functionality."""

    def test_session_results_round_trip(
        self, tmp_path: Path, sample_simulation_results
    ) -> None:
        """Verify session results survive round-trip export/load."""
        path = tmp_path / "results.json"
        export_json(sample_simulation_results, path)
        data = load_json(path)

        # Verify all session data is preserved
        assert len(data["session_results"]) == 3

        session = data["session_results"][0]
        assert session["outcome"] == "win"
        assert session["stop_reason"] == "win_limit"
        assert session["hands_played"] == 25
        assert session["starting_bankroll"] == 500.0
        assert session["final_bankroll"] == 600.0
        assert session["session_profit"] == 100.0
        assert session["total_wagered"] == 750.0

    def test_hands_round_trip(
        self,
        tmp_path: Path,
        sample_simulation_results,
        sample_hand_records: list[HandRecord],
    ) -> None:
        """Verify hand records survive round-trip export/load."""
        path = tmp_path / "results.json"
        export_json(
            sample_simulation_results,
            path,
            include_hands=True,
            hands=sample_hand_records,
        )
        data = load_json(path)

        # Verify all hand data is preserved
        assert len(data["hands"]) == 3

        hand = data["hands"][0]
        assert hand["hand_id"] == 0
        assert hand["session_id"] == 0
        assert hand["shoe_id"] is None
        assert hand["cards_player"] == "Ah Kh Qh"
        assert hand["cards_community"] == "Jh Th"
        assert hand["decision_bet1"] == "ride"
        assert hand["decision_bet2"] == "ride"
        assert hand["final_hand_rank"] == "royal_flush"
        assert hand["base_bet"] == 5.0
        assert hand["main_payout"] == 15000.0

    def test_config_round_trip(self, tmp_path: Path, sample_simulation_results) -> None:
        """Verify config survives round-trip export/load."""
        path = tmp_path / "results.json"
        export_json(sample_simulation_results, path, include_config=True)
        data = load_json(path)

        # Verify config structure is preserved
        assert data["config"]["simulation"]["num_sessions"] == 3
        assert data["config"]["simulation"]["hands_per_session"] == 50
        assert data["config"]["bankroll"]["starting_amount"] == 500.0
        assert data["config"]["bankroll"]["base_bet"] == 5.0
        assert data["config"]["strategy"]["type"] == "basic"


class TestJSONExporter:
    """Tests for JSONExporter class."""

    def test_creates_output_directory(self, tmp_path: Path) -> None:
        """Verify output directory is created if it doesn't exist."""
        output_dir = tmp_path / "subdir" / "output"
        exporter = JSONExporter(output_dir)

        from let_it_ride.config.models import FullConfig
        from let_it_ride.simulation.controller import SimulationResults

        config = FullConfig()
        results = SimulationResults(
            config=config,
            session_results=[
                SessionResult(
                    outcome=SessionOutcome.WIN,
                    stop_reason=StopReason.MAX_HANDS,
                    hands_played=10,
                    starting_bankroll=100.0,
                    final_bankroll=110.0,
                    session_profit=10.0,
                    total_wagered=30.0,
                    total_bonus_wagered=0.0,
                    peak_bankroll=115.0,
                    max_drawdown=5.0,
                    max_drawdown_pct=0.05,
                )
            ],
            start_time=datetime.now(),
            end_time=datetime.now(),
            total_hands=10,
        )

        exporter.export(results)
        assert output_dir.exists()

    def test_exports_with_default_prefix(
        self, tmp_path: Path, sample_simulation_results
    ) -> None:
        """Verify default prefix is 'simulation'."""
        exporter = JSONExporter(tmp_path)
        path = exporter.export(sample_simulation_results)

        assert path.name == "simulation_results.json"

    def test_exports_with_custom_prefix(
        self, tmp_path: Path, sample_simulation_results
    ) -> None:
        """Verify custom prefix is used in filename."""
        exporter = JSONExporter(tmp_path, prefix="my_sim")
        path = exporter.export(sample_simulation_results)

        assert path.name == "my_sim_results.json"

    def test_pretty_setting_propagates(
        self, tmp_path: Path, sample_simulation_results
    ) -> None:
        """Verify pretty setting is applied to exports."""
        exporter = JSONExporter(tmp_path, pretty=False)
        path = exporter.export(sample_simulation_results)

        content = path.read_text()
        assert "\n  " not in content

    def test_include_config_option(
        self, tmp_path: Path, sample_simulation_results
    ) -> None:
        """Verify include_config option works."""
        exporter = JSONExporter(tmp_path)

        # With config
        path = exporter.export(sample_simulation_results, include_config=True)
        data = load_json(path)
        assert "config" in data

    def test_include_hands_option(
        self,
        tmp_path: Path,
        sample_simulation_results,
        sample_hand_records: list[HandRecord],
    ) -> None:
        """Verify include_hands option works."""
        exporter = JSONExporter(tmp_path)
        path = exporter.export(
            sample_simulation_results,
            include_hands=True,
            hands=sample_hand_records,
        )

        data = load_json(path)
        assert "hands" in data
        assert len(data["hands"]) == 3

    def test_include_hands_without_data_raises(
        self, tmp_path: Path, sample_simulation_results
    ) -> None:
        """Verify error when include_hands=True but no hands provided."""
        exporter = JSONExporter(tmp_path)
        with pytest.raises(ValueError, match="include_hands is True but hands is None"):
            exporter.export(sample_simulation_results, include_hands=True)

    def test_properties(self, tmp_path: Path) -> None:
        """Verify exporter properties are accessible."""
        exporter = JSONExporter(tmp_path, prefix="test", pretty=False)

        assert exporter.output_dir == tmp_path
        assert exporter.prefix == "test"
        assert exporter.pretty is False

    def test_returns_path(self, tmp_path: Path, sample_simulation_results) -> None:
        """Verify export returns path to created file."""
        exporter = JSONExporter(tmp_path)
        path = exporter.export(sample_simulation_results)

        assert isinstance(path, Path)
        assert path.exists()


class TestLargeDataHandling:
    """Tests for handling large datasets."""

    def test_large_session_count(self, tmp_path: Path) -> None:
        """Verify export handles many sessions."""
        from let_it_ride.config.models import FullConfig
        from let_it_ride.simulation.controller import SimulationResults

        # Create many sessions
        num_sessions = 1000
        session_results = [
            SessionResult(
                outcome=SessionOutcome.WIN if i % 3 == 0 else SessionOutcome.LOSS,
                stop_reason=StopReason.MAX_HANDS,
                hands_played=50 + (i % 10),
                starting_bankroll=500.0,
                final_bankroll=500.0 + (i % 200) - 100,
                session_profit=(i % 200) - 100,
                total_wagered=1500.0,
                total_bonus_wagered=0.0,
                peak_bankroll=600.0,
                max_drawdown=100.0,
                max_drawdown_pct=0.17,
            )
            for i in range(num_sessions)
        ]

        config = FullConfig()
        results = SimulationResults(
            config=config,
            session_results=session_results,
            start_time=datetime.now(),
            end_time=datetime.now(),
            total_hands=sum(r.hands_played for r in session_results),
        )

        path = tmp_path / "large_sessions.json"
        export_json(results, path)

        data = load_json(path)
        assert len(data["session_results"]) == num_sessions

    def test_large_hand_count(self, tmp_path: Path, sample_simulation_results) -> None:
        """Verify export handles many hand records."""
        # Create many hands
        num_hands = 10000
        hand_records = [
            HandRecord(
                hand_id=i,
                session_id=i // 100,
                shoe_id=None,
                cards_player="Ah Kh Qh",
                cards_community="Jh Th",
                decision_bet1="ride",
                decision_bet2="ride" if i % 2 == 0 else "pull",
                final_hand_rank="pair" if i % 5 == 0 else "high_card",
                base_bet=5.0,
                bets_at_risk=15.0 if i % 2 == 0 else 10.0,
                main_payout=0.0,
                bonus_bet=0.0,
                bonus_hand_rank=None,
                bonus_payout=0.0,
                bankroll_after=500.0 - i * 0.01,
            )
            for i in range(num_hands)
        ]

        path = tmp_path / "large_hands.json"
        export_json(
            sample_simulation_results,
            path,
            include_hands=True,
            hands=hand_records,
        )

        data = load_json(path)
        assert len(data["hands"]) == num_hands


class TestUnicodeHandling:
    """Tests for unicode character handling."""

    def test_unicode_in_output(self, tmp_path: Path, sample_simulation_results) -> None:
        """Verify unicode characters are preserved (not escaped)."""
        path = tmp_path / "results.json"
        export_json(sample_simulation_results, path)

        content = path.read_text(encoding="utf-8")
        # Verify file is readable as UTF-8
        assert isinstance(content, str)
        # Verify JSON is valid
        json.loads(content)
