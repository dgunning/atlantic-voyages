# Schema design: field registry and Parquet tables

Phase 1 design, agreed 2026-10-19. `src/voyages/schema/fields.yaml` is authoritative; this file explains why it looks the way it does.

## What the raw files contain (measured 2026-10-19)

| File | Rows | Cols | Value-label sets |
|---|---|---|---|
| tastdb-exp-2020.sav (Trans-Atlantic) | 36,108 voyages | 274 | 38 |
| I-Am1.0.sav (Intra-American) | 11,521 voyages | 169 | 17 |
| 2010-estimates-SPSS.sav | 11,709 year x carrier x route rows | 36 | 13 |

- 158 of the 169 Intra-American columns are the Trans-Atlantic columns in lowercase. 11 are new (AFRINFO, COMMENTS, Other_Cargo, voyageID2 link to a TA voyage on 66 rows, a few date composites, infant7).
- Voyage IDs do not overlap (TA 1–900237, IA 100002–161266), so one `voyage_id` key covers both.
- Place codes are a single hierarchy encoded in the digits: broad region = code // 10000 * 10000, region = code // 100 * 100, place = full 5-digit code. 947 TA codes, zero conflicts across 24 label sets.
- IA adds 151 place codes and spells 55 shared codes differently (mostly diacritics/variants: Marseille / Marseilles; some not: 10202 "Lagos" vs "Portugal").
- ~18 coded columns use codes absent from their own label set (e.g. 60627/60628 in the embarkation ports, 39999, 80200); 26 labels read "undefined NNN".
- Strings use "" for missing; `filter_$` is a leftover SPSS filter, not data.
- No coordinates anywhere in the .sav files.
- Codebook (2022, PDF p.30): in the expanded dataset a voyage's region code can differ from the one its place code implies (places that changed jurisdiction: Jamaica, Bonaire, Demerara/Berbice). So region columns are kept as recorded, never recomputed from place codes.
- Codebook provenance, first pass over 274 TA variables: 174 recorded, 53 derived (ratios, region/broad-region, year groupings, date composites, age/sex totals), 30 imputed, 17 unclear. Codebook and .sav disagree on the *IMP people counts, DEPTREGIMP(1) and the *7 stage counts ("Derived" in codebook, "Imputed" in .sav).
- *RAT* columns are labelled "Percentage" but stored as 0–1 fractions.
- Codebook label errors to fix in our `label` (keep the original in `source_label`): INTRAAMER copies EVGREEN's label; IA D1SLATR*/DLSLATR* name different events than the codebook; IA *RAT7 say "at first port of purchase".
- 2019 CSV = same 36,108 voyages; usable as a cross-check, not a second source.

## Proposed tables (data/*.parquet)

Core
- `voyages` — one row per voyage, both datasets. Scalar fields only (ship, flag, tonnage, rig, crew totals, outcome codes, imputed totals, year groupings). Columns: `voyage_id`, `dataset`, then registry fields. Codes stay as Int32 codes; names come from joins. Column names are readable snake_case; fields.yaml maps each to its SPSS name.
- `voyages_wide` — convenience: `voyages` + decoded label columns for every coded field (`principal_purchase_place` + `principal_purchase_place_name`), + principal places' region/broad region names. Generated, never edited.

Long tables (where the wide file encodes a repeated structure)
- `voyage_places` — voyage_id, role (departure, intended_embarkation, purchase, principal_purchase, landing, principal_landing, intended_landing, return, construction, registration, call_before_crossing), seq (1..3), place_code, provenance, source_column. ~25 columns fold in here.
- `voyage_dates` — voyage_id, event (departure, purchase_began, left_africa, first_landing, second_landing, third_landing, left_on_return, completed, constructed, registered), year, month, day, date (only when all three known), provenance, source_columns. Partial dates are common (year known, day not), so components stay separate.
- `voyage_people_counts` — voyage_id, stage (1 embarked first port … 7 at departure/arrival, per codebook), category (men, women, boys, girls, males, females, adults, children, infants), count, provenance. Replaces ~70 columns; the *RAT* ratio columns become derived and are recomputable.
- `voyage_crew` — stage counts and deaths (CREW1–5, SAILD1–5, CREWDIED, NDESERT), same long shape.
- `voyage_sources` — voyage_id, seq, source_text (SOURCEA–R). Parsing source text into a sources table is later work.
- `voyage_enslavers` — voyage_id, role (owner, captain), seq, name (OWNERA–P, CAPTAINA–C). Name strings as recorded; no deduplication in Phase 1.

Estimates
- `estimates` — its own table, its own region codes (they don't use the place hierarchy). Whole table is CC BY-NC; every field provenance = derived/imputed per codebook.

Reference (schema/reference/*.csv, generated from value labels, committed for diffability)
- `places.csv` — code, name, level (place/region/broad_region), region_code, broad_region_code, alt_names (IA spellings), lat, lon, coord_source, coord_precision, coord_ref, and map_lat, map_lon, map_precision, map_code.
  - `coord_precision`: `place` (the place itself), `representative` (a "port unspecified" code drawn at the principal port), `region` (a region's centre).
  - Region centres are the region's medoid port: the port with the smallest total distance to the region's other ports. That keeps the point on land and robust to odd filings. Catch-all regions (Other Africa, Americas, Spanish Americas, ...) and broad regions get no point.
  - `map_*` is the point to draw for a code: its own coordinates, else its region's centre, else empty. Apps should style `region` endpoints differently and count, not silently drop, voyages with no point.
  - Coverage (2026-10-19, imputed principal ports): 67% of Trans-Atlantic and 83% of Intra-American voyages have a drawable route. Most of the rest have no imputed endpoint (4,361 TA) or an imputed purchase region of "Other Africa" (7,291 TA): the data does not say where in Africa.
- `nations.csv`, `rigs.csv`, `outcomes.csv` (FATE, FATE2–4 as four small tables or one with `kind`), `ton_types.csv`, `resistance.csv`, `year_periods.csv`, `xmimpflag.csv`, `estimates_*.csv`.
- Codes used but unlabeled get a row with name = null and `note = "code used in data, no label in source"` so joins never drop voyages.

## Query layer: `voyage_endpoints` (Phase 2, 2026-10-19)

`Voyages()` opens an in-memory DuckDB connection: each Parquet table is a view over both
voyage datasets, each reference CSV a small typed table. `voyage_endpoints` is a derived
view (`src/voyages/api/views.py`, registered in fields.yaml with `view: true`), one row per
voyage, for maps.

- Place: the imputed principal place (MJBYPTIMP / MJSLPTIMP), as the site's maps use; else
  the recorded one. The imputed place differs from the recorded one on ~1,800 TA embarkations
  and ~1,500 disembarkations (often recorded "port unspecified", imputed a named port), so
  `*_provenance` is `recorded` only when the two agree.
- Region / broad region: the voyage's own principal region fields, else the place's parents.
- Point: the place's own point (`place`, `representative`); else the centre of the voyage's
  region; else the place's `map_*` fallback. Catch-alls get none.
- Imputed code 99801 "???" (region 99800 "Codes without labels", 5 TA voyages) means the
  imputation had no answer; the site shows "???" too. The recorded principal place is used
  instead (Havana for 4 of the 5).
- `v.endpoint_coverage()` counts voyages per endpoint status (`place`, `representative`,
  `region`, `no_point`, `no_place`) and drawable routes. Full data, 2026-10-19: 24,108 of
  36,108 TA (66.8%) and 9,526 of 11,521 IA (82.7%) drawable.

## Recorded-only queries (2026-10-19)

`recorded_only=True` (API), `.recorded_only()` (on a query) or `--recorded-only` (CLI) reads no
imputed field, for work that must stay within the public-domain data. Nothing is substituted
under the same name:

- Places: `voyage_endpoints_recorded`, built from the recorded principal places (MAJBUYPT,
  MAJSELPT) with regions from the place hierarchy. 18,100 TA voyages are drawable this way,
  against 24,108 with imputed places.
- Years: the recorded dates of the same events (first landing, departure, leaving Africa)
  instead of YEARAM / YEARDEP / YEARAF.
- Totals: named recorded fields; default `captives_on_board_leaving_africa` (TSLAVESD) and
  `captives_arrived_first_landing` (SLAARRIV). `embarked` / `disembarked` raise. Recorded
  counts are sparse (8,300 TA voyages have TSLAVESD, against 34,477 with SLAXIMP), so
  `summary()` reports how many voyages each total covers.
- Imputed columns, the imputed flag and FATE2 raise `ValueError`; `.outcome()` (FATE) and the
  recorded flag (NATIONAL) are available. `where()` conditions are not checked.
- The year groupings YEAR5, YEAR10, YEAR25, YEAR100 group YEARAM (checked for all 47,629
  voyages). They carry `derived_from: [year_arrived_imputed]` in fields.yaml and count as
  imputed for licensing.

## fields.yaml shape

```yaml
- name: principal_purchase_place   # readable snake_case
  spss_name: MAJBUYPT
  label: Principal place of purchase
  source_label: Principal port of slave purchase   # verbatim from .sav
  dtype: int32
  kind: code                # code | count | ratio | date_part | date | text | id | flag
  reference: places
  provenance: recorded      # recorded | imputed | derived
  datasets: [transatlantic, intraamerican]
  table: voyage_places      # where it lands
  long: {role: principal_purchase, seq: 1}
  codebook_section: ...
  codebook_page: ...
```

`label` is ours, in project language; `source_label` keeps the original wording verbatim for traceability.

## Decisions made without asking
- Provenance conflicts resolve to the more restrictive class: if either the codebook or the .sav calls a field imputed, it is `imputed` (CC BY-NC). `provenance_note` records the conflict. Licensing errs safe.
- Technical identifiers and flags (VOYAGEID, voyageID2, INTRAAMER, EVGREEN, XMIMPFLAG) are `derived`: assigned by the compilers, not transcribed. VOYAGE (middle-passage days) and JAMCASPR (standardized price) get `TODO(field)` and an issue, as CLAUDE.md requires.
- `voyage_places` stores region and broad region alongside the place code, as recorded. The places table gives the default parent; a test counts voyages where the two differ.
- Drop `filter_$`. Convert EVGREEN to boolean `in_1999_cdrom`.
- "" -> null, whitespace trimmed, for all strings.
- TA spelling wins for shared place codes; IA spelling kept in alt_names.
- `.sav` is the source of truth; CSV only for a cross-check test.

## Decided with the user (2026-10-19)
- Column names: readable snake_case everywhere (`principal_purchase_place`, `embarked_imputed`, `flag_imputed`). `spss_name` in fields.yaml maps back to the codebook and the literature.
- Coordinates: source them in Phase 1. Take the real points from the IQSS/voyages fixture (`coord_source = slavevoyages`); (0,0) placeholders are treated as missing. Fill gaps by name-matching against GeoNames (CC BY 4.0; `coord_source = geonames`, plus `coord_match` confidence); low-confidence matches stay empty for review. `coord_precision` = place | representative (for "unspecified" codes). Ask the SlaveVoyages team about a licence for their coordinates in parallel.

## Coordinate sources checked (2026-10-19)
- rice-crc/voyages-api is now IQSS/voyages-api: no licence; coordinates live in its database, not the repo. Its timelapse port_routes.json is keyed by internal DB ids and has wrong points (Alicante at Huelva).
- IQSS/voyages (legacy site): no licence. fixtures/test_set_200_voyages.json has 830 places keyed by SPSS code with lat/lon. Covers 828 of our 994 place codes, but 269 are (0,0) placeholders, so ~560 usable (56%). "Unspecified" codes sit on a representative port (Jamaica, unspecified = Kingston). 26 names differ, one is a different place entirely (10115).
- The legacy repo also has an Oct 2023 georecode (new, merged, renumbered place codes). Our 2020 .sav predates it, so current site place codes can differ from ours. Tests that compare to the live site must allow for that.

## Still open
- Licence for SlaveVoyages coordinates (to ask the project team).
- `TODO(field)`: VOYAGE (middle-passage days: transcribed or computed?), JAMCASPR (standardization method).
- 2023 codebook edition: not on the legacy server.
