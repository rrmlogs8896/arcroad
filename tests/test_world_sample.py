"""World sample cities: groundwork registry stays well-formed and desk-only."""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "data" / "world" / "sample_cities.json").read_text())


def test_status_is_desk_only():
    assert "DESK" in DATA["status"] and "NOTHING" in DATA["status"]


def test_cities_well_formed():
    ids = set()
    for c in DATA["cities"]:
        assert c["id"].startswith("world-") and c["id"] not in ids
        ids.add(c["id"])
        x0, y0, x1, y1 = c["bbox"]
        assert -180 <= x0 < x1 <= 180 and -90 <= y0 < y1 <= 90
        assert (x1 - x0) < 1.5 and (y1 - y0) < 1.5, "box too large for a city"
        assert c["geofabrik_scope"].startswith("/") and c["problem"] and c["metric"]


def test_collector_reads_world_registry():
    import sys
    sys.path.insert(0, str(ROOT))
    from tools import multicity_collect as m
    w = m.world_cities()
    assert set(w) == {c["id"] for c in DATA["cities"]}
    assert all(isinstance(scope, str) for _, scope in w.values())
