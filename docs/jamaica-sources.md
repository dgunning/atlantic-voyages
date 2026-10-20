# Sources beyond SlaveVoyages: where in Jamaica people lived

SlaveVoyages records the port where captives were landed, not where they lived. Notebook 06
shows that Montego Bay drew far more on the Bight of Biafra than Kingston did in 1763–1808,
but the landing port is not the parish. This page reviews other sources that might link
African origin to parish or estate, and whether code could use them.

Checked 19 October 2026. Several sites blocked automated requests, so much of the detail on
access and licences is unconfirmed. Each claim is marked:

- **seen**: on the source's own page;
- **reported**: from search results or secondary accounts, not checked.

No source found gives African region by Jamaican parish directly. The likely route is
indirect: records naming an ethnonym or African birth, matched by parish and period to
SlaveVoyages regional shares.

## Summary

| Source | Coverage | African origin | Parish or estate | Access | Licence | Verdict |
|---|---|---|---|---|---|---|
| Runaway notices in Jamaican newspapers (Douglas Chambers) | 1718–1795, plus workhouse lists 1790–1795 (reported) | Often, as an ethnonym (reported) | Often (reported) | Penn and University of Florida repositories; format not confirmed | Not known | Usable with effort; check licence first |
| UCL Legacies of British Slavery (LBS) | About 8,000 estates (reported); counts of enslaved people from registers and almanacs, 1809–1839 (seen) | No | Yes (seen) | Website only; no export or API seen | © UCL, no reuse licence (seen) | Needs permission |
| Slave registers, 1817–1832 (TNA T 71) | Every enslaved person by estate, every three years (reported) | African or Creole often noted (reported) | Yes (reported) | Searchable on Ancestry; no bulk download | Ancestry terms | Not usable now; watch for an open UCL release |
| Enslaved.org (MATRIX, Michigan State) | 731,500 people, 10,381 places (seen) | Varies by dataset | Not known | Bulk JSON and RDF dump (seen; file live) | None on the page (seen) | Usable with effort; check per-dataset terms |
| LBS Jamaican inventories (Trevor Burnard) | Over 10,000 probate inventories, 1674–1784 (seen) | No | Yes (reported) | Browsable on LBS; download not stated (seen) | Not stated | Needs permission |
| Jamaica Almanac transcriptions (jamaicanfamilysearch.com) | Estate returns, 1810s–1840 (reported) | No | Yes | HTML pages only | Not known | Prefer LBS, which includes them |
| Freedom on the Move | North American runaway notices (reported) | — | — | Download advertised (seen) | Not stated | Not usable: no Jamaica |
| liberatedafricans.org | Over 700,000 people, 1800–1920 (seen) | Some | Not for Jamaica (reported) | No download seen | Not read | Not usable for parishes |
| Digital Library of the Caribbean, *Royal Gazette* (Kingston) | Newspapers from 1780 (reported) | In notices | In notices | Scanned text; metadata only | Not known | A text-mining project, not a dataset |

## Notes on the most useful

**Runaway notices.** These are the only records found that tie an African ethnonym ("Eboe",
"Coromantee", "Congo", "Chamba") to a place in Jamaica, through the owner's or the
workhouse's parish. They are a small, biased sample: people who escaped, mostly men, named in
the owner's terms. The transcriptions are said to be at the University of Florida Digital
Collections (<https://ufdc.ufl.edu/AA00021144/00001>), and coded datasets at the University
of Pennsylvania (<https://repository.upenn.edu/mead/41>, <https://repository.upenn.edu/mead/44>).
Both blocked the review, so files, fields and terms are unconfirmed.

**Legacies of British Slavery** (<https://www.ucl.ac.uk/lbs/>). The best record of which
parishes and estates held how many enslaved people, 1809–1839. An example estate page
(<https://lbs.ucl.ac.uk/lbs/estate/view/18817>) shows parish and a series of counts. It has no
African origins, so it would serve as the denominator: SlaveVoyages shares by period, weighted
by each parish's numbers. The site is copyright UCL with no reuse licence, so the library
should not download it at run time or redistribute it without written permission from the
Centre for the Study of the Legacies of British Slavery.

**Slave registers.** The registers list people estate by estate, often marking each as
African or Creole (born in Jamaica). An index of African-born people by parish and estate,
1817–1832, would be the closest available measure of where Africans lived. Today the
registers are searchable only on Ancestry, whose terms rule out bulk use. A UCL open-access
database ("Valuable Lives") has been reported; its status was not confirmed.

**Enslaved.org** (<https://enslaved.org/>, <https://docs.enslaved.org/lod/>). The only
source with a confirmed bulk download, a Wikibase dump in JSON and RDF. It brings together
many contributed datasets, each with its own terms, published through the *Journal of Slavery
and Data Preservation*. How much Jamaican, parish-level material it holds is not known.

## Gaps

- **Historic parish boundaries.** Jamaica had about 21 parishes before they were merged into
  14 in 1867. No downloadable map of them was found. One would have to be made, for example by
  georeferencing James Robertson's 1804 map, and curated with a source on every row, as
  `tools/place_coordinates.py` does for ports.
- **No join key.** None of these sources carries SlaveVoyages voyage IDs. Links would be by
  period, port, and sometimes ship name, never person by person.

## Next steps

1. Download the Enslaved.org dump and count records with Jamaican places and their source
   datasets.
2. Ask UCL (LBS, registers) and the Penn and Florida libraries (runaway notices) about terms
   for research use and redistribution.
3. If any of these are added, record them in `docs/DATA.md` with file, URL, date and
   checksum, as for the SlaveVoyages downloads, and keep their licences separate.
