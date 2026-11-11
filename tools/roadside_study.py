"""Roadside activity and slow traffic, from the drive-photo labels (docs/PREREG-roadside-activity.md).

    python3 tools/roadside_study.py sample OUT_DIR      draw the 50-photo label check (do this first)
    python3 tools/roadside_study.py agree OUT_DIR       score your labels in OUT_DIR/label-check.csv
    python3 tools/roadside_study.py run OUT_DIR         the comparison (a candidate, never published as is)

Reads the private label files in ~/arcroad-nights/_work. Writes only to OUT_DIR. No photo leaves the iMac.
"""

from __future__ import annotations

import csv
import json
import pathlib
import secrets
import subprocess
import sys
from datetime import UTC, datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pipeline.roadside import combine, label_agreement, label_check_sample, tabulate  # noqa: E402

WORK = pathlib.Path("~/arcroad-nights/_work").expanduser()
LABELS = [WORK / "labels-v1.jsonl", WORK / "n7" / "labels-2026-11-07.jsonl"]
FIELDS = ("congestion", "establishment_spillover", "parking_on_carriageway", "vendors_on_carriageway")
CHOICES = {"congestion": "free/slow/queue/standstill/unsure", "establishment_spillover": "yes/no/unsure",
           "parking_on_carriageway": "none/one_lane_partly/one_lane/more/unsure", "vendors_on_carriageway": "yes/no/unsure"}


def load():
    recs, unparsed = [], 0
    for p in LABELS:
        for line in p.read_text().splitlines():
            r = json.loads(line)
            if r.get("labels"):
                recs.append(r)
            else:
                unparsed += 1
    return recs, unparsed


def commit():
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def sample(out):
    recs, _ = load()
    seed = secrets.randbits(32)
    (out / "label-check-seed.json").write_text(json.dumps({"seed": seed, "commit": commit(),
                                                           "drawn": datetime.now(UTC).isoformat()}) + "\n")
    files = label_check_sample(recs, seed)
    with open(out / "label-check.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["file", *FIELDS])
        w.writerow(["(choices)", *(CHOICES[k] for k in FIELDS)])
        for name in files:
            w.writerow([name, "", "", "", ""])
    print(f"Drew {len(files)} photos (seed {seed}). Open each photo, fill {out / 'label-check.csv'} "
          "without looking at the model's labels, then run: agree")


def agree(out):
    recs, _ = load()
    model = {r["file"]: r["labels"] for r in recs}
    with open(out / "label-check.csv") as f:
        person = {row["file"]: row for row in csv.DictReader(f) if row["file"] != "(choices)"
                  and all(row[k].strip() for k in FIELDS)}
    person = {k: {f: v[f].strip() for f in FIELDS} for k, v in person.items()}
    a = label_agreement(model, person, FIELDS)
    (out / "label-check-result.json").write_text(json.dumps(a, indent=1) + "\n")
    for k, v in a.items():
        print(f"  {k:26} {v['agree']}/{v['n']}  {'passes' if v['passes'] else 'DROPPED (below 80%)'}")


def run(out):
    recs, unparsed = load()
    table = tabulate(recs)
    res = {"job": "roadside-activity-v1", "prereg": "docs/PREREG-roadside-activity.md",
           "status": "CANDIDATE, NOT PUBLISHED", "commit": commit(), "ran": datetime.now(UTC).isoformat(),
           "photos_parsed": len(recs), "photos_unparsed": unparsed, "table": table, "result": combine(table)}
    p = out / f"roadside-{datetime.now(UTC).strftime('%Y%m%dT%H%MZ')}.json"
    p.write_text(json.dumps(res, indent=1) + "\n")
    r = res["result"]
    print(f"{len(recs)} parsed photos ({unparsed} unparsed, left out). Strata with 30+ each side: "
          f"{len(r['strata_used'])}. Difference {r['diff']} interval {r['ci']}: {r['verdict']}.")
    print(f"Wrote {p}. A candidate: an association within strata, not a cause.")


if __name__ == "__main__":
    cmds = {"sample": sample, "agree": agree, "run": run}
    if len(sys.argv) != 3 or sys.argv[1] not in cmds:
        sys.exit(__doc__)
    d = pathlib.Path(sys.argv[2]).expanduser()
    d.mkdir(parents=True, exist_ok=True)
    cmds[sys.argv[1]](d)
