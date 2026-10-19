"""Where raw downloads and built data live on disk.

Raw files are never committed. They are cached outside the repository,
in ``$VOYAGES_DATA_DIR`` if set, otherwise in the platform user cache
directory (``~/.cache/voyages`` on Linux, ``~/Library/Caches/voyages``
on macOS).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ENV_VAR = "VOYAGES_DATA_DIR"


def data_dir() -> Path:
    """Return the data directory, creating it if needed."""
    env = os.environ.get(ENV_VAR)
    if env:
        base = Path(env).expanduser()
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Caches" / "voyages"
    else:
        xdg = os.environ.get("XDG_CACHE_HOME")
        base = (Path(xdg) if xdg else Path.home() / ".cache") / "voyages"
    base.mkdir(parents=True, exist_ok=True)
    return base


def raw_dir() -> Path:
    """Directory for the official downloads (.sav, .csv, codebook)."""
    d = data_dir() / "raw"
    d.mkdir(parents=True, exist_ok=True)
    return d


def built_dir() -> Path:
    """Directory for Parquet files produced by ``voyages build``."""
    d = data_dir() / "built"
    d.mkdir(parents=True, exist_ok=True)
    return d
