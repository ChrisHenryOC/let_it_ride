"""Parallel session execution for Let It Ride simulation.

This module provides parallel execution support using multiprocessing:
- ParallelExecutor: Manages worker pools for concurrent session execution
- Worker function: Top-level function for pickling support

Key design decisions:
- Pre-generate ALL session seeds before parallel execution for determinism
- Each worker creates fresh Strategy, Paytables, BettingSystem (not shared)
- Progress aggregation via multiprocessing Queue
"""

from __future__ import annotations

import os
import random
from collections.abc import Callable
from dataclasses import dataclass
from math import ceil
from multiprocessing import Pool
from typing import TYPE_CHECKING, Literal

from let_it_ride.config.paytables import (
    BonusPaytable,
    MainGamePaytable,
    bonus_paytable_a,
    bonus_paytable_b,
    bonus_paytable_c,
    standard_main_paytable,
)
from let_it_ride.core.deck import Deck
from let_it_ride.core.game_engine import GameEngine
from let_it_ride.simulation.controller import (
    create_betting_system,
    create_strategy,
)
from let_it_ride.simulation.session import Session, SessionConfig, SessionResult

if TYPE_CHECKING:
    from let_it_ride.bankroll import BettingSystem
    from let_it_ride.config.models import FullConfig
    from let_it_ride.strategy import Strategy


# Type alias for progress callback
ProgressCallback = Callable[[int, int], None]


@dataclass(frozen=True, slots=True)
class WorkerTask:
    """Task specification for a single worker.

    Attributes:
        worker_id: Unique identifier for this worker.
        session_ids: List of session IDs this worker will process.
        session_seeds: Mapping of session_id to RNG seed.
        config: Full simulation configuration (serializable).
    """

    worker_id: int
    session_ids: list[int]
    session_seeds: dict[int, int]
    config: FullConfig


@dataclass(frozen=True, slots=True)
class WorkerResult:
    """Result from a single worker.

    Attributes:
        worker_id: Identifier of the worker that produced this result.
        session_results: List of (session_id, SessionResult) tuples.
        error: Error message if worker failed, None otherwise.
    """

    worker_id: int
    session_results: list[tuple[int, SessionResult]]
    error: str | None = None


def _get_main_paytable(config: FullConfig) -> MainGamePaytable:
    """Get the main game paytable from configuration.

    Args:
        config: The full simulation configuration.

    Returns:
        The appropriate MainGamePaytable instance.

    Raises:
        NotImplementedError: If the paytable type is not yet supported.
    """
    paytable_type = config.paytables.main_game.type
    if paytable_type == "standard":
        return standard_main_paytable()
    raise NotImplementedError(
        f"Main paytable type '{paytable_type}' is not yet implemented. "
        "Only 'standard' is currently supported."
    )


def _get_bonus_paytable(config: FullConfig) -> BonusPaytable | None:
    """Get the bonus paytable from configuration.

    Args:
        config: The full simulation configuration.

    Returns:
        The appropriate BonusPaytable instance, or None if bonus is disabled.

    Raises:
        ValueError: If the bonus paytable type is unknown.
    """
    if not config.bonus_strategy.enabled:
        return None

    paytable_type = config.paytables.bonus.type
    if paytable_type == "paytable_a":
        return bonus_paytable_a()
    if paytable_type == "paytable_b":
        return bonus_paytable_b()
    if paytable_type == "paytable_c":
        return bonus_paytable_c()
    raise ValueError(
        f"Unknown bonus paytable type: '{paytable_type}'. "
        "Supported types: 'paytable_a', 'paytable_b', 'paytable_c'."
    )


def _calculate_bonus_bet(config: FullConfig) -> float:
    """Calculate the bonus bet amount from configuration.

    Args:
        config: The full simulation configuration.

    Returns:
        The bonus bet amount (0.0 if disabled).
    """
    if not config.bonus_strategy.enabled:
        return 0.0

    if config.bonus_strategy.always is not None:
        return config.bonus_strategy.always.amount
    if config.bonus_strategy.static is not None:
        if config.bonus_strategy.static.amount is not None:
            return config.bonus_strategy.static.amount
        if config.bonus_strategy.static.ratio is not None:
            return config.bankroll.base_bet * config.bonus_strategy.static.ratio

    return 0.0


def _create_session_config(config: FullConfig, bonus_bet: float) -> SessionConfig:
    """Create a SessionConfig from FullConfig.

    Args:
        config: The full simulation configuration.
        bonus_bet: The bonus bet amount.

    Returns:
        A SessionConfig instance.
    """
    bankroll_config = config.bankroll
    stop_conditions = bankroll_config.stop_conditions

    return SessionConfig(
        starting_bankroll=bankroll_config.starting_amount,
        base_bet=bankroll_config.base_bet,
        win_limit=stop_conditions.win_limit,
        loss_limit=stop_conditions.loss_limit,
        max_hands=config.simulation.hands_per_session,
        stop_on_insufficient_funds=stop_conditions.stop_on_insufficient_funds,
        bonus_bet=bonus_bet,
    )


def _run_single_session(
    seed: int,
    config: FullConfig,
    strategy: Strategy,
    main_paytable: MainGamePaytable,
    bonus_paytable: BonusPaytable | None,
    betting_system_factory: Callable[[], BettingSystem],
    session_config: SessionConfig,
) -> SessionResult:
    """Run a single session with the given seed.

    Args:
        seed: RNG seed for this session.
        config: Full simulation configuration.
        strategy: Strategy instance to use.
        main_paytable: Main game paytable.
        bonus_paytable: Bonus paytable (or None).
        betting_system_factory: Factory to create fresh betting system.
        session_config: Session configuration.

    Returns:
        The SessionResult from running the session.
    """
    session_rng = random.Random(seed)
    deck = Deck()

    engine = GameEngine(
        deck=deck,
        strategy=strategy,
        main_paytable=main_paytable,
        bonus_paytable=bonus_paytable,
        rng=session_rng,
        dealer_config=config.dealer,
    )

    betting_system = betting_system_factory()
    session = Session(session_config, engine, betting_system)

    return session.run_to_completion()


def run_worker_sessions(task: WorkerTask) -> WorkerResult:
    """Execute sessions assigned to a worker.

    This is a top-level function (not a method) to support pickling
    for multiprocessing.

    Args:
        task: WorkerTask containing session IDs, seeds, and config.

    Returns:
        WorkerResult containing session results or error information.
    """
    try:
        # Create components fresh in this worker (not shared across processes)
        strategy = create_strategy(task.config.strategy)
        main_paytable = _get_main_paytable(task.config)
        bonus_paytable = _get_bonus_paytable(task.config)
        bonus_bet = _calculate_bonus_bet(task.config)
        session_config = _create_session_config(task.config, bonus_bet)

        def betting_system_factory() -> BettingSystem:
            return create_betting_system(task.config.bankroll)

        results: list[tuple[int, SessionResult]] = []

        for session_id in task.session_ids:
            seed = task.session_seeds[session_id]
            result = _run_single_session(
                seed=seed,
                config=task.config,
                strategy=strategy,
                main_paytable=main_paytable,
                bonus_paytable=bonus_paytable,
                betting_system_factory=betting_system_factory,
                session_config=session_config,
            )
            results.append((session_id, result))

        return WorkerResult(
            worker_id=task.worker_id,
            session_results=results,
            error=None,
        )

    except Exception as e:
        return WorkerResult(
            worker_id=task.worker_id,
            session_results=[],
            error=str(e),
        )


class ParallelExecutor:
    """Manages parallel execution of simulation sessions.

    Uses multiprocessing to distribute sessions across multiple workers
    while maintaining reproducibility through deterministic RNG seeding.
    """

    __slots__ = ("_num_workers",)

    def __init__(self, num_workers: int | Literal["auto"]) -> None:
        """Initialize the parallel executor.

        Args:
            num_workers: Number of worker processes, or "auto" to use CPU count.
        """
        if num_workers == "auto":
            self._num_workers = os.cpu_count() or 1
        else:
            self._num_workers = max(1, num_workers)

    @property
    def num_workers(self) -> int:
        """Return the number of worker processes."""
        return self._num_workers

    def _generate_session_seeds(
        self, num_sessions: int, base_seed: int | None
    ) -> dict[int, int]:
        """Pre-generate deterministic seeds for all sessions.

        Args:
            num_sessions: Total number of sessions.
            base_seed: Base seed for the master RNG, or None for random.

        Returns:
            Dictionary mapping session_id to seed.
        """
        if base_seed is not None:
            master_rng = random.Random(base_seed)
        else:
            master_rng = random.Random()

        return {
            session_id: master_rng.randint(0, 2**31 - 1)
            for session_id in range(num_sessions)
        }

    def _create_worker_tasks(
        self,
        num_sessions: int,
        session_seeds: dict[int, int],
        config: FullConfig,
    ) -> list[WorkerTask]:
        """Create task specifications for each worker.

        Distributes sessions evenly among workers.

        Args:
            num_sessions: Total number of sessions.
            session_seeds: Pre-generated seeds for all sessions.
            config: Full simulation configuration.

        Returns:
            List of WorkerTask objects.
        """
        batch_size = ceil(num_sessions / self._num_workers)
        tasks: list[WorkerTask] = []

        for worker_id in range(self._num_workers):
            start_idx = worker_id * batch_size
            end_idx = min(start_idx + batch_size, num_sessions)

            if start_idx >= num_sessions:
                # No more sessions to distribute
                break

            session_ids = list(range(start_idx, end_idx))
            worker_seeds = {sid: session_seeds[sid] for sid in session_ids}

            tasks.append(
                WorkerTask(
                    worker_id=worker_id,
                    session_ids=session_ids,
                    session_seeds=worker_seeds,
                    config=config,
                )
            )

        return tasks

    def _merge_results(
        self, worker_results: list[WorkerResult], num_sessions: int
    ) -> list[SessionResult]:
        """Merge and order results from all workers.

        Args:
            worker_results: Results from all workers.
            num_sessions: Expected number of sessions.

        Returns:
            List of SessionResult objects ordered by session ID.

        Raises:
            RuntimeError: If any worker failed or results are missing.
        """
        # Check for worker failures
        failed_workers = [wr for wr in worker_results if wr.error is not None]
        if failed_workers:
            errors = [f"Worker {wr.worker_id}: {wr.error}" for wr in failed_workers]
            raise RuntimeError(f"Worker failures: {'; '.join(errors)}")

        # Collect all results into a dictionary keyed by session_id
        results_by_id: dict[int, SessionResult] = {}
        for worker_result in worker_results:
            for session_id, session_result in worker_result.session_results:
                results_by_id[session_id] = session_result

        # Verify we have all expected results
        if len(results_by_id) != num_sessions:
            missing = set(range(num_sessions)) - set(results_by_id.keys())
            raise RuntimeError(
                f"Missing results for {len(missing)} sessions: {sorted(missing)[:10]}..."
            )

        # Return results ordered by session_id
        return [results_by_id[i] for i in range(num_sessions)]

    def run_sessions(
        self,
        config: FullConfig,
        progress_callback: ProgressCallback | None = None,
    ) -> list[SessionResult]:
        """Execute sessions in parallel.

        Args:
            config: Full simulation configuration.
            progress_callback: Optional callback for progress reporting.

        Returns:
            List of SessionResult objects in session order.

        Raises:
            RuntimeError: If any worker fails.
        """
        num_sessions = config.simulation.num_sessions
        base_seed = config.simulation.random_seed

        # Pre-generate all session seeds for determinism
        session_seeds = self._generate_session_seeds(num_sessions, base_seed)

        # Create worker tasks
        tasks = self._create_worker_tasks(num_sessions, session_seeds, config)

        # Execute in parallel
        with Pool(processes=len(tasks)) as pool:
            worker_results = pool.map(run_worker_sessions, tasks)

        # Report progress (all sessions complete)
        if progress_callback is not None:
            progress_callback(num_sessions, num_sessions)

        # Merge and return ordered results
        return self._merge_results(worker_results, num_sessions)


def get_effective_worker_count(workers: int | Literal["auto"]) -> int:
    """Get the effective worker count from configuration.

    Args:
        workers: Number of workers or "auto".

    Returns:
        The actual number of workers to use.
    """
    if workers == "auto":
        return os.cpu_count() or 1
    return max(1, workers)
