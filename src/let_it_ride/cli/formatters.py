"""Console output formatting for Let It Ride simulations.

This module provides formatted console output using Rich library:
- Configuration summaries
- Statistics tables with colorized metrics
- Hand frequency distribution tables
- Session details for verbose mode
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.console import Console
from rich.table import Table

if TYPE_CHECKING:
    from pathlib import Path

    from let_it_ride.config.models import FullConfig
    from let_it_ride.simulation.aggregation import AggregateStatistics
    from let_it_ride.simulation.session import SessionResult


# Hand rank display order (strongest to weakest)
HAND_RANK_ORDER = [
    "royal_flush",
    "straight_flush",
    "four_of_a_kind",
    "full_house",
    "flush",
    "straight",
    "three_of_a_kind",
    "two_pair",
    "pair_tens_or_better",
    "pair",
    "high_card",
]

# Display names for hand ranks
HAND_RANK_DISPLAY = {
    "royal_flush": "Royal Flush",
    "straight_flush": "Straight Flush",
    "four_of_a_kind": "Four of a Kind",
    "full_house": "Full House",
    "flush": "Flush",
    "straight": "Straight",
    "three_of_a_kind": "Three of a Kind",
    "two_pair": "Two Pair",
    "pair_tens_or_better": "Pair (10s+)",
    "pair": "Pair (Low)",
    "high_card": "High Card",
}


class OutputFormatter:
    """Formats simulation output for console display.

    Provides Rich-based formatting for simulation results with support
    for multiple verbosity levels and optional color output.

    Attributes:
        verbosity: Output detail level (0=minimal, 1=normal, 2=detailed).
        use_color: Whether to use color output.
        console: Rich Console instance for output.
    """

    __slots__ = ("verbosity", "use_color", "console")

    def __init__(
        self,
        verbosity: int = 1,
        use_color: bool = True,
        console: Console | None = None,
    ) -> None:
        """Initialize output formatter.

        Args:
            verbosity: Output detail level (0=minimal, 1=normal, 2=detailed).
            use_color: Whether to use color output.
            console: Optional Rich Console instance. Creates new one if not provided.
        """
        self.verbosity = verbosity
        self.use_color = use_color
        self.console = console or Console(no_color=not use_color)

    def _color(self, text: str, color: str) -> str:
        """Apply color markup if colors are enabled.

        Args:
            text: Text to colorize.
            color: Rich color name (e.g., "green", "red", "yellow").

        Returns:
            Text with Rich color markup if colors enabled, otherwise plain text.
        """
        if self.use_color:
            return f"[{color}]{text}[/{color}]"
        return text

    def _profit_color(self, value: float) -> str:
        """Get color for a profit/loss value.

        Args:
            value: Profit (positive) or loss (negative) amount.

        Returns:
            Rich color name: "green" for profit, "red" for loss, "yellow" for zero.
        """
        if value > 0:
            return "green"
        elif value < 0:
            return "red"
        return "yellow"

    def _format_currency(self, value: float, show_sign: bool = False) -> str:
        """Format a value as currency.

        Args:
            value: Amount to format.
            show_sign: If True, include +/- sign for non-zero values.

        Returns:
            Formatted currency string.
        """
        if show_sign:
            return f"${value:+,.2f}"
        return f"${value:,.2f}"

    def _format_percent(self, value: float, decimal_places: int = 1) -> str:
        """Format a value as percentage.

        Args:
            value: Decimal value (0.0 to 1.0).
            decimal_places: Number of decimal places to show.

        Returns:
            Formatted percentage string.
        """
        return f"{value * 100:.{decimal_places}f}%"

    def print_config_summary(self, config: FullConfig) -> None:
        """Display configuration summary at start of simulation.

        Args:
            config: Simulation configuration.
        """
        if self.verbosity < 1:
            return

        table = Table(title="Configuration", show_header=False, box=None)
        table.add_column("Setting", style="dim")
        table.add_column("Value")

        # Simulation settings
        table.add_row("Sessions", f"{config.simulation.num_sessions:,}")
        table.add_row("Hands/Session", f"{config.simulation.hands_per_session:,}")
        if config.simulation.random_seed is not None:
            table.add_row("Seed", str(config.simulation.random_seed))
        table.add_row("Workers", str(config.simulation.workers))

        # Table settings (only show if multi-seat)
        if config.table.num_seats > 1:
            table.add_row("", "")  # Separator
            table.add_row("Table Seats", str(config.table.num_seats))

        # Bankroll settings
        table.add_row("", "")  # Separator
        table.add_row(
            "Starting Bankroll", self._format_currency(config.bankroll.starting_amount)
        )
        table.add_row("Base Bet", self._format_currency(config.bankroll.base_bet))
        table.add_row("Betting System", config.bankroll.betting_system.type)

        # Strategy settings
        table.add_row("", "")  # Separator
        table.add_row("Strategy", config.strategy.type)
        table.add_row("Bonus Strategy", config.bonus_strategy.type)

        self.console.print(table)
        self.console.print()

    def print_statistics(
        self,
        stats: AggregateStatistics,
        duration_secs: float,
    ) -> None:
        """Display summary statistics table after completion.

        Args:
            stats: Aggregate statistics from simulation.
            duration_secs: Total simulation duration in seconds.
        """
        if self.verbosity < 1:
            return

        # Session outcomes table
        session_table = Table(title="Session Outcomes", box=None)
        session_table.add_column("Outcome", style="dim")
        session_table.add_column("Count", justify="right")
        session_table.add_column("Rate", justify="right")

        win_rate_str = self._format_percent(stats.session_win_rate)
        loss_rate = (
            stats.losing_sessions / stats.total_sessions
            if stats.total_sessions > 0
            else 0
        )
        push_rate = (
            stats.push_sessions / stats.total_sessions
            if stats.total_sessions > 0
            else 0
        )

        session_table.add_row(
            self._color("Winning", "green"),
            f"{stats.winning_sessions:,}",
            self._color(win_rate_str, "green"),
        )
        session_table.add_row(
            self._color("Losing", "red"),
            f"{stats.losing_sessions:,}",
            self._color(self._format_percent(loss_rate), "red"),
        )
        session_table.add_row(
            self._color("Push", "yellow"),
            f"{stats.push_sessions:,}",
            self._color(self._format_percent(push_rate), "yellow"),
        )

        self.console.print(session_table)
        self.console.print()

        # Financial summary table
        financial_table = Table(title="Financial Summary", box=None)
        financial_table.add_column("Metric", style="dim")
        financial_table.add_column("Value", justify="right")

        net_color = self._profit_color(stats.net_result)
        ev_color = self._profit_color(stats.expected_value_per_hand)

        financial_table.add_row(
            "Total Wagered", self._format_currency(stats.total_wagered)
        )
        financial_table.add_row("Total Won", self._format_currency(stats.total_won))
        financial_table.add_row(
            "Net Result",
            self._color(
                self._format_currency(stats.net_result, show_sign=True), net_color
            ),
        )
        financial_table.add_row(
            "EV/Hand",
            self._color(
                self._format_currency(stats.expected_value_per_hand, show_sign=True),
                ev_color,
            ),
        )

        self.console.print(financial_table)
        self.console.print()

        # Session profit distribution
        if self.verbosity >= 2:
            dist_table = Table(title="Session Profit Distribution", box=None)
            dist_table.add_column("Metric", style="dim")
            dist_table.add_column("Value", justify="right")

            dist_table.add_row(
                "Mean", self._format_currency(stats.session_profit_mean, show_sign=True)
            )
            dist_table.add_row(
                "Std Dev", self._format_currency(stats.session_profit_std)
            )
            dist_table.add_row(
                "Median",
                self._format_currency(stats.session_profit_median, show_sign=True),
            )
            dist_table.add_row(
                "Min", self._format_currency(stats.session_profit_min, show_sign=True)
            )
            dist_table.add_row(
                "Max", self._format_currency(stats.session_profit_max, show_sign=True)
            )

            self.console.print(dist_table)
            self.console.print()

        # Performance metrics
        hands_per_sec = stats.total_hands / duration_secs if duration_secs > 0 else 0
        perf_table = Table(title="Performance", box=None)
        perf_table.add_column("Metric", style="dim")
        perf_table.add_column("Value", justify="right")

        perf_table.add_row("Total Hands", f"{stats.total_hands:,}")
        perf_table.add_row("Duration", f"{duration_secs:.2f}s")
        perf_table.add_row("Throughput", f"{hands_per_sec:,.0f} hands/sec")

        self.console.print(perf_table)
        self.console.print()

    def print_hand_frequencies(self, frequencies: dict[str, int]) -> None:
        """Display hand frequency distribution table.

        Args:
            frequencies: Dictionary mapping hand rank to count.
        """
        if self.verbosity < 2 or not frequencies:
            return

        total = sum(frequencies.values())
        if total == 0:
            return

        table = Table(title="Hand Distribution", box=None)
        table.add_column("Hand Rank")
        table.add_column("Count", justify="right")
        table.add_column("Frequency", justify="right")

        # Display in rank order
        displayed_ranks: set[str] = set()
        for rank in HAND_RANK_ORDER:
            count = frequencies.get(rank, 0)
            if count > 0:
                pct = count / total
                display_name = HAND_RANK_DISPLAY.get(rank, rank)
                table.add_row(display_name, f"{count:,}", self._format_percent(pct, 2))
            displayed_ranks.add(rank)

        # Handle any unknown ranks not in HAND_RANK_ORDER (defensive)
        for rank, count in frequencies.items():
            if rank not in displayed_ranks and count > 0:
                pct = count / total
                display_name = rank.replace("_", " ").title()
                table.add_row(display_name, f"{count:,}", self._format_percent(pct, 2))

        self.console.print(table)
        self.console.print()

    def print_session_details(self, results: list[SessionResult]) -> None:
        """Display per-session details (verbose mode only).

        Args:
            results: List of session results.
        """
        if self.verbosity < 2:
            return

        table = Table(title="Session Details", box=None)
        table.add_column("#", justify="right", style="dim")
        table.add_column("Profit", justify="right")
        table.add_column("Hands", justify="right")
        table.add_column("Stop Reason")

        for i, result in enumerate(results, 1):
            color = self._profit_color(result.session_profit)
            profit_str = self._color(
                self._format_currency(result.session_profit, show_sign=True),
                color,
            )
            table.add_row(
                str(i),
                profit_str,
                f"{result.hands_played:,}",
                result.stop_reason.value,
            )

        self.console.print(table)
        self.console.print()

    def print_completion(self, total_hands: int, duration_secs: float) -> None:
        """Display completion message with throughput stats.

        Args:
            total_hands: Total number of hands simulated.
            duration_secs: Total simulation duration in seconds.
        """
        hands_per_sec = total_hands / duration_secs if duration_secs > 0 else 0
        msg = self._color("Simulation complete!", "green")
        self.console.print(msg)
        if self.verbosity >= 1:
            self.console.print(
                f"Processed {total_hands:,} hands in {duration_secs:.2f}s "
                f"({hands_per_sec:,.0f} hands/sec)"
            )
        self.console.print()

    def print_exported_files(self, paths: list[Path]) -> None:
        """Display list of exported files.

        Args:
            paths: List of exported file paths.
        """
        if self.verbosity < 1 or not paths:
            return

        self.console.print(self._color("Exported files:", "bold"))
        for path in paths:
            self.console.print(f"  {path}")
        self.console.print()

    def print_minimal_completion(
        self,
        num_sessions: int,
        total_hands: int,
        output_dir: Path,
    ) -> None:
        """Display minimal completion message (quiet mode).

        Args:
            num_sessions: Number of sessions completed.
            total_hands: Total number of hands simulated.
            output_dir: Output directory path.
        """
        self.console.print(f"Completed {num_sessions} sessions, {total_hands:,} hands")
        self.console.print(f"Output: {output_dir}")
