"""Detour baseline for a proposed one-way loop (docs/PREREG-cyberabad-loop.md).

Pure functions: an OpenStreetMap extract goes in, route lengths come out. The network fetch lives in
tools/loopcost.py. Two networks are compared, today's and the same network with every segment that runs
against the loop's direction removed. Nothing is added to the loop network.
"""

from __future__ import annotations

import heapq
import itertools
import math

from pipeline.filters import oneway_dirs, strip_military
from pipeline.geometry import angle_between, bearing_deg, haversine_m

DRIVABLE = {
    "motorway", "trunk", "primary", "secondary", "tertiary", "unclassified", "residential", "living_street",
    "motorway_link", "trunk_link", "primary_link", "secondary_link", "tertiary_link",
}
MAJOR = {"motorway", "trunk", "primary", "secondary", "tertiary"}
CORRIDOR_M = 30.0        # pre-registered: against-direction segments within this distance of the loop path go
ANTIPARALLEL_TOL = 60.0  # pre-registered: "against" means a bearing within this many degrees of opposite
LONGER_MIN_M = 100.0     # pre-registered: a pair counts as longer only if at least 100 m longer...
LONGER_MIN_FRAC = 0.10   # ...and at least 10% longer
REJECT_BELOW = 1 / 3     # pre-registered: fewer than a third of pairs longer rejects the hypothesis


def build_graph(elements):
    """Directed graph from Overpass JSON elements. Returns (nodes, adj): nodes {id: (lon, lat)},
    adj {u: {v: metres}}. Defence attributes are stripped on ingest, as everywhere in arcroad."""
    nodes = {e["id"]: (e["lon"], e["lat"]) for e in elements if e.get("type") == "node"}
    adj: dict[int, dict[int, float]] = {}
    for e in elements:
        if e.get("type") != "way":
            continue
        tags, _ = strip_military(dict(e.get("tags", {})))
        if tags.get("highway") not in DRIVABLE or tags.get("access") in ("no", "private") or tags.get("area") == "yes":
            continue
        fwd, back = oneway_dirs(tags)
        ids = [n for n in e.get("nodes", []) if n in nodes]
        for u, v in itertools.pairwise(ids):
            d = haversine_m(*nodes[u], *nodes[v])
            if fwd:
                adj.setdefault(u, {})[v] = min(d, adj.get(u, {}).get(v, math.inf))
            if back:
                adj.setdefault(v, {})[u] = min(d, adj.get(v, {}).get(u, math.inf))
    return nodes, adj


def major_nodes(elements):
    """Nodes on roads of class tertiary or above, at ground level: the only places a gate may snap to
    (prereg changes 11 Nov 14:40 and 14:55). A node on a flyover is not a junction anyone can turn at."""
    ground = set()
    for e in elements:
        tags = e.get("tags", {})
        if e.get("type") != "way" or tags.get("highway") not in MAJOR:
            continue
        layer = str(tags.get("layer", "0")).lstrip("+")
        if tags.get("bridge") not in (None, "no") or (layer.isdigit() and int(layer) > 0):
            continue
        ground.update(e.get("nodes", []))
    return ground


def routable(adj):
    out = set(adj)
    for vs in adj.values():
        out.update(vs)
    return out


def nearest_node(nodes, adj, lon, lat, allowed=None):
    """Nearest node that has at least one usable edge (and is in allowed, if given), with its distance in metres."""
    best, best_d = None, math.inf
    for n in routable(adj):
        if allowed is not None and n not in allowed:
            continue
        d = haversine_m(lon, lat, *nodes[n])
        if d < best_d:
            best, best_d = n, d
    return best, best_d


def shortest(adj, s, t):
    """Dijkstra. Returns (metres, [nodes]) or (None, []) when t cannot be reached from s."""
    if s == t:
        return 0.0, [s]
    dist, prev, seen = {s: 0.0}, {}, set()
    heap = [(0.0, s)]
    while heap:
        d, u = heapq.heappop(heap)
        if u in seen:
            continue
        if u == t:
            path = [t]
            while path[-1] != s:
                path.append(prev[path[-1]])
            return d, path[::-1]
        seen.add(u)
        for v, w in adj.get(u, {}).items():
            nd = d + w
            if nd < dist.get(v, math.inf):
                dist[v], prev[v] = nd, u
                heapq.heappush(heap, (nd, v))
    return None, []


def loop_path(adj, gate_nodes):
    """The loop as directed edges: shortest legal path from each gate to the next, closing back to the first.
    Returns (edges, missing_legs)."""
    edges, missing = [], []
    ring = [*gate_nodes, gate_nodes[0]]
    for i, (a, b) in enumerate(itertools.pairwise(ring)):
        d, path = shortest(adj, a, b)
        if d is None:
            missing.append(i)
            continue
        edges.extend(itertools.pairwise(path))
    return edges, missing


def _xy(lon, lat, lat0):
    k = math.cos(math.radians(lat0)) * 111_320.0
    return lon * k, lat * 110_540.0


def _seg_dist_m(p, a, b, lat0):
    px, py = _xy(*p, lat0)
    ax, ay = _xy(*a, lat0)
    bx, by = _xy(*b, lat0)
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def loop_network(nodes, adj, loop_edges, corridor_m=CORRIDOR_M, tol=ANTIPARALLEL_TOL):
    """Copy of adj with every segment that runs against the loop removed: the reverse of each loop edge, and
    any segment with both ends within corridor_m of one loop edge and a bearing within tol of opposite to it.
    Returns (new_adj, removed_edges)."""
    lat0 = sum(nodes[u][1] for u, _ in loop_edges) / max(len(loop_edges), 1)
    loop_set = set(loop_edges)
    segs = [(nodes[u], nodes[v], bearing_deg(*nodes[u], *nodes[v])) for u, v in loop_edges]
    removed = set()
    for u, vs in adj.items():
        for v in vs:
            if (u, v) in loop_set:
                continue
            if (v, u) in loop_set:
                removed.add((u, v))
                continue
            b = bearing_deg(*nodes[u], *nodes[v])
            for a, c, lb in segs:
                if abs(angle_between(b, lb) - 180.0) <= tol and \
                        _seg_dist_m(nodes[u], a, c, lat0) <= corridor_m and _seg_dist_m(nodes[v], a, c, lat0) <= corridor_m:
                    removed.add((u, v))
                    break
    new = {u: {v: w for v, w in vs.items() if (u, v) not in removed} for u, vs in adj.items()}
    return new, sorted(removed)


def is_longer(today_m, loop_m):
    if today_m is None or loop_m is None:
        return None
    return loop_m - today_m >= LONGER_MIN_M and loop_m >= today_m * (1 + LONGER_MIN_FRAC)


def compare(adj_today, adj_loop, gates):
    """gates: [(name, node)]. Every ordered pair, both networks. Unreachable pairs are kept, never dropped."""
    rows = []
    for na, a in gates:
        for nb, b in gates:
            if a == b:
                continue
            t, _ = shortest(adj_today, a, b)
            lp, _ = shortest(adj_loop, a, b)
            rows.append({"from": na, "to": nb,
                         "today_m": None if t is None else round(t, 1),
                         "loop_m": None if lp is None else round(lp, 1),
                         "added_m": None if t is None or lp is None else round(lp - t, 1),
                         "longer": is_longer(t, lp)})
    return rows


def summarise(rows):
    judged = [r for r in rows if r["longer"] is not None]
    longer = [r for r in judged if r["longer"]]
    added = sorted(r["added_m"] for r in longer)
    share = len(longer) / len(judged) if judged else None
    return {"pairs": len(rows), "judged": len(judged), "longer": len(longer),
            "unreachable_today": sum(r["today_m"] is None for r in rows),
            "unreachable_loop": sum(r["loop_m"] is None for r in rows),
            "share_longer": None if share is None else round(share, 3),
            "median_added_m_where_longer": added[len(added) // 2] if added else None,
            "max_added_m": added[-1] if added else None,
            "hypothesis": None if share is None else ("rejected" if share < REJECT_BELOW else "not rejected")}
