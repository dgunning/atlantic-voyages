"""Field helpers (v.fields, v.describe) and recorded-only queries."""

import pandas as pd
import pytest
from typer.testing import CliRunner

from voyages import schema
from voyages.api.fields import lookup
from voyages.api.query import column_provenance
from voyages.cli import app


# ------------------------------------------------------------------- fields
def test_fields_lists_the_registry(v):
    df = v.fields()
    assert len(df) == len(schema.load())
    assert {"name", "spss_name", "label", "provenance", "derived_from"} <= set(df.columns)


def test_fields_filters(v):
    rec = v.fields(provenance="recorded")
    assert len(rec) and (rec.provenance == "recorded").all()
    est = v.fields(dataset="estimates")
    assert len(est) and est.datasets.str.contains("estimates").all()
    hits = v.fields(search="majbuypt")
    assert hits.name.tolist() == ["principal_purchase_place"]
    assert (
        "principal_purchase_place"
        in v.fields(search="principal port of slave purchase").name.values
    )
    with pytest.raises(ValueError):
        v.fields(provenance="guessed")


def test_year_groupings_are_derived_from_the_imputed_year(v):
    df = v.fields(search="year grouping")
    groupings = (
        v.fields().set_index("name").loc[["period_5yr", "decade", "quarter_century", "century"]]
    )
    assert (groupings.derived_from == "year_arrived_imputed").all()
    assert column_provenance("decade") == "imputed"
    assert isinstance(df, pd.DataFrame)


# ----------------------------------------------------------------- describe
@pytest.mark.parametrize(
    "name,expected",
    [
        ("MAJBUYPT", "principal_purchase_place"),
        ("majbuypt", "principal_purchase_place"),
        ("principal_purchase_place", "principal_purchase_place"),
        ("SLAXIMP", "embarked_imputed"),
    ],
)
def test_lookup_by_name_or_spss_name(name, expected):
    assert lookup(name).name == expected


def test_lookup_prefers_the_voyage_field_unless_asked():
    assert lookup("NATINIMP").name == "flag_imputed"
    assert lookup("NATINIMP", dataset="estimates").name == "carrier"
    assert lookup("YEARAM").name == "year_arrived_imputed"
    assert lookup("route").name == "route"  # not route_documented, whose SPSS name is "route"
    with pytest.raises(KeyError, match="did you mean"):
        lookup("MAJBUYP")


def test_describe_a_place_code(v):
    d = v.describe("MAJBUYPT")
    assert d.field.name == "principal_purchase_place"
    cov = d.coverage.set_index("dataset")
    assert cov.loc["transatlantic", "rows"] == 300 and cov.loc["intraamerican", "rows"] == 300
    assert 0 < cov.loc["transatlantic", "with_value"] < 300
    assert {"code", "label", "rows"} <= set(d.values.columns)
    assert d.values.rows.is_monotonic_decreasing
    text = str(d)
    assert "MAJBUYPT" in text and "recorded" in text and "Principal port of slave purchase" in text


def test_describe_counts_match_the_data(v):
    d = v.describe("embarked_imputed")
    wide = v.table("voyages_wide").to_pandas()
    cov = d.coverage.set_index("dataset")
    for ds in ("transatlantic", "intraamerican"):
        assert (
            cov.loc[ds, "with_value"]
            == wide.loc[wide.dataset == ds, "embarked_imputed"].notna().sum()
        )
    assert d.values["total"].item() == wide.embarked_imputed.sum()
    assert "imputed" in str(d)


def test_describe_text_and_estimates_fields(v):
    assert "value" in v.describe("ship_name").values.columns
    est = v.describe("embarkation_region", dataset="estimates")
    assert est.coverage.dataset.tolist() == ["estimates"]
    assert "label" in est.values.columns


def test_describe_shows_derivation(v):
    assert "derived from year_arrived_imputed" in str(v.describe("YEAR10"))


# ------------------------------------------------------------ recorded only
def test_recorded_endpoints_ignore_imputed_places(v):
    """Voyage 509, S André Diligente: recorded "West Central Africa and St. Helena,
    port unspecified", imputed St. Paul de Loanda. Voyage 113, Tellus: no recorded
    principal place of purchase (Benguela is imputed)."""
    ends = v.endpoints(recorded_only=True).set_index("voyage_id")
    e = ends.loc[509]
    assert e.embarkation_place == 60799 and e.embarkation_provenance == "recorded"
    assert e.embarkation_region_name == "West Central Africa and St. Helena"
    assert pd.isna(ends.loc[113, "embarkation_place"]) and not ends.loc[113, "drawable"]
    assert ends.loc[113, "disembarkation_place_name"] == "Havana"
    assert ends.loc[91000, "embarkation_place"] == 60408  # recorded = imputed here
    assert set(ends.embarkation_provenance.dropna()) == {"recorded"}


def test_recorded_endpoints_schema_matches_the_registry(v):
    got = v.table("voyage_endpoints_recorded").to_arrow().schema
    assert got.equals(schema.arrow_schema("voyage_endpoints_recorded"), check_metadata=False)


def test_recorded_place_filter_uses_the_recorded_place(v):
    wide = v.table("voyages_wide").to_pandas()
    places = v.table("places").to_pandas().set_index("code")
    region = wide.principal_purchase_place.map(places.region_code)
    expected = set(wide.loc[region == 60400, "voyage_id"])
    got = set(
        v.query(recorded_only=True).embarked_from("Gold Coast").to_pandas(["voyage_id"]).voyage_id
    )
    assert got == expected and got


def test_recorded_years_are_the_recorded_dates(v):
    wide = v.table("voyages_wide").to_pandas()
    q = v.query(recorded_only=True)
    assert len(q.between(1750, 1800)) == wide.first_landing_year.between(1750, 1800).sum()
    assert len(q.between(1750, on="departed")) == (wide.departure_year >= 1750).sum()
    decades = q.by_decade("voyages")
    assert decades.voyages.sum() == 600
    assert (
        decades.loc[decades.decade.isna(), "voyages"].item() == wide.first_landing_year.isna().sum()
    )


def test_recorded_totals_are_named_recorded_fields(v):
    df = v.transatlantic.recorded_only().by_decade()
    assert list(df.columns) == [
        "decade",
        "voyages",
        "captives_on_board_leaving_africa",
        "captives_arrived_first_landing",
    ]
    assert set(df.attrs["provenance"].values()) == {"derived", "recorded"}
    s = v.transatlantic.recorded_only().summary()
    assert "embarked" not in s.columns and "voyages_with_captives_on_board_leaving_africa" in s


def test_recorded_flag_and_outcome(v):
    wide = v.table("voyages_wide").to_pandas()
    q = v.query(recorded_only=True)
    assert len(q.flag("Great Britain")) == (wide.flag == 7).sum()
    assert len(q.outcome(1)) == (wide.outcome == 1).sum()


@pytest.mark.parametrize(
    "call,message",
    [
        (lambda q: q.by_decade(["embarked"]), "imputed total"),
        (lambda q: q.by("flag_imputed"), "imputed"),
        (lambda q: q.by("decade"), "imputed"),
        (lambda q: q.to_pandas(["embarked_imputed"]), "imputed"),
        (lambda q: q.captive_outcome(1), "outcome"),
    ],
)
def test_recorded_only_refuses_imputed_data(v, call, message):
    with pytest.raises(ValueError, match=message):
        call(v.transatlantic.recorded_only())


def test_recorded_only_must_come_first(v):
    with pytest.raises(ValueError, match="before"):
        v.transatlantic.between(1700).recorded_only()


def test_recorded_rows_hold_no_imputed_column(v):
    df = v.transatlantic.recorded_only().to_pandas()
    for c in df.columns:
        assert column_provenance(c, recorded=True) != "imputed", c
    assert "ship_name" in df and "embarked_imputed" not in df and "decade" not in df
    assert "flag_imputed_name" not in df


def test_cli_recorded_only(built):
    r = CliRunner().invoke(
        app,
        [
            "query",
            "--built",
            str(built),
            "--recorded-only",
            "-d",
            "transatlantic",
            "--by",
            "decade",
        ],
    )
    assert r.exit_code == 0, r.output
    assert "captives_on_board_leaving_africa" in r.stdout.splitlines()[0]
    assert "CC BY-NC" not in r.stderr
    r = CliRunner().invoke(
        app, ["query", "--built", str(built), "--recorded-only", "-m", "embarked", "--by", "decade"]
    )
    assert r.exit_code == 2 and "imputed total" in r.stderr
