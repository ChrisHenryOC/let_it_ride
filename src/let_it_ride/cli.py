"""Command-line interface for Let It Ride Strategy Simulator."""

import typer
from rich.console import Console

from let_it_ride import __version__

app = typer.Typer(
    name="let-it-ride",
    help="Let It Ride Strategy Simulator - Analyze play and betting strategies",
    no_args_is_help=True,
)
console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"let-it-ride version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(  # noqa: ARG001
        False,
        "--version",
        "-v",
        help="Show version and exit",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """Let It Ride Strategy Simulator CLI."""


@app.command()
def run(
    config: str = typer.Argument(..., help="Path to YAML configuration file"),
) -> None:
    """Run a simulation from a configuration file."""
    console.print(f"[green]Running simulation with config:[/green] {config}")
    console.print("[yellow]Simulation not yet implemented[/yellow]")


@app.command()
def validate(
    config: str = typer.Argument(..., help="Path to YAML configuration file"),
) -> None:
    """Validate a configuration file without running simulation."""
    console.print(f"[green]Validating config:[/green] {config}")
    console.print("[yellow]Validation not yet implemented[/yellow]")


if __name__ == "__main__":
    app()
