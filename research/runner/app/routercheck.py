"""Pre-registered job: do two independent open routers agree with arcroad's modelled detours?
(docs/PREREG-routercheck.md)

Routers: OSRM (car profile) and Valhalla (auto), each on OpenStreetMap data and each obeying OSM turn
restrictions, which arcroad's own model does not. Uses the public demo servers politely: one request at a
time with a pause, 48 routes a night. Output is a candidate check, never published as is.
"""
from __future__ import annotations

import json
import time
import urllib.parse
from datetime import UTC, datetime

from openings import PLACES_URL, get

OSRM = "https://router.project-osrm.org/route/v1/driving/"
VALHALLA = "https://valhalla1.openstreetmap.de/route"
AGREE = 0.15          # pre-registered: within 15% of the model counts as agreement
LONGER_FLAG = 0.20    # router at least 20% longer: possible banned U-turn used by the model
SNAP_M = 25


def ratio(router_m, model_m):
    if not router_m or not model_m:
        return None
    return router_m / model_m


def classify(r):
    if r is None:
        return "NO_ROUTE"
    if abs(r - 1) <= AGREE:
        return "AGREES"
    if r - 1 >= LONGER_FLAG:
        return "ROUTER_LONGER"
    return "ROUTER_SHORTER" if r < 1 else "DIFFERS"


def osrm(a, b):
    coords = f"{a[0]},{a[1]};{b[0]},{b[1]}"
    q = urllib.parse.urlencode({"overview": "false", "radiuses": f"{SNAP_M};{SNAP_M}", "continue_straight": "true"})
    d = json.loads(get(OSRM + coords + "?" + q))
    return d["routes"][0]["distance"] if d.get("code") == "Ok" and d.get("routes") else None


def valhalla(a, b):
    body = {"locations": [{"lon": a[0], "lat": a[1], "radius": SNAP_M}, {"lon": b[0], "lat": b[1], "radius": SNAP_M}],
            "costing": "auto", "units": "kilometers", "directions_type": "none"}
    d = json.loads(get(VALHALLA + "?json=" + urllib.parse.quote(json.dumps(body))))
    return d["trip"]["summary"]["length"] * 1000 if "trip" in d else None


def summarise(rows, key):
    cls = [r[key]["class"] for r in rows if key in r]
    n = len(cls)
    return {k: cls.count(k) for k in ("AGREES", "ROUTER_LONGER", "ROUTER_SHORTER", "NO_ROUTE")} | {"n": n}


def run(log):
    spots = json.loads(get(PLACES_URL))["spots"]
    out = {"job": "routercheck-v1", "prereg": "docs/PREREG-routercheck.md", "status": "CANDIDATE, NOT PUBLISHED",
           "started": datetime.now(UTC).isoformat(),
           "routers": {"osrm": "OSRM demo server, car profile (OSM, ODbL)",
                       "valhalla": "Valhalla, FOSSGIS server, auto costing (OSM, ODbL)"},
           "rows": []}
    for s in spots:
        for d, (p, q) in (("ab", (s["a"], s["b"])), ("ba", (s["b"], s["a"]))):
            model = s.get(d)
            row = {"id": s["id"], "dir": d, "model_m": model,
                   "driven_m": (s.get("driven") or {}).get(d, {}).get("m")}
            for name, fn in (("osrm", osrm), ("valhalla", valhalla)):
                try:
                    m = fn(p, q)
                except Exception as e:  # recorded, never dropped
                    m, row[name + "_error"] = None, str(e)[:200]
                r = ratio(m, model)
                row[name] = {"m": round(m, 1) if m else None, "ratio": round(r, 3) if r else None,
                             "class": classify(r)}
                time.sleep(1.5)
            out["rows"].append(row)
            log(f"routercheck {s['id']} {d} osrm={row['osrm']['class']} valhalla={row['valhalla']['class']}")
    rows = out["rows"]
    driven = [r for r in rows if r["driven_m"]]

    def err(key):
        e = [abs(r[key]["m"] - r["driven_m"]) / r["driven_m"] for r in driven if r[key]["m"]]
        return round(sum(e) / len(e), 3) if e else None

    model_err = [abs(r["model_m"] - r["driven_m"]) / r["driven_m"] for r in driven if r["model_m"]]
    out["summary"] = {
        "osrm": summarise(rows, "osrm"), "valhalla": summarise(rows, "valhalla"),
        "both_routers_longer": [f"{r['id']}-{r['dir']}" for r in rows
                                if r["osrm"]["class"] == r["valhalla"]["class"] == "ROUTER_LONGER"],
        "mean_abs_error_vs_driven": {"model": round(sum(model_err) / len(model_err), 3) if model_err else None,
                                     "osrm": err("osrm"), "valhalla": err("valhalla"), "n_driven": len(driven)},
    }
    out["finished"] = datetime.now(UTC).isoformat()
    return json.dumps(out, indent=1).encode()
