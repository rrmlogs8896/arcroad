"""Buses through the proposed Hi-Tech City loop area today, from a TGSRTC GTFS zip (docs/PREREG-cyberabad-loop.md).

    python3 tools/bus_loop.py GTFS.zip OUT_DIR

Uses the checked gates in data/loop/gates.json. Writes OUT_DIR/buses-<UTC time>.json, a candidate that stays private
until reviewed. With a confirmed route (data/loop/route.json, "gate_order"), patterns that run against the loop are
marked; without one, none are.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import sys
from datetime import UTC, datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pipeline.gtfsloop import GATE_RADIUS_M, WEEKDAY, against, patterns, read  # noqa: E402


def main(gtfs, out_dir):
    gates = [{"name": g["name"], "lon": g["match"]["lon"], "lat": g["match"]["lat"]}
             for g in json.loads((ROOT / "data/loop/gates.json").read_text())["gates"] if g["checked"] and g["match"]]
    route_file = ROOT / "data/loop/route.json"
    loop_order = json.loads(route_file.read_text()).get("gate_order") if route_file.exists() else None
    feed = read(gtfs)
    r = patterns(feed, gates)
    rows = sorted(({"route": k[0], "gates": list(k[1]), "trips": n,
                    "against_loop": [list(p) for p in against(k[1], loop_order)] if loop_order else None}
                   for k, n in r["patterns"].items()), key=lambda x: -x["trips"])
    info = (feed["feed_info"] or [{}])[0]
    out = {"job": "bus-loop-v1", "prereg": "docs/PREREG-cyberabad-loop.md", "status": "CANDIDATE, NOT PUBLISHED",
           "feed": {"file": pathlib.Path(gtfs).name, "sha256": hashlib.sha256(pathlib.Path(gtfs).read_bytes()).hexdigest(),
                    "publisher": info.get("feed_publisher_name"), "version": info.get("feed_version"),
                    "start": info.get("feed_start_date"), "end": info.get("feed_end_date")},
           "rule": {"gate_radius_m": GATE_RADIUS_M, "weekday": WEEKDAY}, "gates": [g["name"] for g in gates],
           "trips_counted": r["trips_counted"], "trips_in_area": r["trips_in_area"], "stops_in_area": r["stops_in_area"],
           "calendar_missing": r["calendar_missing"], "patterns": rows}
    out_dir = pathlib.Path(out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / f"buses-{datetime.now(UTC).strftime('%Y%m%dT%H%MZ')}.json"
    p.write_text(json.dumps(out, indent=1) + "\n")
    multi = [x for x in rows if len(x["gates"]) >= 2]
    print(f"{r['stops_in_area']} stops within {GATE_RADIUS_M:.0f} m of the gates; {r['trips_in_area']} {WEEKDAY} trips "
          f"serve them, {sum(x['trips'] for x in multi)} of them between two or more gates, on "
          f"{len({x['route'] for x in multi})} routes.{' Calendar missing: every trip counted.' if r['calendar_missing'] else ''}")
    for x in rows[:12]:
        print(f"  {x['route']:>10}  {' > '.join(x['gates']):60}  {x['trips']} trips")
    print(f"Wrote {p}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
