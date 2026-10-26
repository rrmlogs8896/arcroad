"""M2 Access to essentials: hospitals first (build step 5; ledger 36.33, 36.72).

How much further, by legal road, is the nearest hospital than it looks on a map,
and how many people carry that extra distance.

Decisions (Rohit, 27 Oct 2026):

* Hospitals first; schools, bus stops and metro stations follow one at a time.
* Headline measure is EXCESS METRES (road distance minus straight-line distance).
  The ratio is kept as a secondary column.
* Origins are 250 m grid cells weighted by GHSL population, never homes or people.
* Government and private hospitals are separate layers. A private hospital next
  door does not serve someone who depends on free government care.

Rules carried over from M1, each enforced here rather than left to memory:

* Distance and geometry only, never travel time. Driving only.
* None means "not measured", never "zero". Every unmeasured cell is counted,
  with its people, in the summary instead of dropping out of it.
* A cell whose centre is far from any drivable road is a data gap, not a result.
"""

from __future__ import annotations

import math

from pipeline.geometry import haversine_m

CELL_M = 250.0
# A cell centre more than this from the nearest drivable node is a data gap:
# the road it would use is probably missing from the map.
SNAP_MAX_M = 150.0
# An OSM hospital this close to an official government facility is taken to be
# that facility, so it is not counted twice or mislabelled private.
MATCH_M = 150.0

# Official facility types that count as a hospital for this layer: places a
# person goes for inpatient or emergency care. Dispensaries, sub-centres and
# wellness centres are excluded; PHCs are kept out of v1 (most offer no
# emergency care) and can be added as their own layer later.
GOVT_HOSPITAL_WORDS = (
    "hospital",
    "community health centre",
    "community health center",
    "chc",
)
# AYUSH hospitals are excluded from v1 too: they rarely run emergency care.
GOVT_EXCLUDE_WORDS = (
    "dispensary", "sub centre", "sub-centre", "subcentre", "wellness",
    "ayush", "ayurveda", "ayurvedic", "homoeopathy", "homeopathy", "unani", "siddha", "naturopathy",
)

GOVT_OPERATOR_TYPES = {"government", "public", "state", "central"}

EXCESS_BANDS_M = (500, 1000, 2000, 5000)


def grid_cells(bbox, cell_m: float = CELL_M):
    """Cell centres covering bbox = (min_lon, min_lat, max_lon, max_lat).

    Cells are fixed in degrees from the bbox origin, sized at the bbox's mid
    latitude, so ids are stable for a given bbox and size.
    """
    min_lon, min_lat, max_lon, max_lat = bbox
    if not (min_lon < max_lon and min_lat < max_lat):
        raise ValueError("bbox must be (min_lon, min_lat, max_lon, max_lat)")
    mid = math.radians((min_lat + max_lat) / 2)
    dlat = cell_m / 111_320.0
    dlon = cell_m / (111_320.0 * math.cos(mid))
    cells = []
    rows = math.ceil((max_lat - min_lat) / dlat)
    cols = math.ceil((max_lon - min_lon) / dlon)
    for r in range(rows):
        for c in range(cols):
            cells.append({
                "cell_id": f"r{r}c{c}",
                "lon": min_lon + (c + 0.5) * dlon,
                "lat": min_lat + (r + 0.5) * dlat,
            })
    return cells, (dlon, dlat)


def cell_of(lon: float, lat: float, bbox, steps) -> str | None:
    """The id of the grid cell containing a point, or None outside the grid.

    The grid is whole cells, so its last row and column reach slightly past the
    bbox; a point there belongs to that edge cell, not to "outside".
    """
    min_lon, min_lat, max_lon, max_lat = bbox
    dlon, dlat = steps
    rows = math.ceil((max_lat - min_lat) / dlat)
    cols = math.ceil((max_lon - min_lon) / dlon)
    r = math.floor((lat - min_lat) / dlat)
    c = math.floor((lon - min_lon) / dlon)
    if not (0 <= r < rows and 0 <= c < cols):
        return None
    return f"r{r}c{c}"


def add_population(cells, pixels, bbox, steps):
    """Sum population pixels {lon, lat, pop} into the cells that contain them.

    Returns the cells with a `pop` field, and the population that fell outside
    the bbox, so nothing disappears unaccounted.
    """
    by_id = {c["cell_id"]: dict(c, pop=0.0) for c in cells}
    outside = 0.0
    for p in pixels:
        cid = cell_of(p["lon"], p["lat"], bbox, steps)
        if cid is None or cid not in by_id:
            outside += p["pop"]
            continue
        by_id[cid]["pop"] += p["pop"]
    return list(by_id.values()), outside


def _norm(s) -> str:
    return " ".join(str(s or "").lower().replace(".", " ").split())


def is_govt_hospital(facility: dict) -> bool:
    """True for an official facility that is government-owned, functional and a hospital."""
    if _norm(facility.get("ownership")) != "government":
        return False
    if _norm(facility.get("status")) not in ("", "functional"):
        return False
    ftype = _norm(facility.get("facility_type"))
    if any(w in ftype for w in GOVT_EXCLUDE_WORDS):
        return False
    return any(w == ftype or w in ftype.split() or (" " in w and w in ftype) for w in GOVT_HOSPITAL_WORDS)


def hospital_layers(official, osm):
    """Split hospitals into government and private destination layers.

    Government: official facilities passing is_govt_hospital, plus any OSM
    hospital whose operator type says government and that no official
    facility already covers. Private: OSM amenity=hospital not within MATCH_M
    of a government facility and not tagged as government-run. An OSM hospital
    near an official one is that facility; it is never counted twice.
    """
    govt = [
        {"dest_id": f"tg:{f['id']}", "lon": f["lon"], "lat": f["lat"], "name": f.get("name"), "source": "official"}
        for f in official
        if is_govt_hospital(f)
    ]
    private = []
    for h in osm:
        tags = h.get("tags", {})
        if tags.get("amenity") != "hospital":
            continue
        near_govt = any(haversine_m(h["lon"], h["lat"], g["lon"], g["lat"]) <= MATCH_M for g in govt)
        if near_govt:
            continue
        rec = {"dest_id": f"osm:{h['id']}", "lon": h["lon"], "lat": h["lat"], "name": tags.get("name"), "source": "osm"}
        if _norm(tags.get("operator:type")) in GOVT_OPERATOR_TYPES:
            govt.append(rec)
        else:
            private.append(rec)
    return {"government": govt, "private": private}


def nearest_by_line(lon: float, lat: float, dests):
    """(dest, metres) of the straight-line nearest destination, or (None, None)."""
    best, best_m = None, None
    for d in dests:
        m = haversine_m(lon, lat, d["lon"], d["lat"])
        if best_m is None or m < best_m:
            best, best_m = d, m
    return best, best_m


def access_record(cell: dict, layer: str, dests, road_m: dict, snap_m: float | None):
    """One measured row for a cell and a destination layer.

    `road_m` maps dest_id to routed driving metres from the cell's snapped node
    (missing or None means unreachable within the routing limit). The nearest
    by road may be a different hospital from the nearest by straight line;
    both are recorded. Excess is the road distance to the nearest hospital by
    road minus the straight-line distance to the nearest hospital on the map,
    as approved in the design (27 Oct): it is the gap a resident sees between
    "the hospital looks this close" and "this is how far I must drive". It is
    never negative, because no road trip is shorter than the nearest straight
    line. The straight line to the hospital actually reached is kept too.
    """
    near, s_line = nearest_by_line(cell["lon"], cell["lat"], dests)
    rec = {
        "cell_id": cell["cell_id"],
        "lon": cell["lon"],
        "lat": cell["lat"],
        "pop": cell.get("pop"),
        "layer": layer,
        "snap_m": snap_m,
        "line_dest_id": near["dest_id"] if near else None,
        "line_m": s_line,
        "road_dest_id": None,
        "road_m": None,
        "road_dest_line_m": None,
        "excess_m": None,
        "ratio": None,
        "status": "measured",
    }
    if near is None:
        rec["status"] = "no_destinations"
        return rec
    if snap_m is None or snap_m > SNAP_MAX_M:
        rec["status"] = "gap_no_road"
        return rec
    reachable = {k: v for k, v in road_m.items() if v is not None and math.isfinite(v)}
    if not reachable:
        rec["status"] = "unreachable"
        return rec
    dest_id = min(reachable, key=reachable.get)
    dest = next(d for d in dests if d["dest_id"] == dest_id)
    straight = haversine_m(cell["lon"], cell["lat"], dest["lon"], dest["lat"])
    rec.update(
        road_dest_id=dest_id,
        road_m=reachable[dest_id],
        road_dest_line_m=straight,
        excess_m=max(0.0, reachable[dest_id] - s_line),
        ratio=(reachable[dest_id] / s_line) if s_line > 0 else None,
    )
    return rec


def _weighted_quantile(pairs, q):
    pairs = sorted(pairs)
    total = sum(w for _, w in pairs)
    if total <= 0:
        return None
    acc = 0.0
    for v, w in pairs:
        acc += w
        if acc >= q * total:
            return v
    return pairs[-1][0]


def people_summary(records, bands=EXCESS_BANDS_M):
    """Population-weighted summary over EVERY record of one layer.

    Unmeasured cells are not dropped: their people are reported by status, so
    the share of people the measure could not reach is always visible.
    """
    total = sum(r.get("pop") or 0.0 for r in records)
    measured = [r for r in records if r["status"] == "measured" and (r.get("pop") or 0) > 0]
    m_pop = sum(r["pop"] for r in measured)
    by_status = {}
    for r in records:
        if r["status"] != "measured":
            by_status[r["status"]] = by_status.get(r["status"], 0.0) + (r.get("pop") or 0.0)
    pairs = [(r["excess_m"], r["pop"]) for r in measured]
    out = {
        "people_total": round(total),
        "people_measured": round(m_pop),
        "people_unmeasured_by_status": {k: round(v) for k, v in sorted(by_status.items())},
        "median_excess_m": _weighted_quantile(pairs, 0.5),
        "p90_excess_m": _weighted_quantile(pairs, 0.9),
    }
    for b in bands:
        share = sum(w for v, w in pairs if v >= b)
        out[f"pct_people_excess_ge_{b}m"] = round(100.0 * share / m_pop, 1) if m_pop else 0.0
    return out


REQUIRED_EXPORT_FIELDS = (
    "cell_id", "lon", "lat", "pop", "layer", "status", "snap_m",
    "line_dest_id", "line_m", "road_dest_id", "road_m", "excess_m",
    "extract_date", "graph_hash", "population_source", "destination_source",
)


def export_problems(rec: dict) -> list[str]:
    """What stops a row being re-checkable by someone else (the B-09 lesson)."""
    missing = [k for k in REQUIRED_EXPORT_FIELDS if k not in rec]
    probs = [f"missing {k}" for k in missing]
    if rec.get("status") == "measured":
        for k in ("road_dest_id", "road_m", "excess_m", "extract_date", "graph_hash"):
            if rec.get(k) in (None, ""):
                probs.append(f"measured row without {k}")
    return probs
