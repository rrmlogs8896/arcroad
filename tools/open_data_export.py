"""Build the public open-data table from city collection manifests.

Reads every MANIFEST.json under a folder (written by tools/multicity_collect.py)
and writes one row per city with counts from the open map and the GHSL population,
both measured inside the same collection box. These are counts of what the open map
records, not arcroad measurements: no detour figure is exported here.

Usage:
    python tools/open_data_export.py OUT_FOLDER EXPORT_FOLDER
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import pathlib
import sys

WORLD_FILE = pathlib.Path(__file__).resolve().parents[1] / "data" / "world" / "sample_cities.json"
FIELDS = [
    "city", "country", "osm_extract_date", "run_date", "collection_box", "population_in_box",
    "road_km", "arterial_km", "arterial_divided_pct", "crossings", "footbridges",
    "traffic_signals", "turn_restrictions", "u_turn_restrictions",
    "crossings_per_100k", "footbridges_per_100k", "road_km_per_100k",
]
NOTE = ("Counts of what OpenStreetMap records inside an approximate collection box, "
        "with GHSL 2020 population for the same box. Not measurements of the ground, "
        "not an official boundary, and not a ranking of cities.")
LICENCE = ("Map data (c) OpenStreetMap contributors, ODbL 1.0. Population: GHSL (c) European Union, "
           "JRC, CC BY 4.0. This table: arcroad, ODbL 1.0.")


def _country(city: str, world: dict) -> str:
    return world.get(city, "India")


def _per100k(n, pop):
    return round(n * 100000 / pop, 2) if pop else None


def rows_from(folder: pathlib.Path) -> list[dict]:
    world = {}
    if WORLD_FILE.exists():
        world = {c["id"]: c["country"] for c in json.loads(WORLD_FILE.read_text())["cities"]}
    latest: dict[str, dict] = {}
    for mf in sorted(folder.rglob("MANIFEST.json")):
        m = json.loads(mf.read_text())
        cov = m.get("coverage_in_box")
        if not cov:
            continue  # older manifests only have buffered counts; areas would not match the population
        prev = latest.get(m["city"])
        if prev is None or m["run_date"] >= prev["run_date"]:
            latest[m["city"]] = m
    out = []
    for city, m in sorted(latest.items()):
        cov, pop = m["coverage_in_box"], int(m.get("ghsl_pop_in_box") or 0)
        out.append({
            "city": city.removeprefix("world-"), "country": _country(city, world),
            "osm_extract_date": str(m.get("osm_extract_date") or ""), "run_date": m["run_date"],
            "collection_box": " ".join(f"{v:.3f}" for v in m["collection_box"]),
            "population_in_box": pop,
            "road_km": cov["road_km"], "arterial_km": cov["arterial_km"],
            "arterial_divided_pct": cov["arterial_divided_pct"], "crossings": cov["crossings"],
            "footbridges": cov["footbridges"], "traffic_signals": cov["traffic_signals"],
            "turn_restrictions": cov["turn_restrictions"], "u_turn_restrictions": cov["u_turn_restrictions"],
            "crossings_per_100k": _per100k(cov["crossings"], pop),
            "footbridges_per_100k": _per100k(cov["footbridges"], pop),
            "road_km_per_100k": _per100k(cov["road_km"], pop),
        })
    return out


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    src, dst = pathlib.Path(argv[0]), pathlib.Path(argv[1])
    dst.mkdir(parents=True, exist_ok=True)
    rows = rows_from(src)
    if not rows:
        raise SystemExit("No manifests with coverage_in_box found.")
    stamp = dt.date.today().isoformat()
    csv_name = f"arcroad_open_city_counts_{stamp}.csv"
    with open(dst / csv_name, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    payload = {"generated": stamp, "csv": csv_name, "note": NOTE, "licence": LICENCE, "fields": FIELDS, "cities": rows}
    (dst / "cities.json").write_text(json.dumps(payload, indent=1, ensure_ascii=False))
    print(f"{len(rows)} cities -> {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
