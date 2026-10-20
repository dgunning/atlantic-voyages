# Europeans in Jamaica, 1655-1950: residents, officials, census counts

Scouted 2026-10-20 against the six rules in CLAUDE.md ("Supplementary sources").
"Verified" means the page was fetched. "Not verified" means a page blocked fetching
(HTTP 401/403), returned only a shell, or was known only from search snippets.

## Bottom line

No source found qualifies. The one candidate that matters most, the Burnard
inventories (10,219 records, 1674-1784), is held only inside the LBS web interface
with no download, no licence statement, and no deposit. Best routes forward:
(1) ask UCL LBS for permission and a bulk file of the inventories; (2) use the
Wikidata CC0 route only as a small, honestly labelled enrichment (425 people),
which does not satisfy rule 1 as written.

## Verdicts

| Candidate | Verdict | Failing rule |
|---|---|---|
| Burnard, Jamaican Inventories 1674-1784 (hosted by LBS) | NEEDS PERMISSION | 1, 2, 3 (no bulk file, no licence, no checksum) |
| LBS database, full export / deposit | FAILS (as a new source) | 1: UKDS record has no files |
| Jamaica census birthplace tables 1844-1943 | FAILS | 1, 3: no open digital tables found |
| Higman, Jamaican Censuses of 1844 and 1861 | FAILS | 1, 2: sold as print |
| STATIN / IPUMS Jamaica census | FAILS (out of period) | scope: microdata only 1982, 1991, 2001 |
| JJCPF Jewish cemetery database | NEEDS PERMISSION | 1, 2: per-cemetery web viewer, no licence |
| Barnett and Wright, Jews of Jamaica Tombstone Inscriptions 1663-1880 | FAILS | 1, 2: scanned book, rights not verified |
| Wright, Monumental Inscriptions of Jamaica (1966) | FAILS | 1, 2: FamilySearch login, no dataset |
| jamaicanfamilysearch.com almanacs, wills | FAILS | 1, 2: website, pay-per-view per one guide, no terms found |
| History of Parliament | NEEDS PERMISSION / not verified | 2: site blocked (HTTP 401) |
| Royal Navy / army officer lists | FAILS | no open bulk dataset found |
| Wikidata extract | FAILS rule 1 as written; usable only if the rule is relaxed | 1 |
| Zenodo / Harvard Dataverse sweep | nothing relevant | none |

## Details

### 1. Burnard, "Jamaican Inventories" (NEEDS PERMISSION)
- Publisher: Legacies of British Slavery (LBS), UCL Department of History. Gift of the
  late Prof. Trevor Burnard. Landing: https://lbs.ucl.ac.uk/lbs/project/invdesc (verified);
  listing https://lbs.ucl.ac.uk/lbs/inventories/ (verified, 10,219 inventories).
- Source: Jamaica Archives, Spanish Town, IB/11/3/1-65. Range 1674-1784, almost 60%
  from 1740-1779. Some volumes missing (1690s-1700s) and one unreadable.
- Fields (per search summary of the "fields of information" page; that page itself was
  not fetched): name, occupation, parish, total estate value, number and value of
  enslaved people, cash, plate, debts. Bracketed LBS person ID where the person is
  matched to the main LBS database. No birthplace or origin: inventories are probate
  records of people who died in Jamaica. Value is for finding a surname's earliest
  Jamaican presence, occupation and parish, not origin.
- Licence: none stated. Only "(c) Copyright Legacies of British Slavery - UCL
  Department of History 2026". No download, no citation format on the pages fetched.
  Guidance pages https://www.ucl.ac.uk/lbs/project/invsource returned 403 (not verified).
- Burnard's book (Planters, Merchants, and Slaves, Chicago 2015) is the citation to use.
- No deposit found in UKDS, Zenodo, Dataverse, figshare or UCL RDR (RDR search returned
  403, not verified). Searched via web search and the Zenodo and Dataverse APIs.
- Burnard's other datasets (white population, Thistlewood, Kingston): nothing deposited
  found. The Thistlewood papers are digitised images at Yale Beinecke (OSB MSS 176),
  not a dataset. A Sussex figshare record for a Burnard chapter is "not publicly available".
- Route: write to LBS (Keith McClelland, k.mcclelland@ucl.ac.uk is the UKDS contact
  for the LBS study) asking for a licensed bulk export of the inventories.

### 2. LBS bulk export / deposit (FAILS as new source)
- UK Data Service ReShare study 852209, Hall (2017), DOI 10.5255/UKDA-SN-852209, covers
  ~40,000 claims, ~47,000 individuals, ~3,000 biographies, ~8,000 estates, 1740-1839.
  Verified at https://reshare.ukdataservice.ac.uk/852209/: "No Files to display"; data
  "held in an external repository" which points to the LBS website. No licence named.
- JSDP data article (verified): https://jsdp.enslaved.org/fullDataArticle/volume1-issue2-legacies-of-british-slave-ownership ,
  DOI 10.12921/07em-3t32. Article is CC BY-NC-SA 4.0; "the page does not state the
  licence for the dataset itself". Says data can be viewed on Enslaved.org and
  downloaded from UKDS, but the UKDS record has no files.
- No Zenodo or UCL RDR deposit found (Zenodo "Legacies of British Slavery" search: one
  unrelated Australian conference paper). So Enslaved.org remains the only bulk route,
  which is already ingested.
- Note for the existing ingest: the Enslaved.org dump states CC BY 4.0 per source, but
  the UKDS and JSDP pages state no dataset licence. Worth confirming that the LBS
  contributed source's CC BY 4.0 is as recorded (from DATA.md; not re-checked here).

### 3. Census tables with birthplace (FAILS)
- Censuses: 1844, 1861, 1871, 1881, 1891, 1911, 1921, 1943 (IPUMS country report,
  https://users.pop.umn.edu/~rmccaa/ipums-global/jamaica_ipums_durban_workshop.pdf;
  PDF text not extractable by the fetcher, so claims come from search snippets).
- IPUMS International has Jamaica microdata only for 1982, 1991, 2001 (search snippets;
  IPUMS site not checked; registration required).
- STATIN (https://statinja.gov.jm) publishes 2011 census tables online, including
  "Local and Foreign Born" and parish-of-birth tables (verified for 2011 only, no
  licence on page, no download button). Not in the 1655-1950 window.
- Higman (ed.), The Jamaican Censuses of 1844 and 1861 (UWI Social History Project)
  https://www.mona.uwi.edu/history/shp/census.htm (verified): print, J$100 / US$5, no
  digital edition mentioned, no mention of birthplace tables.
- dLOC / UFDC and HathiTrust: searches found no digitised Jamaican census volumes.
  dloc.com result page returned only a shell; HathiTrust returned 403 (not verified).
  Archive.org advanced search returned nothing relevant.
- Indicative totals (unverified, Wikipedia/Gleaner via search): white population
  13,101 in 1871, about 12,737 in 1787. Race categories, not birthplace.
- Route: the volumes are probably in print/microform only. A manual transcription of
  birthplace tables from 1871-1921 reports would be a new derived dataset, not a
  bulk-file source.

### 4. Jewish community records
- JJCPF database (https://www.jjcpf.org/cemify, verified): five cemeteries listed
  (Falmouth, Hunts Bay, Lacovia, Rowe's Corner, Lucea) with photos, transcriptions and
  translations; "still digitizing". 33 burial sites recorded 2008-2017 (search
  snippet). No download, no licence, no terms on pages fetched. Contact
  contact@jjcpf.org. NEEDS PERMISSION.
- Barnett and Wright, The Jews of Jamaica: Tombstone Inscriptions 1663-1880 (Ben Zvi
  Institute 1997, 1,456 inscriptions per a review snippet). A UFDC copy is reported at
  ufdc.ufl.edu/AA00001365/00001; page returned only a shell, rights not verified.
  Scanned book, not tabular. Origin value: Sephardic epitaphs sometimes name
  Iberian or Dutch places. Not a bulk dataset.

### 5. Officials, officers
- History of Parliament Online: pages returned 401 (not verified). Biographies of MPs
  only, a tiny slice of Jamaican residents; no bulk download or licence found.
- National Archives ADM 1 / ADM 128 lists (Jamaica station officers) are catalogue
  descriptions; no bulk open dataset found. threedecks.org licence not checked.
- No "Colonial Office officials" or Assembly-member dataset with a bulk file found.

### 6. Wikidata (assessed honestly)
- Licence: CC0 for structured data (verified,
  https://www.wikidata.org/wiki/Wikidata:Licensing; the page does not name dumps
  explicitly). Dumps are public bulk files, but Wikidata is a crowd-edited
  knowledge base, not a research or archival project's deposit, so rule 1 is not met
  on its face. It also fails the spirit of rule 1 on provenance: values are
  unattributed per record unless references are kept.
- Counts, SPARQL run 2026-10-20 (query.wikidata.org, scouting only):
  425 humans with place of death in Jamaica or any place within it (P20, P131*);
  54 of those born in the UK, Ireland or a constituent country. Place of death
  Jamaica itself: 104 humans, 57 with a birthplace, 15 born in the UK.
  Too small, and biased to notables, to trace family origins; useful only for
  governors, officers, clergy.
- If the owner wants it: treat as a documented exception to rule 1 (pinned extract,
  CC0, opt-in, own `wikidata_*` tables). Needs an explicit decision to amend the rules.

### 7. Repository sweep
- Zenodo (API queries: Jamaica planters, inventories, census, Jewish, wills,
  Legacies of British Slavery, free people of colour): nothing usable. Hits that look
  relevant are not datasets: Mullen, The Glasgow Sugar Aristocracy (book PDF,
  CC BY-NC-ND 4.0, https://zenodo.org/records/19849572); Baptists in Jamaica 1780-1832
  (article, CC BY 4.0, https://zenodo.org/records/13158480).
- Harvard Dataverse: one broad query, nothing relevant. ICPSR, UKDS catalogue
  search, figshare, Mendeley Data, dLOC: not searched directly (only via web search);
  not verified.
- Oxford ORA: Jamaican customs data c. 1800-45 (goods, not people):
  https://ora.ox.ac.uk/objects/uuid:8c1597fe-f502-4e46-a19a-4c8befaae186 (not fetched).
- British Library EAP148 digitised Jamaica Archives manumission volumes 5-12
  (1747-1778): page headings show a licence section but content not retrieved. Images
  of manumissions of enslaved people, not a dataset of Europeans. Not verified.
- Dobson, The People of Jamaica 1655-1855 (>2,000 Euro-Jamaicans) and Mitchell's index
  of Jamaican wills 1644-1816: printed/web resources, hosting and licence unknown.

## Ranking by value for tracing origins (none qualifies today)
1. Burnard inventories via UCL permission: best coverage of the planter and merchant
   class 1674-1784 (10,219 people, with LBS ID links), but no origin field.
2. Wikidata extract: only source with explicit birthplace; tiny and notable-biased.
3. JJCPF cemetery data via permission: Sephardic origin clues, small.
4. Census birthplace tables: highest value for European-born counts 1871-1921 but
   would need manual transcription from print.
