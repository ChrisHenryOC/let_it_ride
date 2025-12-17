"""Integration tests for CSV export functionality.

Tests file creation, content validation, field selection, BOM encoding,
and large file handling.
"""

import csv
from pathlib import Path

import pytest

from let_it_ride.analytics.chair_position import (
    ChairPositionAnalysis,
    SeatStatistics,
)
from let_it_ride.analytics.export_csv import (
    HAND_RECORD_FIELDS,
    SEAT_AGGREGATE_FIELDS,
    SESSION_RESULT_FIELDS,
    CSVExporter,
    export_aggregate_csv,
    export_hands_csv,
    export_seat_aggregate_csv,
    export_sessions_csv,
)
from let_it_ride.simulation.aggregation import AggregateStatistics, aggregate_results
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
def sample_aggregate_stats(
    sample_session_results: list[SessionResult],
) -> AggregateStatistics:
    """Create sample aggregate statistics for testing."""
    return aggregate_results(sample_session_results)


class TestExportSessionsCsv:
    """Tests for export_sessions_csv function."""

    def test_exports_all_sessions(
        self, tmp_path: Path, sample_session_results: list[SessionResult]
    ) -> None:
        """Verify all sessions are exported to CSV."""
        path = tmp_path / "sessions.csv"
        export_sessions_csv(sample_session_results, path)

        assert path.exists()
        with path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 3
        assert rows[0]["outcome"] == "win"
        assert rows[1]["outcome"] == "loss"
        assert rows[2]["outcome"] == "push"

    def test_exports_all_fields_by_default(
        self, tmp_path: Path, sample_session_results: list[SessionResult]
    ) -> None:
        """Verify all fields are exported when no fields specified."""
        path = tmp_path / "sessions.csv"
        export_sessions_csv(sample_session_results, path)

        with path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert set(rows[0].keys()) == set(SESSION_RESULT_FIELDS)

    def test_field_selection(
        self, tmp_path: Path, sample_session_results: list[SessionResult]
    ) -> None:
        """Verify only selected fields are exported."""
        path = tmp_path / "sessions.csv"
        fields = ["outcome", "hands_played", "session_profit"]
        export_sessions_csv(sample_session_results, path, fields_to_export=fields)

        with path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert set(rows[0].keys()) == set(fields)
        assert rows[0]["outcome"] == "win"
        assert rows[0]["hands_played"] == "25"
        assert rows[0]["session_profit"] == "100.0"

    def test_invalid_field_raises_error(
        self, tmp_path: Path, sample_session_results: list[SessionResult]
    ) -> None:
        """Verify invalid field names raise ValueError."""
        path = tmp_path / "sessions.csv"
        with pytest.raises(ValueError, match="Invalid field names"):
            export_sessions_csv(
                sample_session_results, path, fields_to_export=["invalid_field"]
            )

    def test_empty_results_raises_error(self, tmp_path: Path) -> None:
        """Verify empty results list raises ValueError."""
        path = tmp_path / "sessions.csv"
        with pytest.raises(ValueError, match="Cannot export empty results list"):
            export_sessions_csv([], path)

    def test_bom_included_by_default(
        self, tmp_path: Path, sample_session_results: list[SessionResult]
    ) -> None:
        """Verify UTF-8 BOM is included by default for Excel compatibility."""
        path = tmp_path / "sessions.csv"
        export_sessions_csv(sample_session_results, path)

        with path.open("rb") as f:
            bom = f.read(3)
        assert bom == b"\xef\xbb\xbf"

    def test_bom_excluded_when_disabled(
        self, tmp_path: Path, sample_session_results: list[SessionResult]
    ) -> None:
        """Verify UTF-8 BOM is excluded when disabled."""
        path = tmp_path / "sessions.csv"
        export_sessions_csv(sample_session_results, path, include_bom=False)

        with path.open("rb") as f:
            start = f.read(3)
        assert start != b"\xef\xbb\xbf"


class TestExportAggregateCsv:
    """Tests for export_aggregate_csv function."""

    def test_exports_aggregate_stats(
        self, tmp_path: Path, sample_aggregate_stats: AggregateStatistics
    ) -> None:
        """Verify aggregate statistics are exported to CSV."""
        path = tmp_path / "aggregate.csv"
        export_aggregate_csv(sample_aggregate_stats, path)

        assert path.exists()
        with path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1
        assert rows[0]["total_sessions"] == "3"
        assert rows[0]["winning_sessions"] == "1"
        assert rows[0]["losing_sessions"] == "1"
        assert rows[0]["push_sessions"] == "1"

    def test_excludes_session_profits_tuple(
        self, tmp_path: Path, sample_aggregate_stats: AggregateStatistics
    ) -> None:
        """Verify session_profits internal field is excluded."""
        path = tmp_path / "aggregate.csv"
        export_aggregate_csv(sample_aggregate_stats, path)

        with path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert "session_profits" not in rows[0]

    def test_bom_included_by_default(
        self, tmp_path: Path, sample_aggregate_stats: AggregateStatistics
    ) -> None:
        """Verify UTF-8 BOM is included by default."""
        path = tmp_path / "aggregate.csv"
        export_aggregate_csv(sample_aggregate_stats, path)

        with path.open("rb") as f:
            bom = f.read(3)
        assert bom == b"\xef\xbb\xbf"

    def test_bom_excluded_when_disabled(
        self, tmp_path: Path, sample_aggregate_stats: AggregateStatistics
    ) -> None:
        """Verify UTF-8 BOM is excluded when disabled."""
        path = tmp_path / "aggregate.csv"
        export_aggregate_csv(sample_aggregate_stats, path, include_bom=False)

        with path.open("rb") as f:
            start = f.read(3)
        assert start != b"\xef\xbb\xbf"

    def test_flattens_hand_frequency_dicts(
        self, tmp_path: Path, sample_session_results: list[SessionResult]
    ) -> None:
        """Verify nested hand frequency dicts are flattened with prefixed keys."""
        from let_it_ride.simulation.aggregation import aggregate_with_hand_frequencies

        # Create aggregate stats with hand frequency data
        hand_freqs = {"royal_flush": 1, "flush": 10, "high_card": 100}
        stats = aggregate_with_hand_frequencies(sample_session_results, hand_freqs)

        path = tmp_path / "aggregate.csv"
        export_aggregate_csv(stats, path)

        with path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Verify flattened keys exist with correct values
        assert rows[0]["hand_frequencies_royal_flush"] == "1"
        assert rows[0]["hand_frequencies_flush"] == "10"
        assert rows[0]["hand_frequencies_high_card"] == "100"
        # Verify percentage keys also exist
        assert "hand_frequency_pct_royal_flush" in rows[0]
        assert "hand_frequency_pct_flush" in rows[0]
        assert "hand_frequency_pct_high_card" in rows[0]


class TestExportHandsCsv:
    """Tests for export_hands_csv function."""

    def test_exports_all_hands(
        self, tmp_path: Path, sample_hand_records: list[HandRecord]
    ) -> None:
        """Verify all hands are exported to CSV."""
        path = tmp_path / "hands.csv"
        export_hands_csv(sample_hand_records, path)

        assert path.exists()
        with path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 3
        assert rows[0]["final_hand_rank"] == "royal_flush"
        assert rows[1]["final_hand_rank"] == "high_card"
        assert rows[2]["final_hand_rank"] == "three_of_a_kind"

    def test_exports_all_fields_by_default(
        self, tmp_path: Path, sample_hand_records: list[HandRecord]
    ) -> None:
        """Verify all fields are exported when no fields specified."""
        path = tmp_path / "hands.csv"
        export_hands_csv(sample_hand_records, path)

        with path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert set(rows[0].keys()) == set(HAND_RECORD_FIELDS)

    def test_field_selection(
        self, tmp_path: Path, sample_hand_records: list[HandRecord]
    ) -> None:
        """Verify only selected fields are exported."""
        path = tmp_path / "hands.csv"
        fields = ["hand_id", "final_hand_rank", "main_payout"]
        export_hands_csv(sample_hand_records, path, fields_to_export=fields)

        with path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert set(rows[0].keys()) == set(fields)

    def test_invalid_field_raises_error(
        self, tmp_path: Path, sample_hand_records: list[HandRecord]
    ) -> None:
        """Verify invalid field names raise ValueError."""
        path = tmp_path / "hands.csv"
        with pytest.raises(ValueError, match="Invalid field names"):
            export_hands_csv(sample_hand_records, path, fields_to_export=["invalid"])

    def test_empty_hands_raises_error(self, tmp_path: Path) -> None:
        """Verify empty hands iterable raises ValueError."""
        path = tmp_path / "hands.csv"
        with pytest.raises(ValueError, match="Cannot export empty hands iterable"):
            export_hands_csv([], path)

    def test_handles_none_values(
        self, tmp_path: Path, sample_hand_records: list[HandRecord]
    ) -> None:
        """Verify None values are handled correctly in CSV output."""
        path = tmp_path / "hands.csv"
        export_hands_csv(sample_hand_records, path)

        with path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # First two hands have shoe_id=None, bonus_hand_rank=None
        # CSV DictWriter represents Python None as empty string
        assert rows[0]["shoe_id"] == ""
        assert rows[0]["bonus_hand_rank"] == ""
        # Third hand has values
        assert rows[2]["shoe_id"] == "1"
        assert rows[2]["bonus_hand_rank"] == "three_of_a_kind"

    def test_special_characters_escaped(self, tmp_path: Path) -> None:
        """Verify special CSV characters are escaped correctly."""
        hands = [
            HandRecord(
                hand_id=0,
                session_id=0,
                shoe_id=None,
                cards_player="Ah, Kh, Qh",  # Comma in data
                cards_community='"Jh" Th',  # Quote in data
                decision_bet1="ride",
                decision_bet2="ride",
                final_hand_rank="high_card",
                base_bet=5.0,
                bets_at_risk=5.0,
                main_payout=0.0,
                bonus_bet=0.0,
                bonus_hand_rank=None,
                bonus_payout=0.0,
                bankroll_after=500.0,
            )
        ]
        path = tmp_path / "special.csv"
        export_hands_csv(hands, path)

        with path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # CSV module should properly escape commas and quotes
        assert rows[0]["cards_player"] == "Ah, Kh, Qh"
        assert rows[0]["cards_community"] == '"Jh" Th'

    def test_large_file_handling(self, tmp_path: Path) -> None:
        """Verify large number of hands can be exported."""
        # Create 10,000 hand records
        hands = [
            HandRecord(
                hand_id=i,
                session_id=i // 100,
                shoe_id=None,
                cards_player="Ah Kh Qh",
                cards_community="Jh Th",
                decision_bet1="ride",
                decision_bet2="ride",
                final_hand_rank="high_card",
                base_bet=5.0,
                bets_at_risk=5.0,
                main_payout=0.0,
                bonus_bet=0.0,
                bonus_hand_rank=None,
                bonus_payout=0.0,
                bankroll_after=500.0 - i,
            )
            for i in range(10000)
        ]

        path = tmp_path / "large_hands.csv"
        export_hands_csv(hands, path)

        with path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 10000

    def test_bom_excluded_when_disabled(
        self, tmp_path: Path, sample_hand_records: list[HandRecord]
    ) -> None:
        """Verify UTF-8 BOM is excluded when disabled."""
        path = tmp_path / "hands.csv"
        export_hands_csv(sample_hand_records, path, include_bom=False)

        with path.open("rb") as f:
            start = f.read(3)
        assert start != b"\xef\xbb\xbf"

    def test_accepts_generator(self, tmp_path: Path) -> None:
        """Verify export_hands_csv accepts a generator for memory efficiency."""

        def hand_generator():
            for i in range(100):
                yield HandRecord(
                    hand_id=i,
                    session_id=0,
                    shoe_id=None,
                    cards_player="Ah Kh Qh",
                    cards_community="Jh Th",
                    decision_bet1="ride",
                    decision_bet2="ride",
                    final_hand_rank="high_card",
                    base_bet=5.0,
                    bets_at_risk=5.0,
                    main_payout=0.0,
                    bonus_bet=0.0,
                    bonus_hand_rank=None,
                    bonus_payout=0.0,
                    bankroll_after=500.0,
                )

        path = tmp_path / "generator_hands.csv"
        export_hands_csv(hand_generator(), path)

        with path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 100

    def test_streaming_large_export(self, tmp_path: Path) -> None:
        """Verify large streaming export completes without loading all into memory.

        This test uses a generator to produce 50,000 records and validates the
        output by counting lines without reading the entire CSV into memory.
        This validates that the Iterable[HandRecord] signature enables memory-
        efficient exports for large datasets (targeting 10M hand support).
        """
        expected_count = 50000

        def hand_generator():
            for i in range(expected_count):
                yield HandRecord(
                    hand_id=i,
                    session_id=i // 1000,
                    shoe_id=None,
                    cards_player="Ah Kh Qh",
                    cards_community="Jh Th",
                    decision_bet1="ride",
                    decision_bet2="ride",
                    final_hand_rank="high_card",
                    base_bet=5.0,
                    bets_at_risk=5.0,
                    main_payout=0.0,
                    bonus_bet=0.0,
                    bonus_hand_rank=None,
                    bonus_payout=0.0,
                    bankroll_after=500.0 - (i % 100),
                )

        path = tmp_path / "streaming_hands.csv"
        export_hands_csv(hand_generator(), path)

        # Validate by counting lines without reading all into memory
        line_count = 0
        with path.open(encoding="utf-8-sig") as f:
            for _ in f:
                line_count += 1

        # expected_count data rows + 1 header row
        assert line_count == expected_count + 1

        # Verify file size is reasonable (each row ~70 bytes for this data)
        file_size = path.stat().st_size
        assert file_size > expected_count * 50  # At least 50 bytes per row
        assert file_size < expected_count * 150  # At most 150 bytes per row


class TestCSVExporter:
    """Tests for CSVExporter class."""

    def test_creates_output_directory(self, tmp_path: Path) -> None:
        """Verify output directory is created if it doesn't exist."""
        output_dir = tmp_path / "output" / "csv"
        exporter = CSVExporter(output_dir)

        results = [
            SessionResult(
                outcome=SessionOutcome.WIN,
                stop_reason=StopReason.WIN_LIMIT,
                hands_played=10,
                starting_bankroll=500.0,
                final_bankroll=600.0,
                session_profit=100.0,
                total_wagered=300.0,
                total_bonus_wagered=0.0,
                peak_bankroll=600.0,
                max_drawdown=0.0,
                max_drawdown_pct=0.0,
            )
        ]
        exporter.export_sessions(results)

        assert output_dir.exists()

    def test_export_sessions(
        self, tmp_path: Path, sample_session_results: list[SessionResult]
    ) -> None:
        """Verify export_sessions creates expected file."""
        exporter = CSVExporter(tmp_path, prefix="test")
        path = exporter.export_sessions(sample_session_results)

        assert path == tmp_path / "test_sessions.csv"
        assert path.exists()

    def test_export_aggregate(
        self, tmp_path: Path, sample_aggregate_stats: AggregateStatistics
    ) -> None:
        """Verify export_aggregate creates expected file."""
        exporter = CSVExporter(tmp_path, prefix="test")
        path = exporter.export_aggregate(sample_aggregate_stats)

        assert path == tmp_path / "test_aggregate.csv"
        assert path.exists()

    def test_export_hands(
        self, tmp_path: Path, sample_hand_records: list[HandRecord]
    ) -> None:
        """Verify export_hands creates expected file."""
        exporter = CSVExporter(tmp_path, prefix="test")
        path = exporter.export_hands(sample_hand_records)

        assert path == tmp_path / "test_hands.csv"
        assert path.exists()

    def test_export_sessions_with_field_selection(
        self, tmp_path: Path, sample_session_results: list[SessionResult]
    ) -> None:
        """Verify export_sessions respects field selection via class method."""
        exporter = CSVExporter(tmp_path, prefix="test")
        fields = ["outcome", "hands_played"]
        path = exporter.export_sessions(sample_session_results, fields_to_export=fields)

        with path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert set(rows[0].keys()) == set(fields)
        assert rows[0]["outcome"] == "win"
        assert rows[0]["hands_played"] == "25"

    def test_export_hands_with_field_selection(
        self, tmp_path: Path, sample_hand_records: list[HandRecord]
    ) -> None:
        """Verify export_hands respects field selection via class method."""
        exporter = CSVExporter(tmp_path, prefix="test")
        fields = ["hand_id", "final_hand_rank", "main_payout"]
        path = exporter.export_hands(sample_hand_records, fields_to_export=fields)

        with path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert set(rows[0].keys()) == set(fields)
        assert rows[0]["hand_id"] == "0"
        assert rows[0]["final_hand_rank"] == "royal_flush"

    def test_export_all_without_hands(
        self, tmp_path: Path, sample_session_results: list[SessionResult]
    ) -> None:
        """Verify export_all creates sessions and aggregate files."""
        from datetime import datetime

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
            total_hands=115,
        )

        exporter = CSVExporter(tmp_path, prefix="sim")
        paths = exporter.export_all(results, include_hands=False)

        assert len(paths) == 2
        assert (tmp_path / "sim_sessions.csv").exists()
        assert (tmp_path / "sim_aggregate.csv").exists()

    def test_export_all_with_hands(
        self,
        tmp_path: Path,
        sample_session_results: list[SessionResult],
        sample_hand_records: list[HandRecord],
    ) -> None:
        """Verify export_all includes hands when requested."""
        from datetime import datetime

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
            total_hands=115,
        )

        exporter = CSVExporter(tmp_path, prefix="sim")
        paths = exporter.export_all(
            results, include_hands=True, hands=sample_hand_records
        )

        assert len(paths) == 3
        assert (tmp_path / "sim_sessions.csv").exists()
        assert (tmp_path / "sim_aggregate.csv").exists()
        assert (tmp_path / "sim_hands.csv").exists()

    def test_export_all_include_hands_without_data_raises(
        self, tmp_path: Path, sample_session_results: list[SessionResult]
    ) -> None:
        """Verify export_all raises error if include_hands but no hands provided."""
        from datetime import datetime

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
            total_hands=115,
        )

        exporter = CSVExporter(tmp_path)
        with pytest.raises(ValueError, match="include_hands is True but hands list"):
            exporter.export_all(results, include_hands=True)

    def test_custom_prefix(
        self, tmp_path: Path, sample_session_results: list[SessionResult]
    ) -> None:
        """Verify custom prefix is used in filenames."""
        exporter = CSVExporter(tmp_path, prefix="my_simulation")
        path = exporter.export_sessions(sample_session_results)

        assert path.name == "my_simulation_sessions.csv"

    def test_bom_setting_propagates(
        self, tmp_path: Path, sample_session_results: list[SessionResult]
    ) -> None:
        """Verify BOM setting propagates to all exports."""
        exporter = CSVExporter(tmp_path, include_bom=False)
        path = exporter.export_sessions(sample_session_results)

        with path.open("rb") as f:
            start = f.read(3)
        assert start != b"\xef\xbb\xbf"

    def test_properties(self, tmp_path: Path) -> None:
        """Verify exporter properties are accessible."""
        exporter = CSVExporter(tmp_path, prefix="test", include_bom=False)

        assert exporter.output_dir == tmp_path
        assert exporter.prefix == "test"
        assert exporter.include_bom is False


class TestSeatNumberInSessionResult:
    """Tests for seat_number field in SessionResult and CSV export."""

    def test_session_result_with_seat_number(self) -> None:
        """Verify SessionResult can store seat_number."""
        result = SessionResult(
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
            seat_number=3,
        )
        assert result.seat_number == 3

    def test_session_result_seat_number_defaults_none(self) -> None:
        """Verify seat_number defaults to None for single-seat sessions."""
        result = SessionResult(
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
        )
        assert result.seat_number is None

    def test_with_seat_number_creates_copy(self) -> None:
        """Verify with_seat_number returns new SessionResult with seat_number.

        All 12 fields must be correctly copied to the new instance.
        """
        original = SessionResult(
            outcome=SessionOutcome.WIN,
            stop_reason=StopReason.WIN_LIMIT,
            hands_played=25,
            starting_bankroll=500.0,
            final_bankroll=600.0,
            session_profit=100.0,
            total_wagered=750.0,
            total_bonus_wagered=50.0,
            peak_bankroll=620.0,
            max_drawdown=50.0,
            max_drawdown_pct=0.08,
        )
        with_seat = original.with_seat_number(2)

        # Verify original is unchanged
        assert original.seat_number is None

        # Verify seat_number is set on copy
        assert with_seat.seat_number == 2

        # Verify ALL fields are correctly copied (all 12 fields)
        assert with_seat.outcome == original.outcome
        assert with_seat.stop_reason == original.stop_reason
        assert with_seat.hands_played == original.hands_played
        assert with_seat.starting_bankroll == original.starting_bankroll
        assert with_seat.final_bankroll == original.final_bankroll
        assert with_seat.session_profit == original.session_profit
        assert with_seat.total_wagered == original.total_wagered
        assert with_seat.total_bonus_wagered == original.total_bonus_wagered
        assert with_seat.peak_bankroll == original.peak_bankroll
        assert with_seat.max_drawdown == original.max_drawdown
        assert with_seat.max_drawdown_pct == original.max_drawdown_pct

    def test_to_dict_includes_seat_number(self) -> None:
        """Verify to_dict includes seat_number field."""
        result = SessionResult(
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
            seat_number=4,
        )
        d = result.to_dict()
        assert "seat_number" in d
        assert d["seat_number"] == 4

    def test_csv_export_includes_seat_number_column(self, tmp_path: Path) -> None:
        """Verify CSV export includes seat_number column."""
        results = [
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
                seat_number=1,
            ),
            SessionResult(
                outcome=SessionOutcome.LOSS,
                stop_reason=StopReason.LOSS_LIMIT,
                hands_played=30,
                starting_bankroll=500.0,
                final_bankroll=300.0,
                session_profit=-200.0,
                total_wagered=900.0,
                total_bonus_wagered=0.0,
                peak_bankroll=520.0,
                max_drawdown=220.0,
                max_drawdown_pct=0.42,
                seat_number=2,
            ),
        ]
        path = tmp_path / "sessions.csv"
        export_sessions_csv(results, path)

        with path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert "seat_number" in rows[0]
        assert rows[0]["seat_number"] == "1"
        assert rows[1]["seat_number"] == "2"

    def test_csv_export_seat_number_none_as_empty(self, tmp_path: Path) -> None:
        """Verify CSV export shows empty string for None seat_number."""
        results = [
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
                seat_number=None,
            ),
        ]
        path = tmp_path / "sessions.csv"
        export_sessions_csv(results, path)

        with path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert rows[0]["seat_number"] == ""

    def test_session_result_fields_includes_seat_number(self) -> None:
        """Verify SESSION_RESULT_FIELDS list includes seat_number."""
        assert "seat_number" in SESSION_RESULT_FIELDS
        # Should be first for easy identification in CSV
        assert SESSION_RESULT_FIELDS[0] == "seat_number"

    @pytest.mark.parametrize(
        "seat_number,expected",
        [
            (1, 1),  # Minimum valid seat
            (6, 6),  # Maximum valid seat (TableConfig max)
            (0, 0),  # Edge case: zero (no validation in with_seat_number)
            (-1, -1),  # Edge case: negative (no validation in with_seat_number)
            (100, 100),  # Edge case: large value (no validation in with_seat_number)
        ],
    )
    def test_with_seat_number_boundary_values(
        self, seat_number: int, expected: int
    ) -> None:
        """Verify with_seat_number accepts boundary values without error.

        Note: with_seat_number() does not validate seat numbers. Validation
        is handled at the TableConfig level (1-6 seats). This test documents
        that behavior and ensures no runtime errors occur.
        """
        result = SessionResult(
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
        )
        with_seat = result.with_seat_number(seat_number)
        assert with_seat.seat_number == expected

    def test_csv_export_with_max_seat_number(self, tmp_path: Path) -> None:
        """Verify CSV export works with maximum valid seat_number (6)."""
        results = [
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
                seat_number=6,
            ),
        ]
        path = tmp_path / "sessions.csv"
        export_sessions_csv(results, path)

        with path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert rows[0]["seat_number"] == "6"


class TestExportSeatAggregateCsv:
    """Tests for export_seat_aggregate_csv function."""

    @pytest.fixture
    def sample_chair_analysis(self) -> ChairPositionAnalysis:
        """Create sample ChairPositionAnalysis for testing."""
        seat_stats = (
            SeatStatistics(
                seat_number=1,
                total_rounds=100,
                wins=40,
                losses=55,
                pushes=5,
                win_rate=0.40,
                win_rate_ci_lower=0.31,
                win_rate_ci_upper=0.50,
                expected_value=-5.25,
                total_profit=-525.0,
            ),
            SeatStatistics(
                seat_number=2,
                total_rounds=100,
                wins=38,
                losses=57,
                pushes=5,
                win_rate=0.38,
                win_rate_ci_lower=0.29,
                win_rate_ci_upper=0.48,
                expected_value=-6.10,
                total_profit=-610.0,
            ),
            SeatStatistics(
                seat_number=3,
                total_rounds=100,
                wins=42,
                losses=53,
                pushes=5,
                win_rate=0.42,
                win_rate_ci_lower=0.33,
                win_rate_ci_upper=0.52,
                expected_value=-4.80,
                total_profit=-480.0,
            ),
        )
        return ChairPositionAnalysis(
            seat_statistics=seat_stats,
            chi_square_statistic=0.267,
            chi_square_p_value=0.875,
            is_position_independent=True,
        )

    def test_exports_seat_statistics(
        self, tmp_path: Path, sample_chair_analysis: ChairPositionAnalysis
    ) -> None:
        """Verify seat aggregate statistics are exported to CSV."""
        path = tmp_path / "seat_aggregate.csv"
        export_seat_aggregate_csv(sample_chair_analysis, path)

        assert path.exists()
        with path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # 3 seats + 1 summary row
        assert len(rows) == 4
        assert rows[0]["seat_number"] == "1"
        assert rows[1]["seat_number"] == "2"
        assert rows[2]["seat_number"] == "3"
        assert rows[3]["seat_number"] == "SUMMARY"

    def test_exports_per_seat_metrics(
        self, tmp_path: Path, sample_chair_analysis: ChairPositionAnalysis
    ) -> None:
        """Verify per-seat metrics are correctly exported."""
        path = tmp_path / "seat_aggregate.csv"
        export_seat_aggregate_csv(sample_chair_analysis, path)

        with path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Check seat 1 metrics
        assert rows[0]["total_rounds"] == "100"
        assert rows[0]["wins"] == "40"
        assert rows[0]["losses"] == "55"
        assert rows[0]["pushes"] == "5"
        assert rows[0]["win_rate"] == "0.4"
        assert rows[0]["total_profit"] == "-525.0"

    def test_exports_chi_square_in_summary(
        self, tmp_path: Path, sample_chair_analysis: ChairPositionAnalysis
    ) -> None:
        """Verify chi-square results are in summary row."""
        path = tmp_path / "seat_aggregate.csv"
        export_seat_aggregate_csv(sample_chair_analysis, path)

        with path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        summary = rows[-1]
        assert summary["chi_square_statistic"] == "0.267"
        assert summary["chi_square_p_value"] == "0.875"
        assert summary["is_position_independent"] == "True"

    def test_summary_row_aggregates_totals(
        self, tmp_path: Path, sample_chair_analysis: ChairPositionAnalysis
    ) -> None:
        """Verify summary row has aggregated totals."""
        path = tmp_path / "seat_aggregate.csv"
        export_seat_aggregate_csv(sample_chair_analysis, path)

        with path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        summary = rows[-1]
        assert summary["total_rounds"] == "300"  # 100 * 3 seats
        assert summary["wins"] == "120"  # 40 + 38 + 42
        assert summary["losses"] == "165"  # 55 + 57 + 53
        assert summary["total_profit"] == "-1615.0"  # -525 + -610 + -480

    def test_empty_seat_statistics_raises_error(self, tmp_path: Path) -> None:
        """Verify empty seat statistics raises ValueError."""
        empty_analysis = ChairPositionAnalysis(
            seat_statistics=(),
            chi_square_statistic=0.0,
            chi_square_p_value=1.0,
            is_position_independent=True,
        )
        path = tmp_path / "seat_aggregate.csv"
        with pytest.raises(ValueError, match="Cannot export empty seat statistics"):
            export_seat_aggregate_csv(empty_analysis, path)

    def test_bom_included_by_default(
        self, tmp_path: Path, sample_chair_analysis: ChairPositionAnalysis
    ) -> None:
        """Verify UTF-8 BOM is included by default."""
        path = tmp_path / "seat_aggregate.csv"
        export_seat_aggregate_csv(sample_chair_analysis, path)

        with path.open("rb") as f:
            bom = f.read(3)
        assert bom == b"\xef\xbb\xbf"

    def test_bom_excluded_when_disabled(
        self, tmp_path: Path, sample_chair_analysis: ChairPositionAnalysis
    ) -> None:
        """Verify UTF-8 BOM is excluded when disabled."""
        path = tmp_path / "seat_aggregate.csv"
        export_seat_aggregate_csv(sample_chair_analysis, path, include_bom=False)

        with path.open("rb") as f:
            start = f.read(3)
        assert start != b"\xef\xbb\xbf"

    def test_seat_aggregate_fields_complete(self) -> None:
        """Verify SEAT_AGGREGATE_FIELDS has all expected fields."""
        expected_fields = [
            "seat_number",
            "total_rounds",
            "wins",
            "losses",
            "pushes",
            "win_rate",
            "win_rate_ci_lower",
            "win_rate_ci_upper",
            "expected_value",
            "total_profit",
        ]
        assert expected_fields == SEAT_AGGREGATE_FIELDS


class TestSeatNumberE2EFlow:
    """End-to-end tests for seat_number data flow from simulation to CSV export."""

    def test_multi_seat_parallel_execution_to_csv_export(self, tmp_path: Path) -> None:
        """Verify seat_number flows correctly: parallel execution -> CSV export.

        This is an E2E test that:
        1. Runs a multi-seat parallel simulation
        2. Exports results to CSV
        3. Verifies each seat_number is correctly preserved in the export
        """
        from let_it_ride.config.models import (
            BankrollConfig,
            BettingSystemConfig,
            FullConfig,
            SimulationConfig,
            StopConditionsConfig,
            StrategyConfig,
            TableConfig,
        )
        from let_it_ride.simulation.controller import SimulationController

        num_sessions = 5
        num_seats = 3

        config = FullConfig(
            simulation=SimulationConfig(
                num_sessions=num_sessions,
                hands_per_session=20,
                random_seed=12345,
                workers=2,  # Parallel execution
            ),
            table=TableConfig(num_seats=num_seats),
            bankroll=BankrollConfig(
                starting_amount=500.0,
                base_bet=5.0,
                stop_conditions=StopConditionsConfig(
                    win_limit=100.0,
                    loss_limit=200.0,
                    stop_on_insufficient_funds=True,
                ),
                betting_system=BettingSystemConfig(type="flat"),
            ),
            strategy=StrategyConfig(type="basic"),
        )

        # Run simulation
        controller = SimulationController(config)
        results = controller.run()

        # Export to CSV
        csv_path = tmp_path / "sessions.csv"
        export_sessions_csv(results.session_results, csv_path)

        # Read and verify CSV
        with csv_path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Should have num_sessions * num_seats rows
        assert len(rows) == num_sessions * num_seats

        # Verify seat_number column exists and has valid values
        seat_numbers = [int(row["seat_number"]) for row in rows]

        # Each seat (1, 2, 3) should appear num_sessions times
        for seat in range(1, num_seats + 1):
            count = seat_numbers.count(seat)
            assert count == num_sessions, (
                f"Seat {seat} should appear {num_sessions} times, got {count}"
            )

        # Verify seat_number is the first column
        assert next(iter(rows[0].keys())) == "seat_number"

    def test_multi_seat_sequential_execution_to_csv_export(self, tmp_path: Path) -> None:
        """Verify seat_number flows correctly: sequential execution -> CSV export."""
        from let_it_ride.config.models import (
            BankrollConfig,
            BettingSystemConfig,
            FullConfig,
            SimulationConfig,
            StopConditionsConfig,
            StrategyConfig,
            TableConfig,
        )
        from let_it_ride.simulation.controller import SimulationController

        num_sessions = 3
        num_seats = 4

        config = FullConfig(
            simulation=SimulationConfig(
                num_sessions=num_sessions,
                hands_per_session=15,
                random_seed=67890,
                workers=1,  # Sequential execution
            ),
            table=TableConfig(num_seats=num_seats),
            bankroll=BankrollConfig(
                starting_amount=500.0,
                base_bet=5.0,
                stop_conditions=StopConditionsConfig(
                    win_limit=100.0,
                    loss_limit=200.0,
                    stop_on_insufficient_funds=True,
                ),
                betting_system=BettingSystemConfig(type="flat"),
            ),
            strategy=StrategyConfig(type="basic"),
        )

        # Run simulation
        controller = SimulationController(config)
        results = controller.run()

        # Export to CSV
        csv_path = tmp_path / "sessions.csv"
        export_sessions_csv(results.session_results, csv_path)

        # Read and verify CSV
        with csv_path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Should have num_sessions * num_seats rows
        assert len(rows) == num_sessions * num_seats

        # Verify all seat numbers are valid (1 to num_seats)
        for row in rows:
            seat_num = int(row["seat_number"])
            assert 1 <= seat_num <= num_seats, f"Invalid seat_number: {seat_num}"

        # Each seat should appear exactly num_sessions times
        seat_numbers = [int(row["seat_number"]) for row in rows]
        for seat in range(1, num_seats + 1):
            assert seat_numbers.count(seat) == num_sessions
