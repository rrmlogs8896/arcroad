"""End to end, offline: tools/loopcost.py run gives no loop figure without a confirmed route, and a sound one with
it (docs/PREREG-cyberabad-loop.md, change of 11 Nov 14:20)."""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import loopcost as tool  # noqa: E402

D = 0.001
ELEMENTS = [{"type": "node", "id": i, "lon": lon, "lat": lat} for i, lon, lat in
            ((1, 78.0, 17.0), (2, 78.0 + D, 17.0), (3, 78.0 + D, 17.0 + D), (4, 78.0, 17.0 + D))] + \
           [{"type": "way", "id": 10 + k, "nodes": n, "tags": {"highway": "secondary"}}
            for k, n in enumerate(([1, 2], [2, 3], [3, 4], [4, 1]))]


def gates(tmp):
    g = {"gates": [{"name": n, "checked": True, "match": {"lon": lon, "lat": lat}} for n, lon, lat in
                   (("A", 78.0, 17.0), ("B", 78.0 + D, 17.0), ("C", 78.0 + D, 17.0 + D), ("D", 78.0, 17.0 + D))]}
    p = tmp / "gates.json"
    p.write_text(json.dumps(g))
    return p


def run(tmp, monkeypatch, route=None):
    monkeypatch.setattr(tool, "GATES", gates(tmp))
    r = tmp / "route.json"
    if route:
        r.write_text(json.dumps(route))
    monkeypatch.setattr(tool, "ROUTE", r)
    monkeypatch.setattr(tool, "overpass", lambda bbox: ({"elements": ELEMENTS}, "q", "2026-11-11T00:00:00"))
    monkeypatch.setattr(tool, "public_router", lambda a, b: {"osrm_m": None, "valhalla_m": None})
    out = tmp / "out"
    tool.run(str(out))
    return json.loads(next(out.glob("loopcost-*[0-9]Z.json")).read_text())


def test_without_a_route_there_is_no_loop_figure(tmp_path, monkeypatch):
    res = run(tmp_path, monkeypatch)
    assert res["loop"]["sound"] is False and res["loop"]["route"] is None
    assert all(r["loop_m"] is None and r["longer"] is None for r in res["rows"])
    assert all(r["today_m"] for r in res["rows"])


def test_with_a_sound_route_the_trips_against_it_go_round(tmp_path, monkeypatch):
    route = {"source": "test", "date": "2026-11-11", "ways": [{"way": 10}, {"way": 11}, {"way": 12}, {"way": 13}]}
    res = run(tmp_path, monkeypatch, route)
    assert res["loop"]["sound"] is True and res["loop"]["gaps"] == []
    against = [r for r in res["rows"] if (r["from"], r["to"]) in (("B", "A"), ("C", "B"), ("D", "C"), ("A", "D"))]
    assert all(r["longer"] for r in against)


def test_a_route_with_a_gap_gives_no_loop_figure(tmp_path, monkeypatch):
    route = {"source": "test", "date": "2026-11-11", "ways": [{"way": 10}, {"way": 12}]}
    res = run(tmp_path, monkeypatch, route)
    assert res["loop"]["sound"] is False and res["loop"]["gaps"]
    assert all(r["loop_m"] is None for r in res["rows"])
