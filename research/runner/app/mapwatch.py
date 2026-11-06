"""Nightly watch: has anyone edited the roads or turn rules near a place? (docs/PREREG-routercheck.md, part 2)

Asks OpenStreetMap through Overpass for road ways and turn-restriction relations within 1 km of each place
that changed in the last 48 hours (runs overlap on purpose, so a missed night loses nothing). A hit means
"re-check this place", never "the detour changed". Mapper names are not collected.
"""
from __future__ import annotations

import json
import math
import time
import urllib.parse
from datetime import UTC, datetime, timedelta

from openings import OVERPASS, PLACES_URL, get

RADIUS_M = 1000
LOOKBACK_H = 48


def query(lat, lon, since):
    return f"""[out:json][timeout:90];
(way(around:{RADIUS_M},{lat},{lon})[highway](newer:"{since}");
 relation(around:{RADIUS_M},{lat},{lon})[type=restriction](newer:"{since}");
 node(around:{RADIUS_M},{lat},{lon})[highway~"^(traffic_signals|turning_circle|turning_loop|crossing)$"](newer:"{since}"););
out meta;"""


def area_query(bbox, since):
    """One query for the whole study area; 5 Nov 2026 the per-place queries took about 10 minutes each."""
    s, w, n, e = bbox
    return f"""[out:json][timeout:300][bbox:{s},{w},{n},{e}];
(way[highway](newer:"{since}");
 relation[type=restriction](newer:"{since}");
 node[highway~"^(traffic_signals|turning_circle|turning_loop|crossing)$"](newer:"{since}"););
out meta geom;"""


def _points(el):
    if el["type"] == "node":
        return [(el["lat"], el["lon"])]
    if el["type"] == "way":
        return [(g["lat"], g["lon"]) for g in el.get("geometry") or []]
    pts = []
    for m in el.get("members", []):
        if "lat" in m:
            pts.append((m["lat"], m["lon"]))
        pts += [(g["lat"], g["lon"]) for g in m.get("geometry") or []]
    return pts


def _seg_dist_m(lat, lon, a, b):
    """Metres from (lat, lon) to the segment a-b, on a local flat projection (fine at 1 km)."""
    kx = 111_320 * math.cos(math.radians(lat))
    ax, ay = (a[1] - lon) * kx, (a[0] - lat) * 110_540
    bx, by = (b[1] - lon) * kx, (b[0] - lat) * 110_540
    dx, dy = bx - ax, by - ay
    t = 0.0 if dx == dy == 0 else max(0.0, min(1.0, -(ax * dx + ay * dy) / (dx * dx + dy * dy)))
    return math.hypot(ax + t * dx, ay + t * dy)


def near(el, lat, lon, radius=RADIUS_M):
    """Same meaning as Overpass around:radius: any part of the element within radius of the point."""
    pts = _points(el)
    if not pts:
        return False
    if len(pts) == 1 or el["type"] == "relation":
        return any(_seg_dist_m(lat, lon, p, p) <= radius for p in pts) or (
            el["type"] == "relation" and any(_seg_dist_m(lat, lon, pts[i], pts[i + 1]) <= radius
                                             for i in range(len(pts) - 1)))
    return any(_seg_dist_m(lat, lon, pts[i], pts[i + 1]) <= radius for i in range(len(pts) - 1))


def summarise(el):
    t = el.get("tags", {})
    return {"type": el["type"], "id": el["id"], "version": el.get("version"), "timestamp": el.get("timestamp"),
            "changeset": el.get("changeset"),
            "what": t.get("restriction") or t.get("highway") or t.get("type")}


def run(log):
    spots = json.loads(get(PLACES_URL))["spots"]
    since = (datetime.now(UTC) - timedelta(hours=LOOKBACK_H)).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = {"job": "mapwatch-v1", "since": since, "radius_m": RADIUS_M,
           "data": "OpenStreetMap via Overpass (ODbL)", "status": "INTERNAL: re-check list, not published",
           "places": []}
    def one(s):
        lat, lon = (s["a"][1] + s["b"][1]) / 2, (s["a"][0] + s["b"][0]) / 2
        try:
            d = json.loads(get(OVERPASS, urllib.parse.urlencode({"data": query(lat, lon, since)}).encode()))
            edits = [summarise(e) for e in d.get("elements", [])]
            return {"id": s["id"], "edits": edits, "recheck": bool(edits)}
        except Exception as e:
            return {"id": s["id"], "error": str(e)[:200], "recheck": None}

    centres = [((s["a"][1] + s["b"][1]) / 2, (s["a"][0] + s["b"][0]) / 2) for s in spots]
    pad = 0.012   # a little over 1 km
    bbox = (min(c[0] for c in centres) - pad, min(c[1] for c in centres) - pad,
            max(c[0] for c in centres) + pad, max(c[1] for c in centres) + pad)
    try:
        d = json.loads(get(OVERPASS, urllib.parse.urlencode({"data": area_query(bbox, since)}).encode()))
        els = d.get("elements", [])
        log(f"mapwatch one query: {len(els)} edited elements in the area")
        for s, (lat, lon) in zip(spots, centres, strict=True):
            edits = [summarise(e) for e in els if near(e, lat, lon)]
            out["places"].append({"id": s["id"], "edits": edits, "recheck": bool(edits)})
            log(f"mapwatch {s['id']} {len(edits)} edits")
    except Exception as e:   # fall back to the slower per-place queries
        log(f"mapwatch area query failed ({str(e)[:80]}); asking place by place")
        out["places"] = []
        for s in spots:
            row = one(s)
            out["places"].append(row)
            log(f"mapwatch {s['id']} {len(row.get('edits', []))} edits")
            time.sleep(5)
    for k, s in enumerate(spots):   # one more try at the end for places the server dropped
        if "error" in out["places"][k]:
            time.sleep(60)
            row = one(s)
            if "error" not in row:
                out["places"][k] = row
                log(f"mapwatch retry {s['id']} {len(row['edits'])} edits")
    out["recheck"] = [p["id"] for p in out["places"] if p.get("recheck")]
    out["finished"] = datetime.now(UTC).isoformat()
    return json.dumps(out, indent=1).encode()
