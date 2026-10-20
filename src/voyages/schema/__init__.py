"""The field registry: every column the library produces, described once.

``fields.yaml`` next to this file is authoritative. Each field has a
readable ``name`` (its column in ``voyages_wide`` and its identifier in
the API), the ``spss_name`` it comes from (for a supplementary source, the
source's own variable, e.g. a Wikibase property such as ``P46``), a ``label`` in project
language, the original ``source_label`` verbatim, and a ``provenance``
of recorded, imputed or derived. ``table`` and ``long`` say where the
value lands in the normalized Parquet tables.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from typing import Any

import yaml

REGISTRY_PATH = Path(__file__).with_name("fields.yaml")

PROVENANCE = ("recorded", "imputed", "derived")
DATASETS = ("transatlantic", "intraamerican", "estimates", "enslaved")
# Supplementary sources: published by other projects, opt-in, kept in their own
# tables and never merged into the SlaveVoyages tables. See docs/DATA.md.
SUPPLEMENTARY_DATASETS = ("enslaved",)
VOYAGE_DATASETS = ("transatlantic", "intraamerican")


@dataclass(frozen=True)
class Field:
    name: str
    spss_name: str
    label: str
    dtype: str
    kind: str
    provenance: str
    provenance_evidence: str
    datasets: tuple[str, ...]
    table: str
    source_label: dict[str, str] = field(default_factory=dict)
    provenance_note: str | None = None
    reference: str | None = None
    long: dict[str, Any] | None = None
    codebook: dict[str, Any] | None = None
    notes: str | None = None
    spss_name_by_dataset: dict[str, str] = field(default_factory=dict)
    derived_from: tuple[str, ...] = ()

    @property
    def is_voyage_field(self) -> bool:
        """A field of the voyage datasets (a column of ``voyages_wide``)."""
        return any(d in VOYAGE_DATASETS for d in self.datasets)

    def spss_name_in(self, dataset: str) -> str:
        """SPSS variable name for this field in a given dataset's file."""
        return self.spss_name_by_dataset.get(dataset, self.spss_name)


@dataclass(frozen=True)
class Registry:
    fields: tuple[Field, ...]
    tables: dict[str, dict[str, Any]]
    dropped: tuple[dict[str, str], ...]

    def __len__(self) -> int:
        return len(self.fields)

    def __getitem__(self, name: str) -> Field:
        for f in self.fields:
            if f.name == name:
                return f
        raise KeyError(name)

    def by_spss(self, spss_name: str, dataset: str | None = None) -> Field:
        """Look up a field by its SPSS name (case-insensitive)."""
        key = spss_name.upper()
        for f in self.fields:
            if dataset and dataset not in f.datasets:
                continue
            names = {f.spss_name.upper(), *(n.upper() for n in f.spss_name_by_dataset.values())}
            if key in names:
                return f
        raise KeyError(spss_name)

    def for_table(self, table: str) -> tuple[Field, ...]:
        return tuple(f for f in self.fields if f.table == table)

    def for_dataset(self, dataset: str) -> tuple[Field, ...]:
        return tuple(f for f in self.fields if dataset in f.datasets)


@cache
def load(path: Path = REGISTRY_PATH) -> Registry:
    """Load and parse ``fields.yaml``. Cached; the file is read once."""
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    fields = tuple(
        Field(
            **{
                **f,
                "datasets": tuple(f["datasets"]),
                "source_label": f.get("source_label") or {},
                "derived_from": tuple(f.get("derived_from") or ()),
            }
        )
        for f in doc["fields"]
    )
    return Registry(fields=fields, tables=doc["tables"], dropped=tuple(doc.get("dropped", ())))


# ------------------------------------------------------------ table schemas


def table_columns(table: str, registry: Registry | None = None) -> list[dict[str, str]]:
    """Columns of a Parquet table, in order, with `from_fields` expanded.

    Each item has name, dtype and description. This is the single place
    the Parquet layout is defined; the build writes exactly these columns.
    """
    reg = registry or load()
    spec = reg.tables[table]
    if "same_columns_as" in spec:
        return table_columns(spec["same_columns_as"], reg)
    cols: list[dict[str, str]] = []
    for c in spec["columns"]:
        if "from_fields" not in c:
            cols.append(c)
            continue
        if table == "voyages_wide":
            fields = [f for f in reg.fields if f.is_voyage_field]
        else:
            fields = list(reg.for_table(table))
        for f in fields:
            if f.name == "voyage_id":  # already the key column
                continue
            cols.append({"name": f.name, "dtype": f.dtype, "description": f.label})
            if table == "voyages_wide" and f.reference:
                cols.append(
                    {
                        "name": f"{f.name}_name",
                        "dtype": "string",
                        "description": f"{f.label} (decoded from reference {f.reference})",
                    }
                )
    return cols


def arrow_schema(table: str, registry: Registry | None = None):
    """pyarrow schema for a Parquet table, from the registry."""
    import pyarrow as pa

    types = {
        "int8": pa.int8(),
        "int16": pa.int16(),
        "int32": pa.int32(),
        "float64": pa.float64(),
        "string": pa.string(),
        "bool": pa.bool_(),
        "date32": pa.date32(),
    }
    return pa.schema(
        [
            pa.field(c["name"], types[c["dtype"]], metadata={"description": c["description"]})
            for c in table_columns(table, registry)
        ]
    )
