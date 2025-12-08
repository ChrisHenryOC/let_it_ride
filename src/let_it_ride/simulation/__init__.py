"""Simulation orchestration.

This module contains session and simulation management:
- Session state management with stop conditions
- Table session for multi-player management
- Simulation controller for running multiple sessions
- Parallel execution support
- Results aggregation
- Hand records and result data structures
"""

from let_it_ride.simulation.aggregation import (
    AggregateStatistics,
    aggregate_results,
    aggregate_with_hand_frequencies,
    merge_aggregates,
)
from let_it_ride.simulation.controller import (
    ProgressCallback,
    SimulationController,
    SimulationResults,
    create_betting_system,
    create_strategy,
)
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
    calculate_new_streak,
)
from let_it_ride.simulation.table_session import (
    SeatSessionResult,
    TableSession,
    TableSessionConfig,
    TableSessionResult,
)

__all__ = [
    "AggregateStatistics",
    "HandRecord",
    "ProgressCallback",
    "SeatSessionResult",
    "Session",
    "SessionConfig",
    "SessionOutcome",
    "SessionResult",
    "SimulationController",
    "SimulationResults",
    "StopReason",
    "TableSession",
    "TableSessionConfig",
    "TableSessionResult",
    "aggregate_results",
    "aggregate_with_hand_frequencies",
    "calculate_new_streak",
    "count_hand_distribution",
    "count_hand_distribution_from_game_results",
    "count_hand_distribution_from_ranks",
    "count_hand_distribution_from_records",
    "create_betting_system",
    "create_strategy",
    "get_decision_from_string",
    "merge_aggregates",
]
