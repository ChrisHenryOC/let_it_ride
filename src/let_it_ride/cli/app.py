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
from let_it_ride.cli.formatters import OutputFormatter
from let_it_ride.config.loader import (
    ConfigFileNotFoundError,
    ConfigParseError,
    ConfigValidationError,
    load_config,
)
from let_it_ride.config.models import FullConfig  # noqa: TCH001
from let_it_ride.simulation import SimulationController
from let_it_ride.simulation.aggregation import aggregate_results

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

    # Determine verbosity level: quiet (0), normal (1), or verbose (2)
    verbosity = 0 if quiet else (2 if verbose else 1)
    formatter = OutputFormatter(verbosity=verbosity, console=console)

    if not quiet:
        console.print(f"[green]Running simulation:[/green] {config}")
        formatter.print_config_summary(cfg)

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

    # Export results
    output_dir = Path(cfg.output.directory)
    try:
        exporter = CSVExporter(output_dir, prefix=cfg.output.prefix)
        exported_files = exporter.export_all(
            results,
            include_seat_aggregate=cfg.output.formats.csv.include_seat_aggregate,
            num_seats=cfg.table.num_seats,
        )
    except Exception as e:
        error_console.print(f"[red]Export error:[/red] {e}")
        if verbose:
            import traceback

            error_console.print(traceback.format_exc())
        raise typer.Exit(code=1) from e

    # Print summary using formatter
    if not quiet:
        console.print()
        formatter.print_completion(total_hands, duration_secs)

        # Aggregate statistics for formatted display
        stats = aggregate_results(results.session_results)
        formatter.print_statistics(stats, duration_secs)
        formatter.print_hand_frequencies(stats.hand_frequencies)
        formatter.print_session_details(results.session_results)
        formatter.print_exported_files(exported_files)
    else:
        # Quiet mode: just print essential info
        formatter.print_minimal_completion(num_sessions, total_hands, output_dir)


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

    # Print validation success with config summary using formatter
    console.print(f"[green]Configuration valid:[/green] {config}")
    console.print()
    formatter = OutputFormatter(verbosity=1, console=console)
    formatter.print_config_summary(cfg)


if __name__ == "__main__":
    app()
