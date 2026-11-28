"""Fetch test for the rider-fuel study (approved by Rohit 28 Nov 2026). Inventory only, no routing.

Downloads the Geofabrik zone(s) covering the HMDA box, clips with osmium (same fetch as areascan), and counts
what the study will need: divided major roads, short links that join two one-way major roads (median-opening
candidates), food and grocery outlets, and buildings. Nothing here is published; it only proves the fetch works
and sizes the full run.
"""
from __future__ import annotations

import json
import math
import sys
from datetime import UTC, datetime
from pathlib import Path

VERSION = "fueltest-v1"
MAJOR = {"trunk", "primary", "secondary", "trunk_link", "primary_link", "secondary_link"}
LINK_MAX_M = 60.0
FOOD = {"restaurant", "fast_food", "cafe"}
SHOPS = {"supermarket", "convenience", "grocery"}


def hav(lat1, lon1, lat2, lon2):
    p = math.pi / 180
    a = math.sin((lat2 - lat1) * p / 2) ** 2 + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2
    return 12742000 * math.asin(math.sqrt(a))


def run(log, repo: Path, work=Path("/tmp/fueltest")):
    sys.path.insert(0, str(repo))
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import osmium
    from areascan import fetch
    from pipeline import pairing
    started = datetime.now(UTC).isoformat()
    bbox = pairing.HMDA_BBOX
    pbf, date = fetch(bbox, work, log)
    log(f"fueltest: extract dated {date}, {pbf.stat().st_size / 1e6:.0f} MB clipped")

    class Pass1(osmium.SimpleHandler):
        def __init__(self):
            super().__init__()
            self.oneway_major_km = 0.0
            self.dual_tagged = 0
            self.major_ways = 0
            self.node_owner = {}
            self.food = self.shops = self.buildings = 0

        def node(self, n):
            t = n.tags
            if t.get("amenity") in FOOD:
                self.food += 1
            if t.get("shop") in SHOPS:
                self.shops += 1

        def way(self, w):
            t = w.tags
            if "building" in t:
                self.buildings += 1
                if t.get("amenity") in FOOD:
                    self.food += 1
                if t.get("shop") in SHOPS:
                    self.shops += 1
                return
            if t.get("highway") not in MAJOR:
                return
            self.major_ways += 1
            if t.get("dual_carriageway") == "yes":
                self.dual_tagged += 1
            if t.get("oneway") not in ("yes", "1", "-1"):
                return
            pts = [(nd.lat, nd.lon) for nd in w.nodes if nd.location.valid()]
            self.oneway_major_km += sum(hav(*pts[i], *pts[i + 1]) for i in range(len(pts) - 1)) / 1000
            for nd in w.nodes:
                self.node_owner.setdefault(nd.ref, set()).add(w.id)

    h1 = Pass1()
    h1.apply_file(str(pbf), locations=True)
    log(f"fueltest: {h1.major_ways:,} major ways, {h1.oneway_major_km:,.0f} km one-way major carriageway")

    class Pass2(osmium.SimpleHandler):
        def __init__(self, owner):
            super().__init__()
            self.owner = owner
            self.links = 0

        def way(self, w):
            if "highway" not in w.tags or len(w.nodes) < 2:
                return
            a, b = w.nodes[0], w.nodes[-1]
            if not (a.location.valid() and b.location.valid()):
                return
            oa, ob = self.owner.get(a.ref), self.owner.get(b.ref)
            if not oa or not ob or w.id in oa or w.id in ob or oa & ob:
                return
            if hav(a.lat, a.lon, b.lat, b.lon) <= LINK_MAX_M:
                self.links += 1

    h2 = Pass2(h1.node_owner)
    h2.apply_file(str(pbf), locations=True)
    out = {"job": VERSION, "status": "FETCH TEST, NOT PUBLISHED", "started": started,
           "finished": datetime.now(UTC).isoformat(), "osm_extract_date": date, "bbox": list(bbox),
           "clipped_mb": round(pbf.stat().st_size / 1e6, 1),
           "counts": {"major_ways": h1.major_ways, "dual_carriageway_tagged": h1.dual_tagged,
                      "oneway_major_km": round(h1.oneway_major_km, 1),
                      "median_link_candidates": h2.links, "food_outlets": h1.food,
                      "grocery_shops": h1.shops, "buildings": h1.buildings},
           "rules": {"major": sorted(MAJOR), "link_max_m": LINK_MAX_M},
           "source": "Map data (c) OpenStreetMap contributors, ODbL. Counts only."}
    pbf.unlink(missing_ok=True)
    log(f"fueltest: {h2.links:,} median-link candidates, {h1.food:,} food, {h1.shops:,} grocery, {h1.buildings:,} buildings")
    return json.dumps(out, indent=1).encode()
