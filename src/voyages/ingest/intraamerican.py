"""Ingest the Intra-American Slave Trade Database (version 1.0).

Source: I-Am1.0.sav from legacy.slavevoyages.org (see docs/DATA.md).
The work is done by :mod:`voyages.ingest.voyages`, driven by the registry.
Voyage IDs do not overlap with the Trans-Atlantic database, so both
datasets share the same tables, told apart by the ``dataset`` column.
"""

from __future__ import annotations

from pathlib import Path

import pyarrow as pa

from voyages.config import built_dir, raw_dir
from voyages.ingest import voyages
from voyages.ingest.reference import SAV_FILES

DATASET = "intraamerican"


def build_tables(sav_path: Path | None = None) -> dict[str, pa.Table]:
    return voyages.build_tables(DATASET, sav_path or raw_dir() / SAV_FILES[DATASET])


def build(sav_path: Path | None = None, out_dir: Path | None = None) -> dict[str, Path]:
    """Build and write every Intra-American table. Returns {table: path}."""
    return voyages.write(build_tables(sav_path), DATASET, out_dir or built_dir())
