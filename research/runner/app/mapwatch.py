"""Nightly watch: has anyone edited the roads or turn rules near a place? (docs/PREREG-routercheck.md, part 2)

Asks OpenStreetMap through Overpass for road ways and turn-restriction relations within 1 km of each place
that changed in the last 48 hours (runs overlap on purpose, so a missed night loses nothing). A hit means
"re-check this place", never "the detour changed". Mapper names are not collected.
"""
from __future__ import annotations

import json
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
    for s in spots:
        lat, lon = (s["a"][1] + s["b"][1]) / 2, (s["a"][0] + s["b"][0]) / 2
        try:
            d = json.loads(get(OVERPASS, urllib.parse.urlencode({"data": query(lat, lon, since)}).encode()))
            edits = [summarise(e) for e in d.get("elements", [])]
            row = {"id": s["id"], "edits": edits, "recheck": bool(edits)}
        except Exception as e:
            row = {"id": s["id"], "error": str(e)[:200], "recheck": None}
        out["places"].append(row)
        log(f"mapwatch {s['id']} {len(row.get('edits', []))} edits")
        time.sleep(5)
    out["recheck"] = [p["id"] for p in out["places"] if p.get("recheck")]
    out["finished"] = datetime.now(UTC).isoformat()
    return json.dumps(out, indent=1).encode()
