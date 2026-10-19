"""Intra-American ingest: same tables as Trans-Atlantic, checked against the site.

Offline tests build from tests/fixtures/intraamerican_sample.sav (300 real
voyages). Full-data tests need VOYAGES_DATA_DIR.
"""

import os
from pathlib import Path

import pyarrow as pa
import pytest

from voyages import schema
from voyages.ingest import intraamerican, transatlantic, voyages

FIXTURE = Path(__file__).parent / "fixtures" / "intraamerican_sample.sav"

# Checked against https://legacy.slavevoyages.org/voyage/<id>/variables on
# 2026-10-19: vessel name, first captain, year arrived (imputed), total
# embarked (imputed), total disembarked (imputed). All 14 voyages checked
# agree with I-Am1.0.sav (12 here, plus 105238 and 105990 below).
SITE_CHECKED = [
    (100008, "Ranger", "Smith, Dan.", 1737, 9, 8),
    (100030, "Patty", "Gorham, Isaac", 1783, 1, 1),
    (100037, "William and Mary", "Nicholson, George", 1761, 4, 3),
    (101481, "Endeavour", "Bayley, George", 1814, 30, 29),
    (101547, "Enterprize", "Yallowley, John [Cellen?]", 1807, 87, 84),
    (101747, "Tourtelle", "Devaux, Jean", 1789, 3, 3),
    (101756, "Nouvelle Orleans", "Pinett, Francis", 1789, 135, 129),
    (103577, "Esperanza", "Aballo (a) Abell, Joseph", 1796, 19, 18),
    (103706, "Hermanos", "Lopez, John", 1809, 4, 4),
    (105692, "Francesa", "Galason", 1802, 48, 47),
    (108699, "Goleta Inglesa", None, 1738, 10, 9),
    (112742, "Nuestra Señora de la Salvación", "Rodriguez, Thomas", 1605, 283, 278),
]


@pytest.fixture(scope="module")
def tables() -> dict[str, pa.Table]:
    with pytest.warns(UserWarning, match="set to null"):
        return intraamerican.build_tables(FIXTURE)


def rows(tbl: pa.Table, **where) -> list[dict]:
    return [r for r in tbl.to_pylist() if all(r[k] == v for k, v in where.items())]


def test_every_table_matches_the_registry_schema(tables):
    assert set(tables) == set(voyages.VOYAGE_TABLES)
    for name, tbl in tables.items():
        assert tbl.schema.equals(schema.arrow_schema(name), check_metadata=False), name
    assert set(tables["voyages"].column("dataset").to_pylist()) == {"intraamerican"}


def test_one_row_per_voyage(tables):
    ids = tables["voyages"].column("voyage_id").to_pylist()
    assert len(ids) == len(set(ids)) == 300


@pytest.mark.parametrize("vid,ship,captain,year,embarked,disembarked", SITE_CHECKED)
def test_values_match_the_site(tables, vid, ship, captain, year, embarked, disembarked):
    (w,) = rows(tables["voyages_wide"], voyage_id=vid)
    assert w["ship_name"] == ship
    assert w["year_arrived_imputed"] == year
    assert w["embarked_imputed"] == embarked
    assert w["disembarked_imputed"] == disembarked
    caps = rows(tables["voyage_enslavers"], voyage_id=vid, role="captain", seq=1)
    assert (caps[0]["name"] if caps else None) == captain


def test_known_bad_counts_are_null_not_rounded(tables):
    """Voyages 105238 and 105990 record fractions of people (0.2 boys, 0.5 infants).

    The site shows shares for both that cannot add up (105990: men 80%, male
    100%, boys 11.1%; https://legacy.slavevoyages.org/voyage/105990/variables,
    2026-10-19). The listed counts become null; everything else is kept.
    """
    (a,) = rows(tables["voyages_wide"], voyage_id=105238)
    assert a["boys_landed_first_place"] is None and a["infants_landed_first_place"] is None
    assert a["girls_landed_first_place"] == 3  # whole numbers are untouched
    assert a["disembarked_imputed"] == 10
    (b,) = rows(tables["voyages_wide"], voyage_id=105990)
    assert b["girls_landed_first_place"] is None
    assert b["men_landed_first_place"] == 4


def test_links_to_transatlantic_voyages(tables):
    """voyageID2 is text in the source; 111086 lists two voyages ("10275, 10157")."""
    links = {(r["voyage_id"], r["linked_voyage_id"]) for r in tables["voyage_links"].to_pylist()}
    assert {(111086, 10275), (111086, 10157), (100034, 11850)} <= links
    (w,) = rows(tables["voyages_wide"], voyage_id=111086)
    assert w["transatlantic_voyage_ids"] == "10275;10157"
    for r in tables["voyage_links"].to_pylist():
        assert r["relation"] == "transatlantic_voyage" and r["linked_dataset"] == "transatlantic"


def test_long_tables_hold_every_non_null_value(tables):
    wide = tables["voyages_wide"]
    reg = schema.load()
    for t in voyages.LONG_TABLES:
        if t == "voyage_links":
            continue  # one field can hold several links; checked above
        fields = [f for f in reg.for_table(t) if "intraamerican" in f.datasets]
        expected = sum(wide.num_rows - wide.column(f.name).null_count for f in fields)
        assert tables[t].num_rows == expected, t


def test_transatlantic_only_fields_are_empty(tables):
    wide = tables["voyages_wide"]
    reg = schema.load()
    for f in reg.fields:
        if f.datasets == ("transatlantic",):
            assert wide.column(f.name).null_count == wide.num_rows, f.name


# ------------------------------------------------------------------ full data
needs_full_data = pytest.mark.skipif(
    not os.environ.get("VOYAGES_DATA_DIR"), reason="needs VOYAGES_DATA_DIR"
)


@pytest.fixture(scope="module")
def full_tables() -> dict[str, pa.Table]:
    with pytest.warns(UserWarning, match="set to null"):
        return intraamerican.build_tables()


@pytest.mark.fulldata
@needs_full_data
def test_full_build_counts(full_tables):
    assert full_tables["voyages"].num_rows == 11521
    assert full_tables["voyage_links"].num_rows == 67  # 66 voyages, one with two links


@pytest.mark.fulldata
@needs_full_data
def test_fixture_build_equals_full_build_for_the_same_voyages(tables, full_tables):
    import pyarrow.compute as pc

    ids = tables["voyages"].column("voyage_id")
    for name, small in tables.items():
        big = full_tables[name].filter(pc.is_in(full_tables[name].column("voyage_id"), ids))
        key = schema.load().tables[name].get("key") or ["voyage_id"]
        order = [(k, "ascending") for k in key]
        assert small.sort_by(order).equals(big.sort_by(order)), name


@pytest.mark.fulldata
@needs_full_data
def test_voyage_ids_are_unique_across_datasets(full_tables):
    ta = transatlantic.build_tables()
    ta_ids = set(ta["voyages"].column("voyage_id").to_pylist())
    ia_ids = set(full_tables["voyages"].column("voyage_id").to_pylist())
    assert not ta_ids & ia_ids
    linked = set(full_tables["voyage_links"].column("linked_voyage_id").to_pylist())
    # Two linked voyages are not in the 2020 Trans-Atlantic file.
    assert linked - ta_ids == {11850, 96007}
