"""`voyages query`: the fluent API from the command line, on the fixture build."""

import io
import json

import pandas as pd
import pyarrow.parquet as pq
import pytest
from typer.testing import CliRunner

from voyages import citation
from voyages.cli import app

runner = CliRunner()


@pytest.fixture
def run(built):
    def _run(*args):
        return runner.invoke(app, ["query", "--built", str(built), *args])

    return _run


def csv(result) -> pd.DataFrame:
    assert result.exit_code == 0, result.output
    return pd.read_csv(io.StringIO(result.stdout))


def test_by_decade_matches_the_api(run, v):
    r = run("-d", "transatlantic", "-e", "Gold Coast", "--from", "1700", "--to", "1800",
            "--by", "decade")  # fmt: skip
    got = csv(r)
    expected = v.transatlantic.embarked_from("Gold Coast").between(1700, 1800).by_decade()
    assert got.to_dict("list") == expected.astype(object).to_dict("list")


def test_citation_and_licence_go_to_stderr(run):
    r = run("-d", "transatlantic", "--by", "summary")
    assert citation() in r.stderr and "CC BY-NC" in r.stderr
    assert citation() not in r.stdout
    assert list(csv(r).columns)[:2] == ["dataset", "voyages"]


def test_rows_with_columns_and_where(run):
    r = run("-c", "voyage_id,ship_name", "--where", "ship_name = 'Cerberus'")
    assert csv(r).to_dict("records") == [{"voyage_id": 91000, "ship_name": "Cerberus"}]
    # Recorded columns only: no licence note.
    assert "CC BY-NC" not in r.stderr


def test_repeated_places_combine_with_or(run, v):
    got = csv(run("-l", "Jamaica", "-l", "Brazil", "-c", "voyage_id"))
    expected = v.query().disembarked_in("Jamaica", "Brazil").to_pandas(["voyage_id"])
    assert set(got.voyage_id) == set(expected.voyage_id)


def test_region_grouping_and_measures(run):
    got = csv(run("--by", "embarkation_broad_region", "-m", "voyages", "-m", "embarked"))
    assert list(got.columns) == [
        "embarkation_broad_region",
        "embarkation_broad_region_name",
        "voyages",
        "embarked",
    ]
    assert got.voyages.sum() == 600


def test_parquet_output_carries_citation_and_provenance(run, tmp_path):
    out = tmp_path / "jamaica.parquet"
    r = run("-l", "Jamaica", "--by", "endpoints", "--drawable-only", "-o", str(out))
    assert r.exit_code == 0, r.output
    t = pq.read_table(out)
    assert t.num_rows > 0 and all(t.column("drawable").to_pylist())
    meta = t.schema.metadata
    assert meta[b"voyages.citation"].decode() == citation()
    prov = json.loads(meta[b"voyages.provenance"])
    assert prov["disembarkation_region"] == "imputed"
    assert prov["disembarkation_lat"] == "derived"
    assert "disembarkation_provenance" not in prov


def test_csv_file_output(run, tmp_path):
    out = tmp_path / "decades.csv"
    r = run("--by", "decade", "-o", str(out))
    assert r.exit_code == 0 and "wrote" in r.stderr
    assert pd.read_csv(out).voyages.sum() == 600


@pytest.mark.parametrize(
    "args,message",
    [
        (["-e", "Senegal"], "60118"),
        (["-e", "Jamiaca"], "did you mean"),
        (["--flag", "Atlantis"], "no nations label"),
        (["--by", "nope"], "no column"),
        (["-d", "estimates"], "dataset must be"),
        (["--by", "decade", "--year", "sailed"], "on must be"),
    ],
)
def test_bad_input_is_a_clear_error(run, args, message):
    r = run(*args)
    assert r.exit_code == 2
    assert message in r.stderr and "Traceback" not in r.output


def test_output_must_be_csv_or_parquet(run, tmp_path):
    r = run("-o", str(tmp_path / "out.xlsx"))
    assert r.exit_code != 0 and not (tmp_path / "out.xlsx").exists()


def test_missing_build(tmp_path):
    r = runner.invoke(app, ["query", "--built", str(tmp_path)])
    assert r.exit_code == 2 and "voyages build" in r.stderr
