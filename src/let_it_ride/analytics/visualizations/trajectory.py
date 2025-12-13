"""Bankroll trajectory visualization.

This module provides line chart visualization of bankroll trajectories
over the course of sample sessions.
"""

import random
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import matplotlib.figure
import matplotlib.pyplot as plt

from let_it_ride.simulation.session import SessionOutcome, SessionResult

# Color palette consistent with histogram.py
PROFIT_COLOR = "#2ecc71"  # Green for winning sessions
LOSS_COLOR = "#e74c3c"  # Red for losing sessions
BREAKEVEN_COLOR = "#95a5a6"  # Gray for push sessions
LIMIT_COLOR = "#3498db"  # Blue for reference lines
BASELINE_COLOR = "#2c3e50"  # Dark blue-gray for starting bankroll


@dataclass(slots=True)
class TrajectoryConfig:
    """Configuration for bankroll trajectory visualization.

    Attributes:
        sample_sessions: Number of sample sessions to display on the chart.
            If fewer sessions are available, all will be shown.
        figsize: Figure size as (width, height) in inches.
        dpi: Resolution in dots per inch for rasterized output.
        show_limits: Whether to display win/loss limit reference lines.
        alpha: Line transparency (0.0 to 1.0) for overlapping trajectories.
        title: Chart title.
        xlabel: Label for the x-axis.
        ylabel: Label for the y-axis.
        random_seed: Seed for reproducible session sampling. None for random.
    """

    sample_sessions: int = 20
    figsize: tuple[float, float] = (12, 6)
    dpi: int = 150
    show_limits: bool = True
    alpha: float = 0.6
    title: str = "Bankroll Trajectories"
    xlabel: str = "Hands Played"
    ylabel: str = "Bankroll ($)"
    random_seed: int | None = None


def _get_outcome_color(outcome: SessionOutcome) -> str:
    """Get the line color for a session based on its outcome.

    Args:
        outcome: The session outcome (WIN, LOSS, or PUSH).

    Returns:
        Hex color string for the outcome.
    """
    if outcome == SessionOutcome.WIN:
        return PROFIT_COLOR
    elif outcome == SessionOutcome.LOSS:
        return LOSS_COLOR
    return BREAKEVEN_COLOR


def _sample_sessions(
    results: list[SessionResult],
    histories: list[list[float]],
    n_samples: int,
    random_seed: int | None,
) -> tuple[list[SessionResult], list[list[float]]]:
    """Sample a subset of sessions for display.

    Args:
        results: Full list of session results.
        histories: Full list of bankroll histories (parallel to results).
        n_samples: Number of samples to select.
        random_seed: Random seed for reproducibility. None for random selection.

    Returns:
        Tuple of (sampled_results, sampled_histories).
    """
    if len(results) <= n_samples:
        return results, histories

    if random_seed is not None:
        random.seed(random_seed)

    indices = random.sample(range(len(results)), n_samples)
    sampled_results = [results[i] for i in indices]
    sampled_histories = [histories[i] for i in indices]
    return sampled_results, sampled_histories


def plot_bankroll_trajectories(
    results: list[SessionResult],
    bankroll_histories: list[list[float]],
    config: TrajectoryConfig | None = None,
    win_limit: float | None = None,
    loss_limit: float | None = None,
) -> matplotlib.figure.Figure:
    """Generate a line chart of bankroll trajectories for sample sessions.

    Creates a multi-line chart visualization with:
    - Color-coded lines based on session outcome (green=win, red=loss, gray=push)
    - Optional horizontal reference lines for win/loss limits
    - Starting bankroll baseline
    - Legend with outcome counts

    Args:
        results: List of session results to visualize.
        bankroll_histories: List of bankroll history lists, one per session.
            Each history should contain the bankroll value after each hand.
            Must be the same length as results.
        config: Trajectory configuration. Uses defaults if not provided.
        win_limit: Win limit amount (profit target). If provided and show_limits
            is True, a horizontal line will be drawn at starting_bankroll + win_limit.
        loss_limit: Loss limit amount (stop loss, positive value). If provided and
            show_limits is True, a horizontal line will be drawn at
            starting_bankroll - loss_limit.

    Returns:
        Matplotlib Figure object containing the trajectory chart.

    Raises:
        ValueError: If results list is empty or if results and histories
            have different lengths.
    """
    if not results:
        raise ValueError("Cannot create trajectory chart from empty results list")

    if len(results) != len(bankroll_histories):
        raise ValueError(
            f"Results and histories must have same length. "
            f"Got {len(results)} results and {len(bankroll_histories)} histories."
        )

    if config is None:
        config = TrajectoryConfig()

    # Sample sessions if we have more than the configured limit
    sampled_results, sampled_histories = _sample_sessions(
        results, bankroll_histories, config.sample_sessions, config.random_seed
    )

    # Get starting bankroll from first session (assume all have same starting bankroll)
    starting_bankroll = sampled_results[0].starting_bankroll

    # Create figure and axes
    fig, ax = plt.subplots(figsize=config.figsize)

    # Track outcomes for legend
    wins_plotted = False
    losses_plotted = False
    pushes_plotted = False

    # Plot each trajectory
    for result, history in zip(sampled_results, sampled_histories, strict=True):
        color = _get_outcome_color(result.outcome)

        # Build x values (hand numbers starting at 0 for initial bankroll)
        # Prepend starting bankroll to history for complete trajectory
        full_history = [starting_bankroll, *history]
        x_values = list(range(len(full_history)))

        # Set label only once per outcome type for legend
        label = None
        if result.outcome == SessionOutcome.WIN and not wins_plotted:
            label = "Win"
            wins_plotted = True
        elif result.outcome == SessionOutcome.LOSS and not losses_plotted:
            label = "Loss"
            losses_plotted = True
        elif result.outcome == SessionOutcome.PUSH and not pushes_plotted:
            label = "Push"
            pushes_plotted = True

        ax.plot(
            x_values,
            full_history,
            color=color,
            alpha=config.alpha,
            linewidth=1.5,
            label=label,
        )

    # Add reference lines
    # Starting bankroll baseline
    ax.axhline(
        y=starting_bankroll,
        color=BASELINE_COLOR,
        linestyle="-",
        linewidth=2,
        label=f"Start: ${starting_bankroll:,.0f}",
        zorder=5,
    )

    # Win and loss limit lines
    if config.show_limits:
        if win_limit is not None:
            win_threshold = starting_bankroll + win_limit
            ax.axhline(
                y=win_threshold,
                color=PROFIT_COLOR,
                linestyle="--",
                linewidth=2,
                label=f"Win Limit: ${win_threshold:,.0f}",
                zorder=5,
            )

        if loss_limit is not None:
            loss_threshold = starting_bankroll - loss_limit
            ax.axhline(
                y=loss_threshold,
                color=LOSS_COLOR,
                linestyle="--",
                linewidth=2,
                label=f"Loss Limit: ${loss_threshold:,.0f}",
                zorder=5,
            )

    # Add annotation with sample info
    total_sessions = len(results)
    displayed = len(sampled_results)
    win_count = sum(1 for r in sampled_results if r.outcome == SessionOutcome.WIN)
    loss_count = sum(1 for r in sampled_results if r.outcome == SessionOutcome.LOSS)
    push_count = displayed - win_count - loss_count

    annotation_text = f"Showing {displayed} of {total_sessions:,} sessions\n"
    annotation_text += f"W: {win_count} | L: {loss_count} | P: {push_count}"

    ax.annotate(
        annotation_text,
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

    # Add legend
    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(loc="upper left", fontsize=9)

    # Add grid for readability
    ax.grid(axis="both", alpha=0.3, linestyle="-")
    ax.set_axisbelow(True)

    # Tight layout
    fig.tight_layout()

    return fig


def save_trajectory_chart(
    results: list[SessionResult],
    bankroll_histories: list[list[float]],
    path: Path,
    output_format: Literal["png", "svg"] = "png",
    config: TrajectoryConfig | None = None,
    win_limit: float | None = None,
    loss_limit: float | None = None,
) -> None:
    """Generate and save a bankroll trajectory chart to file.

    Args:
        results: List of session results to visualize.
        bankroll_histories: List of bankroll history lists, one per session.
        path: Output file path. Extension will be added if not present.
        output_format: Output format, either "png" or "svg".
        config: Trajectory configuration. Uses defaults if not provided.
        win_limit: Win limit amount (profit target).
        loss_limit: Loss limit amount (stop loss, positive value).

    Raises:
        ValueError: If results list is empty, lengths don't match,
            or format is invalid.
    """
    if output_format not in ("png", "svg"):
        raise ValueError(f"Invalid format '{output_format}'. Must be 'png' or 'svg'.")

    if config is None:
        config = TrajectoryConfig()

    # Ensure path has correct extension
    path = Path(path)
    if path.suffix.lower() != f".{output_format}":
        path = path.with_suffix(f".{output_format}")

    # Create parent directories if needed
    path.parent.mkdir(parents=True, exist_ok=True)

    # Generate and save figure
    fig = plot_bankroll_trajectories(
        results,
        bankroll_histories,
        config=config,
        win_limit=win_limit,
        loss_limit=loss_limit,
    )
    try:
        fig.savefig(path, format=output_format, dpi=config.dpi, bbox_inches="tight")
    finally:
        plt.close(fig)
