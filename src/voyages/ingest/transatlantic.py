"""Ingest the Trans-Atlantic Slave Trade Database (expanded dataset, 2020).

Source: tastdb-exp-2020.sav from legacy.slavevoyages.org (see docs/DATA.md).
The work is done by :mod:`voyages.ingest.voyages`, driven by the registry.
"""

from __future__ import annotations

from pathlib import Path

import pyarrow as pa

from voyages.config import built_dir, raw_dir
from voyages.ingest import voyages
from voyages.ingest.reference import SAV_FILES

DATASET = "transatlantic"


def build_tables(sav_path: Path | None = None) -> dict[str, pa.Table]:
    return voyages.build_tables(DATASET, sav_path or raw_dir() / SAV_FILES[DATASET])


def build(sav_path: Path | None = None, out_dir: Path | None = None) -> dict[str, Path]:
    """Build and write every Trans-Atlantic table. Returns {table: path}."""
    return voyages.write(build_tables(sav_path), DATASET, out_dir or built_dir())
