"""Offline tests for the download manifest and verification logic."""

from pathlib import Path

from voyages import fetch
from voyages.fetch import MANIFEST, RawFile, sha256_of, verify


def test_manifest_covers_every_default_dataset():
    present = {e.dataset for e in MANIFEST}
    assert set(fetch.DEFAULT_DATASETS) <= present


def test_manifest_names_are_unique():
    names = [e.name for e in MANIFEST]
    assert len(names) == len(set(names))


def test_download_urls_point_at_legacy_site():
    for e in MANIFEST:
        if e.dataset in fetch.SUPPLEMENTARY_DATASETS:
            continue
        assert e.download_url.startswith("https://legacy.slavevoyages.org/documents/download/")
        assert e.download_url.endswith(e.name)


def test_supplementary_files_are_opt_in_and_pinned():
    supp = [e for e in MANIFEST if e.dataset in fetch.SUPPLEMENTARY_DATASETS]
    assert {e.dataset for e in supp} == set(fetch.SUPPLEMENTARY_DATASETS)
    assert not set(fetch.SUPPLEMENTARY_DATASETS) & set(fetch.DEFAULT_DATASETS)
    for e in supp:
        assert e.sha256 and e.url and e.url.startswith("https://"), e.name


def test_each_dataset_has_an_spss_file_except_codebook():
    for ds in ("transatlantic", "intraamerican", "estimates"):
        assert any(e.dataset == ds and e.name.endswith(".sav") for e in MANIFEST), ds


def test_verify_reports_missing_and_unverified(tmp_path: Path):
    status = verify(tmp_path)
    assert set(status) == {e.name for e in MANIFEST}
    for e in MANIFEST:
        optional = e.dataset in fetch.SUPPLEMENTARY_DATASETS
        assert status[e.name] == ("not fetched (optional)" if optional else "missing")

    first = MANIFEST[0]
    (tmp_path / first.name).write_bytes(b"not real data")
    status = verify(tmp_path)
    assert status[first.name] == ("unverified" if first.sha256 is None else "mismatch")


def test_sha256_of_matches_hashlib(tmp_path: Path):
    p = tmp_path / "x.bin"
    p.write_bytes(b"abc")
    assert sha256_of(p) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_rawfile_url_override():
    e = RawFile("x.sav", "transatlantic", "test", url="https://example.org/x.sav")
    assert e.download_url == "https://example.org/x.sav"
