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

`v.fields(search="captives")` lists the fields, and `v.describe("MAJBUYPT")` shows one with
its provenance, codebook reference and values. `v.query(recorded_only=True)` (or
`--recorded-only`) keeps to data transcribed from historical records, which is public
domain: no imputed field is read.

The same filters work from the command line. Output is CSV on stdout, or a CSV or
Parquet file with `-o`; the citation and licence note go to stderr, and Parquet files
carry them in their metadata:

```bash
voyages query -d transatlantic -e "Bight of Biafra" -l Jamaica --from 1700 --to 1800 --by decade
voyages query -l Jamaica --by endpoints --drawable-only -o jamaica.parquet
```

## Supplementary sources

Data from other projects can be added alongside, opt-in and in tables of its own; nothing
is merged into the SlaveVoyages tables. The first is
[Enslaved.org](https://enslaved.org): 731,500 person records from about 40 contributed
datasets, with names, roles, ethnonyms, places and the sources each record cites.

```bash
voyages fetch -d enslaved   # 464 MB dump, checksummed
voyages build               # adds the enslaved_* tables
```

```python
import voyages
from voyages import Voyages

v = Voyages()
runaways = v.sql("""
    SELECT p.person_name, p.ethnonym, p.ethnonym_as_written, s.source_title AS newspaper
    FROM enslaved_people p
    JOIN enslaved_record_sources rs ON rs.record_id = p.person_id
    JOIN enslaved_sources s USING (source_id)
    JOIN enslaved_projects USING (project_id)
    JOIN enslaved_roles r ON r.person_id = p.person_id
    WHERE project_code = 'FSJ'   -- Fugitives from Slavery in Jamaica
      AND r.participant_role = 'Runaway'
      AND s.source_title NOT LIKE 'Chambers%'
""").to_pandas()
print(voyages.citation("enslaved"))
```

Every source record carries its licence (`enslaved_sources.licence`) and its contributing
dataset (`enslaved_projects`, with the dataset's DOI); credit both. See `docs/DATA.md`.

## Worked analyses

Notebooks in `notebooks/`, each a `.py` source paired with an executed `.ipynb`
(`uv run jupytext --sync notebooks/*.py`, then `uv run jupyter nbconvert --to notebook
--execute --inplace notebooks/<name>.ipynb`; needs the full data).

- [Arrivals in Jamaica by African region of embarkation](notebooks/01_jamaica_arrivals.ipynb):
  recorded, imputed and Estimates figures side by side, decade by decade.

![People disembarked in Jamaica by decade](notebooks/figures/01_jamaica_by_decade.png)

- [Calabar to Jamaica](notebooks/02_calabar_to_jamaica.ipynb): the voyages from Old Calabar,
  where their captives were landed, and how many died on the way, with maps.

![Routes from Calabar](notebooks/figures/02_calabar_routes.png)

- [Re-exports from Jamaica](notebooks/03_jamaica_reexports.ipynb): captives shipped on from
  Jamaica to other colonies, from the Intra-American data: destinations, timing, a comparison
  with arrivals from Africa, and the journeys that can be traced from the African coast.

![Routes from Jamaica](notebooks/figures/03_reexport_routes.png)

- [Bight of Biafra, Gold Coast, Bight of Benin](notebooks/04_three_regions_destinations.ipynb):
  where people embarked on three neighbouring coasts were landed, quarter-century by
  quarter-century, and Jamaica's share of each.

![Destinations by quarter-century](notebooks/figures/04_destinations_by_period.png)

- [Deaths on the middle passage](notebooks/05_mortality_and_duration.ipynb): the share of people
  who died at sea and the length of the crossing, by period, African region and route, on the
  voyages whose deaths can be measured; and the same for voyages to Jamaica.

![Crossing length and deaths by route](notebooks/figures/05_routes.png)

- [Landing ports in Jamaica](notebooks/06_jamaica_landing_ports.ipynb): Kingston and Montego Bay
  compared over the same years, 1763–1808. About two-thirds of the people landed at Montego Bay
  came from the Bight of Biafra, against about a third at Kingston.

![African regions by Jamaican landing port](notebooks/figures/06_port_origins.png)

- [Runaway notices and landings](notebooks/07_jamaica_runaways.ipynb): the African origins of
  782 people whose escapes were advertised in Montego Bay and Kingston newspapers (Enslaved.org,
  *Fugitives from Slavery in Jamaica*), set against the landings at each port. The Bight of
  Biafra is 37% of African-born runaways in the Montego Bay paper and 17% in the Kingston papers.

![Runaways and landings by port](notebooks/figures/07_runaways_vs_landings.png)

- [The trade in one decade, the 1790s](notebooks/08_flows_1790s.ipynb): flows from African
  regions to the Americas, with a close-up of the Caribbean. Jamaica was the largest single
  destination of the decade (150,536 people).

![Flows, 1790s](notebooks/figures/08_flows_1790s.png)

## Data and license

The library code is Apache-2.0. The data belongs to SlaveVoyages: records
transcribed from historical documents are public domain; imputed fields and the
Estimates database are CC BY-NC 4.0. See `NOTICE` and `docs/DATA.md`.

```python
>>> import voyages
>>> print(voyages.citation())
SlaveVoyages, Trans-Atlantic Slave Trade Database, https://www.slavevoyages.org (accessed ...).
```
