"""Command-line entry points."""

from __future__ import annotations

import json

import typer

from .data import bootstrap_data
from .projects import run_all

app = typer.Typer(no_args_is_help=True, help="Build The Next Possession NBA portfolio.")


@app.command()
def data(refresh: bool = typer.Option(False, help="Ignore cached raw responses.")) -> None:
    """Fetch and normalize all portfolio datasets."""

    frames = bootstrap_data(refresh=refresh)
    typer.echo(json.dumps({name: len(frame) for name, frame in frames.items()}, indent=2))


@app.command()
def build() -> None:
    """Run all seven analyses and generate report artifacts."""

    typer.echo(json.dumps(run_all(), indent=2))


@app.command(name="all")
def all_steps(refresh: bool = typer.Option(False, help="Ignore cached raw responses.")) -> None:
    """Fetch data, run every project, and generate report artifacts."""

    bootstrap_data(refresh=refresh)
    typer.echo(json.dumps(run_all(), indent=2))


if __name__ == "__main__":  # pragma: no cover
    app()

