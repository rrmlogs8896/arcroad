"""Pair each sample with the far kerb, route between them, emit re-routable records.

B-09, 26 Oct 2026. Ported from the Colab notebooks, which until now were the only
place this logic lived:

- ``HMA_Phase2a_DetourIndex_v07.ipynb`` sections 5, 6, 6b, 7, 9 and 10 (cells
  ``GraphPass``, the graph build with ``node_bearing``, connected components, the
  ``cKDTree`` pairing loop using ``is_antiparallel(..., BEARING_TOL)``, the chunked
  Dijkstra, and the record build).
- ``arcroad_Phase2e_Diagnostics_v10.ipynb``, the run that wrote
  ``di_v10_points_2026-10-25.csv``. Its graph, components, routing and record cells
  are byte-identical to v07. Its pairing cell differs by one line, a guard so that
  ``FOCUS_ZONE = None`` means "no focus zone"; the guard is ported. Its parse cell
  also collects named places for the area atlas, which do not touch pairing; they
  are ported so the atlas keeps working. What v10 changed is configuration, which
  is why both runs are kept below as presets rather than folded into one default.

**The port is deliberately literal.** Node order, candidate order, the stride test
``k % stride``, tie-breaking (strict ``<`` on distance, first hit in KD-tree query
order wins), the ``seen`` de-duplication and the ``MAX_SAMPLES`` break are all as
the notebook had them. A silent change to any of them would make the next run
incomparable with v1.0, and nothing in the output would show it.

What is NEW, and only this:

1. **Both endpoints are kept** (B-09). Every record carries ``a_*`` and ``b_*``
   coordinates and OSM node ids, so any measurement can be re-routed by anyone.
2. **A null route names its reason**: ``different_component`` when the two
   endpoints sit in different weak components of the graph, otherwise
   ``unreachable`` (no directed route within the routing limit).
3. **The study box is an explicit parameter** (B-10). Clipping happens AFTER
   pairing and BEFORE routing, on endpoint A, so the sampling inside the box is
   exactly what v1.0 sampled there; only the pairs outside are dropped, and they
   are counted. The box used is written into every record and into the run
   metadata.
4. **Export refuses invalid records.** ``write_point_file`` runs
   ``provenance.validate_export`` first and writes nothing if any record fails.
"""

from __future__ import annotations

import collections
import csv
import itertools
import json
import math
import os
import subprocess
from dataclasses import asdict, dataclass, field

from pipeline.filters import levels_compatible, oneway_dirs, strip_military, way_level
from pipeline.geometry import bearing_deg, haversine_m, is_antiparallel, zone_of
from pipeline.metrics import detour_index
from pipeline.provenance import validate_export

# The study area the project declares. Defined in the notebooks as
# ZONES["hmda_all"]; v1.0 declared it and then did not clip to it (B-10).
HMDA_BBOX = (78.050, 17.050, 78.850, 17.750)

ZONES = {
    "core_city": (78.380, 17.370, 78.520, 17.460),
    "patancheru": (78.230, 17.490, 78.330, 17.570),
    "hmda_all": HMDA_BBOX,
}

DRIVABLE = {
    "motorway", "trunk", "primary", "secondary", "tertiary",
    "motorway_link", "trunk_link", "primary_link", "secondary_link", "tertiary_link",
    "unclassified", "residential", "living_street", "service", "road",
}
ARTERIAL = {"motorway", "trunk", "primary", "secondary"}


@dataclass(frozen=True)
class PairingConfig:
    """Every knob the pairing and routing steps read. Recorded with each run."""

    cross_min_m: float = 12
    cross_max_m: float = 70
    bearing_tol: float = 35          # F-2: degrees from antiparallel still accepted
    sample_stride: int = 4
    focus_zone: str | None = None
    focus_stride: int = 5
    max_samples: int = 16000
    route_limit_m: float = 25000
    di_review: float = 50.0          # F-6: a FLAG on points, never a filter
    route_chunk: int = 200
    label: str = "v1.0"


# The run that produced di_v10_points_2026-10-25.csv. This is the default because
# the next run is compared against it.
V10 = PairingConfig()

# The v0.7 settings, kept so a v0.7 figure can be reproduced on demand.
V07 = PairingConfig(
    sample_stride=12, focus_zone="patancheru", focus_stride=1,
    max_samples=9000, route_limit_m=50000, label="v0.7",
)


# --------------------------------------------------------------------------
# Section 5: parse the road network (needs osmium; imported lazily so the rest of
# this module, and its tests, run without it).
# --------------------------------------------------------------------------

def load_network(pbf_path):
    """Parse drivable ways from an OSM extract. Returns the notebook's ``g``.

    Attributes: ``ways`` as (way_id, nodes, fwd, bwd, highway, divided, level),
    ``coords`` {node_id: (lon, lat)} in first-seen order (the order matters, see
    the module docstring), ``places`` and ``military_stripped``.
    """
    import osmium

    class GraphPass(osmium.SimpleHandler):
        def __init__(self):
            super().__init__()
            self.ways = []
            self.coords = {}
            self.places = []
            self.military_stripped = 0

        def way(self, w):
            tags = dict(w.tags)
            hw = tags.get("highway")
            if hw not in DRIVABLE:
                return
            tags, stripped = strip_military(tags)
            if stripped:
                self.military_stripped += 1
            try:
                nodes = [n.ref for n in w.nodes]
                for n in w.nodes:
                    self.coords[n.ref] = (n.lon, n.lat)
            except Exception:
                return
            if len(nodes) < 2:
                return
            fwd, bwd = oneway_dirs(tags)
            divided = (tags.get("oneway") in ("yes", "true", "1", "-1")
                       or tags.get("dual_carriageway") == "yes")
            self.ways.append((w.id, nodes, fwd, bwd, hw, divided, way_level(tags)))

        def node(self, n):
            t = dict(n.tags)
            p = t.get("place")
            nm = t.get("name")
            if not p or not nm:
                return
            if p not in ("city", "town", "suburb", "neighbourhood", "village", "hamlet", "quarter"):
                return
            try:
                self.places.append((nm, p, n.location.lon, n.location.lat))
            except Exception:
                pass

    g = GraphPass()
    g.apply_file(pbf_path, locations=True)
    return g


def extract_date(pbf_path):
    """The replication timestamp in the extract's header, or None if it has none."""
    import osmium

    reader = osmium.io.Reader(str(pbf_path), osmium.osm.osm_entity_bits.NOTHING)
    try:
        ts = reader.header().get("osmosis_replication_timestamp")
    finally:
        reader.close()
    return ts or None


def commit_sha(repo_dir="."):
    """HEAD of the repository the pipeline was imported from, '+dirty' if pipeline/
    has uncommitted changes. None outside a git checkout."""
    try:
        sha = subprocess.run(
            ["git", "-C", str(repo_dir), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "-C", str(repo_dir), "status", "--porcelain", "pipeline"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None
    return sha + ("+dirty" if dirty else "")


# --------------------------------------------------------------------------
# Section 6: graph, per-node levels and bearings.
# --------------------------------------------------------------------------

@dataclass
class Graph:
    node_ids: object
    idx_of: dict
    lon: object
    lat: object
    G: object
    node_way: dict
    node_levels: dict
    node_bearing: dict
    comp_label: object = None
    n_comp: int = 0

    @property
    def n(self):
        return len(self.node_ids)


def build_graph(ways, coords):
    """Section 6 and 6b of the notebook, unchanged."""
    import numpy as np
    from scipy.sparse import csr_matrix
    from scipy.sparse.csgraph import connected_components

    node_ids = np.fromiter(coords.keys(), dtype=np.int64)
    idx_of = {int(nid): i for i, nid in enumerate(node_ids)}
    lon = np.array([coords[n][0] for n in coords])
    lat = np.array([coords[n][1] for n in coords])
    N = len(node_ids)

    rows, cols, vals = [], [], []
    node_way = collections.defaultdict(set)
    node_levels = collections.defaultdict(set)    # F-1
    node_bearing = collections.defaultdict(list)  # F-2

    for wid, nodes, fwd, bwd, _hw, _divided, lvl in ways:
        for a, b in itertools.pairwise(nodes):
            if a not in idx_of or b not in idx_of:
                continue
            ia, ib = idx_of[a], idx_of[b]
            d = haversine_m(lon[ia], lat[ia], lon[ib], lat[ib])
            if d <= 0:
                continue
            brg = bearing_deg(lon[ia], lat[ia], lon[ib], lat[ib])
            # travel bearing, so a oneway=-1 carriageway points the way you may drive
            node_bearing[a].append(brg if fwd else (brg + 180) % 360)
            node_bearing[b].append(brg if fwd else (brg + 180) % 360)
            if fwd:
                rows.append(ia)
                cols.append(ib)
                vals.append(d)
            if bwd:
                rows.append(ib)
                cols.append(ia)
                vals.append(d)
        for n in nodes:
            node_way[n].add(wid)
            node_levels[n].add(lvl)

    G = csr_matrix((vals, (rows, cols)), shape=(N, N))
    n_comp, comp_label = connected_components(G, directed=True, connection="weak")
    return Graph(node_ids, idx_of, lon, lat, G, node_way, node_levels, node_bearing,
                 comp_label, int(n_comp))


# --------------------------------------------------------------------------
# Section 7: pair each sample with the far kerb.
# --------------------------------------------------------------------------

@dataclass
class Pairs:
    sources: list = field(default_factory=list)
    targets: list = field(default_factory=list)
    straight: list = field(default_factory=list)
    rejections: collections.Counter = field(default_factory=collections.Counter)
    n_candidates: int = 0


def pair_candidates(ways, graph, config=V10, zones=ZONES):
    """The notebook's pairing loop, unchanged except that it returns its state."""
    import numpy as np
    from scipy.spatial import cKDTree

    lon, lat, idx_of, node_ids = graph.lon, graph.lat, graph.idx_of, graph.node_ids
    node_way, node_levels, node_bearing = graph.node_way, graph.node_levels, graph.node_bearing

    LAT0 = float(np.mean(lat))
    xy = np.column_stack([lon * (111320.0 * math.cos(math.radians(LAT0))), lat * 110540.0])
    tree = cKDTree(xy)

    cand = set()
    for _wid, nodes, _fwd, _bwd, hw, divided, _lvl in ways:
        if hw in ARTERIAL and divided:
            cand.update(nodes)
    cand = sorted(n for n in cand if n in idx_of)

    out = Pairs(n_candidates=len(cand))
    rej = out.rejections               # F-8: keyed by (zone, reason)
    seen = set()

    def _note(nid_idx, reason):
        z = zone_of(lon[nid_idx], lat[nid_idx], zones) or ["outside"]
        for zz in z:
            rej[(zz, reason)] += 1

    for k, nid in enumerate(cand):
        i = idx_of[nid]
        in_focus = bool(config.focus_zone) and config.focus_zone in zone_of(lon[i], lat[i], zones)
        stride = config.focus_stride if in_focus else config.sample_stride
        if k % stride:
            continue
        if not node_bearing[nid]:
            _note(i, "no bearing")
            continue
        best, best_d = None, None
        for j in tree.query_ball_point(xy[i], config.cross_max_m):
            if j == i:
                continue
            njd = int(node_ids[j])
            d = haversine_m(lon[i], lat[i], lon[j], lat[j])
            if d < config.cross_min_m:
                continue
            if node_way[nid] & node_way[njd]:
                _note(i, "same way")
                continue
            if not levels_compatible(node_levels[nid], node_levels[njd]):
                _note(i, "grade separated")
                continue
            if not any(is_antiparallel(b1, b2, config.bearing_tol)
                       for b1 in node_bearing[nid] for b2 in node_bearing[njd]):
                _note(i, "not antiparallel")
                continue
            if best_d is None or d < best_d:
                best, best_d = j, d
        if best is None:
            _note(i, "no valid target")
            continue
        key = (min(i, best), max(i, best))
        if key in seen:
            continue
        seen.add(key)
        out.sources.append(i)
        out.targets.append(best)
        out.straight.append(best_d)
        if len(out.sources) >= config.max_samples:
            break
    return out


# --------------------------------------------------------------------------
# B-10: clip to the declared study box. New; the notebooks never did this.
# --------------------------------------------------------------------------

def in_box(lon, lat, bbox):
    x0, y0, x1, y1 = bbox
    return x0 <= lon <= x1 and y0 <= lat <= y1


def clip_pairs(pairs, graph, bbox):
    """Keep pairs whose endpoint A lies inside ``bbox``. Returns (kept, n_excluded).

    Endpoint A because that is the point v1.0 reported as ``lat, lon``, so the
    excluded count is directly comparable with the 1,549 B-10 found.
    """
    kept = Pairs(rejections=pairs.rejections, n_candidates=pairs.n_candidates)
    excluded = 0
    for s, t, st in zip(pairs.sources, pairs.targets, pairs.straight, strict=True):
        if in_box(graph.lon[s], graph.lat[s], bbox):
            kept.sources.append(s)
            kept.targets.append(t)
            kept.straight.append(st)
        else:
            excluded += 1
    return kept, excluded


# --------------------------------------------------------------------------
# Section 9: route every accepted pair.
# --------------------------------------------------------------------------

def route_pairs(graph, pairs, config=V10):
    """Chunked directed Dijkstra, as the notebook. inf means no route within limit."""
    import numpy as np
    from scipy.sparse.csgraph import dijkstra

    net = np.empty(len(pairs.sources))
    chunk = config.route_chunk
    for s in range(0, len(pairs.sources), chunk):
        idxs = pairs.sources[s:s + chunk]
        D = dijkstra(graph.G, directed=True, indices=idxs, limit=config.route_limit_m)
        for r, t in enumerate(pairs.targets[s:s + chunk]):
            net[s + r] = D[r, t]
    return net


# --------------------------------------------------------------------------
# Section 10: records. Same derived columns as v1.0, plus both endpoints.
# --------------------------------------------------------------------------

POINT_COLUMNS = (
    "a_lat", "a_lon", "b_lat", "b_lon", "straight_m", "network_m", "detour_index",
    "null_reason", "a_node_id", "b_node_id", "a_way_ids", "b_way_ids",
    "osm_extract_date", "commit_sha", "study_bbox",
    # v1.0 columns, kept so downstream diagnostics read the file unchanged.
    # lat, lon are endpoint A.
    "lat", "lon", "unreachable", "near_limit", "flagged_high", "diff_component",
    "core_city", "patancheru",
)


def bbox_str(bbox):
    return ",".join(f"{v:.6f}" for v in bbox)


def build_records(graph, pairs, net, config=V10, zones=ZONES, study_bbox=HMDA_BBOX,
                  osm_extract_date=None, sha=None):
    import numpy as np

    lon, lat, node_ids, comp = graph.lon, graph.lat, graph.node_ids, graph.comp_label
    box = bbox_str(study_bbox)
    recs = []
    for i, (si, ti, st) in enumerate(zip(pairs.sources, pairs.targets, pairs.straight,
                                         strict=True)):
        routed = bool(np.isfinite(net[i]))
        di = detour_index(float(net[i]), st)
        diff = bool(comp[si] != comp[ti])
        zs = zone_of(lon[si], lat[si], zones)
        a_id, b_id = int(node_ids[si]), int(node_ids[ti])
        null_reason = None
        if not routed:
            null_reason = "different_component" if diff else "unreachable"
        recs.append({
            "a_lat": round(float(lat[si]), 7), "a_lon": round(float(lon[si]), 7),
            "b_lat": round(float(lat[ti]), 7), "b_lon": round(float(lon[ti]), 7),
            "straight_m": round(float(st), 1),
            "network_m": round(float(net[i]), 1) if routed else None,
            "detour_index": None if di is None else round(float(di), 2),
            "null_reason": null_reason,
            "a_node_id": a_id, "b_node_id": b_id,
            "a_way_ids": ";".join(str(w) for w in sorted(graph.node_way[a_id])),
            "b_way_ids": ";".join(str(w) for w in sorted(graph.node_way[b_id])),
            "osm_extract_date": osm_extract_date,
            "commit_sha": sha,
            "study_bbox": box,
            "lat": round(float(lat[si]), 6), "lon": round(float(lon[si]), 6),
            "unreachable": not routed,
            "near_limit": bool(routed and net[i] > 0.9 * config.route_limit_m),
            "flagged_high": bool(di is not None and di >= config.di_review),
            "diff_component": diff,
            "core_city": "core_city" in zs, "patancheru": "patancheru" in zs,
        })
    return recs


# --------------------------------------------------------------------------
# One call for the whole step, and the export that refuses invalid output.
# --------------------------------------------------------------------------

@dataclass
class PairingRun:
    records: list
    rejections: collections.Counter
    meta: dict


def run_pairing(ways, coords, config=V10, zones=ZONES, study_bbox=HMDA_BBOX,
                osm_extract_date=None, sha=None, graph=None):
    """Graph -> pairs -> clip -> route -> records. ``graph`` may be passed in to
    avoid rebuilding it."""
    graph = graph or build_graph(ways, coords)
    pairs = pair_candidates(ways, graph, config, zones)
    n_paired = len(pairs.sources)
    kept, n_outside = clip_pairs(pairs, graph, study_bbox)
    net = route_pairs(graph, kept, config)
    recs = build_records(graph, kept, net, config, zones, study_bbox, osm_extract_date, sha)
    meta = {
        "config": asdict(config),
        "study_bbox": list(study_bbox),
        "study_bbox_is_declared_hmda": tuple(study_bbox) == HMDA_BBOX,
        "clip_rule": "endpoint A inside study_bbox, applied after pairing, before routing",
        "graph_nodes": graph.n,
        "graph_edges": int(graph.G.nnz),
        "weak_components": graph.n_comp,
        "candidates": pairs.n_candidates,
        "pairs_accepted": n_paired,
        "pairs_outside_box": n_outside,
        "pairs_kept": len(recs),
        "null_routes": collections.Counter(r["null_reason"] for r in recs if r["null_reason"]),
        "osm_extract_date": osm_extract_date,
        "commit_sha": sha,
    }
    return PairingRun(recs, pairs.rejections, meta)


class ExportValidationError(ValueError):
    """A point file failed provenance validation. Nothing was written."""


def write_point_file(records, path, meta=None):
    """Validate, then write ``path`` (CSV) and ``path + '.meta.json'``.

    Raises ExportValidationError, writing nothing, if any record is invalid.
    """
    n_bad, report = validate_export(records)
    if n_bad:
        raise ExportValidationError(
            f"{n_bad} of {len(records)} records failed provenance validation; "
            f"nothing written. First problems: {report[:5]}"
        )
    if not records:
        raise ExportValidationError("no records; an empty point file is not a result")
    tmp = f"{path}.tmp"
    with open(tmp, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=POINT_COLUMNS, extrasaction="raise")
        w.writeheader()
        for r in records:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in POINT_COLUMNS})
    os.replace(tmp, path)
    with open(f"{path}.meta.json", "w") as f:
        json.dump(meta or {}, f, indent=2, default=str)
    return path
