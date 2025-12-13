#!/usr/bin/env python3
"""Profiling tools for identifying simulation hotspots.

This module uses cProfile to identify performance bottlenecks in the
simulation code.

Usage:
    poetry run python benchmarks/profile_hotspots.py
    poetry run python benchmarks/profile_hotspots.py --summary
    poetry run python benchmarks/profile_hotspots.py --output profile.prof
"""

from __future__ import annotations

import argparse
import cProfile
import io
import pstats
from pstats import SortKey

from let_it_ride.config.models import (
    BankrollConfig,
    BettingSystemConfig,
    FullConfig,
    SimulationConfig,
    StopConditionsConfig,
    StrategyConfig,
)
from let_it_ride.simulation import SimulationController


def create_benchmark_config(
    num_sessions: int = 1_000,
    hands_per_session: int = 100,
    workers: int = 1,  # Single worker for accurate profiling
) -> FullConfig:
    """Create a config for profiling."""
    return FullConfig(
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


def profile_simulation(
    num_sessions: int = 1_000,
    hands_per_session: int = 100,
    top_n: int = 30,
) -> str:
    """Profile simulation and return formatted stats.

    Uses single-threaded execution for accurate profiling.

    Args:
        num_sessions: Number of sessions to run
        hands_per_session: Hands per session
        top_n: Number of top functions to display

    Returns:
        Formatted profiling statistics string
    """
    config = create_benchmark_config(num_sessions, hands_per_session, workers=1)
    controller = SimulationController(config)

    # Profile the simulation
    profiler = cProfile.Profile()
    profiler.enable()
    results = controller.run()
    profiler.disable()

    # Format results
    output = io.StringIO()
    stats = pstats.Stats(profiler, stream=output)
    stats.strip_dirs()

    output.write("\n" + "=" * 80 + "\n")
    output.write("PROFILE: CUMULATIVE TIME (sorted by cumulative time)\n")
    output.write(f"Sessions: {num_sessions:,}, Hands: {results.total_hands:,}\n")
    output.write("=" * 80 + "\n")

    stats.sort_stats(SortKey.CUMULATIVE)
    stats.print_stats(top_n)

    output.write("\n" + "=" * 80 + "\n")
    output.write("PROFILE: TOTAL TIME (sorted by total time in function)\n")
    output.write("=" * 80 + "\n")

    stats.sort_stats(SortKey.TIME)
    stats.print_stats(top_n)

    output.write("\n" + "=" * 80 + "\n")
    output.write("PROFILE: CALL COUNT (sorted by number of calls)\n")
    output.write("=" * 80 + "\n")

    stats.sort_stats(SortKey.CALLS)
    stats.print_stats(top_n)

    return output.getvalue()


def profile_to_file(
    output_path: str = "profile_output.prof",
    num_sessions: int = 1_000,
    hands_per_session: int = 100,
) -> None:
    """Run profiler and save binary output for external visualization.

    The .prof file can be opened with:
    - snakeviz: `snakeviz profile_output.prof`
    - gprof2dot: `gprof2dot -f pstats profile_output.prof | dot -Tpng -o profile.png`

    Args:
        output_path: Path to save the profile data
        num_sessions: Number of sessions to run
        hands_per_session: Hands per session
    """
    config = create_benchmark_config(num_sessions, hands_per_session, workers=1)
    controller = SimulationController(config)

    # Profile and save to file
    profiler = cProfile.Profile()
    profiler.enable()
    controller.run()
    profiler.disable()

    profiler.dump_stats(output_path)
    print(f"Profile data saved to: {output_path}")
    print("Visualize with: snakeviz " + output_path)


def identify_hotspots(
    num_sessions: int = 1_000,
    hands_per_session: int = 100,
) -> list[tuple[str, float, int]]:
    """Identify the top hotspot functions.

    Returns list of (function_name, cumulative_time_percent, call_count) tuples,
    sorted by cumulative time.
    """
    config = create_benchmark_config(num_sessions, hands_per_session, workers=1)
    controller = SimulationController(config)

    profiler = cProfile.Profile()
    profiler.enable()
    controller.run()
    profiler.disable()

    stats = pstats.Stats(profiler)
    stats.strip_dirs()

    # Access the internal stats dict (type: ignore for pstats internal API)
    stats_dict = stats.stats  # type: ignore[attr-defined]

    # Get total time
    total_time = sum(stat[3] for stat in stats_dict.values())  # cumulative time

    # Extract hotspots
    hotspots = []
    for func, stat in stats_dict.items():
        _, _, func_name = func
        cumtime = stat[3]
        ncalls = stat[0]
        percent = (cumtime / total_time * 100) if total_time > 0 else 0
        hotspots.append((func_name, percent, ncalls))

    # Sort by cumulative time percentage
    hotspots.sort(key=lambda x: x[1], reverse=True)

    return hotspots[:20]


def print_hotspot_summary() -> None:
    """Print a summary of hotspots for quick analysis."""
    print("\n" + "=" * 80)
    print("HOTSPOT SUMMARY")
    print("=" * 80)

    hotspots = identify_hotspots(num_sessions=500, hands_per_session=100)

    print(f"\n{'Function':<50} {'Time %':>10} {'Calls':>12}")
    print("-" * 74)

    for func_name, percent, calls in hotspots:
        print(f"{func_name:<50} {percent:>9.1f}% {calls:>12,}")

    print("-" * 74)
    print("\nFocus optimization efforts on functions with highest time %")


def main() -> None:
    """Run profiling based on command line arguments."""
    parser = argparse.ArgumentParser(
        description="Profile Let It Ride simulation for hotspots"
    )
    parser.add_argument(
        "--sessions",
        type=int,
        default=1_000,
        help="Number of sessions to simulate (default: 1000)",
    )
    parser.add_argument(
        "--hands",
        type=int,
        default=100,
        help="Hands per session (default: 100)",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Save profile to file for external visualization",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print only hotspot summary (default: full profile)",
    )

    args = parser.parse_args()

    if args.output:
        profile_to_file(args.output, args.sessions, args.hands)
    elif args.summary:
        print_hotspot_summary()
    else:
        print(profile_simulation(args.sessions, args.hands))
        print_hotspot_summary()


if __name__ == "__main__":
    main()
