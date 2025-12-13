#!/usr/bin/env python3
"""
Proof of Concept: Let It Ride Simulation

This script demonstrates the full capabilities of the simulation system including:
- Single-player and multi-player table sessions
- Multiple betting systems (Flat, Martingale, Paroli, D'Alembert, Fibonacci)
- Various strategies (Basic, Conservative, Aggressive)
- Bonus strategies
- Dealer discard configuration
- Bankroll tracking with drawdown analysis

NEW FUNCTIONALITY DEMONSTRATED:
- YAML configuration loading (config/loader.py)
- SimulationController for orchestrated execution (simulation/controller.py)
- RNGManager for centralized seed management (simulation/rng.py)
- AggregateStatistics for comprehensive statistics (simulation/aggregation.py)
- OutputFormatter for Rich-based console output (cli/formatters.py)
- CSVExporter for results export (analytics/export_csv.py)

Run with: poetry run python3 scratchpads/poc_simulation.py
"""

import random
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

# Core game components
from let_it_ride.core.deck import Deck
from let_it_ride.core.game_engine import GameEngine
from let_it_ride.core.table import Table

# Strategy components
from let_it_ride.strategy.basic import BasicStrategy
from let_it_ride.strategy.presets import conservative_strategy, aggressive_strategy
from let_it_ride.strategy.bonus import (
    NeverBonusStrategy,
    AlwaysBonusStrategy,
    StaticBonusStrategy,
    BankrollConditionalBonusStrategy,
)

# Configuration components
from let_it_ride.config.paytables import standard_main_paytable, bonus_paytable_b
from let_it_ride.config.models import DealerConfig, TableConfig
from let_it_ride.config.loader import load_config, load_config_from_string

# Session components
from let_it_ride.simulation.session import Session, SessionConfig, SessionOutcome, SessionResult
from let_it_ride.simulation.table_session import TableSession, TableSessionConfig

# Betting systems
from let_it_ride.bankroll.betting_systems import (
    FlatBetting,
    MartingaleBetting,
    ReverseMartingaleBetting,
    ParoliBetting,
    DAlembertBetting,
    FibonacciBetting,
)

# NEW: Controller and orchestration
from let_it_ride.simulation.controller import SimulationController, SimulationResults

# NEW: RNG management
from let_it_ride.simulation.rng import RNGManager, validate_rng_quality

# NEW: Aggregation
from let_it_ride.simulation.aggregation import aggregate_results, AggregateStatistics

# NEW: Output formatting
from let_it_ride.cli.formatters import OutputFormatter

# NEW: CSV export
from let_it_ride.analytics.export_csv import CSVExporter


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
    avg_max_drawdown_pct: float = 0.0


def get_strategy(strategy_name: str):
    """Get strategy by name."""
    if strategy_name == "basic":
        return BasicStrategy()
    elif strategy_name == "conservative":
        return conservative_strategy()
    elif strategy_name == "aggressive":
        return aggressive_strategy()
    else:
        raise ValueError(f"Unknown strategy: {strategy_name}")


def get_betting_system(system_name: str, base_bet: float):
    """Get betting system by name."""
    if system_name == "flat":
        return FlatBetting(base_bet)
    elif system_name == "martingale":
        return MartingaleBetting(base_bet, max_bet=base_bet * 16, max_progressions=4)
    elif system_name == "reverse_martingale":
        return ReverseMartingaleBetting(base_bet, max_bet=base_bet * 16, profit_target_streak=3)
    elif system_name == "paroli":
        return ParoliBetting(base_bet, wins_before_reset=3, max_bet=base_bet * 8)
    elif system_name == "dalembert":
        return DAlembertBetting(base_bet, unit=base_bet, max_bet=base_bet * 10)
    elif system_name == "fibonacci":
        return FibonacciBetting(base_bet, max_bet=base_bet * 20, max_position=8)
    else:
        raise ValueError(f"Unknown betting system: {system_name}")


def run_single_session(
    session_id: int,
    config: SessionConfig,
    seed: int | None = None,
    strategy_name: str = "basic",
    betting_system_name: str = "flat",
    dealer_discard: bool = False,
    verbose: bool = False,
) -> tuple[int, "SessionResult"]:
    """Run a single session and return results."""
    # Create components with optional seed
    rng = random.Random(seed) if seed is not None else random.Random()
    deck = Deck()

    # Get strategy
    strategy = get_strategy(strategy_name)

    main_paytable = standard_main_paytable()
    bonus_paytable = bonus_paytable_b()

    # Optional dealer discard configuration
    dealer_config = DealerConfig(discard_enabled=True, discard_cards=1) if dealer_discard else None

    # Create game engine
    engine = GameEngine(
        deck=deck,
        strategy=strategy,
        main_paytable=main_paytable,
        bonus_paytable=bonus_paytable,
        rng=rng,
        dealer_config=dealer_config,
    )

    # Create betting system
    betting_system = get_betting_system(betting_system_name, config.base_bet)

    # Create and run session
    session = Session(config, engine, betting_system)
    result = session.run_to_completion()

    if verbose:
        print(
            f"  Session {session_id}: {result.outcome.value} - "
            f"{result.hands_played} hands, "
            f"profit: ${result.session_profit:+.2f}, "
            f"max drawdown: {result.max_drawdown_pct:.1f}%, "
            f"reason: {result.stop_reason.value}"
        )

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
    betting_system_name: str = "flat",
    dealer_discard: bool = False,
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
        betting_system_name: Betting system ("flat", "martingale", "paroli", etc.)
        dealer_discard: Enable dealer discard (burns 1 card before community)
        random_seed: Base seed for reproducibility (None for random)
        verbose: Print progress and session details

    Returns:
        SimulationSummary with aggregated statistics
    """
    if verbose:
        print(f"\n{'='*60}")
        print("Let It Ride Simulation - Proof of Concept")
        print(f"{'='*60}")
        print("Configuration:")
        print(f"  Sessions: {num_sessions}")
        print(f"  Bankroll: ${starting_bankroll:.2f}")
        print(f"  Base Bet: ${base_bet:.2f}")
        print(f"  Win Limit: ${win_limit:.2f}")
        print(f"  Loss Limit: ${loss_limit:.2f}")
        print(f"  Max Hands: {max_hands}")
        print(f"  Bonus Bet: ${bonus_bet:.2f}")
        print(f"  Strategy: {strategy_name}")
        print(f"  Betting System: {betting_system_name}")
        print(f"  Dealer Discard: {dealer_discard}")
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
            betting_system_name=betting_system_name,
            dealer_discard=dealer_discard,
            verbose=verbose and num_sessions <= 20,  # Only show details for small runs
        )
        results.append(result)

        # Progress indicator for large runs
        if verbose and num_sessions > 20 and (i + 1) % (num_sessions // 10) == 0:
            print(f"  Progress: {i + 1}/{num_sessions} sessions completed...")

    elapsed = time.perf_counter() - start_time

    # Calculate summary statistics
    winning = sum(1 for r in results if r.outcome == SessionOutcome.WIN)
    losing = sum(1 for r in results if r.outcome == SessionOutcome.LOSS)
    breakeven = sum(1 for r in results if r.outcome == SessionOutcome.PUSH)

    total_hands = sum(r.hands_played for r in results)
    total_profit = sum(r.session_profit for r in results)
    profits = [r.session_profit for r in results]
    avg_drawdown = sum(r.max_drawdown_pct for r in results) / num_sessions

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
        avg_max_drawdown_pct=avg_drawdown,
    )

    if verbose:
        print(f"\n{'='*60}")
        print("SIMULATION RESULTS")
        print(f"{'='*60}")
        print("Sessions:")
        print(f"  Total: {summary.total_sessions}")
        print(f"  Winning: {summary.winning_sessions} ({summary.win_rate:.1f}%)")
        print(f"  Losing: {summary.losing_sessions} ({summary.losing_sessions/num_sessions*100:.1f}%)")
        print(f"  Breakeven: {summary.breakeven_sessions}")
        print("\nProfitability:")
        print(f"  Total Profit: ${summary.total_profit:+,.2f}")
        print(f"  Avg Profit/Session: ${summary.total_profit/num_sessions:+,.2f}")
        print(f"  Best Session: ${summary.best_session_profit:+,.2f}")
        print(f"  Worst Session: ${summary.worst_session_profit:+,.2f}")
        print("\nRisk Metrics:")
        print(f"  Avg Max Drawdown: {summary.avg_max_drawdown_pct:.1f}%")
        print("\nPerformance:")
        print(f"  Total Hands: {summary.total_hands:,}")
        print(f"  Avg Hands/Session: {summary.avg_hands_per_session:.1f}")
        print(f"  Elapsed Time: {summary.elapsed_seconds:.2f}s")
        print(f"  Throughput: {summary.hands_per_second:,.0f} hands/second")
        print(f"{'='*60}\n")

    return summary


def demo_single_hand():
    """Demonstrate a single hand with full details."""
    print("\n" + "=" * 60)
    print("SINGLE HAND DEMONSTRATION")
    print("=" * 60)

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
    print("\nDecisions:")
    print(f"  Bet 1 (after 3 cards): {result.decision_bet1.value}")
    print(f"  Bet 2 (after 4 cards): {result.decision_bet2.value}")
    print(f"\nFinal Hand: {result.final_hand_rank.name}")
    print(f"Bets at Risk: {result.bets_at_risk / 5.0:.0f} x $5.00 = ${result.bets_at_risk:.2f}")
    print("\nPayouts:")
    print(f"  Main Game: ${result.main_payout:.2f}")
    print(f"  Bonus: ${result.bonus_payout:.2f}")
    print(f"  Net Result: ${result.net_result:+.2f}")
    print("=" * 60 + "\n")


def demo_dealer_discard():
    """Demonstrate dealer discard configuration."""
    print("\n" + "=" * 60)
    print("DEALER DISCARD DEMONSTRATION")
    print("=" * 60)

    rng = random.Random(12345)
    deck = Deck()
    strategy = BasicStrategy()
    main_paytable = standard_main_paytable()
    bonus_paytable = bonus_paytable_b()

    # Enable dealer discard - burns 1 card before community cards
    dealer_config = DealerConfig(discard_enabled=True, discard_cards=1)

    engine = GameEngine(
        deck=deck,
        strategy=strategy,
        main_paytable=main_paytable,
        bonus_paytable=bonus_paytable,
        rng=rng,
        dealer_config=dealer_config,
    )

    # Play a hand with dealer discard
    result = engine.play_hand(hand_id=1, base_bet=5.0)

    print(f"\nPlayer Cards: {', '.join(str(c) for c in result.player_cards)}")
    print(f"Discarded Cards: {', '.join(str(c) for c in engine.last_discarded_cards())}")
    print(f"Community Cards: {', '.join(str(c) for c in result.community_cards)}")
    print(f"Final Hand: {result.final_hand_rank.name}")
    print("=" * 60 + "\n")


def demo_multi_player_table():
    """Demonstrate multi-player table session."""
    print("\n" + "=" * 60)
    print("MULTI-PLAYER TABLE DEMONSTRATION (3 seats)")
    print("=" * 60)

    rng = random.Random(54321)
    deck = Deck()
    strategy = BasicStrategy()
    main_paytable = standard_main_paytable()
    bonus_paytable = bonus_paytable_b()

    # Configure 3-seat table
    table_config = TableConfig(num_seats=3)

    table = Table(
        deck=deck,
        strategy=strategy,
        main_paytable=main_paytable,
        bonus_paytable=bonus_paytable,
        rng=rng,
        table_config=table_config,
    )

    # Configure table session
    session_config = TableSessionConfig(
        table_config=table_config,
        starting_bankroll=500.0,
        base_bet=5.0,
        win_limit=100.0,
        loss_limit=100.0,
        max_hands=50,
        bonus_bet=1.0,
    )

    betting_system = FlatBetting(5.0)
    table_session = TableSession(session_config, table, betting_system)

    # Run table session
    result = table_session.run_to_completion()

    print(f"\nTotal Rounds Played: {result.total_rounds}")
    print(f"Stop Reason: {result.stop_reason.value}")
    print("\nPer-Seat Results:")
    for seat_result in result.seat_results:
        sr = seat_result.session_result
        print(
            f"  Seat {seat_result.seat_number}: {sr.outcome.value} - "
            f"Profit: ${sr.session_profit:+.2f}, "
            f"Max Drawdown: {sr.max_drawdown_pct:.1f}%"
        )
    print("=" * 60 + "\n")


def compare_strategies():
    """Compare different strategies."""
    print("\n" + "=" * 60)
    print("STRATEGY COMPARISON")
    print("=" * 60)

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

    print(f"\n{'Strategy':<15} {'Win Rate':>10} {'Avg Profit':>12} {'Avg Drawdown':>14} {'Hands/Sec':>12}")
    print("-" * 66)
    for name, summary in results.items():
        avg_profit = summary.total_profit / summary.total_sessions
        print(
            f"{name:<15} {summary.win_rate:>9.1f}% ${avg_profit:>10.2f} "
            f"{summary.avg_max_drawdown_pct:>13.1f}% {summary.hands_per_second:>11,.0f}"
        )
    print("=" * 60 + "\n")


def compare_betting_systems():
    """Compare different betting systems."""
    print("\n" + "=" * 60)
    print("BETTING SYSTEM COMPARISON")
    print("=" * 60)

    betting_systems = ["flat", "martingale", "paroli", "dalembert", "fibonacci"]
    results = {}

    for system_name in betting_systems:
        summary = run_simulation(
            num_sessions=1000,
            betting_system_name=system_name,
            random_seed=42,
            verbose=False,
        )
        results[system_name] = summary

    print(f"\n{'Betting System':<18} {'Win Rate':>10} {'Avg Profit':>12} {'Avg Drawdown':>14}")
    print("-" * 56)
    for name, summary in results.items():
        avg_profit = summary.total_profit / summary.total_sessions
        print(
            f"{name:<18} {summary.win_rate:>9.1f}% ${avg_profit:>10.2f} "
            f"{summary.avg_max_drawdown_pct:>13.1f}%"
        )
    print("=" * 60 + "\n")


def demo_bonus_strategies():
    """Demonstrate different bonus betting strategies."""
    print("\n" + "=" * 60)
    print("BONUS STRATEGY DEMONSTRATION")
    print("=" * 60)

    from let_it_ride.strategy.bonus import BonusContext

    # Create context for demonstration
    context = BonusContext(
        bankroll=550.0,
        starting_bankroll=500.0,
        session_profit=50.0,
        hands_played=20,
        main_streak=2,
        bonus_streak=1,
        base_bet=5.0,
        min_bonus_bet=1.0,
        max_bonus_bet=25.0,
    )

    strategies = [
        ("Never Bonus", NeverBonusStrategy()),
        ("Always $1", AlwaysBonusStrategy(amount=1.0)),
        ("Static $2", StaticBonusStrategy(amount=2.0)),
        ("Static 20% of base", StaticBonusStrategy(ratio=0.2)),
        (
            "Bankroll Conditional",
            BankrollConditionalBonusStrategy(
                base_amount=1.0,
                min_session_profit=25.0,
                profit_percentage=0.1,
            ),
        ),
    ]

    print(f"\nContext: bankroll=${context.bankroll}, profit=${context.session_profit}, streak={context.main_streak}")
    print("\nBonus bet amounts:")
    for name, strategy in strategies:
        bet = strategy.get_bonus_bet(context)
        print(f"  {name:<25}: ${bet:.2f}")
    print("=" * 60 + "\n")


# =============================================================================
# NEW FUNCTIONALITY DEMONSTRATIONS
# =============================================================================


def demo_yaml_config_loading():
    """Demonstrate YAML configuration loading."""
    print("\n" + "=" * 60)
    print("YAML CONFIGURATION LOADING DEMONSTRATION")
    print("=" * 60)

    # Demo 1: Load from YAML string
    yaml_content = """
simulation:
  num_sessions: 100
  hands_per_session: 50
  random_seed: 42
  workers: 1

bankroll:
  starting_amount: 500.0
  base_bet: 5.0
  stop_conditions:
    win_limit: 100.0
    loss_limit: 100.0
    max_hands: 50
  betting_system:
    type: "flat"

strategy:
  type: "basic"

bonus_strategy:
  enabled: false
  type: "never"
"""
    print("\nLoading configuration from YAML string...")
    config = load_config_from_string(yaml_content)

    print(f"  Sessions: {config.simulation.num_sessions}")
    print(f"  Hands/Session: {config.simulation.hands_per_session}")
    print(f"  Random Seed: {config.simulation.random_seed}")
    print(f"  Workers: {config.simulation.workers}")
    print(f"  Starting Bankroll: ${config.bankroll.starting_amount:.2f}")
    print(f"  Base Bet: ${config.bankroll.base_bet:.2f}")
    print(f"  Strategy Type: {config.strategy.type}")
    print(f"  Betting System: {config.bankroll.betting_system.type}")

    # Demo 2: Load from file if available
    config_path = Path("configs/basic_strategy.yaml")
    if config_path.exists():
        print(f"\nLoading configuration from file: {config_path}")
        file_config = load_config(config_path)
        print(f"  Sessions: {file_config.simulation.num_sessions:,}")
        print(f"  Strategy: {file_config.strategy.type}")
        print(f"  Betting System: {file_config.bankroll.betting_system.type}")
    else:
        print(f"\n(Skipping file load - {config_path} not found)")

    print("=" * 60 + "\n")
    return config


def demo_rng_manager():
    """Demonstrate RNGManager for centralized seed management."""
    print("\n" + "=" * 60)
    print("RNG MANAGER DEMONSTRATION")
    print("=" * 60)

    # Create RNG manager with fixed seed for reproducibility
    rng_manager = RNGManager(base_seed=42)
    print(f"\nRNGManager created with base_seed: {rng_manager.base_seed}")

    # Demonstrate session seed generation
    print("\nPre-generating seeds for 5 sessions:")
    session_seeds = rng_manager.create_session_seeds(5)
    for session_id, seed in session_seeds.items():
        print(f"  Session {session_id}: seed = {seed}")

    # Demonstrate reproducibility - reset and regenerate
    print("\nResetting and regenerating (should be identical):")
    rng_manager.reset()
    session_seeds_2 = rng_manager.create_session_seeds(5)
    for session_id, seed in session_seeds_2.items():
        match = "✓" if seed == session_seeds[session_id] else "✗"
        print(f"  Session {session_id}: seed = {seed} {match}")

    # Demonstrate worker RNG for parallel execution
    print("\nWorker RNGs (for parallel execution):")
    for worker_id in range(3):
        worker_rng = rng_manager.create_worker_rng(worker_id)
        first_value = worker_rng.random()
        print(f"  Worker {worker_id}: first random value = {first_value:.6f}")

    # Demonstrate RNG quality validation
    print("\nRNG Quality Validation:")
    test_rng = random.Random(12345)
    quality_result = validate_rng_quality(test_rng, sample_size=10000)
    print(f"  Overall Passed: {quality_result.passed}")
    print(f"  Chi-Square Stat: {quality_result.chi_square_stat:.2f} (passed: {quality_result.chi_square_passed})")
    print(f"  Runs Test Z-Score: {quality_result.runs_test_stat:.2f} (passed: {quality_result.runs_test_passed})")
    print(f"  Sample Size: {quality_result.sample_size:,}")

    # Demonstrate state serialization
    print("\nState Serialization (for checkpointing):")
    state = rng_manager.get_state()
    print(f"  base_seed: {state['base_seed']}")
    print(f"  seed_counter: {state['seed_counter']}")
    print(f"  use_crypto: {state['use_crypto']}")

    # Restore from state
    restored_manager = RNGManager.from_state(state)
    print(f"\n  Restored manager base_seed: {restored_manager.base_seed}")

    print("=" * 60 + "\n")


def demo_simulation_controller():
    """Demonstrate SimulationController for orchestrated execution."""
    print("\n" + "=" * 60)
    print("SIMULATION CONTROLLER DEMONSTRATION")
    print("=" * 60)

    # Load a minimal configuration
    yaml_content = """
simulation:
  num_sessions: 50
  hands_per_session: 100
  random_seed: 42
  workers: 1

bankroll:
  starting_amount: 500.0
  base_bet: 5.0
  stop_conditions:
    win_limit: 100.0
    loss_limit: 100.0
    max_hands: 100
  betting_system:
    type: "flat"

strategy:
  type: "basic"

bonus_strategy:
  enabled: false
  type: "never"
"""
    config = load_config_from_string(yaml_content)

    # Create progress callback
    completed_count = [0]

    def progress_callback(completed: int, total: int) -> None:
        completed_count[0] = completed
        if completed % 10 == 0 or completed == total:
            print(f"  Progress: {completed}/{total} sessions")

    print("\nRunning simulation via SimulationController...")
    start_time = time.perf_counter()

    # Create and run controller
    controller = SimulationController(config, progress_callback=progress_callback)
    results: SimulationResults = controller.run()

    elapsed = time.perf_counter() - start_time

    print(f"\nSimulationResults:")
    print(f"  Total Sessions: {len(results.session_results)}")
    print(f"  Total Hands: {results.total_hands:,}")
    print(f"  Start Time: {results.start_time.isoformat()}")
    print(f"  End Time: {results.end_time.isoformat()}")
    print(f"  Duration: {elapsed:.2f}s")
    print(f"  Throughput: {results.total_hands / elapsed:,.0f} hands/sec")

    # Show first few session results
    print("\nFirst 5 session results:")
    for i, session_result in enumerate(results.session_results[:5]):
        print(
            f"  Session {i + 1}: {session_result.outcome.value} - "
            f"Profit: ${session_result.session_profit:+.2f}, "
            f"Hands: {session_result.hands_played}"
        )

    print("=" * 60 + "\n")
    return results


def demo_aggregate_statistics(results: SimulationResults | None = None):
    """Demonstrate AggregateStatistics for comprehensive analysis."""
    print("\n" + "=" * 60)
    print("AGGREGATE STATISTICS DEMONSTRATION")
    print("=" * 60)

    # Use provided results or generate new ones
    if results is None:
        yaml_content = """
simulation:
  num_sessions: 100
  hands_per_session: 100
  random_seed: 42
  workers: 1
bankroll:
  starting_amount: 500.0
  base_bet: 5.0
  stop_conditions:
    win_limit: 100.0
    loss_limit: 100.0
    max_hands: 100
  betting_system:
    type: "flat"
strategy:
  type: "basic"
bonus_strategy:
  enabled: false
  type: "never"
"""
        config = load_config_from_string(yaml_content)
        controller = SimulationController(config)
        results = controller.run()

    # Aggregate results
    stats: AggregateStatistics = aggregate_results(results.session_results)

    print("\nSession Outcomes:")
    print(f"  Total Sessions: {stats.total_sessions}")
    print(f"  Winning: {stats.winning_sessions} ({stats.session_win_rate * 100:.1f}%)")
    print(f"  Losing: {stats.losing_sessions}")
    print(f"  Push: {stats.push_sessions}")

    print("\nFinancial Summary:")
    print(f"  Total Wagered: ${stats.total_wagered:,.2f}")
    print(f"  Total Won: ${stats.total_won:,.2f}")
    print(f"  Net Result: ${stats.net_result:+,.2f}")
    print(f"  EV per Hand: ${stats.expected_value_per_hand:+.4f}")

    print("\nMain Game Breakdown:")
    print(f"  Main Wagered: ${stats.main_wagered:,.2f}")
    print(f"  Main Won: ${stats.main_won:,.2f}")
    print(f"  Main EV/Hand: ${stats.main_ev_per_hand:+.4f}")

    print("\nSession Profit Distribution:")
    print(f"  Mean: ${stats.session_profit_mean:+.2f}")
    print(f"  Std Dev: ${stats.session_profit_std:.2f}")
    print(f"  Median: ${stats.session_profit_median:+.2f}")
    print(f"  Min: ${stats.session_profit_min:+.2f}")
    print(f"  Max: ${stats.session_profit_max:+.2f}")

    print("\nTotal Hands: {:,}".format(stats.total_hands))

    print("=" * 60 + "\n")
    return stats


def demo_output_formatter(results: SimulationResults | None = None):
    """Demonstrate Rich-based OutputFormatter for console output."""
    print("\n" + "=" * 60)
    print("OUTPUT FORMATTER DEMONSTRATION (Rich Console)")
    print("=" * 60)

    # Use provided results or generate new ones
    if results is None:
        yaml_content = """
simulation:
  num_sessions: 50
  hands_per_session: 100
  random_seed: 42
  workers: 1
bankroll:
  starting_amount: 500.0
  base_bet: 5.0
  stop_conditions:
    win_limit: 100.0
    loss_limit: 100.0
    max_hands: 100
  betting_system:
    type: "flat"
strategy:
  type: "basic"
bonus_strategy:
  enabled: false
  type: "never"
"""
        config = load_config_from_string(yaml_content)
        controller = SimulationController(config)
        results = controller.run()

    # Calculate statistics and duration
    stats = aggregate_results(results.session_results)
    duration = (results.end_time - results.start_time).total_seconds()

    # Create formatter with different verbosity levels
    print("\n--- Verbosity Level 1 (Normal) ---")
    formatter = OutputFormatter(verbosity=1, use_color=True)
    config = results.config
    formatter.print_config_summary(config)
    formatter.print_statistics(stats, duration)
    formatter.print_completion(results.total_hands, duration)

    print("\n--- Verbosity Level 2 (Detailed) ---")
    formatter_detailed = OutputFormatter(verbosity=2, use_color=True)
    formatter_detailed.print_statistics(stats, duration)
    formatter_detailed.print_session_details(results.session_results[:5])

    print("=" * 60 + "\n")


def demo_csv_export(results: SimulationResults | None = None):
    """Demonstrate CSVExporter for results export."""
    print("\n" + "=" * 60)
    print("CSV EXPORT DEMONSTRATION")
    print("=" * 60)

    # Use provided results or generate new ones
    if results is None:
        yaml_content = """
simulation:
  num_sessions: 20
  hands_per_session: 50
  random_seed: 42
  workers: 1
bankroll:
  starting_amount: 500.0
  base_bet: 5.0
  stop_conditions:
    win_limit: 100.0
    loss_limit: 100.0
    max_hands: 50
  betting_system:
    type: "flat"
strategy:
  type: "basic"
bonus_strategy:
  enabled: false
  type: "never"
"""
        config = load_config_from_string(yaml_content)
        controller = SimulationController(config)
        results = controller.run()

    # Create temporary directory for exports
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)

        # Create exporter
        exporter = CSVExporter(output_dir, prefix="poc_demo", include_bom=True)

        print(f"\nExporting to: {output_dir}")

        # Export sessions
        sessions_path = exporter.export_sessions(results.session_results)
        print(f"\n  Sessions CSV: {sessions_path.name}")

        # Read and show first few lines
        with sessions_path.open("r", encoding="utf-8-sig") as f:
            lines = f.readlines()[:4]
            for line in lines:
                print(f"    {line.rstrip()}")

        # Export aggregate statistics
        stats = aggregate_results(results.session_results)
        aggregate_path = exporter.export_aggregate(stats)
        print(f"\n  Aggregate CSV: {aggregate_path.name}")

        # Read and show content
        with aggregate_path.open("r", encoding="utf-8-sig") as f:
            lines = f.readlines()
            # Show header and first few columns
            header = lines[0].rstrip().split(",")[:5]
            values = lines[1].rstrip().split(",")[:5]
            print(f"    Columns (first 5): {header}")
            print(f"    Values (first 5): {values}")

        # Use export_all for convenience
        print("\n  Using export_all():")
        all_paths = exporter.export_all(results, include_hands=False)
        for path in all_paths:
            print(f"    Created: {path.name}")

        print(f"\n  Total files exported: {len(all_paths)}")

    print("\n  (Temporary files cleaned up)")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  LET IT RIDE SIMULATION - PROOF OF CONCEPT")
    print("  Demonstrating All Simulation System Capabilities")
    print("=" * 70)

    # =========================================================================
    # PART 1: ORIGINAL DEMONSTRATIONS (Core Functionality)
    # =========================================================================
    print("\n" + "=" * 70)
    print("  PART 1: CORE FUNCTIONALITY DEMONSTRATIONS")
    print("=" * 70)

    # Demo single hand
    demo_single_hand()

    # Demo dealer discard
    demo_dealer_discard()

    # Demo multi-player table
    demo_multi_player_table()

    # Demo bonus strategies
    demo_bonus_strategies()

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
        betting_system_name="flat",
        random_seed=42,
        verbose=True,
    )

    # Run a larger simulation
    print("\n" + "=" * 60)
    print("LARGE SIMULATION (1000 sessions)")
    print("=" * 60)
    run_simulation(
        num_sessions=1000,
        starting_bankroll=500.0,
        base_bet=5.0,
        win_limit=250.0,
        loss_limit=200.0,
        max_hands=200,
        bonus_bet=1.0,
        strategy_name="basic",
        betting_system_name="flat",
        random_seed=42,
        verbose=True,
    )

    # Compare strategies
    compare_strategies()

    # Compare betting systems
    compare_betting_systems()

    # =========================================================================
    # PART 2: NEW FUNCTIONALITY DEMONSTRATIONS
    # =========================================================================
    print("\n" + "=" * 70)
    print("  PART 2: NEW FUNCTIONALITY DEMONSTRATIONS")
    print("=" * 70)

    # Demo YAML configuration loading
    demo_yaml_config_loading()

    # Demo RNG manager
    demo_rng_manager()

    # Demo SimulationController and reuse results for subsequent demos
    controller_results = demo_simulation_controller()

    # Demo AggregateStatistics (reuse results)
    demo_aggregate_statistics(controller_results)

    # Demo OutputFormatter (reuse results)
    demo_output_formatter(controller_results)

    # Demo CSV export (reuse results)
    demo_csv_export(controller_results)

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "=" * 70)
    print("  POC COMPLETE")
    print("=" * 70)
    print("""
Demonstrated capabilities:

CORE FUNCTIONALITY:
  - Single-player hand execution with full decision tracking
  - Dealer discard (burn card) configuration
  - Multi-player table sessions (shared community cards)
  - Multiple betting systems (Flat, Martingale, Paroli, D'Alembert, Fibonacci)
  - Multiple strategies (Basic, Conservative, Aggressive)
  - Bonus betting strategies

NEW FUNCTIONALITY:
  - YAML configuration loading (load_config, load_config_from_string)
  - RNGManager for centralized seed management
  - RNG quality validation (chi-square and runs tests)
  - SimulationController for orchestrated execution
  - AggregateStatistics for comprehensive statistical analysis
  - OutputFormatter for Rich-based console output
  - CSVExporter for results export to CSV files

Run this POC with:
  poetry run python3 scratchpads/poc_simulation.py
""")
    print("=" * 70 + "\n")
