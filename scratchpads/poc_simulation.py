#!/usr/bin/env python3
"""
Proof of Concept: Let It Ride Simulation

This script demonstrates running simulations using the current state of the system.
Run with: poetry run python3 scratchpads/poc_simulation.py
"""

import random
import time
from dataclasses import dataclass

from let_it_ride.core.deck import Deck
from let_it_ride.core.game_engine import GameEngine
from let_it_ride.strategy.basic import BasicStrategy
from let_it_ride.strategy.presets import conservative_strategy, aggressive_strategy
from let_it_ride.config.paytables import standard_main_paytable, bonus_paytable_b
from let_it_ride.simulation.session import Session, SessionConfig
from let_it_ride.bankroll.betting_systems import FlatBetting


@dataclass
class SimulationSummary:
    """Summary statistics for a multi-session simulation."""
    total_sessions: int
    winning_sessions: int
    losing_sessions: int
    breakeven_sessions: int
    total_hands: int
    total_profit: float
    best_session_profit: float
    worst_session_profit: float
    avg_hands_per_session: float
    win_rate: float
    elapsed_seconds: float
    hands_per_second: float


def run_single_session(
    session_id: int,
    config: SessionConfig,
    seed: int | None = None,
    strategy_name: str = "basic",
    verbose: bool = False,
) -> tuple[int, "SessionResult"]:
    """Run a single session and return results."""
    # Create components with optional seed
    rng = random.Random(seed) if seed is not None else random.Random()
    deck = Deck()

    # Get strategy
    if strategy_name == "basic":
        strategy = BasicStrategy()
    elif strategy_name == "conservative":
        strategy = conservative_strategy()
    elif strategy_name == "aggressive":
        strategy = aggressive_strategy()
    else:
        raise ValueError(f"Unknown strategy: {strategy_name}")

    main_paytable = standard_main_paytable()
    bonus_paytable = bonus_paytable_b()

    # Create game engine
    engine = GameEngine(
        deck=deck,
        strategy=strategy,
        main_paytable=main_paytable,
        bonus_paytable=bonus_paytable,
        rng=rng,
    )

    # Create betting system
    betting_system = FlatBetting(config.base_bet)

    # Create and run session
    session = Session(config, engine, betting_system)
    result = session.run_to_completion()

    if verbose:
        print(f"  Session {session_id}: {result.outcome.value} - "
              f"{result.hands_played} hands, "
              f"profit: ${result.session_profit:+.2f}, "
              f"reason: {result.stop_reason.value}")

    return session_id, result


def run_simulation(
    num_sessions: int = 100,
    starting_bankroll: float = 500.0,
    base_bet: float = 5.0,
    win_limit: float = 250.0,
    loss_limit: float = 200.0,
    max_hands: int = 200,
    bonus_bet: float = 1.0,
    strategy_name: str = "basic",
    random_seed: int | None = 42,
    verbose: bool = True,
) -> SimulationSummary:
    """
    Run a multi-session simulation.

    Args:
        num_sessions: Number of sessions to simulate
        starting_bankroll: Starting bankroll for each session
        base_bet: Base bet amount per hand
        win_limit: Stop session after reaching this profit
        loss_limit: Stop session after reaching this loss
        max_hands: Maximum hands per session
        bonus_bet: Bonus bet amount (0 to disable)
        strategy_name: Strategy to use ("basic", "conservative", "aggressive")
        random_seed: Base seed for reproducibility (None for random)
        verbose: Print progress and session details

    Returns:
        SimulationSummary with aggregated statistics
    """
    if verbose:
        print(f"\n{'='*60}")
        print(f"Let It Ride Simulation - Proof of Concept")
        print(f"{'='*60}")
        print(f"Configuration:")
        print(f"  Sessions: {num_sessions}")
        print(f"  Bankroll: ${starting_bankroll:.2f}")
        print(f"  Base Bet: ${base_bet:.2f}")
        print(f"  Win Limit: ${win_limit:.2f}")
        print(f"  Loss Limit: ${loss_limit:.2f}")
        print(f"  Max Hands: {max_hands}")
        print(f"  Bonus Bet: ${bonus_bet:.2f}")
        print(f"  Strategy: {strategy_name}")
        print(f"  Random Seed: {random_seed}")
        print(f"{'='*60}\n")

    # Create session config
    config = SessionConfig(
        starting_bankroll=starting_bankroll,
        base_bet=base_bet,
        win_limit=win_limit,
        loss_limit=loss_limit,
        max_hands=max_hands,
        bonus_bet=bonus_bet,
    )

    # Track results
    results = []
    start_time = time.perf_counter()

    # Run sessions
    for i in range(num_sessions):
        # Create unique seed for each session if base seed provided
        session_seed = (random_seed + i) if random_seed is not None else None

        _, result = run_single_session(
            session_id=i + 1,
            config=config,
            seed=session_seed,
            strategy_name=strategy_name,
            verbose=verbose and num_sessions <= 20,  # Only show details for small runs
        )
        results.append(result)

        # Progress indicator for large runs
        if verbose and num_sessions > 20 and (i + 1) % (num_sessions // 10) == 0:
            print(f"  Progress: {i + 1}/{num_sessions} sessions completed...")

    elapsed = time.perf_counter() - start_time

    # Calculate summary statistics
    from let_it_ride.simulation.session import SessionOutcome

    winning = sum(1 for r in results if r.outcome == SessionOutcome.WIN)
    losing = sum(1 for r in results if r.outcome == SessionOutcome.LOSS)
    breakeven = sum(1 for r in results if r.outcome == SessionOutcome.PUSH)

    total_hands = sum(r.hands_played for r in results)
    total_profit = sum(r.session_profit for r in results)
    profits = [r.session_profit for r in results]

    summary = SimulationSummary(
        total_sessions=num_sessions,
        winning_sessions=winning,
        losing_sessions=losing,
        breakeven_sessions=breakeven,
        total_hands=total_hands,
        total_profit=total_profit,
        best_session_profit=max(profits),
        worst_session_profit=min(profits),
        avg_hands_per_session=total_hands / num_sessions,
        win_rate=winning / num_sessions * 100,
        elapsed_seconds=elapsed,
        hands_per_second=total_hands / elapsed if elapsed > 0 else 0,
    )

    if verbose:
        print(f"\n{'='*60}")
        print(f"SIMULATION RESULTS")
        print(f"{'='*60}")
        print(f"Sessions:")
        print(f"  Total: {summary.total_sessions}")
        print(f"  Winning: {summary.winning_sessions} ({summary.win_rate:.1f}%)")
        print(f"  Losing: {summary.losing_sessions} ({summary.losing_sessions/num_sessions*100:.1f}%)")
        print(f"  Breakeven: {summary.breakeven_sessions}")
        print(f"\nProfitability:")
        print(f"  Total Profit: ${summary.total_profit:+,.2f}")
        print(f"  Avg Profit/Session: ${summary.total_profit/num_sessions:+,.2f}")
        print(f"  Best Session: ${summary.best_session_profit:+,.2f}")
        print(f"  Worst Session: ${summary.worst_session_profit:+,.2f}")
        print(f"\nPerformance:")
        print(f"  Total Hands: {summary.total_hands:,}")
        print(f"  Avg Hands/Session: {summary.avg_hands_per_session:.1f}")
        print(f"  Elapsed Time: {summary.elapsed_seconds:.2f}s")
        print(f"  Throughput: {summary.hands_per_second:,.0f} hands/second")
        print(f"{'='*60}\n")

    return summary


def demo_single_hand():
    """Demonstrate a single hand with full details."""
    print("\n" + "="*60)
    print("SINGLE HAND DEMONSTRATION")
    print("="*60)

    # Create components
    rng = random.Random(12345)
    deck = Deck()
    strategy = BasicStrategy()
    main_paytable = standard_main_paytable()
    bonus_paytable = bonus_paytable_b()

    engine = GameEngine(
        deck=deck,
        strategy=strategy,
        main_paytable=main_paytable,
        bonus_paytable=bonus_paytable,
        rng=rng,
    )

    # Play a single hand
    result = engine.play_hand(hand_id=1, base_bet=5.0, bonus_bet=1.0)

    print(f"\nPlayer Cards: {', '.join(str(c) for c in result.player_cards)}")
    print(f"Community Cards: {', '.join(str(c) for c in result.community_cards)}")
    print(f"\nDecisions:")
    print(f"  Bet 1 (after 3 cards): {result.decision_bet1.value}")
    print(f"  Bet 2 (after 4 cards): {result.decision_bet2.value}")
    print(f"\nFinal Hand: {result.final_hand_rank.name}")
    print(f"Bets at Risk: {result.bets_at_risk / 5.0:.0f} x $5.00 = ${result.bets_at_risk:.2f}")
    print(f"\nPayouts:")
    print(f"  Main Game: ${result.main_payout:.2f}")
    print(f"  Bonus: ${result.bonus_payout:.2f}")
    print(f"  Net Result: ${result.net_result:+.2f}")
    print("="*60 + "\n")


def compare_strategies():
    """Compare different strategies."""
    print("\n" + "="*60)
    print("STRATEGY COMPARISON")
    print("="*60)

    strategies = ["basic", "conservative", "aggressive"]
    results = {}

    for strategy_name in strategies:
        summary = run_simulation(
            num_sessions=1000,
            strategy_name=strategy_name,
            random_seed=42,
            verbose=False,
        )
        results[strategy_name] = summary

    print(f"\n{'Strategy':<15} {'Win Rate':>10} {'Avg Profit':>12} {'Hands/Sec':>12}")
    print("-" * 52)
    for name, summary in results.items():
        avg_profit = summary.total_profit / summary.total_sessions
        print(f"{name:<15} {summary.win_rate:>9.1f}% ${avg_profit:>10.2f} {summary.hands_per_second:>11,.0f}")
    print("="*60 + "\n")


if __name__ == "__main__":
    # Demo single hand
    demo_single_hand()

    # Run a small simulation with verbose output
    run_simulation(
        num_sessions=10,
        starting_bankroll=500.0,
        base_bet=5.0,
        win_limit=100.0,
        loss_limit=100.0,
        max_hands=100,
        bonus_bet=1.0,
        strategy_name="basic",
        random_seed=42,
        verbose=True,
    )

    # Run a larger simulation
    print("\n" + "="*60)
    print("LARGE SIMULATION (1000 sessions)")
    print("="*60)
    run_simulation(
        num_sessions=1000,
        starting_bankroll=500.0,
        base_bet=5.0,
        win_limit=250.0,
        loss_limit=200.0,
        max_hands=200,
        bonus_bet=1.0,
        strategy_name="basic",
        random_seed=42,
        verbose=True,
    )

    # Compare strategies
    compare_strategies()
