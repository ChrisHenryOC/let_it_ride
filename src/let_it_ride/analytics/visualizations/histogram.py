"""Session outcome histogram visualization.

This module provides histogram visualization of session profit/loss distribution.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import matplotlib.figure
import matplotlib.pyplot as plt
import numpy as np
from numpy.typing import NDArray

from let_it_ride.simulation.session import SessionOutcome, SessionResult


@dataclass(slots=True)
class HistogramConfig:
    """Configuration for session outcome histogram visualization.

    Attributes:
        bins: Number of bins or binning strategy. Can be an integer for fixed
            bin count, or "auto" for automatic bin selection using numpy's
            histogram_bin_edges with the "auto" algorithm.
        figsize: Figure size as (width, height) in inches.
        dpi: Resolution in dots per inch for rasterized output.
        show_mean: Whether to display a vertical line at the mean.
        show_median: Whether to display a vertical line at the median.
        show_zero_line: Whether to display a vertical line at zero (break-even).
        title: Chart title.
        xlabel: Label for the x-axis.
        ylabel: Label for the y-axis.
    """

    bins: int | str = "auto"
    figsize: tuple[float, float] = (10, 6)
    dpi: int = 150
    show_mean: bool = True
    show_median: bool = True
    show_zero_line: bool = True
    title: str = "Session Outcome Distribution"
    xlabel: str = "Session Profit/Loss ($)"
    ylabel: str = "Frequency"


def _calculate_win_rate(results: list[SessionResult]) -> float:
    """Calculate the percentage of winning sessions.

    Args:
        results: List of session results.

    Returns:
        Win rate as a percentage (0-100).
    """
    if not results:
        return 0.0
    wins = sum(1 for r in results if r.outcome == SessionOutcome.WIN)
    return (wins / len(results)) * 100


def _get_bin_colors(
    bin_edges: NDArray[np.floating[Any]],
) -> list[str]:
    """Determine colors for histogram bins based on profit/loss.

    Args:
        bin_edges: Array of bin edge values.

    Returns:
        List of color strings for each bin.
    """
    colors: list[str] = []
    for i in range(len(bin_edges) - 1):
        left_edge = bin_edges[i]
        right_edge = bin_edges[i + 1]
        bin_center = (left_edge + right_edge) / 2

        if bin_center > 0:
            colors.append("#2ecc71")  # Green for profit
        elif bin_center < 0:
            colors.append("#e74c3c")  # Red for loss
        else:
            colors.append("#95a5a6")  # Gray for break-even

    return colors


def plot_session_histogram(
    results: list[SessionResult],
    config: HistogramConfig | None = None,
) -> matplotlib.figure.Figure:
    """Generate a histogram of session profit/loss distribution.

    Creates a histogram visualization with:
    - Color-coded bins (green for profit, red for loss)
    - Optional mean and median marker lines
    - Optional zero (break-even) line
    - Win rate annotation

    Args:
        results: List of session results to visualize.
        config: Histogram configuration. Uses defaults if not provided.

    Returns:
        Matplotlib Figure object containing the histogram.

    Raises:
        ValueError: If results list is empty.
    """
    if not results:
        raise ValueError("Cannot create histogram from empty results list")

    if config is None:
        config = HistogramConfig()

    # Extract profit values
    profits = np.array([r.session_profit for r in results])

    # Calculate statistics
    mean_profit = float(np.mean(profits))
    median_profit = float(np.median(profits))
    win_rate = _calculate_win_rate(results)

    # Create figure and axes
    fig, ax = plt.subplots(figsize=config.figsize)

    # Calculate bin edges
    bin_edges = np.histogram_bin_edges(profits, bins=config.bins)

    # Calculate histogram values for coloring
    counts, _ = np.histogram(profits, bins=bin_edges)

    # Get colors for each bin
    colors = _get_bin_colors(bin_edges)

    # Plot histogram bars manually for individual coloring
    for i in range(len(counts)):
        ax.bar(
            x=(bin_edges[i] + bin_edges[i + 1]) / 2,
            height=counts[i],
            width=bin_edges[i + 1] - bin_edges[i],
            color=colors[i],
            edgecolor="white",
            linewidth=0.5,
            alpha=0.8,
        )

    # Add zero line (break-even)
    if config.show_zero_line:
        ax.axvline(
            x=0,
            color="black",
            linestyle="-",
            linewidth=2,
            label="Break-even",
            zorder=5,
        )

    # Add mean line
    if config.show_mean:
        ax.axvline(
            x=mean_profit,
            color="#3498db",
            linestyle="--",
            linewidth=2,
            label=f"Mean: ${mean_profit:,.2f}",
            zorder=5,
        )

    # Add median line
    if config.show_median:
        ax.axvline(
            x=median_profit,
            color="#e67e22",
            linestyle="--",
            linewidth=2,
            label=f"Median: ${median_profit:,.2f}",
            zorder=5,
        )

    # Add win rate annotation
    ax.annotate(
        f"Win Rate: {win_rate:.1f}%\nSessions: {len(results):,}",
        xy=(0.98, 0.98),
        xycoords="axes fraction",
        ha="right",
        va="top",
        fontsize=10,
        bbox={"boxstyle": "round,pad=0.5", "facecolor": "white", "alpha": 0.8},
    )

    # Set labels and title
    ax.set_xlabel(config.xlabel, fontsize=11)
    ax.set_ylabel(config.ylabel, fontsize=11)
    ax.set_title(config.title, fontsize=13, fontweight="bold")

    # Add legend only if there are labeled artists
    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(loc="upper left", fontsize=9)

    # Add grid for readability
    ax.grid(axis="y", alpha=0.3, linestyle="-")
    ax.set_axisbelow(True)

    # Tight layout
    fig.tight_layout()

    return fig


def save_histogram(
    results: list[SessionResult],
    path: Path,
    format: Literal["png", "svg"] = "png",
    config: HistogramConfig | None = None,
) -> None:
    """Generate and save a session outcome histogram to file.

    Args:
        results: List of session results to visualize.
        path: Output file path. Extension will be added if not present.
        format: Output format, either "png" or "svg".
        config: Histogram configuration. Uses defaults if not provided.

    Raises:
        ValueError: If results list is empty or format is invalid.
    """
    if format not in ("png", "svg"):
        raise ValueError(f"Invalid format '{format}'. Must be 'png' or 'svg'.")

    if config is None:
        config = HistogramConfig()

    # Ensure path has correct extension
    path = Path(path)
    if path.suffix.lower() != f".{format}":
        path = path.with_suffix(f".{format}")

    # Create parent directories if needed
    path.parent.mkdir(parents=True, exist_ok=True)

    # Generate and save figure
    fig = plot_session_histogram(results, config)
    fig.savefig(path, format=format, dpi=config.dpi, bbox_inches="tight")
    plt.close(fig)
