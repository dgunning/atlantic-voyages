"""Execute every notebook top to bottom. They hold their own assertions.

Needs the full data (VOYAGES_DATA_DIR and `voyages build`), so it is marked
``fulldata``. Equivalent to `uv run jupyter nbconvert --execute` on each.
"""

import os
from pathlib import Path

import pytest

NOTEBOOKS = sorted((Path(__file__).parent.parent / "notebooks").glob("*.ipynb"))


@pytest.mark.fulldata
@pytest.mark.skipif(not os.environ.get("VOYAGES_DATA_DIR"), reason="needs VOYAGES_DATA_DIR")
@pytest.mark.parametrize("path", NOTEBOOKS, ids=[p.stem for p in NOTEBOOKS])
def test_notebook_runs(path, tmp_path):
    nbformat = pytest.importorskip("nbformat")
    nbclient = pytest.importorskip("nbclient")
    nb = nbformat.read(path, as_version=4)
    # Run in the notebook's directory (figures/ paths are relative), keep outputs out of git.
    nbclient.NotebookClient(
        nb, timeout=600, resources={"metadata": {"path": str(path.parent)}}
    ).execute()
    nbformat.write(nb, tmp_path / path.name)
