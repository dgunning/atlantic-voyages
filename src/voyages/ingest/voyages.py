"""Turn a voyage .sav file into the typed Parquet tables the registry defines.

Works for any voyage dataset (Trans-Atlantic, Intra-American): every
decision about names, types, provenance and destination table comes from
``fields.yaml``. The steps:

1. read the .sav with pyreadstat, codes left as numbers;
2. rename each SPSS column to its registry ``name`` and coerce to its dtype
   (strings trimmed, "" -> null; integer columns checked to be whole);
3. split fields into the normalized tables (``voyages`` plus the long
   tables) and the convenience ``voyages_wide``;
4. check every table against its registry schema and key, then write Parquet.
"""

from __future__ import annotations

import datetime as dt
import re
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from voyages import schema
from voyages.ingest import reference

PANDAS_INT = {"int8": "Int8", "int16": "Int16", "int32": "Int32"}
LONG_TABLES = (
    "voyage_links",
    "voyage_places",
    "voyage_people_counts",
    "voyage_people_shares",
    "voyage_crew",
    "voyage_sources",
    "voyage_enslavers",
)
VOYAGE_TABLES = ("voyages", "voyage_dates", *LONG_TABLES, "voyages_wide")


class IngestError(ValueError):
    """The raw data does not fit the registry."""


# Values in the source that cannot be right, listed one by one. Each is set
# to null with a warning; anything not listed still fails the build.
# (dataset, voyage_id, field name): reason
KNOWN_BAD_VALUES = {
    ("intraamerican", 105238, "boys_landed_first_place"): "0.2 boys",
    ("intraamerican", 105238, "boys_departure_or_arrival_imputed"): "0.2 boys",
    ("intraamerican", 105238, "infants_landed_first_place"): "0.5 infants",
    ("intraamerican", 105238, "infants_departure_or_arrival_imputed"): "0.5 infants",
    ("intraamerican", 105990, "boys_landed_first_place"): "0.556 boys",
    ("intraamerican", 105990, "boys_departure_or_arrival_imputed"): "0.556 boys",
    ("intraamerican", 105990, "girls_landed_first_place"): "0.2 girls",
    ("intraamerican", 105990, "girls_departure_or_arrival_imputed"): "0.2 girls",
    ("intraamerican", 105990, "females_departure_or_arrival_imputed"): "0.333 females",
    ("intraamerican", 105990, "females_landed_first_place_imputed"): "0.333 females",
}


# ------------------------------------------------------------------ reading
def read_sav(path: Path) -> pd.DataFrame:
    import pyreadstat

    df, _ = pyreadstat.read_sav(path, apply_value_formats=False)
    return df


def coerce(raw: pd.DataFrame, dataset: str, reg: schema.Registry) -> pd.DataFrame:
    """One column per registry field, named by ``name``, typed by ``dtype``."""
    cols = {c.upper(): c for c in raw.columns}
    ids = raw[cols["VOYAGEID"]]
    out = {}
    for f in reg.for_dataset(dataset):
        src = cols.get(f.spss_name_in(dataset).upper())
        if src is None:
            raise IngestError(f"{dataset}: column {f.spss_name_in(dataset)} ({f.name}) missing")
        out[f.name] = _coerce_column(_drop_known_bad(raw[src], ids, dataset, f.name), f)
    return pd.DataFrame(out)


def _drop_known_bad(s: pd.Series, ids: pd.Series, dataset: str, name: str) -> pd.Series:
    for (ds, vid, field_name), reason in KNOWN_BAD_VALUES.items():
        if ds == dataset and field_name == name:
            hit = ids == vid
            if hit.any() and s[hit].notna().any():
                warnings.warn(
                    f"{dataset} voyage {vid}: {name} set to null ({reason})", stacklevel=2
                )
                s = s.mask(hit)
    return s


def _coerce_column(s: pd.Series, f: schema.Field) -> pd.Series:
    if f.kind == "id_list":
        # IDs stored as text, sometimes several ("10275, 10157") -> "10275;10157"
        def norm(v):
            if not isinstance(v, str) or not v.strip():
                return None
            parts = re.split(r"[,;\s]+", v.strip())
            if not all(p.isdigit() for p in parts):
                raise IngestError(f"{f.name}: not a list of IDs: {v!r}")
            return ";".join(parts)

        return s.map(norm).astype("object")
    if f.dtype == "string":
        s = s.astype("object").map(lambda v: v.strip() if isinstance(v, str) else v)
        return s.where(s.notna() & (s != ""), None)
    if f.dtype in PANDAS_INT:
        nn = s.dropna()
        if len(nn) and not np.all(np.mod(nn, 1) == 0):
            raise IngestError(
                f"{f.name}: non-integer values, e.g. {nn[np.mod(nn, 1) != 0].iloc[0]}"
            )
        return s.astype(PANDAS_INT[f.dtype])
    if f.dtype == "float64":
        return s.astype("float64")
    if f.dtype == "bool":
        mapping = {"True": True, "False": False, 1: True, 0: False}  # 1.0 == 1 as a key
        bad = set(s.dropna().unique()) - set(mapping)
        if bad:
            raise IngestError(f"{f.name}: unexpected flag values {sorted(map(str, bad))}")
        return s.map(mapping).astype("boolean")
    if f.dtype == "date32":
        return s.map(lambda v: v if isinstance(v, dt.date) else None).astype("object")
    raise IngestError(f"{f.name}: unknown dtype {f.dtype}")


# ------------------------------------------------------------------ tables
def _base(typed: pd.DataFrame, dataset: str, mask: pd.Series) -> dict:
    return {"voyage_id": typed.loc[mask, "voyage_id"].to_numpy(), "dataset": dataset}


def _long(typed, dataset, fields, value_col, extra, table_cols):
    """Melt wide fields into rows: one per non-null value.

    ``provenance`` and ``spss_name`` are added only if the table defines them.
    """
    parts = []
    for f in fields:
        s = typed[f.name]
        m = s.notna()
        if not m.any():
            continue
        parts.append(
            pd.DataFrame(
                {
                    **_base(typed, dataset, m),
                    **{k: f.long[k] for k in extra if k in f.long},
                    value_col: s[m].to_numpy(),
                    **({"provenance": f.provenance} if "provenance" in table_cols else {}),
                    **({"spss_name": f.spss_name_in(dataset)} if "spss_name" in table_cols else {}),
                }
            )
        )
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def _links(typed: pd.DataFrame, dataset: str, fields) -> pd.DataFrame:
    """One row per link from an ID-list field."""
    parts = []
    for f in fields:
        s = typed[f.name]
        m = s.notna()
        linked = s[m].str.split(";")
        df = pd.DataFrame(
            {"voyage_id": typed.loc[m, "voyage_id"].to_numpy(), "ids": linked.to_numpy()}
        ).explode("ids")
        parts.append(
            pd.DataFrame(
                {
                    "voyage_id": df["voyage_id"].to_numpy(),
                    "dataset": dataset,
                    "relation": f.long["relation"],
                    "linked_voyage_id": df["ids"].astype("int64").to_numpy(),
                    "linked_dataset": "transatlantic",
                }
            )
        )
    if not parts:
        return pd.DataFrame()
    return pd.concat(parts, ignore_index=True).drop_duplicates(
        ["voyage_id", "relation", "linked_voyage_id"]
    )


def _dates(typed: pd.DataFrame, dataset: str, fields) -> pd.DataFrame:
    """One row per voyage and event with year/month/day and a full date.

    ``date`` is the source's composite date where it has one, otherwise it
    is built from the parts when they form a valid date. Parts stay as
    recorded even when invalid (e.g. day 99, month 13 occur in the source).
    """
    events: dict[str, dict[str, str]] = {}
    for f in fields:
        events.setdefault(f.long["event"], {})[f.long["part"]] = f.name
    parts = []
    for event, p in events.items():
        cols = {k: typed[v] if v else None for k, v in p.items()}
        year, month, day = cols.get("year"), cols.get("month"), cols.get("day")
        composite = cols.get("date")
        built = pd.Series(
            [_make_date(y, mo, d) for y, mo, d in zip(year, month, day, strict=True)],
            index=typed.index,
            dtype="object",
        )
        date = composite.where(composite.notna(), built) if composite is not None else built
        m = year.notna() | month.notna() | day.notna() | date.notna()
        parts.append(
            pd.DataFrame(
                {
                    **_base(typed, dataset, m),
                    "event": event,
                    "year": year[m].to_numpy(),
                    "month": month[m].to_numpy(),
                    "day": day[m].to_numpy(),
                    "date": date[m].to_numpy(),
                }
            )
        )
    return pd.concat(parts, ignore_index=True)


def _make_date(y, m, d):
    if pd.isna(y) or pd.isna(m) or pd.isna(d):
        return None
    try:
        return dt.date(int(y), int(m), int(d))
    except ValueError:
        return None


def _wide(typed: pd.DataFrame, dataset: str, reg: schema.Registry) -> pd.DataFrame:
    """Every field as a column, plus decoded ``*_name`` columns for codes."""
    labels = {}
    out = {"voyage_id": typed["voyage_id"], "dataset": dataset}
    for col in schema.table_columns("voyages_wide", reg)[2:]:
        name = col["name"]
        if name in typed:
            out[name] = typed[name]
        elif name.endswith("_name") and name[: -len("_name")] in typed:
            f = reg[name[: -len("_name")]]
            if f.reference not in labels:
                labels[f.reference] = _reference_labels(f.reference)
            out[name] = typed[f.name].map(labels[f.reference]).astype("object")
        else:  # a field of the other voyage dataset
            out[name] = None
    return pd.DataFrame(out)


def _reference_labels(ref: str) -> dict[int, str]:
    import csv

    with (reference.REFERENCE_DIR / f"{ref}.csv").open(encoding="utf-8") as fh:
        key = "name" if ref == "places" else "label"
        return {int(r["code"]): (r[key] or None) for r in csv.DictReader(fh)}


def build_tables(dataset: str, sav_path: Path) -> dict[str, pa.Table]:
    """Read one voyage dataset and return every Parquet table for it."""
    if dataset not in schema.VOYAGE_DATASETS:
        raise ValueError(f"not a voyage dataset: {dataset}")
    reg = schema.load()
    typed = coerce(read_sav(sav_path), dataset, reg)
    if typed["voyage_id"].isna().any():
        raise IngestError(f"{dataset}: voyages without an ID")

    frames: dict[str, pd.DataFrame] = {}
    in_ds = lambda table: [f for f in reg.for_table(table) if dataset in f.datasets]  # noqa: E731

    voyage_cols = [f.name for f in in_ds("voyages") if f.name != "voyage_id"]
    frames["voyages"] = pd.concat(
        [typed[["voyage_id"]].assign(dataset=dataset), typed[voyage_cols]], axis=1
    )
    frames["voyage_dates"] = _dates(typed, dataset, in_ds("voyage_dates"))
    value_col = {
        "voyage_places": ("code", ["role", "seq", "level"]),
        "voyage_people_counts": ("count", ["stage", "category"]),
        "voyage_people_shares": ("share", ["stage", "category"]),
        "voyage_crew": ("count", ["measure", "stage"]),
        "voyage_sources": ("reference", ["seq"]),
        "voyage_enslavers": ("name", ["role", "seq"]),
    }
    frames["voyage_links"] = _links(typed, dataset, in_ds("voyage_links"))
    for table, (col, keys) in value_col.items():
        table_cols = {c["name"] for c in schema.table_columns(table, reg)}
        frames[table] = _long(typed, dataset, in_ds(table), col, keys, table_cols)
    frames["voyages_wide"] = _wide(typed, dataset, reg)

    return {t: _to_arrow(t, df, reg) for t, df in frames.items()}


def _to_arrow(table: str, df: pd.DataFrame, reg: schema.Registry) -> pa.Table:
    """Conform a frame to the registry schema exactly, and check its key."""
    sch = schema.arrow_schema(table, reg)
    for c in sch.names:
        if c not in df:
            df[c] = None  # e.g. a voyages column only the other dataset has
    extra = set(df.columns) - set(sch.names)
    if extra:
        raise IngestError(f"{table}: columns not in the registry: {sorted(extra)}")
    df = df[sch.names]
    key = reg.tables[table].get("key")
    if key and len(df) and df.duplicated(key).any():
        dup = df[df.duplicated(key, keep=False)].head(4)
        raise IngestError(f"{table}: duplicate key {key}:\n{dup}")
    return pa.Table.from_pandas(df, schema=sch, preserve_index=False)


def write(tables: dict[str, pa.Table], dataset: str, out_dir: Path) -> dict[str, Path]:
    """Write ``<out_dir>/<table>/<dataset>.parquet`` for each table."""
    paths = {}
    for name, tbl in tables.items():
        p = out_dir / name / f"{dataset}.parquet"
        p.parent.mkdir(parents=True, exist_ok=True)
        pq.write_table(tbl, p, compression="zstd")
        paths[name] = p
    return paths
