"""Buses through the proposed Hi-Tech City loop, from the TGSRTC GTFS feed (docs/PREREG-cyberabad-loop.md, measure 2).

Pure functions on a GTFS zip. A stop belongs to a gate's area when it is within GATE_RADIUS_M of the gate (fixed
before the feed was read, 11 Nov 2026). For every trip that runs on a Wednesday, the gate areas it serves are
listed in the order it serves them; a pattern is a route plus that order. Trips are counted per pattern, so the
result says how many buses a day pass between which loop points, in which direction.
"""

from __future__ import annotations

import csv
import io
import itertools
import zipfile
from collections import Counter, defaultdict

from pipeline.geometry import haversine_m

GATE_RADIUS_M = 400.0   # pre-registered 11 Nov 2026
WEEKDAY = "wednesday"   # pre-registered: one ordinary weekday; trips with no calendar entry are counted and flagged


def _rows(z, name):
    try:
        with z.open(name) as fh:
            return list(csv.DictReader(io.TextIOWrapper(fh, encoding="utf-8-sig")))
    except KeyError:
        return []


def read(path):
    with zipfile.ZipFile(path) as z:
        return {n: _rows(z, f"{n}.txt") for n in ("stops", "routes", "trips", "stop_times", "calendar", "feed_info")}


def gate_areas(stops, gates, radius_m=GATE_RADIUS_M):
    """stop_id -> gate name, for stops within radius of a gate (nearest gate wins)."""
    out = {}
    for s in stops:
        try:
            lon, lat = float(s["stop_lon"]), float(s["stop_lat"])
        except (KeyError, ValueError):
            continue
        best = min(((haversine_m(lon, lat, g["lon"], g["lat"]), g["name"]) for g in gates), default=(None, None))
        if best[0] is not None and best[0] <= radius_m:
            out[s["stop_id"]] = best[1]
    return out


def weekday_services(calendar, day=WEEKDAY):
    return {c["service_id"] for c in calendar if c.get(day) == "1"}


def patterns(feed, gates, radius_m=GATE_RADIUS_M):
    """Counter of (route_short_name, gate order) -> trips on the weekday, plus totals."""
    area = gate_areas(feed["stops"], gates, radius_m)
    services = weekday_services(feed["calendar"])
    no_calendar = not feed["calendar"]
    routes = {r["route_id"]: r.get("route_short_name") or r.get("route_long_name") or r["route_id"] for r in feed["routes"]}
    trip_route = {}
    for t in feed["trips"]:
        if no_calendar or t.get("service_id") in services:
            trip_route[t["trip_id"]] = routes.get(t["route_id"], t["route_id"])
    seq = defaultdict(list)
    for st in feed["stop_times"]:
        if st["trip_id"] in trip_route and st["stop_id"] in area:
            seq[st["trip_id"]].append((int(st["stop_sequence"]), area[st["stop_id"]]))
    count = Counter()
    for trip, visits in seq.items():
        order = []
        for _, g in sorted(visits):
            if not order or order[-1] != g:
                order.append(g)
        count[(trip_route[trip], tuple(order))] += 1
    return {"patterns": count, "trips_counted": len(trip_route), "trips_in_area": len(seq),
            "stops_in_area": len(area), "calendar_missing": no_calendar}


def against(order, loop_order):
    """Consecutive gate pairs in a bus pattern that run against the loop's order (needs the confirmed route's order).
    A pair (a, b) runs with the loop when b follows a in loop order; otherwise it runs against."""
    pos = {g: i for i, g in enumerate(loop_order)}
    n = len(loop_order)
    out = []
    for a, b in itertools.pairwise(order):
        if a in pos and b in pos and (pos[b] - pos[a]) % n != 1:
            out.append((a, b))
    return out
