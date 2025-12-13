"""Integration tests for visualization functionality.

Tests histogram and trajectory generation, file export, and configuration options.
"""

from pathlib import Path

import matplotlib
import matplotlib.figure
import pytest

from let_it_ride.analytics.visualizations import (
    HistogramConfig,
    TrajectoryConfig,
    plot_bankroll_trajectories,
    plot_session_histogram,
    save_histogram,
    save_trajectory_chart,
)
from let_it_ride.simulation.session import SessionOutcome, SessionResult, StopReason


@pytest.fixture
def sample_session_results() -> list[SessionResult]:
    """Create sample session results with varied outcomes for testing."""
    return [
        # Winning sessions
        SessionResult(
            outcome=SessionOutcome.WIN,
            stop_reason=StopReason.WIN_LIMIT,
            hands_played=25,
            starting_bankroll=500.0,
            final_bankroll=600.0,
            session_profit=100.0,
            total_wagered=750.0,
            total_bonus_wagered=0.0,
            peak_bankroll=620.0,
            max_drawdown=50.0,
            max_drawdown_pct=0.08,
        ),
        SessionResult(
            outcome=SessionOutcome.WIN,
            stop_reason=StopReason.WIN_LIMIT,
            hands_played=30,
            starting_bankroll=500.0,
            final_bankroll=650.0,
            session_profit=150.0,
            total_wagered=900.0,
            total_bonus_wagered=0.0,
            peak_bankroll=660.0,
            max_drawdown=40.0,
            max_drawdown_pct=0.06,
        ),
        SessionResult(
            outcome=SessionOutcome.WIN,
            stop_reason=StopReason.MAX_HANDS,
            hands_played=50,
            starting_bankroll=500.0,
            final_bankroll=525.0,
            session_profit=25.0,
            total_wagered=1500.0,
            total_bonus_wagered=0.0,
            peak_bankroll=560.0,
            max_drawdown=60.0,
            max_drawdown_pct=0.11,
        ),
        # Losing sessions
        SessionResult(
            outcome=SessionOutcome.LOSS,
            stop_reason=StopReason.LOSS_LIMIT,
            hands_played=40,
            starting_bankroll=500.0,
            final_bankroll=300.0,
            session_profit=-200.0,
            total_wagered=1200.0,
            total_bonus_wagered=0.0,
            peak_bankroll=550.0,
            max_drawdown=250.0,
            max_drawdown_pct=0.45,
        ),
        SessionResult(
            outcome=SessionOutcome.LOSS,
            stop_reason=StopReason.INSUFFICIENT_FUNDS,
            hands_played=60,
            starting_bankroll=500.0,
            final_bankroll=50.0,
            session_profit=-450.0,
            total_wagered=1800.0,
            total_bonus_wagered=0.0,
            peak_bankroll=520.0,
            max_drawdown=470.0,
            max_drawdown_pct=0.90,
        ),
        # Push session
        SessionResult(
            outcome=SessionOutcome.PUSH,
            stop_reason=StopReason.MAX_HANDS,
            hands_played=50,
            starting_bankroll=500.0,
            final_bankroll=500.0,
            session_profit=0.0,
            total_wagered=1500.0,
            total_bonus_wagered=0.0,
            peak_bankroll=580.0,
            max_drawdown=80.0,
            max_drawdown_pct=0.14,
        ),
    ]


@pytest.fixture
def large_session_results() -> list[SessionResult]:
    """Create a larger set of session results for thorough testing."""
    results = []
    # Generate 100 sessions with varying profits
    for i in range(100):
        # Alternate between wins and losses with some randomness
        if i % 3 == 0:
            profit = 50.0 + (i % 10) * 10  # Wins: 50-140
            outcome = SessionOutcome.WIN
            stop_reason = StopReason.WIN_LIMIT
        elif i % 3 == 1:
            profit = -30.0 - (i % 10) * 15  # Losses: -30 to -165
            outcome = SessionOutcome.LOSS
            stop_reason = StopReason.LOSS_LIMIT
        else:
            profit = -10.0 + (i % 5) * 5  # Mixed: -10 to 10
            if profit > 0:
                outcome = SessionOutcome.WIN
            elif profit < 0:
                outcome = SessionOutcome.LOSS
            else:
                outcome = SessionOutcome.PUSH
            stop_reason = StopReason.MAX_HANDS

        results.append(
            SessionResult(
                outcome=outcome,
                stop_reason=stop_reason,
                hands_played=25 + i,
                starting_bankroll=500.0,
                final_bankroll=500.0 + profit,
                session_profit=profit,
                total_wagered=750.0 + i * 30,
                total_bonus_wagered=0.0,
                peak_bankroll=550.0 + max(0, profit),
                max_drawdown=abs(min(0, profit)),
                max_drawdown_pct=abs(min(0, profit)) / 500.0,
            )
        )
    return results


class TestPlotSessionHistogram:
    """Tests for plot_session_histogram function."""

    def test_creates_figure(self, sample_session_results: list[SessionResult]) -> None:
        """Test that function returns a matplotlib Figure."""
        fig = plot_session_histogram(sample_session_results)

        assert isinstance(fig, matplotlib.figure.Figure)
        matplotlib.pyplot.close(fig)

    def test_empty_results_raises_error(self) -> None:
        """Test that empty results list raises ValueError."""
        with pytest.raises(ValueError, match="empty results list"):
            plot_session_histogram([])

    def test_default_config(self, sample_session_results: list[SessionResult]) -> None:
        """Test that default configuration produces valid figure."""
        fig = plot_session_histogram(sample_session_results)

        # Check figure has one axes
        assert len(fig.axes) == 1
        ax = fig.axes[0]

        # Check title is set
        assert ax.get_title() == "Session Outcome Distribution"

        # Check axis labels
        assert "Profit" in ax.get_xlabel()
        assert "Frequency" in ax.get_ylabel()

        matplotlib.pyplot.close(fig)

    def test_custom_config(self, sample_session_results: list[SessionResult]) -> None:
        """Test custom configuration is applied."""
        config = HistogramConfig(
            bins=5,
            figsize=(12, 8),
            title="Custom Title",
            xlabel="Custom X",
            ylabel="Custom Y",
            show_mean=False,
            show_median=False,
            show_zero_line=False,
        )
        fig = plot_session_histogram(sample_session_results, config)
        ax = fig.axes[0]

        assert ax.get_title() == "Custom Title"
        assert ax.get_xlabel() == "Custom X"
        assert ax.get_ylabel() == "Custom Y"

        matplotlib.pyplot.close(fig)

    def test_mean_median_markers(
        self, sample_session_results: list[SessionResult]
    ) -> None:
        """Test that mean and median markers are added when enabled."""
        config = HistogramConfig(show_mean=True, show_median=True)
        fig = plot_session_histogram(sample_session_results, config)
        ax = fig.axes[0]

        # Check legend contains mean and median labels
        legend_texts = [t.get_text() for t in ax.get_legend().get_texts()]
        mean_label = [t for t in legend_texts if "Mean" in t]
        median_label = [t for t in legend_texts if "Median" in t]

        assert len(mean_label) == 1
        assert len(median_label) == 1

        matplotlib.pyplot.close(fig)

    def test_zero_line_marker(
        self, sample_session_results: list[SessionResult]
    ) -> None:
        """Test that zero line is added when enabled."""
        config = HistogramConfig(show_zero_line=True)
        fig = plot_session_histogram(sample_session_results, config)
        ax = fig.axes[0]

        # Check legend contains break-even label
        legend_texts = [t.get_text() for t in ax.get_legend().get_texts()]
        breakeven_label = [t for t in legend_texts if "Break-even" in t]

        assert len(breakeven_label) == 1

        matplotlib.pyplot.close(fig)

    def test_win_rate_annotation(
        self, sample_session_results: list[SessionResult]
    ) -> None:
        """Test that win rate annotation is present."""
        fig = plot_session_histogram(sample_session_results)
        ax = fig.axes[0]

        # Find annotation text
        annotations = ax.texts
        win_rate_annotations = [a for a in annotations if "Win Rate" in a.get_text()]

        assert len(win_rate_annotations) == 1
        # With 3 wins out of 6 sessions, win rate is 50%
        assert "50.0%" in win_rate_annotations[0].get_text()

        matplotlib.pyplot.close(fig)

    def test_large_dataset(self, large_session_results: list[SessionResult]) -> None:
        """Test histogram generation with larger dataset."""
        fig = plot_session_histogram(large_session_results)

        assert isinstance(fig, matplotlib.figure.Figure)
        matplotlib.pyplot.close(fig)

    def test_auto_bins(self, large_session_results: list[SessionResult]) -> None:
        """Test automatic bin selection."""
        config = HistogramConfig(bins="auto")
        fig = plot_session_histogram(large_session_results, config)

        assert isinstance(fig, matplotlib.figure.Figure)
        matplotlib.pyplot.close(fig)

    def test_fixed_bin_count(self, sample_session_results: list[SessionResult]) -> None:
        """Test fixed bin count configuration."""
        config = HistogramConfig(bins=10)
        fig = plot_session_histogram(sample_session_results, config)

        assert isinstance(fig, matplotlib.figure.Figure)
        matplotlib.pyplot.close(fig)


class TestSaveHistogram:
    """Tests for save_histogram function."""

    def test_save_png(
        self, sample_session_results: list[SessionResult], tmp_path: Path
    ) -> None:
        """Test saving histogram as PNG file."""
        output_path = tmp_path / "histogram.png"
        save_histogram(sample_session_results, output_path, output_format="png")

        assert output_path.exists()
        assert output_path.stat().st_size > 0
        # Check PNG magic bytes
        with output_path.open("rb") as f:
            magic = f.read(8)
        assert magic[:4] == b"\x89PNG"

    def test_save_svg(
        self, sample_session_results: list[SessionResult], tmp_path: Path
    ) -> None:
        """Test saving histogram as SVG file."""
        output_path = tmp_path / "histogram.svg"
        save_histogram(sample_session_results, output_path, output_format="svg")

        assert output_path.exists()
        assert output_path.stat().st_size > 0
        # Check SVG content
        content = output_path.read_text()
        assert "<svg" in content

    def test_adds_extension(
        self, sample_session_results: list[SessionResult], tmp_path: Path
    ) -> None:
        """Test that correct extension is added if missing."""
        output_path = tmp_path / "histogram"
        save_histogram(sample_session_results, output_path, output_format="png")

        expected_path = tmp_path / "histogram.png"
        assert expected_path.exists()

    def test_creates_parent_directories(
        self, sample_session_results: list[SessionResult], tmp_path: Path
    ) -> None:
        """Test that parent directories are created if needed."""
        output_path = tmp_path / "subdir" / "nested" / "histogram.png"
        save_histogram(sample_session_results, output_path, output_format="png")

        assert output_path.exists()

    def test_invalid_format_raises_error(
        self, sample_session_results: list[SessionResult], tmp_path: Path
    ) -> None:
        """Test that invalid format raises ValueError."""
        output_path = tmp_path / "histogram.pdf"
        with pytest.raises(ValueError, match="Invalid format"):
            save_histogram(
                sample_session_results,
                output_path,
                output_format="pdf",  # type: ignore[arg-type]
            )

    def test_custom_dpi(
        self, sample_session_results: list[SessionResult], tmp_path: Path
    ) -> None:
        """Test custom DPI setting affects output."""
        low_dpi_path = tmp_path / "low_dpi.png"
        high_dpi_path = tmp_path / "high_dpi.png"

        save_histogram(
            sample_session_results,
            low_dpi_path,
            config=HistogramConfig(dpi=72),
        )
        save_histogram(
            sample_session_results,
            high_dpi_path,
            config=HistogramConfig(dpi=300),
        )

        # Higher DPI should produce larger file
        assert high_dpi_path.stat().st_size > low_dpi_path.stat().st_size

    def test_custom_figsize(
        self, sample_session_results: list[SessionResult], tmp_path: Path
    ) -> None:
        """Test custom figure size affects output."""
        small_path = tmp_path / "small.png"
        large_path = tmp_path / "large.png"

        save_histogram(
            sample_session_results,
            small_path,
            config=HistogramConfig(figsize=(5, 3), dpi=100),
        )
        save_histogram(
            sample_session_results,
            large_path,
            config=HistogramConfig(figsize=(15, 10), dpi=100),
        )

        # Larger figure should produce larger file
        assert large_path.stat().st_size > small_path.stat().st_size


class TestHistogramConfig:
    """Tests for HistogramConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = HistogramConfig()

        assert config.bins == "auto"
        assert config.figsize == (10, 6)
        assert config.dpi == 150
        assert config.show_mean is True
        assert config.show_median is True
        assert config.show_zero_line is True
        assert config.title == "Session Outcome Distribution"

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = HistogramConfig(
            bins=20,
            figsize=(8, 6),
            dpi=200,
            show_mean=False,
            show_median=False,
            show_zero_line=False,
            title="Custom Histogram",
            xlabel="Net Profit",
            ylabel="Count",
        )

        assert config.bins == 20
        assert config.figsize == (8, 6)
        assert config.dpi == 200
        assert config.show_mean is False
        assert config.show_median is False
        assert config.show_zero_line is False
        assert config.title == "Custom Histogram"
        assert config.xlabel == "Net Profit"
        assert config.ylabel == "Count"


class TestHistogramIntegration:
    """End-to-end integration tests."""

    def test_full_workflow(
        self, large_session_results: list[SessionResult], tmp_path: Path
    ) -> None:
        """Test complete workflow from data to saved file."""
        config = HistogramConfig(
            bins=15,
            figsize=(12, 8),
            dpi=150,
            title="Simulation Results - 100 Sessions",
            show_mean=True,
            show_median=True,
            show_zero_line=True,
        )

        # Generate and save PNG
        png_path = tmp_path / "results.png"
        save_histogram(
            large_session_results, png_path, output_format="png", config=config
        )
        assert png_path.exists()

        # Generate and save SVG
        svg_path = tmp_path / "results.svg"
        save_histogram(
            large_session_results, svg_path, output_format="svg", config=config
        )
        assert svg_path.exists()

        # Verify both files have content
        assert png_path.stat().st_size > 10000  # PNG should be substantial
        assert svg_path.stat().st_size > 1000  # SVG should have content

    def test_all_wins(self) -> None:
        """Test histogram with all winning sessions."""
        results = [
            SessionResult(
                outcome=SessionOutcome.WIN,
                stop_reason=StopReason.WIN_LIMIT,
                hands_played=25,
                starting_bankroll=500.0,
                final_bankroll=600.0 + i * 10,
                session_profit=100.0 + i * 10,
                total_wagered=750.0,
                total_bonus_wagered=0.0,
                peak_bankroll=620.0,
                max_drawdown=50.0,
                max_drawdown_pct=0.08,
            )
            for i in range(10)
        ]

        fig = plot_session_histogram(results)
        ax = fig.axes[0]

        # Win rate should be 100%
        annotations = [a for a in ax.texts if "Win Rate" in a.get_text()]
        assert "100.0%" in annotations[0].get_text()

        matplotlib.pyplot.close(fig)

    def test_all_losses(self) -> None:
        """Test histogram with all losing sessions."""
        results = [
            SessionResult(
                outcome=SessionOutcome.LOSS,
                stop_reason=StopReason.LOSS_LIMIT,
                hands_played=40,
                starting_bankroll=500.0,
                final_bankroll=300.0 - i * 10,
                session_profit=-200.0 - i * 10,
                total_wagered=1200.0,
                total_bonus_wagered=0.0,
                peak_bankroll=550.0,
                max_drawdown=250.0,
                max_drawdown_pct=0.45,
            )
            for i in range(10)
        ]

        fig = plot_session_histogram(results)
        ax = fig.axes[0]

        # Win rate should be 0%
        annotations = [a for a in ax.texts if "Win Rate" in a.get_text()]
        assert "0.0%" in annotations[0].get_text()

        matplotlib.pyplot.close(fig)

    def test_all_pushes(self) -> None:
        """Test histogram with all push (break-even) sessions."""
        results = [
            SessionResult(
                outcome=SessionOutcome.PUSH,
                stop_reason=StopReason.MAX_HANDS,
                hands_played=50,
                starting_bankroll=500.0,
                final_bankroll=500.0,
                session_profit=0.0,
                total_wagered=1500.0,
                total_bonus_wagered=0.0,
                peak_bankroll=550.0,
                max_drawdown=50.0,
                max_drawdown_pct=0.10,
            )
            for _ in range(10)
        ]

        fig = plot_session_histogram(results)
        ax = fig.axes[0]

        # Win rate should be 0%
        annotations = [a for a in ax.texts if "Win Rate" in a.get_text()]
        assert "0.0%" in annotations[0].get_text()

        matplotlib.pyplot.close(fig)

    def test_single_session_result(self) -> None:
        """Test histogram with single session result edge case."""
        results = [
            SessionResult(
                outcome=SessionOutcome.WIN,
                stop_reason=StopReason.WIN_LIMIT,
                hands_played=25,
                starting_bankroll=500.0,
                final_bankroll=600.0,
                session_profit=100.0,
                total_wagered=750.0,
                total_bonus_wagered=0.0,
                peak_bankroll=620.0,
                max_drawdown=50.0,
                max_drawdown_pct=0.08,
            )
        ]

        fig = plot_session_histogram(results)
        assert isinstance(fig, matplotlib.figure.Figure)

        ax = fig.axes[0]
        # Win rate should be 100% with 1 session
        annotations = [a for a in ax.texts if "Win Rate" in a.get_text()]
        assert "100.0%" in annotations[0].get_text()
        assert "1" in annotations[0].get_text()  # Sessions count

        matplotlib.pyplot.close(fig)

    def test_identical_profit_values(self) -> None:
        """Test histogram when all sessions have identical profit values."""
        results = [
            SessionResult(
                outcome=SessionOutcome.WIN,
                stop_reason=StopReason.WIN_LIMIT,
                hands_played=25,
                starting_bankroll=500.0,
                final_bankroll=550.0,
                session_profit=50.0,  # All identical
                total_wagered=750.0,
                total_bonus_wagered=0.0,
                peak_bankroll=560.0,
                max_drawdown=20.0,
                max_drawdown_pct=0.04,
            )
            for _ in range(10)
        ]

        fig = plot_session_histogram(results)
        assert isinstance(fig, matplotlib.figure.Figure)

        ax = fig.axes[0]
        # Mean and median should be identical (both $50)
        legend_texts = [t.get_text() for t in ax.get_legend().get_texts()]
        mean_labels = [t for t in legend_texts if "Mean" in t]
        median_labels = [t for t in legend_texts if "Median" in t]

        assert len(mean_labels) == 1
        assert len(median_labels) == 1
        # Both should show $50.00
        assert "$50.00" in mean_labels[0]
        assert "$50.00" in median_labels[0]

        matplotlib.pyplot.close(fig)


# ============================================================================
# Bankroll Trajectory Tests
# ============================================================================


@pytest.fixture
def sample_trajectories() -> tuple[list[SessionResult], list[list[float]]]:
    """Create sample session results with corresponding bankroll histories."""
    results = [
        # Winning session - steady climb
        SessionResult(
            outcome=SessionOutcome.WIN,
            stop_reason=StopReason.WIN_LIMIT,
            hands_played=5,
            starting_bankroll=500.0,
            final_bankroll=600.0,
            session_profit=100.0,
            total_wagered=150.0,
            total_bonus_wagered=0.0,
            peak_bankroll=600.0,
            max_drawdown=20.0,
            max_drawdown_pct=0.04,
        ),
        # Losing session - steady decline
        SessionResult(
            outcome=SessionOutcome.LOSS,
            stop_reason=StopReason.LOSS_LIMIT,
            hands_played=5,
            starting_bankroll=500.0,
            final_bankroll=400.0,
            session_profit=-100.0,
            total_wagered=150.0,
            total_bonus_wagered=0.0,
            peak_bankroll=520.0,
            max_drawdown=120.0,
            max_drawdown_pct=0.23,
        ),
        # Push session - back to start
        SessionResult(
            outcome=SessionOutcome.PUSH,
            stop_reason=StopReason.MAX_HANDS,
            hands_played=5,
            starting_bankroll=500.0,
            final_bankroll=500.0,
            session_profit=0.0,
            total_wagered=150.0,
            total_bonus_wagered=0.0,
            peak_bankroll=550.0,
            max_drawdown=50.0,
            max_drawdown_pct=0.09,
        ),
    ]
    histories = [
        # Win: 500 -> 520 -> 540 -> 560 -> 580 -> 600
        [520.0, 540.0, 560.0, 580.0, 600.0],
        # Loss: 500 -> 480 -> 460 -> 440 -> 420 -> 400
        [480.0, 460.0, 440.0, 420.0, 400.0],
        # Push: 500 -> 520 -> 510 -> 490 -> 510 -> 500
        [520.0, 510.0, 490.0, 510.0, 500.0],
    ]
    return results, histories


@pytest.fixture
def large_trajectories() -> tuple[list[SessionResult], list[list[float]]]:
    """Create a larger set of session results with histories for sampling tests."""
    results = []
    histories = []

    for i in range(50):
        # Alternate outcomes
        if i % 3 == 0:
            profit = 100.0
            outcome = SessionOutcome.WIN
            stop_reason = StopReason.WIN_LIMIT
        elif i % 3 == 1:
            profit = -100.0
            outcome = SessionOutcome.LOSS
            stop_reason = StopReason.LOSS_LIMIT
        else:
            profit = 0.0
            outcome = SessionOutcome.PUSH
            stop_reason = StopReason.MAX_HANDS

        results.append(
            SessionResult(
                outcome=outcome,
                stop_reason=stop_reason,
                hands_played=10,
                starting_bankroll=500.0,
                final_bankroll=500.0 + profit,
                session_profit=profit,
                total_wagered=300.0,
                total_bonus_wagered=0.0,
                peak_bankroll=550.0,
                max_drawdown=abs(min(0.0, profit)),
                max_drawdown_pct=abs(min(0.0, profit)) / 500.0,
            )
        )

        # Create a simple history of 10 hands
        step = profit / 10
        history = [500.0 + step * (j + 1) for j in range(10)]
        histories.append(history)

    return results, histories


class TestPlotBankrollTrajectories:
    """Tests for plot_bankroll_trajectories function."""

    def test_creates_figure(
        self, sample_trajectories: tuple[list[SessionResult], list[list[float]]]
    ) -> None:
        """Test that function returns a matplotlib Figure."""
        results, histories = sample_trajectories
        fig = plot_bankroll_trajectories(results, histories)

        assert isinstance(fig, matplotlib.figure.Figure)
        matplotlib.pyplot.close(fig)

    def test_empty_results_raises_error(self) -> None:
        """Test that empty results list raises ValueError."""
        with pytest.raises(ValueError, match="empty results list"):
            plot_bankroll_trajectories([], [])

    def test_mismatched_lengths_raises_error(
        self, sample_trajectories: tuple[list[SessionResult], list[list[float]]]
    ) -> None:
        """Test that mismatched results/histories lengths raises ValueError."""
        results, histories = sample_trajectories
        with pytest.raises(ValueError, match="same length"):
            plot_bankroll_trajectories(results, histories[:-1])

    def test_default_config(
        self, sample_trajectories: tuple[list[SessionResult], list[list[float]]]
    ) -> None:
        """Test that default configuration produces valid figure."""
        results, histories = sample_trajectories
        fig = plot_bankroll_trajectories(results, histories)

        assert len(fig.axes) == 1
        ax = fig.axes[0]

        # Check title is set
        assert ax.get_title() == "Bankroll Trajectories"

        # Check axis labels
        assert "Hands" in ax.get_xlabel()
        assert "Bankroll" in ax.get_ylabel()

        matplotlib.pyplot.close(fig)

    def test_custom_config(
        self, sample_trajectories: tuple[list[SessionResult], list[list[float]]]
    ) -> None:
        """Test custom configuration is applied."""
        results, histories = sample_trajectories
        config = TrajectoryConfig(
            figsize=(10, 8),
            title="Custom Trajectory Title",
            xlabel="Hand Number",
            ylabel="Balance ($)",
            alpha=0.8,
            show_limits=False,
        )
        fig = plot_bankroll_trajectories(results, histories, config=config)
        ax = fig.axes[0]

        assert ax.get_title() == "Custom Trajectory Title"
        assert ax.get_xlabel() == "Hand Number"
        assert ax.get_ylabel() == "Balance ($)"

        matplotlib.pyplot.close(fig)

    def test_win_limit_line(
        self, sample_trajectories: tuple[list[SessionResult], list[list[float]]]
    ) -> None:
        """Test that win limit reference line is added when enabled."""
        results, histories = sample_trajectories
        config = TrajectoryConfig(show_limits=True)
        fig = plot_bankroll_trajectories(
            results, histories, config=config, win_limit=100.0
        )
        ax = fig.axes[0]

        legend_texts = [t.get_text() for t in ax.get_legend().get_texts()]
        win_limit_label = [t for t in legend_texts if "Win Limit" in t]

        assert len(win_limit_label) == 1
        assert "600" in win_limit_label[0]  # 500 + 100

        matplotlib.pyplot.close(fig)

    def test_loss_limit_line(
        self, sample_trajectories: tuple[list[SessionResult], list[list[float]]]
    ) -> None:
        """Test that loss limit reference line is added when enabled."""
        results, histories = sample_trajectories
        config = TrajectoryConfig(show_limits=True)
        fig = plot_bankroll_trajectories(
            results, histories, config=config, loss_limit=100.0
        )
        ax = fig.axes[0]

        legend_texts = [t.get_text() for t in ax.get_legend().get_texts()]
        loss_limit_label = [t for t in legend_texts if "Loss Limit" in t]

        assert len(loss_limit_label) == 1
        assert "400" in loss_limit_label[0]  # 500 - 100

        matplotlib.pyplot.close(fig)

    def test_starting_bankroll_line(
        self, sample_trajectories: tuple[list[SessionResult], list[list[float]]]
    ) -> None:
        """Test that starting bankroll baseline is always shown."""
        results, histories = sample_trajectories
        fig = plot_bankroll_trajectories(results, histories)
        ax = fig.axes[0]

        legend_texts = [t.get_text() for t in ax.get_legend().get_texts()]
        start_label = [t for t in legend_texts if "Start" in t]

        assert len(start_label) == 1
        assert "500" in start_label[0]

        matplotlib.pyplot.close(fig)

    def test_annotation_shows_session_count(
        self, sample_trajectories: tuple[list[SessionResult], list[list[float]]]
    ) -> None:
        """Test that annotation shows session count."""
        results, histories = sample_trajectories
        fig = plot_bankroll_trajectories(results, histories)
        ax = fig.axes[0]

        annotations = ax.texts
        count_annotations = [a for a in annotations if "3" in a.get_text()]

        assert len(count_annotations) >= 1

        matplotlib.pyplot.close(fig)

    def test_outcome_colors_in_legend(
        self, sample_trajectories: tuple[list[SessionResult], list[list[float]]]
    ) -> None:
        """Test that win, loss, and push outcomes appear in legend."""
        results, histories = sample_trajectories
        fig = plot_bankroll_trajectories(results, histories)
        ax = fig.axes[0]

        legend_texts = [t.get_text() for t in ax.get_legend().get_texts()]

        assert any("Win" in t for t in legend_texts)
        assert any("Loss" in t for t in legend_texts)
        assert any("Push" in t for t in legend_texts)

        matplotlib.pyplot.close(fig)

    def test_sampling_with_seed(
        self, large_trajectories: tuple[list[SessionResult], list[list[float]]]
    ) -> None:
        """Test that random seed produces reproducible sampling."""
        results, histories = large_trajectories
        config = TrajectoryConfig(sample_sessions=10, random_seed=42)

        fig1 = plot_bankroll_trajectories(results, histories, config=config)
        fig2 = plot_bankroll_trajectories(results, histories, config=config)

        # Both should produce the same annotation text (same sessions sampled)
        ax1 = fig1.axes[0]
        ax2 = fig2.axes[0]

        ann1 = [a.get_text() for a in ax1.texts]
        ann2 = [a.get_text() for a in ax2.texts]

        assert ann1 == ann2

        matplotlib.pyplot.close(fig1)
        matplotlib.pyplot.close(fig2)

    def test_sampling_limits_displayed_sessions(
        self, large_trajectories: tuple[list[SessionResult], list[list[float]]]
    ) -> None:
        """Test that sample_sessions limits the number of trajectories plotted."""
        results, histories = large_trajectories
        config = TrajectoryConfig(sample_sessions=5)
        fig = plot_bankroll_trajectories(results, histories, config=config)
        ax = fig.axes[0]

        # Annotation should show "5 of 50"
        annotations = ax.texts
        display_ann = [a for a in annotations if "5 of 50" in a.get_text()]

        assert len(display_ann) == 1

        matplotlib.pyplot.close(fig)

    def test_no_sampling_when_fewer_sessions(
        self, sample_trajectories: tuple[list[SessionResult], list[list[float]]]
    ) -> None:
        """Test that all sessions shown when fewer than sample_sessions."""
        results, histories = sample_trajectories
        config = TrajectoryConfig(sample_sessions=100)  # More than we have
        fig = plot_bankroll_trajectories(results, histories, config=config)
        ax = fig.axes[0]

        # Should show "3 of 3"
        annotations = ax.texts
        display_ann = [a for a in annotations if "3 of 3" in a.get_text()]

        assert len(display_ann) == 1

        matplotlib.pyplot.close(fig)


class TestSaveTrajectoryChart:
    """Tests for save_trajectory_chart function."""

    def test_save_png(
        self,
        sample_trajectories: tuple[list[SessionResult], list[list[float]]],
        tmp_path: Path,
    ) -> None:
        """Test saving trajectory chart as PNG file."""
        results, histories = sample_trajectories
        output_path = tmp_path / "trajectory.png"
        save_trajectory_chart(results, histories, output_path, output_format="png")

        assert output_path.exists()
        assert output_path.stat().st_size > 0
        # Check PNG magic bytes
        with output_path.open("rb") as f:
            magic = f.read(8)
        assert magic[:4] == b"\x89PNG"

    def test_save_svg(
        self,
        sample_trajectories: tuple[list[SessionResult], list[list[float]]],
        tmp_path: Path,
    ) -> None:
        """Test saving trajectory chart as SVG file."""
        results, histories = sample_trajectories
        output_path = tmp_path / "trajectory.svg"
        save_trajectory_chart(results, histories, output_path, output_format="svg")

        assert output_path.exists()
        assert output_path.stat().st_size > 0
        # Check SVG content
        content = output_path.read_text()
        assert "<svg" in content

    def test_adds_extension(
        self,
        sample_trajectories: tuple[list[SessionResult], list[list[float]]],
        tmp_path: Path,
    ) -> None:
        """Test that correct extension is added if missing."""
        results, histories = sample_trajectories
        output_path = tmp_path / "trajectory"
        save_trajectory_chart(results, histories, output_path, output_format="png")

        expected_path = tmp_path / "trajectory.png"
        assert expected_path.exists()

    def test_creates_parent_directories(
        self,
        sample_trajectories: tuple[list[SessionResult], list[list[float]]],
        tmp_path: Path,
    ) -> None:
        """Test that parent directories are created if needed."""
        results, histories = sample_trajectories
        output_path = tmp_path / "subdir" / "nested" / "trajectory.png"
        save_trajectory_chart(results, histories, output_path, output_format="png")

        assert output_path.exists()

    def test_invalid_format_raises_error(
        self,
        sample_trajectories: tuple[list[SessionResult], list[list[float]]],
        tmp_path: Path,
    ) -> None:
        """Test that invalid format raises ValueError."""
        results, histories = sample_trajectories
        output_path = tmp_path / "trajectory.pdf"
        with pytest.raises(ValueError, match="Invalid format"):
            save_trajectory_chart(
                results,
                histories,
                output_path,
                output_format="pdf",  # type: ignore[arg-type]
            )

    def test_with_limits(
        self,
        sample_trajectories: tuple[list[SessionResult], list[list[float]]],
        tmp_path: Path,
    ) -> None:
        """Test saving with win and loss limits."""
        results, histories = sample_trajectories
        output_path = tmp_path / "trajectory_limits.png"
        save_trajectory_chart(
            results,
            histories,
            output_path,
            output_format="png",
            win_limit=100.0,
            loss_limit=100.0,
        )

        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_custom_dpi(
        self,
        sample_trajectories: tuple[list[SessionResult], list[list[float]]],
        tmp_path: Path,
    ) -> None:
        """Test custom DPI setting affects output."""
        results, histories = sample_trajectories
        low_dpi_path = tmp_path / "low_dpi.png"
        high_dpi_path = tmp_path / "high_dpi.png"

        save_trajectory_chart(
            results,
            histories,
            low_dpi_path,
            config=TrajectoryConfig(dpi=72),
        )
        save_trajectory_chart(
            results,
            histories,
            high_dpi_path,
            config=TrajectoryConfig(dpi=300),
        )

        # Higher DPI should produce larger file
        assert high_dpi_path.stat().st_size > low_dpi_path.stat().st_size


class TestTrajectoryConfig:
    """Tests for TrajectoryConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = TrajectoryConfig()

        assert config.sample_sessions == 20
        assert config.figsize == (12, 6)
        assert config.dpi == 150
        assert config.show_limits is True
        assert config.alpha == 0.6
        assert config.title == "Bankroll Trajectories"
        assert config.random_seed is None

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = TrajectoryConfig(
            sample_sessions=10,
            figsize=(8, 6),
            dpi=200,
            show_limits=False,
            alpha=0.8,
            title="Custom Trajectory",
            xlabel="Hand #",
            ylabel="Balance",
            random_seed=42,
        )

        assert config.sample_sessions == 10
        assert config.figsize == (8, 6)
        assert config.dpi == 200
        assert config.show_limits is False
        assert config.alpha == 0.8
        assert config.title == "Custom Trajectory"
        assert config.xlabel == "Hand #"
        assert config.ylabel == "Balance"
        assert config.random_seed == 42


class TestTrajectoryIntegration:
    """End-to-end integration tests for trajectory visualization."""

    def test_full_workflow(
        self,
        large_trajectories: tuple[list[SessionResult], list[list[float]]],
        tmp_path: Path,
    ) -> None:
        """Test complete workflow from data to saved file."""
        results, histories = large_trajectories
        config = TrajectoryConfig(
            sample_sessions=15,
            figsize=(14, 8),
            dpi=150,
            title="Simulation Bankroll Trajectories",
            show_limits=True,
            alpha=0.5,
            random_seed=123,
        )

        # Generate and save PNG
        png_path = tmp_path / "trajectories.png"
        save_trajectory_chart(
            results,
            histories,
            png_path,
            output_format="png",
            config=config,
            win_limit=100.0,
            loss_limit=100.0,
        )
        assert png_path.exists()

        # Generate and save SVG
        svg_path = tmp_path / "trajectories.svg"
        save_trajectory_chart(
            results,
            histories,
            svg_path,
            output_format="svg",
            config=config,
            win_limit=100.0,
            loss_limit=100.0,
        )
        assert svg_path.exists()

        # Verify both files have content
        assert png_path.stat().st_size > 10000
        assert svg_path.stat().st_size > 1000

    def test_single_session(self) -> None:
        """Test trajectory with single session."""
        results = [
            SessionResult(
                outcome=SessionOutcome.WIN,
                stop_reason=StopReason.WIN_LIMIT,
                hands_played=3,
                starting_bankroll=500.0,
                final_bankroll=600.0,
                session_profit=100.0,
                total_wagered=90.0,
                total_bonus_wagered=0.0,
                peak_bankroll=600.0,
                max_drawdown=0.0,
                max_drawdown_pct=0.0,
            )
        ]
        histories = [[520.0, 560.0, 600.0]]

        fig = plot_bankroll_trajectories(results, histories)
        assert isinstance(fig, matplotlib.figure.Figure)

        ax = fig.axes[0]
        annotations = [a for a in ax.texts if "1 of 1" in a.get_text()]
        assert len(annotations) == 1

        matplotlib.pyplot.close(fig)

    def test_all_wins(self) -> None:
        """Test trajectory with all winning sessions."""
        results = [
            SessionResult(
                outcome=SessionOutcome.WIN,
                stop_reason=StopReason.WIN_LIMIT,
                hands_played=3,
                starting_bankroll=500.0,
                final_bankroll=600.0 + i * 10,
                session_profit=100.0 + i * 10,
                total_wagered=90.0,
                total_bonus_wagered=0.0,
                peak_bankroll=600.0 + i * 10,
                max_drawdown=0.0,
                max_drawdown_pct=0.0,
            )
            for i in range(5)
        ]
        histories = [[520.0, 560.0, 600.0 + i * 10] for i in range(5)]

        fig = plot_bankroll_trajectories(results, histories)
        ax = fig.axes[0]

        legend_texts = [t.get_text() for t in ax.get_legend().get_texts()]
        # Should only have "Win" outcome, not "Loss" or "Push"
        assert any("Win" in t for t in legend_texts)
        assert not any("Loss" in t for t in legend_texts)
        assert not any("Push" in t for t in legend_texts)

        matplotlib.pyplot.close(fig)

    def test_empty_history_entries(self) -> None:
        """Test with valid but short history lists."""
        results = [
            SessionResult(
                outcome=SessionOutcome.WIN,
                stop_reason=StopReason.WIN_LIMIT,
                hands_played=1,
                starting_bankroll=500.0,
                final_bankroll=550.0,
                session_profit=50.0,
                total_wagered=30.0,
                total_bonus_wagered=0.0,
                peak_bankroll=550.0,
                max_drawdown=0.0,
                max_drawdown_pct=0.0,
            )
        ]
        histories = [[550.0]]  # Single entry

        fig = plot_bankroll_trajectories(results, histories)
        assert isinstance(fig, matplotlib.figure.Figure)

        matplotlib.pyplot.close(fig)
