"""The one-night Bengaluru remote check (approved 6 Nov 2026) and the night's queue.

The places file is private and read from arcroad-internal; the job points the standing modules at it and
always points them back at the published Hyderabad places afterwards, so the night's own jobs are unchanged.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "research" / "runner" / "app"))
import server

PLACES = {"status": "CANDIDATE", "selection": "declared", "cities": [{"id": "bengaluru", "c": [77.59, 12.97]}],
          "spots": [{"id": "B01", "a": [77.5, 12.9], "b": [77.5001, 12.9001], "ab": 5000.0, "ba": None}]}


def test_queue_runs_bengaluru_first_only_on_its_night():
    names = [n for n, _ in server.tonight(server.BENGALURU_REMOTE_NIGHT)]
    assert names[0] == "bengaluru_remote" and names.count("bengaluru_remote") == 1
    assert "bengaluru_remote" not in [n for n, _ in server.tonight("2026-11-07")]


def test_sunday_adds_the_viability_brief_last():
    assert server.tonight("2026-11-08")[-1][0] == "viability"
    assert "viability" not in [n for n, _ in server.tonight("2026-11-07")]


def test_points_modules_at_private_places_then_restores(monkeypatch, tmp_path):
    monkeypatch.setattr(server, "OUT", tmp_path)
    monkeypatch.setattr(server.filer, "get", lambda path, log: json.dumps(PLACES))
    seen = {}

    def fake(name):
        def run(log, *a):
            mod = getattr(server, name)
            seen[name] = json.loads(server.openings.get(mod.PLACES_URL))["spots"][0]["id"]
            return json.dumps({"job": name}).encode()
        return run

    for n in ("mapwatch", "openings", "structures", "remote"):
        monkeypatch.setattr(getattr(server, n), "run", fake(n))
    before = server.openings.PLACES_URL
    p = server.job_bengaluru_remote()
    out = json.loads(p.read_text())
    assert seen == {"mapwatch": "B01", "openings": "B01", "structures": "B01", "remote": "B01"}
    assert set(out) >= {"mapwatch", "openings", "structures", "remote"} and out["city"] == "bengaluru"
    assert all(getattr(server, n).PLACES_URL == before for n in ("mapwatch", "openings", "structures", "remote"))
    assert before.startswith("https://arcroad.org/")
