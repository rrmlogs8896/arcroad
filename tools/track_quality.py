"""Check a GPS track is fit for scoring, without printing a single coordinate.

    python tools/track_quality.py TRACK.gpx

Run it on a two-minute test recording before a field day, and on the real track
before scoring. It reports what decides POOR_TRACK in pipeline/groundtruth.py:
holes longer than MAX_SAMPLE_GAP_S. It also says whether those holes happened
while the phone was standing still, which is the signature of a logger with a
distance filter (it stops writing points when you stop moving, so a red light
in the middle of a crossing becomes a 30 s hole and the pass reads POOR_TRACK).

Output is counts and durations only. The track itself never leaves the machine.
"""

from __future__ import annotations

import os
import statistics
import sys
from itertools import pairwise

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.geometry import haversine_m
from pipeline.groundtruth import MAX_SAMPLE_GAP_S, parse_gpx

STILL_M = 15.0        # moved less than this across a hole: the phone was standing still
SPIKE_KMH = 120.0     # faster than this between consecutive samples: a GPS jump, not riding


def summarise(track) -> dict:
    """Counts and durations describing a track's sampling. No coordinates."""
    timed = [p for p in track if p[0] is not None]
    out = {
        "points": len(track), "untimed_points": len(track) - len(timed),
        "minutes": None, "km": 0.0, "median_step_s": None,
        "holes_over_limit": 0, "holes_over_limit_while_still": 0, "longest_hole_s": 0.0,
        "duplicate_times": 0, "speed_spikes": 0, "min_step_m": None,
    }
    if len(timed) < 2:
        return out
    steps, gaps = [], []
    for p, q in pairwise(timed):
        dt = q[0] - p[0]
        m = haversine_m(p[2], p[1], q[2], q[1])
        steps.append(m)
        out["km"] += m / 1000
        if dt <= 0:
            out["duplicate_times"] += 1
            continue
        gaps.append(dt)
        if m / dt * 3.6 > SPIKE_KMH:
            out["speed_spikes"] += 1
        if dt > MAX_SAMPLE_GAP_S:
            out["holes_over_limit"] += 1
            if m < STILL_M:
                out["holes_over_limit_while_still"] += 1
    out["minutes"] = round((timed[-1][0] - timed[0][0]) / 60, 1)
    out["km"] = round(out["km"], 2)
    out["median_step_s"] = statistics.median(gaps) if gaps else None
    out["longest_hole_s"] = max(gaps, default=0.0)
    out["min_step_m"] = round(min(steps), 2)
    return out


def advice(s: dict) -> list[str]:
    tips = []
    if s["median_step_s"] is not None and s["median_step_s"] > 1:
        tips.append("logging interval is above 1 s; set it to 1 s")
    if s["holes_over_limit_while_still"]:
        tips.append("points stop while standing still: the logger has a distance filter; "
                    "set minimum displacement to 0 or use a logger that writes every second")
    if s["min_step_m"] is not None and s["min_step_m"] > 1.0 and s["points"] > 60:
        tips.append("no step under 1 m in the whole track: consistent with a distance filter")
    if s["untimed_points"]:
        tips.append("some points carry no time; the scorer cannot check gaps on them")
    return tips


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print(__doc__)
        return 2
    with open(argv[0], encoding="utf-8") as fh:
        s = summarise(parse_gpx(fh.read()))
    for k, v in s.items():
        print(f"{k:>30}  {v}")
    for t in advice(s):
        print("ADVICE:", t)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
