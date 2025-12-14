"""Risk of ruin curve visualization.

This module provides visualization of risk of ruin curves across
different bankroll levels.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import matplotlib.figure
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter

from let_it_ride.analytics.risk_of_ruin import RiskOfRuinReport

# Color palette for risk curves
COLORS = {
    "quarter_loss": "#ffd93d",
    "half_loss": "#ff9f43",
    "ruin": "#e74c3c",
    "analytical": "#3498db",
    "threshold_1pct": "#2ecc71",
    "threshold_5pct": "#f39c12",
}


@dataclass(slots=True)
class RiskCurveConfig:
    """Configuration for risk of ruin curve visualization.

    Attributes:
        figsize: Figure size as (width, height) in inches.
        dpi: Resolution in dots per inch for rasterized output.
        show_confidence_bands: Whether to display confidence interval bands.
        show_analytical: Whether to overlay analytical estimates.
        show_thresholds: Whether to show common risk threshold lines.
        title: Chart title.
        xlabel: Label for the x-axis.
        ylabel: Label for the y-axis.
    """

    figsize: tuple[float, float] = (12, 8)
    dpi: int = 150
    show_confidence_bands: bool = True
    show_analytical: bool = True
    show_thresholds: bool = True
    title: str = "Risk of Ruin by Bankroll Level"
    xlabel: str = "Bankroll (Units of Base Bet)"
    ylabel: str = "Probability"


def plot_risk_curves(
    report: RiskOfRuinReport,
    config: RiskCurveConfig | None = None,
) -> matplotlib.figure.Figure:
    """Generate a risk of ruin curve visualization.

    Creates a plot showing:
    - Ruin probability curve across bankroll levels
    - Half-bankroll (50% loss) risk curve
    - Quarter-bankroll (25% loss) risk curve
    - Confidence bands for ruin probability
    - Optional analytical estimate comparison
    - Common risk threshold lines (1%, 5%, 10%)

    Args:
        report: RiskOfRuinReport with calculated results.
        config: Visualization configuration. Uses defaults if not provided.

    Returns:
        Matplotlib Figure object containing the plot.

    Raises:
        ValueError: If report has no results.
    """
    if not report.results:
        raise ValueError("Cannot create plot from report with no results")

    if config is None:
        config = RiskCurveConfig()

    # Extract data from report in a single pass
    n_results = len(report.results)
    bankroll_units = np.empty(n_results, dtype=np.int64)
    ruin_probs = np.empty(n_results)
    half_risks = np.empty(n_results)
    quarter_risks = np.empty(n_results)
    ci_lowers = np.empty(n_results)
    ci_uppers = np.empty(n_results)
    confidence_level = report.results[0].confidence_interval.level

    for i, r in enumerate(report.results):
        bankroll_units[i] = r.bankroll_units
        ruin_probs[i] = r.ruin_probability
        half_risks[i] = r.half_bankroll_risk
        quarter_risks[i] = r.quarter_bankroll_risk
        ci_lowers[i] = r.confidence_interval.lower
        ci_uppers[i] = r.confidence_interval.upper

    # Create figure and axes
    fig, ax = plt.subplots(figsize=config.figsize)

    # Plot 25% loss risk (lightest color)
    ax.plot(
        bankroll_units,
        quarter_risks,
        color=COLORS["quarter_loss"],
        linewidth=2,
        marker="s",
        markersize=6,
        label="25% Loss Risk",
        zorder=3,
    )

    # Plot 50% loss risk (medium color)
    ax.plot(
        bankroll_units,
        half_risks,
        color=COLORS["half_loss"],
        linewidth=2,
        marker="^",
        markersize=6,
        label="50% Loss Risk",
        zorder=3,
    )

    # Plot ruin probability (darkest color)
    ax.plot(
        bankroll_units,
        ruin_probs,
        color=COLORS["ruin"],
        linewidth=2.5,
        marker="o",
        markersize=7,
        label="Ruin Probability",
        zorder=4,
    )

    # Add confidence bands
    if config.show_confidence_bands:
        ci_level_pct = int(confidence_level * 100)
        ax.fill_between(
            bankroll_units,
            ci_lowers,
            ci_uppers,
            color=COLORS["ruin"],
            alpha=0.2,
            label=f"{ci_level_pct}% Confidence Band",
            zorder=2,
        )

    # Add analytical estimates if available
    if config.show_analytical and report.analytical_estimates is not None:
        analytical = np.array(report.analytical_estimates)
        # Filter out NaN values
        valid_mask = ~np.isnan(analytical)
        if np.any(valid_mask):
            ax.plot(
                bankroll_units[valid_mask],
                analytical[valid_mask],
                color=COLORS["analytical"],
                linewidth=2,
                linestyle="--",
                marker="x",
                markersize=6,
                label="Analytical Estimate",
                zorder=3,
            )

    # Add threshold lines
    if config.show_thresholds:
        ax.axhline(
            y=0.01,
            color=COLORS["threshold_1pct"],
            linestyle=":",
            linewidth=1,
            alpha=0.7,
            zorder=1,
            label="1% threshold",
        )
        ax.axhline(
            y=0.05,
            color=COLORS["threshold_5pct"],
            linestyle=":",
            linewidth=1,
            alpha=0.7,
            zorder=1,
            label="5% threshold",
        )
        ax.axhline(
            y=0.10,
            color=COLORS["ruin"],
            linestyle=":",
            linewidth=1,
            alpha=0.7,
            zorder=1,
            label="10% threshold",
        )

    # Set axis properties
    ax.set_xlabel(config.xlabel, fontsize=11)
    ax.set_ylabel(config.ylabel, fontsize=11)
    ax.set_title(config.title, fontsize=13, fontweight="bold")

    # Set y-axis to show probabilities nicely
    ax.set_ylim(bottom=0)
    max_prob = max(max(quarter_risks), 1.0)
    ax.set_ylim(top=min(max_prob * 1.1, 1.0))

    # Format y-axis as percentages
    ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y:.0%}"))

    # Add grid
    ax.grid(True, alpha=0.3, linestyle="-")
    ax.set_axisbelow(True)

    # Add legend
    ax.legend(loc="upper right", fontsize=9, framealpha=0.9)

    # Add annotation with key statistics
    annotation_text = (
        f"Base Bet: ${report.base_bet:.2f}\n"
        f"Mean Session Profit: ${report.mean_session_profit:.2f}\n"
        f"Session Std Dev: ${report.session_profit_std:.2f}"
    )
    ax.annotate(
        annotation_text,
        xy=(0.02, 0.98),
        xycoords="axes fraction",
        ha="left",
        va="top",
        fontsize=9,
        bbox={"boxstyle": "round,pad=0.5", "facecolor": "white", "alpha": 0.8},
    )

    # Tight layout
    fig.tight_layout()

    return fig


def save_risk_curves(
    report: RiskOfRuinReport,
    path: Path,
    output_format: Literal["png", "svg"] = "png",
    config: RiskCurveConfig | None = None,
) -> None:
    """Generate and save risk of ruin curves to file.

    Args:
        report: RiskOfRuinReport with calculated results.
        path: Output file path. Extension will be added if not present.
        output_format: Output format, either "png" or "svg".
        config: Visualization configuration. Uses defaults if not provided.

    Raises:
        ValueError: If report has no results or format is invalid.
    """
    if output_format not in ("png", "svg"):
        raise ValueError(f"Invalid format '{output_format}'. Must be 'png' or 'svg'.")

    if config is None:
        config = RiskCurveConfig()

    # Ensure path has correct extension
    path = Path(path)
    if path.suffix.lower() != f".{output_format}":
        path = path.with_suffix(f".{output_format}")

    # Create parent directories if needed
    path.parent.mkdir(parents=True, exist_ok=True)

    # Generate and save figure
    fig = plot_risk_curves(report, config)
    try:
        fig.savefig(path, format=output_format, dpi=config.dpi, bbox_inches="tight")
    finally:
        plt.close(fig)
