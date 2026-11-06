"""mapwatch asks Overpass once for the whole area and assigns edits to places itself.

5 Nov 2026 night: the per-place queries took about 10 minutes each (24 places, about 4 hours). The single
query must give the same answer as Overpass around:1000 for each place.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "research" / "runner" / "app"))
import mapwatch


def way(points):
    return {"type": "way", "id": 1, "version": 2, "timestamp": "t", "changeset": 9,
            "tags": {"highway": "residential"}, "geometry": [{"lat": a, "lon": b} for a, b in points]}


def test_a_way_passing_within_1_km_counts_even_with_no_vertex_inside():
    # a straight way whose two ends are each ~2 km away but which passes 500 m from the place
    lat, lon = 17.45, 78.38
    w = way([(lat + 0.0045, lon - 0.02), (lat + 0.0045, lon + 0.02)])
    assert mapwatch.near(w, lat, lon)


def test_a_way_1_5_km_away_does_not_count():
    lat, lon = 17.45, 78.38
    assert not mapwatch.near(way([(lat + 0.0135, lon - 0.02), (lat + 0.0135, lon + 0.02)]), lat, lon)


def test_nodes_and_relations():
    lat, lon = 17.45, 78.38
    assert mapwatch.near({"type": "node", "lat": lat + 0.005, "lon": lon}, lat, lon)
    rel = {"type": "relation", "members": [{"type": "node", "lat": lat + 0.02, "lon": lon},
                                           {"type": "way", "geometry": [{"lat": lat, "lon": lon + 0.001},
                                                                        {"lat": lat, "lon": lon + 0.002}]}]}
    assert mapwatch.near(rel, lat, lon)


def test_run_uses_one_query_and_keeps_the_output_shape(monkeypatch):
    places = {"spots": [{"id": "S1", "a": [78.38, 17.45], "b": [78.3801, 17.4501]},
                        {"id": "S2", "a": [78.50, 17.40], "b": [78.5001, 17.4001]}]}
    calls = []

    def get(url, data=None):
        calls.append(url)
        if data is None:
            return json.dumps(places).encode()
        return json.dumps({"elements": [way([(17.452, 78.37), (17.452, 78.39)])]}).encode()

    monkeypatch.setattr(mapwatch, "get", get)
    out = json.loads(mapwatch.run(lambda m: None))
    assert len(calls) == 2
    assert [(p["id"], len(p["edits"]), p["recheck"]) for p in out["places"]] == [("S1", 1, True), ("S2", 0, False)]
    assert out["recheck"] == ["S1"]
