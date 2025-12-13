#!/usr/bin/env python3
"""Memory benchmarks for Let It Ride simulator.

This module measures memory usage during simulations to ensure
the simulator stays within memory constraints.

Usage:
    poetry run python benchmarks/benchmark_memory.py
"""

from __future__ import annotations

import gc
import tracemalloc
from dataclasses import dataclass

from let_it_ride.config.models import (
    BankrollConfig,
    BettingSystemConfig,
    FullConfig,
    SimulationConfig,
    StopConditionsConfig,
    StrategyConfig,
)
from let_it_ride.simulation import SimulationController


@dataclass
class MemoryBenchmarkResult:
    """Result of a memory benchmark run."""

    name: str
    current_mb: float
    peak_mb: float
    target_mb: float | None = None
    num_sessions: int = 0
    total_hands: int = 0

    @property
    def meets_target(self) -> bool | None:
        """Check if peak memory meets target, if one is set."""
        if self.target_mb is None:
            return None
        return self.peak_mb <= self.target_mb


def measure_simulation_memory(
    num_sessions: int,
    hands_per_session: int,
    workers: int = 4,
    target_mb: float | None = None,
    name: str | None = None,
) -> MemoryBenchmarkResult:
    """Measure memory usage for a simulation configuration.

    Args:
        num_sessions: Number of sessions to simulate
        hands_per_session: Hands per session
        workers: Number of parallel workers
        target_mb: Optional target maximum memory in MB
        name: Optional benchmark name

    Returns:
        MemoryBenchmarkResult with memory usage data
    """
    config = FullConfig(
        simulation=SimulationConfig(
            num_sessions=num_sessions,
            hands_per_session=hands_per_session,
            random_seed=42,
            workers=workers,
        ),
        bankroll=BankrollConfig(
            starting_amount=500.0,
            base_bet=5.0,
            stop_conditions=StopConditionsConfig(
                win_limit=250.0,
                loss_limit=200.0,
                stop_on_insufficient_funds=True,
            ),
            betting_system=BettingSystemConfig(type="flat"),
        ),
        strategy=StrategyConfig(type="basic"),
    )

    # Force garbage collection for accurate baseline
    gc.collect()

    # Start memory tracking
    tracemalloc.start()

    # Run simulation
    controller = SimulationController(config)
    results = controller.run()

    # Get memory usage
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return MemoryBenchmarkResult(
        name=name or f"Simulation ({num_sessions:,} sessions)",
        current_mb=current / (1024 * 1024),
        peak_mb=peak / (1024 * 1024),
        target_mb=target_mb,
        num_sessions=num_sessions,
        total_hands=results.total_hands,
    )


def benchmark_memory_scaling() -> list[MemoryBenchmarkResult]:
    """Benchmark memory usage at different simulation scales.

    Tests memory growth as simulation size increases to verify
    sub-linear scaling.
    """
    results = []

    # Small simulation
    results.append(
        measure_simulation_memory(
            num_sessions=1_000,
            hands_per_session=50,
            workers=4,
            name="Small (1K sessions)",
        )
    )

    # Medium simulation
    results.append(
        measure_simulation_memory(
            num_sessions=10_000,
            hands_per_session=50,
            workers=4,
            target_mb=500,  # Target: <500MB for 10K sessions
            name="Medium (10K sessions)",
        )
    )

    # Large simulation
    results.append(
        measure_simulation_memory(
            num_sessions=100_000,
            hands_per_session=50,
            workers=4,
            target_mb=2000,  # Target: <2GB for 100K sessions
            name="Large (100K sessions)",
        )
    )

    return results


def benchmark_10m_hands() -> MemoryBenchmarkResult:
    """Benchmark memory for 10M hand simulation.

    Target: <4GB for 10M hands (primary project requirement)
    """
    # 10M hands = 100K sessions * 100 hands/session
    return measure_simulation_memory(
        num_sessions=100_000,
        hands_per_session=100,
        workers=4,
        target_mb=4000,  # Target: <4GB
        name="10M Hands Target",
    )


def print_memory_results(results: list[MemoryBenchmarkResult]) -> None:
    """Print memory benchmark results."""
    print("\n" + "=" * 80)
    print("MEMORY BENCHMARK RESULTS")
    print("=" * 80)

    for result in results:
        status = ""
        if result.target_mb is not None:
            status = " [PASS]" if result.meets_target else " [FAIL]"

        target_str = f" (target: <{result.target_mb:.0f}MB)" if result.target_mb else ""

        print(f"\n{result.name}{status}")
        print(f"  Sessions: {result.num_sessions:,}")
        print(f"  Total hands: {result.total_hands:,}")
        print(f"  Current memory: {result.current_mb:.1f}MB")
        print(f"  Peak memory: {result.peak_mb:.1f}MB{target_str}")

        # Memory per hand for scaling analysis
        if result.total_hands > 0:
            bytes_per_hand = (result.peak_mb * 1024 * 1024) / result.total_hands
            print(f"  Bytes per hand: {bytes_per_hand:.1f}")

    print("\n" + "=" * 80)

    # Summary
    passed = sum(1 for r in results if r.meets_target is True)
    failed = sum(1 for r in results if r.meets_target is False)
    no_target = sum(1 for r in results if r.meets_target is None)

    print(f"Summary: {passed} passed, {failed} failed, {no_target} informational")
    print("=" * 80)


def run_all_benchmarks() -> list[MemoryBenchmarkResult]:
    """Run all memory benchmarks."""
    print("Running memory scaling benchmarks...")
    scaling_results = benchmark_memory_scaling()

    print("Running 10M hands benchmark (this may take a while)...")
    target_result = benchmark_10m_hands()

    return [*scaling_results, target_result]


if __name__ == "__main__":
    results = run_all_benchmarks()
    print_memory_results(results)
