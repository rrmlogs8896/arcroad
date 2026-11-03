"""Pre-registered job: where is crossing pressure likely highest? (docs/PREREG-hotspots.md)

Open sources only:
  - GHSL GHS-POP R2023A, epoch 2020, 3 arc-second grid (European Commission JRC, CC BY 4.0)
  - WorldPop 2020 constrained, India, 100 m (University of Southampton, CC BY 4.0), as a cross-check
  - OpenStreetMap via Overpass (ODbL): main roads and daytime destinations

This measures exposure, not traffic. No open source in India publishes counted traffic, so every
output is a pressure proxy and is labelled that way. Nothing here is published until reviewed.
"""
from __future__ import annotations

import itertools
import json
import math
import sys
import urllib.parse
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from openings import OVERPASS, PLACES_URL, get

WORLDPOP = ("https://data.worldpop.org/GIS/Population/Global_2000_2020_Constrained/2020/BSGM/IND/"
            "ind_ppp_2020_UNadj_constrained.tif")
CELL_M = 500.0
NEAR_M = 500.0
CATCH_M = 1000.0
TOP_N = 25
TRIANGULATE_MIN_RHO = 0.70   # pre-registered: GHSL and WorldPop must agree at the places
ROAD_ADDS_INFO_MAX_OVERLAP = 0.80  # pre-registered control against "it is only population"
MAIN_ROADS = ("motorway", "trunk", "primary", "secondary")
DESTINATIONS = [
    '["amenity"~"^(school|college|university|hospital|clinic|marketplace|bus_station)$"]',
    '["shop"~"^(mall|supermarket|department_store)$"]',
    '["office"]',
    '["railway"="station"]',
    '["public_transport"="station"]',
]


# ---------------- pure helpers (unit-tested) ----------------

def m_per_deg(lat: float) -> tuple[float, float]:
    """Metres per degree of longitude and latitude at a latitude."""
    return 111320.0 * math.cos(math.radians(lat)), 110574.0


def disk_sum(arr: np.ndarray, transform, lon: float, lat: float, radius_m: float) -> float:
    """Sum of raster cells whose centres fall within radius_m of (lon, lat). transform is an affine
    (a, b, c, d, e, f) with b = d = 0, as GDAL north-up rasters have."""
    a, _, c, _, e, f = transform[:6]
    mx, my = m_per_deg(lat)
    dc, dr = radius_m / (abs(a) * mx), radius_m / (abs(e) * my)
    col, row = (lon - c) / a, (lat - f) / e
    r0, r1 = max(0, int(row - dr) - 1), min(arr.shape[0], int(row + dr) + 2)
    c0, c1 = max(0, int(col - dc) - 1), min(arr.shape[1], int(col + dc) + 2)
    if r0 >= r1 or c0 >= c1:
        return 0.0
    rr, cc = np.mgrid[r0:r1, c0:c1]
    ylat = f + (rr + 0.5) * e
    xlon = c + (cc + 0.5) * a
    d = np.hypot((xlon - lon) * mx, (ylat - lat) * my)
    win = arr[r0:r1, c0:c1]
    ok = (d <= radius_m) & np.isfinite(win) & (win > 0)
    return float(win[ok].sum())


def spearman(x, y) -> float | None:
    x, y = np.asarray(x, float), np.asarray(y, float)
    if len(x) < 5:
        return None
    rx, ry = x.argsort().argsort(), y.argsort().argsort()
    if rx.std() == 0 or ry.std() == 0:
        return None
    return float(np.corrcoef(rx, ry)[0, 1])


def pct_rank(v: np.ndarray) -> np.ndarray:
    """Percentile rank in [0, 1]; ties share the lower rank."""
    v = np.asarray(v, float)
    if len(v) < 2:
        return np.zeros_like(v)
    return v.argsort().argsort() / (len(v) - 1)


def grid_cells(bbox, cell_m: float = CELL_M):
    x0, y0, x1, y1 = bbox
    mx, my = m_per_deg((y0 + y1) / 2)
    dx, dy = cell_m / mx, cell_m / my
    xs = np.arange(x0 + dx / 2, x1, dx)
    ys = np.arange(y0 + dy / 2, y1, dy)
    return [(float(x), float(y)) for y in ys for x in xs]


def line_km_near(lines, lon, lat, radius_m) -> float:
    """Kilometres of polyline whose segment midpoints lie within radius_m of the point."""
    mx, my = m_per_deg(lat)
    tot = 0.0
    for pts in lines:
        for (ax, ay), (bx, by) in itertools.pairwise(pts):
            mxp, myp = (ax + bx) / 2, (ay + by) / 2
            if math.hypot((mxp - lon) * mx, (myp - lat) * my) <= radius_m:
                tot += math.hypot((bx - ax) * mx, (by - ay) * my)
    return tot / 1000.0


class Near:
    """Fast radius queries in metres for many points and many road segments (KD-tree)."""

    def __init__(self, points, lines, lat0):
        from scipy.spatial import cKDTree

        self.mx, self.my = m_per_deg(lat0)
        P = np.array(points, float).reshape(-1, 2)
        self.pt = cKDTree(np.c_[P[:, 0] * self.mx, P[:, 1] * self.my]) if len(P) else None
        mids, lens = [], []
        for pts in lines:
            for (ax, ay), (bx, by) in itertools.pairwise(pts):
                mids.append(((ax + bx) / 2 * self.mx, (ay + by) / 2 * self.my))
                lens.append(math.hypot((bx - ax) * self.mx, (by - ay) * self.my))
        self.seg = cKDTree(np.array(mids)) if mids else None
        self.len = np.array(lens)

    def count(self, lon, lat, r):
        return 0 if self.pt is None else len(self.pt.query_ball_point((lon * self.mx, lat * self.my), r))

    def road_km(self, lon, lat, r):
        if self.seg is None:
            return 0.0
        return float(self.len[self.seg.query_ball_point((lon * self.mx, lat * self.my), r)].sum()) / 1000.0


def count_near(points, lon, lat, radius_m) -> int:
    mx, my = m_per_deg(lat)
    return sum(1 for (x, y) in points if math.hypot((x - lon) * mx, (y - lat) * my) <= radius_m)


# ---------------- data ----------------

def overpass_bbox(bbox, log):
    x0, y0, x1, y1 = bbox
    b = f"{y0},{x0},{y1},{x1}"
    roads = "|".join(MAIN_ROADS)
    q1 = f'[out:json][timeout:300];way["highway"~"^({roads})$"]({b});out geom;'
    data = json.loads(get(OVERPASS, urllib.parse.urlencode({"data": q1}).encode()))
    lines = [[(g["lon"], g["lat"]) for g in w.get("geometry", [])] for w in data["elements"] if w.get("geometry")]
    log(f"hotspots main-road ways {len(lines)}")
    parts = "".join(f"nwr{t}({b});" for t in DESTINATIONS)
    q2 = f"[out:json][timeout:300];({parts});out center;"
    data = json.loads(get(OVERPASS, urllib.parse.urlencode({"data": q2}).encode()))
    pts = []
    for el in data["elements"]:
        if "lon" in el:
            pts.append((el["lon"], el["lat"]))
        elif "center" in el:
            pts.append((el["center"]["lon"], el["center"]["lat"]))
    log(f"hotspots destinations {len(pts)}")
    return lines, pts


def ghsl_array(bbox, repo: Path, log):
    sys.path.insert(0, str(repo))
    sys.path.insert(0, str(repo / "tools"))
    import multicity_collect as mc  # reuses the fixed, self-checking GHSL grid
    import rasterio

    cache = Path("/tmp/cache")
    cache.mkdir(exist_ok=True)
    tif = Path("/tmp/hyd_ghsl.tif")
    total, n = mc.ghsl_clip(bbox, tif, cache)
    log(f"hotspots GHSL tiles {n}, people in box {total}")
    with rasterio.open(tif) as ds:
        a = ds.read(1).astype("float64")
        if ds.nodata is not None:
            a[a == ds.nodata] = np.nan
        return a, tuple(ds.transform)[:6]


def worldpop_array(bbox, log):
    """Windowed read over HTTP; the full India file is about 470 MB, the window a few MB."""
    import rasterio
    from rasterio.windows import from_bounds

    try:
        with rasterio.Env(GDAL_HTTP_USERAGENT="arcroad-research/1.0", GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR"):
            with rasterio.open("/vsicurl/" + WORLDPOP) as ds:
                w = from_bounds(*bbox, transform=ds.transform).round_offsets().round_lengths()
                a = ds.read(1, window=w).astype("float64")
                if ds.nodata is not None:
                    a[a == ds.nodata] = np.nan
                t = ds.window_transform(w)
                return a, tuple(t)[:6]
    except Exception as e:  # recorded; the job then says the cross-check did not run
        log(f"hotspots WorldPop unavailable: {e}")
        return None, None


# ---------------- the job ----------------

def run(log, repo: Path):
    d = json.loads(get(PLACES_URL))
    spots = d["spots"]
    city = next(c for c in d["cities"] if c["id"] == "hyderabad")
    lons = [s["a"][0] for s in spots] + [city["c"][0] - 0.22, city["c"][0] + 0.22]
    lats = [s["a"][1] for s in spots] + [city["c"][1] - 0.2, city["c"][1] + 0.2]
    bbox = (min(lons) - 0.03, min(lats) - 0.03, max(lons) + 0.03, max(lats) + 0.03)
    out = {"job": "hotspots-v1", "prereg": "docs/PREREG-hotspots.md", "status": "CANDIDATE, NOT PUBLISHED",
           "what_this_is": "Crossing-pressure proxies from where people live and where they go. Not counted traffic.",
           "started": datetime.now(UTC).isoformat(), "bbox": bbox,
           "sources": {"population": "GHSL GHS-POP R2023A E2020 3ss (EC JRC, CC BY 4.0)",
                       "cross_check": "WorldPop 2020 constrained UN-adjusted, India (CC BY 4.0)",
                       "roads_and_destinations": "OpenStreetMap via Overpass (ODbL)"}}
    pop, tr = ghsl_array(bbox, repo, log)
    wp, wtr = worldpop_array(bbox, log)
    lines, dest = overpass_bbox(bbox, log)

    near = Near(dest, lines, (bbox[1] + bbox[3]) / 2)
    places = []
    for s in spots:
        lon, lat = (s["a"][0] + s["b"][0]) / 2, (s["a"][1] + s["b"][1]) / 2
        legs = [v for v in (s.get("ab"), s.get("ba")) if v]
        excess_km = (sum(legs) / len(legs) - s["straight"]) / 1000 if legs else None
        r1 = disk_sum(pop, tr, lon, lat, CATCH_M)
        places.append({
            "id": s["id"], "level": s.get("level"),
            "residents_500m": round(disk_sum(pop, tr, lon, lat, NEAR_M)),
            "residents_1km": round(r1),
            "residents_1km_worldpop": round(disk_sum(wp, wtr, lon, lat, CATCH_M)) if wp is not None else None,
            "destinations_1km": near.count(lon, lat, CATCH_M),
            "main_road_km_1km": round(near.road_km(lon, lat, CATCH_M), 2),
            "mean_excess_detour_km": round(excess_km, 3) if excess_km is not None else None,
            "exposure_index": round(r1 * excess_km) if excess_km is not None else None,
        })
    log(f"hotspots places {len(places)}")

    rho = None
    if wp is not None:
        rho = spearman([p["residents_1km"] for p in places], [p["residents_1km_worldpop"] for p in places])
    tri = ("NOT RUN (WorldPop unavailable)" if rho is None and wp is None
           else "PASS" if rho is not None and rho >= TRIANGULATE_MIN_RHO else "FAIL")

    cells = grid_cells(bbox)
    res = np.array([disk_sum(pop, tr, x, y, CATCH_M) for x, y in cells])
    keep = res > 0
    cells = [c for c, k in zip(cells, keep, strict=False) if k]
    res = res[keep]
    dst = np.array([near.count(x, y, CATCH_M) for x, y in cells], float)
    rkm = np.array([near.road_km(x, y, CATCH_M) for x, y in cells])
    load = res / np.maximum(rkm, 0.5)   # residents per km of main road nearby
    score = (pct_rank(res) + pct_rank(dst) + pct_rank(load)) / 3
    top = np.argsort(-score)[:TOP_N]
    top_pop = set(np.argsort(-res)[:TOP_N].tolist())
    overlap = len(top_pop & set(top.tolist())) / TOP_N
    log(f"hotspots grid cells {len(cells)}, overlap with population-only {overlap:.2f}")

    out["places"] = places
    out["grid"] = {"cell_m": CELL_M, "catchment_m": CATCH_M, "cells_with_people": len(cells),
                   "top": [{"lon": round(cells[i][0], 5), "lat": round(cells[i][1], 5),
                            "residents_1km": round(float(res[i])), "destinations_1km": int(dst[i]),
                            "main_road_km_1km": round(float(rkm[i]), 2),
                            "residents_per_main_road_km": round(float(load[i])),
                            "score": round(float(score[i]), 3)} for i in top]}
    out["checks"] = {
        "triangulation_spearman_ghsl_vs_worldpop": rho, "triangulation_min": TRIANGULATE_MIN_RHO,
        "triangulation": tri,
        "top_overlap_with_population_only": round(overlap, 3),
        "roads_and_destinations_add_information": overlap <= ROAD_ADDS_INFO_MAX_OVERLAP,
    }
    out["verdict_per_prereg"] = (
        "REPORTABLE" if tri == "PASS" and overlap <= ROAD_ADDS_INFO_MAX_OVERLAP
        else "POPULATION ONLY (composite adds nothing over where people live)" if tri == "PASS"
        else "NOT REPORTABLE (population sources disagree or cross-check did not run)")
    out["finished"] = datetime.now(UTC).isoformat()
    return json.dumps(out, indent=1).encode()
