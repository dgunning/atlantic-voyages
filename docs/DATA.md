# Data provenance

Every raw file this library consumes is listed here with its source URL,
the date it was downloaded, and its SHA-256. The same manifest lives in
`src/voyages/fetch.py`; keep the two in step. Raw files are cached in
`$VOYAGES_DATA_DIR/raw` (default `~/.cache/voyages/raw`) and are never
committed.

The main site (www.slavevoyages.org) is a single-page application and
does not expose the files directly. The legacy site still serves them
from `https://legacy.slavevoyages.org/documents/download/<filename>`.
Downloads pages, for reference:

- Trans-Atlantic: https://legacy.slavevoyages.org/blog/downloads-trans-atlantic
- Intra-American: https://legacy.slavevoyages.org/blog/downloads-intra-american
- People (PAST): https://legacy.slavevoyages.org/resources/downloads

## License

Data transcribed from historical documents: public domain.
Imputed fields (marked `*` on the site) and the entire Estimates
database: CC BY-NC 4.0, credit SlaveVoyages. Source:
https://www.slavevoyages.org/blog/faqs

## Current files

| File | Dataset | Description | Downloaded | SHA-256 |
|---|---|---|---|---|
| `tastdb-exp-2020.sav` | transatlantic | Expanded dataset, 2020 (SPSS) | 2026-10-19 | `39585586cb7b17cdd38cd20a1ac77fea109f7855f5ae76df19a0708a65e5bc21` |
| `tastdb-exp-2019.csv` | transatlantic | Expanded dataset, Dec 2019 (CSV; 36,108 voyages) | 2026-10-19 | `3fbad142356e30a4662c7f455321d19b70d79770cfa0397278894bb9ae36096f` |
| `I-Am1.0.sav` | intraamerican | Intra-American v1.0 (SPSS) | 2026-10-19 | `7750dcd15454fd171d129ff2d96daa6dba3843f1a9fa2011094ecadb383d01e4` |
| `I-Am1.0.csv` | intraamerican | Intra-American v1.0 (CSV) | 2026-10-19 | `d9a4ebf7d2e0082948682ffba1ea9db315216401dcef9444bc491337fc30b47d` |
| `2010-estimates-SPSS.sav` | estimates | Estimates, 2010 (SPSS); CC BY-NC | 2026-10-19 | `e49ec2b12d39b82ad0f3ba15705ac0223581bd558785ab416977c99bd6171e3d` |
| `2010-estimates-excel.xlsx` | estimates | Estimates, 2010 (Excel); CC BY-NC | 2026-10-19 | `4d73f41c5d48f578f5ede82a6a41e15a97b7936d17509fcc5c78f1c9e0205292` |
| `SPSS_Codebook_2022.pdf` | codebook | Codebook, 2022 edition | 2026-10-19 | `fff98c12c8e3e11e398a53c128c5a017bd2b4ac9631ffd28ab120c374d26a83a` |
| `2010estimates-method.pdf` | codebook | Estimates methodology essay | 2026-10-19 | `57f28971d407314af43eeff5eb9c24cba41ce33f6e4ce7abe65adc07dee44b9b` |

Fill in the `Downloaded` and `SHA-256` columns after the first verified
fetch (`voyages fetch`, then `sha256sum` or `voyages verify`), and copy
the hashes into `MANIFEST` in `fetch.py`.

## Older versions (not fetched by default)

Listed on the Trans-Atlantic downloads page, same base URL: `tastdb-exp-2019.sav`,
`tastdb-exp-2016.sav`, `tastdb-2016.sav`, `tastdb-exp-2010.sav`, `tastdb-2010.sav`,
`tastdb-2010.csv`, `tastdb-exp-2008.sav`, `tastdb-1999.sav` (original CD-ROM),
`SPSS_Codebook_2019.pdf`. Useful for reproducing
published analyses that cite a specific version.

## Place coordinates (curated, committed)

The .sav files carry no coordinates. `src/voyages/schema/reference/curated/place_coordinates.csv`
is built by `tools/place_coordinates.py` (dev-time, not part of `voyages build`) from:

| Source | What | Retrieved | Licence |
|---|---|---|---|
| SlaveVoyages legacy site fixture: `IQSS/voyages` @ `cf1e5a8` (2013-07-19), `voyages/apps/voyage/fixtures/test_set_200_voyages.json`, SHA-256 `2d98130a955237f42719ea567e1b1d2b8eb27686a0356045c4e3c10ca37394f4` | Lat/lon for 830 place codes, 269 of them (0,0) placeholders | 2026-10-19 | None stated in the repo; asked of the SlaveVoyages team (open) |
| GeoNames (https://www.geonames.org), country dumps from https://download.geonames.org/export/dump/ | Reviewed matches for places the fixture lacks; each row cites its `geonames:<id>` | 2026-10-19 | CC BY 4.0 |

Six fixture points were found wrong on review (2026-10-19) and are rejected in
`FIXTURE_REJECT` in `tools/place_coordinates.py`: Cumberland Island GA
(longitude sign flipped), Annobon (lat/lon swapped), Sierra Leone estuary
(at sea), Ponta Negro (wrong state), Bengal (point in Jamaica), Basse
Indres (point near Nantes, code under India). The first five now use
GeoNames records. A test flags any point more than 3,500 km from its
region's centre.

Rules: fixture points are used only when the fixture's place name agrees
with ours (codes were reassigned after 2013), and (0,0) is treated as
missing. GeoNames points are used only when a reviewer accepted the
match. Every row records `coord_source` and `coord_ref`. Regions and broad
regions have no point coordinates.

These two sources are the one exception to "raw data comes only from
slavevoyages.org", agreed 2026-10-19 because the downloads have no
coordinates at all.

## Corrections applied at ingest

Values that cannot be right are listed one by one in `KNOWN_BAD_VALUES`
in `src/voyages/ingest/voyages.py`, set to null with a warning, and never
rounded. Any unlisted bad value fails the build.

- Intra-American voyages 105238 and 105990: fractional people counts
  (0.2 boys, 0.5 infants, 0.556 boys, 0.2 girls, 0.333 females). The site
  shows shares for both that cannot add up.

The Estimates `.sav` rounds each row to whole people, so totals can differ
slightly from the site, which sums unrounded values. Embarked by national
carrier (`totexports`) is within 15 people of
https://legacy.slavevoyages.org/assessment/estimates (checked 2026-10-19;
Netherlands exact; total 12,521,352 vs 12,521,337). The rows have no natural
key, so the table carries `row`, the row number in the source file.

The Intra-American site pages agree with `I-Am1.0.sav` for all 14
voyages checked (2026-10-19), unlike the Trans-Atlantic pages (below).

## Open questions

- **The website shows newer data than `tastdb-exp-2020.sav`.** Checked
  2026-10-19 on https://legacy.slavevoyages.org/voyage/<id>/variables for
  12 voyages. 10 agree with the 2020 file on vessel, captain, year and
  imputed totals. 2 differ: voyage 17223 (site 361 embarked / 319
  disembarked, file 273 / 236; the site also has a recorded 319 landed that
  the file lacks) and voyage 11408 (site 333 / 291, file 303 / 279). Place
  names on the site also follow the Oct 2023 recode ("Luanda" for "St. Paul
  de Loanda", "place unspecified" for "port unspecified"). Our build matches
  the file exactly. Is there a newer bulk download than the 2020 .sav?

- Licence for the SlaveVoyages fixture coordinates (ask the project team).
- 14 place codes used by 30 Trans-Atlantic voyages have no label in any
  source file (e.g. 60628, 41252, 21013). They stay in places.csv with an
  empty name and a note.
- Dixcove (code 60508), a fort town on the western Ghana coast, is coded under
  the Bight of Benin (60500) in the source, though it lies on the Gold Coast
  (60400), west of Elmina. Its map point (4.8, -1.95) is right; the code puts it
  in the wrong region. It is a recorded place of purchase for 9 Trans-Atlantic
  voyages. Kept as in the source, since regions are never recomputed (found
  2026-10-19). Worth raising with the SlaveVoyages team; check whether the Oct
  2023 recode moved it.

- The 6 Nov 2023 codebook (`SPSS_Codebook_2023-11-06.pdf`) returns 404 on
  the legacy site (checked 2026-10-19). The manifest uses the 2022 edition
  until a source for the 2023 edition is found.

- The 2020 `.sav` exists but no 2020 `.csv` is listed; the newest CSV is Dec 2019.
  Confirm whether the main site's "download" button produces a newer CSV export,
  and whether the 2020 `.sav` is the canonical current release.
- The People / African Names data has its own downloads page; add entries once
  the Phase 1 ingest reaches it.
- **Is there a newer bulk export? Checked 2026-10-19: no official export matches the live
  site, but there is a 2023 release on Harvard Dataverse.** Decided 2026-10-19: stay on the
  2020 `.sav` for now; revisit the 2023 release later.
  - Dataverse deposits by the project, anonymous download, MD5 on each record; terms point
    to https://www.slavevoyages.org/about/about#legal/9/en/ (not yet read):
    Trans-Atlantic https://doi.org/10.7910/DVN/DGIHX9 (v1.0, 2023-05-30) and Intra-American
    https://doi.org/10.7910/DVN/QD3JSH (v2.0, 2023-05-30). They also hold the older
    releases and `SPSS_Codebook_2022.pdf`.
  - `Voyages-TSTD-May2023` (file id 7103680, `?format=original` is CSV, 22,832,996 bytes,
    MD5 `36a2517c6a48b249709d62ef06bc517d`, SHA-256
    `5b26b9489216e6cdd4332e28cb32119f4d878be2c7a0a821c5651f5c531c1f29`): 36,079 voyages,
    314 columns, same SPSS variable names. Against our 2020 build: 42 voyages new, 71 gone,
    401 of the 36,037 shared voyages with different imputed totals. Voyages 17223 and 11408
    still have the 2020 values (273/236, 303/279), so it is not the live site's data either.
    Place codes not yet compared with the Oct 2023 recode.
  - `Voyages-IAm-May2023` (file id 7103685, MD5 `515f5a3b01067742de91b1a50df6bad8`): same
    header style; values not yet compared.
  - The live site's download button posts to `IQSS/voyages-api`
    `voyage/VoyageDownload/` (`src/api/voyage/views.py:102-148`), which needs an API token
    and returns the new API schema, not SPSS names. Not usable as a reproducible raw source,
    and CLAUDE.md rules out the live API at runtime.
  - Options: stay on 2020; switch to the 2023 Dataverse files (CSV, needs a CSV ingest path
    and a fresh site check); or offer both as versions. Asking the SlaveVoyages team for a
    current bulk export goes with the coordinates licence question.
