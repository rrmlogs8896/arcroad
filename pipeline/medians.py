"""Median openings (U-turn gaps) on divided roads, and which are worth a second look (docs/PREREG-uturn-spacing.md).

Pure functions on Overpass JSON. Every threshold here is fixed in the pre-registration.
"""

from __future__ import annotations

import itertools
import random

from pipeline.filters import oneway_dirs, strip_military
from pipeline.geometry import angle_between, bearing_deg, haversine_m

CARRIAGEWAY = {"trunk", "primary", "secondary", "tertiary"}
DRIVABLE = {"motorway", "trunk", "primary", "secondary", "tertiary", "unclassified", "residential", "living_street",
            "motorway_link", "trunk_link", "primary_link", "secondary_link", "tertiary_link"}
PUBLIC = {"motorway", "trunk", "primary", "secondary", "tertiary", "unclassified", "residential"}
OPPOSITE_TOL = 30.0      # carriageway bearings within 30 degrees of opposite
GAP_MIN_M, GAP_MAX_M = 6.0, 45.0
OPENING_MAX_M = 45.0
MERGE_M = 25.0
CLOSE_M = 150.0
JUNCTION_M = 100.0
AT_JUNCTION_M = 30.0  # prereg change 11 Nov 20:05: within this, the opening is the junction itself
SAMPLE_N = 10
PASS_K = 7


def _ground(tags):
    layer = str(tags.get("layer", "0")).lstrip("+")
    return tags.get("bridge") in (None, "no") and not (layer.isdigit() and int(layer) > 0)


def _parse(elements):
    nodes = {e["id"]: (e["lon"], e["lat"]) for e in elements if e.get("type") == "node"}
    signals = {e["id"] for e in elements if e.get("type") == "node" and (e.get("tags") or {}).get("highway") == "traffic_signals"}
    ways = []
    for e in elements:
        if e.get("type") != "way":
            continue
        tags, _ = strip_military(dict(e.get("tags", {})))
        ids = [n for n in e.get("nodes", []) if n in nodes]
        if len(ids) >= 2:
            ways.append({"id": e["id"], "tags": tags, "nodes": ids})
    return nodes, signals, ways


def _carriageways(ways):
    """One-way main-road ways at ground level, with node order in the direction of travel."""
    out = {}
    for w in ways:
        t = w["tags"]
        if t.get("highway") not in CARRIAGEWAY or not _ground(t):
            continue
        fwd, back = oneway_dirs(t)
        if fwd == back:
            continue
        out[w["id"]] = dict(w, seq=w["nodes"] if fwd else w["nodes"][::-1])
    return out


def _bearing_at(nodes, seq, n):
    i = seq.index(n)
    a, b = (seq[i], seq[i + 1]) if i + 1 < len(seq) else (seq[i - 1], seq[i])
    return bearing_deg(*nodes[a], *nodes[b])


def _length(nodes, ids):
    return sum(haversine_m(*nodes[a], *nodes[b]) for a, b in itertools.pairwise(ids))


def road_key(w):
    t = w["tags"]
    return t.get("name") or t.get("ref") or f"way {w['id']}"


def find_openings(elements):
    """Median openings, merged within MERGE_M. Each: lon, lat, road, ways, way ids of the connectors."""
    nodes, _, ways = _parse(elements)
    cw = _carriageways(ways)
    on = {}
    for w in cw.values():
        for n in w["seq"]:
            on.setdefault(n, []).append(w["id"])
    raw = []
    for w in ways:
        t = w["tags"]
        if w["id"] in cw or t.get("highway") not in DRIVABLE or t.get("access") in ("no", "private"):
            continue
        a, b = w["nodes"][0], w["nodes"][-1]
        if a not in on or b not in on or _length(nodes, w["nodes"]) > OPENING_MAX_M:
            continue
        gap = haversine_m(*nodes[a], *nodes[b])
        if not GAP_MIN_M <= gap <= GAP_MAX_M:
            continue
        for x in on[a]:
            for y in on[b]:
                if x == y:
                    continue
                ba, bb = _bearing_at(nodes, cw[x]["seq"], a), _bearing_at(nodes, cw[y]["seq"], b)
                if abs(angle_between(ba, bb) - 180.0) <= OPPOSITE_TOL:
                    mid = ((nodes[a][0] + nodes[b][0]) / 2, (nodes[a][1] + nodes[b][1]) / 2)
                    raw.append({"lon": mid[0], "lat": mid[1], "road": road_key(cw[x]), "ways": [w["id"]]})
                    break
            else:
                continue
            break
    merged = []
    for o in raw:
        for m in merged:
            if m["road"] == o["road"] and haversine_m(m["lon"], m["lat"], o["lon"], o["lat"]) <= MERGE_M:
                m["ways"] += o["ways"]
                break
        else:
            merged.append(o)
    return merged


def junctions(elements, openings):
    """Junction and signal points: carriageway nodes shared with a public road that is neither a carriageway of
    the same road nor an opening, plus mapped traffic signals."""
    nodes, signals, ways = _parse(elements)
    cw = _carriageways(ways)
    opening_ways = {wid for o in openings for wid in o["ways"]}
    cw_nodes = {n: road_key(w) for w in cw.values() for n in w["seq"]}
    pts = set()
    for w in ways:
        t = w["tags"]
        if w["id"] in opening_ways or t.get("highway") not in PUBLIC:
            continue
        if w["id"] in cw:
            continue
        name = road_key(w)
        for n in w["nodes"]:
            if n in cw_nodes and cw_nodes[n] != name:
                pts.add(n)
    return [nodes[n] for n in sorted(pts | (signals & set(nodes)))]


def flag(openings, junction_pts):
    """Adds to each opening the distance to the nearest junction or signal and to the nearest other mid-block opening
    on the same road, and the flags (prereg change 11 Nov 20:05: an opening within AT_JUNCTION_M is the junction)."""
    for o in openings:
        js = [haversine_m(o["lon"], o["lat"], *j) for j in junction_pts]
        o["nearest_junction_m"] = round(min(js), 1) if js else None
        o["at_junction"] = bool(js) and min(js) <= AT_JUNCTION_M
    for o in openings:
        others = [haversine_m(o["lon"], o["lat"], p["lon"], p["lat"]) for p in openings
                  if p is not o and p["road"] == o["road"] and not p["at_junction"]]
        o["nearest_opening_m"] = round(min(others), 1) if others else None
        o["close_to_opening"] = not o["at_junction"] and bool(others) and min(others) < CLOSE_M
        o["next_to_junction"] = not o["at_junction"] and o["nearest_junction_m"] is not None and \
            o["nearest_junction_m"] <= JUNCTION_M
        o["second_look"] = o["close_to_opening"] or o["next_to_junction"]
    return openings


def summarise(openings):
    n = len(openings)
    k = sum(o["second_look"] for o in openings)
    by_road = {}
    for o in openings:
        r = by_road.setdefault(o["road"], {"openings": 0, "second_look": 0})
        r["openings"] += 1
        r["second_look"] += o["second_look"]
    return {"openings": n, "second_look": k, "share": round(k / n, 3) if n else None,
            "close_to_opening": sum(o["close_to_opening"] for o in openings),
            "next_to_junction": sum(o["next_to_junction"] for o in openings),
            "at_junction": sum(o["at_junction"] for o in openings),
            "hypothesis_if_ground_check_passes": None if not n else ("supported" if k / n >= 0.25 else "not supported"),
            "by_road": dict(sorted(by_road.items(), key=lambda kv: -kv[1]["second_look"]))}


def ground_sample(openings, seed, n=SAMPLE_N):
    """The pre-registered random draw of flagged openings to check on the road. The seed is recorded first."""
    flagged = [i for i, o in enumerate(openings) if o["second_look"]]
    return sorted(random.Random(seed).sample(flagged, min(n, len(flagged))))


def ground_verdict(checked, flagged_total):
    """checked: booleans (a real opening that matches the map) for the drawn sample. The share is published only if
    at least PASS_K of SAMPLE_N are real; with fewer flagged openings than SAMPLE_N, all are checked and the same
    7-in-10 rate applies."""
    need = min(SAMPLE_N, flagged_total)
    if need == 0 or len(checked) < need:
        return "incomplete"
    return "pass" if sum(checked) >= -(-PASS_K * need // SAMPLE_N) else "fail: mapping finding"
