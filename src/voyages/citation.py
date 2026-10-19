"""Canonical citation for the SlaveVoyages databases.

The SlaveVoyages project asks that any use of the data credit the site
as the original source. The strings below follow the forms given on
the site's FAQ page (https://www.slavevoyages.org/blog/faqs). Keep them
in sync with the site if the recommended form changes.
"""

from __future__ import annotations

from datetime import date

SITE_URL = "https://www.slavevoyages.org"

DATASETS: dict[str, str] = {
    "transatlantic": "Trans-Atlantic Slave Trade Database",
    "intraamerican": "Intra-American Slave Trade Database",
    "estimates": "Estimates of the Size and Direction of the Trans-Atlantic Slave Trade",
    "people": "People of the Atlantic Slave Trade (African Names)",
}


def citation(dataset: str = "transatlantic", accessed: date | None = None) -> str:
    """Return the recommended citation string for a SlaveVoyages dataset.

    Args:
        dataset: one of ``transatlantic``, ``intraamerican``, ``estimates``, ``people``.
        accessed: access date to record; defaults to today.
    """
    if dataset not in DATASETS:
        raise ValueError(f"unknown dataset {dataset!r}; expected one of {sorted(DATASETS)}")
    accessed = accessed or date.today()
    name = DATASETS[dataset]
    return f"SlaveVoyages, {name}, {SITE_URL} (accessed {accessed:%B %d, %Y})."


def license_notice() -> str:
    """Return the data license summary that accompanies redistributed data."""
    return (
        "Data transcribed from historical documents is in the public domain. "
        "Imputed data (marked * on slavevoyages.org) and all data in the "
        "Estimates database are licensed under a Creative Commons "
        "Attribution-NonCommercial 4.0 International License by SlaveVoyages. "
        f"Source: {SITE_URL}"
    )
