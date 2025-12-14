"""Visualization components for Let It Ride analytics.

This module provides chart generation for simulation results:
- Session outcome histograms
- Bankroll trajectory plots
- Risk of ruin curves
"""

from let_it_ride.analytics.visualizations.histogram import (
    HistogramConfig,
    plot_session_histogram,
    save_histogram,
)
from let_it_ride.analytics.visualizations.risk_curves import (
    RiskCurveConfig,
    plot_risk_curves,
    save_risk_curves,
)
from let_it_ride.analytics.visualizations.trajectory import (
    TrajectoryConfig,
    plot_bankroll_trajectories,
    save_trajectory_chart,
)

__all__ = [
    "HistogramConfig",
    "RiskCurveConfig",
    "TrajectoryConfig",
    "plot_bankroll_trajectories",
    "plot_risk_curves",
    "plot_session_histogram",
    "save_histogram",
    "save_risk_curves",
    "save_trajectory_chart",
]
