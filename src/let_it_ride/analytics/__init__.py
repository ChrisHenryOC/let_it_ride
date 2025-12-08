"""Statistics and reporting.

This module contains analytics and export functionality:
- Core statistics calculator
- Statistical validation
- Strategy comparison analytics
- Export formats (CSV, JSON, HTML)
- Visualizations (histograms, trajectories)
"""

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
