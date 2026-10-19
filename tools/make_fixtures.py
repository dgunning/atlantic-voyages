"""Write the committed test fixture: a sample of real voyages as a small .sav.

Dev-time tool. Reads the full raw file and writes
tests/fixtures/<dataset>_sample.sav with the same columns, variable labels
and value labels, so the ingest runs on it unchanged.

The sample is the voyages named in tests (checked against the site) plus a
seeded random draw stratified by decade of arrival, so every period is
represented. Redistribution of these rows is covered by NOTICE.

usage: uv run python tools/make_fixtures.py [transatlantic]
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pyreadstat

from voyages.config import raw_dir
from voyages.ingest.reference import SAV_FILES

FIXTURES = Path(__file__).parents[1] / "tests" / "fixtures"
SEED = 20261019
SAMPLE_SIZE = 300

# Voyages that tests check against slavevoyages.org. Keep in step with tests.
NAMED = {
    "transatlantic": [1, 113, 3844, 5096, 7557, 8110, 9727, 10390, 11502, 91000],
    # 12 site-checked voyages, 2 with known bad counts, 2 with links to
    # Trans-Atlantic voyages (111086 lists two).
    "intraamerican": [
        100008,
        100030,
        100037,
        101481,
        101547,
        101747,
        101756,
        103577,
        103706,
        105692,
        108699,
        112742,
        105238,
        105990,
        111086,
        100034,
    ],  # fmt: skip
}
YEAR_COL = {"transatlantic": "YEARAM", "intraamerican": "yearam"}


def make(dataset: str) -> Path:
    src = raw_dir() / SAV_FILES[dataset]
    df, meta = pyreadstat.read_sav(src, apply_value_formats=False)
    id_col = next(c for c in df.columns if c.upper() == "VOYAGEID")
    named = df[df[id_col].isin(NAMED[dataset])]
    if len(named) != len(NAMED[dataset]):
        raise SystemExit(f"named voyages missing from {src.name}")
    rest = df.drop(named.index)
    decade = (rest[YEAR_COL[dataset]] // 10).fillna(-1)
    per = max(1, (SAMPLE_SIZE - len(named)) // decade.nunique())
    drawn = rest.groupby(decade, group_keys=False).apply(
        lambda g: g.sample(min(len(g), per), random_state=SEED)
    )
    top_up = SAMPLE_SIZE - len(named) - len(drawn)
    if top_up > 0:
        drawn = pd.concat([drawn, rest.drop(drawn.index).sample(top_up, random_state=SEED)])
    sample = pd.concat([named, drawn]).sort_values(id_col)

    # A date column that is empty in the sample comes back as object dtype;
    # pyreadstat would write it as a string with a date format. Keep it numeric.
    for col in sample.columns:
        if sample[col].dtype == object and sample[col].isna().all():
            sample[col] = sample[col].astype("float64")

    out = FIXTURES / f"{dataset}_sample.sav"
    out.parent.mkdir(parents=True, exist_ok=True)
    value_labels = {
        col: meta.value_labels[name]
        for col, name in meta.variable_to_label.items()
        if name in meta.value_labels
    }
    pyreadstat.write_sav(
        sample,
        out,
        column_labels=meta.column_names_to_labels,
        variable_value_labels=value_labels,
        variable_format=meta.original_variable_types,
        variable_measure=meta.variable_measure,
        compress=True,
    )
    print(f"{out}: {len(sample)} voyages, {sample.shape[1]} columns")
    return out


if __name__ == "__main__":
    for ds in sys.argv[1:] or ["transatlantic", "intraamerican"]:
        make(ds)
