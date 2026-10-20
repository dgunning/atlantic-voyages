"""Field helpers: list the registry and describe one field with its data.

``fields()`` reads only ``fields.yaml``. ``describe()`` adds what the data
holds: how many voyages have a value, per dataset, and the commonest codes
(with labels) or the range of numbers.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass

import duckdb
import pandas as pd

from voyages import schema

NUMERIC_KINDS = ("count", "measure", "ratio", "year", "date_part", "id")


def fields(
    dataset: str | None = None,
    provenance: str | None = None,
    table: str | None = None,
    search: str | None = None,
) -> pd.DataFrame:
    """Every registry field, one row each, optionally filtered.

    ``search`` matches the name, SPSS name, label or source label, ignoring case.
    """
    if dataset is not None and dataset not in schema.DATASETS:
        raise ValueError(f"dataset must be one of {schema.DATASETS}, not {dataset!r}")
    if provenance is not None and provenance not in schema.PROVENANCE:
        raise ValueError(f"provenance must be one of {schema.PROVENANCE}, not {provenance!r}")
    rows = []
    for f in schema.load().fields:
        if dataset and dataset not in f.datasets:
            continue
        if provenance and f.provenance != provenance:
            continue
        if table and f.table != table:
            continue
        if search and not _matches(f, search):
            continue
        rows.append(
            {
                "name": f.name,
                "spss_name": f.spss_name,
                "label": f.label,
                "provenance": f.provenance,
                "derived_from": ", ".join(f.derived_from) or None,
                "kind": f.kind,
                "dtype": f.dtype,
                "table": f.table,
                "datasets": ", ".join(f.datasets),
                "reference": f.reference,
                "codebook_page": (f.codebook or {}).get("page"),
            }
        )
    return pd.DataFrame(rows)


def _matches(f: schema.Field, text: str) -> bool:
    t = text.lower()
    hay = [f.name, f.spss_name, f.label, *f.source_label.values()]
    return any(t in h.lower() for h in hay if h)


def lookup(name: str, dataset: str | None = None) -> schema.Field:
    """A field by readable name or SPSS name, ignoring case.

    Some SPSS names exist both in the voyage files and in the Estimates file
    (NATINIMP, YEARAM, MAJBYIMP): the voyage field wins unless ``dataset``
    says ``estimates``. A readable name beats an SPSS name (``route``).
    """
    key = name.strip().lower()
    found = [
        f
        for f in schema.load().fields
        if key
        in (
            f.name.lower(),
            f.spss_name.lower(),
            *(n.lower() for n in f.spss_name_by_dataset.values()),
        )
    ]
    if dataset:
        found = [f for f in found if dataset in f.datasets]
    if len(found) > 1:  # a readable name beats an SPSS name, then voyage beats Estimates
        found.sort(key=lambda f: (f.name.lower() != key, not f.is_voyage_field))
    if not found:
        names = [f.name for f in schema.load().fields] + [f.spss_name for f in schema.load().fields]
        close = difflib.get_close_matches(name, names, n=5)
        raise KeyError(f"no field {name!r}" + (f"; did you mean {close}?" if close else ""))
    return found[0]


@dataclass(frozen=True)
class FieldDescription:
    """A registry field plus what the data holds for it."""

    field: schema.Field
    coverage: pd.DataFrame  # dataset, rows, with_value, share
    values: pd.DataFrame  # commonest codes with labels, or summary statistics

    def __str__(self) -> str:
        f = self.field
        lines = [
            f"{f.name} ({f.spss_name}): {f.label}",
            f"  provenance: {f.provenance}"
            + (f" (derived from {', '.join(f.derived_from)})" if f.derived_from else ""),
            f"  evidence:   {f.provenance_evidence}",
        ]
        if f.provenance_note:
            lines.append(f"  note:       {f.provenance_note}")
        if f.source_label:
            lines.append(
                "  source:     " + "; ".join(f"{d}: {s}" for d, s in f.source_label.items())
            )
        cb = f.codebook or {}
        lines.append(
            f"  type:       {f.kind} ({f.dtype}), table {f.table}"
            + (f", reference {f.reference}" if f.reference else "")
            + (f", codebook p.{cb['page']}" if cb.get("page") else "")
        )
        if f.notes:
            lines.append(f"  notes:      {f.notes}")
        lines += ["", self.coverage.to_string(index=False)]
        if len(self.values):
            lines += ["", self.values.to_string(index=False)]
        return "\n".join(lines)

    __repr__ = __str__


def describe(con: duckdb.DuckDBPyConnection, name: str, dataset: str | None = None):
    """Describe a field: registry entry, coverage per dataset, values."""
    f = lookup(name, dataset)
    source = "voyages_wide" if f.is_voyage_field else f.table
    col = f'"{f.name}"'
    if source != "voyages_wide":
        coverage = con.sql(
            f"SELECT '{f.datasets[0]}' AS dataset, count(*) AS rows, count({col}) AS with_value "
            f"FROM {source}"
        ).df()
        where = "TRUE"
    else:
        datasets = [d for d in f.datasets if d != "estimates"]
        where = "dataset IN (" + ", ".join(f"'{d}'" for d in datasets) + ")"
        coverage = con.sql(
            f"SELECT dataset, count(*) AS rows, count({col}) AS with_value "
            f"FROM voyages_wide WHERE {where} GROUP BY dataset ORDER BY dataset DESC"
        ).df()
    coverage["share"] = (coverage["with_value"] / coverage["rows"]).round(4)
    return FieldDescription(f, coverage, _values(con, f, source, col, where))


def _values(con, f: schema.Field, source: str, col: str, where: str) -> pd.DataFrame:
    if f.reference:
        label = "name" if f.reference == "places" else "label"
        return con.sql(
            f"SELECT {col} AS code, r.{label} AS label, count(*) AS rows "
            f"FROM {source} LEFT JOIN {f.reference} r ON r.code = {col} "
            f"WHERE {where} AND {col} IS NOT NULL GROUP BY ALL ORDER BY rows DESC, code LIMIT 10"
        ).df()
    if f.kind in NUMERIC_KINDS:
        return con.sql(
            f"SELECT min({col}) AS min, median({col}) AS median, avg({col}) AS mean, "
            f"max({col}) AS max, sum({col}) AS total FROM {source} WHERE {where}"
        ).df()
    if f.dtype == "date32":
        return con.sql(
            f"SELECT min({col}) AS first, max({col}) AS last FROM {source} WHERE {where}"
        ).df()
    return con.sql(
        f"SELECT left({col}::VARCHAR, 60) AS value, count(*) AS rows FROM {source} "
        f"WHERE {where} AND {col} IS NOT NULL GROUP BY ALL ORDER BY rows DESC, value LIMIT 10"
    ).df()
