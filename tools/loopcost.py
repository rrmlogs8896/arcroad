"""Detour baseline for the proposed Hi-Tech City one-way loop (docs/PREREG-cyberabad-loop.md).

Run on the iMac with the project venv. Two steps, with a person's check in between:

    python3 tools/loopcost.py geocode   # finds the six gates on OpenStreetMap, writes data/loop/gates.json
    (open each printed OpenStreetMap link and look: is that the place?)
    python3 tools/loopcost.py check "IKEA Rotary" ...   # marks those gates checked (or: check all)
    python3 tools/loopcost.py run OUT_DIR   # routes both networks, writes OUT_DIR/loopcost-<UTC time>.json

Open data only: Nominatim and Overpass (OpenStreetMap, ODbL), public OSRM and Valhalla servers for the
cross-check. No Google data. The output is a candidate, never published as it is.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import UTC, datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pipeline.loopcost import (  # noqa: E402
    DRIVABLE,
    build_graph,
    compare,
    geojson,
    loop_doubles_back,
    loop_network,
    loop_path,
    major_nodes,
    nearest_node,
    summarise,
)

UA = {"User-Agent": "arcroad/1.0 (https://arcroad.org; hello@arcroad.org)"}
NOMINATIM = "https://nominatim.openstreetmap.org/search"
OVERPASS = "https://overpass-api.de/api/interpreter"
OSRM = "https://router.project-osrm.org/route/v1/driving/"
VALHALLA = "https://valhalla1.openstreetmap.de/route"
GATES = ROOT / "data/loop/gates.json"
VIEWBOX = "78.33,17.47,78.42,17.40"  # west, north, east, south: Gachibowli to Madhapur
MARGIN_DEG = 0.015                    # about 1.6 km around the gates
SNAP_FLAG_M = 60.0
CHECK_DIFF = 0.10                     # pre-registered: flag a pair where a public router differs by over 10%

# Loop order, as reported on 29 Oct 2026. Several searches per gate; the first match inside the viewbox is kept.
LOOP = [
    ("Biodiversity Junction", ["Biodiversity Junction", "Bio Diversity Junction", "Biodiversity Flyover",
                               "Bio-Diversity Park", "Biodiversity Park", "Biodiversity"]),
    ("IKEA Rotary", ["IKEA Hyderabad", "IKEA"]),
    ("Mindspace C-Gate", ["Raheja Mindspace", "Mindspace"]),
    ("Knowledge City", ["Knowledge City", "Knowledge City Road"]),
    ("Dallas Center", ["Dallas Center", "Dallas Centre"]),
    ("My Home Bhooja", ["My Home Bhooja", "Bhooja", "My Home Bhooja Raidurg", "My Home Twitza", "My Home"]),
]


def get(url, data=None, timeout=180):
    req = urllib.request.Request(url, data=data, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def geocode():
    """Searches only gates without a match yet; matches already in gates.json, and their checks, are kept."""
    old = {g["name"]: g for g in json.loads(GATES.read_text())["gates"]} if GATES.exists() else {}
    out = {"written": datetime.now(UTC).isoformat(), "source": "Nominatim (OpenStreetMap, ODbL)",
           "note": "Check each match against OpenStreetMap and set checked to true. Unmatched gates are left out.",
           "gates": []}
    for name, queries in LOOP:
        g = old.get(name) or {"name": name, "checked": False, "match": None}
        for q in [] if g["match"] else queries:
            params = urllib.parse.urlencode({"q": q, "format": "jsonv2", "limit": 1, "viewbox": VIEWBOX,
                                             "bounded": 1})
            res = json.loads(get(f"{NOMINATIM}?{params}"))
            time.sleep(1.1)  # Nominatim usage policy: at most one request a second
            if res:
                r = res[0]
                g["match"] = {"query": q, "display_name": r["display_name"], "osm": f"{r['osm_type']}/{r['osm_id']}",
                              "lon": float(r["lon"]), "lat": float(r["lat"])}
                break
        out["gates"].append(g)
        m = g["match"]
        link = "" if not m else f"  open https://www.openstreetmap.org/{m['osm']}"
        print(f"{name:24} {'NOT FOUND' if not m else m['display_name'][:60]}{link}")
    GATES.parent.mkdir(parents=True, exist_ok=True)
    GATES.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    print(f"\nWrote {GATES.relative_to(ROOT)}. Open each link, then mark the right ones: tools/loopcost.py check ...")


def check(names):
    d = json.loads(GATES.read_text())
    for g in d["gates"]:
        if g["match"] and ("all" in names or g["name"] in names):
            g["checked"] = True
            g["checked_at"] = datetime.now(UTC).isoformat()
    GATES.write_text(json.dumps(d, indent=1, ensure_ascii=False) + "\n")
    for g in d["gates"]:
        print(f"{g['name']:24} {'checked' if g['checked'] else 'not checked'}")


def overpass(bbox):
    s, w, n, e = bbox
    cls = "|".join(sorted(DRIVABLE))
    q = f'[out:json][timeout:120];way["highway"~"^({cls})$"]({s},{w},{n},{e});(._;>;);out body;'
    t = datetime.now(UTC).isoformat()
    return json.loads(get(OVERPASS, data=urllib.parse.urlencode({"data": q}).encode())), q, t


def public_router(a, b):
    """Today's route on the public OSRM and Valhalla servers, for the cross-check. Never routes the loop."""
    res = {}
    try:
        d = json.loads(get(f"{OSRM}{a[0]},{a[1]};{b[0]},{b[1]}?overview=false", timeout=30))
        res["osrm_m"] = round(d["routes"][0]["distance"], 1) if d.get("code") == "Ok" else None
    except Exception as e:  # recorded, never dropped
        res["osrm_m"], res["osrm_error"] = None, str(e)[:120]
    time.sleep(1.5)
    body = {"locations": [{"lon": a[0], "lat": a[1]}, {"lon": b[0], "lat": b[1]}], "costing": "auto",
            "units": "kilometers", "directions_type": "none"}
    try:
        d = json.loads(get(VALHALLA + "?json=" + urllib.parse.quote(json.dumps(body)), timeout=30))
        res["valhalla_m"] = round(d["trip"]["summary"]["length"] * 1000, 1) if "trip" in d else None
    except Exception as e:
        res["valhalla_m"], res["valhalla_error"] = None, str(e)[:120]
    time.sleep(1.5)
    return res


def run(out_dir):
    gates_file = json.loads(GATES.read_text())
    gates = [g for g in gates_file["gates"] if g["checked"] and g["match"]]
    left_out = [g["name"] for g in gates_file["gates"] if not (g["checked"] and g["match"])]
    if len(gates) < 3:
        sys.exit("Fewer than three checked gates in data/loop/gates.json: nothing to compute.")
    lons = [g["match"]["lon"] for g in gates]
    lats = [g["match"]["lat"] for g in gates]
    bbox = (min(lats) - MARGIN_DEG, min(lons) - MARGIN_DEG, max(lats) + MARGIN_DEG, max(lons) + MARGIN_DEG)
    print("Fetching the OpenStreetMap extract from Overpass...")
    osm, query, fetched = overpass(bbox)
    nodes, adj = build_graph(osm["elements"])
    major = major_nodes(osm["elements"])
    snapped = []
    for g in gates:
        n, d = nearest_node(nodes, adj, g["match"]["lon"], g["match"]["lat"], allowed=major)
        snapped.append({"name": g["name"], "node": n, "snap_m": round(d, 1), "flag": d > SNAP_FLAG_M})
    order = [s["node"] for s in snapped]
    edges, missing = loop_path(adj, order)
    loop, removed = loop_network(nodes, adj, edges)
    doubles = loop_doubles_back(nodes, edges)
    rows = compare(adj, loop, [(s["name"], s["node"]) for s in snapped])
    print(f"Routed {len(rows)} pairs on both networks. Cross-checking today's routes on public servers...")
    pos = {s["name"]: nodes[s["node"]] for s in snapped}
    for r in rows:
        r.update(public_router(pos[r["from"]], pos[r["to"]]))
        diffs = [abs(r[k] - r["today_m"]) / r["today_m"] for k in ("osrm_m", "valhalla_m")
                 if r.get(k) and r["today_m"]]
        r["router_flag"] = any(x > CHECK_DIFF for x in diffs)
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    out = {"job": "loopcost-v1", "prereg": "docs/PREREG-cyberabad-loop.md", "status": "CANDIDATE, NOT PUBLISHED",
           "label": "Loop figures are scenario figures from OpenStreetMap, not measured effects.",
           "commit": commit, "extract": {"source": "Overpass API (OpenStreetMap, ODbL)", "fetched": fetched,
                                         "query": query, "nodes": len(nodes), "edges": sum(map(len, adj.values()))},
           "gates": snapped, "gates_left_out": left_out, "loop": {"edges": len(edges), "missing_legs": missing,
                                                                  "segments_removed": len(removed),
                                                                  "edges_doubling_back": len(doubles)},
           "rows": rows, "summary": summarise(rows)}
    out_dir = pathlib.Path(out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / f"loopcost-{datetime.now(UTC).strftime('%Y%m%dT%H%MZ')}.json"
    p.write_text(json.dumps(out, indent=1) + "\n")
    (p.with_suffix(".geojson")).write_text(json.dumps(geojson(nodes, edges, removed,
                                                              [(x["name"], x["node"]) for x in snapped])))
    (p.with_name(p.stem + "-extract.json")).write_text(json.dumps(osm))
    s = out["summary"]
    print(f"\n{s['longer']} of {s['judged']} pairs longer on the loop network (share {s['share_longer']}); "
          f"hypothesis {s['hypothesis']}. Router flags: {sum(r['router_flag'] for r in rows)}. "
          f"Snap flags: {sum(x['flag'] for x in snapped)}. Missing loop legs: {missing}. "
          f"Loop edges doubling back: {len(doubles)}.")
    print(f"Wrote {p}")


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "geocode":
        geocode()
    elif len(sys.argv) >= 3 and sys.argv[1] == "check":
        check(sys.argv[2:])
    elif len(sys.argv) == 3 and sys.argv[1] == "run":
        run(sys.argv[2])
    else:
        sys.exit(__doc__)
