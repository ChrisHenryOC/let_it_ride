#!/usr/bin/env python3
"""Throughput benchmarks for Let It Ride simulator.

This module measures simulation throughput across different configurations
and component isolation tests.

Usage:
    poetry run python benchmarks/benchmark_throughput.py
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass

from let_it_ride.config.models import (
    BankrollConfig,
    BettingSystemConfig,
    FullConfig,
    SimulationConfig,
    StopConditionsConfig,
    StrategyConfig,
)
from let_it_ride.core.card import Card, Rank, Suit
from let_it_ride.core.deck import Deck
from let_it_ride.core.hand_evaluator import evaluate_five_card_hand
from let_it_ride.core.three_card_evaluator import evaluate_three_card_hand
from let_it_ride.simulation import SimulationController


@dataclass
class BenchmarkResult:
    """Result of a benchmark run."""

    name: str
    iterations: int
    elapsed_seconds: float
    throughput: float  # iterations per second
    target: float | None = None

    @property
    def meets_target(self) -> bool | None:
        """Check if throughput meets target, if one is set."""
        if self.target is None:
            return None
        return self.throughput >= self.target


def benchmark_hand_evaluation(iterations: int = 100_000) -> BenchmarkResult:
    """Benchmark five-card hand evaluation throughput.

    Creates random 5-card hands and evaluates them.
    Target: >500,000 hands/second
    """
    rng = random.Random(42)
    all_cards = [Card(rank, suit) for suit in Suit for rank in Rank]

    # Pre-generate hands to avoid random overhead in timing
    hands = [rng.sample(all_cards, 5) for _ in range(iterations)]

    start = time.perf_counter()
    for hand in hands:
        evaluate_five_card_hand(hand)
    elapsed = time.perf_counter() - start

    return BenchmarkResult(
        name="Hand Evaluation (5-card)",
        iterations=iterations,
        elapsed_seconds=elapsed,
        throughput=iterations / elapsed,
        target=500_000,
    )


def benchmark_three_card_evaluation(iterations: int = 100_000) -> BenchmarkResult:
    """Benchmark three-card hand evaluation throughput.

    Creates random 3-card hands and evaluates them.
    Target: >1,000,000 hands/second (simpler than 5-card)
    """
    rng = random.Random(42)
    all_cards = [Card(rank, suit) for suit in Suit for rank in Rank]

    # Pre-generate hands
    hands = [rng.sample(all_cards, 3) for _ in range(iterations)]

    start = time.perf_counter()
    for hand in hands:
        evaluate_three_card_hand(hand)
    elapsed = time.perf_counter() - start

    return BenchmarkResult(
        name="Hand Evaluation (3-card bonus)",
        iterations=iterations,
        elapsed_seconds=elapsed,
        throughput=iterations / elapsed,
        target=1_000_000,
    )


def benchmark_deck_operations(iterations: int = 100_000) -> BenchmarkResult:
    """Benchmark deck shuffle and deal operations.

    Simulates a typical hand: reset, shuffle, deal 3+2 cards.
    Target: >200,000 hands/second (deck operations only)
    """
    deck = Deck()
    rng = random.Random(42)

    start = time.perf_counter()
    for _ in range(iterations):
        deck.reset()
        deck.shuffle(rng)
        deck.deal(3)  # Player cards
        deck.deal(2)  # Community cards
    elapsed = time.perf_counter() - start

    return BenchmarkResult(
        name="Deck Operations (reset/shuffle/deal)",
        iterations=iterations,
        elapsed_seconds=elapsed,
        throughput=iterations / elapsed,
        target=200_000,
    )


def benchmark_full_simulation(
    num_sessions: int = 1_000,
    hands_per_session: int = 100,
    workers: int = 4,
) -> BenchmarkResult:
    """Benchmark full simulation throughput.

    Target: >100,000 hands/second with parallel execution.
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

    controller = SimulationController(config)

    start = time.perf_counter()
    results = controller.run()
    elapsed = time.perf_counter() - start

    return BenchmarkResult(
        name=f"Full Simulation ({workers} workers)",
        iterations=results.total_hands,
        elapsed_seconds=elapsed,
        throughput=results.total_hands / elapsed,
        target=100_000,
    )


def benchmark_sequential_simulation(
    num_sessions: int = 500,
    hands_per_session: int = 100,
) -> BenchmarkResult:
    """Benchmark sequential (single-worker) simulation throughput.

    Establishes baseline for parallelization speedup measurement.
    """
    config = FullConfig(
        simulation=SimulationConfig(
            num_sessions=num_sessions,
            hands_per_session=hands_per_session,
            random_seed=42,
            workers=1,
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

    controller = SimulationController(config)

    start = time.perf_counter()
    results = controller.run()
    elapsed = time.perf_counter() - start

    return BenchmarkResult(
        name="Full Simulation (sequential)",
        iterations=results.total_hands,
        elapsed_seconds=elapsed,
        throughput=results.total_hands / elapsed,
        target=25_000,  # Lower target for sequential
    )


def run_all_benchmarks() -> list[BenchmarkResult]:
    """Run all throughput benchmarks and return results."""
    results = [
        benchmark_hand_evaluation(),
        benchmark_three_card_evaluation(),
        benchmark_deck_operations(),
        benchmark_sequential_simulation(),
        benchmark_full_simulation(),
    ]
    return results


def print_results(results: list[BenchmarkResult]) -> None:
    """Print benchmark results in a formatted table."""
    print("\n" + "=" * 80)
    print("THROUGHPUT BENCHMARK RESULTS")
    print("=" * 80)

    for result in results:
        status = ""
        if result.target is not None:
            status = " [PASS]" if result.meets_target else " [FAIL]"

        target_str = f" (target: {result.target:,.0f}/s)" if result.target else ""

        print(f"\n{result.name}{status}")
        print(f"  Iterations: {result.iterations:,}")
        print(f"  Time: {result.elapsed_seconds:.3f}s")
        print(f"  Throughput: {result.throughput:,.0f}/s{target_str}")

    print("\n" + "=" * 80)

    # Summary
    passed = sum(1 for r in results if r.meets_target is True)
    failed = sum(1 for r in results if r.meets_target is False)
    no_target = sum(1 for r in results if r.meets_target is None)

    print(f"Summary: {passed} passed, {failed} failed, {no_target} informational")
    print("=" * 80)


if __name__ == "__main__":
    results = run_all_benchmarks()
    print_results(results)
