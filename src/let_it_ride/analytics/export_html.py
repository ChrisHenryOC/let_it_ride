"""HTML report generation for simulation results.

This module provides HTML report generation with embedded Plotly visualizations:
- generate_html_report(): Generate a complete HTML report from simulation results
- HTMLReportGenerator: Class to orchestrate HTML report generation
- HTMLReportConfig: Configuration for HTML report content and appearance
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Literal

import plotly.graph_objects as go
from jinja2 import Environment, PackageLoader, select_autoescape

from let_it_ride import __version__

if TYPE_CHECKING:
    from pathlib import Path

    from let_it_ride.analytics.statistics import DetailedStatistics
    from let_it_ride.simulation.aggregation import AggregateStatistics
    from let_it_ride.simulation.controller import SimulationResults
    from let_it_ride.simulation.session import SessionResult


# Theoretical hand frequency probabilities for Let It Ride (5-card poker)
# These are the expected frequencies for standard poker hands
THEORETICAL_HAND_FREQUENCIES: dict[str, float] = {
    "royal_flush": 0.000154,
    "straight_flush": 0.00139,
    "four_of_a_kind": 0.024,
    "full_house": 0.144,
    "flush": 0.197,
    "straight": 0.392,
    "three_of_a_kind": 2.113,
    "two_pair": 4.754,
    "pair_tens_or_better": 16.91,  # Paying pair (10s+)
    "pair_under_tens": 12.93,  # Non-paying pair (under 10s)
    "high_card": 62.40,
}


@dataclass(slots=True)
class HTMLReportConfig:
    """Configuration for HTML report generation.

    Attributes:
        title: Title of the HTML report.
        include_charts: Whether to include interactive Plotly charts.
        chart_library: Chart library to use (only "plotly" supported).
        include_config: Whether to include configuration summary.
        include_raw_data: Whether to include raw session data table.
        self_contained: If True, embed Plotly JS for offline viewing.
            If False, use CDN for smaller file size.
        trajectory_sample_size: Number of sessions to show in trajectory chart.
        histogram_bins: Number of bins for session outcome histogram.
    """

    title: str = "Let It Ride Simulation Report"
    include_charts: bool = True
    chart_library: Literal["plotly"] = "plotly"
    include_config: bool = True
    include_raw_data: bool = False
    self_contained: bool = True
    trajectory_sample_size: int = 10
    histogram_bins: int | str = "auto"


@dataclass(slots=True)
class _ChartData:
    """Internal container for chart HTML fragments."""

    histogram_html: str = ""
    trajectory_html: str = ""
    hand_frequency_html: str = ""


@dataclass(slots=True)
class _ReportContext:
    """Context data for Jinja2 template rendering."""

    title: str
    generated_at: str
    simulator_version: str
    config: dict[str, Any] | None
    stats: dict[str, Any]
    aggregate: dict[str, Any]
    charts: _ChartData
    include_charts: bool
    include_config: bool
    include_raw_data: bool
    raw_sessions: list[dict[str, Any]] = field(default_factory=list)


def _format_number(value: float, decimals: int = 2) -> str:
    """Format a number with thousand separators and fixed decimals.

    Args:
        value: Number to format.
        decimals: Number of decimal places.

    Returns:
        Formatted string representation.
    """
    return f"{value:,.{decimals}f}"


def _format_percentage(value: float, decimals: int = 2) -> str:
    """Format a decimal as a percentage string.

    Args:
        value: Decimal value (0.0 to 1.0).
        decimals: Number of decimal places.

    Returns:
        Percentage string (e.g., "42.50%").
    """
    return f"{value * 100:.{decimals}f}%"


def _format_currency(value: float) -> str:
    """Format a value as currency.

    Args:
        value: Currency value.

    Returns:
        Formatted currency string (e.g., "$1,234.56").
    """
    if value >= 0:
        return f"${value:,.2f}"
    return f"-${abs(value):,.2f}"


def _create_histogram_chart(
    session_results: list[SessionResult],
    bins: int | str = "auto",
) -> go.Figure:
    """Create a Plotly histogram of session profit/loss distribution.

    Args:
        session_results: List of session results.
        bins: Number of bins or "auto" for automatic binning.

    Returns:
        Plotly Figure object.
    """
    profits = [r.session_profit for r in session_results]

    fig = go.Figure()

    # Add histogram trace
    fig.add_trace(
        go.Histogram(
            x=profits,
            nbinsx=None if bins == "auto" else bins,
            marker_color="#3498db",
            marker_line_color="white",
            marker_line_width=1,
            opacity=0.8,
            name="Sessions",
        )
    )

    # Add mean line
    mean_profit = sum(profits) / len(profits)
    fig.add_vline(
        x=mean_profit,
        line_dash="dash",
        line_color="#e74c3c",
        annotation_text=f"Mean: {_format_currency(mean_profit)}",
        annotation_position="top right",
    )

    # Add zero line (break-even)
    fig.add_vline(
        x=0,
        line_dash="solid",
        line_color="#2c3e50",
        line_width=2,
        annotation_text="Break-even",
        annotation_position="bottom right",
    )

    fig.update_layout(
        title="Session Profit/Loss Distribution",
        xaxis_title="Session Profit/Loss ($)",
        yaxis_title="Frequency",
        template="plotly_white",
        showlegend=False,
        margin={"l": 60, "r": 40, "t": 60, "b": 60},
    )

    return fig


def _create_trajectory_chart(
    session_results: list[SessionResult],
    sample_size: int = 10,
) -> go.Figure:
    """Create a Plotly line chart of bankroll trajectories.

    Args:
        session_results: List of session results.
        sample_size: Number of sessions to sample for display.

    Returns:
        Plotly Figure object.
    """
    fig = go.Figure()

    # Sample sessions for trajectory display
    if len(session_results) <= sample_size:
        sampled = session_results
    else:
        # Take evenly spaced samples
        step = len(session_results) // sample_size
        sampled = [session_results[i * step] for i in range(sample_size)]

    # Get starting bankroll from first session
    starting_bankroll = sampled[0].starting_bankroll if sampled else 0

    for i, session in enumerate(sampled):
        # Create trajectory from starting to final bankroll
        # We only have start and end points from SessionResult
        x_values = [0, session.hands_played]
        y_values = [starting_bankroll, session.final_bankroll]

        # Color based on outcome
        if session.final_bankroll > starting_bankroll:
            color = "#27ae60"  # Green for profit
        elif session.final_bankroll < starting_bankroll:
            color = "#e74c3c"  # Red for loss
        else:
            color = "#95a5a6"  # Gray for break-even

        fig.add_trace(
            go.Scatter(
                x=x_values,
                y=y_values,
                mode="lines",
                line={"color": color, "width": 1.5},
                opacity=0.7,
                name=f"Session {i + 1}",
                hovertemplate=(
                    f"Session {i + 1}<br>"
                    "Hands: %{x}<br>"
                    "Bankroll: $%{y:,.2f}<extra></extra>"
                ),
            )
        )

    # Add starting bankroll line
    fig.add_hline(
        y=starting_bankroll,
        line_dash="dash",
        line_color="#2c3e50",
        annotation_text=f"Starting: {_format_currency(starting_bankroll)}",
        annotation_position="right",
    )

    fig.update_layout(
        title=f"Bankroll Trajectories (Sample of {len(sampled)} Sessions)",
        xaxis_title="Hands Played",
        yaxis_title="Bankroll ($)",
        template="plotly_white",
        showlegend=False,
        margin={"l": 60, "r": 40, "t": 60, "b": 60},
    )

    return fig


def _create_hand_frequency_chart(
    aggregate_stats: AggregateStatistics,
) -> go.Figure:
    """Create a Plotly bar chart comparing actual vs theoretical hand frequencies.

    Args:
        aggregate_stats: Aggregate statistics with hand frequency data.

    Returns:
        Plotly Figure object.
    """
    fig = go.Figure()

    # Get actual frequencies
    actual_freq = aggregate_stats.hand_frequency_pct

    if not actual_freq:
        # No hand frequency data available
        fig.add_annotation(
            text="Hand frequency data not available",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font={"size": 16, "color": "#7f8c8d"},
        )
        fig.update_layout(
            title="Hand Frequency Comparison",
            template="plotly_white",
        )
        return fig

    # Order hands from most to least common
    hand_order = [
        "high_card",
        "pair_under_tens",
        "pair_tens_or_better",
        "two_pair",
        "three_of_a_kind",
        "straight",
        "flush",
        "full_house",
        "four_of_a_kind",
        "straight_flush",
        "royal_flush",
    ]

    # Filter to hands present in data
    hands = [
        h for h in hand_order if h in actual_freq or h in THEORETICAL_HAND_FREQUENCIES
    ]

    # Format hand names for display
    display_names = [h.replace("_", " ").title() for h in hands]

    actual_values = [actual_freq.get(h, 0) * 100 for h in hands]
    theoretical_values = [THEORETICAL_HAND_FREQUENCIES.get(h, 0) for h in hands]

    # Add actual frequency bars
    fig.add_trace(
        go.Bar(
            x=display_names,
            y=actual_values,
            name="Actual",
            marker_color="#3498db",
            text=[f"{v:.2f}%" for v in actual_values],
            textposition="outside",
        )
    )

    # Add theoretical frequency bars
    fig.add_trace(
        go.Bar(
            x=display_names,
            y=theoretical_values,
            name="Theoretical",
            marker_color="#95a5a6",
            text=[f"{v:.2f}%" for v in theoretical_values],
            textposition="outside",
        )
    )

    fig.update_layout(
        title="Hand Frequency: Actual vs Theoretical",
        xaxis_title="Hand Type",
        yaxis_title="Frequency (%)",
        barmode="group",
        template="plotly_white",
        legend={"yanchor": "top", "y": 0.99, "xanchor": "right", "x": 0.99},
        margin={"l": 60, "r": 40, "t": 60, "b": 100},
        xaxis_tickangle=-45,
    )

    return fig


def _detailed_stats_to_dict(stats: DetailedStatistics) -> dict[str, Any]:
    """Convert DetailedStatistics to dictionary for template rendering.

    Args:
        stats: DetailedStatistics object.

    Returns:
        Dictionary with formatted statistics.
    """
    return {
        "session_win_rate": _format_percentage(stats.session_win_rate),
        "session_win_rate_ci": (
            f"{_format_percentage(stats.session_win_rate_ci.lower)} - "
            f"{_format_percentage(stats.session_win_rate_ci.upper)}"
        ),
        "ev_per_hand": _format_currency(stats.ev_per_hand),
        "ev_per_hand_ci": (
            f"{_format_currency(stats.ev_per_hand_ci.lower)} - "
            f"{_format_currency(stats.ev_per_hand_ci.upper)}"
        ),
        "main_game_ev": _format_currency(stats.main_game_ev),
        "bonus_ev": _format_currency(stats.bonus_ev),
        "total_sessions": f"{stats.total_sessions:,}",
        "total_hands": f"{stats.total_hands:,}",
        "distribution": {
            "mean": _format_currency(stats.session_profit_distribution.mean),
            "std": _format_currency(stats.session_profit_distribution.std),
            "min": _format_currency(stats.session_profit_distribution.min),
            "max": _format_currency(stats.session_profit_distribution.max),
            "percentiles": {
                str(k): _format_currency(v)
                for k, v in stats.session_profit_distribution.percentiles.items()
            },
        },
        "risk": {
            "prob_any_loss": _format_percentage(stats.risk_metrics.prob_any_loss),
            "prob_loss_50pct": _format_percentage(stats.risk_metrics.prob_loss_50pct),
            "prob_loss_100pct": _format_percentage(stats.risk_metrics.prob_loss_100pct),
            "max_drawdown_mean": _format_currency(stats.risk_metrics.max_drawdown_mean),
            "max_drawdown_std": _format_currency(stats.risk_metrics.max_drawdown_std),
        },
    }


def _aggregate_stats_to_dict(stats: AggregateStatistics) -> dict[str, Any]:
    """Convert AggregateStatistics to dictionary for template rendering.

    Args:
        stats: AggregateStatistics object.

    Returns:
        Dictionary with formatted statistics.
    """
    return {
        "total_sessions": f"{stats.total_sessions:,}",
        "winning_sessions": f"{stats.winning_sessions:,}",
        "losing_sessions": f"{stats.losing_sessions:,}",
        "push_sessions": f"{stats.push_sessions:,}",
        "session_win_rate": _format_percentage(stats.session_win_rate),
        "total_hands": f"{stats.total_hands:,}",
        "total_wagered": _format_currency(stats.total_wagered),
        "total_won": _format_currency(stats.total_won),
        "net_result": _format_currency(stats.net_result),
        "expected_value_per_hand": _format_currency(stats.expected_value_per_hand),
        "main_wagered": _format_currency(stats.main_wagered),
        "main_won": _format_currency(stats.main_won),
        "main_ev_per_hand": _format_currency(stats.main_ev_per_hand),
        "bonus_wagered": _format_currency(stats.bonus_wagered),
        "bonus_won": _format_currency(stats.bonus_won),
        "bonus_ev_per_hand": _format_currency(stats.bonus_ev_per_hand),
        "session_profit_mean": _format_currency(stats.session_profit_mean),
        "session_profit_std": _format_currency(stats.session_profit_std),
        "session_profit_median": _format_currency(stats.session_profit_median),
        "session_profit_min": _format_currency(stats.session_profit_min),
        "session_profit_max": _format_currency(stats.session_profit_max),
    }


def _config_to_dict(results: SimulationResults) -> dict[str, Any]:
    """Extract configuration summary for template rendering.

    Args:
        results: SimulationResults containing configuration.

    Returns:
        Dictionary with configuration summary.
    """
    cfg = results.config
    return {
        "simulation": {
            "num_sessions": f"{cfg.simulation.num_sessions:,}",
            "hands_per_session": f"{cfg.simulation.hands_per_session:,}",
            "random_seed": str(cfg.simulation.random_seed or "None"),
            "workers": str(cfg.simulation.workers),
        },
        "bankroll": {
            "starting_amount": _format_currency(cfg.bankroll.starting_amount),
            "base_bet": _format_currency(cfg.bankroll.base_bet),
            "betting_system": cfg.bankroll.betting_system.type,
        },
        "strategy": {
            "type": cfg.strategy.type,
        },
        "bonus_strategy": {
            "type": cfg.bonus_strategy.type,
        },
        "timing": {
            "start_time": results.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": results.end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration": str(results.end_time - results.start_time),
        },
    }


class HTMLReportGenerator:
    """Generates HTML reports from simulation results.

    Uses Jinja2 templates and Plotly for interactive visualizations.
    """

    __slots__ = ("_env", "_config")

    def __init__(self, config: HTMLReportConfig | None = None) -> None:
        """Initialize the HTML report generator.

        Args:
            config: Report configuration. Uses defaults if not provided.
        """
        self._config = config or HTMLReportConfig()
        self._env = Environment(
            loader=PackageLoader("let_it_ride.analytics", "templates"),
            autoescape=select_autoescape(["html", "xml"]),
        )

    @property
    def config(self) -> HTMLReportConfig:
        """Return the report configuration."""
        return self._config

    def _generate_charts(
        self,
        results: SimulationResults,
        aggregate_stats: AggregateStatistics,
    ) -> _ChartData:
        """Generate Plotly chart HTML fragments.

        Args:
            results: Simulation results.
            aggregate_stats: Aggregate statistics.

        Returns:
            _ChartData with HTML fragments for each chart.
        """
        charts = _ChartData()

        if not self._config.include_charts:
            return charts

        # Determine Plotly JS inclusion mode
        include_plotlyjs: bool | str = True if self._config.self_contained else "cdn"

        # Session outcome histogram
        histogram_fig = _create_histogram_chart(
            results.session_results,
            bins=self._config.histogram_bins,
        )
        charts.histogram_html = histogram_fig.to_html(
            full_html=False,
            include_plotlyjs=include_plotlyjs,
            div_id="histogram-chart",
        )

        # Bankroll trajectory
        trajectory_fig = _create_trajectory_chart(
            results.session_results,
            sample_size=self._config.trajectory_sample_size,
        )
        charts.trajectory_html = trajectory_fig.to_html(
            full_html=False,
            include_plotlyjs=False,  # Already included above
            div_id="trajectory-chart",
        )

        # Hand frequency comparison
        frequency_fig = _create_hand_frequency_chart(aggregate_stats)
        charts.hand_frequency_html = frequency_fig.to_html(
            full_html=False,
            include_plotlyjs=False,  # Already included above
            div_id="frequency-chart",
        )

        return charts

    def render(
        self,
        results: SimulationResults,
        stats: DetailedStatistics,
    ) -> str:
        """Render the HTML report as a string.

        Args:
            results: Simulation results.
            stats: Detailed statistics.

        Returns:
            Complete HTML document as string.
        """
        from let_it_ride.simulation.aggregation import aggregate_results

        aggregate_stats = aggregate_results(results.session_results)

        # Generate charts
        charts = self._generate_charts(results, aggregate_stats)

        # Build template context
        context = _ReportContext(
            title=self._config.title,
            generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            simulator_version=__version__,
            config=_config_to_dict(results) if self._config.include_config else None,
            stats=_detailed_stats_to_dict(stats),
            aggregate=_aggregate_stats_to_dict(aggregate_stats),
            charts=charts,
            include_charts=self._config.include_charts,
            include_config=self._config.include_config,
            include_raw_data=self._config.include_raw_data,
        )

        # Add raw session data if requested
        if self._config.include_raw_data:
            context.raw_sessions = [
                {
                    "outcome": r.outcome.value,
                    "hands_played": r.hands_played,
                    "starting_bankroll": _format_currency(r.starting_bankroll),
                    "final_bankroll": _format_currency(r.final_bankroll),
                    "session_profit": _format_currency(r.session_profit),
                    "max_drawdown": _format_currency(r.max_drawdown),
                }
                for r in results.session_results
            ]

        # Render template
        template = self._env.get_template("report.html.j2")
        return template.render(
            title=context.title,
            generated_at=context.generated_at,
            simulator_version=context.simulator_version,
            config=context.config,
            stats=context.stats,
            aggregate=context.aggregate,
            histogram_html=context.charts.histogram_html,
            trajectory_html=context.charts.trajectory_html,
            hand_frequency_html=context.charts.hand_frequency_html,
            include_charts=context.include_charts,
            include_config=context.include_config,
            include_raw_data=context.include_raw_data,
            raw_sessions=context.raw_sessions,
        )


class HTMLExporter:
    """Orchestrates HTML export of simulation results to a file.

    Attributes:
        output_dir: Directory where HTML files are written.
        prefix: Filename prefix for exported files.
    """

    __slots__ = ("_output_dir", "_prefix", "_config")

    def __init__(
        self,
        output_dir: Path,
        prefix: str = "simulation",
        config: HTMLReportConfig | None = None,
    ) -> None:
        """Initialize the HTML exporter.

        Args:
            output_dir: Directory for output files. Created if it doesn't exist.
            prefix: Filename prefix (default: "simulation").
            config: HTML report configuration. Uses defaults if not provided.
        """
        self._output_dir = output_dir
        self._prefix = prefix
        self._config = config or HTMLReportConfig()

    @property
    def output_dir(self) -> Path:
        """Return the output directory."""
        return self._output_dir

    @property
    def prefix(self) -> str:
        """Return the filename prefix."""
        return self._prefix

    @property
    def config(self) -> HTMLReportConfig:
        """Return the HTML report configuration."""
        return self._config

    def _ensure_output_dir(self) -> None:
        """Create output directory if it doesn't exist.

        Creates directory with 0o755 permissions (owner rwx, group/other rx).
        """
        self._output_dir.mkdir(parents=True, exist_ok=True, mode=0o755)

    def export(
        self,
        results: SimulationResults,
        stats: DetailedStatistics,
    ) -> Path:
        """Export simulation results to HTML file.

        Args:
            results: SimulationResults to export.
            stats: DetailedStatistics for the results.

        Returns:
            Path to the created file.
        """
        self._ensure_output_dir()

        generator = HTMLReportGenerator(self._config)
        html_content = generator.render(results, stats)

        path = self._output_dir / f"{self._prefix}_report.html"
        with path.open("w", encoding="utf-8") as f:
            f.write(html_content)

        return path


def generate_html_report(
    results: SimulationResults,
    stats: DetailedStatistics,
    output_path: Path,
    config: HTMLReportConfig | None = None,
) -> None:
    """Generate an HTML report and save to file.

    This is the main entry point for HTML report generation.

    Args:
        results: Simulation results to report on.
        stats: Detailed statistics for the results.
        output_path: Path where HTML file will be written.
        config: Report configuration. Uses defaults if not provided.

    Example:
        >>> from pathlib import Path
        >>> from let_it_ride.analytics import generate_html_report
        >>> generate_html_report(results, stats, Path("report.html"))
    """
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True, mode=0o755)

    generator = HTMLReportGenerator(config)
    html_content = generator.render(results, stats)

    with output_path.open("w", encoding="utf-8") as f:
        f.write(html_content)
