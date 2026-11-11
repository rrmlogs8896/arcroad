#!/usr/bin/env python3
"""Road names for each measured place, from OpenStreetMap (ODbL), for the street search.

Runs anywhere with ordinary internet (standard library only), e.g. on the iMac:
    python3 tools/road_names.py
Reads  web/globe/data/places.json
Writes web/globe/data/road_names.json

For each place it asks OpenStreetMap's Nominatim, once per side of the crossing,
for the nearest road (name, ref) and its neighbourhood. Nothing else is fetched
or stored. About one request a second, within Nominatim's usage policy.
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLACES = os.path.join(ROOT, "web", "globe", "data", "places.json")
OUT = os.path.join(ROOT, "web", "globe", "data", "road_names.json")
NOMINATIM = "https://nominatim.openstreetmap.org/reverse"
PAUSE_S = 1.2  # Nominatim usage policy: at most one request a second
UA = "arcroad.org road-name lookup (open data project)"


def nominatim(lat, lon, zoom):
    q = urllib.parse.urlencode({"format": "jsonv2", "lat": f"{lat:.6f}", "lon": f"{lon:.6f}", "zoom": zoom,
                                "addressdetails": 1, "namedetails": 1, "accept-language": "en"})
    last = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(NOMINATIM + "?" + q, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=25) as r:
                return json.load(r)
        except Exception as e:  # network hiccup or rate limit: back off and retry
            last = e
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"Nominatim unreachable: {last}")


# Local names that differ from the OpenStreetMap address. Rohit, 7 Nov 2026: the area at S18 is known
# locally as KPHB Colony (Kukatpally Housing Board); the address lookup returns "APHB Colony".
AREA_LOCAL = {"APHB Colony": "KPHB Colony"}


def lookup(s):
    """Road names from the road nearest each side of the crossing, area from the address."""
    roads, refs, area = [], [], None
    for lon, lat in (s["a"], s["b"]):
        d = nominatim(lat, lon, 17)
        nd, ad = d.get("namedetails") or {}, d.get("address") or {}
        for n in (nd.get("name:en"), nd.get("name"), ad.get("road")):
            if n and n.strip() and n.strip() not in roads:
                roads.append(n.strip())
        for r in (nd.get("ref") or "").split(";"):
            if r.strip() and r.strip() not in refs:
                refs.append(r.strip())
        area = area or next((ad[k] for k in ("neighbourhood", "suburb", "quarter", "village", "town", "city_district", "hamlet") if ad.get(k)), None)
        time.sleep(PAUSE_S)
    return {"roads": roads[:4], "refs": refs[:3], "area": AREA_LOCAL.get(area, area)}


def main():
    places = json.load(open(PLACES, encoding="utf-8"))
    out = {"generated": time.strftime("%Y-%m-%d"), "source": "© OpenStreetMap contributors, ODbL (via Nominatim reverse geocoding)", "spots": {}}
    for s in places["spots"]:
        info = lookup(s)
        out["spots"][s["id"]] = info
        label = ", ".join(info["roads"] or info["refs"]) or "(no named road)"
        print(f"{s['id']}: {label}" + (f" · {info['area']}" if info["area"] else ""), flush=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    named = sum(1 for v in out["spots"].values() if v["roads"] or v["refs"])
    print(f"Saved {OUT} · {named} of {len(out['spots'])} places have a road name")


if __name__ == "__main__":
    sys.exit(main())
