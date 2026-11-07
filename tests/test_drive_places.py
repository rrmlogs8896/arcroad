"""Every place the /drive/3d/ ride offers is a driven, matched pass, with the same numbers as the field results.

Reporting rule 1 (every number traceable) for the place picker: a place, distance, time or straight-line
figure typed into web/drive/3d/drive.js that drifts from data/field/*-results.json fails here.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JS = (ROOT / "web" / "drive" / "3d" / "drive.js").read_text(encoding="utf-8")


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


MAP = (ROOT / "web" / "drive" / "index.html").read_text(encoding="utf-8")


def map_places():
    block = MAP[MAP.index("var P = ["): MAP.index("var THREE_D")]
    out = {}
    for m in re.finditer(r"\{ id: '(S\d+)'.*?st: ([\d.]+), ab: ([\d.]+), ba: ([\d.]+),\s*d: \{(.*?)\} \} \}", block, re.S):
        drives = {d: (float(a), int(b)) for d, a, b in re.findall(r"(ab|ba): \{ m: ([\d.]+), s: (\d+)", m.group(5))}
        out[m.group(1)] = (float(m.group(2)), {"ab": float(m.group(3)), "ba": float(m.group(4))}, drives)
    return out


def test_map_view_figures_match_the_field_results():
    """The /drive/ map view types its fallback figures in; each must equal the published pass."""
    fp, found = field_passes(), map_places()
    assert len(found) == 7, sorted(found)
    for pid, (straight, model, drives) in found.items():
        for d, (m, s) in drives.items():
            p = fp[(pid, d)]
            assert p["verdict"] == "MATCH", (pid, d)
            assert (p["driven_m"], p["seconds"], p["straight_m"], p["model_m"]) == (m, s, straight, model[d]), (pid, d)


def test_map_view_shows_every_matched_pass_for_its_places():
    found = map_places()
    for (pid, d), p in field_passes().items():
        if pid in found and p["verdict"] == "MATCH":
            assert d in found[pid][2], (pid, d)
