"""Trans-Atlantic ingest: registry-conformant tables, checked against the site.

Offline tests build from tests/fixtures/transatlantic_sample.sav (300 real
voyages, made by tools/make_fixtures.py). Full-data tests need
VOYAGES_DATA_DIR and also check that the fixture build equals the same
voyages in the full build.
"""

import datetime as dt
import os
from pathlib import Path

import pyarrow as pa
import pytest

from voyages import schema
from voyages.ingest import reference, transatlantic, voyages

FIXTURE = Path(__file__).parent / "fixtures" / "transatlantic_sample.sav"

# Checked against https://legacy.slavevoyages.org/voyage/<id>/variables on
# 2026-10-19: vessel name, first captain, year arrived (imputed), total
# embarked (imputed), total disembarked (imputed).
# Voyages 17223 and 11408 were also checked and differ: the site shows newer
# figures than the 2020 .sav (see docs/DATA.md), so they are not used here.
SITE_CHECKED = [
    (1, "Pastora de Lima", "Dias, Manoel José", 1817, 404, 290),
    (113, "Tellus", "Botet, Juan", 1820, 196, 177),
    (3844, "Astro", None, 1850, 603, 500),
    (5096, "Peggy", "Mayberry", 1799, 150, 123),
    (7557, "Pennel", "Porter", 1809, 18, 18),
    (8110, "Ana e Lisboa", "Mota, Paulino Pinto da", 1798, 714, 660),
    (9727, "William and Jane", "Harding, William", 1702, 247, 211),
    (10390, "Adriana Petronella", "Drijber, Jacobus", 1759, 360, 336),
    (11502, "Solitaire", "Lessier, Pierre", 1782, 442, 402),
    (91000, "Cerberus", "Kendall, John", 1766, 350, 270),
]


@pytest.fixture(scope="module")
def tables() -> dict[str, pa.Table]:
    return transatlantic.build_tables(FIXTURE)


def rows(tbl: pa.Table, **where) -> list[dict]:
    return [r for r in tbl.to_pylist() if all(r[k] == v for k, v in where.items())]


def test_every_table_matches_the_registry_schema(tables):
    assert set(tables) == set(voyages.VOYAGE_TABLES)
    for name, tbl in tables.items():
        assert tbl.schema.equals(schema.arrow_schema(name), check_metadata=False), name


def test_one_row_per_voyage(tables):
    assert tables["voyages"].num_rows == 300
    assert tables["voyages_wide"].num_rows == 300
    ids = tables["voyages"].column("voyage_id").to_pylist()
    assert len(set(ids)) == 300


@pytest.mark.parametrize("vid,ship,captain,year,embarked,disembarked", SITE_CHECKED)
def test_values_match_the_site(tables, vid, ship, captain, year, embarked, disembarked):
    (w,) = rows(tables["voyages_wide"], voyage_id=vid)
    assert w["ship_name"] == ship
    assert w["year_arrived_imputed"] == year
    assert w["embarked_imputed"] == embarked
    assert w["disembarked_imputed"] == disembarked
    caps = rows(tables["voyage_enslavers"], voyage_id=vid, role="captain", seq=1)
    assert (caps[0]["name"] if caps else None) == captain


def test_cerberus_in_detail(tables):
    """Voyage 91000, Cerberus (1766), Liverpool -> Anomabu -> Kingston.

    Every value checked on https://legacy.slavevoyages.org/voyage/91000/variables
    (2026-10-19). The site shows 365 for standardized tonnage (rounded) and the
    current place name "Anomabu"; the 2020 .sav names code 60408 "Anomabu, Adja, Agga".
    """
    (w,) = rows(tables["voyages_wide"], voyage_id=91000)
    assert (w["flag_name"], w["flag_imputed_name"]) == ("Great Britain", "Great Britain")
    assert (w["year_constructed"], w["year_registered"], w["rig_name"]) == (1759, 1762, "Ship")
    assert (w["tonnage"], round(w["tonnage_standardized_imputed"]), w["guns"]) == (250, 365, 4)
    assert w["outcome_name"] == "Voyage completed as intended"
    assert w["principal_landing_place_imputed_name"] == "Kingston"
    assert w["principal_purchase_place_imputed"] == 60408
    assert (w["captives_intended_first_port"], w["captives_on_board_leaving_africa"]) == (400, 350)
    assert w["captives_arrived_first_landing"] == 270
    assert (w["died_middle_passage_imputed"], w["mortality_rate_imputed"]) == (80, 0.23)
    assert (w["middle_passage_days_imputed"], w["days_to_first_landing_imputed"]) == (79, 437)

    dates = {r["event"]: r["date"] for r in rows(tables["voyage_dates"], voyage_id=91000)}
    assert dates == {
        "departure": dt.date(1765, 4, 6),
        "left_africa": dt.date(1766, 3, 30),
        "first_landing": dt.date(1766, 6, 17),
        "left_last_landing": dt.date(1766, 9, 30),
        "completed": dt.date(1766, 12, 1),
    }
    owners = sorted(
        rows(tables["voyage_enslavers"], voyage_id=91000, role="owner"), key=lambda r: r["seq"]
    )
    assert [o["name"] for o in owners] == [
        "Gregson, William", "Blundel, Jonathan", "Bridge, John", "Kendall, Thomas", "Pole, Charles",
    ]  # fmt: skip
    crew = {r["stage"]: r["count"] for r in rows(tables["voyage_crew"], voyage_id=91000)}
    assert crew["outset"] == 30 and crew["first_landing"] == 30


def test_long_tables_hold_every_non_null_value(tables):
    """No value is lost or invented when wide fields are melted into long tables."""
    wide = tables["voyages_wide"]
    reg = schema.load()
    for t in voyages.LONG_TABLES:
        fields = [f for f in reg.for_table(t) if "transatlantic" in f.datasets]
        expected = sum(wide.num_rows - wide.column(f.name).null_count for f in fields)
        assert tables[t].num_rows == expected, t


def test_long_rows_carry_registry_provenance(tables):
    reg = schema.load()
    for t in ("voyage_places", "voyage_people_counts", "voyage_people_shares"):
        for r in tables[t].to_pylist():
            assert r["provenance"] == reg.by_spss(r["spss_name"], "transatlantic").provenance


def test_every_place_code_is_in_the_reference_table(tables):
    import csv

    with (reference.REFERENCE_DIR / "places.csv").open(encoding="utf-8") as fh:
        known = {int(r["code"]) for r in csv.DictReader(fh)}
    used = set(tables["voyage_places"].column("code").to_pylist())
    assert used <= known


def test_strings_are_trimmed_and_empty_is_null(tables):
    for t, col in (("voyage_enslavers", "name"), ("voyage_sources", "reference")):
        for v in tables[t].column(col).to_pylist():
            assert v and v == v.strip()


def test_dates_are_built_only_from_valid_parts():
    import pandas as pd

    typed = pd.DataFrame(
        {
            "voyage_id": pd.array([1, 2, 3], dtype="Int32"),
            "departure_day": pd.array([6, 99, None], dtype="Int8"),
            "departure_month": pd.array([4, 3, 5], dtype="Int8"),
            "departure_year": pd.array([1765, 1702, 1800], dtype="Int16"),
            "departure_date": [None, None, None],
        }
    )
    fields = [f for f in schema.load().for_table("voyage_dates") if f.long["event"] == "departure"]
    out = voyages._dates(typed, "transatlantic", fields).set_index("voyage_id")
    assert out.loc[1, "date"] == dt.date(1765, 4, 6)  # built from parts
    assert out.loc[2, "date"] is None and out.loc[2, "day"] == 99  # day 99 kept, no date
    assert out.loc[3, "date"] is None and out.loc[3, "month"] == 5  # partial date


# ------------------------------------------------------------------ full data
needs_full_data = pytest.mark.skipif(
    not os.environ.get("VOYAGES_DATA_DIR"), reason="needs VOYAGES_DATA_DIR"
)


@pytest.fixture(scope="module")
def full_tables() -> dict[str, pa.Table]:
    return transatlantic.build_tables()


@pytest.mark.fulldata
@needs_full_data
def test_full_build_counts(full_tables):
    # 36,108 voyages in tastdb-exp-2020.sav (and in the Dec 2019 CSV).
    assert full_tables["voyages"].num_rows == 36108
    for name, tbl in full_tables.items():
        assert tbl.schema.equals(schema.arrow_schema(name), check_metadata=False), name


@pytest.mark.fulldata
@needs_full_data
def test_fixture_build_equals_full_build_for_the_same_voyages(tables, full_tables):
    import pyarrow.compute as pc

    ids = tables["voyages"].column("voyage_id")
    for name, small in tables.items():
        big = full_tables[name].filter(pc.is_in(full_tables[name].column("voyage_id"), ids))
        key = schema.load().tables[name].get("key") or ["voyage_id"]
        assert small.sort_by([(k, "ascending") for k in key]).equals(
            big.sort_by([(k, "ascending") for k in key])
        ), name
