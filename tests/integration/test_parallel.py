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
from typing import Literal
from unittest.mock import patch

import pytest

from let_it_ride.config.models import (
    AlwaysBonusConfig,
    BankrollConfig,
    BettingSystemConfig,
    BonusStrategyConfig,
    FullConfig,
    SimulationConfig,
    StopConditionsConfig,
    StrategyConfig,
    TableConfig,
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
    workers: int | Literal["auto"] = 2,
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


class TestBoundaryConditions:
    """Tests for boundary conditions at the parallel/sequential threshold."""

    def test_boundary_nine_sessions_uses_sequential(self) -> None:
        """Test exactly 9 sessions falls back to sequential.

        The boundary is _MIN_SESSIONS_FOR_PARALLEL = 10, so 9 sessions
        should use sequential execution (progress callback per session).
        """
        config = create_test_config(num_sessions=9, workers=4)
        callback_calls: list[tuple[int, int]] = []

        def track(completed: int, total: int) -> None:
            callback_calls.append((completed, total))

        controller = SimulationController(config, progress_callback=track)
        controller.run()

        # Sequential: per-session callbacks = 9 calls
        assert len(callback_calls) == 9

    def test_boundary_ten_sessions_uses_parallel(self) -> None:
        """Test exactly 10 sessions uses parallel execution.

        The boundary is _MIN_SESSIONS_FOR_PARALLEL = 10, so 10 sessions
        should use parallel execution (single progress callback at end).
        """
        config = create_test_config(num_sessions=10, workers=4)
        callback_calls: list[tuple[int, int]] = []

        def track(completed: int, total: int) -> None:
            callback_calls.append((completed, total))

        controller = SimulationController(config, progress_callback=track)
        controller.run()

        # Parallel: single callback at completion
        assert len(callback_calls) == 1
        assert callback_calls[0] == (10, 10)


class TestMultipleWorkerFailures:
    """Tests for handling multiple simultaneous worker failures."""

    def test_multiple_worker_failures_reported(self) -> None:
        """Test error message contains all failed worker errors."""
        executor = ParallelExecutor(num_workers=3)

        worker_results = [
            WorkerResult(worker_id=0, session_results=[], error="Error A"),
            WorkerResult(worker_id=1, session_results=[], error="Error B"),
            WorkerResult(
                worker_id=2,
                session_results=[(0, None)],  # type: ignore[list-item]
                error=None,
            ),
        ]

        with pytest.raises(RuntimeError) as exc_info:
            executor._merge_results(worker_results, num_sessions=10)

        error_message = str(exc_info.value)
        assert "Worker 0: Error A" in error_message
        assert "Worker 1: Error B" in error_message


class TestBonusStrategyInParallel:
    """Tests for bonus strategy functionality in parallel execution."""

    def test_parallel_with_bonus_enabled(self) -> None:
        """Test parallel execution with bonus betting enabled."""
        config = FullConfig(
            simulation=SimulationConfig(
                num_sessions=20,
                hands_per_session=50,
                random_seed=42,
                workers=2,
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
            bonus_strategy=BonusStrategyConfig(
                enabled=True,
                type="always",
                always=AlwaysBonusConfig(amount=5.0),
            ),
        )

        controller = SimulationController(config)
        results = controller.run()

        assert len(results.session_results) == 20
        # Verify all sessions completed successfully
        for result in results.session_results:
            assert result.hands_played > 0

    def test_bonus_parallel_sequential_equivalence(self) -> None:
        """Test bonus betting produces identical results in parallel and sequential."""
        bonus_config = BonusStrategyConfig(
            enabled=True,
            type="always",
            always=AlwaysBonusConfig(amount=5.0),
        )

        config_seq = FullConfig(
            simulation=SimulationConfig(
                num_sessions=15,
                hands_per_session=50,
                random_seed=12345,
                workers=1,
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
            bonus_strategy=bonus_config,
        )

        config_par = FullConfig(
            simulation=SimulationConfig(
                num_sessions=15,
                hands_per_session=50,
                random_seed=12345,
                workers=2,
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
            bonus_strategy=bonus_config,
        )

        results_seq = SimulationController(config_seq).run()
        results_par = SimulationController(config_par).run()

        # Verify identical results
        for seq, par in zip(
            results_seq.session_results, results_par.session_results, strict=True
        ):
            assert seq.session_profit == par.session_profit
            assert seq.hands_played == par.hands_played


class TestMaxWorkersLimit:
    """Tests for MAX_WORKERS limit on worker count."""

    def test_worker_count_capped_at_max_workers(self) -> None:
        """Test that worker count is capped at MAX_WORKERS."""
        from let_it_ride.simulation.parallel import MAX_WORKERS

        # Request more workers than MAX_WORKERS
        executor = ParallelExecutor(num_workers=MAX_WORKERS + 100)
        assert executor.num_workers == MAX_WORKERS

    def test_get_effective_worker_count_capped(self) -> None:
        """Test get_effective_worker_count respects MAX_WORKERS."""
        from let_it_ride.simulation.parallel import MAX_WORKERS

        result = get_effective_worker_count(MAX_WORKERS + 500)
        assert result == MAX_WORKERS


class TestParallelMultiSeatExecution:
    """Tests for parallel execution with multi-seat tables."""

    def test_multi_seat_parallel_produces_correct_result_count(self) -> None:
        """Test multi-seat parallel execution produces num_sessions * num_seats results."""
        config = FullConfig(
            simulation=SimulationConfig(
                num_sessions=10,
                hands_per_session=50,
                random_seed=42,
                workers=2,
            ),
            table=TableConfig(num_seats=4),
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

        controller = SimulationController(config)
        results = controller.run()

        # Should have num_sessions * num_seats = 10 * 4 = 40 results
        assert len(results.session_results) == 40

    def test_multi_seat_parallel_vs_sequential_equivalence(self) -> None:
        """Test multi-seat produces identical results in parallel vs sequential.

        Also verifies that table_session_id and seat_number are correctly
        populated and match between parallel and sequential execution.
        """
        seed = 54321
        num_sessions = 10
        num_seats = 3

        base_config = {
            "simulation": SimulationConfig(
                num_sessions=num_sessions,
                hands_per_session=50,
                random_seed=seed,
            ),
            "table": TableConfig(num_seats=num_seats),
            "bankroll": BankrollConfig(
                starting_amount=500.0,
                base_bet=5.0,
                stop_conditions=StopConditionsConfig(
                    win_limit=100.0,
                    loss_limit=200.0,
                    stop_on_insufficient_funds=True,
                ),
                betting_system=BettingSystemConfig(type="flat"),
            ),
            "strategy": StrategyConfig(type="basic"),
        }

        # Sequential (workers=1)
        config_seq = FullConfig(
            **{
                **base_config,
                "simulation": SimulationConfig(
                    num_sessions=num_sessions,
                    hands_per_session=50,
                    random_seed=seed,
                    workers=1,
                ),
            }
        )
        results_seq = SimulationController(config_seq).run()

        # Parallel (workers=2)
        config_par = FullConfig(
            **{
                **base_config,
                "simulation": SimulationConfig(
                    num_sessions=num_sessions,
                    hands_per_session=50,
                    random_seed=seed,
                    workers=2,
                ),
            }
        )
        results_par = SimulationController(config_par).run()

        # Should have same number of results
        assert len(results_seq.session_results) == len(results_par.session_results)
        assert len(results_seq.session_results) == num_sessions * num_seats

        # Verify each result matches including table_session_id and seat_number
        for seq, par in zip(
            results_seq.session_results, results_par.session_results, strict=True
        ):
            assert seq.hands_played == par.hands_played
            assert seq.session_profit == par.session_profit
            assert seq.final_bankroll == par.final_bankroll
            assert seq.outcome == par.outcome
            # Verify table_session_id and seat_number match
            assert seq.table_session_id == par.table_session_id
            assert seq.seat_number == par.seat_number
            # Verify they are populated (not None in multi-seat mode)
            assert seq.table_session_id is not None
            assert seq.seat_number is not None

    def test_table_session_id_grouping_semantics(self) -> None:
        """Test that seats sharing community cards have the same table_session_id.

        Verifies that:
        1. Each table_session_id has exactly num_seats results
        2. Results with same table_session_id have seat_numbers 1 to num_seats
        3. The grouping is consistent between parallel and sequential execution
        """
        seed = 77777
        num_sessions = 8
        num_seats = 4

        config = FullConfig(
            simulation=SimulationConfig(
                num_sessions=num_sessions,
                hands_per_session=50,
                random_seed=seed,
                workers=2,
            ),
            table=TableConfig(num_seats=num_seats),
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

        controller = SimulationController(config)
        results = controller.run()

        # Total results should be num_sessions * num_seats
        assert len(results.session_results) == num_sessions * num_seats

        # Group results by table_session_id
        from collections import defaultdict

        grouped: dict[int | None, list[int]] = defaultdict(list)
        for result in results.session_results:
            grouped[result.table_session_id].append(result.seat_number)

        # Each table_session_id should have exactly num_seats results
        assert len(grouped) == num_sessions, (
            f"Expected {num_sessions} unique table_session_ids, got {len(grouped)}"
        )

        for table_session_id, seat_numbers in grouped.items():
            # Verify table_session_id is not None
            assert table_session_id is not None, (
                "table_session_id should not be None in multi-seat mode"
            )
            # Each table session should have exactly num_seats results
            assert len(seat_numbers) == num_seats, (
                f"table_session_id {table_session_id} has {len(seat_numbers)} results, "
                f"expected {num_seats}"
            )
            # Seat numbers should be 1 through num_seats (no duplicates, no gaps)
            assert sorted(seat_numbers) == list(range(1, num_seats + 1)), (
                f"table_session_id {table_session_id} has seat_numbers {sorted(seat_numbers)}, "
                f"expected {list(range(1, num_seats + 1))}"
            )

    def test_multi_seat_parallel_with_various_seat_counts(self) -> None:
        """Test parallel execution works with different seat counts."""
        for num_seats in [2, 4, 6]:
            config = FullConfig(
                simulation=SimulationConfig(
                    num_sessions=5,
                    hands_per_session=30,
                    random_seed=12345,
                    workers=2,
                ),
                table=TableConfig(num_seats=num_seats),
                bankroll=BankrollConfig(
                    starting_amount=500.0,
                    base_bet=5.0,
                    stop_conditions=StopConditionsConfig(
                        win_limit=100.0,
                        loss_limit=200.0,
                    ),
                    betting_system=BettingSystemConfig(type="flat"),
                ),
                strategy=StrategyConfig(type="basic"),
            )

            controller = SimulationController(config)
            results = controller.run()

            expected_count = 5 * num_seats
            assert (
                len(results.session_results) == expected_count
            ), f"Expected {expected_count} results for {num_seats} seats"

    def test_multi_seat_parallel_all_results_valid(self) -> None:
        """Test all multi-seat parallel results have valid data."""
        config = FullConfig(
            simulation=SimulationConfig(
                num_sessions=15,
                hands_per_session=50,
                random_seed=42,
                workers=3,
            ),
            table=TableConfig(num_seats=4),
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

        controller = SimulationController(config)
        results = controller.run()

        for result in results.session_results:
            assert result.hands_played > 0
            assert result.starting_bankroll == 500.0
            assert result.stop_reason in StopReason
            assert result.outcome in SessionOutcome
            assert result.total_wagered >= 0

    def test_multi_seat_parallel_with_bonus_betting(self) -> None:
        """Test multi-seat parallel execution with static bonus betting."""
        config = FullConfig(
            simulation=SimulationConfig(
                num_sessions=10,
                hands_per_session=50,
                random_seed=42,
                workers=2,
            ),
            table=TableConfig(num_seats=3),
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
            bonus_strategy=BonusStrategyConfig(
                enabled=True,
                type="always",
                always=AlwaysBonusConfig(amount=5.0),
            ),
        )

        controller = SimulationController(config)
        results = controller.run()

        # Should have 10 * 3 = 30 results
        assert len(results.session_results) == 30

        # All results should be valid
        for result in results.session_results:
            assert result.hands_played > 0

    def test_multi_seat_parallel_worker_task_includes_num_seats(self) -> None:
        """Test that WorkerTask correctly carries multi-seat configuration."""
        config = FullConfig(
            simulation=SimulationConfig(
                num_sessions=10,
                hands_per_session=50,
                random_seed=42,
                workers=2,
            ),
            table=TableConfig(num_seats=6),
            bankroll=BankrollConfig(
                starting_amount=500.0,
                base_bet=5.0,
                stop_conditions=StopConditionsConfig(),
                betting_system=BettingSystemConfig(type="flat"),
            ),
            strategy=StrategyConfig(type="basic"),
        )

        task = WorkerTask(
            worker_id=0,
            session_ids=[0, 1, 2],
            session_seeds={0: 12345, 1: 23456, 2: 34567},
            config=config,
        )

        result = run_worker_sessions(task)

        assert result.error is None
        # 3 sessions * 6 seats = 18 results
        assert len(result.session_results) == 18
