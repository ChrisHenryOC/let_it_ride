"""Integration tests for visualization functionality.

Tests histogram generation, file export, and configuration options.
"""

from pathlib import Path

import matplotlib
import matplotlib.figure
import pytest

from let_it_ride.analytics.visualizations import (
    HistogramConfig,
    plot_session_histogram,
    save_histogram,
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
        save_histogram(sample_session_results, output_path, format="png")

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
        save_histogram(sample_session_results, output_path, format="svg")

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
        save_histogram(sample_session_results, output_path, format="png")

        expected_path = tmp_path / "histogram.png"
        assert expected_path.exists()

    def test_creates_parent_directories(
        self, sample_session_results: list[SessionResult], tmp_path: Path
    ) -> None:
        """Test that parent directories are created if needed."""
        output_path = tmp_path / "subdir" / "nested" / "histogram.png"
        save_histogram(sample_session_results, output_path, format="png")

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
                format="pdf",  # type: ignore[arg-type]
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
        save_histogram(large_session_results, png_path, format="png", config=config)
        assert png_path.exists()

        # Generate and save SVG
        svg_path = tmp_path / "results.svg"
        save_histogram(large_session_results, svg_path, format="svg", config=config)
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
