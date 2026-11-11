"""U-turn openings worth a second look, Cyberabad IT corridor (docs/PREREG-uturn-spacing.md).

    python3 tools/uturn_study.py OUT_DIR

Fetches one OpenStreetMap extract from Overpass, finds median openings, flags them, records a random seed, then
draws the ground-check sample. Writes OUT_DIR/uturns-<UTC time>.json and .geojson. A candidate: nothing is
published until the ground check passes (7 of 10).
"""

from __future__ import annotations

import json
import pathlib
import secrets
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import UTC, datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pipeline.medians import DRIVABLE, find_openings, flag, ground_sample, junctions, summarise  # noqa: E402

AREA = (17.40, 78.33, 17.47, 78.42)  # south, west, north, east: pre-registered
OVERPASS = "https://overpass-api.de/api/interpreter"
UA = {"User-Agent": "arcroad/1.0 (https://arcroad.org; hello@arcroad.org)"}


def fetch():
    s, w, n, e = AREA
    cls = "|".join(sorted(DRIVABLE))
    q = (f'[out:json][timeout:180];(way["highway"~"^({cls})$"]({s},{w},{n},{e});'
         f'node["highway"="traffic_signals"]({s},{w},{n},{e}););(._;>;);out body;')
    for attempt in range(3):
        try:
            req = urllib.request.Request(OVERPASS, data=urllib.parse.urlencode({"data": q}).encode(), headers=UA)
            with urllib.request.urlopen(req, timeout=240) as r:
                return json.loads(r.read()), q, datetime.now(UTC).isoformat()
        except Exception as e:  # Overpass is busy at times: retry, then give up loudly
            print(f"Overpass busy ({e}); retry {attempt + 1} in 60 s")
            time.sleep(60)
    sys.exit("Overpass did not answer after three tries.")


def main(out_dir):
    osm, query, fetched = fetch()
    ops = find_openings(osm["elements"])
    flag(ops, junctions(osm["elements"], ops))
    seed = secrets.randbits(32)  # written to the results before the draw
    sample = ground_sample(ops, seed)
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    out = {"job": "uturn-spacing-v1", "prereg": "docs/PREREG-uturn-spacing.md", "status": "CANDIDATE, NOT PUBLISHED",
           "commit": commit, "area": AREA,
           "extract": {"source": "Overpass API (OpenStreetMap, ODbL)", "fetched": fetched, "query": query},
           "summary": summarise(ops), "seed": seed,
           "ground_check": [{"index": i, "lon": round(ops[i]["lon"], 6), "lat": round(ops[i]["lat"], 6),
                             "road": ops[i]["road"], "real": None} for i in sample],
           "openings": ops}
    out_dir = pathlib.Path(out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / f"uturns-{datetime.now(UTC).strftime('%Y%m%dT%H%MZ')}.json"
    p.write_text(json.dumps(out, indent=1) + "\n")
    feats = [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [o["lon"], o["lat"]]},
              "properties": {k: o[k] for k in ("road", "second_look", "close_to_opening", "next_to_junction",
                                               "nearest_opening_m", "nearest_junction_m")}} for o in ops]
    p.with_suffix(".geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}))
    s = out["summary"]
    print(f"{s['openings']} median openings in the IT corridor; {s['second_look']} worth a second look "
          f"(share {s['share']}): {s['close_to_opening']} close to another opening, {s['next_to_junction']} next to "
          f"a junction. Ground-check sample: {len(sample)} openings (seed {seed}).")
    for road, r in list(s["by_road"].items())[:8]:
        print(f"  {road[:40]:40} {r['second_look']:>3} of {r['openings']}")
    print(f"Wrote {p}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
