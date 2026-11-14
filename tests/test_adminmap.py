"""The Telangana administrative map job: open map only, polite, one night only."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research" / "runner" / "app"))
import adminmap as a  # noqa: E402


def way(pts):
    return {"type": "way", "role": "outer", "geometry": [{"lon": x, "lat": y} for x, y in pts]}


def test_rings_join_split_ways_into_one_outline():
    rel = {"id": 1, "tags": {"name": "X", "admin_level": "6"},
           "members": [way([(78.0, 17.0), (78.1, 17.0), (78.1, 17.1)]), way([(78.1, 17.1), (78.0, 17.1), (78.0, 17.0)])]}
    f = a.feature(rel, parent=9)
    assert f["parent"] == 9 and len(f["rings"]) == 1 and f["rings"][0][0] == f["rings"][0][-1]


def test_relation_without_ways_has_no_shape_and_is_not_invented():
    assert a.feature({"id": 2, "tags": {"name": "Y"}, "members": []})["rings"] == []


def test_run_packs_counts_and_skips_what_fails(tmp_path, monkeypatch):
    sq = [way([(78.0, 17.0), (78.1, 17.0), (78.1, 17.1), (78.0, 17.1), (78.0, 17.0)])]

    def fake(q):
        if '"admin_level"="4"' in q:
            return [{"type": "relation", "id": 5}]
        if '"admin_level"="5"' in q:
            return [{"type": "relation", "id": 10, "tags": {"name": "D", "admin_level": "5"}, "members": sq}]
        if '"admin_level"="6"' in q:
            return [{"type": "relation", "id": 20, "tags": {"name": "M", "admin_level": "6"}, "members": sq}]
        if "place" in q:
            raise OSError("no answer")
        return []
    monkeypatch.setattr(a, "ask", fake)
    monkeypatch.setattr(a, "PAUSE", 0)
    import json
    import tarfile
    tgz = a.run(lambda m: None, tmp_path)
    with tarfile.open(tgz) as t:
        man = json.load(t.extractfile("adminmap/manifest.json"))
    assert man["counts"]["districts"] == 1 and man["counts"]["mandals"] == 1 and man["counts"]["places"] == 0
    assert any("places not fetched" in n for n in man["notes"]) and man["licence"].startswith("ODbL")


def test_runs_on_one_night_only_and_after_the_standing_jobs():
    src = (ROOT / "research" / "runner" / "app" / "server.py").read_text()
    assert 'ADMINMAP_NIGHT = "2026-11-15"' in src and '[*last, ("adminmap", job_adminmap)]' in src
