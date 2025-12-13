"""Statistics and reporting.

This module contains analytics and export functionality:
- Core statistics calculator
- Statistical validation
- Chair position analytics
- Strategy comparison analytics
- Export formats (CSV, JSON, HTML)
- Visualizations (histograms, trajectories)
"""

from let_it_ride.analytics.chair_position import (
    ChairPositionAnalysis,
    SeatStatistics,
    analyze_chair_positions,
)
from let_it_ride.analytics.export_csv import (
    CSVExporter,
    export_aggregate_csv,
    export_hands_csv,
    export_sessions_csv,
)
from let_it_ride.analytics.export_json import (
    JSONExporter,
    ResultsEncoder,
    export_json,
    load_json,
)
from let_it_ride.analytics.statistics import (
    ConfidenceInterval,
    DetailedStatistics,
    DistributionStats,
    RiskMetrics,
    calculate_statistics,
    calculate_statistics_from_results,
)
from let_it_ride.analytics.validation import (
    ChiSquareResult,
    ValidationReport,
    calculate_chi_square,
    calculate_wilson_confidence_interval,
    validate_simulation,
)

__all__ = [
    # Chair position types
    "ChairPositionAnalysis",
    "SeatStatistics",
    # Chair position functions
    "analyze_chair_positions",
    # CSV export
    "CSVExporter",
    "export_aggregate_csv",
    "export_hands_csv",
    "export_sessions_csv",
    # JSON export
    "JSONExporter",
    "ResultsEncoder",
    "export_json",
    "load_json",
    # Statistics types
    "ConfidenceInterval",
    "DetailedStatistics",
    "DistributionStats",
    "RiskMetrics",
    # Statistics functions
    "calculate_statistics",
    "calculate_statistics_from_results",
    # Validation types
    "ChiSquareResult",
    "ValidationReport",
    # Validation functions
    "calculate_chi_square",
    "calculate_wilson_confidence_interval",
    "validate_simulation",
]
