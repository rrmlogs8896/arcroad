"""Pre-registered job: fixed structures standing in a road's median (docs/PREREG-structures.md).

Finds mapped structures that sit between the two carriageways of a divided main road: places of
worship of every faith, statues and memorials, police posts, transformers and similar. A structure in
the median is a fixed reason an opening cannot be placed there. The job reports where they are and
whether arcroad's places with one nearby have longer detours than places without, against controls.

Neutral by design: every faith and every kind of structure is counted the same way. The public site
shows only the total of all kinds together; the breakdown by kind and the locations stay internal.
"""
from __future__ import annotations

import itertools
import json
import math
import urllib.parse
from datetime import UTC, datetime

from openings import OVERPASS, PLACES_URL, get

MAIN = ("motorway", "trunk", "primary", "secondary")
KINDS = [
    ('["amenity"="place_of_worship"]', "place_of_worship"),
    ('["historic"~"^(memorial|monument|wayside_shrine|wayside_cross)$"]', "memorial_or_shrine"),
    ('["tourism"="artwork"]["artwork_type"="statue"]', "statue"),
    ('["amenity"="police"]', "police_post"),
    ('["power"~"^(transformer|substation)$"]', "power_equipment"),
]
SIDE_M = 30.0        # each carriageway centreline within this distance of the structure
NEAR_PLACE_M = 500.0  # a place counts as "with a structure" if one is within this distance
MIN_GROUP = 4         # pre-registered: no comparison with fewer places in either group


def xy(lat0, lat, lon):
    return lon * 111320.0 * math.cos(math.radians(lat0)), lat * 110574.0


def seg_dist(p, a, b):
    """Distance from point p to segment ab, all (x, y) in metres; also the segment direction."""
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
    qx, qy = ax + t * dx, ay + t * dy
    return math.hypot(p[0] - qx, p[1] - qy), (dx, dy)


def in_median(pt, carriageways, lat0):
    """True if two one-way carriageways run in opposite directions on either side of pt, each within SIDE_M.

    carriageways: list of polylines [(lat, lon), ...] already in travel order (one-way ways)."""
    p = xy(lat0, *pt)
    near = []
    for line in carriageways:
        best = None
        for a, b in itertools.pairwise(line):
            d, v = seg_dist(p, xy(lat0, *a), xy(lat0, *b))
            if best is None or d < best[0]:
                best = (d, v, xy(lat0, *a))
        if best and best[0] <= SIDE_M:
            near.append(best)
    for i in range(len(near)):
        for j in range(i + 1, len(near)):
            (_, v1, a1), (_, v2, a2) = near[i], near[j]
            n1, n2 = math.hypot(*v1), math.hypot(*v2)
            if not n1 or not n2:
                continue
            if (v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2) > -0.8:   # not opposite directions
                continue
            # opposite sides: the cross products of p relative to each line have the same sign when the
            # lines run in opposite directions and p lies between them
            c1 = v1[0] * (p[1] - a1[1]) - v1[1] * (p[0] - a1[0])
            c2 = v2[0] * (p[1] - a2[1]) - v2[1] * (p[0] - a2[0])
            if c1 * c2 > 0:
                return True
    return False


def query(bbox):
    s, w, n, e = bbox[1], bbox[0], bbox[3], bbox[2]
    b = f"{s},{w},{n},{e}"
    roads = "|".join(MAIN)
    parts = "".join(f"nwr{t}({b});" for t, _ in KINDS)
    q = (f'[out:json][timeout:300];way["highway"~"^({roads})$"]["oneway"~"^(yes|-1)$"]({b})->.r;'
         f".r out geom;({parts});out center tags;")
    return json.loads(get(OVERPASS, urllib.parse.urlencode({"data": q}).encode()))


def kind_of(tags):
    if tags.get("amenity") == "place_of_worship":
        return "place_of_worship"
    if tags.get("historic") in ("memorial", "monument", "wayside_shrine", "wayside_cross"):
        return "memorial_or_shrine"
    if tags.get("tourism") == "artwork":
        return "statue"
    if tags.get("amenity") == "police":
        return "police_post"
    return "power_equipment"


def run(log, city_id="hyderabad"):
    d = json.loads(get(PLACES_URL))
    spots = d["spots"]
    city = next(c for c in d["cities"] if c["id"] == city_id)
    lons = [s["a"][0] for s in spots] + [city["c"][0] - 0.22, city["c"][0] + 0.22]
    lats = [s["a"][1] for s in spots] + [city["c"][1] - 0.2, city["c"][1] + 0.2]
    bbox = (min(lons) - 0.03, min(lats) - 0.03, max(lons) + 0.03, max(lats) + 0.03)
    lat0 = (bbox[1] + bbox[3]) / 2
    data = query(bbox)
    lines, found = [], []
    for el in data["elements"]:
        if el["type"] == "way" and "geometry" in el and el.get("tags", {}).get("highway"):
            pts = [(g["lat"], g["lon"]) for g in el["geometry"]]
            if el["tags"].get("oneway") == "-1":
                pts.reverse()
            lines.append(pts)
    log(f"structures carriageways {len(lines)}")
    for el in data["elements"]:
        t = el.get("tags", {})
        if el["type"] == "way" and t.get("highway"):
            continue
        if "lat" in el:
            c = (el["lat"], el["lon"])
        elif "center" in el:
            c = (el["center"]["lat"], el["center"]["lon"])
        else:
            continue
        if in_median(c, lines, lat0):
            found.append({"osm": f"{el['type']}/{el['id']}", "kind": kind_of(t), "lat": round(c[0], 6), "lon": round(c[1], 6)})
    log(f"structures in medians {len(found)}")

    def near(s):
        la, lo = (s["a"][1] + s["b"][1]) / 2, (s["a"][0] + s["b"][0]) / 2
        mx, my = xy(lat0, la, lo)
        n = 0
        for f in found:
            fx, fy = xy(lat0, f["lat"], f["lon"])
            n += math.hypot(fx - mx, fy - my) <= NEAR_PLACE_M
        return n

    rows = []
    for s in spots:
        legs = [v for v in (s.get("ab"), s.get("ba")) if v]
        rows.append({"id": s["id"], "structures_500m": near(s),
                     "mean_detour_m": round(sum(legs) / len(legs), 1) if legs else None})
    w = [r["mean_detour_m"] for r in rows if r["structures_500m"] and r["mean_detour_m"]]
    wo = [r["mean_detour_m"] for r in rows if not r["structures_500m"] and r["mean_detour_m"]]

    def med(v):
        v = sorted(v)
        return None if not v else (v[len(v) // 2] if len(v) % 2 else (v[len(v) // 2 - 1] + v[len(v) // 2]) / 2)

    comparison = ("NOT ENOUGH PLACES" if len(w) < MIN_GROUP or len(wo) < MIN_GROUP else
                  {"with_structure_n": len(w), "with_structure_median_m": med(w),
                   "without_n": len(wo), "without_median_m": med(wo)})
    by_kind = {}
    for f in found:
        by_kind[f["kind"]] = by_kind.get(f["kind"], 0) + 1
    out = {"job": "structures-v1", "prereg": "docs/PREREG-structures.md", "status": "INTERNAL, NOT PUBLISHED",
           "started": datetime.now(UTC).isoformat(), "bbox": bbox,
           "data": "OpenStreetMap via Overpass (ODbL)",
           "public_summary": {"structures_in_medians_all_kinds": len(found)},
           "internal": {"by_kind": by_kind, "structures": found, "places": rows, "comparison": comparison},
           "finished": datetime.now(UTC).isoformat()}
    return json.dumps(out, indent=1).encode()
