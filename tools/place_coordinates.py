"""Curate place coordinates into src/voyages/schema/reference/curated/place_coordinates.csv.

Dev-time tool, not part of `voyages build`. Coordinates are not in the
SlaveVoyages .sav files, so they come from two outside sources:

1. slavevoyages: the legacy site's 2013 test fixture
   (IQSS/voyages @ cf1e5a8, voyages/apps/voyage/fixtures/test_set_200_voyages.json),
   keyed by place code. (0, 0) points are placeholders and are skipped.
   A point is used only when the fixture's place name agrees with ours,
   because some codes were reassigned after 2013.
2. geonames: reviewed matches against GeoNames (CC BY 4.0), read from
   tools/geonames_matches.csv. Only rows marked accepted are used.

usage:
    uv run python tools/place_coordinates.py <fixture.json> [geonames_matches.csv]
Also writes tools/places_without_coordinates.csv: the queue for GeoNames matching.
"""

from __future__ import annotations

import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

from voyages.ingest.reference import COORDINATES_CSV, REFERENCE_DIR

FIXTURE_REF = "IQSS/voyages@cf1e5a8:voyages/apps/voyage/fixtures/test_set_200_voyages.json"
TOOLS = Path(__file__).parent


def norm(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\((port|eng\.|fr\.|[a-z .]+)\)", " ", s)
    s = re.sub(r"\b(port|location|colony)?,? ?unspecified\b", " ", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return s.strip()


# Fixture names checked by hand (2026-10-19) as the same place under another spelling.
SAME_PLACE = {
    36299: "Guadeloupe (spelling)",
    50302: "Itamaraca (fixture has a broken character)",
    60242: "Kissey River (word order)",
    60734: "Luanda, historically Sao Paulo de Loanda",
}


# Fixture points found wrong on review (2026-10-19). These codes take their
# coordinates from tools/geonames_matches.csv instead, or stay empty.
FIXTURE_REJECT = {
    21404: "longitude sign flipped (30.85, +81.45)",
    60661: "lat/lon swapped (5.63, -1.40 is in Ghana)",
    60220: "point ~220 km out at sea",
    50421: "fixture has Ponta Negra, Natal (RN); code is under Southeast Brazil",
    80601: "point (18.45, -77.45) is in Jamaica, not Bengal",
    80604: "point is Basse-Indre near Nantes, but the code is under India",
}


def names_agree(a: str, b: str) -> bool:
    na, nb = norm(a), norm(b)
    if not na or not nb:
        return False
    return na == nb or na.startswith(nb) or nb.startswith(na) or na.rstrip("s") == nb.rstrip("s")


def main(fixture_path: Path, geonames_path: Path | None) -> None:
    places = list(csv.DictReader((REFERENCE_DIR / "places.csv").open(encoding="utf-8")))
    fx = json.loads(fixture_path.read_text(encoding="utf-8"))
    fixture = {x["fields"]["value"]: x["fields"] for x in fx if x["model"] == "voyage.place"}
    geo = {}
    if geonames_path and geonames_path.exists():
        for r in csv.DictReader(geonames_path.open(encoding="utf-8")):
            if r.get("decision") == "accept":
                geo[int(r["code"])] = r

    out, queue, rejected = [], [], []
    for p in places:
        code, name = int(p["code"]), p["source_name"] or ""
        precision = "representative" if code % 100 == 99 else "place"
        f = fixture.get(code)
        if p["level"] != "place":
            continue  # regions and broad regions: no point coordinates
        if code in FIXTURE_REJECT:
            f = None
        if f and (float(f["latitude"]), float(f["longitude"])) != (0.0, 0.0):
            if code in SAME_PLACE or names_agree(name, f["place"]):
                out.append(
                    {
                        "code": code,
                        "lat": round(float(f["latitude"]), 5),
                        "lon": round(float(f["longitude"]), 5),
                        "coord_source": "slavevoyages",
                        "coord_precision": precision,
                        "coord_ref": FIXTURE_REF,
                        "note": ""
                        if norm(name) == norm(f["place"])
                        else f"fixture name: {f['place']}",
                    }
                )
                continue
            rejected.append((code, name, f["place"]))
        if code in geo:
            g = geo[code]
            out.append(
                {
                    "code": code,
                    "lat": round(float(g["lat"]), 5),
                    "lon": round(float(g["lon"]), 5),
                    "coord_source": "geonames",
                    "coord_precision": g.get("precision") or precision,
                    "coord_ref": f"geonames:{g['geonameid']}",
                    "note": g.get("note", ""),
                }
            )
            continue
        if p["used_in_data"] == "True" and p["source_name"]:
            queue.append(p)

    COORDINATES_CSV.parent.mkdir(parents=True, exist_ok=True)
    with COORDINATES_CSV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(sorted(out, key=lambda r: r["code"]))
    by_code = {int(p["code"]): p for p in places}
    with (TOOLS / "places_without_coordinates.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["code", "name", "alt_name", "region", "broad_region"])
        for p in queue:
            reg = by_code.get(int(p["region_code"] or 0), {}).get("source_name", "")
            broad = by_code.get(int(p["broad_region_code"] or 0), {}).get("source_name", "")
            w.writerow([p["code"], p["source_name"], p["alt_name"], reg, broad])

    n_sv = sum(r["coord_source"] == "slavevoyages" for r in out)
    n_gn = sum(r["coord_source"] == "geonames" for r in out)
    print(f"slavevoyages: {n_sv}  geonames: {n_gn}  queued (used, no coords): {len(queue)}")
    print(f"fixture points rejected for name mismatch: {len(rejected)}")
    for r in rejected:
        print("   ", r)


if __name__ == "__main__":
    main(
        Path(sys.argv[1]),
        Path(sys.argv[2]) if len(sys.argv) > 2 else TOOLS / "geonames_matches.csv",
    )
