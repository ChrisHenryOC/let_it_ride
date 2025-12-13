"""Visualization components for Let It Ride analytics.

This module provides chart generation for simulation results:
- Session outcome histograms
- Bankroll trajectory plots (future)
- Hand frequency distributions (future)
"""

from let_it_ride.analytics.visualizations.histogram import (
    HistogramConfig,
    plot_session_histogram,
    save_histogram,
)

__all__ = [
    "HistogramConfig",
    "plot_session_histogram",
    "save_histogram",
]
