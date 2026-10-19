"""``voyages query``: the fluent query API from the command line.

The filters mirror :class:`voyages.api.Query`. Output is CSV on stdout by
default, or a CSV or Parquet file with ``-o``. Parquet files carry the
citation and the provenance of each column in their metadata. The citation
and a licence note go to stderr, so stdout stays clean for piping.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Annotated

import pandas as pd
import typer

from voyages import citation
from voyages.api.query import column_provenance

GROUPINGS = ("decade", "summary", "endpoints")
REGION_GROUPINGS = tuple(
    f"{side}_{level}"
    for side in ("embarkation", "disembarkation")
    for level in ("region", "broad_region", "place")
)


Many = list[str] | None


def query(
    dataset: Annotated[
        Many,
        typer.Option(
            "--dataset", "-d", help="transatlantic or intraamerican (repeat; default both)."
        ),
    ] = None,
    embarked_from: Annotated[
        Many,
        typer.Option(
            "--embarked-from",
            "-e",
            help="Place of embarkation: port, region or broad region, name or code. Repeat for OR.",
        ),
    ] = None,
    disembarked_in: Annotated[
        Many,
        typer.Option("--disembarked-in", "-l", help="Place of disembarkation. Repeat for OR."),
    ] = None,
    start: Annotated[int | None, typer.Option("--from", help="First year, inclusive.")] = None,
    end: Annotated[int | None, typer.Option("--to", help="Last year, inclusive.")] = None,
    year: Annotated[
        str,
        typer.Option(help="Year for --from/--to and decades: arrived, departed or left_africa."),
    ] = "arrived",
    captive_outcome: Annotated[
        Many,
        typer.Option("--captive-outcome", help="Imputed outcome for the captives, label or code."),
    ] = None,
    flag: Annotated[
        Many, typer.Option("--flag", help="Imputed flag of the vessel, label or code.")
    ] = None,
    where: Annotated[
        str | None, typer.Option("--where", help="Extra SQL condition on any column.")
    ] = None,
    by: Annotated[
        str | None,
        typer.Option(
            "--by",
            help="Summarize: decade, summary, endpoints, embarkation_region "
            "(or _broad_region, _place), disembarkation_region (...), or any column. "
            "Default: one row per voyage.",
        ),
    ] = None,
    measure: Annotated[
        Many,
        typer.Option(
            "--measure",
            "-m",
            help="Totals for --by: voyages, embarked, disembarked, died, or a numeric column.",
        ),
    ] = None,
    columns: Annotated[
        str | None,
        typer.Option("--columns", "-c", help="Comma-separated columns for per-voyage rows."),
    ] = None,
    drawable_only: Annotated[
        bool, typer.Option(help="With --by endpoints: only voyages with both points.")
    ] = False,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Write a .csv or .parquet file instead of stdout."),
    ] = None,
    built: Annotated[
        Path | None,
        typer.Option(help="Built Parquet directory (default: under $VOYAGES_DATA_DIR)."),
    ] = None,
) -> None:
    """Filter voyages and write rows or totals as CSV or Parquet.

    Example: voyages query -d transatlantic -e "Bight of Biafra" -l Jamaica
    --from 1700 --to 1800 --by decade
    """
    from voyages.api import DataNotBuilt, Voyages

    if output is not None and output.suffix.lower() not in (".csv", ".parquet"):
        raise typer.BadParameter("must end in .csv or .parquet", param_hint="--output")
    try:
        with Voyages(built) as v:
            q = v.query(*(dataset or []))
            if embarked_from:
                q = q.embarked_from(*embarked_from)
            if disembarked_in:
                q = q.disembarked_in(*disembarked_in)
            if start is not None or end is not None:
                q = q.between(start, end, on=year)
            if captive_outcome:
                q = q.captive_outcome(*captive_outcome)
            if flag:
                q = q.flag(*flag)
            if where:
                q = q.where(where)
            df = _run(q, by, list(measure or []) or None, columns, year, drawable_only)
    except DataNotBuilt as e:
        _fail(str(e))
    except (LookupError, ValueError) as e:  # bad place, label, column or option value
        _fail(e.args[0] if e.args else str(e))

    _write(df, output)
    _notice(df)


def _run(q, by, measures, columns, year, drawable_only) -> pd.DataFrame:
    kw = {"measures": measures} if measures else {}
    if by is None:
        cols = [c.strip() for c in columns.split(",")] if columns else None
        return q.to_pandas(cols)
    if by == "decade":
        return q.by_decade(on=year, **kw)
    if by == "summary":
        return q.summary()
    if by == "endpoints":
        return q.endpoints(drawable_only=drawable_only)
    if by in REGION_GROUPINGS:
        side, level = by.split("_", 1)
        return q.by_region(side, level=level, **kw)
    return q.by(by, **kw)


def _write(df: pd.DataFrame, output: Path | None) -> None:
    if output is None:
        df.to_csv(sys.stdout, index=False)
        return
    if output.suffix.lower() == ".csv":
        df.to_csv(output, index=False)
    else:
        import pyarrow as pa
        import pyarrow.parquet as pq

        table = pa.Table.from_pandas(df, preserve_index=False)
        meta = {
            **(table.schema.metadata or {}),
            b"voyages.citation": citation().encode(),
            b"voyages.provenance": json.dumps(_provenance(df)).encode(),
        }
        pq.write_table(table.replace_schema_metadata(meta), output)
    typer.echo(f"wrote {len(df)} rows to {output}", err=True)


def _provenance(df: pd.DataFrame) -> dict[str, str]:
    """Provenance for each output column that is a registry field or a known measure."""
    prov = dict(df.attrs.get("provenance", {}))
    for c in df.columns:
        if c not in prov and (p := column_provenance(c)):
            prov[c] = p
    return prov


def _notice(df: pd.DataFrame) -> None:
    if "imputed" in _provenance(df).values():
        typer.echo(
            "Includes imputed values (CC BY-NC 4.0, SlaveVoyages). See docs/DATA.md.", err=True
        )
    typer.echo(citation(), err=True)


def _fail(message: str) -> None:
    typer.echo(f"error: {message}", err=True)
    raise typer.Exit(2)
