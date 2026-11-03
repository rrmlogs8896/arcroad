"""Pre-registered job: is there a public-road intersection at each place? (docs/PREREG-openings.md)

Reads the published places, queries OpenStreetMap through Overpass once per place, and writes one JSON
document. Every output is a candidate; nothing here is published until it has been reviewed.
"""
from __future__ import annotations

import json
import math
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

PLACES_URL = "https://arcroad.org/globe/data/places.json"
OVERPASS = "https://overpass-api.de/api/interpreter"
UA = "arcroad-research/1.0 (https://arcroad.org; hello@arcroad.org)"

MAIN = {"motorway", "trunk", "primary", "secondary", "tertiary"}
PUBLIC = MAIN | {"unclassified", "residential"}
AT_INTERSECTION_M = 100.0
SIGNAL_NEAR_M = 300.0
SPACING_M = 750.0
CONTROL_MIN_M, CONTROL_MAX_M = 350.0, 450.0
RADIUS_M = 900


def hav(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371008.8 * math.asin(math.sqrt(h))


def get(url, data=None, tries=4):
    for k in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=180) as r:
                return r.read()
        except Exception:
            if k == tries - 1:
                raise
            time.sleep(20 * (k + 1))


def overpass(lat, lon):
    q = f"""[out:json][timeout:120];
(way(around:{RADIUS_M},{lat},{lon})[highway];)->.w;
.w out body geom;
node(around:1500,{lat},{lon})[highway=traffic_signals];
out body;
node(around:1500,{lat},{lon})[traffic_calming];
out body;"""
    return json.loads(get(OVERPASS, urllib.parse.urlencode({"data": q}).encode()))


def nearest_way(ways, p):
    best, bd = None, 1e18
    for w in ways:
        for g in w.get("geometry", []):
            d = hav(p, (g["lat"], g["lon"]))
            if d < bd:
                best, bd = w, d
    return best, bd


def analyse(place, data):
    a = (place["a"][1], place["a"][0])
    b = (place["b"][1], place["b"][0])
    mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    ways = [e for e in data["elements"] if e["type"] == "way"]
    nodes = [e for e in data["elements"] if e["type"] == "node"]
    signals = [(e["lat"], e["lon"]) for e in nodes if e.get("tags", {}).get("highway") == "traffic_signals"]
    calming = [(e["lat"], e["lon"], e["tags"]["traffic_calming"]) for e in nodes if e.get("tags", {}).get("traffic_calming")]
    mains = [w for w in ways if w.get("tags", {}).get("highway") in MAIN]
    wa, da = nearest_way(mains, a)
    wb, db = nearest_way(mains, b)
    if not wa or not wb:
        return {"id": place["id"], "status": "NO_MAIN_ROAD"}
    seeds = {wa["id"], wb["id"]}
    cls = wa["tags"].get("highway")
    keys = {(t.get("name"), t.get("ref")) for t in (wa.get("tags", {}), wb.get("tags", {}))}
    named = any(n or r for n, r in keys)
    def same_road(w):
        t = w.get("tags", {})
        k = (t.get("name"), t.get("ref"))
        return t.get("highway") == cls and any(k) and k in keys

    divided = [w for w in ways if w["id"] in seeds or (named and same_road(w))]
    div_ids = {w["id"] for w in divided}
    div_nodes = {}
    for w in divided:
        for nid, g in zip(w.get("nodes", []), w.get("geometry", [])):
            div_nodes[nid] = (g["lat"], g["lon"])
    inter = {}
    for w in ways:
        h = w.get("tags", {}).get("highway", "")
        if w["id"] in div_ids or h not in PUBLIC:
            continue
        for nid in w.get("nodes", []):
            if nid in div_nodes:
                inter[nid] = div_nodes[nid]

    def at(p):
        ds = [hav(p, q) for q in inter.values()]
        return min(ds) if ds else None

    def count_within(p, r):
        return sum(1 for q in inter.values() if hav(p, q) <= r)

    # controls: two divided-road points 350-450 m from the midpoint, as far apart as possible
    cands = [q for q in div_nodes.values() if CONTROL_MIN_M <= hav(mid, q) <= CONTROL_MAX_M]
    controls = []
    if cands:
        c1 = cands[0]
        c2 = max(cands, key=lambda q: hav(c1, q))
        c1 = max(cands, key=lambda q: hav(c2, q))
        controls = [c1] if hav(c1, c2) < 200 else [c1, c2]
    near = at(mid)
    sig = min((hav(mid, s) for s in signals), default=None)
    return {
        "id": place["id"],
        "status": "OK",
        "road_class": cls,
        "lanes": wa.get("tags", {}).get("lanes"),
        "a_to_road_m": round(da, 1), "b_to_road_m": round(db, 1),
        "nearest_intersection_m": None if near is None else round(near, 1),
        "class": "AT_INTERSECTION" if near is not None and near <= AT_INTERSECTION_M else "MID_BLOCK",
        "intersections_within_750m": count_within(mid, SPACING_M),
        "nearest_signal_m": None if sig is None else round(sig, 1),
        "signal_nearby": sig is not None and sig <= SIGNAL_NEAR_M,
        # speed breakers and other traffic calming mapped within 750 m (descriptive; OSM maps few of them)
        "traffic_calming_within_750m": sum(1 for c in calming if hav(mid, c[:2]) <= SPACING_M),
        "traffic_calming_types": sorted({c[2] for c in calming if hav(mid, c[:2]) <= SPACING_M}),
        "controls": [{"at_intersection": (lambda d: d is not None and d <= AT_INTERSECTION_M)(at(c)),
                      "nearest_intersection_m": None if at(c) is None else round(at(c), 1)} for c in controls],
    }


def run(log):
    places = json.loads(get(PLACES_URL))["spots"]
    out = {"job": "openings-guidance-v1", "prereg": "docs/PREREG-openings.md",
           "started": datetime.now(timezone.utc).isoformat(), "source": PLACES_URL,
           "data": "OpenStreetMap via Overpass API (ODbL)", "status": "CANDIDATE, NOT PUBLISHED", "places": []}
    for i, p in enumerate(places):
        a = (p["a"][1] + p["b"][1]) / 2, (p["a"][0] + p["b"][0]) / 2
        try:
            r = analyse(p, overpass(*a))
        except Exception as e:  # recorded, never dropped silently
            r = {"id": p["id"], "status": "ERROR", "error": str(e)[:300]}
        out["places"].append(r)
        log(f"openings {i + 1}/{len(places)} {p['id']} {r.get('class', r['status'])}")
        time.sleep(6)
    ok = [r for r in out["places"] if r["status"] == "OK"]
    ctl = [c for r in ok for c in r["controls"]]
    sp = sum(r["class"] == "AT_INTERSECTION" for r in ok) / len(ok) if ok else None
    sc = sum(c["at_intersection"] for c in ctl) / len(ctl) if ctl else None
    verdict = "INCONCLUSIVE"
    if sp is not None and sc is not None:
        if sp - sc >= 0.20:
            verdict = "SUPPORTS_C (places sit at intersections more than controls)"
        elif sc - sp >= 0.20:
            verdict = "SUPPORTS_H (places are mid-block more than controls)"
    out["summary"] = {"places_ok": len(ok), "controls": len(ctl),
                      "places_at_intersection_share": sp, "controls_at_intersection_share": sc,
                      "verdict_per_prereg": verdict}
    out["finished"] = datetime.now(timezone.utc).isoformat()
    return json.dumps(out, indent=1).encode()
