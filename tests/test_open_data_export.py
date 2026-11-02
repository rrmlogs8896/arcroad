"""Open-data export: one row per city, box-matched counts only, no detour figures."""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from tools import open_data_export as ode

COV = {"road_km": 1000.0, "arterial_km": 200.0, "arterial_divided_pct": 40.0, "crossings": 50,
       "footbridges": 5, "traffic_signals": 30, "turn_restrictions": 12, "u_turn_restrictions": 3,
       "military_tagged_stripped": 0}


def _mf(folder, city, date, cov=True):
    d = folder / city / date
    d.mkdir(parents=True)
    m = {"city": city, "run_date": date, "collection_box": [1, 2, 3, 4], "osm_extract_date": date,
         "ghsl_pop_in_box": 500000, "coverage_on_buffered_extract": COV}
    if cov:
        m["coverage_in_box"] = COV
    (d / "MANIFEST.json").write_text(json.dumps(m))


def test_latest_run_per_city_and_ratios(tmp_path):
    _mf(tmp_path, "pune", "2026-10-01")
    _mf(tmp_path, "pune", "2026-11-02")
    _mf(tmp_path, "world-manila", "2026-11-02")
    _mf(tmp_path, "chennai", "2026-11-02", cov=False)  # old manifest: skipped
    rows = ode.rows_from(tmp_path)
    assert [r["city"] for r in rows] == ["pune", "manila"]
    assert rows[0]["run_date"] == "2026-11-02"
    assert rows[1]["country"] == "Philippines"
    assert rows[0]["crossings_per_100k"] == 10.0


def test_no_detour_fields():
    assert not any("detour" in f or "index" in f for f in ode.FIELDS)
