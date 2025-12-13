"""CLI package for Let It Ride Strategy Simulator.

This package provides command-line interface components including
output formatting and display utilities.
"""

from let_it_ride.cli.app import _load_config_with_errors, app
from let_it_ride.cli.formatters import OutputFormatter

__all__ = ["OutputFormatter", "_load_config_with_errors", "app"]
