"""Write web/cost/baselines.json: the cost calculator's baseline cards, from arcroad's own driven passes.

    python3 tools/build_cost_baselines.py          # rewrite the file
    python3 tools/build_cost_baselines.py --check  # exit 1 if it is out of date (CI)

Every card number traces to a driven pass in data/field/*-results.json (rule 1). Only passes that matched the
model count, and places left out by the road-class rule are excluded. Extra distance is driven minus straight
line; detour speed is driven distance over driven time. The other settings are the calculator's own defaults,
each sourced on the page.
"""

from __future__ import annotations

import datetime as dt
import glob
import json
import os
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from build_field_page import out_of_scope  # noqa: E402

OUT = os.path.join(ROOT, "web", "cost", "baselines.json")


def passes():
    scope = out_of_scope()
    rows = []
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "field", "*-results.json"))):
        with open(f, encoding="utf-8") as fh:
            for p in json.load(fh)["passes"]:
                if p["verdict"] != "MATCH" or p["id"] in scope or p.get("straight_m") is None or not p.get("seconds"):
                    continue
                rows.append({"place": p["id"], "dir": p["dir"], "date": p["date"],
                             "extra_km": round((p["driven_m"] - p["straight_m"]) / 1000, 2),
                             "kmh": round(p["driven_m"] / p["seconds"] * 3.6, 1)})
    return rows


def build():
    rows = passes()
    km = [r["extra_km"] for r in rows]
    kmh = [r["kmh"] for r in rows]
    shortest = min(rows, key=lambda r: r["extra_km"])
    longest = max(rows, key=lambda r: r["extra_km"])
    slowest = min(rows, key=lambda r: r["kmh"])
    base = {"trips": 2, "days": 300, "occ": 1, "veh": "tw"}

    def card(key, title, line, k, s, src):
        return {"key": key, "title": title, "line": line, "set": dict(base, km=k, spd=round(s)), "source": src}

    def one(r):
        d = dt.date.fromisoformat(r["date"])
        return f"Place {r['place']}, driven {d.day} {d:%b %Y}"

    cards = [
        card("median", "Typical crossing", "The middle of every crossing we have driven", round(statistics.median(km), 2),
             statistics.median(kmh), f"Median of {len(rows)} driven passes at {len({r['place'] for r in rows})} places"),
        card("short", "Shortest we drove", "The least a crossing has cost on our drives", shortest["extra_km"],
             shortest["kmh"], one(shortest)),
        card("long", "Longest we drove", "The most a crossing has cost on our drives", longest["extra_km"],
             longest["kmh"], one(longest)),
        card("slow", "Peak-hour crawl", "The slowest crossing we drove, same distance at its real speed",
             slowest["extra_km"], slowest["kmh"], one(slowest)),
    ]
    dates = sorted({r["date"] for r in rows})
    first, last = (dt.date.fromisoformat(x) for x in (dates[0], dates[-1]))
    when = (f"{first.day} to {last.day} {last:%b %Y}" if (first.year, first.month) == (last.year, last.month)
            else f"{first.day} {first:%b} to {last.day} {last:%b %Y}")
    return {"built_from": "data/field/*-results.json (passes that matched the model, road-class rule applied)",
            "drives": when, "drive_dates": [dates[0], dates[-1]], "passes": rows, "cards": cards,
            "assumptions": "Two crossings a day, 300 days a year, one person on a petrol two-wheeler "
                           "(about 73% of Telangana's vehicles). Every other setting is the calculator's default."}


def keep_mark(data):
    """Keep the build mark the fingerprint tool gave this file (every published data file carries one)."""
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as fh:
            mark = json.load(fh).get("_build")
        if mark:
            return {**data, "_build": mark}
    return data


if __name__ == "__main__":
    text = json.dumps(keep_mark(build()), indent=1, ensure_ascii=False) + "\n"
    if "--check" in sys.argv:
        with open(OUT, encoding="utf-8") as fh:
            sys.exit(0 if fh.read() == text else "web/cost/baselines.json is out of date: run tools/build_cost_baselines.py")
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(f"wrote {os.path.relpath(OUT, ROOT)}")
