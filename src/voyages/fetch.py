"""Download the official SlaveVoyages data files into the raw cache.

The manifest below is the only place download URLs live. Every entry
records the dataset it belongs to and, once a file has been fetched and
verified, its SHA-256. Keep ``docs/DATA.md`` in step with this file.

Downloads come from the legacy site, which still serves the static
files (the main site is a single-page app and does not expose them).
"""

from __future__ import annotations

import hashlib
import shutil
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from voyages import __version__
from voyages.config import raw_dir

USER_AGENT = f"voyages/{__version__} (+https://github.com/dgunning/voyages)"

LEGACY_BASE = "https://legacy.slavevoyages.org/documents/download/"


@dataclass(frozen=True)
class RawFile:
    name: str
    dataset: str  # transatlantic | intraamerican | estimates | codebook
    description: str
    sha256: str | None = None  # filled in after first verified download
    url: str | None = None

    @property
    def download_url(self) -> str:
        return self.url or LEGACY_BASE + self.name


# Current versions first; older versions are listed for reproducibility
# of published analyses, not fetched by default.
MANIFEST: tuple[RawFile, ...] = (
    RawFile(
        "tastdb-exp-2020.sav",
        "transatlantic",
        "Trans-Atlantic Slave Trade Database, expanded dataset, 2020 (SPSS)",
    ),
    RawFile(
        "tastdb-exp-2019.csv",
        "transatlantic",
        "Trans-Atlantic Slave Trade Database, expanded dataset, Dec 2019 (CSV, 36,108 voyages)",
    ),
    RawFile(
        "I-Am1.0.sav",
        "intraamerican",
        "Intra-American Slave Trade Database v1.0 (SPSS)",
    ),
    RawFile(
        "I-Am1.0.csv",
        "intraamerican",
        "Intra-American Slave Trade Database v1.0 (CSV)",
    ),
    RawFile(
        "2010-estimates-SPSS.sav",
        "estimates",
        "Estimates of the size and direction of the trade, 2010 (SPSS); CC BY-NC",
    ),
    RawFile(
        "2010-estimates-excel.xlsx",
        "estimates",
        "Estimates of the size and direction of the trade, 2010 (Excel); CC BY-NC",
    ),
    RawFile(
        "SPSS_Codebook_2023-11-06.pdf",
        "codebook",
        "SPSS codebook, 6 November 2023 edition",
    ),
    RawFile(
        "2010estimates-method.pdf",
        "codebook",
        "Estimates methodology essay, 2010",
    ),
)

DEFAULT_DATASETS = ("transatlantic", "intraamerican", "estimates", "codebook")


def sha256_of(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while block := f.read(chunk):
            h.update(block)
    return h.hexdigest()


def fetch_one(entry: RawFile, dest_dir: Path | None = None, *, force: bool = False) -> Path:
    """Download one manifest entry, verifying the checksum when known."""
    dest_dir = dest_dir or raw_dir()
    dest = dest_dir / entry.name
    if dest.exists() and not force:
        if entry.sha256 and sha256_of(dest) != entry.sha256:
            raise RuntimeError(f"{dest} exists but its SHA-256 does not match the manifest")
        return dest
    tmp = dest.with_suffix(dest.suffix + ".part")
    req = urllib.request.Request(entry.download_url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as r, tmp.open("wb") as f:  # noqa: S310
        shutil.copyfileobj(r, f, length=1 << 20)
    digest = sha256_of(tmp)
    if entry.sha256 and digest != entry.sha256:
        tmp.unlink()
        raise RuntimeError(f"checksum mismatch for {entry.name}: got {digest}")
    tmp.replace(dest)
    return dest


def fetch_all(
    datasets: tuple[str, ...] = DEFAULT_DATASETS,
    dest_dir: Path | None = None,
    *,
    force: bool = False,
) -> list[Path]:
    return [fetch_one(e, dest_dir, force=force) for e in MANIFEST if e.dataset in datasets]


def verify(dest_dir: Path | None = None) -> dict[str, str]:
    """Return ``{filename: status}`` for every manifest entry.

    Status is one of ``ok``, ``missing``, ``mismatch`` or ``unverified``
    (present, but the manifest has no checksum for it yet).
    """
    dest_dir = dest_dir or raw_dir()
    out: dict[str, str] = {}
    for e in MANIFEST:
        p = dest_dir / e.name
        if not p.exists():
            out[e.name] = "missing"
        elif e.sha256 is None:
            out[e.name] = "unverified"
        elif sha256_of(p) == e.sha256:
            out[e.name] = "ok"
        else:
            out[e.name] = "mismatch"
    return out
