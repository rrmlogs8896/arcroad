"""Pre-registered job: entries that make residents drive past their own road (docs/PREREG-entryscan.md).

For every residential side road that joins only one carriageway of a divided main road, measures how far a
resident arriving on the OTHER carriageway must drive to turn into it: past the entry to the next legal U-turn
and back. Ranks the entries by extra distance and by how many homes lie behind them. Benchmark: the entry
near Isnapur X Road on NH-65, driven privately at about 3.4 km extra. Output is a private candidate list,
never published as is.
"""
from __future__ import annotations

import json
import math
import os
import subprocess
import time
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import osmium
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree

VERSION = "entryscan-v1"
BOX = tuple(float(x) for x in os.environ.get("ES_BOX", "78.15,17.38,78.52,17.62").split(","))  # Cyberabad and the NH-65 corridor to Isnapur
DRIVABLE = {"motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link", "secondary",
            "secondary_link", "tertiary", "tertiary_link", "unclassified", "residential", "living_street", "service"}
MAIN = {"trunk", "primary", "secondary"}  # divided main roads studied; motorways (ORR) are out of scope
SIDE = {"residential", "unclassified", "living_street", "service", "tertiary"}
HOME_TAGS = {"apartments", "residential", "house", "detached", "terrace", "dormitory", "semidetached_house"}
OPP_MIN_M, OPP_MAX_M = 6.0, 60.0          # the other carriageway must lie this far across
OPP_ANGLE = 135.0                         # and run the opposite way (bearing difference, degrees)
MIN_EXTRA_M = 1000.0                      # pre-registered floor for a candidate
HOMES_RADIUS_M = 400.0                    # homes counted on the entry's side within this radius
CLUSTER_M = 150.0                         # entries this close on one carriageway count once (the worst kept)
LIMIT_M = 12000.0                         # longest detour searched
TOP_N = 20
BENCH = {"name": "societies near Isnapur X Road (NH-65)", "lat": 17.55322, "lon": 78.19693, "extra_m": 3400}
BENCH_TOL = 0.25                          # method check passes if the benchmark is found within 25%
OSRM = "https://router.project-osrm.org/route/v1/driving/"
VALHALLA = "https://valhalla1.openstreetmap.de/route"
GEOFABRIK_INDEX = "https://download.geofabrik.de/index-v1.json"


def hav(lat1, lon1, lat2, lon2):
    p = math.radians
    a = math.sin(p(lat2 - lat1) / 2) ** 2 + math.cos(p(lat1)) * math.cos(p(lat2)) * math.sin(p(lon2 - lon1) / 2) ** 2
    return 2 * 6371000 * math.asin(math.sqrt(a))


def get(url, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "arcroad-research (hello@arcroad.org)"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(10 * 2 ** i)


def fetch_extract(work: Path, log) -> Path:
    """Geofabrik zones that cover the box, clipped to it with osmium."""
    from shapely.geometry import box, shape
    work.mkdir(parents=True, exist_ok=True)
    feats = json.loads(get(GEOFABRIK_INDEX))["features"]
    b = box(*BOX)
    zones = [(f["properties"]["id"], f["properties"]["urls"]["pbf"]) for f in feats
             if "/asia/india/" in f["properties"].get("urls", {}).get("pbf", "") and shape(f["geometry"]).intersects(b)]
    parts = []
    for zid, url in zones:
        src = work / f"{zid}.osm.pbf"
        if not src.exists():
            log(f"entryscan: downloading {zid}")
            urllib.request.urlretrieve(url, src)
        dst = work / f"{zid}-box.osm.pbf"
        subprocess.run(["osmium", "extract", "-b", ",".join(map(str, BOX)), str(src), "-o", str(dst),
                        "--overwrite", "-s", "complete_ways"], check=True)
        src.unlink(missing_ok=True)          # keep the 4 GB container's disk free
        parts.append(dst)
    out = work / "box.osm.pbf"
    if len(parts) == 1:
        parts[0].rename(out)
    else:
        subprocess.run(["osmium", "merge", *map(str, parts), "-o", str(out), "--overwrite"], check=True)
    return out


class Reader(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.ways = []          # (way id, highway, node ids, oneway: 1 forward, -1 backward, 0 both)
        self.loc = {}           # node id -> (lat, lon)
        self.homes = []         # (lat, lon, weight)

    def way(self, w):
        t = w.tags
        hw = t.get("highway")
        if hw in DRIVABLE and t.get("access") not in ("private", "no") and t.get("service") not in ("parking_aisle", "driveway"):
            ow = t.get("oneway", "")
            one = 1 if (ow in ("yes", "1", "true") or t.get("junction") == "roundabout" or hw == "motorway") else (-1 if ow == "-1" else 0)
            nodes = []
            for n in w.nodes:
                if n.location.valid():
                    self.loc[n.ref] = (n.location.lat, n.location.lon)
                    nodes.append(n.ref)
            if len(nodes) > 1:
                self.ways.append((w.id, hw, nodes, one))
            return
        b = t.get("building")
        if b in HOME_TAGS or (t.get("landuse") == "residential"):
            pts = [(n.location.lat, n.location.lon) for n in w.nodes if n.location.valid()]
            if pts:
                lat = sum(p[0] for p in pts) / len(pts)
                lon = sum(p[1] for p in pts) / len(pts)
                if b:
                    weight = 10.0 if b in ("apartments", "dormitory") else 1.0
                else:  # residential land: one home-equivalent per 1,000 m2 of its rough bounding area
                    la = [p[0] for p in pts]; lo = [p[1] for p in pts]
                    area = hav(min(la), min(lo), max(la), min(lo)) * hav(min(la), min(lo), min(la), max(lo))
                    weight = min(area / 1000.0, 200.0)
                self.homes.append((lat, lon, weight))


def bearing(a, b):
    y = math.sin(math.radians(b[1] - a[1])) * math.cos(math.radians(b[0]))
    x = math.cos(math.radians(a[0])) * math.sin(math.radians(b[0])) - math.sin(math.radians(a[0])) * math.cos(math.radians(b[0])) * math.cos(math.radians(b[1] - a[1]))
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def angdiff(a, b):
    d = abs(a - b) % 360
    return 360 - d if d > 180 else d


def xy(lat, lon, lat0):
    return (lon * 111320 * math.cos(math.radians(lat0)), lat * 110540)


def build(r: Reader):
    ids = {}
    def idx(n):
        if n not in ids:
            ids[n] = len(ids)
        return ids[n]
    rows, cols, wts = [], [], []
    for _, hw, nodes, one in r.ways:
        for a, b in zip(nodes, nodes[1:]):
            d = hav(*r.loc[a], *r.loc[b])
            ia, ib = idx(a), idx(b)
            if one >= 0:
                rows.append(ia); cols.append(ib); wts.append(d)
            if one <= 0:
                rows.append(ib); cols.append(ia); wts.append(d)
    n = len(ids)
    g = csr_matrix((wts, (rows, cols)), shape=(n, n))
    return g, ids


def entries_and_opposites(r: Reader, ids):
    lat0 = (BOX[1] + BOX[3]) / 2
    carriage = [(wid, nodes) for wid, hw, nodes, one in r.ways if hw in MAIN and one == 1]
    seg_pts, seg_meta = [], []          # densified carriageway points every ~10 m: (way, u, v, bearing)
    on_carriage = {}
    for wid, nodes in carriage:
        for a, b in zip(nodes, nodes[1:]):
            pa, pb = r.loc[a], r.loc[b]
            br = bearing(pa, pb)
            d = hav(*pa, *pb)
            k = max(1, int(d // 10))
            for i in range(k + 1):
                f = i / k
                p = (pa[0] + (pb[0] - pa[0]) * f, pa[1] + (pb[1] - pa[1]) * f)
                seg_pts.append(xy(*p, lat0)); seg_meta.append((wid, a, b, br, f, d, p))
            on_carriage.setdefault(a, []).append((wid, br, b))
            on_carriage.setdefault(b, []).append((wid, br, None))
    tree = cKDTree(np.array(seg_pts))
    side_first = {}
    for wid, hw, nodes, one in r.ways:
        if hw not in SIDE:
            continue
        for end, nxt in ((nodes[0], nodes[1]), (nodes[-1], nodes[-2])):
            if end in on_carriage:
                inbound_ok = one == 0 or (one == 1 and end == nodes[0]) or (one == -1 and end == nodes[-1])
                if inbound_ok:
                    side_first.setdefault(end, []).append((wid, nxt))
    out = []
    for j, sides in side_first.items():
        jl = r.loc[j]
        cw, cbr, _ = on_carriage[j][0]
        hits = tree.query_ball_point(xy(*jl, lat0), OPP_MAX_M)
        best = None
        for h in hits:
            wid, u, v, br, f, seglen, p = seg_meta[h]
            if wid == cw or angdiff(br, cbr) < OPP_ANGLE:
                continue
            d = hav(*jl, *p)
            if d < OPP_MIN_M:
                continue
            if best is None or d < best[0]:
                best = (d, u, v, f, seglen, p, br)
        if best is None:
            continue
        for sw, k in sides:
            out.append({"j": j, "k": k, "side_way": sw, "carriageway": cw, "bearing": cbr,
                        "across_m": best[0], "opp_v": best[2], "opp_rest_m": (1 - best[3]) * best[4],
                        "opp_point": best[5]})
    return out


def homes_behind(r: Reader, e, tree, wts, lat0):
    jl = r.loc[e["j"]]
    op = e["opp_point"]
    hits = tree.query_ball_point(xy(*jl, lat0), HOMES_RADIUS_M)
    if not hits:
        return 0.0
    # Homes on the entry's side of the main road: opposite sign to the other carriageway's side.
    br = math.radians(e["bearing"])
    dx, dy = math.sin(br), math.cos(br)
    jx, jy = xy(*jl, lat0)
    ox, oy = xy(*op, lat0)
    opp_side = dx * (oy - jy) - dy * (ox - jx)
    total = 0.0
    pts = tree.data
    for h in hits:
        hx, hy = pts[h]
        s = dx * (hy - jy) - dy * (hx - jx)
        if s * opp_side < 0:
            total += wts[h]
    return total


def route(fn, a, b):
    try:
        return fn(a, b)
    except Exception:
        return None


def osrm(a, b):
    q = urllib.parse.urlencode({"overview": "false", "radiuses": "25;25", "continue_straight": "true"})
    d = json.loads(get(OSRM + f"{a[1]},{a[0]};{b[1]},{b[0]}?" + q))
    return d["routes"][0]["distance"] if d.get("code") == "Ok" and d.get("routes") else None


def valhalla(a, b):
    body = {"locations": [{"lon": a[1], "lat": a[0], "radius": 25}, {"lon": b[1], "lat": b[0], "radius": 25}],
            "costing": "auto", "units": "kilometers", "directions_type": "none"}
    d = json.loads(get(VALHALLA + "?json=" + urllib.parse.quote(json.dumps(body))))
    return d["trip"]["summary"]["length"] * 1000 if "trip" in d else None


def scan(pbf: Path, log, cross_check=True):
    r = Reader()
    r.apply_file(str(pbf), locations=True)
    log(f"entryscan: {len(r.ways)} drivable ways, {len(r.homes)} home features")
    g, ids = build(r)
    ents = entries_and_opposites(r, ids)
    log(f"entryscan: {len(ents)} one-sided entries with an opposite carriageway")
    lat0 = (BOX[1] + BOX[3]) / 2
    hp = np.array([xy(h[0], h[1], lat0) for h in r.homes]) if r.homes else np.zeros((1, 2))
    hw = [h[2] for h in r.homes] or [0.0]
    htree = cKDTree(hp)
    rows = []
    B = 32
    for s in range(0, len(ents), B):
        batch = ents[s:s + B]
        src = [ids[e["opp_v"]] for e in batch]
        dist = dijkstra(g, directed=True, indices=src, limit=LIMIT_M)
        for e, drow in zip(batch, dist):
            dk = drow[ids[e["k"]]]
            if not np.isfinite(dk):
                continue
            driven = e["opp_rest_m"] + float(dk)
            kl = r.loc[e["k"]]
            straight = hav(*e["opp_point"], *kl)
            extra = driven - straight
            if extra < MIN_EXTRA_M:
                continue
            jl = r.loc[e["j"]]
            rows.append({"lat": round(jl[0], 5), "lon": round(jl[1], 5), "carriageway": e["carriageway"],
                         "across_m": round(e["across_m"], 1), "driven_m": round(driven), "extra_m": round(extra),
                         "homes_index": round(homes_behind(r, e, htree, hw, lat0), 1),
                         "from": [round(e["opp_point"][0], 6), round(e["opp_point"][1], 6)],
                         "to": [round(kl[0], 6), round(kl[1], 6)]})
    # One per carriageway cluster: the worst entry kept.
    rows.sort(key=lambda x: -x["extra_m"])
    kept = []
    for x in rows:
        if any(y["carriageway"] == x["carriageway"] and hav(x["lat"], x["lon"], y["lat"], y["lon"]) < CLUSTER_M for y in kept):
            continue
        kept.append(x)
    for x in kept:
        x["score"] = round(x["extra_m"] / 1000 * math.log1p(x["homes_index"]), 2)
    kept.sort(key=lambda x: -x["score"])
    bench = min(kept, key=lambda x: hav(x["lat"], x["lon"], BENCH["lat"], BENCH["lon"]), default=None)
    bench_d = hav(bench["lat"], bench["lon"], BENCH["lat"], BENCH["lon"]) if bench else None
    check = {"benchmark": BENCH, "nearest_found": bench, "nearest_distance_m": round(bench_d) if bench_d is not None else None}
    check["passed"] = bool(bench and bench_d < 200 and abs(bench["extra_m"] - BENCH["extra_m"]) <= BENCH_TOL * BENCH["extra_m"])
    top = kept[:TOP_N]
    if cross_check:
        for x in top:
            a, b = tuple(x["from"]), tuple(x["to"])
            x["osrm_m"] = route(osrm, a, b); time.sleep(1.5)
            x["valhalla_m"] = route(valhalla, a, b); time.sleep(1.5)
    return {"candidates_total": len(kept), "top": top, "method_check": check}


def run(log, work=Path("/tmp/entryscan")):
    started = datetime.now(UTC).isoformat()
    pbf = fetch_extract(work, log)
    res = scan(pbf, log)
    out = {"job": VERSION, "prereg": "docs/PREREG-entryscan.md", "status": "CANDIDATE, NOT PUBLISHED",
           "started": started, "finished": datetime.now(UTC).isoformat(), "box": BOX,
           "source": "OpenStreetMap via Geofabrik (ODbL)", **res}
    return json.dumps(out, indent=1).encode()


if __name__ == "__main__":
    import sys
    print(json.dumps(scan(Path(sys.argv[1]), print, cross_check=False), indent=1))
