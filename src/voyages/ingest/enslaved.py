"""Ingest Enslaved.org (Enslaved: Peoples of the Historical Slave Trade), a supplementary source.

Source: the project's Wikibase JSON dump (see docs/DATA.md and ``fetch.MANIFEST``),
one JSON entity per line. Every record in it is an item with an ``instance of``
(P1) class: Person, Event, Place, Entity with Provenance (a source) or Research
Project (a contributed dataset), plus the controlled vocabularies (sex, roles,
statuses, ethnonyms, event types, place types, licences).

The build reads the dump twice: once for the label and class of every item,
once to write the tables. Nothing is merged into the SlaveVoyages tables. Each
statement in the dump cites its sources (references, P6); ``enslaved_record_sources``
keeps those links, and ``enslaved_sources`` carries each source's licence, so a
record's licence is always recoverable. Licences vary by contributed dataset.

Multi-valued fields are joined with ``"; "`` (descriptions with ``" | "``), in
source order, without duplicates.
"""

from __future__ import annotations

import gzip
import json
from collections.abc import Iterator
from pathlib import Path

import pandas as pd
import pyarrow as pa

from voyages import schema
from voyages.config import built_dir, raw_dir
from voyages.ingest import voyages

DATASET = "enslaved"
RAW_FILE = "enslaved-wikibase-2026-03-31.json.gz"

# Class labels (P1 values) that become tables.
PERSON, EVENT, PLACE, SOURCE, PROJECT = (
    "Person",
    "Event",
    "Place",
    "Entity with Provenance",
    "Research Project",
)
TABLES = (
    "enslaved_people",
    "enslaved_roles",
    "enslaved_events",
    "enslaved_event_places",
    "enslaved_places",
    "enslaved_sources",
    "enslaved_projects",
    "enslaved_record_sources",
)


# ---------------------------------------------------------------- reading
def entities(path: Path) -> Iterator[dict]:
    """Every entity in a Wikibase JSON dump (gzipped JSON array, one entity per line)."""
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip().rstrip(",")
            if line in ("", "[", "]"):
                continue
            yield json.loads(line)


def _qid(value: dict | None) -> int | None:
    if isinstance(value, dict) and value.get("id", "").startswith("Q"):
        return int(value["id"][1:])
    return None


def _value(snak: dict):
    return snak.get("datavalue", {}).get("value")


def _label(entity: dict) -> str:
    labels = entity.get("labels", {})
    for lang in ("en", "en-us"):
        if lang in labels:
            return labels[lang]["value"]
    return next(iter(labels.values()))["value"] if labels else ""


def _description(entity: dict) -> str | None:
    d = entity.get("descriptions", {}).get("en")
    return d["value"] if d else None


def _claims(entity: dict, prop: str) -> list[dict]:
    return entity.get("claims", {}).get(prop, [])


def _first(entity: dict, prop: str):
    """The value of a property's first statement, or None."""
    claims = _claims(entity, prop)
    return _value(claims[0]["mainsnak"]) if claims else None


def _items(entity: dict, prop: str) -> list[int]:
    return [q for c in _claims(entity, prop) if (q := _qid(_value(c["mainsnak"]))) is not None]


def _strings(entity: dict, prop: str) -> list[str]:
    return [v for c in _claims(entity, prop) if isinstance(v := _value(c["mainsnak"]), str)]


def _qualifier_items(claim: dict, prop: str) -> list[int]:
    return [
        q for s in claim.get("qualifiers", {}).get(prop, []) if (q := _qid(_value(s))) is not None
    ]


def _join(values, sep: str = "; ") -> str | None:
    out = list(dict.fromkeys(v for v in values if v))
    return sep.join(out) if out else None


def format_date(value: dict | None) -> tuple[str | None, int | None]:
    """A Wikibase time value as ISO text cut to its precision, and its year.

    ``{"time": "+1785-00-00T00:00:00Z", "precision": 9}`` gives ``("1785", 1785)``;
    precision 10 keeps the month, 11 the day.
    """
    if not isinstance(value, dict) or "time" not in value:
        return None, None
    t = value["time"]
    if not t.startswith("+"):
        return None, None  # BCE or malformed; none expected
    date = t[1:11]
    year = int(date[:4])
    keep = {9: 4, 10: 7, 11: 10}.get(value.get("precision"), 4)
    return date[:keep], year


# ---------------------------------------------------------------- build
def scan_labels(path: Path) -> tuple[dict[int, str], dict[int, tuple[int, ...]]]:
    """Pass 1: the label of every item, and its classes (all P1 values)."""
    labels: dict[int, str] = {}
    classes: dict[int, tuple[int, ...]] = {}
    for e in entities(path):
        if e.get("type") != "item":
            continue
        q = int(e["id"][1:])
        labels[q] = _label(e)
        p1 = _items(e, "P1")
        if p1:
            classes[q] = tuple(p1)
    return labels, classes


def class_ids(labels: dict[int, str], classes: dict[int, tuple[int, ...]]) -> dict[int, str]:
    """``{item id: class label}`` for the five table classes.

    Every ``instance of`` value with one of the five labels counts: the
    2026-03-31 dump has two classes called "Place" (Q301, 10,379 records, and
    Q280159, 2), and enslaved.org counts both (10,381 places).
    """
    used = {c for cs in classes.values() for c in cs}
    names = (PERSON, EVENT, PLACE, SOURCE, PROJECT)
    return {q: labels[q] for q in sorted(used) if labels.get(q) in names}


def build_frames(path: Path) -> dict[str, pd.DataFrame]:
    """Pass 2: one frame per table, columns as in the registry."""
    labels, classes = scan_labels(path)
    want = class_ids(labels, classes)

    def names(qs) -> list[str]:
        return [labels.get(q, "") for q in qs]

    rows: dict[str, list[dict]] = {t: [] for t in TABLES}
    for e in entities(path):
        if e.get("type") != "item":
            continue
        q = int(e["id"][1:])
        cls = next((want[c] for c in classes.get(q, ()) if c in want), None)
        if cls is None:
            continue
        if cls in (PERSON, EVENT):
            refs = {
                src
                for cs in e.get("claims", {}).values()
                for c in cs
                for r in c.get("references", [])
                for s in r.get("snaks", {}).get("P6", [])
                if (src := _qid(_value(s))) is not None
            }
            rows["enslaved_record_sources"] += [
                {"record_id": q, "source_id": s} for s in sorted(refs)
            ]
        if cls == PERSON:
            rows["enslaved_people"].append(_person(e, q, names))
            seen = set()
            for c in _claims(e, "P17"):
                role = _qid(_value(c["mainsnak"]))
                for ev in _qualifier_items(c, "P19") or _qualifier_items(c, "P18"):
                    if (ev, role) not in seen:
                        seen.add((ev, role))
                        rows["enslaved_roles"].append(
                            {"person_id": q, "event_id": ev, "participant_role": labels.get(role)}
                        )
        elif cls == EVENT:
            date, year = format_date(_first(e, "P28"))
            rows["enslaved_events"].append(
                {
                    "event_id": q,
                    "event_record_id": _description(e),
                    "event_name": next(iter(_strings(e, "P20")), None) or _label(e),
                    "event_type": _join(names(_items(e, "P30"))),
                    "event_date": date,
                    "event_year": year,
                    "event_description": _join(_strings(e, "P66"), " | "),
                }
            )
            for seq, place in enumerate(dict.fromkeys(_items(e, "P27")), start=1):
                rows["enslaved_event_places"].append({"event_id": q, "seq": seq, "place_id": place})
        elif cls == PLACE:
            coords = _first(e, "P59") or {}
            rows["enslaved_places"].append(
                {
                    "place_id": q,
                    "place_label": next(iter(_strings(e, "P20")), None) or _label(e),
                    "place_type": _join(names(_items(e, "P8"))),
                    "located_in_id": next(iter(_items(e, "P7")), None),
                    "located_in": _join(names(_items(e, "P7"))),
                    "latitude": coords.get("latitude"),
                    "longitude": coords.get("longitude"),
                    "geonames_id": next(iter(_strings(e, "P36")), None),
                    "modern_country_code": next(iter(_strings(e, "P9")), None),
                }
            )
        elif cls == SOURCE:
            _, year = format_date(_first(e, "P28"))
            rows["enslaved_sources"].append(
                {
                    "source_id": q,
                    "source_record_id": _description(e),
                    "source_title": next(iter(_strings(e, "P20")), None) or _label(e),
                    "project_id": next(iter(_items(e, "P16")), None),
                    "licence": _join(names(_items(e, "P15"))),
                    "source_type": _join(names(_items(e, "P23"))),
                    "source_url": next(iter(_strings(e, "P21")), None),
                    "source_year": year,
                }
            )
        elif cls == PROJECT:
            resources = {
                _value(c["mainsnak"]): next(
                    (_value(s) for s in c.get("qualifiers", {}).get("P12", [])), None
                )
                for c in _claims(e, "P83")
            }
            _, start = format_date(_first(e, "P82"))
            _, end = format_date(_first(e, "P63"))
            rows["enslaved_projects"].append(
                {
                    "project_id": q,
                    "project_code": _description(e),
                    "project_name": next(iter(_strings(e, "P20")), None) or _label(e),
                    "contributors": _join(_strings(e, "P13")),
                    "start_year": start,
                    "end_year": end,
                    "data_article_url": next(
                        (u for k, u in resources.items() if k and "Data Article" in k), None
                    ),
                    "documentation_url": next(
                        (u for k, u in resources.items() if k and "Documentation" in k), None
                    ),
                    "project_description": next(iter(_strings(e, "P66")), None),
                }
            )
    frames = {t: pd.DataFrame(r) for t, r in rows.items()}
    frames["enslaved_record_sources"] = frames["enslaved_record_sources"].drop_duplicates()
    return frames


def _person(e: dict, q: int, names) -> dict:
    ethnonyms = _claims(e, "P46")
    return {
        "person_id": q,
        "person_record_id": _description(e),
        "person_name": next(iter(_strings(e, "P20")), None) or _label(e),
        "first_name": _join(_strings(e, "P73")),
        "surname": _join(_strings(e, "P72")),
        "alternate_names": _join(_strings(e, "P71")),
        "sex": _join(names(_items(e, "P31"))),
        "age": _join(names(_items(e, "P42"))),
        "age_category": _join(names(_items(e, "P4"))),
        "race_or_color": _join(_strings(e, "P32")),
        "ethnonym": _join(names(_items(e, "P46"))),
        "ethnonym_place_of_origin": _join(
            names(q2 for c in ethnonyms for q2 in _qualifier_items(c, "P47"))
        ),
        "ethnonym_as_written": _join(_strings(e, "P77")),
        "occupation": _join(names(_items(e, "P22"))),
        "occupation_as_written": _join(_strings(e, "P78")),
        "person_statuses": _join(names(_items(e, "P33"))),
        "person_description": _join(_strings(e, "P66"), " | "),
    }


def build_tables(path: Path | None = None) -> dict[str, pa.Table]:
    reg = schema.load()
    frames = build_frames(path or raw_dir() / RAW_FILE)
    return {t: voyages._to_arrow(t, frames[t], reg) for t in TABLES}


def build(path: Path | None = None, out_dir: Path | None = None) -> dict[str, Path]:
    """Build the ``enslaved_*`` tables. Returns {table: path}."""
    return voyages.write(build_tables(path), DATASET, out_dir or built_dir())


def available(path: Path | None = None) -> bool:
    """Whether the dump has been fetched (it is opt-in: ``voyages fetch -d enslaved``)."""
    return (path or raw_dir() / RAW_FILE).exists()
