"""Command-line interface for Let It Ride Strategy Simulator."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
)

from let_it_ride import __version__
from let_it_ride.analytics.export_csv import CSVExporter
from let_it_ride.config.loader import (
    ConfigFileNotFoundError,
    ConfigParseError,
    ConfigValidationError,
    load_config,
)
from let_it_ride.config.models import FullConfig  # noqa: TCH001
from let_it_ride.simulation import SimulationController

app = typer.Typer(
    name="let-it-ride",
    help="Let It Ride Strategy Simulator - Analyze play and betting strategies",
    no_args_is_help=True,
)
console = Console()
error_console = Console(stderr=True)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"let-it-ride version {__version__}")
        raise typer.Exit()


def _load_config_with_errors(config_path: Path) -> FullConfig:
    """Load configuration with user-friendly error messages.

    Args:
        config_path: Path to the YAML configuration file.

    Returns:
        Validated FullConfig object.

    Raises:
        typer.Exit: With code 1 if configuration loading fails.
    """
    try:
        return load_config(config_path)
    except ConfigFileNotFoundError as e:
        error_console.print(f"[red]Error:[/red] {e.message}")
        if e.details:
            error_console.print(f"[dim]{e.details}[/dim]")
        raise typer.Exit(code=1) from e
    except ConfigParseError as e:
        error_console.print(f"[red]Configuration parse error:[/red] {e.message}")
        if e.details:
            error_console.print(f"[dim]{e.details}[/dim]")
        raise typer.Exit(code=1) from e
    except ConfigValidationError as e:
        error_console.print(f"[red]Configuration validation error:[/red] {e.message}")
        if e.details:
            error_console.print(f"[dim]{e.details}[/dim]")
        raise typer.Exit(code=1) from e


@app.callback()
def main(
    version: bool = typer.Option(  # noqa: ARG001
        False,
        "--version",
        help="Show version and exit",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """Let It Ride Strategy Simulator CLI."""


@app.command()
def run(
    config: Annotated[
        Path,
        typer.Argument(
            help="Path to YAML configuration file",
            exists=False,  # We handle file validation ourselves for better errors
        ),
    ],
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Output directory override",
        ),
    ] = None,
    seed: Annotated[
        int | None,
        typer.Option(
            "--seed",
            help="Random seed override",
        ),
    ] = None,
    sessions: Annotated[
        int | None,
        typer.Option(
            "--sessions",
            help="Session count override",
            min=1,
        ),
    ] = None,
    quiet: Annotated[
        bool,
        typer.Option(
            "--quiet",
            "-q",
            help="Minimal output (no progress bar). Takes precedence over --verbose.",
        ),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            help="Detailed output",
        ),
    ] = False,
) -> None:
    """Run a simulation from a configuration file."""
    # Load and validate configuration
    cfg = _load_config_with_errors(config)

    # Apply CLI overrides by creating a modified config
    if seed is not None or sessions is not None:
        sim_config = cfg.simulation
        cfg = cfg.model_copy(
            update={
                "simulation": sim_config.model_copy(
                    update={
                        "random_seed": seed
                        if seed is not None
                        else sim_config.random_seed,
                        "num_sessions": sessions
                        if sessions is not None
                        else sim_config.num_sessions,
                    }
                )
            }
        )

    if output is not None:
        out_config = cfg.output
        cfg = cfg.model_copy(
            update={
                "output": out_config.model_copy(
                    update={"directory": str(output.resolve())}
                )
            }
        )

    num_sessions = cfg.simulation.num_sessions
    hands_per_session = cfg.simulation.hands_per_session

    if not quiet:
        console.print(f"[green]Running simulation:[/green] {config}")
        console.print(f"  Sessions: {num_sessions}")
        console.print(f"  Hands per session: {hands_per_session}")
        console.print(f"  Strategy: {cfg.strategy.type}")
        if cfg.simulation.random_seed is not None:
            console.print(f"  Seed: {cfg.simulation.random_seed}")
        console.print()

    # Create progress callback for SimulationController
    progress_bar: Progress | None = None
    task_id: TaskID | None = None

    def progress_callback(completed: int, total: int) -> None:
        """Update progress bar with session completion status."""
        if progress_bar is not None and task_id is not None:
            progress_bar.update(task_id, completed=completed, total=total)

    # Run simulation with or without progress bar
    try:
        if quiet:
            # No progress bar in quiet mode
            controller = SimulationController(cfg)
            results = controller.run()
        else:
            # Show progress bar
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                MofNCompleteColumn(),
                TimeElapsedColumn(),
                console=console,
            ) as progress_bar:
                task_id = progress_bar.add_task(
                    "Running sessions...", total=num_sessions
                )
                controller = SimulationController(
                    cfg, progress_callback=progress_callback
                )
                results = controller.run()
    except Exception as e:
        error_console.print(f"[red]Simulation error:[/red] {e}")
        if verbose:
            import traceback

            error_console.print(traceback.format_exc())
        raise typer.Exit(code=1) from e

    # Calculate statistics
    total_hands = results.total_hands
    duration = results.end_time - results.start_time
    duration_secs = duration.total_seconds()
    hands_per_sec = total_hands / duration_secs if duration_secs > 0 else 0

    # Calculate statistics in a single pass for efficiency
    winning_sessions = 0
    losing_sessions = 0
    total_profit = 0.0
    for r in results.session_results:
        total_profit += r.session_profit
        if r.session_profit > 0:
            winning_sessions += 1
        elif r.session_profit < 0:
            losing_sessions += 1
    breakeven_sessions = num_sessions - winning_sessions - losing_sessions
    win_rate = winning_sessions / num_sessions * 100 if num_sessions > 0 else 0
    avg_profit = total_profit / num_sessions if num_sessions > 0 else 0

    # Export results
    output_dir = Path(cfg.output.directory)
    try:
        exporter = CSVExporter(output_dir, prefix=cfg.output.prefix)
        exported_files = exporter.export_all(results)
    except Exception as e:
        error_console.print(f"[red]Export error:[/red] {e}")
        if verbose:
            import traceback

            error_console.print(traceback.format_exc())
        raise typer.Exit(code=1) from e

    # Print summary
    if not quiet:
        console.print()
        console.print("[green]Simulation complete![/green]")
        console.print()
        console.print("[bold]Results Summary:[/bold]")
        console.print(f"  Total hands: {total_hands:,}")
        console.print(
            f"  Duration: {duration_secs:.2f}s ({hands_per_sec:,.0f} hands/sec)"
        )
        console.print()
        console.print(f"  Winning sessions: {winning_sessions} ({win_rate:.1f}%)")
        console.print(f"  Losing sessions: {losing_sessions}")
        console.print(f"  Breakeven sessions: {breakeven_sessions}")
        console.print(f"  Total profit: ${total_profit:,.2f}")
        console.print(f"  Avg profit/session: ${avg_profit:.2f}")
        console.print()
        console.print("[bold]Exported files:[/bold]")
        for path in exported_files:
            console.print(f"  {path}")

        if verbose:
            console.print()
            console.print("[bold]Session Details:[/bold]")
            for i, r in enumerate(results.session_results):
                outcome_color = (
                    "green"
                    if r.session_profit > 0
                    else "red"
                    if r.session_profit < 0
                    else "yellow"
                )
                console.print(
                    f"  Session {i + 1}: "
                    f"[{outcome_color}]${r.session_profit:+.2f}[/{outcome_color}] "
                    f"({r.hands_played} hands, {r.stop_reason.value})"
                )
    else:
        # Quiet mode: just print essential info
        console.print(f"Completed {num_sessions} sessions, {total_hands} hands")
        console.print(f"Output: {output_dir}")


@app.command()
def validate(
    config: Annotated[
        Path,
        typer.Argument(
            help="Path to YAML configuration file",
            exists=False,  # We handle file validation ourselves for better errors
        ),
    ],
) -> None:
    """Validate a configuration file without running simulation."""
    cfg = _load_config_with_errors(config)

    # Print validation success with config summary
    console.print(f"[green]Configuration valid:[/green] {config}")
    console.print()
    console.print("[bold]Configuration Summary:[/bold]")
    console.print(f"  Sessions: {cfg.simulation.num_sessions}")
    console.print(f"  Hands per session: {cfg.simulation.hands_per_session}")
    console.print(f"  Workers: {cfg.simulation.workers}")
    console.print()
    console.print(f"  Starting bankroll: ${cfg.bankroll.starting_amount:.2f}")
    console.print(f"  Base bet: ${cfg.bankroll.base_bet:.2f}")
    console.print(f"  Betting system: {cfg.bankroll.betting_system.type}")
    console.print()
    console.print(f"  Strategy: {cfg.strategy.type}")
    console.print(f"  Bonus strategy: {cfg.bonus_strategy.type}")
    console.print()
    console.print(f"  Output directory: {cfg.output.directory}")
    # List enabled output formats
    enabled_formats = []
    if cfg.output.formats.csv.enabled:
        enabled_formats.append("csv")
    if cfg.output.formats.json_output.enabled:
        enabled_formats.append("json")
    if cfg.output.formats.html.enabled:
        enabled_formats.append("html")
    console.print(f"  Output formats: {', '.join(enabled_formats) or 'none'}")

    if cfg.simulation.random_seed is not None:
        console.print(f"  Random seed: {cfg.simulation.random_seed}")


if __name__ == "__main__":
    app()
