"""Shared fixtures: Parquet built from the committed sample .sav files."""

import warnings
from pathlib import Path

import pytest

from voyages import Voyages
from voyages.ingest import estimates, intraamerican, transatlantic

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def built(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("built")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # the known-bad-value warnings
        transatlantic.build(FIXTURES / "transatlantic_sample.sav", out)
        intraamerican.build(FIXTURES / "intraamerican_sample.sav", out)
        estimates.build(FIXTURES / "estimates_sample.sav", out)
    return out


@pytest.fixture(scope="session")
def v(built):
    with Voyages(built) as v:
        yield v
