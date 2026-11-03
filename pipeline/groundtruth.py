"""Ground truth: score a driven GPS track against the model's network distances.

This is the Phase 2b check. Until a modelled A -> B distance has been compared
with a driven one, every arcroad value is a candidate (AGENTS.md).

Rule 5, written before any drive is scored (28 Oct 2026, ahead of Field Day 1):

  Hypothesis      The model's network distance is what a legal driver must
                  actually travel from side A to side B.
  Competing       The map is missing a legal connection (a median opening, a
  explanation     U-turn, a slip road), so the real legal drive is far shorter
                  and the "detour" is a hole in OpenStreetMap.
  What separates  The driven distance. Near the model's value supports the
  them            hypothesis; well under it supports the competing explanation.
                  Over it says nothing about the model (the driver may simply
                  have taken a longer way) and is reported separately.

Gate (fixed here, never adjusted after seeing results):

  MATCH        |driven - network| <= max(MATCH_ABS_M, MATCH_REL * network)
  SHORTER      driven < SHORTER_REL * network   -> the map is likely missing a link
  LONGER       driven > network + tolerance       -> uninformative about the model
  BETWEEN      anything else                      -> review by hand
  NOT_DRIVEN   no A-then-B pass in the track
  POOR_TRACK   a pass exists but the samples are too sparse to measure it

Privacy: a raw track shows where the driver lives and went. This module returns
per-stop numbers only, never track coordinates, and raw GPX files are never
committed to this repository.
"""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from datetime import datetime
from itertools import pairwise

from pipeline.geometry import haversine_m

# --- the pre-registered gate (see module docstring; do not tune after results) ---
MATCH_ABS_M = 150.0      # GPS noise plus where exactly "A" and "B" are taken
MATCH_REL = 0.25         # lane choice and turn geometry on a 1-3 km loop
SHORTER_REL = 0.5        # half the modelled distance: a real missing link, not noise

# --- what counts as having driven a stop ---
VISIT_RADIUS_M = 40.0    # phone GPS on a divided road; A and B sit 12-60 m apart
MAX_PASS_S = 1800.0      # an A -> B pass longer than 30 minutes is not one crossing
MAX_SAMPLE_GAP_S = 15.0  # OsmAnd records every 1 s; a 15 s hole can hide a turn
# B-15 (1 Nov 2026): "nearer to B than to A" is not "at B". The 31 Oct remote run produced
# 25 false passes (3-21 m "driven" against 13-58 m straight): a vehicle on one carriageway
# drifted from nearer-A to nearer-B without ever crossing, because A and B are often offset
# along the road. A pass now has to come within END_REACH_M of both points. Added after
# seeing that run, as a bug fix, before any further run; it can only drop passes (no
# evidence), never create a SHORTER, so it errs on the safe side.
END_REACH_M = 10.0       # a car on the right carriageway passes A or B within a lane plus GPS error

VERDICTS = ("MATCH", "SHORTER", "LONGER", "BETWEEN", "NOT_DRIVEN", "POOR_TRACK")


def parse_gpx(text: str) -> list[tuple[float | None, float, float]]:
    """Track points as (unix_seconds or None, lat, lon), in file order.

    Namespace-agnostic, because OsmAnd, Strava and phone exporters differ.
    """
    root = ET.fromstring(text)
    out = []
    for el in root.iter():
        if el.tag.rsplit("}", 1)[-1] != "trkpt":
            continue
        lat, lon = float(el.get("lat")), float(el.get("lon"))
        t = None
        for child in el:
            if child.tag.rsplit("}", 1)[-1] == "time" and child.text:
                t = datetime.fromisoformat(child.text.strip().replace("Z", "+00:00")).timestamp()
        out.append((t, lat, lon))
    return out


MIN_RUN = 3              # samples in a row on one side before it counts as being there


def _side(pt, a, b, radius):
    """'A', 'B' or None: the nearer side, if within radius.

    Nearest-side, not a plain radius test, because A and B sit 12-60 m apart on
    the Field Day stops, closer than the visit radius itself.
    """
    da = haversine_m(pt[2], pt[1], a[1], a[0])
    db = haversine_m(pt[2], pt[1], b[1], b[0])
    if min(da, db) > radius:
        return None
    return "A" if da <= db else "B"


def _runs(labels, min_run):
    """(label, first, last) for each run of A or B at least min_run long.

    Shorter runs are GPS jitter (a parked phone flickering towards the other
    side) and are dropped, so they can never form a spurious 10 m pass.
    """
    runs, k, n = [], 0, len(labels)
    while k < n:
        m = k
        while m + 1 < n and labels[m + 1] == labels[k]:
            m += 1
        if labels[k] is not None and m - k + 1 >= min_run:
            runs.append((labels[k], k, m))
        k = m + 1
    return runs


def find_pass(track, a, b, radius=VISIT_RADIUS_M, max_pass_s=MAX_PASS_S, min_run=MIN_RUN, accept=None):
    """Indices (i, j) of the shortest A-then-B pass, or None.

    i is the LAST sample of a stay at A, j the FIRST sample of the next stay at
    B, so time parked at either end is not counted as driving. a and b are
    (lat, lon).

    accept(pt, side) -> bool, optional: a further test that a sample really is on
    that side, e.g. that it lies on side B's carriageway in the road network and
    not merely nearer to B (B-15). A pass must also come within END_REACH_M of A
    during its stay at A, and of B during its stay at B.
    """
    labels = []
    for pt in track:
        side = _side(pt, a, b, radius)
        if side is not None and accept is not None and not accept(pt, side):
            side = None
        labels.append(side)
    runs = _runs(labels, min_run)

    def reaches(lo, hi, p):
        return min(haversine_m(track[k][2], track[k][1], p[1], p[0]) for k in range(lo, hi + 1)) <= END_REACH_M

    # A run that never comes within END_REACH_M of its own point is passing on the other
    # carriageway (B-15), so it is dropped before pairing: it must not be counted as being
    # there, and must not stand between a real stay at A and a real stay at B. Declared
    # method change of 2 Nov 2026 (before: only adjacent runs were paired, so such a run
    # blocked the Hafeezpet flyover loop); applied to every drive, not one.
    runs = [r for r in runs if reaches(r[1], r[2], a if r[0] == "A" else b)]
    best = None
    for (l1, _i0, i), (l2, j, _j1) in pairwise(runs):
        if (l1, l2) != ("A", "B"):
            continue
        ti, tj = track[i][0], track[j][0]
        if ti is not None and tj is not None and tj - ti > max_pass_s:
            continue
        length = path_length_m(track, i, j)
        # A pass shorter than half the straight line (or than the straight line minus both end
        # tolerances, if that is larger) cannot be a crossing: it is GPS jitter while stopped or
        # passing along the road (3 Nov 2026 drive, B-16). It is skipped so it cannot win over a
        # real, longer loop. Declared method change of 3 Nov 2026, applied to every drive on file.
        straight = haversine_m(a[1], a[0], b[1], b[0])
        if length < max(straight - 2 * END_REACH_M, 0.5 * straight):
            continue
        if best is None or length < best[2]:
            best = (i, j, length)
    return None if best is None else (best[0], best[1])


def path_length_m(track, i, j) -> float:
    return sum(
        haversine_m(track[k][2], track[k][1], track[k + 1][2], track[k + 1][1])
        for k in range(i, j)
    )


def max_gap_s(track, i, j) -> float | None:
    times = [track[k][0] for k in range(i, j + 1)]
    if any(t is None for t in times):
        return None
    return max((b - a for a, b in pairwise(times)), default=0.0)


def verdict(driven_m: float, network_m: float) -> str:
    tol = max(MATCH_ABS_M, MATCH_REL * network_m)
    if abs(driven_m - network_m) <= tol:
        return "MATCH"
    if driven_m < SHORTER_REL * network_m:
        return "SHORTER"
    if driven_m > network_m + tol:
        return "LONGER"
    return "BETWEEN"


def score_stop(track, stop: dict, network_m: float | None) -> dict:
    """One stop -> a row of numbers. Never returns track coordinates."""
    a, b = tuple(stop["a"]), tuple(stop["b"])
    row = {
        "id": stop["id"],
        "straight_m": round(haversine_m(a[1], a[0], b[1], b[0]), 1),
        "network_m": network_m,
        "driven_m": None,
        "minutes": None,
        "max_gap_s": None,
        "verdict": "NOT_DRIVEN",
    }
    found = find_pass(track, a, b)
    if found is None:
        return row
    i, j = found
    row["driven_m"] = round(path_length_m(track, i, j), 1)
    # A short pass that moves ALONG the road, not across it, went past both points on one carriageway
    # (2 Nov 2026 commute; the same artefact B-15 removes from Mapillary). A real straight-over crossing
    # moves across, in the direction from A to B, and still counts (it is the evidence of map lag).
    if row["driven_m"] < row["straight_m"] * 0.9:
        (_, la1, lo1), (_, la2, lo2) = track[i][:3], track[j][:3]
        k = math.cos(math.radians((a[0] + b[0]) / 2))
        mv = ((lo2 - lo1) * k, la2 - la1)
        ab = ((b[1] - a[1]) * k, b[0] - a[0])
        nmv, nab = math.hypot(*mv), math.hypot(*ab)
        across = (mv[0] * ab[0] + mv[1] * ab[1]) / (nmv * nab) if nmv and nab else 0.0
        if across < 0.5:
            row["driven_m"] = None
            row["passed_by"] = True
            return row
    gap = max_gap_s(track, i, j)
    row["max_gap_s"] = gap
    if track[i][0] is not None and track[j][0] is not None:
        row["minutes"] = round((track[j][0] - track[i][0]) / 60, 1)
    if gap is None or gap > MAX_SAMPLE_GAP_S:
        row["verdict"] = "POOR_TRACK"
    elif network_m is None:
        row["verdict"] = "BETWEEN"  # driven, but nothing to compare against yet
    else:
        row["verdict"] = verdict(row["driven_m"], network_m)
    return row


def score_day(track, stops: list[dict], network: dict) -> dict:
    """Every stop scored, plus counts. Skipped and undriven stops stay in the count."""
    rows = [score_stop(track, s, network.get(s["id"])) for s in stops if s.get("b")]
    counts = {v: sum(r["verdict"] == v for r in rows) for v in VERDICTS}
    return {"stops": rows, "counts": counts}
