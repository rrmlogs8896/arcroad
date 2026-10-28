"""Order a field day's stops into a driving sequence and estimate the day. Stdlib only.

    python tools/field_plan.py data/field/field_day_1_stops.json --start S04 --end S13

Prints the driver-facing stop table used in docs/field/field_day_1_route.md.

What the driver sees is deliberately limited to the stop id, its public model
coordinates and generic geometry (which side of the median B is on). The model's
network distance, the map gap and any detour value are never printed: a driver
who knows the expected detour can be steered towards it (STATE.md, Phase 2b).

Estimates are straight-line distances times a road factor plus a flat allowance
per stop. They are planning figures, not measurements, and nothing in them comes
from the model's routing.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from itertools import pairwise

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.geometry import bearing_deg, haversine_m

# Planning assumptions, stated so the estimate can be argued with.
ROAD_FACTOR = 1.4          # road km per straight-line km on a mixed urban/highway corridor
AVG_KMH = 25.0             # Sunday daytime average on a two-wheeler, signals included
CROSSING_KM = (1.0, 3.0)   # generic allowance to find a legal crossing and come back
CROSSING_MIN = 8.0         # arrive at A, find the crossing, reach B, note it
PHOTO_MIN = 5.0            # pull over safely, photograph, move on

FORBIDDEN_WORDS = ("network", "detour", "map_gap", "model distance")

_COMPASS = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")


def _a(stop):
    return stop["a"]  # [lat, lon]


def dist_m(p, q) -> float:
    """Straight-line metres between two [lat, lon] points."""
    return haversine_m(p[1], p[0], q[1], q[0])


def compass(p, q) -> str:
    """Eight-point compass direction from p to q ([lat, lon])."""
    b = bearing_deg(p[1], p[0], q[1], q[0])
    return _COMPASS[int((b + 22.5) // 45) % 8]


def path_m(stops_by_id, order) -> float:
    return sum(dist_m(_a(stops_by_id[x]), _a(stops_by_id[y])) for x, y in pairwise(order))


def order_stops(stops, start, end=None):
    """Nearest-neighbour from `start`, then 2-opt; `start` (and `end`, if given) stay fixed.

    Deterministic: ties break on file order, so the sheet is reproducible.
    """
    by_id = {s["id"]: s for s in stops}
    if start not in by_id or (end is not None and end not in by_id):
        raise KeyError("start/end must be stop ids in the file")
    rank = {s["id"]: k for k, s in enumerate(stops)}
    rest = [s["id"] for s in stops if s["id"] not in (start, end)]
    route = [start]
    while rest:
        here = _a(by_id[route[-1]])
        nxt = min(rest, key=lambda x: (dist_m(here, _a(by_id[x])), rank[x]))
        route.append(nxt)
        rest.remove(nxt)
    if end is not None:
        route.append(end)

    last = len(route) - 1 if end is not None else len(route)
    improved = True
    while improved:
        improved = False
        for i in range(1, last):
            for k in range(i + 1, last):
                cand = route[:i] + route[i:k + 1][::-1] + route[k + 1:]
                if path_m(by_id, cand) < path_m(by_id, route) - 1e-6:
                    route, improved = cand, True
    return route


def estimate(stops, order):
    """Planning totals for a sequence: road km and hours, as (low, high) ranges."""
    by_id = {s["id"]: s for s in stops}
    crossings = sum(1 for x in order if by_id[x].get("b"))
    photos = len(order) - crossings
    road_km = path_m(by_id, order) / 1000 * ROAD_FACTOR
    km = (road_km + crossings * CROSSING_KM[0], road_km + crossings * CROSSING_KM[1])
    stop_h = (crossings * CROSSING_MIN + photos * PHOTO_MIN) / 60
    hours = (km[0] / AVG_KMH + stop_h, km[1] / AVG_KMH + stop_h)
    return {
        "stops": len(order), "crossings": crossings, "photos": photos,
        "straight_km": round(path_m(by_id, order) / 1000, 1),
        "between_stops_road_km": round(road_km, 1),
        "total_km": (round(km[0]), round(km[1])),
        "hours": (round(hours[0], 1), round(hours[1], 1)),
    }


def osm_link(p) -> str:
    return f"https://www.openstreetmap.org/?mlat={p[0]}&mlon={p[1]}#map=19/{p[0]}/{p[1]}"


def sheet_rows(stops, order):
    """Driver-facing rows: position, id, kind, A coordinates, where B is. Nothing else."""
    by_id = {s["id"]: s for s in stops}
    rows = []
    for n, sid in enumerate(order, 1):
        s = by_id[sid]
        a = _a(s)
        if s.get("b"):
            kind = "crossing"
            where_b = f"B is {compass(a, s['b'])} of A, across the median"
        else:
            kind = "photo only"
            where_b = "-"
        rows.append({"n": n, "id": sid, "kind": kind,
                     "a": f"{a[0]}, {a[1]}", "link": osm_link(a), "b": where_b})
    return rows


def render_table(rows) -> str:
    out = ["| # | Stop | Task | Side A (lat, lon) | Side B |", "|---|---|---|---|---|"]
    for r in rows:
        out.append(f"| {r['n']} | **{r['id']}** | {r['kind']} | [{r['a']}]({r['link']}) | {r['b']} |")
    text = "\n".join(out)
    low = text.lower()
    assert not any(w in low for w in FORBIDDEN_WORDS), "field sheet must not steer the driver"
    return text


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("stops")
    ap.add_argument("--start", required=True)
    ap.add_argument("--end")
    ap.add_argument("--split", type=int, default=0,
                    help="also estimate two legs, the first ending after this many stops")
    args = ap.parse_args(argv)
    with open(args.stops, encoding="utf-8") as fh:
        stops = json.load(fh)["stops"]
    order = order_stops(stops, args.start, args.end)
    print(" -> ".join(order))
    print(render_table(sheet_rows(stops, order)))
    print("whole day:", estimate(stops, order))
    if args.split:
        print("leg 1:", estimate(stops, order[:args.split]))
        print("leg 2:", estimate(stops, order[args.split:]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
