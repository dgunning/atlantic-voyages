# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.6
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Surnames of Jamaica's claimants, 1835–1845
#
# This is the first step towards a data layer on European migration to Jamaica: where
# Jamaican surnames came from. No open bulk dataset of European arrivals in Jamaica exists
# (see `research_notes/European migration sources/`), so this notebook starts with what the
# library already holds: the *Legacies of British Slavery* (LBS) records published through
# Enslaved.org.
#
# After the Slavery Abolition Act of 1833, people who claimed ownership of enslaved people
# in Jamaica applied to the Slave Compensation Commission. LBS records each claim
# (1835–1845) and the people named in it: awardees, claimants, counterclaimants,
# executors and trustees.
#
# What the index is, and what it is not:
#
# - It is an index of **surnames of people named in Jamaican compensation claims**. Most
#   were of European descent, but not all: the records include free people of colour and
#   Maroons who owned enslaved people. Where the source records a description of colour,
#   the index counts it.
# - It is **not a migration record**. A claim says nothing about where a person was born.
#   Many claimants lived in Britain and never saw Jamaica.
# - **Parish is known for about a quarter of claims.** In the Enslaved.org copy, claim
#   names drop the parish ("Jamaica 429", not "Jamaica Westmoreland 429"), and the same
#   claim number recurs in different parishes. A claim gets a parish only when it links to
#   an estate whose place record gives one.
# - Surnames are grouped as written, after removing editorial marks such as "(sic)" and
#   peerage titles. Spelling variants (Gunn, Gunning) are not merged.
#
# Needs the full data and the Enslaved.org source:
# `uv run voyages fetch && uv run voyages fetch -d enslaved && uv run voyages build`.

# %%
import pandas as pd

import voyages
from voyages import Voyages

pd.set_option("display.max_colwidth", 80)

LBS_PROJECT = 13445  # enslaved_projects.project_id for Legacies of British Slavery
v = Voyages()
con = v.con

# %% [markdown]
# ## Jamaican claims and their parish
#
# A claim is an LBS event whose record ID starts `LBS-EVE-CLA-`. Its place is either
# "Jamaica" itself, or an estate or other place inside Jamaica, whose `located_in` path
# ends with the parish (e.g. `Caribbean Islands; Americas; Jamaica; Westmoreland`).

# %%
con.sql(
    """
    CREATE OR REPLACE TEMP TABLE jamaica_claims AS
    WITH claim_places AS (
        SELECT
            e.event_id, e.event_record_id, e.event_name, e.event_year,
            CASE
                WHEN pl.located_in LIKE '%; Jamaica; %'
                    THEN split_part(pl.located_in, '; Jamaica; ', 2)
                WHEN pl.place_type = 'County or Parish' AND pl.located_in LIKE '%Jamaica'
                    THEN pl.place_label
            END AS parish
        FROM enslaved_events e
        JOIN enslaved_event_places ep USING (event_id)
        JOIN enslaved_places pl USING (place_id)
        WHERE e.event_record_id LIKE 'LBS-EVE-CLA-%'
          AND (pl.place_label = 'Jamaica' OR pl.located_in LIKE '%Jamaica%')
    )
    SELECT
        event_id,
        any_value(event_record_id) AS claim_record_id,
        any_value(event_name) AS claim,
        any_value(event_year) AS claim_year,
        string_agg(DISTINCT parish, '; ' ORDER BY parish) AS parish
    FROM claim_places
    GROUP BY event_id
    """
)
claims = con.sql("SELECT * FROM jamaica_claims").df()
claim_summary = pd.Series(
    {
        "claims": len(claims),
        "with parish": int(claims.parish.notna().sum()),
        "first year": int(claims.claim_year.min()),
        "last year": int(claims.claim_year.max()),
    }
)
claim_summary

# %%
claims.parish.value_counts().head(22).rename("claims").to_frame()

# %% [markdown]
# ## People named in the claims
#
# `surname_as_written` is the source's surname. `surname` removes editorial marks
# ("(sic)", "[sp?]", "?"), notes in brackets ("(later Riches Blagrave)"), and peerage
# titles after a comma ("Ogilvy, 4th Earl of Airlie" becomes "Ogilvy"). People recorded
# as "Unnamed" have no surname and are left out of the index.

# %%
people = con.sql(
    """
    SELECT DISTINCT
        p.person_id, p.person_record_id, p.person_name, trim(p.surname) AS surname_as_written,
        p.sex, p.race_or_color, c.claim_record_id, c.claim, c.claim_year, c.parish
    FROM jamaica_claims c
    JOIN enslaved_roles r USING (event_id)
    JOIN enslaved_people p USING (person_id)
    """
).df()


def clean_surname(s: str | None) -> str | None:
    if s is None or pd.isna(s):
        return None
    s = s.split(",")[0]  # peerage title
    s = pd.Series([s]).str.replace(r"\((?:sic|\?|later [^)]*|was [^)]*)\)", "", regex=True)[0]
    s = s.replace("[sic]", "").replace("[sp?]", "").replace("?", "")
    s = s.replace("[", "").replace("]", "")  # "Samue[l]s" -> "Samuels"
    return " ".join(s.split()) or None


people["surname"] = people.surname_as_written.map(clean_surname)
people_summary = pd.Series(
    {
        "people": people.person_id.nunique(),
        "with a surname": people.loc[people.surname.notna(), "person_id"].nunique(),
        "distinct surnames": people.surname.nunique(),
        "colour recorded": people.loc[people.race_or_color.notna(), "person_id"].nunique(),
    }
)
people_summary

# %% [markdown]
# ## The index
#
# One row per surname: how many people and claims, the claim years, the parishes known,
# and how many of the people have a description of colour in the source.

# %%
named = people[people.surname.notna()].copy()
named["colour_person"] = named.person_id.where(named.race_or_color.notna())
index = (
    named.groupby("surname")
    .agg(
        people=("person_id", "nunique"),
        claims=("claim_record_id", "nunique"),
        first_year=("claim_year", "min"),
        last_year=("claim_year", "max"),
        parishes=(
            "parish",
            lambda s: "; ".join(sorted({p for v in s.dropna() for p in v.split("; ")})),
        ),
        colour_recorded=("colour_person", "nunique"),
    )
    .sort_values(["people", "claims"], ascending=False)
)
index.head(25)

# %% [markdown]
# Campbell heads the list. The top 25 mix surnames common in Scotland (Grant, Gordon,
# Reid, Anderson, Robertson, Stewart) with ones common across England and Wales (Smith,
# Williams, Brown, Jones). The index cannot say more than that: it has no origin field,
# and a surname is not a birthplace. A surname reference table (where each name was
# concentrated in Britain and Ireland) is the next layer, and needs permission from its
# publishers (requested; see `PLAN_STORIES.md`, S-5).
#
# Most surnames are rare: more than half appear for only one person.

# %%
singletons = int((index.people == 1).sum())
print(f"{singletons:,} of {len(index):,} surnames ({singletons / len(index):.0%}) have one person")

# %% [markdown]
# ## Looking up a surname
#
# `lookup` returns every person and claim for a surname, with links to the LBS pages. The
# LBS ID is the number after `LBS-PER-` or `LBS-EVE-CLA-`.


# %%
def lookup(surname: str) -> pd.DataFrame:
    rows = people[people.surname.str.lower() == surname.lower()].copy()
    rows["person_url"] = (
        "https://lbs.ucl.ac.uk/lbs/person/view/"
        + rows.person_record_id.str.removeprefix("LBS-PER-")
    )
    rows["claim_url"] = (
        "https://lbs.ucl.ac.uk/lbs/claim/view/"
        + rows.claim_record_id.str.removeprefix("LBS-EVE-CLA-")
    )
    cols = [
        "person_name",
        "claim",
        "claim_year",
        "parish",
        "race_or_color",
        "person_url",
        "claim_url",
    ]
    return rows[cols].sort_values(["claim_year", "person_name"]).reset_index(drop=True)


gunning = lookup("Gunning")
gunning

# %% [markdown]
# James Gunning is named in one claim, "Jamaica 429", with no parish in the data. The LBS
# page for claim 15709 (https://lbs.ucl.ac.uk/lbs/claim/view/15709, checked 2026-10-20)
# names it "Jamaica Westmoreland 429": 4 enslaved people, £100 10s 5d, awarded 18 January
# 1836. This is the parish gap described above.
#
# Hugh Gunning, a Westmoreland planter whose will was proved in 1775, is in the LBS
# records too (`LBS-PER-2146663319`) but is not in this index: it covers only people named
# in the 1835–1845 claims.

# %% [markdown]
# ## One parish: Westmoreland
#
# Surnames in Westmoreland claims, where the parish is known.

# %%
west = named[named.parish.fillna("").str.contains("Westmoreland")]
west_index = (
    west.groupby("surname")
    .agg(people=("person_id", "nunique"), claims=("claim_record_id", "nunique"))
    .sort_values(["people", "claims"], ascending=False)
)
print(
    f"{len(west_index)} surnames, {west.person_id.nunique()} people, "
    f"{west.claim_record_id.nunique()} claims with a known Westmoreland parish"
)
west_index.head(20)

# %% [markdown]
# ## Checks
#
# Values checked against the LBS site on 2026-10-20:
#
# - Claim 15709 (https://lbs.ucl.ac.uk/lbs/claim/view/15709): James Gunning, sole
#   claimant, award dated 18 January 1836.
# - Claim 16234 (https://lbs.ucl.ac.uk/lbs/claim/view/16234): Jamaica Westmoreland 414,
#   New Shafston Pen. The derived parish here must be Westmoreland.

# %%
assert claim_summary.tolist() == [13182, 3366, 1835, 1845]
assert people_summary["people"] == 12217
assert index.index[0] == "Campbell"
assert gunning[["person_name", "claim", "claim_year"]].values.tolist() == [
    ["James Gunning", "Jamaica 429", 1836]
]
assert pd.isna(gunning.parish[0])
c414 = claims.set_index("claim_record_id").loc["LBS-EVE-CLA-16234"]
assert (c414.claim, c414.parish, c414.claim_year) == ("Jamaica 414", "Westmoreland", 1837)
assert clean_surname("Ogilvy, 4th Earl of Airlie") == "Ogilvy"
assert clean_surname("Gabandon (sic)") == "Gabandon"
assert clean_surname("Samue[l]s") == "Samuels"
assert clean_surname("Riches (later Riches Blagrave)") == "Riches"

# %% [markdown]
# Data: Enslaved.org, dataset *Legacies of British Slavery* (Centre for the Study of the
# Legacies of British Slavery, UCL; https://doi.org/10.12921/07em-3t32), CC BY 4.0.

# %%
print(voyages.citation("enslaved"))
