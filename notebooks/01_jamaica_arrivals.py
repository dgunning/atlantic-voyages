# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Arrivals in Jamaica by African region of embarkation, by decade
#
# About a million enslaved Africans were landed in Jamaica. This notebook asks where on the
# African coast they were embarked, decade by decade, and how the answer depends on the source:
#
# - **Recorded**: numbers transcribed from historical documents. For each voyage that landed
#   captives in Jamaica, the number of captives arriving at the first place of landing
#   (SLAARRIV), with the African region taken from the recorded principal place of purchase.
#   Public domain.
# - **Imputed**: the voyage database's imputed totals (SLAMIMP) and imputed principal places,
#   which fill gaps in the record voyage by voyage. CC BY-NC 4.0.
# - **Estimates**: the 2010 Estimates, which model the whole trade, including voyages that left
#   no record. CC BY-NC 4.0.
#
# Read the gaps between the three as a measure of what the surviving records do not show,
# not as errors in any one of them.
#
# Needs the full data: `uv run voyages fetch && uv run voyages build`.

# %%
import matplotlib.pyplot as plt
import pandas as pd

import voyages
from voyages import Voyages

v = Voyages()

# %% [markdown]
# ## Regions
#
# The voyage data and the Estimates name the African regions slightly differently, and use
# different codes. The eight regions correspond one to one. "Other Africa" in the voyage data
# means the record does not say where in Africa the captives were embarked; the Estimates have
# no such category, because they assign every captive to a region.

# %%
REGIONS = pd.DataFrame(
    [
        (60100, 1, "Senegambia"),
        (60200, 2, "Sierra Leone"),
        (60300, 3, "Windward Coast"),
        (60400, 4, "Gold Coast"),
        (60500, 5, "Bight of Benin"),
        (60600, 6, "Bight of Biafra"),
        (60700, 7, "West Central Africa"),
        (60800, 8, "South-east Africa"),
    ],
    columns=["voyage_region", "estimates_region", "region"],
)
UNKNOWN = "Region not known"

names = REGIONS.assign(
    voyage_name=REGIONS.voyage_region.map(
        v.sql("SELECT code, name FROM places").to_pandas().set_index("code").name
    ),
    estimates_name=REGIONS.estimates_region.map(
        v.table("estimates_embarkation_regions").to_pandas().set_index("code").label
    ),
)
# The short names are the Estimates labels; check the voyage names say the same thing.
assert (names.region == names.estimates_name).all()
assert all(
    n.split(" and ")[0].replace("Southeast", "South-east").startswith(r.split()[0])
    for n, r in zip(names.voyage_name, names.region, strict=True)
)
names[["region", "voyage_name", "estimates_name"]]


# %%
def short_region(code):
    """Voyage region code -> the short region name, or 'Region not known'."""
    lookup = REGIONS.set_index("voyage_region").region
    return lookup.get(code, UNKNOWN) if pd.notna(code) else UNKNOWN


# %% [markdown]
# ## Three sources, one shape
#
# Each source becomes a table of decade x region x people. Decades follow the year of arrival:
# the imputed year (YEARAM) for the imputed data and the Estimates, and the recorded year of
# first landing for the recorded data.

# %%
imputed = (
    v.transatlantic.disembarked_in("Jamaica")
    .by_decade(["voyages", "disembarked"], by="embarkation_region")
    .assign(region=lambda d: d.embarkation_region.map(short_region), source="Imputed")
    .rename(columns={"disembarked": "people"})
)

recorded = (
    v.transatlantic.recorded_only()
    .disembarked_in("Jamaica")
    .by_decade(["voyages", "captives_arrived_first_landing"], by="embarkation_region")
    .assign(region=lambda d: d.embarkation_region.map(short_region), source="Recorded")
    .rename(columns={"captives_arrived_first_landing": "people"})
)

estimates = (
    v.sql(
        """
        SELECT (year // 10 * 10)::SMALLINT AS decade, embarkation_region AS estimates_region,
               sum(disembarked_estimated_total) AS people
        FROM estimates
        WHERE disembarkation_region = (
            SELECT code FROM estimates_disembarkation_regions WHERE label = 'Jamaica')
        GROUP BY ALL
        """
    )
    .to_pandas()
    .merge(REGIONS[["estimates_region", "region"]], how="left")
    .assign(region=lambda d: d.region.fillna(UNKNOWN), source="Estimates", voyages=pd.NA)
)

cols = ["source", "decade", "region", "voyages", "people"]
long = pd.concat([estimates[cols], imputed[cols], recorded[cols]], ignore_index=True)
long["people"] = long.people.fillna(0).astype(int)

# %% [markdown]
# ### Checks
#
# The Estimates table reproduces the site's total embarked (12,521,337 on
# https://legacy.slavevoyages.org/assessment/estimates, checked 2026-10-19; the `.sav` rounds
# each row, see docs/DATA.md). Each source's regional rows add up to its own total.

# %%
total_embarked = v.sql("SELECT sum(embarked_estimated_total) FROM estimates").relation.fetchone()[0]
assert abs(total_embarked - 12_521_337) <= 20, total_embarked

imp_total = v.transatlantic.disembarked_in("Jamaica").summary().disembarked.item()
assert imputed.people.sum() == imp_total
rec_summary = v.transatlantic.recorded_only().disembarked_in("Jamaica").summary()
assert recorded.people.sum() == rec_summary.captives_arrived_first_landing.item()
assert (estimates.region != UNKNOWN).all()  # the Estimates assign every captive to a region

# %% [markdown]
# ## Totals by region

# %%
by_region = long.pivot_table(
    index="region", columns="source", values="people", aggfunc="sum", fill_value=0
)[["Recorded", "Imputed", "Estimates"]]
order = [*REGIONS.region, UNKNOWN]
by_region = by_region.reindex(order).fillna(0).astype(int)
by_region.loc["Total"] = by_region.sum()
by_region

# %% [markdown]
# How many voyages lie behind the voyage-based columns, and how many of the recorded voyages
# have a count of captives at all:

# %%
coverage = pd.DataFrame(
    {
        "voyages": [rec_summary.voyages.item(), imputed.voyages.sum()],
        "voyages with a count": [
            rec_summary.voyages_with_captives_arrived_first_landing.item(),
            v.transatlantic.disembarked_in("Jamaica").summary().voyages_with_disembarked.item(),
        ],
    },
    index=["Recorded", "Imputed"],
)
coverage

# %% [markdown]
# ## By decade
#
# Chart conventions: one colour per source in every chart (Estimates blue, imputed orange,
# recorded aqua and dashed), people in thousands, one y-axis per panel.

# %%
COLORS = {"Estimates": "#2a78d6", "Imputed": "#eb6834", "Recorded": "#1baf7a"}
STYLES = {"Estimates": "-", "Imputed": "-", "Recorded": "--"}
SURFACE, INK, MUTED = "#fcfcfb", "#0b0b0b", "#52514e"

plt.rcParams.update(
    {
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "axes.edgecolor": MUTED,
        "axes.labelcolor": MUTED,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "text.color": INK,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.grid.axis": "y",
        "grid.color": "#e4e3df",
        "grid.linewidth": 0.8,
        "font.size": 10,
    }
)

by_decade = (
    long.dropna(subset=["decade"])
    .pivot_table(index="decade", columns="source", values="people", aggfunc="sum", fill_value=0)
    .sort_index()
)
fig, ax = plt.subplots(figsize=(9, 4.5))
for source in ["Estimates", "Imputed", "Recorded"]:
    s = by_decade[source] / 1000
    ax.plot(s.index, s.values, STYLES[source], color=COLORS[source], linewidth=2, label=source)
    # Direct labels where the three lines sit well apart.
    below = source == "Recorded"
    ax.annotate(
        source, (1720, s.loc[1720]), xytext=(12 if below else -4, -14 if below else 6),
        textcoords="offset points", ha="left" if below else "right", color=INK, fontsize=9,
    )  # fmt: skip
ax.set_title("People disembarked in Jamaica, by decade of arrival", loc="left", color=INK)
ax.set_ylabel("thousands of people")
ax.set_xlim(by_decade.index.min(), by_decade.index.max() + 10)
ax.legend(frameon=False, loc="upper left")
fig.tight_layout()
fig.savefig("figures/01_jamaica_by_decade.png", dpi=150)

# %%
by_decade.astype(int)

# %% [markdown]
# The recorded line drops in the 1730s and 1770s. Few of that decade's voyages have a
# transcribed count of captives arriving, although the voyages themselves are known:

# %%
v.sql(
    """
    SELECT (year_arrived_imputed // 10 * 10)::SMALLINT AS decade,
           count(*) AS voyages,
           count(captives_arrived_first_landing) AS with_recorded_count
    FROM voyages_wide JOIN voyage_endpoints USING (voyage_id, dataset)
    WHERE dataset = 'transatlantic' AND disembarkation_region = 35100
      AND year_arrived_imputed BETWEEN 1700 AND 1809
    GROUP BY 1 ORDER BY 1
    """
).to_pandas().assign(share=lambda d: (d.with_recorded_count / d.voyages).round(2))

# %% [markdown]
# ## By region and decade
#
# One panel per region, same scale throughout so the panels compare. In the voyage data, the
# last panel holds the captives whose region of embarkation is not known; the Estimates have
# assigned all of them to the eight regions.

# %%
grid = long.dropna(subset=["decade"]).pivot_table(
    index=["region", "decade"], columns="source", values="people", aggfunc="sum", fill_value=0
)
decades = range(int(grid.index.get_level_values("decade").min()), 1870, 10)
fig, axes = plt.subplots(3, 3, figsize=(11, 8), sharex=True, sharey=True)
for ax, region in zip(axes.flat, order, strict=True):
    panel = grid.loc[region].reindex(decades, fill_value=0) if region in grid.index else None
    for source in ["Estimates", "Imputed", "Recorded"]:
        if panel is not None and source in panel:
            ax.plot(
                panel.index,
                panel[source] / 1000,
                STYLES[source],
                color=COLORS[source],
                linewidth=1.6,
                label=source,
            )
    ax.set_title(region, loc="left", fontsize=10, color=INK)
for ax in axes[:, 0]:
    ax.set_ylabel("thousands")
axes[0, 0].legend(frameon=False, fontsize=8, loc="upper left")
fig.suptitle(
    "People disembarked in Jamaica, by African region of embarkation and decade",
    x=0.01,
    ha="left",
    color=INK,
)
fig.tight_layout()
fig.savefig("figures/01_jamaica_by_region.png", dpi=150)

# %% [markdown]
# ## What the voyage records cover
#
# The imputed voyage totals as a share of the Estimates, by decade: how much of the modelled
# trade into Jamaica is accounted for by voyages in the database. Decades with fewer than
# 1,000 people in the Estimates are left out; their ratios are noise.

# %%
main = by_decade[by_decade.Estimates >= 1000]
pd.DataFrame(
    {
        "Estimates": main.Estimates.astype(int),
        "Imputed": main.Imputed.astype(int),
        "imputed / estimates": (main.Imputed / main.Estimates).round(2),
    }
)

# %%
# The figures quoted below, checked against the tables above.
imp, est = by_region["Imputed"], by_region["Estimates"]
known_gap = est["Total"] - (imp["Total"] - imp[UNKNOWN])
assert (imp[UNKNOWN], imp["Total"], est["Total"]) == (225_283, 934_577, 1_019_588)
assert est["Total"] - imp["Total"] == 85_011
assert 0.70 < imp[UNKNOWN] / known_gap < 0.75
assert set(est.drop(["Total", UNKNOWN]).nlargest(2).index) == {"Gold Coast", "Bight of Biafra"}
assert set(by_region["Recorded"].drop(["Total", UNKNOWN]).nlargest(2).index) == {
    "Gold Coast",
    "Bight of Biafra",
}
ratios = (main.Imputed / main.Estimates).loc[1700:1800]
assert 0.84 <= ratios.min() < 0.85 and 0.99 <= ratios.max() < 0.995

# %% [markdown]
# ## Reading the results
#
# - The Gold Coast and the Bight of Biafra are the two largest known regions of embarkation in
#   every column. The Estimates put them close together, at about 300,000 people each.
# - In the imputed voyage data, 225,283 of the 934,577 people were on voyages whose African
#   region is not known. The Estimates assign such captives to regions, so this accounts for
#   nearly three quarters of the gap between the two columns for the eight regions. The rest,
#   85,011 people, is the trade the Estimates add for voyages missing from the database.
# - In each decade from 1700 to 1809, the peak of the trade into Jamaica, voyages in the
#   database account for 84 to 99 per cent of the Estimates; the gap is widest before 1700.
# - The recorded column is a floor, not an estimate: it counts only voyages with a transcribed
#   number of captives arriving at the first landing, and that number survives unevenly (35 of
#   307 voyages in the 1730s). Its regions follow the recorded place of purchase, which is
#   missing more often than the imputed one.
# - The Jamaica total in the Estimates (1,019,588) has not been checked against the site,
#   whose estimates page needs its form to select Jamaica.

# %% [markdown]
# ## Source and licence
#
# Imputed variables and the Estimates are licensed CC BY-NC 4.0 by SlaveVoyages; the recorded
# data is public domain. See NOTICE and docs/DATA.md.

# %%
print(voyages.citation())
