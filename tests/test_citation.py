from datetime import date

import pytest

import voyages
from voyages.citation import DATASETS, citation, license_notice


def test_default_citation_names_transatlantic_and_site():
    s = citation(accessed=date(2026, 10, 19))
    assert s.startswith("SlaveVoyages, Trans-Atlantic Slave Trade Database")
    assert "https://www.slavevoyages.org" in s
    assert "October 19, 2026" in s


@pytest.mark.parametrize("dataset", sorted(DATASETS))
def test_every_dataset_has_a_citation(dataset):
    assert DATASETS[dataset] in citation(dataset)


def test_unknown_dataset_rejected():
    with pytest.raises(ValueError):
        citation("not-a-dataset")


def test_license_notice_distinguishes_public_domain_from_cc_by_nc():
    n = license_notice()
    assert "public domain" in n
    assert "Attribution-NonCommercial" in n


def test_package_exposes_citation():
    assert voyages.citation() == citation()
