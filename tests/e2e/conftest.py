"""Shared fixtures and helpers for E2E tests.

This module provides common utilities used across E2E test files:
- Configuration factory functions
- Reusable hand callback factories
- Common test constants
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from collections.abc import Callable

from let_it_ride.config.models import (
    BankrollConfig,
    BettingSystemConfig,
    FullConfig,
    SimulationConfig,
    StopConditionsConfig,
    StrategyConfig,
)

if TYPE_CHECKING:
    from let_it_ride.core.game_engine import GameHandResult

# =============================================================================
# Win Rate Assertion Constants
# =============================================================================
# These bounds are intentionally wide to account for variance in simulation results.
# The actual win rate depends heavily on stop conditions (win/loss limits) and strategy.
# With basic strategy and typical stop conditions, session win rates typically fall
# in the 30-50% range, but we use wider bounds for test stability.

# Minimum expected session win rate (20%) - accounts for unlucky streaks
MIN_SESSION_WIN_RATE = 0.20

# Maximum expected session win rate (60%) - accounts for lucky streaks
MAX_SESSION_WIN_RATE = 0.60

# Extended bounds for aggregate tests with larger variance
MIN_AGGREGATE_WIN_RATE = 0.15
MAX_AGGREGATE_WIN_RATE = 0.65


# =============================================================================
# Configuration Factory Functions
# =============================================================================


def create_e2e_config(
    num_sessions: int = 1000,
    hands_per_session: int = 100,
    random_seed: int | None = 42,
    workers: int | Literal["auto"] = 1,
    starting_amount: float = 500.0,
    base_bet: float = 5.0,
    win_limit: float = 250.0,
    loss_limit: float = 200.0,
) -> FullConfig:
    """Create a configuration for E2E testing.

    This is the primary configuration factory for E2E tests. It creates a
    standard configuration suitable for testing full simulation pipelines.

    Args:
        num_sessions: Number of sessions to run.
        hands_per_session: Maximum hands per session.
        random_seed: Optional seed for reproducibility. Use None for random.
        workers: Number of workers or "auto" for automatic detection.
        starting_amount: Starting bankroll amount.
        base_bet: Base bet amount per hand.
        win_limit: Stop session when profit reaches this amount.
        loss_limit: Stop session when loss reaches this amount.

    Returns:
        A FullConfig instance ready for simulation.
    """
    return FullConfig(
        simulation=SimulationConfig(
            num_sessions=num_sessions,
            hands_per_session=hands_per_session,
            random_seed=random_seed,
            workers=workers,
        ),
        bankroll=BankrollConfig(
            starting_amount=starting_amount,
            base_bet=base_bet,
            stop_conditions=StopConditionsConfig(
                win_limit=win_limit,
                loss_limit=loss_limit,
                stop_on_insufficient_funds=True,
            ),
            betting_system=BettingSystemConfig(type="flat"),
        ),
        strategy=StrategyConfig(type="basic"),
    )


def create_output_test_config(
    num_sessions: int = 100,
    hands_per_session: int = 50,
    random_seed: int = 42,
    workers: int = 1,
) -> FullConfig:
    """Create a configuration for output format testing.

    This creates a smaller configuration suitable for testing CSV/JSON
    export functionality without long simulation times.

    Args:
        num_sessions: Number of sessions to run.
        hands_per_session: Maximum hands per session.
        random_seed: Seed for reproducibility.
        workers: Number of workers.

    Returns:
        A FullConfig instance ready for simulation.
    """
    return create_e2e_config(
        num_sessions=num_sessions,
        hands_per_session=hands_per_session,
        random_seed=random_seed,
        workers=workers,
        win_limit=200.0,
        loss_limit=150.0,
    )


def create_performance_config(
    num_sessions: int,
    hands_per_session: int,
    workers: int | Literal["auto"] = 4,
    random_seed: int = 42,
) -> FullConfig:
    """Create configuration for performance testing.

    This creates a configuration suitable for throughput and memory benchmarks.
    Uses 4 workers by default for parallel performance testing.

    Args:
        num_sessions: Number of sessions.
        hands_per_session: Maximum hands per session.
        workers: Number of parallel workers. Use "auto" for automatic
            detection based on available CPU cores.
        random_seed: Seed for reproducibility.

    Returns:
        FullConfig instance.
    """
    return create_e2e_config(
        num_sessions=num_sessions,
        hands_per_session=hands_per_session,
        random_seed=random_seed,
        workers=workers,
    )


# =============================================================================
# Hand Callback Factories
# =============================================================================


def create_hand_frequency_tracker() -> (
    tuple[dict[str, int], Callable[[int, int, GameHandResult], None]]
):
    """Create a hand frequency tracking callback and its data store.

    This factory creates a callback function that tracks hand rank frequencies
    during simulation. Use this for chi-square testing and statistical validation.

    Returns:
        A tuple of (frequencies_dict, callback_function) where:
        - frequencies_dict: Dictionary that will be populated with hand rank
            counts as {rank_name: count}
        - callback_function: The callback to pass to SimulationController
    """
    hand_frequencies: dict[str, int] = {}

    def track_hands(
        session_id: int,  # noqa: ARG001
        hand_id: int,  # noqa: ARG001
        result: GameHandResult,
    ) -> None:
        """Track hand frequencies during simulation."""
        hand_rank = result.final_hand_rank.name.lower()
        hand_frequencies[hand_rank] = hand_frequencies.get(hand_rank, 0) + 1

    return hand_frequencies, track_hands


def create_hand_record_collector() -> (
    tuple[list[dict[str, Any]], Callable[[int, int, GameHandResult], None]]
):
    """Create a hand record collection callback and its data store.

    This factory creates a callback function that collects detailed hand
    records during simulation. Use this for output format testing.

    Returns:
        A tuple of (records_list, callback_function) where:
        - records_list: List that will be populated with hand record dicts
        - callback_function: The callback to pass to SimulationController
    """
    hand_records: list[dict[str, Any]] = []

    def collect_hands(
        session_id: int,
        hand_id: int,  # noqa: ARG001
        result: GameHandResult,
    ) -> None:
        """Collect hand records during simulation."""
        player_cards = " ".join(str(c) for c in result.player_cards)
        community_cards = " ".join(str(c) for c in result.community_cards)

        final_rank = result.final_hand_rank.name.lower()
        bonus_rank = (
            result.bonus_hand_rank.name.lower()
            if result.bonus_hand_rank is not None
            else None
        )

        hand_records.append(
            {
                "hand_id": len(hand_records),
                "session_id": session_id,
                "cards_player": player_cards,
                "cards_community": community_cards,
                "decision_bet1": result.decision_bet1.value,
                "decision_bet2": result.decision_bet2.value,
                "final_hand_rank": final_rank,
                "base_bet": result.base_bet,
                "bets_at_risk": result.bets_at_risk,
                "main_payout": result.main_payout,
                "bonus_bet": result.bonus_bet,
                "bonus_hand_rank": bonus_rank,
                "bonus_payout": result.bonus_payout,
            }
        )

    return hand_records, collect_hands
