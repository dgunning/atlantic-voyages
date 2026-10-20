"""A DuckDB connection over the built Parquet and the reference tables.

The connection is in memory and holds no data of its own: each Parquet
table under the built directory becomes a view (both voyage datasets in
one view, told apart by ``dataset``), each reference CSV becomes a small
table, and the derived views in :mod:`voyages.api.views` sit on top.
Nothing is written to disk.
"""

from __future__ import annotations

import csv
from pathlib import Path

import duckdb

from voyages import schema
from voyages.api import views
from voyages.config import built_dir
from voyages.ingest.reference import REFERENCE_DIR


class DataNotBuilt(FileNotFoundError):
    """The Parquet tables are missing: run ``voyages build`` first."""


# Reference CSV columns that are not text. Everything else loads as VARCHAR.
REFERENCE_TYPES = {
    "code": "INTEGER",
    "region_code": "INTEGER",
    "broad_region_code": "INTEGER",
    "map_code": "INTEGER",
    "lat": "DOUBLE",
    "lon": "DOUBLE",
    "map_lat": "DOUBLE",
    "map_lon": "DOUBLE",
    "used_in_data": "BOOLEAN",
}


def parquet_tables(registry: schema.Registry | None = None) -> list[str]:
    """Tables ``voyages build`` writes as Parquet (the registry's non-view tables)."""
    reg = registry or schema.load()
    return [t for t, spec in reg.tables.items() if not spec.get("view")]


def registry_table(table: str) -> dict:
    return schema.load().tables[table]


def connect(
    built: Path | None = None, reference: Path = REFERENCE_DIR
) -> duckdb.DuckDBPyConnection:
    """Open an in-memory DuckDB connection with every table and view registered."""
    built = Path(built) if built else built_dir()
    con = duckdb.connect(":memory:")
    missing = []
    for table in parquet_tables():
        files = sorted((built / table).glob("*.parquet"))
        if not files:
            if not registry_table(table).get("optional"):
                missing.append(table)
            continue
        paths = ", ".join(_quote(str(p)) for p in files)
        con.execute(
            f"CREATE VIEW {table} AS SELECT * FROM read_parquet([{paths}], union_by_name = true)"
        )
    if missing:
        con.close()
        raise DataNotBuilt(
            f"no Parquet for {', '.join(missing)} in {built}. Run `voyages build` first."
        )
    for path in sorted(reference.glob("*.csv")):
        _load_reference(con, path)
    views.create(con)
    return con


def _load_reference(con: duckdb.DuckDBPyConnection, path: Path) -> None:
    name = path.stem
    if name in parquet_tables():
        raise ValueError(f"reference table {name} clashes with a Parquet table")
    with path.open(encoding="utf-8", newline="") as fh:
        header = next(csv.reader(fh))
    columns = ", ".join(f"{_quote(c)}: {_quote(REFERENCE_TYPES.get(c, 'VARCHAR'))}" for c in header)
    con.execute(
        f"CREATE TABLE {name} AS SELECT * FROM read_csv({_quote(str(path))}, "
        f"header = true, columns = {{{columns}}})"
    )


def _quote(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"
