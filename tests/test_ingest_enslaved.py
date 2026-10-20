"""Enslaved.org ingest (supplementary source): tables, links and licences.

Offline tests use tests/fixtures/enslaved_sample.json.gz: the first 60 people of
the "Fugitives from Slavery in Jamaica" dataset (FSJ, CC BY 4.0) with every
record they refer to, written by ``tools/make_fixtures.py enslaved``.

The named person is Abraham (Enslaved.org item Q1125779, record FSJ-R-PER-00005),
an Igbo man aged 50 advertised as a runaway in the Cornwall Chronicle (Montego
Bay) in 1785. Values checked against the dump (2026-10-20); the site renders
person pages in the browser, so they could not be fetched for checking.
Full-data totals are the counts on https://enslaved.org (checked 2026-10-20).
"""

import os
from pathlib import Path

import pytest

from voyages import schema
from voyages.ingest import enslaved

FIXTURE = Path(__file__).parent / "fixtures" / "enslaved_sample.json.gz"
ABRAHAM = 1125779
RAN_AWAY, ADVERTISED = 1127346, 1127345
CHAMBERS, CORNWALL_CHRONICLE = 1124889, 1124885


@pytest.fixture(scope="module")
def tables():
    return {t: tbl.to_pandas() for t, tbl in enslaved.build_tables(FIXTURE).items()}


def test_every_table_matches_the_registry_schema():
    for name, tbl in enslaved.build_tables(FIXTURE).items():
        assert tbl.schema.equals(schema.arrow_schema(name), check_metadata=False), name
        assert schema.load().tables[name].get("optional"), name


def test_fixture_people():
    people = enslaved.build_tables(FIXTURE)["enslaved_people"].to_pandas()
    fsj = people[people.person_record_id.str.startswith("FSJ-R-PER-", na=False)]
    assert len(fsj) >= 60


def test_a_named_person(tables):
    p = tables["enslaved_people"].set_index("person_id").loc[ABRAHAM]
    assert (p.person_record_id, p.person_name, p.sex, p.age) == (
        "FSJ-R-PER-00005",
        "Abraham",
        "Male",
        "Age 50",
    )
    assert (p.ethnonym, p.ethnonym_place_of_origin) == ("Igbo", "Bight of Biafra")
    assert p.person_statuses == "Enslaved Person; Liminal Status Person"
    assert "Obeah-Man" in p.person_description


def test_roles_link_people_to_events(tables):
    roles = tables["enslaved_roles"]
    mine = roles[roles.person_id == ABRAHAM].set_index("event_id").participant_role
    assert mine.to_dict() == {ADVERTISED: "Mentioned Person", RAN_AWAY: "Runaway"}
    events = tables["enslaved_events"].set_index("event_id")
    e = events.loc[RAN_AWAY]
    assert (e.event_type, e.event_date, e.event_year) == ("Disappearance", "1785", 1785)
    assert events.loc[ADVERTISED].event_type == "Advertisement"


def test_event_places_and_place_hierarchy(tables):
    ep = tables["enslaved_event_places"]
    place = ep[ep.event_id == RAN_AWAY].place_id.tolist()
    places = tables["enslaved_places"].set_index("place_id")
    assert [places.loc[p].place_label for p in place] == ["Jamaica"]


def test_every_record_cites_sources_with_a_licence(tables):
    rs = tables["enslaved_record_sources"]
    assert set(rs[rs.record_id == ABRAHAM].source_id) == {CHAMBERS, CORNWALL_CHRONICLE}
    sources = tables["enslaved_sources"].set_index("source_id")
    assert sources.loc[CHAMBERS].licence == "CC BY 4.0"
    # Every person in the fixture has at least one source, and every source a licence.
    assert set(tables["enslaved_people"].person_id) <= set(rs.record_id)
    assert sources.licence.notna().all()


def test_projects_carry_attribution(tables):
    sources = tables["enslaved_sources"].set_index("source_id")
    projects = tables["enslaved_projects"].set_index("project_id")
    fsj = projects.loc[sources.loc[CHAMBERS].project_id]
    assert (fsj.project_code, fsj.project_name) == ("FSJ", "Fugitives from Slavery in Jamaica")
    assert fsj.data_article_url == "https://doi.org/10.25971/a7na-ky57"
    assert (fsj.start_year, fsj.end_year) == (1718, 1795)


@pytest.mark.parametrize(
    "value,expected",
    [
        ({"time": "+1785-00-00T00:00:00Z", "precision": 9}, ("1785", 1785)),
        ({"time": "+1785-03-00T00:00:00Z", "precision": 10}, ("1785-03", 1785)),
        ({"time": "+1785-03-04T00:00:00Z", "precision": 11}, ("1785-03-04", 1785)),
        (None, (None, None)),
    ],
)
def test_format_date(value, expected):
    assert enslaved.format_date(value) == expected


def test_class_ids_take_every_class_with_a_table_label():
    # Two classes are called "Place" in the dump; both are places. Labels of
    # items that are never used as a class do not count.
    labels = {1: "Place", 2: "Place", 3: "Person", 4: "Event"}
    classes = {10: (1,), 11: (1,), 12: (2,), 13: (3, 2)}
    assert enslaved.class_ids(labels, classes) == {1: "Place", 2: "Place", 3: "Person"}


def test_queries_work_without_the_supplementary_tables(tmp_path):
    # The enslaved_* tables are optional: a build without them still opens.
    import warnings

    from voyages import Voyages
    from voyages.ingest import estimates, intraamerican, transatlantic

    fx = FIXTURE.parent
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        transatlantic.build(fx / "transatlantic_sample.sav", tmp_path)
        intraamerican.build(fx / "intraamerican_sample.sav", tmp_path)
        estimates.build(fx / "estimates_sample.sav", tmp_path)
    with Voyages(tmp_path) as v:
        assert v.transatlantic.count() > 0
        assert not any(t.startswith("enslaved_") for t in v.tables())


def test_tables_are_queryable(v):
    df = v.sql(
        "SELECT p.person_name, s.licence FROM enslaved_people p "
        "JOIN enslaved_record_sources rs ON rs.record_id = p.person_id "
        "JOIN enslaved_sources s USING (source_id) WHERE p.person_id = ?",
        [ABRAHAM],
    ).to_pandas()
    assert set(df.licence) == {"CC BY 4.0"} and set(df.person_name) == {"Abraham"}
    assert v.describe("ethnonym").coverage.dataset.tolist() == ["enslaved"]


needs_full_data = pytest.mark.skipif(
    not os.environ.get("VOYAGES_DATA_DIR"), reason="needs VOYAGES_DATA_DIR"
)


@pytest.mark.fulldata
@needs_full_data
def test_totals_match_the_site():
    """People, events, places and sources as counted on https://enslaved.org (2026-10-20)."""
    from voyages import Voyages

    with Voyages() as v:
        counts = {
            t: v.sql(f"SELECT count(*) AS n FROM {t}").to_pandas().n[0]
            for t in ("enslaved_people", "enslaved_events", "enslaved_places", "enslaved_sources")
        }
    assert counts == {
        "enslaved_people": 731_500,
        "enslaved_events": 474_012,
        "enslaved_places": 10_381,
        "enslaved_sources": 3_940,
    }


@pytest.mark.fulldata
@needs_full_data
def test_jamaica_runaways_by_newspaper():
    """The FSJ runaways (782) by the newspaper that advertised them."""
    from voyages import Voyages

    with Voyages() as v:
        df = v.sql(
            """
            SELECT s.source_title AS paper, count(DISTINCT p.person_id) AS people
            FROM enslaved_people p
            JOIN enslaved_record_sources rs ON rs.record_id = p.person_id
            JOIN enslaved_sources s USING (source_id)
            JOIN enslaved_projects pr USING (project_id)
            WHERE pr.project_code = 'FSJ' AND p.person_statuses LIKE '%Liminal Status Person%'
              AND s.source_title NOT LIKE 'Chambers%'
            GROUP BY 1
            """
        ).to_pandas()
    assert dict(zip(df.paper, df.people, strict=True)) == {
        "Cornwall Chronicle": 452,
        "Jamaica Mercury": 142,
        "Royal Gazette": 112,
        "Weekly Jamaica Courant": 76,
    }
