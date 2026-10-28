"""Score a field-day GPS track against the model. Run locally; never commit the GPX.

    python tools/score_drive.py TRACK.gpx data/field/field_day_1_stops.json \
        [--network model_network.csv] [--out out/field_day_1_scores.json]

--network is a CSV with columns id,network_m (the model's A -> B distances,
kept off the field page so the driver cannot be steered by them). Without it,
driven distances are reported and every driven stop reads BETWEEN.
"""

import argparse
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.groundtruth import parse_gpx, score_day


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("gpx")
    ap.add_argument("stops")
    ap.add_argument("--network")
    ap.add_argument("--out", default="out/field_day_scores.json")
    args = ap.parse_args(argv)

    with open(args.gpx, encoding="utf-8") as fh:
        track = parse_gpx(fh.read())
    with open(args.stops, encoding="utf-8") as fh:
        stops = json.load(fh)["stops"]
    network = {}
    if args.network:
        with open(args.network, encoding="utf-8") as fh:
            network = {r["id"]: float(r["network_m"]) for r in csv.DictReader(fh)}

    result = score_day(track, stops, network)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1)
    for r in result["stops"]:
        print(f"{r['id']:>4}  {r['verdict']:<10}  straight {r['straight_m']:>6} m  "
              f"driven {r['driven_m'] if r['driven_m'] is not None else '-':>8}  "
              f"model {r['network_m'] if r['network_m'] is not None else '-':>8}")
    print("counts:", result["counts"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
