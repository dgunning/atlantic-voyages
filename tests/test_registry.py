"""Checks on the field registry (src/voyages/schema/fields.yaml).

Offline checks run on every test run. The full-data check that every
.sav column is either registered or explicitly dropped needs the raw
files and is marked ``fulldata``.
"""

import os
import re
from pathlib import Path

import pytest

from voyages import schema

REG = schema.load()
VOYAGE_TABLES = {t for t in REG.tables if t not in ("estimates", "voyages_wide")}


def test_registry_loads_every_field():
    # 278 voyage fields + 36 Estimates fields at bootstrap (2026-10-19)
    assert len(REG) >= 314


def test_names_are_unique_snake_case():
    names = [f.name for f in REG.fields if f.table != "estimates"]
    assert len(names) == len(set(names))
    est = [f.name for f in REG.fields if f.table == "estimates"]
    assert len(est) == len(set(est))
    for n in names + est:
        assert re.fullmatch(r"[a-z][a-z0-9_]*", n), n


def test_provenance_is_always_set_and_valid():
    for f in REG.fields:
        assert f.provenance in schema.PROVENANCE, f.name
        assert f.provenance_evidence, f.name


def test_imputed_voyage_fields_say_so_in_their_name():
    for f in REG.fields:
        if f.table == "estimates":
            continue  # the whole Estimates table is CC BY-NC; names stay short
        assert (f.provenance == "imputed") == f.name.endswith("_imputed"), f.name


def test_datasets_are_known():
    for f in REG.fields:
        assert f.datasets and set(f.datasets) <= set(schema.DATASETS), f.name


def test_every_field_lands_in_a_defined_table():
    for f in REG.fields:
        assert f.table in REG.tables, (f.name, f.table)


def test_long_fields_carry_the_keys_their_table_needs():
    needs = {
        "voyage_places": {"role", "seq", "level"},
        "voyage_dates": {"event", "part"},
        "voyage_people_counts": {"stage", "category"},
        "voyage_people_shares": {"stage", "category"},
        "voyage_crew": {"measure", "stage"},
        "voyage_sources": {"seq"},
        "voyage_enslavers": {"role", "seq"},
    }
    for f in REG.fields:
        if f.table in needs:
            assert f.long and needs[f.table] <= set(f.long), f.name
        else:
            assert f.long is None, f.name


def test_long_keys_are_unique_within_a_table():
    seen: dict[tuple, str] = {}
    for f in REG.fields:
        if not f.long:
            continue
        key = (f.table, f.provenance, *sorted(f.long.items()))
        assert key not in seen, (f.name, seen.get(key))
        seen[key] = f.name


def test_place_fields_use_the_places_reference():
    for f in REG.for_table("voyage_places"):
        assert f.kind == "place_code" and f.reference == "places", f.name


def test_ratios_are_floats():
    for f in REG.fields:
        if f.kind == "ratio":
            assert f.dtype == "float64", f.name


def test_labels_follow_project_language():
    # Original wording is kept verbatim in source_label; our labels do not use
    # "slave(s)" as a noun or "cargo" for people.
    for f in REG.fields:
        assert not re.search(r"\bslaves?\b", f.label, re.I), (f.name, f.label)
    assert REG["other_cargo"].label.startswith("Other cargo (goods)")


def test_lookup_by_spss_name():
    # MAJBUYPT, principal port of purchase, is the field the literature cites most.
    f = REG.by_spss("majbuypt")
    assert f.name == "principal_purchase_place"
    assert f.provenance == "recorded"
    assert REG.by_spss("SLAXIMP").name == "embarked_imputed"
    # Intra-American stores date composites under different SPSS names
    assert REG.by_spss("date_land1", dataset="intraamerican").name == "first_landing_date"


def test_mortality_rate_is_imputed():
    """VYMRTRAT = VYMRTIMP / TSLMTIMP, both imputed (checked on 6,477 voyages)."""
    f = REG.by_spss("VYMRTRAT")
    assert f.provenance == "imputed" and f.name == "mortality_rate_imputed"


def test_dropped_columns_have_reasons():
    assert {d["spss_name"] for d in REG.dropped} == {"FILTER_$", "INTRAAMER"}
    assert all(d["reason"] for d in REG.dropped)


def _raw_dir() -> Path | None:
    d = os.environ.get("VOYAGES_DATA_DIR")
    return Path(d) / "raw" if d else None


@pytest.mark.fulldata
@pytest.mark.skipif(not os.environ.get("VOYAGES_DATA_DIR"), reason="needs VOYAGES_DATA_DIR")
@pytest.mark.parametrize(
    "dataset,file",
    [
        ("transatlantic", "tastdb-exp-2020.sav"),
        ("intraamerican", "I-Am1.0.sav"),
        ("estimates", "2010-estimates-SPSS.sav"),
    ],
)
def test_every_sav_column_is_registered_or_dropped(dataset, file):
    pyreadstat = pytest.importorskip("pyreadstat")
    _, meta = pyreadstat.read_sav(_raw_dir() / file, metadataonly=True)
    dropped = {d["spss_name"].upper() for d in REG.dropped}
    registered = {f.spss_name_in(dataset).upper() for f in REG.for_dataset(dataset)}
    missing = {c for c in meta.column_names if c.upper() not in registered | dropped}
    assert not missing
