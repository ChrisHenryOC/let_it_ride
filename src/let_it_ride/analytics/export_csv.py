"""CSV export functionality for simulation results.

This module provides CSV export for session summaries, aggregate statistics,
and per-hand detail records:
- export_sessions_csv(): Export list of SessionResult to CSV
- export_aggregate_csv(): Export AggregateStatistics to CSV
- export_hands_csv(): Export list of HandRecord to CSV
- CSVExporter: Class to orchestrate all exports to a directory
"""

from __future__ import annotations

import csv
from dataclasses import fields
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from let_it_ride.analytics.chair_position import (
        ChairPositionAnalysis,
        SeatStatistics,
    )
    from let_it_ride.simulation.aggregation import AggregateStatistics
    from let_it_ride.simulation.controller import SimulationResults
    from let_it_ride.simulation.results import HandRecord
    from let_it_ride.simulation.session import SessionResult

# Default fields for SessionResult export (all serializable fields)
# NOTE: Must stay in sync with SessionResult dataclass in simulation/session.py
SESSION_RESULT_FIELDS = [
    "seat_number",
    "outcome",
    "stop_reason",
    "hands_played",
    "starting_bankroll",
    "final_bankroll",
    "session_profit",
    "total_wagered",
    "total_bonus_wagered",
    "peak_bankroll",
    "max_drawdown",
    "max_drawdown_pct",
]

# Default fields for HandRecord export (all fields)
# NOTE: Must stay in sync with HandRecord dataclass in simulation/results.py
HAND_RECORD_FIELDS = [
    "hand_id",
    "session_id",
    "shoe_id",
    "cards_player",
    "cards_community",
    "decision_bet1",
    "decision_bet2",
    "final_hand_rank",
    "base_bet",
    "bets_at_risk",
    "main_payout",
    "bonus_bet",
    "bonus_hand_rank",
    "bonus_payout",
    "bankroll_after",
]

# Fields to exclude from AggregateStatistics export (internal fields)
# NOTE: Must stay in sync with AggregateStatistics dataclass in simulation/aggregation.py
EXCLUDED_AGGREGATE_FIELDS = frozenset({"session_profits"})


def _aggregate_stats_to_dict(stats: AggregateStatistics) -> dict[str, Any]:
    """Convert AggregateStatistics to dictionary for CSV export.

    Nested dictionaries (hand_frequencies, hand_frequency_pct) are flattened
    with prefixed keys. Internal fields (session_profits) are excluded.

    Args:
        stats: AggregateStatistics to convert.

    Returns:
        Dictionary with all fields suitable for CSV export.
    """
    result: dict[str, Any] = {}

    # Add all simple fields except internal ones (EXCLUDED_AGGREGATE_FIELDS)
    for field in fields(stats):
        if field.name in EXCLUDED_AGGREGATE_FIELDS:
            continue  # Skip internal field
        value = getattr(stats, field.name)
        if isinstance(value, dict):
            # Flatten nested dicts with prefix
            for key, val in value.items():
                result[f"{field.name}_{key}"] = val
        else:
            result[field.name] = value

    return result


def export_sessions_csv(
    results: list[SessionResult],
    path: Path,
    fields_to_export: list[str] | None = None,
    include_bom: bool = True,
) -> None:
    """Export session results to CSV file.

    Args:
        results: List of SessionResult objects to export.
        path: Output file path.
        fields_to_export: List of field names to include. None exports all fields.
        include_bom: If True, include UTF-8 BOM for Excel compatibility.

    Raises:
        ValueError: If results list is empty or invalid field names provided.
    """
    if not results:
        raise ValueError("Cannot export empty results list")

    field_names = fields_to_export or SESSION_RESULT_FIELDS

    # Validate field names
    invalid_fields = set(field_names) - set(SESSION_RESULT_FIELDS)
    if invalid_fields:
        raise ValueError(f"Invalid field names: {invalid_fields}")

    encoding = "utf-8-sig" if include_bom else "utf-8"
    with path.open("w", encoding=encoding, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=field_names, extrasaction="ignore")
        writer.writeheader()
        for result in results:
            row = result.to_dict()
            writer.writerow(row)


def export_aggregate_csv(
    stats: AggregateStatistics,
    path: Path,
    include_bom: bool = True,
) -> None:
    """Export aggregate statistics to CSV file.

    The aggregate statistics are exported as a single row with all metrics.
    Nested dictionaries (hand frequencies) are flattened with prefixed keys.

    Note:
        Unlike export_sessions_csv and export_hands_csv, this function does not
        support field selection. Aggregate stats include dynamically-generated
        column names (e.g., hand_frequencies_flush) that are determined at
        runtime based on observed hand types. Since aggregate export produces
        a single summary row, all columns are exported.

    Args:
        stats: AggregateStatistics to export.
        path: Output file path.
        include_bom: If True, include UTF-8 BOM for Excel compatibility.
    """
    row = _aggregate_stats_to_dict(stats)

    encoding = "utf-8-sig" if include_bom else "utf-8"
    with path.open("w", encoding=encoding, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        writer.writeheader()
        writer.writerow(row)


def export_hands_csv(
    hands: Iterable[HandRecord],
    path: Path,
    fields_to_export: list[str] | None = None,
    include_bom: bool = True,
) -> None:
    """Export hand records to CSV file.

    Accepts an Iterable to support streaming/generator-based exports for
    memory efficiency when handling millions of hands.

    Args:
        hands: Iterable of HandRecord objects to export (can be generator).
        path: Output file path.
        fields_to_export: List of field names to include. None exports all fields.
        include_bom: If True, include UTF-8 BOM for Excel compatibility.

    Raises:
        ValueError: If hands iterable is empty or invalid field names provided.
    """
    field_names = fields_to_export or HAND_RECORD_FIELDS

    # Validate field names upfront
    invalid_fields = set(field_names) - set(HAND_RECORD_FIELDS)
    if invalid_fields:
        raise ValueError(f"Invalid field names: {invalid_fields}")

    encoding = "utf-8-sig" if include_bom else "utf-8"
    with path.open("w", encoding=encoding, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=field_names, extrasaction="ignore")
        writer.writeheader()

        count = 0
        for hand in hands:
            writer.writerow(hand.to_dict())
            count += 1

        if count == 0:
            raise ValueError("Cannot export empty hands iterable")


class CSVExporter:
    """Orchestrates CSV export of simulation results to a directory.

    Attributes:
        output_dir: Directory where CSV files are written.
        prefix: Filename prefix for all exported files.
        include_bom: Whether to include UTF-8 BOM for Excel compatibility.
    """

    __slots__ = ("_output_dir", "_prefix", "_include_bom")

    def __init__(
        self,
        output_dir: Path,
        prefix: str = "simulation",
        include_bom: bool = True,
    ) -> None:
        """Initialize the CSV exporter.

        Args:
            output_dir: Directory for output files. Created if it doesn't exist.
            prefix: Filename prefix (default: "simulation").
            include_bom: Include UTF-8 BOM for Excel compatibility (default: True).
        """
        self._output_dir = output_dir
        self._prefix = prefix
        self._include_bom = include_bom

    @property
    def output_dir(self) -> Path:
        """Return the output directory."""
        return self._output_dir

    @property
    def prefix(self) -> str:
        """Return the filename prefix."""
        return self._prefix

    @property
    def include_bom(self) -> bool:
        """Return whether BOM is included."""
        return self._include_bom

    def _ensure_output_dir(self) -> None:
        """Create output directory if it doesn't exist.

        Creates directory with 0o755 permissions (owner rwx, group/other rx).
        """
        self._output_dir.mkdir(parents=True, exist_ok=True, mode=0o755)

    def export_sessions(
        self,
        results: list[SessionResult],
        fields_to_export: list[str] | None = None,
    ) -> Path:
        """Export session results to CSV.

        Args:
            results: List of SessionResult objects.
            fields_to_export: Fields to include. None for all fields.

        Returns:
            Path to the created file.
        """
        self._ensure_output_dir()
        path = self._output_dir / f"{self._prefix}_sessions.csv"
        export_sessions_csv(results, path, fields_to_export, self._include_bom)
        return path

    def export_aggregate(self, stats: AggregateStatistics) -> Path:
        """Export aggregate statistics to CSV.

        Args:
            stats: AggregateStatistics to export.

        Returns:
            Path to the created file.
        """
        self._ensure_output_dir()
        path = self._output_dir / f"{self._prefix}_aggregate.csv"
        export_aggregate_csv(stats, path, self._include_bom)
        return path

    def export_hands(
        self,
        hands: Iterable[HandRecord],
        fields_to_export: list[str] | None = None,
    ) -> Path:
        """Export hand records to CSV.

        Accepts an Iterable to support streaming/generator-based exports.

        Args:
            hands: Iterable of HandRecord objects (can be generator).
            fields_to_export: Fields to include. None for all fields.

        Returns:
            Path to the created file.
        """
        self._ensure_output_dir()
        path = self._output_dir / f"{self._prefix}_hands.csv"
        export_hands_csv(hands, path, fields_to_export, self._include_bom)
        return path

    def export_seat_aggregate(self, analysis: ChairPositionAnalysis) -> Path:
        """Export per-seat aggregate statistics to CSV.

        Args:
            analysis: ChairPositionAnalysis from analyze_session_results_by_seat().

        Returns:
            Path to the created file.
        """
        self._ensure_output_dir()
        path = self._output_dir / f"{self._prefix}_seat_aggregate.csv"
        export_seat_aggregate_csv(analysis, path, self._include_bom)
        return path

    def export_all(
        self,
        results: SimulationResults,
        include_hands: bool = False,
        hands: Iterable[HandRecord] | None = None,
        include_seat_aggregate: bool = False,
        num_seats: int = 1,
    ) -> list[Path]:
        """Export all simulation results to CSV files.

        Args:
            results: SimulationResults containing session results.
            include_hands: If True and hands are provided, export hand records.
            hands: Optional iterable of HandRecord objects for per-hand export.
            include_seat_aggregate: If True and num_seats > 1, export per-seat
                aggregate statistics.
            num_seats: Number of seats in the simulation (for seat aggregate).

        Returns:
            List of paths to created files.

        Raises:
            ValueError: If include_hands is True but hands is None or empty,
                if session_results is empty (from export_sessions), or if
                include_seat_aggregate is True but results lack seat_number data.
        """
        # Deferred imports to avoid circular dependencies
        from let_it_ride.analytics.chair_position import (
            _build_analysis_from_aggregations,
        )
        from let_it_ride.analytics.chair_position import (
            _SeatAggregation as ChairSeatAggregation,
        )
        from let_it_ride.simulation.aggregation import (
            aggregate_results,
            aggregate_with_seats,
        )

        self._ensure_output_dir()
        created_files: list[Path] = []

        # Export sessions (first iteration over results)
        sessions_path = self.export_sessions(results.session_results)
        created_files.append(sessions_path)

        # Compute aggregate statistics and optionally seat aggregations in one pass
        # This combines what was previously two separate iterations
        need_seat_aggregate = include_seat_aggregate and num_seats > 1

        seat_aggregations: dict[int, ChairSeatAggregation] | None = None

        if need_seat_aggregate:
            # Single pass: compute both aggregate stats and seat aggregations
            stats, seat_aggregations_raw = aggregate_with_seats(results.session_results)
            # Convert to chair_position's _SeatAggregation type for compatibility
            seat_aggregations = {}
            for seat_num, agg in seat_aggregations_raw.items():
                chair_agg = ChairSeatAggregation()
                chair_agg.wins = agg.wins
                chair_agg.losses = agg.losses
                chair_agg.pushes = agg.pushes
                chair_agg.total_profit = agg.total_profit
                seat_aggregations[seat_num] = chair_agg
        else:
            # Standard path: just compute aggregate stats
            stats = aggregate_results(results.session_results)

        aggregate_path = self.export_aggregate(stats)
        created_files.append(aggregate_path)

        # Optionally export hands
        if include_hands:
            if not hands:
                raise ValueError(
                    "include_hands is True but hands list is None or empty"
                )
            hands_path = self.export_hands(hands)
            created_files.append(hands_path)

        # Optionally export seat aggregate (multi-seat only)
        if need_seat_aggregate:
            if not seat_aggregations:
                raise ValueError("No seat data found in results")
            analysis = _build_analysis_from_aggregations(
                seat_aggregations,
                confidence_level=0.95,
                significance_level=0.05,
            )
            seat_aggregate_path = self.export_seat_aggregate(analysis)
            created_files.append(seat_aggregate_path)

        return created_files


# Label for summary row in seat aggregate CSV export
SUMMARY_ROW_LABEL = "SUMMARY"

# Seat aggregate export fields from SeatStatistics dataclass
# NOTE: Must stay in sync with SeatStatistics dataclass in analytics/chair_position.py
SEAT_AGGREGATE_FIELDS = [
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


def _seat_statistics_to_dict(stats: SeatStatistics) -> dict[str, Any]:
    """Convert SeatStatistics to dictionary for CSV export.

    Args:
        stats: SeatStatistics to convert.

    Returns:
        Dictionary with all fields suitable for CSV export.
    """
    return {
        "seat_number": stats.seat_number,
        "total_rounds": stats.total_rounds,
        "wins": stats.wins,
        "losses": stats.losses,
        "pushes": stats.pushes,
        "win_rate": stats.win_rate,
        "win_rate_ci_lower": stats.win_rate_ci_lower,
        "win_rate_ci_upper": stats.win_rate_ci_upper,
        "expected_value": stats.expected_value,
        "total_profit": stats.total_profit,
    }


def export_seat_aggregate_csv(
    analysis: ChairPositionAnalysis,
    path: Path,
    include_bom: bool = True,
) -> None:
    """Export per-seat aggregate statistics to CSV file.

    Each row represents one seat with its statistics including win rate,
    confidence intervals, and profit metrics. An additional row at the end
    contains the chi-square test results for seat independence.

    Args:
        analysis: ChairPositionAnalysis from analyze_chair_positions() or
            analyze_session_results_by_seat().
        path: Output file path.
        include_bom: If True, include UTF-8 BOM for Excel compatibility.

    Raises:
        ValueError: If analysis has no seat statistics.
    """
    if not analysis.seat_statistics:
        raise ValueError("Cannot export empty seat statistics")

    encoding = "utf-8-sig" if include_bom else "utf-8"

    # Add summary fields to the columns
    extended_fields = [
        *SEAT_AGGREGATE_FIELDS,
        "chi_square_statistic",
        "chi_square_p_value",
        "is_position_independent",
    ]

    with path.open("w", encoding=encoding, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=extended_fields, extrasaction="ignore")
        writer.writeheader()

        # Write per-seat rows
        for seat_stats in analysis.seat_statistics:
            row = _seat_statistics_to_dict(seat_stats)
            # Leave summary fields empty for per-seat rows
            row["chi_square_statistic"] = ""
            row["chi_square_p_value"] = ""
            row["is_position_independent"] = ""
            writer.writerow(row)

        # Write summary row with chi-square results
        summary_row: dict[str, Any] = {
            "seat_number": SUMMARY_ROW_LABEL,
            "total_rounds": sum(s.total_rounds for s in analysis.seat_statistics),
            "wins": sum(s.wins for s in analysis.seat_statistics),
            "losses": sum(s.losses for s in analysis.seat_statistics),
            "pushes": sum(s.pushes for s in analysis.seat_statistics),
            "win_rate": "",
            "win_rate_ci_lower": "",
            "win_rate_ci_upper": "",
            "expected_value": "",
            "total_profit": sum(s.total_profit for s in analysis.seat_statistics),
            "chi_square_statistic": analysis.chi_square_statistic,
            "chi_square_p_value": analysis.chi_square_p_value,
            "is_position_independent": analysis.is_position_independent,
        }
        writer.writerow(summary_row)
