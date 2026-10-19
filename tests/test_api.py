"""The DuckDB query layer and the resolved map endpoints.

Offline tests build Parquet from the committed fixtures (300 real voyages per
voyage dataset) into a temporary directory. Full-data tests need
VOYAGES_DATA_DIR and a completed `voyages build`.
"""

import os
import warnings
from pathlib import Path

import pyarrow as pa
import pytest

from voyages import Voyages, schema
from voyages.api import DataNotBuilt, connect
from voyages.api.db import parquet_tables
from voyages.ingest import estimates, intraamerican, transatlantic

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def built(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("built")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        transatlantic.build(FIXTURES / "transatlantic_sample.sav", out)
        intraamerican.build(FIXTURES / "intraamerican_sample.sav", out)
        estimates.build(FIXTURES / "estimates_sample.sav", out)
    return out


@pytest.fixture(scope="module")
def v(built):
    with Voyages(built) as v:
        yield v


@pytest.fixture(scope="module")
def ends(v) -> dict[int, dict]:
    return {r["voyage_id"]: r for r in v.table("voyage_endpoints").to_arrow().to_pylist()}


# ------------------------------------------------------------- connection
def test_missing_build_says_what_to_do(tmp_path):
    with pytest.raises(DataNotBuilt, match="voyages build"):
        connect(tmp_path)


def test_connection_opens_on_first_use(built):
    v = Voyages(built)
    assert v._con is None
    v.tables()
    assert v._con is not None
    v.close()
    assert v._con is None


def test_every_table_reference_and_view_is_registered(v):
    names = set(v.tables())
    assert set(parquet_tables()) <= names
    assert {"places", "nations", "outcomes", "voyage_endpoints"} <= names


def test_both_voyage_datasets_in_one_view(v):
    counts = dict(v.sql("SELECT dataset, count(*) FROM voyages GROUP BY 1").relation.fetchall())
    assert counts == {"transatlantic": 300, "intraamerican": 300}


def test_reference_tables_are_typed(v):
    row = v.sql("SELECT code, region_code, map_lat FROM places WHERE code = 60605").relation
    assert row.types == ["INTEGER", "INTEGER", "DOUBLE"]


def test_result_formats(v):
    r = v.sql("SELECT voyage_id FROM voyages WHERE voyage_id = ?", params=[91000])
    assert r.to_pandas()["voyage_id"].tolist() == [91000]
    assert isinstance(r.to_arrow(), pa.Table)
    assert len(r) == 1
    pl = pytest.importorskip("polars")
    assert isinstance(r.to_polars(), pl.DataFrame)


def test_unknown_table(v):
    with pytest.raises(KeyError):
        v.table("slaves")


# --------------------------------------------------------------- endpoints
def test_endpoints_schema_matches_the_registry(v):
    got = v.table("voyage_endpoints").to_arrow().schema
    assert got.equals(schema.arrow_schema("voyage_endpoints"), check_metadata=False)


def test_one_endpoint_row_per_voyage(ends):
    assert len(ends) == 600


def test_recorded_endpoints_draw_at_the_place(ends):
    """Voyage 91000, Cerberus (1766): Anomabu -> Kingston, both recorded.

    Places checked on https://legacy.slavevoyages.org/voyage/91000/variables
    (2026-10-19; the site now spells 60408 "Anomabu").
    """
    e = ends[91000]
    assert (e["embarkation_place"], e["embarkation_place_name"]) == (60408, "Anomabu, Adja, Agga")
    assert e["embarkation_provenance"] == "recorded"
    assert (e["embarkation_region_name"], e["embarkation_broad_region_name"]) == (
        "Gold Coast",
        "Africa",
    )
    assert (e["disembarkation_place"], e["disembarkation_region_name"]) == (35114, "Jamaica")
    assert e["disembarkation_provenance"] == "recorded"
    assert e["embarkation_precision"] == e["disembarkation_precision"] == "place"
    assert (e["disembarkation_lat"], e["disembarkation_lon"]) == (18.0, -76.8)
    assert e["drawable"]


def test_imputed_place_wins_and_is_marked_imputed(ends, v):
    """Voyage 509, S André Diligente (1825): the record says only "West Central
    Africa and St. Helena, port unspecified"; the imputed principal place is
    St. Paul de Loanda. The endpoint follows the imputed place, as the site's
    maps do, and says so."""
    (recorded,) = v.sql(
        "SELECT principal_purchase_place_name FROM voyages_wide WHERE voyage_id = 509"
    ).relation.fetchone()
    assert recorded == "West Central Africa and St. Helena, port unspecified"
    e = ends[509]
    assert (e["embarkation_place"], e["embarkation_place_name"]) == (60734, "St. Paul de Loanda")
    assert e["embarkation_provenance"] == "imputed"
    assert e["embarkation_precision"] == "place"


def test_unspecified_port_draws_at_its_representative_port(ends):
    """Voyage 1, Pastora de Lima (1817): landed at "Bahia, port unspecified"."""
    e = ends[1]
    assert e["disembarkation_place_name"] == "Bahia, port unspecified"
    assert (e["disembarkation_precision"], e["disembarkation_map_code"]) == (
        "representative",
        50299,
    )


def test_place_without_a_point_draws_at_its_region_centre(ends, v):
    """Voyage 40223 (1729): embarked at Costa da Mina, which has no point of
    its own; it draws at the Bight of Benin's centre."""
    e = ends[40223]
    assert e["embarkation_place_name"] == "Costa da Mina"
    assert (e["embarkation_precision"], e["embarkation_map_code"]) == ("region", 60500)
    centre = v.sql("SELECT map_lat, map_lon FROM places WHERE code = 60500").relation.fetchone()
    assert (e["embarkation_lat"], e["embarkation_lon"]) == centre
    assert e["drawable"]


def test_catch_all_place_has_no_point(ends):
    """Voyage 937 (1828): "Africa, port unspecified" has nowhere to draw."""
    e = ends[937]
    assert e["embarkation_place"] is not None
    assert e["embarkation_lat"] is None and e["embarkation_precision"] is None
    assert e["disembarkation_precision"] == "representative"
    assert not e["drawable"]


def test_voyage_without_principal_places(ends):
    """Voyage 3695, Leopoldina (1848): neither endpoint recorded or imputed."""
    e = ends[3695]
    assert e["embarkation_place"] is None and e["disembarkation_place"] is None
    assert not e["drawable"]


def test_unknown_imputed_place_falls_back_to_the_recorded_one(ends, v):
    """Voyage 113, Tellus (1820). The imputed principal place of landing is code
    99801 "???" in region "Codes without labels", as the site also shows
    (https://legacy.slavevoyages.org/voyage/113/variables, 2026-10-19). The
    record names Havana as principal place of landing, so that is drawn."""
    imputed = v.sql(
        "SELECT code FROM voyage_places WHERE voyage_id = 113 "
        "AND role = 'principal_landing' AND level = 'place' AND provenance = 'imputed'"
    ).relation.fetchone()
    assert imputed == (99801,)
    e = ends[113]
    assert (e["disembarkation_place"], e["disembarkation_place_name"]) == (31312, "Havana")
    assert e["disembarkation_provenance"] == "recorded"
    assert (e["disembarkation_region_name"], e["disembarkation_broad_region_name"]) == (
        "Cuba",
        "Caribbean",
    )
    assert e["embarkation_place_name"] == "Benguela"
    assert e["drawable"]


def test_no_endpoint_lands_on_an_unknown_code(ends):
    for e in ends.values():
        assert e["embarkation_region"] != 99800 and e["disembarkation_region"] != 99800


def test_points_have_a_precision_and_a_code(ends):
    for e in ends.values():
        for side in ("embarkation", "disembarkation"):
            has_point = e[f"{side}_lat"] is not None
            assert has_point == (e[f"{side}_lon"] is not None)
            assert has_point == (e[f"{side}_precision"] is not None)
            assert has_point == (e[f"{side}_map_code"] is not None)
            assert (e[f"{side}_provenance"] is None) == (e[f"{side}_place"] is None)


def test_endpoints_filters(v):
    ia = v.endpoints(dataset="intraamerican")
    assert len(ia) == 300 and set(ia["dataset"]) == {"intraamerican"}
    drawable = v.endpoints(drawable_only=True)
    assert drawable["drawable"].all()
    with pytest.raises(ValueError):
        v.endpoints(dataset="estimates")


def test_coverage_counts_every_voyage(v):
    cov = v.endpoint_coverage()
    for (_, endpoint), g in cov.groupby(["dataset", "endpoint"]):
        assert g["voyages"].sum() == 300, endpoint
    route = cov[(cov.endpoint == "route") & (cov.status == "drawable")]
    assert route["voyages"].sum() == len(v.endpoints(drawable_only=True))


# ---------------------------------------------------------------- full data
needs_full_data = pytest.mark.skipif(
    not os.environ.get("VOYAGES_DATA_DIR"), reason="needs VOYAGES_DATA_DIR"
)


@pytest.mark.fulldata
@needs_full_data
def test_full_coverage():
    """Coverage recorded in docs/schema.md (2026-10-19): 67% TA, 83% IA drawable."""
    with Voyages() as v:
        cov = v.endpoint_coverage()
        assert len(v.endpoints()) == 36_108 + 11_521
    share = cov[(cov.endpoint == "route") & (cov.status == "drawable")].set_index("dataset")
    assert share.loc["transatlantic", "share"] >= 0.66
    assert share.loc["intraamerican", "share"] >= 0.82
