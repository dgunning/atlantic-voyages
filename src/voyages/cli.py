"""Command-line entry point: ``voyages fetch``, ``voyages verify``, ``voyages build``."""

from __future__ import annotations

import typer

from voyages import __version__, citation
from voyages import fetch as _fetch
from voyages.config import data_dir, raw_dir

app = typer.Typer(help="Tools for the SlaveVoyages databases.", no_args_is_help=True)


@app.command()
def version() -> None:
    """Print the library version and the data directory in use."""
    typer.echo(f"voyages {__version__}")
    typer.echo(f"data dir: {data_dir()}")


@app.command()
def fetch(
    dataset: list[str] = typer.Option(  # noqa: B008
        list(_fetch.DEFAULT_DATASETS), "--dataset", "-d", help="Datasets to fetch."
    ),
    force: bool = typer.Option(False, help="Re-download even if the file exists."),
) -> None:
    """Download the official data files into the raw cache."""
    for path in _fetch.fetch_all(tuple(dataset), force=force):
        typer.echo(f"ok  {path}")
    typer.echo(f"\n{citation()}")


@app.command()
def verify() -> None:
    """Check the raw cache against the manifest checksums."""
    status = _fetch.verify()
    width = max(len(k) for k in status)
    for name, state in status.items():
        typer.echo(f"{name:<{width}}  {state}")
    typer.echo(f"\nraw dir: {raw_dir()}")


@app.command()
def build() -> None:
    """Build the reference tables (and, later in Phase 1, Parquet) from the raw downloads."""
    from voyages.ingest import reference

    for table, n in reference.build().items():
        typer.echo(f"ok  reference/{table}.csv  {n} rows")
    typer.echo("\nParquet tables are not built yet (Phase 1, see PLAN.md).")


if __name__ == "__main__":
    app()
