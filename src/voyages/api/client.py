"""The ``Voyages`` entry point: a lazy, in-memory DuckDB session over the built data."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

from voyages.api import db, views
from voyages.api.query import Query
from voyages.schema import VOYAGE_DATASETS


class Result:
    """A lazy query result. Nothing runs until you ask for a format."""

    def __init__(self, relation: duckdb.DuckDBPyRelation):
        self.relation = relation

    def to_pandas(self) -> pd.DataFrame:
        return self.relation.df()

    def to_arrow(self):
        """A ``pyarrow.Table``."""
        return self.relation.to_arrow_table()

    def to_polars(self):
        """A ``polars.DataFrame``. Needs the ``polars`` extra."""
        try:
            import polars  # noqa: F401
        except ImportError as e:
            raise ImportError("to_polars() needs polars: pip install 'voyages[polars]'") from e
        return self.relation.pl()

    @property
    def columns(self) -> list[str]:
        return self.relation.columns

    def __len__(self) -> int:
        return self.relation.count("*").fetchone()[0]

    def __repr__(self) -> str:
        return repr(self.relation)


class Voyages:
    """Query the SlaveVoyages data built by ``voyages build``.

    >>> v = Voyages()
    >>> v.endpoints(dataset="transatlantic", drawable_only=True)

    The DuckDB connection opens on first use. ``built`` defaults to the
    built directory under ``$VOYAGES_DATA_DIR``.
    """

    def __init__(self, built: str | Path | None = None):
        self._built = Path(built) if built else None
        self._con: duckdb.DuckDBPyConnection | None = None

    @property
    def con(self) -> duckdb.DuckDBPyConnection:
        """The underlying DuckDB connection, opened on first use."""
        if self._con is None:
            self._con = db.connect(self._built)
        return self._con

    # ------------------------------------------------------------ raw access
    def sql(self, query: str, params: list | dict | None = None) -> Result:
        """Run SQL against the tables and views. See :meth:`tables`."""
        return Result(self.con.sql(query, params=params))

    def table(self, name: str) -> Result:
        if name not in self.tables():
            raise KeyError(f"no table or view {name!r}; see Voyages.tables()")
        return Result(self.con.table(name))

    def tables(self) -> list[str]:
        """Every table and view: Parquet tables, reference tables, derived views."""
        return sorted(
            r[0] for r in self.con.sql("SELECT table_name FROM duckdb_tables()").fetchall()
        ) + sorted(
            r[0]
            for r in self.con.sql(
                "SELECT view_name FROM duckdb_views() WHERE NOT internal"
            ).fetchall()
        )

    # ---------------------------------------------------------- fluent query
    @property
    def transatlantic(self) -> Query:
        """Trans-Atlantic voyages, ready to filter. See :class:`Query`."""
        return Query(self, ("transatlantic",))

    @property
    def intraamerican(self) -> Query:
        """Intra-American voyages, ready to filter. See :class:`Query`."""
        return Query(self, ("intraamerican",))

    def query(self, *datasets: str) -> Query:
        """Voyages from the given datasets (default: both)."""
        return Query(self, tuple(_check_dataset(d) for d in datasets) or VOYAGE_DATASETS)

    # -------------------------------------------------------------- map data
    def endpoints(self, dataset: str | None = None, drawable_only: bool = False) -> pd.DataFrame:
        """Where each voyage embarked and disembarked captives, with map points.

        One row per voyage. ``*_precision`` says what each point stands for
        (``place``, ``representative`` for an unspecified port drawn at the
        principal port, or ``region`` for a region's centre); style region
        points differently. ``drawable_only`` keeps voyages with both points;
        use :meth:`endpoint_coverage` to count the ones left out.
        """
        q = self.query(dataset) if dataset is not None else self.query()
        return q.endpoints(drawable_only=drawable_only)

    def endpoint_coverage(self) -> pd.DataFrame:
        """Voyages by dataset, endpoint and point status.

        Status per endpoint: ``place``, ``representative``, ``region``,
        ``no_point`` (a place is known but has nothing to draw, e.g. "Africa,
        port unspecified") or ``no_place`` (the data names none). The
        ``route`` rows count voyages with both points (``drawable``).
        """
        return self.con.sql(views.COVERAGE_SQL).df()

    # ------------------------------------------------------------- lifecycle
    def close(self) -> None:
        if self._con is not None:
            self._con.close()
            self._con = None

    def __enter__(self) -> Voyages:
        return self

    def __exit__(self, *exc) -> None:
        self.close()


def _check_dataset(dataset: str) -> str:
    if dataset not in VOYAGE_DATASETS:
        raise ValueError(f"dataset must be one of {VOYAGE_DATASETS}, not {dataset!r}")
    return dataset
