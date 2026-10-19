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
| `tastdb-exp-2020.sav` | transatlantic | Expanded dataset, 2020 (SPSS) | — | — |
| `tastdb-exp-2019.csv` | transatlantic | Expanded dataset, Dec 2019 (CSV; 36,108 voyages) | — | — |
| `I-Am1.0.sav` | intraamerican | Intra-American v1.0 (SPSS) | — | — |
| `I-Am1.0.csv` | intraamerican | Intra-American v1.0 (CSV) | — | — |
| `2010-estimates-SPSS.sav` | estimates | Estimates, 2010 (SPSS); CC BY-NC | — | — |
| `2010-estimates-excel.xlsx` | estimates | Estimates, 2010 (Excel); CC BY-NC | — | — |
| `SPSS_Codebook_2023-11-06.pdf` | codebook | Codebook, 6 Nov 2023 edition | — | — |
| `2010estimates-method.pdf` | codebook | Estimates methodology essay | — | — |

Fill in the `Downloaded` and `SHA-256` columns after the first verified
fetch (`voyages fetch`, then `sha256sum` or `voyages verify`), and copy
the hashes into `MANIFEST` in `fetch.py`.

## Older versions (not fetched by default)

Listed on the Trans-Atlantic downloads page, same base URL: `tastdb-exp-2019.sav`,
`tastdb-exp-2016.sav`, `tastdb-2016.sav`, `tastdb-exp-2010.sav`, `tastdb-2010.sav`,
`tastdb-2010.csv`, `tastdb-exp-2008.sav`, `tastdb-1999.sav` (original CD-ROM),
`SPSS_Codebook_2022.pdf`, `SPSS_Codebook_2019.pdf`. Useful for reproducing
published analyses that cite a specific version.

## Open questions

- The 2020 `.sav` exists but no 2020 `.csv` is listed; the newest CSV is Dec 2019.
  Confirm whether the main site's "download" button produces a newer CSV export,
  and whether the 2020 `.sav` is the canonical current release.
- The People / African Names data has its own downloads page; add entries once
  the Phase 1 ingest reaches it.
- The newer API (`rice-crc/voyages-api`) may expose a bulk export that supersedes
  the legacy files. Check before Phase 2.
