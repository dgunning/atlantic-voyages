"""The fluent query API: filters that narrow a set of voyages, then a summary.

>>> v.transatlantic.embarked_from("Bight of Biafra").disembarked_in("Jamaica") \\
...     .between(1700, 1800).by_decade(["embarked", "disembarked"])

Each filter returns a new :class:`Query`; nothing runs until a summary or
``to_*`` method is called. Filters combine with AND; several places in one
call combine with OR. DuckDB does the work: every query is one SQL statement
over ``voyages_wide`` joined to ``voyage_endpoints``.

Places are the voyage's principal places of embarkation and disembarkation as
resolved in ``voyage_endpoints`` (imputed, else recorded): the same places the
site's tables and maps use, and the ones drawn by :meth:`Query.endpoints`.
Years are the imputed year of arrival (YEARAM) unless ``on=`` says otherwise.
Totals sum the imputed totals (SLAXIMP, SLAMIMP) and skip voyages without
one, as the site does. Results carry the provenance of each measure in
``df.attrs["provenance"]``; imputed values are CC BY-NC 4.0.
"""

from __future__ import annotations

import difflib
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

import duckdb
import pandas as pd

from voyages import schema

if TYPE_CHECKING:
    from voyages.api.client import Voyages

# Short names for the measures people ask for most.
MEASURES = {
    "embarked": "embarked_imputed",
    "disembarked": "disembarked_imputed",
    "died": "died_middle_passage_imputed",
}
YEARS = {
    "arrived": "year_arrived_imputed",
    "departed": "year_departed_imputed",
    "left_africa": "year_left_africa_imputed",
}
SIDES = ("embarkation", "disembarkation")
BASE = "voyages_wide JOIN voyage_endpoints USING (voyage_id, dataset)"
LEVELS = ("place", "region", "broad_region")


class PlaceLookupError(LookupError):
    """A name did not resolve to exactly one code (place or label)."""


@dataclass(frozen=True)
class Query:
    """A lazy, immutable set of voyages. See the module docstring."""

    v: Voyages
    datasets: tuple[str, ...]
    clauses: tuple[tuple[str, tuple], ...] = ()

    # ---------------------------------------------------------------- filters
    def embarked_from(self, *places: str | int) -> Query:
        """Voyages whose principal place of embarkation is in any of ``places``.

        A place is a code or a name at any level: port ("Bonny"), region
        ("Bight of Biafra"), or broad region ("Africa").
        """
        return self._place_filter("embarkation", places)

    def disembarked_in(self, *places: str | int) -> Query:
        """Voyages whose principal place of disembarkation is in any of ``places``."""
        return self._place_filter("disembarkation", places)

    def between(
        self, start: int | None = None, end: int | None = None, on: str = "arrived"
    ) -> Query:
        """Voyages with a year in ``start..end``, inclusive. Either end may be open.

        ``on`` is ``arrived`` (default, YEARAM), ``departed`` or ``left_africa``.
        Voyages without that year are left out.
        """
        if on not in YEARS:
            raise ValueError(f"on must be one of {tuple(YEARS)}, not {on!r}")
        col = YEARS[on]
        q = self._where(f"{col} IS NOT NULL")
        if start is not None:
            q = q._where(f"{col} >= ?", int(start))
        if end is not None:
            q = q._where(f"{col} <= ?", int(end))
        return q

    def captive_outcome(self, *outcomes: str | int) -> Query:
        """Voyages by imputed outcome for the captives (FATE2), by label or code,
        e.g. "Captives disembarked in the Americas"."""
        return self._code_filter("outcome_for_captives_imputed", "outcomes_captives", outcomes)

    def flag(self, *nations: str | int) -> Query:
        """Voyages by imputed flag of the vessel (NATINIMP), e.g. "Portugal / Brazil"."""
        return self._code_filter("flag_imputed", "nations", nations)

    def where(self, condition: str, *params) -> Query:
        """Any SQL condition on the columns of ``voyages_wide`` or ``voyage_endpoints``."""
        return self._where(f"({condition})", *params)

    # -------------------------------------------------------------- summaries
    def by_decade(
        self,
        measures: str | Sequence[str] = ("voyages", "embarked", "disembarked"),
        on: str = "arrived",
    ) -> pd.DataFrame:
        """Totals by decade (from the imputed year of arrival by default).

        Voyages without a year form a row with ``decade`` = null rather than
        being dropped.
        """
        if on not in YEARS:
            raise ValueError(f"on must be one of {tuple(YEARS)}, not {on!r}")
        return self._group([f"({YEARS[on]} // 10 * 10)::SMALLINT AS decade"], measures)

    def by_region(
        self,
        side: str = "embarkation",
        measures: str | Sequence[str] = ("voyages", "embarked", "disembarked"),
        level: str = "region",
    ) -> pd.DataFrame:
        """Totals by region of embarkation or disembarkation.

        ``level`` is ``region`` (default), ``broad_region`` or ``place``.
        Voyages with no such place form a row with null code and name.
        """
        if side not in SIDES:
            raise ValueError(f"side must be one of {SIDES}, not {side!r}")
        if level not in LEVELS:
            raise ValueError(f"level must be one of {LEVELS}, not {level!r}")
        col = f"{side}_{level}"
        return self._group([col, f"{col}_name"], measures)

    def by(
        self, *columns: str, measures: str | Sequence[str] = ("voyages", "embarked", "disembarked")
    ) -> pd.DataFrame:
        """Totals grouped by any columns of the query."""
        cols = [self._column(c) for c in columns]
        return self._group(cols, measures)

    def summary(self) -> pd.DataFrame:
        """One row per dataset: voyages, totals, years and drawable routes."""
        sql = f"""
            SELECT dataset,
                count(*) AS voyages,
                sum(embarked_imputed)::BIGINT AS embarked,
                count(embarked_imputed) AS voyages_with_embarked,
                sum(disembarked_imputed)::BIGINT AS disembarked,
                count(disembarked_imputed) AS voyages_with_disembarked,
                min(year_arrived_imputed) AS first_year,
                max(year_arrived_imputed) AS last_year,
                count(*) FILTER (drawable) AS drawable
            FROM ({self.sql()}) GROUP BY dataset ORDER BY dataset DESC"""
        df = self.v.con.sql(sql, params=self.params()).df()
        df.attrs["provenance"] = {"embarked": "imputed", "disembarked": "imputed"}
        return df

    def count(self) -> int:
        return self.v.con.sql(
            f"SELECT count(*) FROM ({self.sql()})", params=self.params()
        ).fetchone()[0]

    __len__ = count

    # ------------------------------------------------------------------- rows
    def endpoints(self, drawable_only: bool = False) -> pd.DataFrame:
        """The ``voyage_endpoints`` rows for these voyages, for drawing on a map."""
        q = self._where("drawable") if drawable_only else self
        cols = ", ".join(c["name"] for c in schema.table_columns("voyage_endpoints"))
        return q._fetch(f"SELECT {cols} FROM ({q.sql()}) ORDER BY voyage_id").df()

    def to_pandas(self, columns: Sequence[str] | None = None) -> pd.DataFrame:
        """One row per voyage: ``voyages_wide`` plus the endpoint columns."""
        return self._rows(columns).df()

    def to_arrow(self, columns: Sequence[str] | None = None):
        return self._rows(columns).to_arrow_table()

    def to_polars(self, columns: Sequence[str] | None = None):
        try:
            import polars  # noqa: F401
        except ImportError as e:
            raise ImportError("to_polars() needs polars: pip install 'voyages[polars]'") from e
        return self._rows(columns).pl()

    # ------------------------------------------------------------------- SQL
    def sql(self) -> str:
        """The SQL for this query's rows; pair with :meth:`params`."""
        marks = ", ".join("?" for _ in self.datasets)
        where = [f"dataset IN ({marks})", *(c for c, _ in self.clauses)]
        return f"SELECT * FROM {BASE} WHERE " + " AND ".join(where)

    def params(self) -> list:
        return [*self.datasets, *(p for _, ps in self.clauses for p in ps)]

    def __repr__(self) -> str:
        return f"<Query {'+'.join(self.datasets)}: {len(self.clauses)} filter(s)>"

    # -------------------------------------------------------------- internals
    def _where(self, clause: str, *params) -> Query:
        return replace(self, clauses=(*self.clauses, (clause, tuple(params))))

    def _fetch(self, sql: str) -> duckdb.DuckDBPyRelation:
        return self.v.con.sql(sql, params=self.params())

    def _rows(self, columns: Sequence[str] | None) -> duckdb.DuckDBPyRelation:
        cols = ", ".join(self._column(c) for c in columns) if columns else "*"
        return self._fetch(f"SELECT {cols} FROM ({self.sql()}) ORDER BY voyage_id")

    def _columns(self) -> list[str]:
        if not hasattr(self.v, "_query_columns"):
            self.v._query_columns = self.v.con.sql(f"SELECT * FROM {BASE} LIMIT 0").columns
        return self.v._query_columns

    def _column(self, name: str) -> str:
        if name not in self._columns():
            close = difflib.get_close_matches(name, self._columns(), n=3)
            raise KeyError(f"no column {name!r}" + (f"; did you mean {close}?" if close else ""))
        return f'"{name}"'

    def _group(self, select: list[str], measures) -> pd.DataFrame:
        if isinstance(measures, str):
            measures = [measures]
        aggs, provenance = [], {}
        for m in measures:
            if m == "voyages":
                aggs.append("count(*) AS voyages")
                continue
            col = MEASURES.get(m, m)
            self._column(col)
            aggs.append(f'sum("{col}")::BIGINT AS "{m}"')
            try:
                provenance[m] = schema.load()[col].provenance
            except KeyError:
                provenance[m] = "derived"
        # Positional keys: an output name like "decade" can shadow a column.
        key_list = ", ".join(str(i + 1) for i in range(len(select)))
        sql = (
            f"SELECT {', '.join([*select, *aggs])} FROM ({self.sql()}) "
            f"GROUP BY {key_list} ORDER BY {key_list} NULLS LAST"
        )
        df = self._fetch(sql).df()
        df.attrs["provenance"] = provenance
        return df

    def _place_filter(self, side: str, places: Iterable[str | int]) -> Query:
        codes = [resolve_place(self.v, p) for p in places]
        if not codes:
            raise ValueError("give at least one place")
        ors, params = [], []
        for level in LEVELS:
            at = [c for c, lv in codes if lv == level]
            if at:
                ors.append(f"{side}_{level} IN ({', '.join('?' for _ in at)})")
                params += at
        return self._where("(" + " OR ".join(ors) + ")", *params)

    def _code_filter(self, column: str, reference: str, values: Iterable[str | int]) -> Query:
        codes = [resolve_label(self.v, reference, x) for x in values]
        if not codes:
            raise ValueError("give at least one value")
        return self._where(f"{column} IN ({', '.join('?' for _ in codes)})", *codes)


# ------------------------------------------------------------------ lookups
_LEVEL_RANK = {"broad_region": 0, "region": 1, "place": 2}


def resolve_place(v: Voyages, place: str | int) -> tuple[int, str]:
    """Return (code, level) for a place code or name.

    Names match ``name``, the source spelling or the Intra-American spelling,
    ignoring case. An exact match wins. Otherwise a name that starts the same
    way matches, and the broadest level wins: "Bight of Biafra" is the region
    "Bight of Biafra and Gulf of Guinea islands", not its "port unspecified".
    Ambiguous or unknown names raise ``LookupError`` with the candidates.
    """
    con = v.con
    if isinstance(place, int) or (isinstance(place, str) and place.isdigit()):
        row = con.sql(
            "SELECT code, level FROM places WHERE code = ?", params=[int(place)]
        ).fetchone()
        if row is None:
            raise PlaceLookupError(f"no place with code {place}")
        return row
    text = place.strip().lower()
    names = "lower(name) {op} OR lower(source_name) {op} OR lower(alt_name) {op}"
    exact = con.sql(
        f"SELECT code, level, name FROM places WHERE {names.format(op='= ?')}", params=[text] * 3
    ).fetchall()
    if len(exact) == 1:
        return exact[0][:2]
    if not exact:
        pre = con.sql(
            f"SELECT code, level, name FROM places WHERE {names.format(op='LIKE ?')}",
            params=[_like_prefix(text)] * 3,
        ).fetchall()
        if pre:
            top = min(_LEVEL_RANK[lv] for _, lv, _ in pre)
            best = [r for r in pre if _LEVEL_RANK[r[1]] == top]
            if len(best) == 1:
                return best[0][:2]
            exact = best
    if exact:
        listing = "; ".join(f"{c} {n} ({lv})" for c, lv, n in sorted(exact))
        raise PlaceLookupError(f"{place!r} matches several places, pass a code: {listing}")
    all_names = [r[0] for r in con.sql("SELECT name FROM places WHERE name IS NOT NULL").fetchall()]
    close = difflib.get_close_matches(place, all_names, n=5, cutoff=0.6)
    raise PlaceLookupError(
        f"no place named {place!r}" + (f"; did you mean {close}?" if close else "")
    )


def resolve_label(v: Voyages, reference: str, value: str | int) -> int:
    """Return the code for a label (exact, else unique prefix, ignoring case) or code."""
    con = v.con
    if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
        row = con.sql(
            f"SELECT code FROM {reference} WHERE code = ?", params=[int(value)]
        ).fetchone()
        if row is None:
            raise PlaceLookupError(f"no code {value} in {reference}")
        return row[0]
    text = value.strip().lower()
    for op, arg in (("= ?", text), ("LIKE ?", _like_prefix(text))):
        rows = con.sql(
            f"SELECT code, label FROM {reference} "
            f"WHERE lower(label) {op} OR lower(source_label) {op}",
            params=[arg, arg],
        ).fetchall()
        if len(rows) == 1:
            return rows[0][0]
        if len(rows) > 1:
            listing = "; ".join(f"{c} {lab}" for c, lab in sorted(rows))
            raise PlaceLookupError(f"{value!r} matches several {reference}, pass a code: {listing}")
    labels = [r[0] for r in con.sql(f"SELECT label FROM {reference}").fetchall() if r[0]]
    close = difflib.get_close_matches(value, labels, n=5, cutoff=0.5)
    raise PlaceLookupError(
        f"no {reference} label {value!r}" + (f"; did you mean {close}?" if close else "")
    )


def _like_prefix(text: str) -> str:
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
