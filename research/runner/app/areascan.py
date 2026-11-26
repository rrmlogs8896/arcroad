"""Pre-registered (docs/PREREG-areascan.md): refresh the "Worst areas measured" table on the latest map.

Same method as the published table, nothing re-tuned: pipeline/ pairing with the V10 config over the
declared HMDA box, routed on our own graph of the latest OpenStreetMap extract, then the Area Atlas
rules (nearest named place within 3 km, at least 30 points, median Detour Index). New in v1: a
three-router check. For the worst areas, a fixed random sample of points is routed again on two
independent public routers (OSRM and Valhalla), so each published area figure is backed by three
engines, or flagged where they disagree. Output is a CANDIDATE; nothing is published until reviewed.
"""
from __future__ import annotations

import json
import math
import random
import subprocess
import sys
import time
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

VERSION = "areascan-v1"
BUFFER_DEG = 0.20          # clip wider than we measure, as the notebook (F-3)
PLACE_MAX_M = 3000.0       # a point further than this from any named place is unassigned
MIN_AREA_N = 30            # below this an area's median is noise
GAP_M = 10000.0            # a typical route past 10 km is flagged as a likely map gap
TOP_AREAS = 15             # areas given the three-router check
CHECK_PER_AREA = 10        # points per area, fixed seed
SEED = 26
AGREE_TOL = 0.25           # an area "agrees" when both routers' medians sit within 25% of ours
GEOFABRIK_INDEX = "https://download.geofabrik.de/index-v1.json"


def _median(v):
    v = sorted(x for x in v if x is not None)
    if not v:
        return None
    n = len(v)
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2


def atlas(points, places, lat0, place_max_m=PLACE_MAX_M, min_n=MIN_AREA_N):
    """points: dicts with lat, lon, detour_index, network_m. places: (name, kind, lon, lat).
    Returns areas sorted worst first, each with its member points (for the router check)."""
    import numpy as np
    from scipy.spatial import cKDTree
    if not points or not places:
        return []
    kx = 111320.0 * math.cos(math.radians(lat0))
    pxy = np.array([[p[2] * kx, p[3] * 110540.0] for p in places])
    qxy = np.array([[r["lon"] * kx, r["lat"] * 110540.0] for r in points])
    dist, idx = cKDTree(pxy).query(qxy)
    groups = {}
    for r, d, i in zip(points, dist, idx, strict=True):
        if d <= place_max_m:
            groups.setdefault(places[i][0], {"kind": places[i][1], "pts": []})["pts"].append(r)
    rows = []
    for name, g in groups.items():
        pts = g["pts"]
        if len(pts) < min_n:
            continue
        di = _median([p["detour_index"] for p in pts])
        net = _median([p["network_m"] for p in pts])
        rows.append({"area": name, "kind": g["kind"], "points": len(pts), "median_di": round(di, 1),
                     "median_network_m": round(net), "map_gap_likely": bool(net and net > GAP_M), "_pts": pts})
    rows.sort(key=lambda x: -x["median_di"])
    return rows


def three_router(rows, log, top=TOP_AREAS, per=CHECK_PER_AREA):
    from entryscan import osrm, route, valhalla
    rng = random.Random(SEED)
    for row in rows[:top]:
        pts = sorted(row["_pts"], key=lambda p: (p["lat"], p["lon"]))
        sample = rng.sample(pts, min(per, len(pts)))
        own, o, v = [], [], []
        for p in sample:
            a, b = (p["a_lat"], p["a_lon"]), (p["b_lat"], p["b_lon"])
            own.append(p["network_m"])
            o.append(route(osrm, a, b)); time.sleep(1.5)
            v.append(route(valhalla, a, b)); time.sleep(1.5)
        mo, mr, mv = _median(own), _median(o), _median(v)
        ok = [x for x in (mr, mv) if x is not None]
        row["check"] = {"points": len(sample), "own_median_m": mo and round(mo),
                        "osrm_median_m": mr and round(mr), "valhalla_median_m": mv and round(mv),
                        "osrm_answered": sum(x is not None for x in o),
                        "valhalla_answered": sum(x is not None for x in v),
                        "three_way_median_m": round(_median([mo, mr, mv])) if mo and ok else None,
                        "agree": bool(mo and len(ok) == 2 and all(abs(x - mo) <= AGREE_TOL * mo for x in ok))}
        log(f"areascan: {row['area']}: own {row['check']['own_median_m']} osrm {row['check']['osrm_median_m']} "
            f"valhalla {row['check']['valhalla_median_m']} agree={row['check']['agree']}")
    return rows


def fetch(bbox, work: Path, log):
    """Geofabrik zones covering the box, clipped with osmium. Returns (pbf, extract date)."""
    from shapely.geometry import box, shape
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from entryscan import get
    work.mkdir(parents=True, exist_ok=True)
    feats = json.loads(get(GEOFABRIK_INDEX))["features"]
    b = box(*bbox)
    zones = [(f["properties"]["id"], f["properties"]["urls"]["pbf"]) for f in feats
             if "/asia/india/" in f["properties"].get("urls", {}).get("pbf", "") and shape(f["geometry"]).intersects(b)]
    parts, date = [], None
    import osmium
    for zid, url in zones:
        src = work / f"{zid}.osm.pbf"
        if not src.exists():
            log(f"areascan: downloading {zid}")
            urllib.request.urlretrieve(url, src)
        rd = osmium.io.Reader(str(src), osmium.osm.osm_entity_bits.NOTHING)
        date = date or rd.header().get("osmosis_replication_timestamp")
        rd.close()
        dst = work / f"{zid}-box.osm.pbf"
        subprocess.run(["osmium", "extract", "-b", ",".join(map(str, bbox)), str(src), "-o", str(dst),
                        "--overwrite", "-s", "complete_ways"], check=True)
        src.unlink(missing_ok=True)
        parts.append(dst)
    out = work / "hmda_buffered.osm.pbf"
    if len(parts) == 1:
        parts[0].rename(out)
    else:
        subprocess.run(["osmium", "merge", *map(str, parts), "-o", str(out), "--overwrite"], check=True)
    return out, date


def run(log, repo: Path, work=Path("/tmp/areascan")):
    sys.path.insert(0, str(repo))
    from pipeline import pairing
    started = datetime.now(UTC).isoformat()
    bbox = pairing.HMDA_BBOX
    b = BUFFER_DEG
    pbf, date = fetch((bbox[0] - b, bbox[1] - b, bbox[2] + b, bbox[3] + b), work, log)
    log(f"areascan: extract dated {date}, parsing")
    g = pairing.load_network(str(pbf))
    sha = (repo / "COMMIT").read_text().strip() if (repo / "COMMIT").exists() else None
    log(f"areascan: {len(g.ways):,} ways, {len(g.places):,} named places; pairing and routing (V10)")
    res = pairing.run_pairing(g.ways, g.coords, config=pairing.V10, study_bbox=bbox,
                              osm_extract_date=date, sha=sha)
    routed = [r for r in res.records if r["detour_index"] is not None and not r["diff_component"]]
    log(f"areascan: {len(res.records):,} pairs, {len(routed):,} routed; building the area table")
    lat0 = (bbox[1] + bbox[3]) / 2
    rows = atlas(routed, g.places, lat0)
    del g
    rows = three_router(rows, log)
    for r in rows:
        r.pop("_pts", None)
    meta = {k: v for k, v in res.meta.items() if k != "config"}
    meta["null_routes"] = dict(meta.get("null_routes") or {})
    out = {"job": VERSION, "prereg": "docs/PREREG-areascan.md", "status": "CANDIDATE, NOT PUBLISHED",
           "started": started, "finished": datetime.now(UTC).isoformat(), "osm_extract_date": date,
           "commit": sha, "study_bbox": list(bbox), "routers": ["own graph (scipy Dijkstra on OSM)",
           "OSRM public demo server", "Valhalla (FOSSGIS public server)"],
           "rules": {"place_max_m": PLACE_MAX_M, "min_area_n": MIN_AREA_N, "gap_m": GAP_M,
                     "top_checked": TOP_AREAS, "per_area": CHECK_PER_AREA, "agree_tol": AGREE_TOL, "seed": SEED},
           "routed_points": len(routed), "areas_total": len(rows), "meta": meta, "areas": rows[:60],
           "source": "Map data (c) OpenStreetMap contributors, ODbL. Distance and geometry only."}
    return json.dumps(out, indent=1, default=str).encode()
