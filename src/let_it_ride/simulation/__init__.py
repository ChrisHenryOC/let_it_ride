"""Simulation orchestration.

This module contains session and simulation management:
- Session state management with stop conditions
- Simulation controller for running multiple sessions
- Parallel execution support
- Results aggregation
"""

from let_it_ride.simulation.session import (
    Session,
    SessionConfig,
    SessionOutcome,
    SessionResult,
    StopReason,
)

__all__ = [
    "Session",
    "SessionConfig",
    "SessionOutcome",
    "SessionResult",
    "StopReason",
]
