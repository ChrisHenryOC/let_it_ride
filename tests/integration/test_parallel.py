"""Integration tests for parallel session execution.

Tests verify:
- Parallel execution produces correct number of sessions
- Same seed produces identical results (parallel vs sequential)
- Different seeds produce different results
- Progress callback invoked correctly
- Worker failure handling
- Auto worker count detection
- Parallel vs sequential equivalence for reproducibility
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from let_it_ride.config.models import (
    BankrollConfig,
    BettingSystemConfig,
    FullConfig,
    SimulationConfig,
    StopConditionsConfig,
    StrategyConfig,
)
from let_it_ride.simulation import (
    SessionOutcome,
    SimulationController,
    SimulationResults,
    StopReason,
)
from let_it_ride.simulation.parallel import (
    ParallelExecutor,
    WorkerResult,
    WorkerTask,
    get_effective_worker_count,
    run_worker_sessions,
)


def create_test_config(
    num_sessions: int = 20,
    hands_per_session: int = 50,
    random_seed: int | None = 42,
    workers: int | str = 2,
) -> FullConfig:
    """Create a test configuration for parallel simulation.

    Args:
        num_sessions: Number of sessions to run.
        hands_per_session: Maximum hands per session.
        random_seed: Optional seed for reproducibility.
        workers: Number of workers or "auto".

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
            starting_amount=500.0,
            base_bet=5.0,
            stop_conditions=StopConditionsConfig(
                win_limit=100.0,
                loss_limit=200.0,
                stop_on_insufficient_funds=True,
            ),
            betting_system=BettingSystemConfig(type="flat"),
        ),
        strategy=StrategyConfig(type="basic"),
    )


class TestParallelExecutorBasics:
    """Basic tests for ParallelExecutor functionality."""

    def test_executor_initializes_with_explicit_workers(self) -> None:
        """Test executor initializes with explicit worker count."""
        executor = ParallelExecutor(num_workers=4)
        assert executor.num_workers == 4

    def test_executor_initializes_with_auto_workers(self) -> None:
        """Test executor initializes with auto worker detection."""
        executor = ParallelExecutor(num_workers="auto")
        expected = os.cpu_count() or 1
        assert executor.num_workers == expected

    def test_executor_handles_zero_workers(self) -> None:
        """Test executor handles zero workers by defaulting to 1."""
        executor = ParallelExecutor(num_workers=0)
        assert executor.num_workers == 1

    def test_executor_handles_negative_workers(self) -> None:
        """Test executor handles negative workers by defaulting to 1."""
        executor = ParallelExecutor(num_workers=-5)
        assert executor.num_workers == 1


class TestGetEffectiveWorkerCount:
    """Tests for get_effective_worker_count function."""

    def test_explicit_worker_count(self) -> None:
        """Test explicit worker count is returned."""
        assert get_effective_worker_count(4) == 4
        assert get_effective_worker_count(1) == 1

    def test_auto_worker_count(self) -> None:
        """Test auto uses CPU count."""
        result = get_effective_worker_count("auto")
        expected = os.cpu_count() or 1
        assert result == expected

    def test_minimum_worker_count(self) -> None:
        """Test minimum worker count is 1."""
        assert get_effective_worker_count(0) == 1
        assert get_effective_worker_count(-1) == 1


class TestParallelExecution:
    """Tests for parallel session execution."""

    def test_parallel_produces_correct_session_count(self) -> None:
        """Test parallel execution produces correct number of sessions."""
        config = create_test_config(num_sessions=20, workers=2)
        controller = SimulationController(config)

        results = controller.run()

        assert isinstance(results, SimulationResults)
        assert len(results.session_results) == 20

    def test_parallel_produces_valid_results(self) -> None:
        """Test parallel execution produces valid session results."""
        config = create_test_config(num_sessions=15, workers=3)
        controller = SimulationController(config)

        results = controller.run()

        for result in results.session_results:
            assert result.hands_played > 0
            assert result.starting_bankroll == 500.0
            assert result.stop_reason in StopReason
            assert result.outcome in SessionOutcome

    def test_parallel_total_hands_aggregated_correctly(self) -> None:
        """Test total_hands is sum of all session hands."""
        config = create_test_config(num_sessions=20, workers=2)
        controller = SimulationController(config)

        results = controller.run()

        expected_total = sum(r.hands_played for r in results.session_results)
        assert results.total_hands == expected_total

    def test_parallel_timing_recorded(self) -> None:
        """Test that start and end times are recorded."""
        config = create_test_config(num_sessions=10, workers=2)
        controller = SimulationController(config)

        results = controller.run()

        assert results.start_time is not None
        assert results.end_time is not None
        assert results.start_time <= results.end_time


class TestParallelVsSequentialEquivalence:
    """Tests verifying parallel and sequential produce identical results.

    These tests are critical for ensuring reproducibility is maintained
    when switching between sequential and parallel execution modes.
    """

    def test_same_seed_produces_identical_results(self) -> None:
        """Test that same seed produces identical results for parallel vs sequential.

        This is the key reproducibility test. With the same seed, parallel
        execution should produce the exact same results as sequential.
        """
        seed = 12345
        num_sessions = 20

        # Sequential execution (workers=1)
        config_seq = create_test_config(
            num_sessions=num_sessions, random_seed=seed, workers=1
        )
        results_seq = SimulationController(config_seq).run()

        # Parallel execution (workers=2)
        config_par = create_test_config(
            num_sessions=num_sessions, random_seed=seed, workers=2
        )
        results_par = SimulationController(config_par).run()

        # Verify same number of results
        assert len(results_seq.session_results) == len(results_par.session_results)

        # Verify each session produces identical results
        for seq, par in zip(
            results_seq.session_results, results_par.session_results, strict=True
        ):
            assert seq.hands_played == par.hands_played
            assert seq.session_profit == par.session_profit
            assert seq.final_bankroll == par.final_bankroll
            assert seq.stop_reason == par.stop_reason
            assert seq.outcome == par.outcome
            assert seq.total_wagered == par.total_wagered

        # Total hands should match
        assert results_seq.total_hands == results_par.total_hands

    def test_reproducibility_with_different_worker_counts(self) -> None:
        """Test reproducibility holds across different worker counts."""
        seed = 77777
        num_sessions = 30

        # Run with 1, 2, and 4 workers
        results_by_workers: dict[int, SimulationResults] = {}

        for workers in [1, 2, 4]:
            config = create_test_config(
                num_sessions=num_sessions, random_seed=seed, workers=workers
            )
            results_by_workers[workers] = SimulationController(config).run()

        # All should produce identical profits
        for workers, results in results_by_workers.items():
            profits = [r.session_profit for r in results.session_results]

            # Compare with workers=1 baseline
            baseline_profits = [
                r.session_profit for r in results_by_workers[1].session_results
            ]
            assert (
                profits == baseline_profits
            ), f"workers={workers} differs from baseline"

    def test_different_seeds_produce_different_results(self) -> None:
        """Test that different seeds produce different results in parallel."""
        config1 = create_test_config(num_sessions=20, random_seed=111, workers=2)
        config2 = create_test_config(num_sessions=20, random_seed=222, workers=2)

        results1 = SimulationController(config1).run()
        results2 = SimulationController(config2).run()

        profits1 = [r.session_profit for r in results1.session_results]
        profits2 = [r.session_profit for r in results2.session_results]

        # Very unlikely to be identical with different seeds
        assert profits1 != profits2


class TestProgressCallback:
    """Tests for progress callback in parallel execution."""

    def test_progress_callback_invoked(self) -> None:
        """Test progress callback is invoked in parallel execution."""
        config = create_test_config(num_sessions=20, workers=2)

        callback_calls: list[tuple[int, int]] = []

        def track_progress(completed: int, total: int) -> None:
            callback_calls.append((completed, total))

        controller = SimulationController(config, progress_callback=track_progress)
        controller.run()

        # In parallel mode, callback is called once at completion
        assert len(callback_calls) >= 1
        # Last call should indicate all sessions complete
        last_call = callback_calls[-1]
        assert last_call[0] == 20
        assert last_call[1] == 20

    def test_no_callback_when_none(self) -> None:
        """Test parallel execution works without callback."""
        config = create_test_config(num_sessions=15, workers=2)
        controller = SimulationController(config, progress_callback=None)

        # Should not raise
        results = controller.run()
        assert len(results.session_results) == 15


class TestWorkerFunction:
    """Tests for the worker function used in parallel execution."""

    def test_worker_processes_sessions_correctly(self) -> None:
        """Test worker function processes assigned sessions."""
        config = create_test_config(num_sessions=10, random_seed=42)

        task = WorkerTask(
            worker_id=0,
            session_ids=[0, 1, 2],
            session_seeds={0: 12345, 1: 23456, 2: 34567},
            config=config,
        )

        result = run_worker_sessions(task)

        assert result.worker_id == 0
        assert result.error is None
        assert len(result.session_results) == 3

        # Verify session IDs are correct
        session_ids = [sr[0] for sr in result.session_results]
        assert session_ids == [0, 1, 2]

    def test_worker_returns_error_on_exception(self) -> None:
        """Test worker returns error information on exception."""
        config = create_test_config(num_sessions=10, random_seed=42)

        # Create task with invalid session seed to trigger error
        task = WorkerTask(
            worker_id=1,
            session_ids=[5, 6],
            session_seeds={5: 12345},  # Missing seed for session 6
            config=config,
        )

        result = run_worker_sessions(task)

        assert result.worker_id == 1
        assert result.error is not None
        assert len(result.session_results) == 0


class TestSessionBatching:
    """Tests for session distribution across workers."""

    def test_sessions_distributed_evenly(self) -> None:
        """Test sessions are distributed evenly across workers."""
        config = create_test_config(num_sessions=100, workers=4)
        executor = ParallelExecutor(num_workers=4)

        # Generate seeds and tasks
        seeds = executor._generate_session_seeds(100, 42)
        tasks = executor._create_worker_tasks(100, seeds, config)

        # Should have 4 tasks (one per worker)
        assert len(tasks) == 4

        # Each worker should have ~25 sessions
        session_counts = [len(t.session_ids) for t in tasks]
        assert sum(session_counts) == 100
        # All workers should have 25 sessions (100 / 4)
        assert session_counts == [25, 25, 25, 25]

    def test_uneven_distribution_handled(self) -> None:
        """Test uneven session counts are handled correctly."""
        config = create_test_config(num_sessions=17, workers=4)
        executor = ParallelExecutor(num_workers=4)

        seeds = executor._generate_session_seeds(17, 42)
        tasks = executor._create_worker_tasks(17, seeds, config)

        # Should have 4 tasks
        assert len(tasks) == 4

        # Sessions should be distributed: 5, 5, 5, 2
        session_counts = [len(t.session_ids) for t in tasks]
        assert sum(session_counts) == 17

    def test_fewer_sessions_than_workers(self) -> None:
        """Test handling when fewer sessions than workers."""
        config = create_test_config(num_sessions=3, workers=8)
        executor = ParallelExecutor(num_workers=8)

        seeds = executor._generate_session_seeds(3, 42)
        tasks = executor._create_worker_tasks(3, seeds, config)

        # Should only create 3 tasks (one per session)
        assert len(tasks) == 3
        for task in tasks:
            assert len(task.session_ids) == 1


class TestResultMerging:
    """Tests for merging results from workers."""

    def test_results_ordered_by_session_id(self) -> None:
        """Test merged results are ordered by session ID."""
        config = create_test_config(num_sessions=20, random_seed=42, workers=4)
        controller = SimulationController(config)

        results = controller.run()

        # Compare with sequential to verify ordering
        config_seq = create_test_config(num_sessions=20, random_seed=42, workers=1)
        results_seq = SimulationController(config_seq).run()

        # Session results should be in same order
        for i, (par, seq) in enumerate(
            zip(results.session_results, results_seq.session_results, strict=True)
        ):
            assert par.session_profit == seq.session_profit, f"Session {i} mismatch"


class TestAutoWorkerDetection:
    """Tests for automatic worker count detection."""

    def test_auto_uses_cpu_count(self) -> None:
        """Test 'auto' uses os.cpu_count()."""
        config = create_test_config(num_sessions=20, workers="auto")

        # With auto workers and >= 10 sessions, should use parallel
        controller = SimulationController(config)
        results = controller.run()

        assert len(results.session_results) == 20

    def test_auto_with_no_cpu_count_defaults_to_one(self) -> None:
        """Test auto defaults to 1 when cpu_count returns None."""
        with patch("os.cpu_count", return_value=None):
            executor = ParallelExecutor(num_workers="auto")
            assert executor.num_workers == 1


class TestSequentialFallback:
    """Tests for fallback to sequential execution."""

    def test_single_worker_uses_sequential(self) -> None:
        """Test workers=1 uses sequential execution."""
        config = create_test_config(num_sessions=20, workers=1)
        controller = SimulationController(config)

        # Track progress calls - sequential calls per session
        callback_calls: list[tuple[int, int]] = []

        def track_progress(completed: int, total: int) -> None:
            callback_calls.append((completed, total))

        controller = SimulationController(config, progress_callback=track_progress)
        results = controller.run()

        # Sequential should call progress for each session
        assert len(callback_calls) == 20
        assert len(results.session_results) == 20

    def test_few_sessions_uses_sequential(self) -> None:
        """Test few sessions fall back to sequential (parallel overhead not worth it)."""
        # Less than _MIN_SESSIONS_FOR_PARALLEL (10)
        config = create_test_config(num_sessions=5, workers=4)
        controller = SimulationController(config)

        callback_calls: list[tuple[int, int]] = []

        def track_progress(completed: int, total: int) -> None:
            callback_calls.append((completed, total))

        controller = SimulationController(config, progress_callback=track_progress)
        results = controller.run()

        # Sequential should call progress for each session
        assert len(callback_calls) == 5
        assert len(results.session_results) == 5


class TestWorkerFailureHandling:
    """Tests for graceful handling of worker failures."""

    def test_worker_failure_raises_runtime_error(self) -> None:
        """Test worker failure is reported via RuntimeError."""
        executor = ParallelExecutor(num_workers=2)

        # Create mock worker results with one failure
        worker_results = [
            WorkerResult(worker_id=0, session_results=[(0, None)], error=None),  # type: ignore[list-item]
            WorkerResult(worker_id=1, session_results=[], error="Test error"),
        ]

        with pytest.raises(RuntimeError, match="Worker failures"):
            executor._merge_results(worker_results, num_sessions=10)

    def test_missing_results_raises_runtime_error(self) -> None:
        """Test missing session results raises RuntimeError."""
        executor = ParallelExecutor(num_workers=2)

        # Create worker results with missing sessions
        worker_results: list[WorkerResult] = [
            WorkerResult(worker_id=0, session_results=[], error=None),
            WorkerResult(worker_id=1, session_results=[], error=None),
        ]

        with pytest.raises(RuntimeError, match="Missing results"):
            executor._merge_results(worker_results, num_sessions=10)


class TestLargeScaleParallel:
    """Tests for larger scale parallel simulations."""

    def test_hundred_sessions_parallel(self) -> None:
        """Test running 100 sessions in parallel."""
        config = create_test_config(num_sessions=100, workers=4)
        controller = SimulationController(config)

        results = controller.run()

        assert len(results.session_results) == 100
        assert results.total_hands <= 100 * 50  # max hands_per_session

    def test_many_workers_with_many_sessions(self) -> None:
        """Test with many workers and many sessions."""
        config = create_test_config(num_sessions=200, workers=8)
        controller = SimulationController(config)

        results = controller.run()

        assert len(results.session_results) == 200

        # Verify results are valid
        for result in results.session_results:
            assert result.hands_played > 0
            assert result.outcome in SessionOutcome


class TestDeterministicSeeding:
    """Tests for deterministic RNG seeding in parallel execution."""

    def test_seed_generation_is_deterministic(self) -> None:
        """Test session seeds are generated deterministically."""
        executor = ParallelExecutor(num_workers=4)

        seeds1 = executor._generate_session_seeds(100, base_seed=42)
        seeds2 = executor._generate_session_seeds(100, base_seed=42)

        assert seeds1 == seeds2

    def test_different_base_seeds_produce_different_session_seeds(self) -> None:
        """Test different base seeds produce different session seeds."""
        executor = ParallelExecutor(num_workers=4)

        seeds1 = executor._generate_session_seeds(100, base_seed=42)
        seeds2 = executor._generate_session_seeds(100, base_seed=43)

        assert seeds1 != seeds2

    def test_no_seed_produces_different_results_each_run(self) -> None:
        """Test None seed produces different results each run."""
        executor = ParallelExecutor(num_workers=4)

        seeds1 = executor._generate_session_seeds(100, base_seed=None)
        seeds2 = executor._generate_session_seeds(100, base_seed=None)

        # Very unlikely to be identical without a fixed seed
        assert seeds1 != seeds2
