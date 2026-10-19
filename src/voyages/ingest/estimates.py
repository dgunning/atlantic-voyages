"""Ingest the 2010 Estimates database (Eltis and Richardson).

Source: 2010-estimates-SPSS.sav from legacy.slavevoyages.org (see
docs/DATA.md). The whole table is CC BY-NC 4.0. Rows are estimation cells
(year x national carrier x route x coverage tier) with their own region
and route codes, not voyage place codes. They have no natural key, so the
table carries ``row``, the 1-based row number in the source file.
"""

from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from voyages import schema
from voyages.config import built_dir, raw_dir
from voyages.ingest import voyages
from voyages.ingest.reference import SAV_FILES

DATASET = "estimates"


def build_table(sav_path: Path | None = None) -> pa.Table:
    reg = schema.load()
    raw = voyages.read_sav(sav_path or raw_dir() / SAV_FILES[DATASET])
    typed = voyages.coerce(raw, DATASET, reg)
    typed.insert(0, "row", range(1, len(typed) + 1))
    return voyages._to_arrow("estimates", typed, reg)


def build(sav_path: Path | None = None, out_dir: Path | None = None) -> dict[str, Path]:
    """Build and write the Estimates table. Returns {"estimates": path}."""
    path = (out_dir or built_dir()) / "estimates" / f"{DATASET}.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(build_table(sav_path), path, compression="zstd")
    return {"estimates": path}
