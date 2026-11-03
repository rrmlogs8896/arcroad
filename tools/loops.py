"""Apply the loop rule (docs/PREREG-loop-rule.md) to private GPS tracks. Prints only place, direction,
metres, seconds and verdict: never coordinates. Run locally; never commit a track.

    python3 tools/loops.py TRACK.gpx [TRACK2.gpx ...]
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from pipeline.groundtruth import find_loops, parse_gpx, verdict

ROOT = pathlib.Path(__file__).resolve().parents[1]


def main(paths):
    spots = json.loads((ROOT / "web/globe/data/places.json").read_text())["spots"]
    for path in paths:
        track = parse_gpx(pathlib.Path(path).read_text())
        print(f"== {pathlib.Path(path).name}: {len(track)} points")
        found = False
        for s in spots:
            a, b = (s["a"][1], s["a"][0]), (s["b"][1], s["b"][0])
            for lp in find_loops(track, a, b):
                model = s.get(lp["dir"])
                v = verdict(lp["driven_m"], model) if model else "NO_MODEL"
                print(f"  {s['id']} {lp['dir']} {lp['driven_m']} m {lp['seconds']} s gap {lp['max_gap_s']} s"
                      f" model {model} -> {v}")
                found = True
        if not found:
            print("  no loops at close-set places")


if __name__ == "__main__":
    main(sys.argv[1:])
