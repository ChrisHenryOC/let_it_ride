"""Simulation orchestration.

This module contains session and simulation management:
- Session state management with stop conditions
- Table session for multi-player management
- Simulation controller for running multiple sessions
- Parallel execution support
- Results aggregation
- Hand records and result data structures
"""

from let_it_ride.simulation.results import (
    HandRecord,
    count_hand_distribution,
    count_hand_distribution_from_game_results,
    count_hand_distribution_from_ranks,
    count_hand_distribution_from_records,
    get_decision_from_string,
)
from let_it_ride.simulation.session import (
    Session,
    SessionConfig,
    SessionOutcome,
    SessionResult,
    StopReason,
)
from let_it_ride.simulation.table_session import (
    SeatSessionResult,
    TableSession,
    TableSessionConfig,
    TableSessionResult,
)

__all__ = [
    "HandRecord",
    "SeatSessionResult",
    "Session",
    "SessionConfig",
    "SessionOutcome",
    "SessionResult",
    "StopReason",
    "TableSession",
    "TableSessionConfig",
    "TableSessionResult",
    "count_hand_distribution",
    "count_hand_distribution_from_game_results",
    "count_hand_distribution_from_ranks",
    "count_hand_distribution_from_records",
    "get_decision_from_string",
]
