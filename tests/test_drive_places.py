"""Every place the /drive/ ride offers is a driven, matched pass, with the same numbers as the field results.

Reporting rule 1 (every number traceable) for the place picker: a place, distance, time or straight-line
figure typed into web/drive/drive.js that drifts from data/field/*-results.json fails here.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JS = (ROOT / "web" / "drive" / "drive.js").read_text(encoding="utf-8")


def field_passes():
    out = {}
    for f in sorted((ROOT / "data" / "field").glob("*-results.json")):
        for p in json.loads(f.read_text(encoding="utf-8")).get("passes", []):
            out[(p["id"], p["dir"])] = p
    return out


def places():
    block = JS[JS.index("var PLACES = {"): JS.index("var PID =")]
    found = {}
    for m in re.finditer(r"(S\d+): \{ road: .*?straight: ([\d.]+)(.*?)\} \} \}", block, re.S):
        drives = dict((d, (float(a), int(b), float(c))) for d, a, b, c in
                      re.findall(r"(ab|ba): \{ m: ([\d.]+), s: (\d+), model: ([\d.]+)", m.group(3)))
        found[m.group(1)] = (float(m.group(2)), drives)
    return found


def test_picker_offers_s18_and_s12():
    assert set(places()) == {"S18", "S12"}


def test_every_offered_pass_matches_the_field_results():
    fp = field_passes()
    for pid, (straight, drives) in places().items():
        assert drives, pid
        for d, (m, s, model) in drives.items():
            p = fp[(pid, d)]
            assert p["verdict"] == "MATCH", (pid, d)
            assert (p["driven_m"], p["seconds"], p["model_m"], p["straight_m"]) == (m, s, model, straight), (pid, d)
