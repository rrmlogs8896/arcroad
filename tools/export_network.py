"""Export the model's A -> B network distance for each field stop, as id,network_m.

    python tools/export_network.py di_points_2026-10-26_c29d9c1.csv \
        data/field/field_day_1_stops.json [--out out/model_network.csv]

The input is the v08 point export written by pipeline.pairing.write_point_file
(columns a_lat, a_lon, b_lat, b_lon, network_m, ...). Each stop is matched to
the export record whose endpoint A and endpoint B both lie within --tol metres
of the stop's sides. Nothing is re-routed: the number written is the number the
model published, so the score compares the drive with that model and no other.

The output is a scoring input, never a field-page input: it goes to out/, which
is gitignored, and must not be committed or shown to the driver (STATE.md).

Stops with no match, or whose record has no route, are listed on stderr and left
out of the CSV; score_drive.py then reports them without a model value.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.geometry import haversine_m

MATCH_TOL_M = 2.0   # the stops file rounds the export's 7 decimals to 6 (about 0.1 m)


def _f(v):
    return None if v in (None, "") else float(v)


def match_stops(records, stops, tol_m=MATCH_TOL_M):
    """-> (rows, problems). rows: [{'id', 'network_m', 'match_m'}]; problems: [(id, why)]."""
    recs = []
    for r in records:
        a_lat, a_lon, b_lat, b_lon = (_f(r.get(k)) for k in ("a_lat", "a_lon", "b_lat", "b_lon"))
        if None in (a_lat, a_lon, b_lat, b_lon):
            continue
        recs.append((a_lat, a_lon, b_lat, b_lon, _f(r.get("network_m")), r.get("null_reason")))
    rows, problems = [], []
    for s in stops:
        if not s.get("b"):
            continue  # photo target: nothing to route
        (sa_lat, sa_lon), (sb_lat, sb_lon) = s["a"], s["b"]
        best = None
        for a_lat, a_lon, b_lat, b_lon, net, why in recs:
            da = haversine_m(sa_lon, sa_lat, a_lon, a_lat)
            if da > tol_m:
                continue
            db = haversine_m(sb_lon, sb_lat, b_lon, b_lat)
            if db > tol_m:
                continue
            if best is None or max(da, db) < best[0]:
                best = (max(da, db), net, why)
        if best is None:
            problems.append((s["id"], f"no export record within {tol_m} m of both sides"))
        elif best[1] is None:
            problems.append((s["id"], f"matched, but the model has no route ({best[2]})"))
        else:
            rows.append({"id": s["id"], "network_m": best[1], "match_m": round(best[0], 2)})
    return rows, problems


REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def safe_out_path(path, repo=REPO) -> bool:
    """False for any path inside the repo other than out/, so the model's distances
    cannot land next to the field page (docs/, web/, data/) and be committed."""
    p, repo = os.path.realpath(path), os.path.realpath(repo)
    if os.path.commonpath([p, repo]) != repo:
        return True  # outside the repo entirely
    return os.path.commonpath([p, os.path.join(repo, "out")]) == os.path.join(repo, "out")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("points_csv")
    ap.add_argument("stops")
    ap.add_argument("--out", default="out/model_network.csv")
    ap.add_argument("--tol", type=float, default=MATCH_TOL_M)
    args = ap.parse_args(argv)

    with open(args.points_csv, encoding="utf-8", newline="") as fh:
        records = list(csv.DictReader(fh))
    with open(args.stops, encoding="utf-8") as fh:
        stops = json.load(fh)["stops"]
    rows, problems = match_stops(records, stops, args.tol)

    if not safe_out_path(args.out):
        print(f"refusing to write {args.out}: inside the repo, only out/ (gitignored) is allowed",
              file=sys.stderr)
        return 2
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "network_m"])
        for r in rows:
            w.writerow([r["id"], r["network_m"]])
    print(f"wrote {len(rows)} stops to {args.out} (keep it off the field page; never commit it)")
    for sid, why in problems:
        print(f"  {sid}: {why}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
