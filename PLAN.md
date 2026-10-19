# PLAN.md

Status: Phase 0 done — all raw files fetched and checksummed (2026-10-19); `voyages verify` reports ok for every file. Phase 1 schema design agreed (docs/schema.md). fields.yaml done. Next: reference tables (places with coordinates, nations, rigs, outcomes, ...) in src/voyages/schema/reference/.

## Goal

An open-source Python library (Apache-2.0) that makes the SlaveVoyages
databases easy to use from code: reproducible ingest from the official
downloads, a provenance-aware field registry, typed Parquet, a DuckDB
query layer with a small fluent API, and a set of worked analyses.

Success looks like:

```python
from voyages import Voyages

v = Voyages()                      # downloads/builds on first use
df = (v.transatlantic
       .disembarked_in("Jamaica")
       .embarked_from("Bight of Biafra")
       .between(1700, 1800)
       .by_decade(["embarked", "disembarked"]))
print(voyages.citation())
```

## Source datasets

| Dataset | Files | Notes |
|---|---|---|
| Trans-Atlantic | `tastdb-exp-*.sav`, `.csv` | ~36k voyages, ~300 columns, SPSS codes + value labels |
| Intra-American | `I-Am*.sav`, `.csv` | ~11k voyages, same codebook family |
| Estimates | site export | modelled totals by region x region x year; fully CC BY-NC |
| People (African Names) | site export | ~90k individuals, links to voyage ID |
| Codebook | `SPSS_Codebook_*.pdf` | variable names, labels, code lists |

Download URLs, dates, and checksums go in `docs/DATA.md` as each is added.

## Phases

### Phase 0 — Bootstrap (1 session)

- [x] `uv init`, package skeleton (`src/voyages/`), `pyproject.toml`, ruff, pytest
- [x] `CLAUDE.md`, `PLAN.md`, `NOTICE`, `LICENSE` (Apache-2.0), `docs/DATA.md`
- [x] Download the Trans-Atlantic and Intra-American `.sav` + `.csv` and the codebook into `$VOYAGES_DATA_DIR`; record provenance in `docs/DATA.md` (fetched and checksummed 2026-10-19; codebook is the 2022 edition, 2023 edition 404s)
- [x] `voyages/citation.py`
- [ ] Decide the final package name (check PyPI); update CLAUDE.md

### Phase 1 — Ingest and registry (3–5 sessions)

Start in plan mode: have Claude read the `.sav` metadata via `pyreadstat`
and the codebook, then propose `fields.yaml` and the Parquet schema
before writing ingest code.

- [x] `voyages fetch`: download with checksum verification, cache outside repo (stdlib urllib; checksums pending first run)
- [ ] `ingest/transatlantic.py`: load `.sav`, coerce types, decode coded fields using value labels
- [x] `schema/fields.yaml`: every column with `name`, `label`, `dtype`, `provenance` (recorded/imputed/derived), `dataset`, `codebook_section` (lives in `src/voyages/schema/` so it ships with the package; 278 voyage + 36 Estimates fields; loader `voyages.schema.load()`)
- [ ] Reference tables in `schema/reference/`: places (port/region/broad region + lat/lon), nationalities, rig types, outcomes, sources
- [ ] Long-format tables where the wide file is awkward: `voyage_dates`, `voyage_places` (place + role: departure, purchase, landing, return), `voyage_sources`, `voyage_people_counts`
- [ ] Wide convenience table `voyages_wide` for people who just want a DataFrame
- [ ] `voyages build`: raw -> Parquet in one command
- [ ] Fixtures: a committed sample of ~300 voyages per dataset; tests run offline
- [ ] Tests: row counts, a dozen known voyage IDs checked against the site, schema == registry
- [ ] Repeat ingest for Intra-American; unify schema where it genuinely matches, don't force it where it doesn't
- [ ] Estimates and African Names as separate tables joined on voyage ID

### Phase 2 — Query layer (2–3 sessions)

- [ ] DuckDB connection over the Parquet directory, lazy, read-only
- [ ] Fluent API: dataset selectors, place filters at any hierarchy level, year ranges, outcome filters, `.by_decade()`, `.by_region()`, `.summary()`
- [ ] Return types: pandas default, `.to_polars()`, `.to_arrow()`, raw SQL escape hatch
- [ ] CLI: `voyages query` with the same filters, CSV/Parquet output
- [ ] Field-level helpers: `v.fields()`, `v.describe("MAJBUYPT")`, provenance filtering (`recorded_only=True`)

### Phase 3 — Worked analyses (2–3 sessions)

Each is a notebook under `notebooks/`, executed in CI, and the basis of a README section.

- [ ] Arrivals into Jamaica by African embarkation region, by decade, recorded vs imputed vs Estimates
- [ ] Re-exports from Jamaica via the Intra-American data
- [ ] Bight of Biafra vs Gold Coast vs Bight of Benin: destinations over time
- [ ] Mortality and voyage duration by route and period
- [ ] A map of embarkation -> disembarkation flows for one decade (static, matplotlib or plotly)

### Phase 4 — Release and follow-ons

- [ ] README with the five-line example, citation, and license section
- [ ] PyPI release (0.1.0)
- [ ] GitHub Actions: lint, offline tests, notebook execution
- [ ] Follow-on candidates, in rough priority: MCP server exposing the query layer; a versioned data package (Parquet + registry) on Hugging Face or Zenodo for people who don't want Python; People-data tooling for genealogical linking

## Open questions

- Final package name
- Whether to vendor the reference tables or regenerate them from the `.sav` value labels each build (lean: regenerate, then commit the result for diffability)
- How much of the Estimates methodology to expose vs just the numbers
- ~~Column names~~ decided 2026-10-19: readable snake_case; `spss_name` in fields.yaml maps back (see docs/schema.md)
- Licence for SlaveVoyages place coordinates (ask the project team); GeoNames fills gaps meanwhile

## Session log

Append one line per Claude Code session: date, phase, what landed, what's next.
- 2026-10-19 — Phase 0 — scaffold, citation, fetch manifest + verify, LICENSE/NOTICE/DATA.md, 15 offline tests passing. Next: fetch raw files locally, record checksums, Phase 1 plan mode on the .sav metadata.
- 2026-10-19 — Phase 0/1 — fetched + checksummed raw files (codebook 2022: 2023 edition 404s); inspected .sav metadata and codebook; agreed schema design in docs/schema.md (readable column names, long tables, places with coords from SlaveVoyages fixture + GeoNames). Next: fields.yaml + reference tables.
- 2026-10-19 — Phase 1 — fields.yaml bootstrapped (278 voyage + 36 Estimates fields, all .sav columns covered or dropped with reason), registry loader + 14 tests. Next: reference tables.
