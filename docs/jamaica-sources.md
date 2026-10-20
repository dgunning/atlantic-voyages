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
| Enslaved.org (MATRIX, Michigan State) | 1.22 million records; includes the Chambers runaway notices (downloaded) | Yes, for 459 of 782 runaways | Free text only; no parish links | Bulk JSON dump, 464 MB (downloaded) | Per source; CC BY 4.0 for the runaway notices (downloaded) | Usable now |
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

**Enslaved.org** (<https://enslaved.org/>, <https://docs.enslaved.org/lod/>). Downloaded
and read on 20 October 2026: the Wikibase JSON dump
(`https://manta.matrix.msu.edu/msumatrix/public/exports/wikibase/2bde7b5b/latest.wikibase.dump.json.gz`,
464,379,438 bytes, last modified 31 March 2026, SHA-256
`0eaf2c8dd6b000d4f10ab6fb90d8deaee9aab68f063af517dad8ba7fdd286c09`). It is now in the
library as a supplementary source: `voyages fetch -d enslaved`, then `voyages build`
for the `enslaved_*` tables (see `docs/DATA.md`). What it holds for Jamaica:

- 1,223,416 records: people, events, places and sources. Each source record carries its
  licence (`hasLicenseInfo`) and the project that contributed it (`generatedBy`).
- **The Chambers runaway notices are in it**, as the project "Fugitives from Slavery in
  Jamaica", licensed CC BY 4.0: 782 people from the *Weekly Jamaica Courant* (Kingston,
  1718–1754, 76 people), the *Jamaica Mercury* (Kingston, 1779–1780, 142), the *Royal
  Gazette* (Kingston, 1791–1792, 112) and the *Cornwall Chronicle* (Montego Bay, 1775–1795,
  452).
- **Ethnonyms** are in two fields: a standardised one (`ethnonym`: Igbo, Congo, Mandingo,
  Creole and others) and the term as written where there is no standard one
  (`ethnonym_as_written`: Coromantee, Canga, Moco, Chamba, Popo, Mungola and others).
  Together they give a term for 459 of the 782 people. Enslaved.org also gives the place
  of origin each standard ethnonym refers to (`ethnonym_place_of_origin`, e.g. Bight of
  Biafra for Igbo).
- **No parish links.** All 21 pre-1867 parishes are in the dump as places, but no Jamaican
  event is attached to one: events sit at "Jamaica" as a whole. Parishes appear only in free
  text, for a few dozen people.
- Most of the other Jamaican events are about 9,800 legal proceedings from the 1830s
  (Parliamentary Papers) and voyages from SlaveVoyages, which the library already has.

The newspaper is a rough guide to place: the *Cornwall Chronicle* was the Montego Bay paper.
Of the African-born runaways whose term can be matched to a region (an approximate mapping:
Igbo, Eboe and Moco to the Bight of Biafra; Coromantee and Fante to the Gold Coast; Popo,
Nago and Yoruba to the Bight of Benin; Congo, Angola and Mungola to West Central Africa;
Mandingo, Soso, Fula and Canga to Upper Guinea), the Bight of Biafra accounts for 37% in the
Montego Bay paper (215 people, 1775–1795) and 18% in the Kingston papers (72 people,
1779–1792). That is the same direction as the landings in notebook 06 (68% and 35%), on far
smaller and more biased numbers: people who escaped, described by the people who claimed
them.

## Gaps

- **Historic parish boundaries.** Jamaica had about 21 parishes before they were merged into
  14 in 1867. No downloadable map of them was found. One would have to be made, for example by
  georeferencing James Robertson's 1804 map, and curated with a source on every row, as
  `tools/place_coordinates.py` does for ports.
- **No join key.** None of these sources carries SlaveVoyages voyage IDs. Links would be by
  period, port, and sometimes ship name, never person by person.

## Next steps

1. A notebook comparing the runaway notices' ethnonyms by newspaper with the landings in
   notebook 06, using the `enslaved_*` tables.
2. Ask UCL (LBS, registers) and the Penn and Florida libraries (runaway notices) about terms
   for research use and redistribution.
3. If any of these are added, record them in `docs/DATA.md` with file, URL, date and
   checksum, as for the SlaveVoyages downloads, and keep their licences separate.
