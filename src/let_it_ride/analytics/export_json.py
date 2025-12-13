"""JSON export functionality for simulation results.

This module provides JSON export with full configuration preservation:
- export_json(): Export SimulationResults to JSON file
- load_json(): Load JSON file back to dictionary
- ResultsEncoder: Custom JSON encoder for simulation data types
- JSONExporter: Class to orchestrate JSON export
"""

from __future__ import annotations

import json
from dataclasses import fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from let_it_ride import __version__
from let_it_ride.analytics.export_csv import EXCLUDED_AGGREGATE_FIELDS

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from let_it_ride.simulation.aggregation import AggregateStatistics
    from let_it_ride.simulation.controller import SimulationResults
    from let_it_ride.simulation.results import HandRecord

# Schema version for the JSON output format
JSON_SCHEMA_VERSION = "1.0"


class ResultsEncoder(json.JSONEncoder):
    """Custom JSON encoder for simulation data types.

    Handles:
    - datetime objects (ISO format)
    - Enum values (string value)
    - Pydantic BaseModel (model_dump())
    - dataclasses (to dict)
    """

    def default(self, obj: Any) -> Any:
        """Encode non-standard types to JSON-serializable values.

        Args:
            obj: Object to encode.

        Returns:
            JSON-serializable representation.

        Raises:
            TypeError: If object type is not supported.
        """
        if isinstance(obj, datetime):
            return obj.isoformat()

        if isinstance(obj, Enum):
            return obj.value

        if isinstance(obj, BaseModel):
            return obj.model_dump()

        if is_dataclass(obj) and not isinstance(obj, type):
            return self._dataclass_to_dict(obj)

        return super().default(obj)

    def _dataclass_to_dict(self, obj: Any) -> dict[str, Any]:
        """Convert dataclass to dictionary, handling nested types.

        Args:
            obj: Dataclass instance.

        Returns:
            Dictionary representation.
        """
        result: dict[str, Any] = {}
        for field in fields(obj):
            value = getattr(obj, field.name)
            if isinstance(value, datetime):
                result[field.name] = value.isoformat()
            elif isinstance(value, Enum):
                result[field.name] = value.value
            elif is_dataclass(value) and not isinstance(value, type):
                result[field.name] = self._dataclass_to_dict(value)
            else:
                result[field.name] = value
        return result


def _aggregate_stats_to_dict(stats: AggregateStatistics) -> dict[str, Any]:
    """Convert AggregateStatistics to dictionary for JSON export.

    Unlike CSV export, nested dictionaries (hand_frequencies, hand_frequency_pct)
    are preserved as nested structures. Internal fields (session_profits) are excluded.

    Args:
        stats: AggregateStatistics to convert.

    Returns:
        Dictionary with all fields suitable for JSON export.
    """
    result: dict[str, Any] = {}

    for field in fields(stats):
        if field.name in EXCLUDED_AGGREGATE_FIELDS:
            continue  # Skip internal field
        result[field.name] = getattr(stats, field.name)

    return result


def _build_metadata() -> dict[str, Any]:
    """Build metadata section for JSON output.

    Returns:
        Dictionary with schema version, timestamp (UTC), and simulator version.
    """
    return {
        "schema_version": JSON_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "simulator_version": __version__,
    }


def export_json(
    results: SimulationResults,
    path: Path,
    pretty: bool = True,
    include_config: bool = True,
    include_hands: bool = False,
    hands: Iterable[HandRecord] | None = None,
) -> None:
    """Export simulation results to JSON file.

    Args:
        results: SimulationResults to export.
        path: Output file path.
        pretty: If True, format with indentation for readability.
        include_config: If True, include full configuration in output.
        include_hands: If True and hands are provided, include hand records.
        hands: Optional iterable of HandRecord objects for per-hand export.

    Raises:
        ValueError: If include_hands is True but hands is None or empty.

    Note:
        When include_hands=True, all hand data is materialized into memory before
        writing. For simulations with millions of hands, this may consume significant
        memory (approximately 300 bytes per hand). For very large exports (>1M hands),
        consider using CSV export for hand data or exporting in batches.
    """
    from let_it_ride.simulation.aggregation import aggregate_results

    # Build output structure
    output: dict[str, Any] = {
        "metadata": _build_metadata(),
    }

    # Include config if requested
    if include_config:
        output["config"] = results.config.model_dump()

    # Add timing information
    output["simulation_timing"] = {
        "start_time": results.start_time.isoformat(),
        "end_time": results.end_time.isoformat(),
        "total_hands": results.total_hands,
    }

    # Add aggregate statistics
    stats = aggregate_results(results.session_results)
    output["aggregate_statistics"] = _aggregate_stats_to_dict(stats)

    # Add session results
    output["session_results"] = [r.to_dict() for r in results.session_results]

    # Optionally add hands
    if include_hands:
        if hands is None:
            raise ValueError("include_hands is True but hands is None")
        hands_list = [h.to_dict() for h in hands]
        if not hands_list:
            raise ValueError("include_hands is True but hands iterable is empty")
        output["hands"] = hands_list

    # Write to file with explicit buffering for large exports
    indent = 2 if pretty else None
    with path.open("w", encoding="utf-8", buffering=65536) as f:
        json.dump(output, f, cls=ResultsEncoder, indent=indent, ensure_ascii=False)
        if pretty:
            f.write("\n")  # Trailing newline for pretty output


def load_json(path: Path) -> dict[str, Any]:
    """Load simulation results from JSON file.

    Returns a dictionary rather than attempting to reconstruct the full
    SimulationResults object, since that would require re-instantiating
    all Pydantic models and dataclasses with their validation.

    Args:
        path: Path to JSON file.

    Returns:
        Dictionary containing the JSON data with these keys:
        - metadata: Schema version, timestamp, simulator version
        - config: Full configuration (if included)
        - simulation_timing: Start/end times and total hands
        - aggregate_statistics: Aggregate statistics
        - session_results: List of session result dicts
        - hands: List of hand record dicts (if included)

    Raises:
        FileNotFoundError: If file does not exist.
        json.JSONDecodeError: If file is not valid JSON.
    """
    with path.open("r", encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
        return data


class JSONExporter:
    """Orchestrates JSON export of simulation results.

    Attributes:
        output_dir: Directory where JSON files are written.
        prefix: Filename prefix for exported files.
        pretty: Whether to format with indentation.
    """

    __slots__ = ("_output_dir", "_prefix", "_pretty")

    def __init__(
        self,
        output_dir: Path,
        prefix: str = "simulation",
        pretty: bool = True,
    ) -> None:
        """Initialize the JSON exporter.

        Args:
            output_dir: Directory for output files. Created if it doesn't exist.
            prefix: Filename prefix (default: "simulation").
            pretty: Format with indentation for readability (default: True).
        """
        self._output_dir = output_dir
        self._prefix = prefix
        self._pretty = pretty

    @property
    def output_dir(self) -> Path:
        """Return the output directory."""
        return self._output_dir

    @property
    def prefix(self) -> str:
        """Return the filename prefix."""
        return self._prefix

    @property
    def pretty(self) -> bool:
        """Return whether pretty formatting is enabled."""
        return self._pretty

    def _ensure_output_dir(self) -> None:
        """Create output directory if it doesn't exist.

        Creates directory with 0o755 permissions (owner rwx, group/other rx).
        """
        self._output_dir.mkdir(parents=True, exist_ok=True, mode=0o755)

    def export(
        self,
        results: SimulationResults,
        include_config: bool = True,
        include_hands: bool = False,
        hands: Iterable[HandRecord] | None = None,
    ) -> Path:
        """Export simulation results to JSON file.

        Args:
            results: SimulationResults to export.
            include_config: If True, include full configuration.
            include_hands: If True and hands provided, include hand records.
            hands: Optional iterable of HandRecord objects.

        Returns:
            Path to the created file.

        Raises:
            ValueError: If include_hands is True but hands is None or empty.
        """
        self._ensure_output_dir()
        path = self._output_dir / f"{self._prefix}_results.json"
        export_json(
            results,
            path,
            pretty=self._pretty,
            include_config=include_config,
            include_hands=include_hands,
            hands=hands,
        )
        return path
