"""The field registry: every column the library produces, described once.

``fields.yaml`` next to this file is authoritative. Each field has a
readable ``name`` (its column in ``voyages_wide`` and its identifier in
the API), the ``spss_name`` it comes from, a ``label`` in project
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
DATASETS = ("transatlantic", "intraamerican", "estimates")


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
            **{**f, "datasets": tuple(f["datasets"]), "source_label": f.get("source_label") or {}}
        )
        for f in doc["fields"]
    )
    return Registry(fields=fields, tables=doc["tables"], dropped=tuple(doc.get("dropped", ())))
