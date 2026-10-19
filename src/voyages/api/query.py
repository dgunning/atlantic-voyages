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

Recorded-only queries (:meth:`Query.recorded_only`) read no imputed field.
Nothing is substituted under the same name: places are the recorded principal
places, years the recorded dates of the same events, and totals must be named
recorded fields (default: captives on board leaving Africa, captives arriving
at the first landing). Anything imputed raises ``ValueError``. Recorded data
covers far fewer voyages than the imputed data. ``where()`` conditions are not
checked; keep them to recorded columns.
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

# Short names for the measures people ask for most (imputed totals).
MEASURES = {
    "embarked": "embarked_imputed",
    "disembarked": "disembarked_imputed",
    "died": "died_middle_passage_imputed",
}
DEFAULT_MEASURES = ("voyages", "embarked", "disembarked")
RECORDED_DEFAULT_MEASURES = (
    "voyages",
    "captives_on_board_leaving_africa",
    "captives_arrived_first_landing",
)
YEARS = {
    "arrived": "year_arrived_imputed",
    "departed": "year_departed_imputed",
    "left_africa": "year_left_africa_imputed",
}
# The same events, as recorded.
RECORDED_YEARS = {
    "arrived": "first_landing_year",
    "departed": "departure_year",
    "left_africa": "left_africa_year",
}
SIDES = ("embarkation", "disembarkation")
LEVELS = ("place", "region", "broad_region")


def _base(recorded: bool) -> str:
    view = "voyage_endpoints_recorded" if recorded else "voyage_endpoints"
    return f"voyages_wide JOIN {view} USING (voyage_id, dataset)"


class PlaceLookupError(LookupError):
    """A name did not resolve to exactly one code (place or label)."""


@dataclass(frozen=True)
class Query:
    """A lazy, immutable set of voyages. See the module docstring."""

    v: Voyages
    datasets: tuple[str, ...]
    clauses: tuple[tuple[str, tuple], ...] = ()
    recorded: bool = False

    def recorded_only(self) -> Query:
        """Read no imputed field from here on (see the module docstring).

        Call it before any filter, so every filter is built on recorded data.
        """
        if self.clauses and not self.recorded:
            raise ValueError("call recorded_only() before adding filters")
        return replace(self, recorded=True)

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

        ``on`` is ``arrived`` (default: YEARAM, or the recorded year of first
        landing in recorded-only mode), ``departed`` or ``left_africa``.
        Voyages without that year are left out.
        """
        col = self._year(on)
        q = self._where(f"{col} IS NOT NULL")
        if start is not None:
            q = q._where(f"{col} >= ?", int(start))
        if end is not None:
            q = q._where(f"{col} <= ?", int(end))
        return q

    def captive_outcome(self, *outcomes: str | int) -> Query:
        """Voyages by imputed outcome for the captives (FATE2), by label or code,
        e.g. "Captives disembarked in the Americas"."""
        if self.recorded:
            raise ValueError(
                "the outcome for captives is imputed; in recorded-only mode use "
                ".outcome() (the particular outcome as recorded)"
            )
        return self._code_filter("outcome_for_captives_imputed", "outcomes_captives", outcomes)

    def outcome(self, *outcomes: str | int) -> Query:
        """Voyages by particular outcome as recorded (FATE), by label or code."""
        return self._code_filter("outcome", "outcomes", outcomes)

    def flag(self, *nations: str | int) -> Query:
        """Voyages by flag of the vessel, e.g. "Portugal / Brazil": the imputed
        flag (NATINIMP), or the recorded one (NATIONAL) in recorded-only mode."""
        return self._code_filter("flag" if self.recorded else "flag_imputed", "nations", nations)

    def where(self, condition: str, *params) -> Query:
        """Any SQL condition on the columns of ``voyages_wide`` or the endpoints.

        Not checked in recorded-only mode: keep it to recorded columns.
        """
        return self._where(f"({condition})", *params)

    # -------------------------------------------------------------- summaries
    def by_decade(
        self, measures: str | Sequence[str] | None = None, on: str = "arrived"
    ) -> pd.DataFrame:
        """Totals by decade of the year ``on`` (see :meth:`between`).

        Voyages without a year form a row with ``decade`` = null rather than
        being dropped.
        """
        col = self._year(on)
        df = self._group([f"({col} // 10 * 10)::SMALLINT AS decade"], measures)
        df.attrs["provenance"] = {
            "decade": "derived" if self.recorded else "imputed",
            **df.attrs["provenance"],
        }
        return df

    def by_region(
        self,
        side: str = "embarkation",
        measures: str | Sequence[str] | None = None,
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

    def by(self, *columns: str, measures: str | Sequence[str] | None = None) -> pd.DataFrame:
        """Totals grouped by any columns of the query."""
        return self._group([self._column(c) for c in columns], measures)

    def summary(self) -> pd.DataFrame:
        """One row per dataset: voyages, totals, years and drawable routes."""
        if self.recorded:
            emb, dis = RECORDED_DEFAULT_MEASURES[1:]
            names = (emb, dis)
        else:
            emb, dis = MEASURES["embarked"], MEASURES["disembarked"]
            names = ("embarked", "disembarked")
        year = self._year("arrived")
        sql = f"""
            SELECT dataset,
                count(*) AS voyages,
                sum({emb})::BIGINT AS {names[0]},
                count({emb}) AS voyages_with_{names[0]},
                sum({dis})::BIGINT AS {names[1]},
                count({dis}) AS voyages_with_{names[1]},
                min({year}) AS first_year,
                max({year}) AS last_year,
                count(*) FILTER (drawable) AS drawable
            FROM ({self.sql()}) GROUP BY dataset ORDER BY dataset DESC"""
        df = self._fetch(sql).df()
        kind = "recorded" if self.recorded else "imputed"
        df.attrs["provenance"] = {
            names[0]: kind,
            names[1]: kind,
            "first_year": kind,
            "last_year": kind,
        }
        return df

    def count(self) -> int:
        return self._fetch(f"SELECT count(*) FROM ({self.sql()})").fetchone()[0]

    __len__ = count

    # ------------------------------------------------------------------- rows
    def endpoints(self, drawable_only: bool = False) -> pd.DataFrame:
        """The endpoint rows for these voyages, for drawing on a map."""
        q = self._where("drawable") if drawable_only else self
        cols = ", ".join(c["name"] for c in schema.table_columns("voyage_endpoints"))
        return q._fetch(f"SELECT {cols} FROM ({q.sql()}) ORDER BY voyage_id").df()

    def to_pandas(self, columns: Sequence[str] | None = None) -> pd.DataFrame:
        """One row per voyage: ``voyages_wide`` plus the endpoint columns.

        In recorded-only mode the default is every column that is not imputed.
        """
        return self._rows(columns).df()

    def to_arrow(self, columns: Sequence[str] | None = None):
        return self._rows(columns).to_arrow_table()

    def to_polars(self, columns: Sequence[str] | None = None):
        try:
            import polars  # noqa: F401
        except ImportError as e:
            raise ImportError("to_polars() needs polars: pip install 'voyages[polars]'") from e
        return self._rows(columns).pl()

    def columns(self) -> list[str]:
        """Columns available to filters, ``by()`` and ``to_*`` in this mode."""
        cols = self._all_columns()
        if self.recorded:
            cols = [c for c in cols if column_provenance(c, recorded=True) != "imputed"]
        return cols

    # ------------------------------------------------------------------- SQL
    def sql(self) -> str:
        """The SQL for this query's rows; pair with :meth:`params`."""
        marks = ", ".join("?" for _ in self.datasets)
        where = [f"dataset IN ({marks})", *(c for c, _ in self.clauses)]
        return f"SELECT * FROM {_base(self.recorded)} WHERE " + " AND ".join(where)

    def params(self) -> list:
        return [*self.datasets, *(p for _, ps in self.clauses for p in ps)]

    def __repr__(self) -> str:
        mode = ", recorded only" if self.recorded else ""
        return f"<Query {'+'.join(self.datasets)}{mode}: {len(self.clauses)} filter(s)>"

    # -------------------------------------------------------------- internals
    def _where(self, clause: str, *params) -> Query:
        return replace(self, clauses=(*self.clauses, (clause, tuple(params))))

    def _fetch(self, sql: str) -> duckdb.DuckDBPyRelation:
        return self.v.con.sql(sql, params=self.params())

    def _rows(self, columns: Sequence[str] | None) -> duckdb.DuckDBPyRelation:
        names = list(columns) if columns else self.columns()
        cols = ", ".join(self._column(c) for c in names)
        return self._fetch(f"SELECT {cols} FROM ({self.sql()}) ORDER BY voyage_id")

    def _all_columns(self) -> list[str]:
        cache = self.v.__dict__.setdefault("_query_columns", {})
        if self.recorded not in cache:
            cache[self.recorded] = self.v.con.sql(
                f"SELECT * FROM {_base(self.recorded)} LIMIT 0"
            ).columns
        return cache[self.recorded]

    def _column(self, name: str) -> str:
        """Quote a column name after checking it exists and is allowed in this mode."""
        if name not in self._all_columns():
            close = difflib.get_close_matches(name, self._all_columns(), n=3)
            raise KeyError(f"no column {name!r}" + (f"; did you mean {close}?" if close else ""))
        if self.recorded and column_provenance(name, recorded=True) == "imputed":
            raise ValueError(f"{name!r} is imputed; not available in recorded-only mode")
        return f'"{name}"'

    def _year(self, on: str) -> str:
        years = RECORDED_YEARS if self.recorded else YEARS
        if on not in years:
            raise ValueError(f"on must be one of {tuple(years)}, not {on!r}")
        return years[on]

    def _measure(self, m: str) -> str:
        if m in MEASURES:
            if self.recorded:
                raise ValueError(
                    f"{m!r} is an imputed total; in recorded-only mode name a recorded field, "
                    f"e.g. {', '.join(RECORDED_DEFAULT_MEASURES[1:])}"
                )
            return MEASURES[m]
        return m

    def _group(self, select: list[str], measures) -> pd.DataFrame:
        if measures is None:
            measures = RECORDED_DEFAULT_MEASURES if self.recorded else DEFAULT_MEASURES
        if isinstance(measures, str):
            measures = [measures]
        aggs, provenance = [], {}
        for m in measures:
            if m == "voyages":
                aggs.append("count(*) AS voyages")
                continue
            col = self._measure(m)
            aggs.append(f'sum({self._column(col)})::BIGINT AS "{m}"')
            provenance[m] = column_provenance(col, recorded=self.recorded) or "derived"
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


# --------------------------------------------------------------- provenance
_POINT_SUFFIXES = ("_lat", "_lon", "_precision", "_map_code")


def column_provenance(name: str, recorded: bool = False) -> str | None:
    """Provenance of a query column: recorded, imputed, derived, or None if unknown.

    Voyage fields come from the registry (never the Estimates fields, some of
    which share names). A field derived from an imputed field (the year
    groupings) counts as ``imputed``. Endpoint places and regions are
    ``imputed``, the more restrictive class, since each row's ``*_provenance``
    column says which rows were recorded; in recorded-only mode (``recorded``)
    places are ``recorded`` and regions ``derived`` from them. Map points and
    ``drawable`` are ``derived``.
    """
    if name.startswith(SIDES) or name == "drawable":
        if name == "drawable" or name.endswith(_POINT_SUFFIXES):
            return "derived"
        if name.endswith("_provenance"):
            return None
        if not recorded:
            return "imputed"
        return "recorded" if name.endswith(("_place", "_place_name")) else "derived"
    f = _voyage_field(name)
    if f is None:
        return None
    if any(_voyage_field(d) and _voyage_field(d).provenance == "imputed" for d in f.derived_from):
        return "imputed"
    return f.provenance


def _voyage_field(name: str) -> schema.Field | None:
    """The voyage field for a column, or for the code column behind a ``*_name`` column."""
    base = name[: -len("_name")] if name.endswith("_name") else name
    for f in schema.load().fields:
        if f.name in (name, base) and f.table != "estimates":
            return f
    return None


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
