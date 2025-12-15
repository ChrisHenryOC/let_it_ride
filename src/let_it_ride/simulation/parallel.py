"""Parallel session execution for Let It Ride simulation.

This module provides parallel execution support using multiprocessing:
- ParallelExecutor: Manages worker pools for concurrent session execution
- Worker function: Top-level function for pickling support

Key design decisions:
- Pre-generate ALL session seeds before parallel execution for determinism
- Each worker creates fresh Strategy, Paytables, BettingSystem (not shared)
- Progress reported at completion (per-session progress not available in parallel mode)
"""

from __future__ import annotations

import os
import random
from collections.abc import Callable
from dataclasses import dataclass
from math import ceil
from multiprocessing import Pool
from typing import TYPE_CHECKING, Literal

from let_it_ride.core.deck import Deck
from let_it_ride.core.game_engine import GameEngine
from let_it_ride.core.table import Table
from let_it_ride.simulation.controller import (
    create_betting_system,
    create_strategy,
)
from let_it_ride.simulation.rng import RNGManager
from let_it_ride.simulation.session import Session, SessionConfig, SessionResult
from let_it_ride.simulation.table_session import TableSession
from let_it_ride.simulation.utils import (
    calculate_bonus_bet,
    create_session_config,
    create_table_session_config,
    get_bonus_paytable,
    get_main_paytable,
)
from let_it_ride.strategy.bonus import BonusStrategy, create_bonus_strategy

if TYPE_CHECKING:
    from let_it_ride.bankroll import BettingSystem
    from let_it_ride.config.models import FullConfig
    from let_it_ride.config.paytables import BonusPaytable, MainGamePaytable
    from let_it_ride.strategy import Strategy


# Type alias for progress callback
ProgressCallback = Callable[[int, int], None]

# Maximum number of workers to prevent resource exhaustion
MAX_WORKERS = 64


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


def _run_single_session(
    seed: int,
    config: FullConfig,
    strategy: Strategy,
    main_paytable: MainGamePaytable,
    bonus_paytable: BonusPaytable | None,
    betting_system_factory: Callable[[], BettingSystem],
    bonus_strategy_factory: Callable[[], BonusStrategy],
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
        bonus_strategy_factory: Factory to create fresh bonus strategy.
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
    bonus_strategy = bonus_strategy_factory()
    session = Session(
        session_config, engine, betting_system, bonus_strategy=bonus_strategy
    )

    return session.run_to_completion()


def _run_single_table_session(
    seed: int,
    config: FullConfig,
    strategy: Strategy,
    main_paytable: MainGamePaytable,
    bonus_paytable: BonusPaytable | None,
    betting_system_factory: Callable[[], BettingSystem],
) -> list[SessionResult]:
    """Run a single multi-seat table session with the given seed.

    Args:
        seed: RNG seed for this session.
        config: Full simulation configuration.
        strategy: Strategy instance to use.
        main_paytable: Main game paytable.
        bonus_paytable: Bonus paytable (or None).
        betting_system_factory: Factory to create fresh betting system.

    Returns:
        List of SessionResult, one per seat.
    """
    session_rng = random.Random(seed)
    deck = Deck()
    bonus_bet = calculate_bonus_bet(config)
    table_session_config = create_table_session_config(config, bonus_bet)

    table = Table(
        deck=deck,
        strategy=strategy,
        main_paytable=main_paytable,
        bonus_paytable=bonus_paytable,
        rng=session_rng,
        table_config=config.table,
        dealer_config=config.dealer,
    )

    betting_system = betting_system_factory()
    table_session = TableSession(
        config=table_session_config,
        table=table,
        betting_system=betting_system,
    )

    table_result = table_session.run_to_completion()
    return [seat_result.session_result for seat_result in table_result.seat_results]


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
        main_paytable = get_main_paytable(task.config)
        bonus_paytable = get_bonus_paytable(task.config)
        bonus_bet = calculate_bonus_bet(task.config)
        session_config = create_session_config(task.config, bonus_bet)

        def betting_system_factory() -> BettingSystem:
            return create_betting_system(task.config.bankroll)

        def bonus_strategy_factory() -> BonusStrategy:
            return create_bonus_strategy(task.config.bonus_strategy)

        results: list[tuple[int, SessionResult]] = []

        # Check if we should use multi-seat table sessions
        num_seats = task.config.table.num_seats
        use_table_session = num_seats > 1

        for session_id in task.session_ids:
            seed = task.session_seeds[session_id]

            if use_table_session:
                # Multi-seat: run TableSession and collect per-seat results
                seat_results = _run_single_table_session(
                    seed=seed,
                    config=task.config,
                    strategy=strategy,
                    main_paytable=main_paytable,
                    bonus_paytable=bonus_paytable,
                    betting_system_factory=betting_system_factory,
                )
                # Add each seat's result with a unique ID
                for seat_idx, seat_result in enumerate(seat_results):
                    # Use composite ID: session_id * num_seats + seat_idx
                    composite_id = session_id * num_seats + seat_idx
                    results.append((composite_id, seat_result))
            else:
                # Single-seat: use Session for efficiency
                result = _run_single_session(
                    seed=seed,
                    config=task.config,
                    strategy=strategy,
                    main_paytable=main_paytable,
                    bonus_paytable=bonus_paytable,
                    betting_system_factory=betting_system_factory,
                    bonus_strategy_factory=bonus_strategy_factory,
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
            error=f"{type(e).__name__}: {e}",
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
                The value is bounded between 1 and MAX_WORKERS to prevent
                resource exhaustion.
        """
        self._num_workers = get_effective_worker_count(num_workers)

    @property
    def num_workers(self) -> int:
        """Return the number of worker processes."""
        return self._num_workers

    def _generate_session_seeds(
        self, num_sessions: int, base_seed: int | None
    ) -> dict[int, int]:
        """Pre-generate deterministic seeds for all sessions.

        Uses RNGManager for centralized seed management.

        Args:
            num_sessions: Total number of sessions.
            base_seed: Base seed for the master RNG, or None for random.

        Returns:
            Dictionary mapping session_id to seed.
        """
        rng_manager = RNGManager(base_seed=base_seed)
        return rng_manager.create_session_seeds(num_sessions)

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
        self,
        worker_results: list[WorkerResult],
        num_sessions: int,
        num_seats: int = 1,
    ) -> list[SessionResult]:
        """Merge and order results from all workers.

        Uses a pre-allocated list for better memory efficiency than dict-based
        collection, avoiding hash table overhead.

        Args:
            worker_results: Results from all workers.
            num_sessions: Expected number of sessions.
            num_seats: Number of seats per table (for multi-seat mode).

        Returns:
            List of SessionResult objects ordered by result ID.

        Raises:
            RuntimeError: If any worker failed or results are missing.
        """
        # Check for worker failures first
        failed_workers = [wr for wr in worker_results if wr.error is not None]
        if failed_workers:
            errors = [f"Worker {wr.worker_id}: {wr.error}" for wr in failed_workers]
            raise RuntimeError(f"Worker failures: {'; '.join(errors)}")

        # For multi-seat, we have num_sessions * num_seats results
        expected_results = num_sessions * num_seats

        # Pre-allocate result list for O(1) direct assignment
        results: list[SessionResult | None] = [None] * expected_results
        for worker_result in worker_results:
            for result_id, session_result in worker_result.session_results:
                results[result_id] = session_result

        # Verify we have all expected results
        missing = [i for i, r in enumerate(results) if r is None]
        if missing:
            raise RuntimeError(
                f"Missing results for {len(missing)} sessions: {missing[:10]}..."
            )

        # Type is now list[SessionResult] since we verified no None values
        return results  # type: ignore[return-value]

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
            For multi-seat tables, returns num_sessions * num_seats results.

        Raises:
            RuntimeError: If any worker fails.
        """
        num_sessions = config.simulation.num_sessions
        num_seats = config.table.num_seats
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
        return self._merge_results(worker_results, num_sessions, num_seats)


def get_effective_worker_count(workers: int | Literal["auto"]) -> int:
    """Get the effective worker count from configuration.

    The value is bounded between 1 and MAX_WORKERS to prevent resource
    exhaustion from misconfiguration.

    Args:
        workers: Number of workers or "auto".

    Returns:
        The actual number of workers to use (1 <= result <= MAX_WORKERS).
    """
    if workers == "auto":
        return min(os.cpu_count() or 1, MAX_WORKERS)
    return min(max(1, workers), MAX_WORKERS)
