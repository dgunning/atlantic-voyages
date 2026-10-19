# voyages

A Python library for the [SlaveVoyages](https://www.slavevoyages.org) databases:
the Trans-Atlantic Slave Trade Database, the Intra-American Slave Trade Database,
the Estimates database, and the People of the Atlantic Slave Trade records.

The aim is a clean, typed, provenance-aware data layer with a small query API, so
that a developer or historian can go from the official downloads to a question
answered in a few lines of Python, reproducibly.

**Status: Phase 0 (bootstrap). Nothing here is usable for analysis yet.** See
`PLAN.md` for the roadmap.

## Install (development)

```bash
uv sync
uv run voyages version
uv run voyages fetch        # downloads the official files to ~/.cache/voyages/raw
uv run pytest
```

Set `VOYAGES_DATA_DIR` to put the raw and built data somewhere else.

## Where this is going

```python
from voyages import Voyages

v = Voyages()
df = (v.transatlantic
       .disembarked_in("Jamaica")
       .embarked_from("Bight of Biafra")
       .between(1700, 1800)
       .by_decade(["embarked", "disembarked"]))
```

## Data and license

The library code is Apache-2.0. The data belongs to SlaveVoyages: records
transcribed from historical documents are public domain; imputed fields and the
Estimates database are CC BY-NC 4.0. See `NOTICE` and `docs/DATA.md`.

```python
>>> import voyages
>>> print(voyages.citation())
SlaveVoyages, Trans-Atlantic Slave Trade Database, https://www.slavevoyages.org (accessed ...).
```
