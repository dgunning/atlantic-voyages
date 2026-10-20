# European migration to Jamaica before 1834: emigrant, indenture, convict and soldier sources

Scouted 2026-10-20. Rules tested: (1) bulk file from a research/archival project, no scraping/login/live API; (2) stated licence allowing research use; (3) pinnable (stable URL + checksum); (4) opt-in; (5) own tables; (6) citable. Enslaved.org/LBS excluded (already ingested).

## Bottom line

No candidate is both bulk-downloadable and substantially about Europeans going to Jamaica. The best-value source (Virtual Jamestown, Bristol registers) has no download and no licence. The two that pass the mechanical rules (Old Bailey XML, British Transportation Registers) have little or no Jamaica content.

## Ranked

| Rank | Source | Verdict | Jamaica value |
|---|---|---|---|
| 1 | Virtual Jamestown Indentured Servants (Bristol 1654-86, Middlesex 1682-85, London I 1682-92, London II 1718-59) | NEEDS PERMISSION (fails 1, 2, 3) | Highest. Origin place, occupation, age (not Bristol), destination. Jamaica count unverified. |
| 2 | Old Bailey Online XML v7.2 (1674-1913) | QUALIFIES mechanically (CC BY-NC 4.0) | Low. Sentence of transportation, destination rarely stated. Defendant names only. |
| 3 | British Transportation Registers 1787-1867 (Digital Panopticon / SLQ) | QUALIFIES mechanically (CC BY 4.0) but out of scope | Negligible. Australia (plus Gibraltar); begins 1787. |
| - | Bailyn Register of Emigrants 1773-76 | FAILS 1 (no deposited dataset found) | Would be small for Jamaica. |
| - | Galenson servant datasets | FAILS 1 (no deposit found) | n/a |
| - | Scottish Emigration Database (Aberdeen) | FAILS 1, 2 and scope (1890-1960) | None. |
| - | Cromwellian Irish / Monmouth / Jacobite / 1655 Western Design lists | FAILS 1 (no dataset exists online) | n/a |

## Details

### Virtual Jamestown, "Indentured Servants" (Registers of Servants Sent to Foreign Plantations)
- Publisher: Virtual Jamestown (Virginia Center for Digital History, UVA / Crandall Shifflett). Landing: https://www.virtualjamestown.org/indentures/about_indentures.html ; search: https://www.virtualjamestown.org/indentures/search_indentures.html
- Content: Bristol 1654-1686 (~10,000), Middlesex 1682-1685 (~1,000), London I 1682-1692 (~1,000), London II 1718-1759 (~3,000); ~15,000 total. Transcribed from Coldham (1988, Bristol), Ghirelli (1968, London I), Kaminkow & Kaminkow (1964, London II), London Metropolitan Archives microfilm (Middlesex).
- Fields: date, servant name, gender, place of origin (city/province), occupation, length of indenture, destination, ship, parents (name, occupation), spouse, agent details, notes. Age on Middlesex, London I and London II only, not Bristol. Lists of origin, occupation and destination values exist (e.g. https://www.virtualjamestown.org/indentures/bristol_destination.html; not read).
- Format: dynamic web search ("Browse Entire Database" per register). Bulk download: none found. Retrieving it would be scraping.
- Licence: only the footer "Crandall Shifflett(c) 1999, 2000". No licence or terms text. No citation guidance. Underlying Coldham book is under copyright (Genealogical Publishing Co.), so a licence from Shifflett alone may not cover it.
- Jamaica: about page names Barbados and "the Caribbean islands", not Jamaica; Jamaica count NOT VERIFIED (would need the destination list page or queries, which I did not run).
- Login: no. Verdict: NEEDS PERMISSION. Ask Shifflett / Virtual Jamestown (contact on site) for a dump and a CC licence; separately consider Genealogical Publishing for the Coldham text rights. Fails rules 1, 2 and 3 as it stands.

### Old Bailey Online XML data
- Publisher: Old Bailey Online project (Univ. of Sheffield, Hertfordshire, Open University) via Sheffield ORDA/figshare. DOI https://doi.org/10.15131/shef.data.4775434.v2 ; API record https://api.figshare.com/v2/articles/4775434 (verified).
- File: OBO_XML_7-2.zip, 315,221,598 bytes, md5 c542673f19bc0946ababfe7b64e8ea52 (published by figshare), plus OB_xml_notes.docx. Published 2017-04-06. 2,163 Proceedings files + 475 Ordinary's Accounts; ~197,750 trials, 1674-1913.
- Licence (figshare metadata): "CC BY-NC 4.0" https://creativecommons.org/licenses/by-nc/4.0/ . Redistribution allowed non-commercially with attribution. No login.
- Fields: defendant name, age and occupation sometimes, offence, verdict, punishment (including "transportation" with term), residence in text. Destination is mostly not tagged. Pre-1776 sentences of transportation went to the American colonies, but Jamaica is seldom named; this is not a Jamaica source and would need text mining. Defendants are Londoners, not a Jamaica-specific population.
- Verdict: QUALIFIES on rules 1-6 mechanically, but low value for Jamaica; would need a derived "transported" subset and honest caveats. Not recommended as a Jamaica layer.

### British Transportation Registers 1787-1867 (Digital Panopticon, from State Library of Queensland)
- Sheffield ORDA: https://doi.org/10.15131/shef.data.5711803.v1 ; API https://api.figshare.com/v2/articles/5711803 (verified). dp_btr_20171218.csv, 32,929,147 bytes, md5 1693a7831164e9ac6532c939c7edb2e6. Licence "CC BY 4.0".
- Original: SLQ "British Convict Registers" CSV on data.qld.gov.au / data.gov.au, licence cc-by-4 per CKAN (https://data.gov.au/data/api/3/action/package_show?id=british-convict-registers). CSV URL returned HTTP 202 empty to HEAD (not verified; use the figshare copy).
- Content: ~123,000 convicts to Australia, 1787-1867, England/Wales/Scotland, not Ireland. Not Jamaica. FAILS relevance (outside 1834-pre period start and destination).
- Other Digital Panopticon data (Judges' Reports, Criminal Registers Middlesex 1791-1802, etc.) are CC BY-NC on figshare per https://www.digitalpanopticon.org/Access_to_Digital_Panopticon_Data ; all London convicts 1780+, mostly Australia. Nothing found on convicts to Jamaica or Barbados.

### Register of Emigrants 1773-1776 (TNA T 47/9-12; Bailyn, Voyagers to the West)
- No ICPSR, Harvard Dataverse, UK Data Service, Zenodo or figshare deposit found. Searches of Zenodo, Dataverse and figshare APIs returned nothing relevant; ICPSR and UK Data Service pages returned 403 / were not directly searchable, so absence there is NOT fully verified.
- Bailyn's coded file of ~10,000 emigrants is mentioned in reviews; no public deposit located. Print transcriptions: Fothergill (1908-11), Coldham (1988, Genealogical Publishing). MyHeritage holds a 422-record subset (not bulk, not open).
- Original TNA registers are public domain (Crown) but are unindexed images; a project would have to transcribe. Verdict: FAILS rule 1. Bailyn's data also concern America; Jamaica was a small share.

### Galenson indentured servant data
- No ICPSR/openICPSR/Dataverse deposit found (ICPSR 403, so not fully verified). Galenson's White Servitude in Colonial America (1981) analyses >20,000 indentured immigrants but I found no public data file. The nearest online data are Virtual Jamestown's London II (Kaminkow) and Middlesex registers above. Verdict: FAILS rule 1.

### Scottish Emigration Database (Univ. of Aberdeen)
- https://www.abdn.ac.uk/emigration/what-is-sed.html : 21,090 passengers from Scottish ports, 1890-1960 (BT 27), (c) Evans and Harper 2005, no licence, search-only. Outside the pre-1834 scope. FAILS rules 1, 2 and scope.

### Cromwellian Irish, Monmouth rebels 1685, Jacobites, 1655 Western Design
- No dataset found. Named lists are in printed calendars (Calendar of State Papers Colonial, British History Online), Barbados council minutes, and the Camden Society muster roll of Venables' forces (1654). Not bulk files. FAILS rule 1.

### Jamaica-specific lists seen but not qualifying
- 1670 Jamaica census abstract (CSP Colonial vol. 7): web transcriptions on genealogy-quest.com, no licence, not bulk.
- 1754 quit-rent landholder list (TNA CO 142/31): transcription on jamaicanfamilysearch.com, terms not verified.
- Burnard, Database of Jamaican inventories 1674-1784 (~10,000): hosted via UCL LBS; download/licence not verified; falls under LBS, so overlaps Enslaved.org scope. Worth a direct query to UCL LBS.
- Seaford Town German settlers 1835: a registry exists per Gleaner; not online.
- Penn MEAD "Escaped and Captured Slave Datasets from Newspapers in Jamaica, 1718-1795": about enslaved people, already close to the Chambers runaway data in Enslaved.org.

### Repository searches run (2026-10-20)
- Zenodo API: "indentured servants", "emigrants Jamaica 1700", "Bristol servants plantations", "Old Bailey": nothing relevant (Old Bailey tools only).
- Harvard Dataverse API: "indentured servants", "emigrants Jamaica", "convicts transported": nothing relevant.
- figshare API: "indentured servants", "Jamaica emigrants": nothing relevant.
- ICPSR (403 to scripts), UK Data Service, openICPSR: web search only; no hits for Bailyn/Galenson. Not verified directly.

## Suggested next steps
1. Email Virtual Jamestown (Crandall Shifflett / UVA) asking for a bulk export and a stated licence. This is the only high-value route.
2. Ask UCL LBS about Burnard inventories export and licence.
3. Check ICPSR and UK Data Service manually in a browser for "Bailyn" and "Galenson".
4. For surnames specifically, consider Old Bailey only if a Jamaica-transport subset is wanted; otherwise skip.
