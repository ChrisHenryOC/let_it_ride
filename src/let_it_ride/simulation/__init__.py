"""Simulation orchestration.

This module contains session and simulation management:
- Session state management with stop conditions
- Simulation controller for running multiple sessions
- Parallel execution support
- Results aggregation
- Hand records and result data structures
"""

from let_it_ride.simulation.results import (
    HandRecord,
    count_hand_distribution,
    count_hand_distribution_from_ranks,
    get_decision_from_string,
)
from let_it_ride.simulation.session import (
    Session,
    SessionConfig,
    SessionOutcome,
    SessionResult,
    StopReason,
)

__all__ = [
    "HandRecord",
    "Session",
    "SessionConfig",
    "SessionOutcome",
    "SessionResult",
    "StopReason",
    "count_hand_distribution",
    "count_hand_distribution_from_ranks",
    "get_decision_from_string",
]
