#!/usr/bin/env python3
"""Road names for each measured place, from OpenStreetMap (ODbL), for the street search.

Runs anywhere with ordinary internet (standard library only), e.g. on the iMac:
    python3 tools/road_names.py
Reads  web/globe/data/places.json
Writes web/globe/data/road_names.json

For each place it asks the public Overpass API, once, for named roads within
RADIUS_M of the crossing midpoint and the nearest named locality within
AREA_M. Nothing else is fetched or stored. One request every PAUSE_S seconds.
"""
import json
import math
import os
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLACES = os.path.join(ROOT, "web", "globe", "data", "places.json")
OUT = os.path.join(ROOT, "web", "globe", "data", "road_names.json")
ENDPOINTS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
RADIUS_M, AREA_M, PAUSE_S = 40, 2500, 2.0
UA = "arcroad.org road-name lookup (open data project)"
ROAD_RANK = {"motorway": 0, "trunk": 1, "primary": 2, "secondary": 3, "tertiary": 4, "motorway_link": 5,
             "trunk_link": 5, "primary_link": 6, "secondary_link": 6, "unclassified": 7, "residential": 8,
             "service": 9}


def query(lat, lon):
    q = f"""[out:json][timeout:40];
(
  way(around:{RADIUS_M},{lat},{lon})["highway"]["name"];
  way(around:{RADIUS_M},{lat},{lon})["highway"]["ref"];
)->.r;
.r out tags;
node(around:{AREA_M},{lat},{lon})["place"~"^(suburb|neighbourhood|quarter|village|town|hamlet|locality)$"]["name"];
out tags center;"""
    body = urllib.parse.urlencode({"data": q}).encode()
    last = None
    for url in ENDPOINTS:
        for attempt in range(3):
            try:
                req = urllib.request.Request(url, data=body, headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=60) as r:
                    return json.load(r)
            except Exception as e:  # network hiccup or rate limit: back off, then try the next mirror
                last = e
                time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"Overpass unreachable: {last}")


def dist_m(lat1, lon1, lat2, lon2):
    k = math.pi / 180
    x = (lon2 - lon1) * k * math.cos((lat1 + lat2) / 2 * k)
    return 6371000 * math.hypot(x, (lat2 - lat1) * k)


def summarise(res, lat, lon):
    roads, refs, areas = {}, set(), []
    for el in res.get("elements", []):
        t = el.get("tags", {})
        if el["type"] == "way":
            rank = ROAD_RANK.get(t.get("highway", ""), 10)
            for key in ("name", "name:en"):
                n = (t.get(key) or "").strip()
                if n:
                    roads[n] = min(roads.get(n, 99), rank)
            for r in (t.get("ref") or "").split(";"):
                if r.strip():
                    refs.add(r.strip())
        elif el["type"] == "node":
            n = (t.get("name:en") or t.get("name") or "").strip()
            if n:
                areas.append((dist_m(lat, lon, el["lat"], el["lon"]), n))
    names = [n for n, _ in sorted(roads.items(), key=lambda kv: (kv[1], kv[0]))]
    areas.sort()
    return {"roads": names[:4], "refs": sorted(refs)[:3], "area": areas[0][1] if areas else None}


def main():
    places = json.load(open(PLACES, encoding="utf-8"))
    out = {"generated": time.strftime("%Y-%m-%d"), "source": "© OpenStreetMap contributors, ODbL (via Overpass API)",
           "radius_m": RADIUS_M, "spots": {}}
    for i, s in enumerate(places["spots"]):
        lon = (s["a"][0] + s["b"][0]) / 2
        lat = (s["a"][1] + s["b"][1]) / 2
        info = summarise(query(lat, lon), lat, lon)
        out["spots"][s["id"]] = info
        label = ", ".join(info["roads"] or info["refs"]) or "(no named road)"
        print(f"{s['id']}: {label}" + (f" · {info['area']}" if info["area"] else ""), flush=True)
        if i < len(places["spots"]) - 1:
            time.sleep(PAUSE_S)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    named = sum(1 for v in out["spots"].values() if v["roads"] or v["refs"])
    print(f"Saved {OUT} · {named} of {len(out['spots'])} places have a road name")


if __name__ == "__main__":
    sys.exit(main())
