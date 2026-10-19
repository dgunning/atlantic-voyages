"""The fluent query API (voyages.api.query).

Offline tests use the Parquet built from the committed fixtures (conftest.py).
Results are checked against an independent pandas computation on the
imputed columns of ``voyages_wide``, and on real voyages.
"""

import os

import pandas as pd
import pytest

from voyages import Voyages
from voyages.api.query import PlaceLookupError, Query, resolve_label, resolve_place


@pytest.fixture(scope="module")
def wide(v) -> pd.DataFrame:
    return v.table("voyages_wide").to_pandas()


# ------------------------------------------------------------- name lookups
@pytest.mark.parametrize(
    "name,expected",
    [
        ("Jamaica", (35100, "region")),
        ("jamaica", (35100, "region")),
        ("Kingston", (35114, "place")),
        ("Kingston (Jamaica)", (35114, "place")),  # the Intra-American spelling
        ("Gold Coast", (60400, "region")),
        ("Africa", (60000, "broad_region")),
        # Prefix match: the region, not "... port unspecified".
        ("Bight of Biafra", (60600, "region")),
        (60605, (60605, "place")),
        ("60605", (60605, "place")),
    ],
)
def test_resolve_place(v, name, expected):
    assert tuple(resolve_place(v, name)) == expected


def test_ambiguous_place_lists_the_codes(v):
    with pytest.raises(PlaceLookupError, match="60118.*60130"):
        resolve_place(v, "Senegal")


def test_unknown_place_suggests_names(v):
    with pytest.raises(PlaceLookupError, match="Jamaica"):
        resolve_place(v, "Jamiaca")
    with pytest.raises(PlaceLookupError):
        resolve_place(v, 12345)


def test_resolve_label(v):
    assert resolve_label(v, "outcomes_captives", "captives disembarked in the americas") == 1
    assert resolve_label(v, "nations", "Great Britain") == 7
    # Matches "... in the Americas" and "... in Africa or Europe".
    with pytest.raises(PlaceLookupError, match="several"):
        resolve_label(v, "outcomes_captives", "Captives disembarked")


# ----------------------------------------------------------------- filters
def test_queries_are_immutable_and_lazy(v):
    base = v.transatlantic
    narrowed = base.embarked_from("Gold Coast")
    assert isinstance(narrowed, Query) and narrowed is not base
    assert base.clauses == () and len(narrowed.clauses) == 1


def test_datasets(v):
    assert len(v.transatlantic) == 300
    assert len(v.intraamerican) == 300
    assert len(v.query()) == 600
    with pytest.raises(ValueError):
        v.query("estimates")


def test_cerberus_matches_every_filter(v):
    """Voyage 91000, Cerberus: Anomabu (Gold Coast) -> Kingston, Jamaica, 1766,
    British flag (https://legacy.slavevoyages.org/voyage/91000/variables)."""
    q = (
        v.transatlantic.embarked_from("Gold Coast")
        .disembarked_in("Kingston")
        .between(1766, 1766)
        .flag("Great Britain")
    )
    assert 91000 in set(q.to_pandas(columns=["voyage_id"])["voyage_id"])
    for wrong in (
        v.transatlantic.embarked_from("Bight of Benin"),
        v.transatlantic.disembarked_in("Barbados"),
        v.transatlantic.between(1767),
    ):
        assert 91000 not in set(wrong.to_pandas(columns=["voyage_id"])["voyage_id"])


def test_region_filter_equals_the_imputed_region_column(v, wide):
    got = set(v.query().embarked_from("Gold Coast").to_pandas(["voyage_id"])["voyage_id"])
    expected = set(wide.loc[wide.principal_purchase_region_imputed == 60400, "voyage_id"])
    assert got == expected and got


def test_broad_region_and_several_places_combine_with_or(v, wide):
    got = set(
        v.transatlantic.disembarked_in("Brazil", "Jamaica").to_pandas(["voyage_id"])["voyage_id"]
    )
    ta = wide[wide.dataset == "transatlantic"]
    expected = set(
        ta.loc[
            (ta.principal_landing_broad_region_imputed == 50000)
            | (ta.principal_landing_region_imputed == 35100),
            "voyage_id",
        ]
    )
    assert got == expected and got


def test_between_is_inclusive_and_open_ended(v, wide):
    ta = wide[wide.dataset == "transatlantic"]
    years = ta.year_arrived_imputed
    assert len(v.transatlantic.between(1750, 1800)) == years.between(1750, 1800).sum()
    assert len(v.transatlantic.between(1800)) == (years >= 1800).sum()
    assert len(v.transatlantic.between(end=1700)) == (years <= 1700).sum()
    dep = ta.year_departed_imputed
    assert len(v.transatlantic.between(1800, on="departed")) == (dep >= 1800).sum()


def test_captive_outcome(v, wide):
    got = len(v.query().captive_outcome("Captives disembarked in the Americas"))
    assert got == (wide.outcome_for_captives_imputed == 1).sum()


def test_where_escape_hatch_uses_parameters(v):
    q = v.transatlantic.where("ship_name = ?", "Cerberus")
    assert q.to_pandas(["voyage_id"])["voyage_id"].tolist() == [91000]


# --------------------------------------------------------------- summaries
def test_by_decade_matches_pandas(v, wide):
    got = v.transatlantic.by_decade().set_index("decade")
    ta = wide[wide.dataset == "transatlantic"]
    decade = (ta.year_arrived_imputed // 10 * 10).astype("Int64")
    exp = ta.groupby(decade, dropna=False).agg(
        voyages=("voyage_id", "size"),
        embarked=("embarked_imputed", "sum"),
        disembarked=("disembarked_imputed", "sum"),
    )
    assert got["voyages"].sum() == 300
    for d, row in exp.iterrows():
        g = got.loc[got.index.isna()] if pd.isna(d) else got.loc[[d]]
        assert g["voyages"].item() == row.voyages, d
        assert g["embarked"].item() == row.embarked, d
        assert g["disembarked"].item() == row.disembarked, d


def test_by_decade_with_extra_columns(v, wide):
    df = v.transatlantic.by_decade("voyages", by="embarkation_region_name")
    assert list(df.columns) == ["decade", "embarkation_region_name", "voyages"]
    assert df.voyages.sum() == 300
    gold = df[df.embarkation_region_name == "Gold Coast"].voyages.sum()
    ta = wide[wide.dataset == "transatlantic"]
    assert gold == (ta.principal_purchase_region_imputed == 60400).sum()
    with pytest.raises(KeyError):
        v.transatlantic.by_decade(by="nope")


def test_by_decade_keeps_voyages_without_a_year(v, wide):
    df = v.query().by_decade("voyages")
    assert df["voyages"].sum() == 600
    missing = wide.year_arrived_imputed.isna().sum()
    assert df.loc[df.decade.isna(), "voyages"].sum() == missing


def test_by_region(v, wide):
    df = v.transatlantic.by_region("embarkation")
    assert df["voyages"].sum() == 300
    gold = df.loc[df.embarkation_region == 60400]
    assert gold["embarkation_region_name"].item() == "Gold Coast"
    ta = wide[wide.dataset == "transatlantic"]
    assert gold["voyages"].item() == (ta.principal_purchase_region_imputed == 60400).sum()
    broad = v.transatlantic.by_region("disembarkation", level="broad_region")
    assert set(broad.columns) >= {"disembarkation_broad_region_name", "voyages"}
    with pytest.raises(ValueError):
        v.transatlantic.by_region("purchase")


def test_measures_carry_provenance(v):
    df = v.transatlantic.by_decade(["voyages", "embarked", "captives_purchased"])
    assert df.attrs["provenance"] == {
        "decade": "imputed",  # from the imputed year of arrival
        "embarked": "imputed",
        "captives_purchased": "recorded",
    }


def test_by_rejects_unknown_columns(v):
    assert "flag_imputed_name" in v.transatlantic.by("flag_imputed_name").columns
    with pytest.raises(KeyError, match="did you mean"):
        v.transatlantic.by("flag_imputed_nam")
    with pytest.raises(KeyError):
        v.transatlantic.by("1); DROP TABLE places; --")


def test_summary_agrees_with_by_decade(v):
    s = v.query().summary().set_index("dataset")
    d = v.intraamerican.by_decade()
    assert s.loc["intraamerican", "voyages"] == d["voyages"].sum() == 300
    assert s.loc["intraamerican", "embarked"] == d["embarked"].sum()


def test_endpoints_of_a_query(v):
    ends = v.transatlantic.disembarked_in("Jamaica").endpoints(drawable_only=True)
    assert len(ends) and ends["drawable"].all()
    assert (ends["disembarkation_region_name"] == "Jamaica").all()
    assert list(ends.columns)[:2] == ["voyage_id", "dataset"]


def test_output_formats(v):
    q = v.transatlantic.where("voyage_id = 91000")
    assert q.to_arrow(["voyage_id", "ship_name"]).to_pylist() == [
        {"voyage_id": 91000, "ship_name": "Cerberus"}
    ]
    pl = pytest.importorskip("polars")
    assert isinstance(q.to_polars(), pl.DataFrame)


# ---------------------------------------------------------------- full data
@pytest.mark.fulldata
@pytest.mark.skipif(not os.environ.get("VOYAGES_DATA_DIR"), reason="needs VOYAGES_DATA_DIR")
def test_plan_example_matches_pandas():
    """The PLAN.md example, Bight of Biafra -> Jamaica, 1700-1800, against pandas
    on the imputed region columns of the full build."""
    with Voyages() as v:
        got = (
            v.transatlantic.embarked_from("Bight of Biafra")
            .disembarked_in("Jamaica")
            .between(1700, 1800)
            .by_decade(["voyages", "embarked", "disembarked"])
        )
        wide = v.sql(
            "SELECT year_arrived_imputed y, embarked_imputed e, disembarked_imputed d "
            "FROM voyages_wide WHERE dataset = 'transatlantic' "
            "AND principal_purchase_region_imputed = 60600 "
            "AND principal_landing_region_imputed = 35100 "
            "AND year_arrived_imputed BETWEEN 1700 AND 1800"
        ).to_pandas()
    assert got["voyages"].sum() == len(wide) == 634
    assert got["embarked"].sum() == wide.e.sum()
    assert got["disembarked"].sum() == wide.d.sum()
