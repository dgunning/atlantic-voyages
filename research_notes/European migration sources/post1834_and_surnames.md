# Post-1834 European migration to Jamaica, and surname-origin reference data

Scouted 2026-10-20. Judged against the six rules in CLAUDE.md "Supplementary sources"
(1 bulk file, no login/scraping/live API; 2 stated licence allowing research use;
3 pinnable; 4 opt-in; 5 own tables; 6 citable).
"Not verified" = page blocked (Cloudflare 403) or text not retrievable.

## Headline

Nothing found fully qualifies today. Two things come close:

1. **Matheson, Special Report on Surnames in Ireland (1894)**, scan on Internet Archive.
   Public-domain text (Crown copyright 1894; expired). Gives, per surname with 5+ births in 1890,
   birth counts by province and the counties where principally found. Fails rule 1 as a
   *structured* bulk file: it is a page scan with OCR text in broken columns; the table
   would have to be rebuilt (OCR/transcription) by this project. Rule 2 muddied: the IA item
   carries a CC BY-NC-ND 3.0 tag on the digitisation (University of Southampton scan), which
   conflicts with using the OCR; the underlying 1894 text is public domain.
2. **UK Data Service SN 4177 / 4178 (1881 census, England+Wales / Scotland, ~26 M people)**
   is the right data but fails rules 1 and 2 (registration + HE/FE-only EUL). A *derived
   aggregate* (surname x county counts) might be publishable with permission; see below.

No open bulk dataset of post-1834 European immigrants to Jamaica exists that I could find.
The Bremen emigrant dataset on Zenodo (CC BY 4.0) was checked and does NOT contain the
1835 Jamaica sailings (see section A3).

## A. Post-emancipation immigration

### A1. Germans 1834-1838 (Seaford Town, Lassen scheme)
- Verdict: **FAILS rule 1** (no dataset found).
- Only secondary sources: Gleaner (https://old.jamaica-gleaner.com/pages/history/story0060.htm),
  Jamaica Observer (https://jamaicaobserver.com/2008/12/31/seaford-town-178-years-on),
  cockpitcountry (https://cockpitcountry.com/germanSettlers.html). They cite a "registry of the
  1835 immigrants" (ages 20-65, families up to nine) but not where held or whether transcribed.
  Headcounts conflict: 249 / ~250 / ~300 at Seaford Town; 532 total in the 1835 wave (Gleaner);
  64 Germans in May 1834. Not verified against archive.
- Lead: Jamaica Archives (Spanish Town) immigration registers; TNA CO 137 (Jamaica) and CO 318
  (West Indies) hold dispatches/returns. Nothing digitised as tables found.

### A2. Scots and Irish bounty immigrants 1834-1842; Portuguese from Madeira 1840s
- Verdict: **FAILS rule 1** (no dataset found).
- Bounty system ran to 1842 (Gleaner, above). Irish wave 1835-42 is the subject of Marianne
  Keating's art/archive project (https://www.newcontemporaries.org.uk/news/blog-post-marianne-keating);
  no data release seen. Madeira: Jo-Anne Ferreira's UWI study covers the Anglophone Caribbean
  1835-1975 but is Trinidad/Guyana/St Vincent/Antigua-weighted
  (https://uwispace.sta.uwi.edu/bitstreams/841e8b3e-3375-4996-b9bf-18a9db56bc6e/download, text
  not read in full). Madeira Regional Archive holds passport applications 1872-1920 and baptisms
  1860-1911 (https://www.ttportuguese.com/the-regional-archives-of-madeira), no bulk file.
- Monica Schuler's work on African immigration to Jamaica 1841-65 exists; no database found.

### A3. Bremen passenger-list dataset (checked because the 1835 Germans sailed from Bremen)
- Name: "A Dataset of 735,000 Migration Records (Bremen, 1830-1939)" (CHUP_Passengerlists.csv).
  Publisher: University of Passau (Perschl, Schmidt, Gassner, Rehbein), from MAUS / Bremen
  Chamber of Commerce transcriptions.
- URL: https://zenodo.org/records/17977460 ; DOI 10.5281/zenodo.17977460 ; published 2025-12-18.
- Licence: CC BY 4.0 (Zenodo metadata). No login. Stable DOI. 272,193,270 bytes, MD5 41f6368b..., 
  SHA-256 0f156daa8bd35c28ced6bcc575a20889fe33832968fc24d77169021982f865d2 (I downloaded to
  scratchpad only, not the repo). 735,545 rows x 62 columns, delimiter "@".
- I scanned it: 1835 has only 93 rows, 1834 has 188; no Jamaica/Kingston/Rio Bueno arrivals
  (the 710 "Jamaica" hits are Jamaica, Queens, NY, 1920s). Departures 1830-42 are ~2,000 rows.
  The record is mostly 1920s US-bound. **Not useful for Jamaica.** Verdict: qualifies
  technically (rules 1-6 plausible) but **zero value** for this question. Do not add.

### A4. UK outward passenger lists BT 27 (1890-1960)
- Verdict: **FAILS rule 1/2** for BT 27 itself. TNA catalogue
  (https://discovery.nationalarchives.gov.uk/details/r/C3070): images only via Findmypast
  and Ancestry (paid). No OGL derivative dataset found. Also post-1890 is late for the
  surname-origin question.
- **Scottish Emigration Database** (Univ. of Aberdeen, Evans and Harper; 21,090 passengers,
  1890-1960 from BT 27, Scottish ports): https://www.abdn.ac.uk/emigration/what-is-sed.html .
  Notice "(c) Nicholas J. Evans and Marjory Harper 2005"; no reuse terms stated; search
  interface only, no bulk download stated; no Jamaica mention. **NEEDS PERMISSION** and is low value.
  1923 subset is on UKDS/AHDS (b2find: https://b2find.eudat.eu/dataset/4b998be6-906b-5d79-b1ad-949f4787dea7),
  licence tier not verified.

### A5. Immigrant Ships Transcribers Guild (ISTG)
- Fails rule 1: transcriptions of ships to N. America/Australia, not Jamaica; website terms
  not found (search returned only MyHeritage's copy). Licence **not verified**. FAILS.

### A6. Caribbean indenture datasets (context)
- ICPSR/openICPSR project 108761, aggregate Indian indentured servants incl. Jamaica from ca. 1905
  (https://www.openicpsr.org/openicpsr/project/108761/version/V1/view). Not European and
  not 1834-42; ICPSR login likely. Not pursued.
- Colonial Blue Books / immigration returns: no digitised-table releases found. Not verified.

## B. Surname distribution

### B1. UK Data Service SN 4177 (England, Wales, Channel Is., Isle of Man) and SN 4178 (Scotland)
- "1881 Census for England, Wales, the Channel Islands and the Isle of Man (Enhanced Version)";
  Woollard (Essex) and Schurer. https://b2find.eudat.eu/dataset/36ce679e-3837-555e-94d3-affede679c8e
- ~26 M individuals, full universe; fields: PRO ref, piece, folio, page, county, parish, address,
  surname, first name, relationship, marital status, sex, age, occupation, birthplace, disabilities.
- Rights (as retrieved): "Crown copyright, held jointly with the Genealogical Society of Utah and
  the University of Essex"; UKDS End User Licence; **registered UKDS users only, limited to HE/FE
  for not-for-profit education and research** (the metadata flag OpenAccess: true contradicts this).
  Commercial use needs owner approval. Note: the DOI shown on the record page
  (10.1080/24694452.2020.1717328) looks like an article DOI, not the data DOI. Scotland SN 4178:
  tier not verified.
- 5% parish sample (UKDS, 716 parishes, includes surname): same rights, same login
  (https://b2find.eudat.eu/dataset/6d38e134-b8c2-5fbb-a627-c91dec35147a). A 5% sample is too
  thin for rare surnames like Gunning anyway.
- Verdict: **FAILS rules 1 and 2** (login; HE/FE restriction). Aggregate redistribution: the EUL
  generally allows publishing derived statistics but not the microdata; the Crown/GSU copyright
  and the HE/FE-only condition mean a published surname x county table would need written
  permission from UKDS/depositors. Not verified against the EUL text. Treat as NEEDS PERMISSION.

### B2. I-CeM Names and Addresses 1851-1911 (Special Licence)
- Over 180 M records (page also says "some 210 million"); copyright K. Schurer, E.J. Higgs,
  BrightSolid. Special Licence, registered users, no commercial use, publications must be sent to
  the nominees 30 working days before publication.
  https://b2find.eudat.eu/dataset/331ae75d-8c66-5f3f-9ea2-94af6fb81978
- Verdict: **FAILS rules 1, 2**; **NEEDS PERMISSION** is the only route; the 30-day pre-publication
  review makes an open library impractical.

### B3. IPUMS International / NAPP 1881 Great Britain
- IPUMS forum (https://forum.ipums.org/t/historical-uk-census-with-names/5733): "Names are not
  available in the current versions of the 1881 complete count UK data." NAPP formerly had
  named GB 1881; ask ipums@umn.edu for restricted access. IPUMS licence terms not fetched
  (from memory: registration, no redistribution of microdata; not verified).
- Verdict: **FAILS rule 1** (login) and the current release has no surnames at all.

### B4. britishsurnames.uk and namecensus.co.uk (1881 census surname pages)
- Surname rankings by county/registration district with counts and "index" (namecensus Cheshire:
  13,220 surnames, 591,819 people). Search-result snippet says britishsurnames.uk describes its
  1881 data as "Crown Copyright used under the Open Government Licence"; **not verified**: site
  returned a Cloudflare 403 to both WebFetch and curl. Neither offers a bulk download; namecensus
  states no operator, no licence or reuse terms (its methodology/terms pages not retrieved).
- Verdict: **FAILS rule 1** (web pages only; getting data means scraping). The OGL claim, if
  true, concerns the census source, not the site's compilation. Useful only as a spot-check
  oracle for our own numbers, not as a source.

### B5. UCL Public Profiler "GB Names" / Surname Profiler (Longley, Webber, Cheshire)
- https://www.publicprofiler.org/ ; 1881 census and 1998 electoral register; ~25,630 names with
  100+ entries. Footer "Copyright (c) 2010 Public Profiler - All rights reserved." Search
  interface only; no download; terms page not retrieved.
- Related open items: van Dijk and Longley, "Platial Geo-Temporal Demographics Using Family
  Names" (Zenodo 3628863, CC BY 4.0, https://zenodo.org/records/3628863): contains only the
  article PDF (1.4 MB), **no data**. Origins of 59,218 surnames are described in the paper;
  Discovery pages (discovery.ucl.ac.uk/id/eprint/18818, 10091750) returned 403, not verified
  whether a data deposit exists there.
- Verdict: **FAILS rule 1/2** ("all rights reserved", no bulk file). NEEDS PERMISSION: ask Longley
  / UCL CASA whether a surname -> 1881 county or "likely origin" table can be released.

### B6. Free UK Genealogy: FreeCEN (1881 included)
- https://www.freecen.org.uk/ ; 53.8 M records overall. Terms (https://www.freecen.org.uk/terms-and-conditions):
  "provided free of charge for personal research purposes only"; "Access ... is only permitted
  manually via the search page"; automated tools prohibited; extracted data may not be reproduced.
- Verdict: **FAILS rules 1 and 2.**

### B7. Ireland: Matheson 1894 (see headline), plus Griffith's Valuation and census 1901/1911
- **Matheson**: Internet Archive item op1253043-1001, "Surnames in Ireland: Registrar-General:
  special report in appendix to 29th Annual Report", HMSO 1894, 53,368,218 bytes total,
  PDF https://archive.org/download/op1253043-1001/op1253043-1001.pdf , OCR text
  https://archive.org/download/op1253043-1001_djvu.txt (path: .../op1253043-1001/op1253043-1001_djvu.txt),
  item licence tag http://creativecommons.org/licenses/by-nc-nd/3.0/ (on the scan). Data: surnames with
  5+ entries in the 1890 birth indexes; entries by registration province; text list of counties
  "in which principally found". I checked the OCR text: it contains "Gunning" and "Griffith" but the
  county column is detached from the name column (e.g. a lone "Gunning," in one block, county
  strings in another), so the table cannot be parsed reliably without page-image work or manual
  transcription. Other editions 1901, 1909 (not located online). Companion: "Varieties and
  Synonymes of Surnames and Christian Names in Ireland" (1890, HathiTrust per NEHGS; not checked).
  Verdict: public-domain content, **no usable bulk file today**: **NEEDS PERMISSION/WORK**
  (rule 1 fails as structured data; the IA CC BY-NC-ND tag should be resolved or the transcription
  done from the Crown-copyright-expired original). Coverage is 1890 births, not Jamaica-bound
  emigrants, but good for "name concentrated in county X in Ireland".
- **National Archives of Ireland census 1901/1911** (https://census.nationalarchives.ie/):
  search + images, no bulk download seen (host refused connection from my fetch; not verified).
  Site usage policy (https://nationalarchives.ie/site-usage-policy/) says content "may be freely
  accessed and downloaded for personal use"; "unauthorised reproduction is prohibited, including
  extracting or storing content in a retrieval system". No CC/OGL licence stated.
  Verdict: **FAILS rules 1 and 2**; NEEDS PERMISSION (CC/PSI request to NAI).
- **Griffith's Valuation**: transcript is on askaboutireland.ie licensed from Eneclann/OM
  (per John Grenham, https://www.johngrenham.com/blog/2025/07/); NLI 1960s Index of Surnames of
  Householders is print/microfiche. No bulk open file. **FAILS rule 1/2.** Not verified at source.
- **Barry Griffin's Irish surname maps** (1901/1911, 6,000+ surnames, partial coverage; described at
  https://www.irishcentral.com/roots/irish-surname-maps): personal site, no licence or download
  found. **NEEDS PERMISSION** (the author could release a table).
- **Ó Gráda, "What's in an Irish Surname?"** UCD WP2016/05, CC-licensed paper
  (http://hdl.handle.net/10197/7716), national 1911 counts for major names only; no dataset
  found. Repository page returned 405; not verified.

### B8. Scotland
- ScotlandsPeople: paid credits + login; data not bulk. FAILS rule 1. (Not fetched; from
  general knowledge and search snippets, not verified.)
- **NRS "Most common surnames"** (https://www.nrscotland.gov.uk/publications/most-common-surnames-2025/):
  XLSX download (~1.1 MB; the 2024 page was described as having a CSV with year, surname, count,
  rank for surnames occurring >=10 times, selected years from 1975). Licence: "All content is
  available under the Open Government Licence v3.0, except for graphic assets and where otherwise
  stated." Stable URL, citable, free, no login.
  Verdict: **QUALIFIES on rules 1-6, but low value**: Scotland-wide counts only (no geography),
  1975+ births/marriages/deaths. Useful only as "surname count in Scotland today". The earlier
  NRS surname page URL I tried returned 404 (path changed).
- ONS: states it will not provide bespoke full surname lists
  (https://www.ons.gov.uk/aboutus/transparencyandgovernance/freedomofinformationfoi/completelistofallforenamesandsurnamesintheuk);
  OGL v3.0 for site content, but no surname file. NISRA: not checked.

### B9. FaNBI: Oxford Dictionary of Family Names in Britain and Ireland
- ~45,000 surnames (>100 bearers today, or >20 in 1881); AHRC "Family Names of the United
  Kingdom" project, UWE Bristol 2010-16 (Coates, Hanks, Hodges). OUP/Oxford Reference
  subscription; free access only 14-21 May 2020. No open data release found. **FAILS rules 1/2.**
  Ask OUP/UWE if a surname -> etymology-category table can be licensed (NEEDS PERMISSION).

## Ranked outcome

Qualifying now (all six rules):
1. NRS Most Common Surnames (OGL v3.0). Real but low value (no geography, post-1975 Scots only).
2. Bremen CHUP passenger lists (CC BY 4.0). Qualifies; zero relevance for Jamaica (no 1835 sailing). Skip.

Closest to valuable but not qualifying (by value):
1. UKDS 1881 census SN 4177/4178: best data, fails rule 1 (login, HE/FE only). Only route is
   written permission to publish a derived surname x county count table (UKDS + Essex + the
   Genealogical Society of Utah/FamilySearch as co-owners).
2. Matheson 1894 (Ireland): free to use in principle (public domain), but needs OCR/transcription
   of page images; cleanest path to an Ireland-by-county table without asking anyone.
3. UCL Public Profiler (Longley/Cheshire): ask for a table of surname -> 1881 county concentration.
4. Barry Griffin (Ireland 1901/1911) and NAI census: ask for permission.
5. Scottish Emigration Database: ask Aberdeen; low value.

For the library's stated goal ("Gunning: concentrated in X counties in 1881"), the only
rule-clean route is to build the 1881 table ourselves from a source we have permission to
redistribute from, i.e. get written permission from UKDS/depositors, or accept computing it from
the UKDS data locally (opt-in, user supplies own file, no redistribution) which still fails
rule 3 (pinned fetch without login) and so would need a rule amendment.

## Not verified / blocked
- britishsurnames.uk (403 Cloudflare), discovery.ucl.ac.uk (403), census.nationalarchives.ie
  (connection refused), nationalarchives.ie terms page (404), UCD repository (405),
  ScotlandsPeople, IPUMS licence text, UKDS EUL text on derived tables, SN 4178 access tier,
  NISRA, Archive.org item rights beyond the license URL.
- Whether Jamaica Archives holds a digitised 1835 registry.
