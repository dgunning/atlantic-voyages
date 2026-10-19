"""Estimates ingest: one table, conformant to the registry, totals checked against the site.

Offline tests use tests/fixtures/estimates_sample.sav (300 rows of the 2010
Estimates, sampled by decade). Full-data tests need VOYAGES_DATA_DIR.
"""

import os
from pathlib import Path

import pyarrow.compute as pc
import pytest

from voyages import schema
from voyages.ingest import estimates

FIXTURE = Path(__file__).parent / "fixtures" / "estimates_sample.sav"

# Embarked by national carrier, 1501-1866, from the default table on
# https://legacy.slavevoyages.org/assessment/estimates (checked 2026-10-19).
SITE_EMBARKED = {
    1: 1_061_524,  # Spain / Uruguay
    2: 5_848_266,  # Portugal / Brazil
    3: 3_259_441,  # Great Britain
    4: 554_336,  # Netherlands
    5: 305_326,  # U.S.A.
    6: 1_381_404,  # France
    7: 111_040,  # Denmark / Baltic
}
SITE_EMBARKED_TOTAL = 12_521_337


def test_fixture_table_matches_the_registry_schema():
    t = estimates.build_table(FIXTURE)
    assert t.schema.equals(schema.arrow_schema("estimates"), check_metadata=False)
    assert t.num_rows == 300
    assert t.column("row").to_pylist() == list(range(1, 301))


def test_codes_use_the_estimates_reference_tables():
    import csv

    from voyages.ingest import reference

    t = estimates.build_table(FIXTURE)
    with (reference.REFERENCE_DIR / "estimates_carriers.csv").open(encoding="utf-8") as fh:
        carriers = {int(r["code"]) for r in csv.DictReader(fh)}
    assert set(t.column("carrier").drop_null().to_pylist()) <= carriers


needs_full_data = pytest.mark.skipif(
    not os.environ.get("VOYAGES_DATA_DIR"), reason="needs VOYAGES_DATA_DIR"
)


@pytest.mark.fulldata
@needs_full_data
def test_embarked_totals_match_the_site():
    """totexports is closest to the site; the .sav rounds each row to whole people.

    By carrier the build is within 14 people of the site (Netherlands exact),
    and the grand total within 15 (12,521,352 vs 12,521,337).
    """
    t = estimates.build_table()
    assert t.num_rows == 11709
    by_carrier = t.group_by("carrier").aggregate([("embarked_estimated_total", "sum")])
    ours = dict(
        zip(
            by_carrier["carrier"].to_pylist(),
            by_carrier["embarked_estimated_total_sum"].to_pylist(),
            strict=True,
        )
    )
    for carrier, site in SITE_EMBARKED.items():
        assert abs(ours[carrier] - site) <= 15, (carrier, ours[carrier], site)
    total = pc.sum(t.column("embarked_estimated_total")).as_py()
    assert abs(total - SITE_EMBARKED_TOTAL) <= 20
    assert ours[4] == SITE_EMBARKED[4]  # Netherlands: exact
