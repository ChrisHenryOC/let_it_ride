"""Visualization components for Let It Ride analytics.

This module provides chart generation for simulation results:
- Session outcome histograms
- Bankroll trajectory plots
- Hand frequency distributions (future)
"""

from let_it_ride.analytics.visualizations.histogram import (
    HistogramConfig,
    plot_session_histogram,
    save_histogram,
)
from let_it_ride.analytics.visualizations.trajectory import (
    TrajectoryConfig,
    plot_bankroll_trajectories,
    save_trajectory_chart,
)

__all__ = [
    "HistogramConfig",
    "TrajectoryConfig",
    "plot_bankroll_trajectories",
    "plot_session_histogram",
    "save_histogram",
    "save_trajectory_chart",
]
