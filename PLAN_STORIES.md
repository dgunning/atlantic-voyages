# PLAN_STORIES.md

Status: A3 in progress (2026-10-20): notebook 09, fact sheet and site checks done; historian review still to do. European migration layer started (S-5): notebook 15 and permission emails drafted. Companion to `PLAN.md`: that plan builds the
library; this one adds the sources and analyses behind a series of newspaper articles on
Jamaica and the slave trade (written with the *Jamaica Gleaner* in mind).

## Goal

A series of 8–9 articles, each backed by an executed notebook that a reporter or editor can
rerun and check. Every figure quoted in an article is asserted in a notebook cell, as in
Phase 3.

## Approach: deep on Jamaica, wide only where it explains Jamaica

- Each article opens on something small and real: one voyage, one person, one parish. It then
  pulls back to the Atlantic numbers. Fixture and example voyages are real voyages; the same
  holds here.
- Each article has one finding that cuts against what readers expect, a local hook (a parish
  or town), a map or chart, and a date to publish against.
- Wider material (Brazil, Cuba, the Atlantic as a whole) comes in only to explain something
  about Jamaica.

## Before any article is published

1. **Licence.** The Estimates and every imputed field are CC BY-NC 4.0, and a newspaper is a
   commercial publisher. Either get written permission from SlaveVoyages for publication, or
   use recorded-only figures (`recorded_only=True`) for printed numbers, with imputed figures
   only as context and labelled. Record the answer in `docs/DATA.md`.
2. **Check the headline numbers against the site.** The Estimates Jamaica total (1,019,588,
   notebook 01) has not yet been checked. Record the URL in the test docstring, as usual.
3. **Historian review.** Ask UWI Mona (Department of History and Archaeology; Centre for
   Reparation Research) to review the history in each piece.
4. **Language.** The project's terminology rules apply to article drafts and captions too.
   Treat owners' surnames with care: many Jamaican families carry them.

## New sources

Each new source has to meet the rules in CLAUDE.md and `docs/DATA.md` ("Supplementary
sources"). The rules column says where a source stands.

| # | Source | What it adds | Rules | Effort |
|---|---|---|---|---|
| S1 | SlaveVoyages African Names (People) | Named people with age, sex and height, linked to voyage ID. Mostly people freed from ships seized after 1807; few on Jamaica-bound voyages | Core source; already Phase 1 in `PLAN.md` | Medium |
| S2 | SlaveVoyages Enslavers database (People) | De-duplicated owners and captains with aliases. `voyage_enslavers` has names only as written in the source, with no de-duplication | Core source | Medium |
| S3 | Jamaica population and sugar-export series (published tables, e.g. Higman, *Slave Population and Economy in Jamaica, 1807–1834*) | A denominator: arrivals vs population, and arrivals vs sugar output | Not a bulk file. Needs a rules decision: a curated, cited reference table like the place coordinates (`tools/place_coordinates.py`), one citation per row | Low–medium |
| S4 | Legacies of British Slavery (UCL) | Estates by parish, counts of enslaved people 1809–1839, compensation claims, owners' addresses in Britain | Website only, © UCL. Ask permission first. Articles can cite the site directly without the library ingesting it | Low to ask; medium if granted |
| S5 | Pre-1867 parish boundaries (21 parishes) | Every "your parish" map | Has to be made: georeference a public-domain map (Robertson, 1804) and record a source per row. Listed as a gap in `docs/jamaica-sources.md` | Medium–high |
| S6 | Liberated Africans brought to Jamaica, 1841–1865 (liberatedafricans.org; Parliamentary Papers) | About 10,000 people: the Yoruba settlements (Abeokuta in Westmoreland, Naggo Head), the Central Africans linked to Kumina in St Thomas | No bulk download seen. Check access and licence first | Unknown |
| S7 | Genetic ancestry studies (e.g. Micheletti et al. 2020, *AJHG*) | Ancestry shares in Jamaicans today vs embarkation regions from the voyages | Not ingested. Quote the published summary figures with a citation | Low |
| S8 | The Gleaner's own archive (from 1834) | Coverage of 1838, 1865 and so on, for the paper's own angle | Editorial partnership, not code | — |

## The series

Each piece names its notebook (existing or new), the sources it needs, and a publication date
to aim for.

| # | Working title | Story | Notebooks | Needs | Date to aim for |
|---|---|---|---|---|---|
| A1 | A million landed, 311,000 at emancipation | Scale; why the population did not grow | 01, new 10 | S3; licence check; Estimates total checked | 1 Aug 2027 (Emancipation Day) |
| A2 | Coromantee before Eboe | Order of arrival and culture: Gold Coast dominance before 1750, Akan words and Anansi, Tacky's Revolt (1760) | 01, 04, `docs/history/jamaican-words.md`, new 11 | — | Easter 2027 (Tacky's Revolt began at Easter) |
| A3 | The Montego Bay pipeline | Bight of Biafra to St James, then the Christmas Rebellion (1831) | 06, 07, 09 | S5 helpful, not required | 27 Dec 2026 (195th anniversary) |
| A4 | Calabar and back | The voyages, then Jamaican missionaries going to Calabar in the 1840s; Calabar College | 02, `docs/history/calabar.md` | — | Open |
| A5 | The crossing | Deaths at sea, told through the *Zong* (1781, bound for Black River) | 05, new 12 (one voyage, in depth) | Check the *Zong* record against the site | Open |
| A6 | Kingston the market | People landed, then shipped on to Cartagena, Portobelo and Cuba | 03 | — | Open |
| A7 | Who profited | Merchant firms behind Jamaica voyages; compensation by parish; the reparations debate | new 13 | S2, S4 | Open; tie to reparations news |
| A8 | After 1807 | Liberated Africans, Abeokuta, Kumina | new 14 | S1, S6 | 25 Mar 2027 (220 years since the 1807 Act) |
| A9 | Your DNA vs the ships | What ancestry tests show vs what the voyages record | 01, 03, 04 | S7 | Open |

A3 fits the nearest date and needs no new source, so it should go first.

## Phases

### S-0 — Groundwork (1 session)

- [ ] Write to SlaveVoyages about CC BY-NC data in a commercial newspaper; record the answer
- [ ] Check the Estimates Jamaica total against the site; add the test
- [ ] Write to UCL LBS about research use and redistribution (S4)
- [ ] Decide whether curated tables taken from published books (S3) are allowed; update
      CLAUDE.md and `docs/DATA.md`
- [ ] Contact a UWI Mona historian about review

### S-1 — A3 (1 session)

- [x] Recorded-only figures (`notebooks/09_montego_bay_pipeline.py`): 71% of people landed at
      Montego Bay from the Bight of Biafra vs 36% at Kingston, 1763–1808
- [x] Article-ready charts: voyages by year; Kingston vs Montego Bay origins
- [x] Fact sheet: `docs/stories/a3_fact_sheet.md` (every number, its notebook and licence status)
- [x] Voyage 18129 (*African Queen*) checked on the site (2026-10-20); all recorded values agree
- [x] Montego Bay totals on the site (2026-10-20): same 144 voyages, 40,050 recorded landed (exact); F7's 71% not recomputed there
- [x] Runaway figure redrawn with recorded landings (`09_runaways_vs_landings_recorded.png`)
- [x] Article draft for review: `docs/stories/a3_draft.md`
- [x] Emails drafted (SlaveVoyages, UWI Mona reviewer, Douglas Chambers); kept local, not in git
- [ ] Send the emails (you); historian review; revise; send to editor

### S-2 — People (2–3 sessions)

- [ ] S1 African Names ingest (shared with `PLAN.md` Phase 1)
- [ ] S2 Enslavers ingest, linked to `voyage_enslavers`
- [ ] Notebook 12: one voyage in depth (the *Zong*)

### S-3 — Context and parishes (2–4 sessions)

- [ ] S3 population and sugar series, if allowed (notebook 10)
- [ ] Notebook 11: arrivals by region before and after 1750 (A2)
- [ ] S5 parish boundaries
- [ ] S4 LBS, if permission is granted (notebook 13)

### S-4 — After 1807 and DNA (2 sessions)

- [ ] S6 access check, then ingest or drop
- [ ] Notebook 14: liberated Africans in Jamaica
- [ ] A9 comparison table from published ancestry figures

### S-5 — European migration (started 2026-10-20)

Where Jamaican surnames came from. No open bulk dataset of European arrivals in Jamaica
was found; candidates and verdicts against the supplementary-source rules are in
`research_notes/European migration sources/`.

- [x] Notebook 15: surname index of people named in Jamaica's compensation claims
      (LBS via Enslaved.org): 13,182 claims, 12,217 people, 3,765 surnames; parish known
      for 3,366 claims
- [x] Permission emails drafted (LBS full export and Burnard's inventories; Virtual
      Jamestown indentures; UK Data Service 1881 surname-by-county):
      kept local, not in git. The LBS one replaces the S-0 LBS email
- [ ] Send the emails (you); record the answers in `docs/DATA.md`
- [ ] Decide whether tables transcribed from out-of-copyright books are allowed (also S-0);
      if so, Matheson, *Surnames in Ireland* (1894), as an Ireland surname-by-county table
- [ ] With permission: surname reference table (Britain 1881, Ireland), joined to the index

## Open questions

- Who at the Gleaner is the contact, and do they want a fixed run (weekly) or pieces timed to dates?
- Are notebooks enough for reporters, or do they need a simpler fact-sheet page per article?
- Do figures published in the paper need to be credited per figure, and in what form (citation
  string from `voyages.citation()`)?
- How should owners' names be handled when they match Jamaican surnames today?

## Session log

- 2026-10-20 — Draft plan written: approach, sources S1–S8, articles A1–A9, phases S-0 to S-4.
- 2026-10-20 — A3 started: notebook 09 (recorded-only Montego Bay figures: 144 voyages, 40,050 people recorded landed, 71% from the Bight of Biafra vs 36% at Kingston; peak 1792; the *African Queen* from Calabar, 1793, as the opening voyage), two charts, fact sheet with licence status per figure. History of 1831 checked against secondary sources; death toll varies by source; African-born share of St James not found. Next: site checks, recorded runaway figure, historian review, draft.
- 2026-10-20 — A3 follow-ups: region glossary (Cameroon is in the Bight of Biafra region, not West Central Africa); Montego Bay's Biafra voyages by today's country (Nigeria 76, Gabon 3, Cameroon 0); runaway chart redrawn on recorded landings (68% vs 27%, matching nb07's imputed 67% vs 28%); Cape Lopez double coding noted in DATA.md.
- 2026-10-20 — *African Queen* (18129) checked on the legacy site: recorded values agree (330 aboard, 214 landed, 255 by age and sex, crew 37 to 18, three captains); the site's 116 deaths (35%) are imputed, so the article prints only 330 and 214.
- 2026-10-20 — Montego Bay totals checked on the legacy site: same 144 voyage IDs, 133 recorded counts totalling 40,050 (exact), imputed embarked 47,563 (equal), imputed landed 43,261 vs 43,263. Next: historian review, then draft.
- 2026-10-20 — A3 draft (about 1,150 words, every figure tagged to the fact sheet, review and check points marked) and three emails drafted, not sent. Next: send emails, historian review.
- 2026-10-20 — S-5 started: family-history research (kept local); three source scouts found no open bulk data on European arrivals in Jamaica; notebook 15 (LBS claimant surname index, parish derived from estates for 26% of claims); three permission emails drafted, not sent. Next: send emails; decide on book-derived tables.
