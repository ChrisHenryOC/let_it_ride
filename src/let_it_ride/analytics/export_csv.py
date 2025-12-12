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

    from let_it_ride.simulation.aggregation import AggregateStatistics
    from let_it_ride.simulation.controller import SimulationResults
    from let_it_ride.simulation.results import HandRecord
    from let_it_ride.simulation.session import SessionResult

# Default fields for SessionResult export (all serializable fields)
# NOTE: Must stay in sync with SessionResult dataclass in simulation/session.py
SESSION_RESULT_FIELDS = [
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


def _session_result_to_dict(result: SessionResult) -> dict[str, Any]:
    """Convert SessionResult to dictionary for CSV export.

    Enum values are converted to their string values.

    Args:
        result: SessionResult to convert.

    Returns:
        Dictionary with all fields suitable for CSV export.
    """
    return {
        "outcome": result.outcome.value,
        "stop_reason": result.stop_reason.value,
        "hands_played": result.hands_played,
        "starting_bankroll": result.starting_bankroll,
        "final_bankroll": result.final_bankroll,
        "session_profit": result.session_profit,
        "total_wagered": result.total_wagered,
        "total_bonus_wagered": result.total_bonus_wagered,
        "peak_bankroll": result.peak_bankroll,
        "max_drawdown": result.max_drawdown,
        "max_drawdown_pct": result.max_drawdown_pct,
    }


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
            row = _session_result_to_dict(result)
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

    def export_all(
        self,
        results: SimulationResults,
        include_hands: bool = False,
        hands: Iterable[HandRecord] | None = None,
    ) -> list[Path]:
        """Export all simulation results to CSV files.

        Args:
            results: SimulationResults containing session results.
            include_hands: If True and hands are provided, export hand records.
            hands: Optional iterable of HandRecord objects for per-hand export.

        Returns:
            List of paths to created files.

        Raises:
            ValueError: If include_hands is True but hands is None or empty,
                or if session_results is empty (from export_sessions).
        """
        from let_it_ride.simulation.aggregation import aggregate_results

        self._ensure_output_dir()
        created_files: list[Path] = []

        # Export sessions
        sessions_path = self.export_sessions(results.session_results)
        created_files.append(sessions_path)

        # Export aggregate statistics
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

        return created_files
