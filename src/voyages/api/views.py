"""Derived DuckDB views. Each one is registered in fields.yaml with ``view: true``.

``voyage_endpoints`` resolves, for every voyage, where its captives were
embarked and disembarked and which point to draw for each on a map.

For each endpoint:

- place: the imputed principal place (MJBYPTIMP / MJSLPTIMP), which is what
  the site's maps use, else the recorded principal place (MAJBUYPT /
  MAJSELPT). The imputed place differs from the recorded one on some
  voyages, so ``provenance`` is ``recorded`` only when the two agree.
- region and broad region: the voyage's own principal region fields (kept
  as recorded, codebook p.30), else the place's parents in ``places``.
- point, in order: the place's own point (precision ``place`` or
  ``representative``); else the centre of the voyage's region; else the
  place's ``map_*`` fallback from ``places``. Catch-all places and regions
  ("Africa, port unspecified", "Other Africa") get no point.

An imputed principal place in the region "Codes without labels" (99800;
place 99801 is named "???") means the imputation had no answer. The site
shows "???" too (voyage 113, checked 2026-10-19). Then the imputed place,
region and broad region are ignored and the recorded place is used.
"""

from __future__ import annotations

import duckdb

ENDPOINTS = {"embarkation": "principal_purchase", "disembarkation": "principal_landing"}

# Imputed regions that mean "unknown": the imputation gave no usable place.
UNKNOWN_REGIONS = (99800,)

_PRINCIPAL = """
    max(code) FILTER (role = '{role}' AND level = 'place' AND provenance = 'imputed') AS {e}_imp,
    max(code) FILTER (role = '{role}' AND level = 'place' AND provenance = 'recorded') AS {e}_rec,
    max(code) FILTER (role = '{role}' AND level = 'region') AS {e}_reg,
    max(code) FILTER (role = '{role}' AND level = 'broad_region') AS {e}_broad,
    coalesce(bool_or(role = '{role}' AND level = 'region' AND code IN ({unknown})), false)
        AS {e}_unknown"""

_KNOWN = """
        CASE WHEN {e}_unknown THEN NULL ELSE {e}_imp END AS {e}_imp,
        CASE WHEN {e}_unknown THEN NULL ELSE {e}_reg END AS {e}_reg,
        CASE WHEN {e}_unknown THEN NULL ELSE {e}_broad END AS {e}_broad"""

_RESOLVED = """
{e} AS (
    SELECT
        v.voyage_id,
        coalesce(v.{e}_imp, v.{e}_rec) AS place,
        CASE
            WHEN coalesce(v.{e}_imp, v.{e}_rec) IS NULL THEN NULL
            WHEN v.{e}_rec = coalesce(v.{e}_imp, v.{e}_rec) THEN 'recorded'
            ELSE 'imputed'
        END AS provenance,
        coalesce(v.{e}_reg, p.region_code) AS region,
        coalesce(v.{e}_broad, p.broad_region_code) AS broad_region,
        p.name AS place_name,
        CASE
            WHEN p.map_precision IN ('place', 'representative') THEN 'own'
            WHEN r.map_lat IS NOT NULL THEN 'voyage_region'
            WHEN p.map_lat IS NOT NULL THEN 'place_fallback'
        END AS point_from,
        p.map_lat AS p_lat, p.map_lon AS p_lon,
        p.map_precision AS p_precision, p.map_code AS p_code,
        r.map_lat AS r_lat, r.map_lon AS r_lon,
        r.map_precision AS r_precision, r.map_code AS r_code
    FROM v
    LEFT JOIN places p ON p.code = coalesce(v.{e}_imp, v.{e}_rec)
    LEFT JOIN places r ON r.code = coalesce(v.{e}_reg, p.region_code)
)"""

_COLUMNS = """
    {e}.place::INTEGER AS {e}_place,
    {e}.place_name AS {e}_place_name,
    {e}.provenance AS {e}_provenance,
    {e}.region::INTEGER AS {e}_region,
    {e}_r.name AS {e}_region_name,
    {e}.broad_region::INTEGER AS {e}_broad_region,
    {e}_b.name AS {e}_broad_region_name,
    (CASE WHEN {e}.point_from = 'voyage_region' THEN {e}.r_lat ELSE {e}.p_lat END)::DOUBLE
        AS {e}_lat,
    (CASE WHEN {e}.point_from = 'voyage_region' THEN {e}.r_lon ELSE {e}.p_lon END)::DOUBLE
        AS {e}_lon,
    CASE WHEN {e}.point_from = 'voyage_region' THEN {e}.r_precision ELSE {e}.p_precision END
        AS {e}_precision,
    (CASE WHEN {e}.point_from = 'voyage_region' THEN {e}.r_code ELSE {e}.p_code END)::INTEGER
        AS {e}_map_code"""

_JOINS = """
JOIN {e} ON {e}.voyage_id = v.voyage_id
LEFT JOIN places {e}_r ON {e}_r.code = {e}.region
LEFT JOIN places {e}_b ON {e}_b.code = {e}.broad_region"""


def endpoints_sql() -> str:
    unknown = ", ".join(str(c) for c in UNKNOWN_REGIONS)
    principal = ",".join(
        _PRINCIPAL.format(e=e, role=role, unknown=unknown) for e, role in ENDPOINTS.items()
    )
    known = ",".join(_KNOWN.format(e=e) for e in ENDPOINTS)
    resolved = ",".join(_RESOLVED.format(e=e) for e in ENDPOINTS)
    columns = ",".join(_COLUMNS.format(e=e) for e in ENDPOINTS)
    joins = "".join(_JOINS.format(e=e) for e in ENDPOINTS)
    return f"""
CREATE VIEW voyage_endpoints AS
WITH principal AS (
    SELECT voyage_id,{principal}
    FROM voyage_places
    WHERE role IN ({", ".join(f"'{r}'" for r in ENDPOINTS.values())})
    GROUP BY voyage_id
),
v AS (
    SELECT voyages.voyage_id, voyages.dataset,
        principal.* EXCLUDE (voyage_id) REPLACE ({known}
        )
    FROM voyages LEFT JOIN principal USING (voyage_id)
),{resolved}
SELECT
    v.voyage_id::INTEGER AS voyage_id,
    v.dataset,{columns},
    (embarkation_lat IS NOT NULL AND disembarkation_lat IS NOT NULL) AS drawable
FROM v{joins}
ORDER BY v.voyage_id
"""


COVERAGE_SQL = """
WITH sides AS (
    SELECT dataset, 'embarkation' AS endpoint,
        coalesce(embarkation_precision,
                 CASE WHEN embarkation_place IS NULL THEN 'no_place' ELSE 'no_point' END) AS status
    FROM voyage_endpoints
    UNION ALL
    SELECT dataset, 'disembarkation',
        coalesce(disembarkation_precision,
                 CASE WHEN disembarkation_place IS NULL THEN 'no_place' ELSE 'no_point' END)
    FROM voyage_endpoints
    UNION ALL
    SELECT dataset, 'route', CASE WHEN drawable THEN 'drawable' ELSE 'not_drawable' END
    FROM voyage_endpoints
)
SELECT dataset, endpoint, status, count(*) AS voyages,
    round(count(*) / sum(count(*)) OVER (PARTITION BY dataset, endpoint), 4) AS share
FROM sides
GROUP BY dataset, endpoint, status
ORDER BY dataset DESC, endpoint DESC, voyages DESC
"""


def create(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(endpoints_sql())
