# CLAUDE.md

Open-source Python library for working with the SlaveVoyages databases
(https://www.slavevoyages.org): the Trans-Atlantic Slave Trade Database,
the Intra-American Slave Trade Database, the Estimates database, and the
People databases (African Names, enslavers). The goal is a clean, typed,
provenance-aware data layer with a small query API, in the spirit of
edgartools: turn a messy public dataset into something a developer or
historian can use in five lines of Python.

Working package name: `voyages` (rename before first PyPI release). Source lives under `src/voyages/` (uv src layout).

## Subject matter and language

This is data about roughly 12.5 million people who were trafficked. The
code, docs, tests, and commit messages should reflect that.

- Follow the source's terminology: "enslaved people", "captives",
  "slaving voyages", "embarked" / "disembarked". Do not write "slaves" as a
  noun; do not write "cargo" for people. "Slave ship" is acceptable only
  when quoting a source.
- Do not invent cute names for tables, fixtures, or test data.
- Example and fixture voyages are real voyages from the dataset; treat
  them as such.

## Data provenance and licensing (non-negotiable)

- Raw downloads come only from slavevoyages.org (the `.sav` and `.csv`
  files and the PDF codebook). Record file name, URL, download date, and
  SHA-256 in `docs/DATA.md` whenever a raw file is added or refreshed.
  One exception: place coordinates (absent from the downloads) come from
  the SlaveVoyages legacy repo fixture and GeoNames (CC BY 4.0), curated
  by `tools/place_coordinates.py`, with a source and reference on every
  row. See `docs/DATA.md`.
- Data transcribed from historical documents is public domain. Imputed
  fields (marked `*` on the site) and the entire Estimates database are
  CC BY-NC 4.0. Every field in the registry carries `provenance:
  recorded | imputed | derived`. Never drop or obscure that flag.
- The library code is Apache-2.0. The bundled sample data and any
  redistributed full data carry the SlaveVoyages attribution and license
  notice in `NOTICE` and in the package metadata.
- The canonical citation string lives in `voyages/citation.py` and is
  exposed as `voyages.citation()`. Every README example ends by
  showing it once.

## Architecture

```
raw downloads (.sav/.csv, cached outside the repo, never committed)
  -> ingest/   pyreadstat load, type coercion, code decoding
  -> schema/   fields.yaml registry + reference tables (places, flags, rigs, outcomes)
  -> data/     typed Parquet, long-format where it makes sense
  -> api/      DuckDB-backed query layer and a thin fluent Python API
  -> cli/      `voyages fetch`, `voyages verify`, `voyages build`, `voyages query`
```

- `pyreadstat` reads the `.sav` files and returns variable labels and
  value labels. Use those as the primary source of field metadata; the
  PDF codebook is the tie-breaker when labels are missing or wrong.
- `schema/fields.yaml` is authoritative. Adding a column anywhere means
  adding it to the registry first, with label, type, provenance, and
  source dataset. CI fails if the Parquet schema and the registry
  disagree.
- Reference tables (ports, regions, broad regions, nationalities, rig
  types, voyage outcomes) are data, not enums in code. They live in
  `schema/reference/*.csv` and get loaded into DuckDB like everything
  else. Places carry the port -> region -> broad-region hierarchy and
  coordinates.
- Everything under `data/` regenerates from raw with one command
  (`voyages build`). Never hand-edit Parquet or derived CSVs.
- Query results return pandas by default, with `.to_polars()` and
  `.to_arrow()` available. Keep the fluent API thin; DuckDB does the work.

## Tests

- Fixture-first. `tests/fixtures/` holds a committed sample of a few
  hundred voyages from each dataset plus the full reference tables. The
  default test run needs no network and no full download.
- Integration tests that need the full data are marked
  `@pytest.mark.fulldata` and skipped unless `VOYAGES_DATA_DIR` is set.
- Every ingest change needs an assertion against a value visible on the
  site (a known voyage ID's embarked count, a known total for a
  region/decade). Record the URL you checked in the test docstring.
- Every derived field needs a test showing the derivation on at least
  one real voyage.

## Working conventions

- Python 3.11+, managed with `uv`. `uv run pytest` must pass before any
  commit. `ruff` for lint and format.
- Prefer small PR-sized changes. One dataset, one phase, one session.
- When unsure about a field's meaning, read the codebook in
  `docs/codebook/` before guessing; if still unsure, leave a `TODO(field)`
  in `fields.yaml` and open an issue rather than inventing a label.
- Don't call the live SlaveVoyages API from library code. It's useful
  for reading their models (`rice-crc/voyages-api` on GitHub) and for
  spot-checking values, not as a runtime dependency.
- Keep notebooks in `notebooks/` executable top to bottom with
  `uv run jupyter nbconvert --execute`; they double as integration tests
  and README material.

## Current phase

See `PLAN.md`. Update the "Status" line there at the end of each session.
