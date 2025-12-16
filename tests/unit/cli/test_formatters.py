"""Unit tests for console output formatters.

Tests for the OutputFormatter class including:
- Configuration summary formatting
- Statistics table formatting
- Hand frequency formatting
- Session details formatting
- Color and verbosity handling
"""

from __future__ import annotations

import re
from io import StringIO
from pathlib import Path

import pytest
from rich.console import Console

from let_it_ride.cli.formatters import (
    HAND_RANK_DISPLAY,
    HAND_RANK_ORDER,
    OutputFormatter,
)
from let_it_ride.simulation.aggregation import AggregateStatistics
from let_it_ride.simulation.session import SessionOutcome, SessionResult, StopReason


@pytest.fixture
def mock_console() -> Console:
    """Create a Console that captures output for testing."""
    return Console(file=StringIO(), force_terminal=True, width=120)


@pytest.fixture
def formatter(mock_console: Console) -> OutputFormatter:
    """Create an OutputFormatter with mock console."""
    return OutputFormatter(verbosity=1, use_color=True, console=mock_console)


@pytest.fixture
def formatter_no_color(mock_console: Console) -> OutputFormatter:
    """Create an OutputFormatter without color."""
    return OutputFormatter(verbosity=1, use_color=False, console=mock_console)


@pytest.fixture
def formatter_verbose(mock_console: Console) -> OutputFormatter:
    """Create an OutputFormatter with verbose output."""
    return OutputFormatter(verbosity=2, use_color=True, console=mock_console)


@pytest.fixture
def formatter_minimal(mock_console: Console) -> OutputFormatter:
    """Create an OutputFormatter with minimal output."""
    return OutputFormatter(verbosity=0, use_color=True, console=mock_console)


@pytest.fixture
def sample_stats() -> AggregateStatistics:
    """Create sample aggregate statistics for testing."""
    return AggregateStatistics(
        total_sessions=100,
        winning_sessions=45,
        losing_sessions=50,
        push_sessions=5,
        session_win_rate=0.45,
        total_hands=10000,
        total_wagered=100000.0,
        total_won=95000.0,
        net_result=-5000.0,
        expected_value_per_hand=-0.50,
        main_wagered=90000.0,
        main_won=85000.0,
        main_ev_per_hand=-0.50,
        bonus_wagered=10000.0,
        bonus_won=10000.0,
        bonus_ev_per_hand=0.0,
        hand_frequencies={
            "high_card": 5000,
            "pair": 3000,
            "two_pair": 1500,
            "three_of_a_kind": 500,
        },
        hand_frequency_pct={
            "high_card": 0.5,
            "pair": 0.3,
            "two_pair": 0.15,
            "three_of_a_kind": 0.05,
        },
        session_profit_mean=-50.0,
        session_profit_std=150.0,
        session_profit_median=-25.0,
        session_profit_min=-500.0,
        session_profit_max=300.0,
        session_profits=tuple(range(-50, 50)),
    )


@pytest.fixture
def sample_session_results() -> list[SessionResult]:
    """Create sample session results for testing."""
    return [
        SessionResult(
            outcome=SessionOutcome.WIN,
            stop_reason=StopReason.WIN_LIMIT,
            hands_played=50,
            starting_bankroll=1000.0,
            final_bankroll=1200.0,
            session_profit=200.0,
            total_wagered=1500.0,
            total_bonus_wagered=0.0,
            peak_bankroll=1250.0,
            max_drawdown=100.0,
            max_drawdown_pct=0.08,
        ),
        SessionResult(
            outcome=SessionOutcome.LOSS,
            stop_reason=StopReason.LOSS_LIMIT,
            hands_played=75,
            starting_bankroll=1000.0,
            final_bankroll=500.0,
            session_profit=-500.0,
            total_wagered=2250.0,
            total_bonus_wagered=0.0,
            peak_bankroll=1100.0,
            max_drawdown=600.0,
            max_drawdown_pct=0.55,
        ),
        SessionResult(
            outcome=SessionOutcome.PUSH,
            stop_reason=StopReason.MAX_HANDS,
            hands_played=100,
            starting_bankroll=1000.0,
            final_bankroll=1000.0,
            session_profit=0.0,
            total_wagered=3000.0,
            total_bonus_wagered=0.0,
            peak_bankroll=1150.0,
            max_drawdown=200.0,
            max_drawdown_pct=0.17,
        ),
    ]


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    ansi_pattern = re.compile(r"\x1b\[[0-9;]*m")
    return ansi_pattern.sub("", text)


def get_console_output(console: Console) -> str:
    """Extract string output from mock console, with ANSI codes stripped."""
    file = console.file
    assert isinstance(file, StringIO)
    return strip_ansi(file.getvalue())


class TestOutputFormatterInit:
    """Tests for OutputFormatter initialization."""

    def test_default_initialization(self) -> None:
        """Test default values are set correctly."""
        formatter = OutputFormatter()
        assert formatter.verbosity == 1
        assert formatter.use_color is True
        assert formatter.console is not None

    def test_custom_verbosity(self) -> None:
        """Test custom verbosity level."""
        formatter = OutputFormatter(verbosity=2)
        assert formatter.verbosity == 2

    def test_no_color_mode(self) -> None:
        """Test color disabled mode."""
        formatter = OutputFormatter(use_color=False)
        assert formatter.use_color is False

    def test_custom_console(self, mock_console: Console) -> None:
        """Test custom console injection."""
        formatter = OutputFormatter(console=mock_console)
        assert formatter.console is mock_console


class TestColorHelper:
    """Tests for color helper methods."""

    def test_color_with_colors_enabled(self, formatter: OutputFormatter) -> None:
        """Test color markup is applied when enabled."""
        result = formatter._color("test", "green")
        assert result == "[green]test[/green]"

    def test_color_with_colors_disabled(
        self, formatter_no_color: OutputFormatter
    ) -> None:
        """Test color markup is not applied when disabled."""
        result = formatter_no_color._color("test", "green")
        assert result == "test"

    def test_no_color_output_has_no_ansi(
        self, sample_stats: AggregateStatistics
    ) -> None:
        """Test that no-color mode produces output without ANSI escape codes."""
        output = StringIO()
        # Note: force_terminal=False allows no_color to take effect
        console = Console(file=output, force_terminal=False, width=120, no_color=True)
        formatter = OutputFormatter(verbosity=1, use_color=False, console=console)

        formatter.print_statistics(sample_stats, duration_secs=10.0)

        raw_output = output.getvalue()
        # ANSI escape codes start with \x1b[
        assert "\x1b[" not in raw_output

    def test_profit_color_positive(self, formatter: OutputFormatter) -> None:
        """Test profit color for positive value."""
        assert formatter._profit_color(100.0) == "green"

    def test_profit_color_negative(self, formatter: OutputFormatter) -> None:
        """Test profit color for negative value."""
        assert formatter._profit_color(-100.0) == "red"

    def test_profit_color_zero(self, formatter: OutputFormatter) -> None:
        """Test profit color for zero value."""
        assert formatter._profit_color(0.0) == "yellow"


class TestFormatHelpers:
    """Tests for format helper methods."""

    def test_format_currency_positive(self, formatter: OutputFormatter) -> None:
        """Test currency formatting for positive value."""
        result = formatter._format_currency(1234.56)
        assert result == "$1,234.56"

    def test_format_currency_negative(self, formatter: OutputFormatter) -> None:
        """Test currency formatting for negative value."""
        result = formatter._format_currency(-1234.56)
        assert result == "$-1,234.56"

    def test_format_currency_with_sign(self, formatter: OutputFormatter) -> None:
        """Test currency formatting with sign."""
        assert formatter._format_currency(100.0, show_sign=True) == "$+100.00"
        assert formatter._format_currency(-100.0, show_sign=True) == "$-100.00"

    def test_format_percent(self, formatter: OutputFormatter) -> None:
        """Test percentage formatting."""
        assert formatter._format_percent(0.456) == "45.6%"
        assert formatter._format_percent(0.456, decimal_places=2) == "45.60%"


class TestPrintStatistics:
    """Tests for print_statistics method."""

    def test_statistics_printed_normal_verbosity(
        self,
        formatter: OutputFormatter,
        sample_stats: AggregateStatistics,
    ) -> None:
        """Test statistics are printed at normal verbosity."""
        formatter.print_statistics(sample_stats, duration_secs=10.0)
        output = get_console_output(formatter.console)

        # Check key elements are present
        assert "Session Outcomes" in output
        assert "Financial Summary" in output
        assert "Performance" in output
        assert "45" in output  # winning sessions
        assert "50" in output  # losing sessions
        assert "10,000" in output  # total hands

    def test_statistics_skipped_minimal_verbosity(
        self,
        formatter_minimal: OutputFormatter,
        sample_stats: AggregateStatistics,
    ) -> None:
        """Test statistics are skipped at minimal verbosity."""
        formatter_minimal.print_statistics(sample_stats, duration_secs=10.0)
        output = get_console_output(formatter_minimal.console)
        assert output == ""

    def test_statistics_verbose_includes_distribution(
        self,
        formatter_verbose: OutputFormatter,
        sample_stats: AggregateStatistics,
    ) -> None:
        """Test verbose mode includes profit distribution."""
        formatter_verbose.print_statistics(sample_stats, duration_secs=10.0)
        output = get_console_output(formatter_verbose.console)

        # Rich may wrap "Session Profit Distribution" across lines
        assert "Distribution" in output
        assert "Mean" in output
        assert "Std Dev" in output
        assert "Median" in output

    def test_throughput_calculation(
        self,
        formatter: OutputFormatter,
        sample_stats: AggregateStatistics,
    ) -> None:
        """Test throughput is calculated correctly."""
        formatter.print_statistics(sample_stats, duration_secs=5.0)
        output = get_console_output(formatter.console)
        # 10000 hands / 5 seconds = 2000 hands/sec
        assert "2,000 hands/sec" in output

    def test_statistics_zero_sessions(self, formatter: OutputFormatter) -> None:
        """Test statistics handles zero sessions gracefully without ZeroDivisionError."""
        zero_stats = AggregateStatistics(
            total_sessions=0,
            winning_sessions=0,
            losing_sessions=0,
            push_sessions=0,
            session_win_rate=0.0,
            total_hands=0,
            total_wagered=0.0,
            total_won=0.0,
            net_result=0.0,
            expected_value_per_hand=0.0,
            main_wagered=0.0,
            main_won=0.0,
            main_ev_per_hand=0.0,
            bonus_wagered=0.0,
            bonus_won=0.0,
            bonus_ev_per_hand=0.0,
            hand_frequencies={},
            hand_frequency_pct={},
            session_profit_mean=0.0,
            session_profit_std=0.0,
            session_profit_median=0.0,
            session_profit_min=0.0,
            session_profit_max=0.0,
            session_profits=(),
        )
        # Should not raise ZeroDivisionError
        formatter.print_statistics(zero_stats, duration_secs=1.0)
        output = get_console_output(formatter.console)
        # Should still produce output with 0% rates
        assert "0.0%" in output


class TestPrintHandFrequencies:
    """Tests for print_hand_frequencies method."""

    def test_frequencies_printed_verbose(
        self, formatter_verbose: OutputFormatter
    ) -> None:
        """Test hand frequencies are printed at verbose level."""
        frequencies = {
            "royal_flush": 1,
            "flush": 100,
            "pair": 1000,
            "high_card": 5000,
        }
        formatter_verbose.print_hand_frequencies(frequencies)
        output = get_console_output(formatter_verbose.console)

        assert "Hand Distribution" in output
        assert "Royal Flush" in output
        assert "Flush" in output
        assert "High Card" in output

    def test_frequencies_skipped_normal_verbosity(
        self, formatter: OutputFormatter
    ) -> None:
        """Test frequencies are skipped at normal verbosity."""
        frequencies = {"pair": 1000}
        formatter.print_hand_frequencies(frequencies)
        output = get_console_output(formatter.console)
        assert output == ""

    def test_empty_frequencies_skipped(
        self, formatter_verbose: OutputFormatter
    ) -> None:
        """Test empty frequencies are skipped."""
        formatter_verbose.print_hand_frequencies({})
        output = get_console_output(formatter_verbose.console)
        assert output == ""

    def test_frequencies_zero_total_skipped(
        self, formatter_verbose: OutputFormatter
    ) -> None:
        """Test frequencies with all zero counts are skipped."""
        frequencies = {"high_card": 0, "pair": 0, "two_pair": 0}
        formatter_verbose.print_hand_frequencies(frequencies)
        output = get_console_output(formatter_verbose.console)
        assert output == ""

    def test_unknown_hand_rank_displayed(
        self, formatter_verbose: OutputFormatter
    ) -> None:
        """Test unknown hand ranks are handled gracefully."""
        frequencies = {
            "high_card": 500,
            "unknown_custom_rank": 100,  # Not in HAND_RANK_ORDER
        }
        formatter_verbose.print_hand_frequencies(frequencies)
        output = get_console_output(formatter_verbose.console)

        assert "Hand Distribution" in output
        assert "High Card" in output
        # Unknown rank should be title-cased
        assert "Unknown Custom Rank" in output


class TestPrintSessionDetails:
    """Tests for print_session_details method."""

    def test_session_details_printed_verbose(
        self,
        formatter_verbose: OutputFormatter,
        sample_session_results: list[SessionResult],
    ) -> None:
        """Test session details are printed at verbose level."""
        formatter_verbose.print_session_details(sample_session_results)
        output = get_console_output(formatter_verbose.console)

        assert "Session Details" in output
        assert "win_limit" in output
        assert "loss_limit" in output
        assert "max_hands" in output

    def test_session_details_skipped_normal_verbosity(
        self,
        formatter: OutputFormatter,
        sample_session_results: list[SessionResult],
    ) -> None:
        """Test session details are skipped at normal verbosity."""
        formatter.print_session_details(sample_session_results)
        output = get_console_output(formatter.console)
        assert output == ""

    def test_session_details_empty_list(
        self, formatter_verbose: OutputFormatter
    ) -> None:
        """Test session details handles empty list gracefully."""
        formatter_verbose.print_session_details([])
        output = get_console_output(formatter_verbose.console)
        # Should print table header but no data rows
        assert "Session Details" in output


class TestPrintCompletion:
    """Tests for print_completion method."""

    def test_completion_message(self, formatter: OutputFormatter) -> None:
        """Test completion message is printed."""
        formatter.print_completion(total_hands=10000, duration_secs=5.0)
        output = get_console_output(formatter.console)

        assert "Simulation complete" in output
        assert "10,000 hands" in output
        assert "5.00s" in output
        assert "2,000 hands/sec" in output

    def test_completion_minimal_verbosity(
        self, formatter_minimal: OutputFormatter
    ) -> None:
        """Test completion at minimal verbosity shows basic message."""
        formatter_minimal.print_completion(total_hands=10000, duration_secs=5.0)
        output = get_console_output(formatter_minimal.console)
        assert "Simulation complete" in output
        # Should not include detailed stats
        assert "hands/sec" not in output


class TestPrintExportedFiles:
    """Tests for print_exported_files method."""

    def test_exported_files_printed(self, formatter: OutputFormatter) -> None:
        """Test exported files list is printed."""
        paths = [
            Path("/output/results.csv"),
            Path("/output/sessions.csv"),
        ]
        formatter.print_exported_files(paths)
        output = get_console_output(formatter.console)

        assert "Exported files" in output
        assert "results.csv" in output
        assert "sessions.csv" in output

    def test_exported_files_skipped_minimal(
        self, formatter_minimal: OutputFormatter
    ) -> None:
        """Test exported files skipped at minimal verbosity."""
        paths = [Path("/output/results.csv")]
        formatter_minimal.print_exported_files(paths)
        output = get_console_output(formatter_minimal.console)
        assert output == ""

    def test_empty_paths_skipped(self, formatter: OutputFormatter) -> None:
        """Test empty path list is skipped."""
        formatter.print_exported_files([])
        output = get_console_output(formatter.console)
        assert output == ""


class TestPrintMinimalCompletion:
    """Tests for print_minimal_completion method."""

    def test_minimal_completion(self, formatter: OutputFormatter) -> None:
        """Test minimal completion message."""
        formatter.print_minimal_completion(
            num_sessions=100,
            total_hands=10000,
            output_dir=Path("/output"),
        )
        output = get_console_output(formatter.console)

        assert "Completed 100 sessions" in output
        assert "10,000 hands" in output
        assert "Output: /output" in output


class TestPrintConfigSummary:
    """Tests for print_config_summary method."""

    def test_config_summary_normal_verbosity(self, formatter: OutputFormatter) -> None:
        """Test config summary is printed at normal verbosity."""
        from unittest.mock import MagicMock

        config = MagicMock()
        config.simulation.num_sessions = 100
        config.simulation.hands_per_session = 50
        config.simulation.random_seed = 42
        config.simulation.workers = 4
        config.table.num_seats = 1
        config.bankroll.starting_amount = 500.0
        config.bankroll.base_bet = 10.0
        config.bankroll.betting_system.type = "flat"
        config.strategy.type = "basic"
        config.bonus_strategy.type = "never"

        formatter.print_config_summary(config)
        output = get_console_output(formatter.console)

        assert "Configuration" in output
        assert "Sessions" in output
        assert "100" in output
        assert "Seed" in output
        assert "42" in output
        assert "Strategy" in output
        assert "basic" in output

    def test_config_summary_skipped_minimal_verbosity(
        self, formatter_minimal: OutputFormatter
    ) -> None:
        """Test config summary is skipped at minimal verbosity."""
        from unittest.mock import MagicMock

        config = MagicMock()
        config.simulation.num_sessions = 100
        config.simulation.hands_per_session = 50
        config.simulation.random_seed = 42
        config.simulation.workers = 4
        config.table.num_seats = 1
        config.bankroll.starting_amount = 500.0
        config.bankroll.base_bet = 10.0
        config.bankroll.betting_system.type = "flat"
        config.strategy.type = "basic"
        config.bonus_strategy.type = "never"

        formatter_minimal.print_config_summary(config)
        output = get_console_output(formatter_minimal.console)
        assert output == ""

    def test_config_summary_without_seed(self, formatter: OutputFormatter) -> None:
        """Test config summary when seed is None."""
        from unittest.mock import MagicMock

        config = MagicMock()
        config.simulation.num_sessions = 100
        config.simulation.hands_per_session = 50
        config.simulation.random_seed = None
        config.simulation.workers = 4
        config.table.num_seats = 1
        config.bankroll.starting_amount = 500.0
        config.bankroll.base_bet = 10.0
        config.bankroll.betting_system.type = "flat"
        config.strategy.type = "basic"
        config.bonus_strategy.type = "never"

        formatter.print_config_summary(config)
        output = get_console_output(formatter.console)

        # Seed row should be omitted when None
        assert "Seed" not in output


class TestConfigSummaryMultiSeat:
    """Tests for multi-seat display in config summary."""

    def test_config_summary_multi_seat_shown(self, formatter: OutputFormatter) -> None:
        """Test config summary shows table seats when num_seats > 1."""
        from unittest.mock import MagicMock

        config = MagicMock()
        config.simulation.num_sessions = 100
        config.simulation.hands_per_session = 50
        config.simulation.random_seed = 42
        config.simulation.workers = 4
        config.table.num_seats = 6
        config.bankroll.starting_amount = 500.0
        config.bankroll.base_bet = 10.0
        config.bankroll.betting_system.type = "flat"
        config.strategy.type = "basic"
        config.bonus_strategy.type = "never"

        formatter.print_config_summary(config)
        output = get_console_output(formatter.console)

        assert "Table Seats" in output
        assert "6" in output

    def test_config_summary_single_seat_hidden(
        self, formatter: OutputFormatter
    ) -> None:
        """Test config summary hides table seats when num_seats == 1."""
        from unittest.mock import MagicMock

        config = MagicMock()
        config.simulation.num_sessions = 100
        config.simulation.hands_per_session = 50
        config.simulation.random_seed = 42
        config.simulation.workers = 4
        config.table.num_seats = 1
        config.bankroll.starting_amount = 500.0
        config.bankroll.base_bet = 10.0
        config.bankroll.betting_system.type = "flat"
        config.strategy.type = "basic"
        config.bonus_strategy.type = "never"

        formatter.print_config_summary(config)
        output = get_console_output(formatter.console)

        assert "Table Seats" not in output

    def test_config_summary_multi_seat_various_counts(self) -> None:
        """Test config summary shows correct seat count for various values."""
        from unittest.mock import MagicMock

        for num_seats in [2, 3, 4, 5, 6]:
            console = Console(file=StringIO(), force_terminal=True, width=120)
            formatter = OutputFormatter(verbosity=1, use_color=True, console=console)

            config = MagicMock()
            config.simulation.num_sessions = 100
            config.simulation.hands_per_session = 50
            config.simulation.random_seed = 42
            config.simulation.workers = 4
            config.table.num_seats = num_seats
            config.bankroll.starting_amount = 500.0
            config.bankroll.base_bet = 10.0
            config.bankroll.betting_system.type = "flat"
            config.strategy.type = "basic"
            config.bonus_strategy.type = "never"

            formatter.print_config_summary(config)
            output = get_console_output(formatter.console)

            assert "Table Seats" in output
            assert str(num_seats) in output


class TestHandRankConstants:
    """Tests for hand rank constants."""

    def test_hand_rank_order_complete(self) -> None:
        """Test that hand rank order includes all expected ranks."""
        assert "royal_flush" in HAND_RANK_ORDER
        assert "high_card" in HAND_RANK_ORDER
        assert len(HAND_RANK_ORDER) >= 10

    def test_hand_rank_display_complete(self) -> None:
        """Test that display names exist for all ranks in order."""
        for rank in HAND_RANK_ORDER:
            assert rank in HAND_RANK_DISPLAY
            assert HAND_RANK_DISPLAY[rank]  # Not empty
