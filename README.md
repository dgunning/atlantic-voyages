# voyages

A Python library for the [SlaveVoyages](https://www.slavevoyages.org) databases:
the Trans-Atlantic Slave Trade Database, the Intra-American Slave Trade Database,
the Estimates database, and the People of the Atlantic Slave Trade records.

The aim is a clean, typed, provenance-aware data layer with a small query API, so
that a developer or historian can go from the official downloads to a question
answered in a few lines of Python, reproducibly.

**Status: Phase 2 (query layer). Usable for exploration; the API may still change.** See
`PLAN.md` for the roadmap.

## Install (development)

```bash
uv sync
uv run voyages version
uv run voyages fetch        # downloads the official files to ~/.cache/voyages/raw
uv run voyages build        # builds the Parquet tables
uv run pytest
```

Set `VOYAGES_DATA_DIR` to put the raw and built data somewhere else.

## Query

After `uv run voyages build`:

```python
import voyages
from voyages import Voyages

v = Voyages()
df = (v.transatlantic
       .disembarked_in("Jamaica")
       .embarked_from("Bight of Biafra")
       .between(1700, 1800)
       .by_decade(["voyages", "embarked", "disembarked"]))
print(voyages.citation())
```

Places are names or codes at any level (port, region, broad region) and match the
voyage's principal places of embarkation and disembarkation, imputed where the
record is silent, as on the site. Totals are the imputed totals; `df.attrs["provenance"]`
says so. `v.transatlantic.disembarked_in("Jamaica").endpoints()` gives the points to
draw each voyage on a map, and `v.sql("...")` runs any SQL over the tables.

## Data and license

The library code is Apache-2.0. The data belongs to SlaveVoyages: records
transcribed from historical documents are public domain; imputed fields and the
Estimates database are CC BY-NC 4.0. See `NOTICE` and `docs/DATA.md`.

```python
>>> import voyages
>>> print(voyages.citation())
SlaveVoyages, Trans-Atlantic Slave Trade Database, https://www.slavevoyages.org (accessed ...).
```
