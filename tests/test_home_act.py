"""The home page says what arcroad is for and what a person can do today, with its sources.

5 Nov 2026: Rohit asked for the primary purpose and citizen guidance (before you leave, on the road,
in an emergency; short- and long-term fixes). Every figure in it must match a published drive, and the
rules it states must name the law they come from.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOME = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
ACT = HOME[HOME.index('id="act"'):HOME.index('aria-labelledby="h-tick"')].replace("&nbsp;", " ")


def driven():
    spots = json.loads((ROOT / "web" / "globe" / "data" / "places.json").read_text(encoding="utf-8"))["spots"]
    return {(s["id"], d): v for s in spots for d, v in (s.get("driven") or {}).items()}


def test_section_has_purpose_three_moments_and_two_horizons():
    for t in ("arcroad exists to", "Before you leave", "On the road", "In an emergency", "Short term", "Long term"):
        assert t in ACT, t


def test_rules_and_numbers_name_their_source():
    for t in ("Motor Vehicles Act 1988", "194E", "Driving) Regulations 2017", "Dial-112", "not measured results"):
        assert t in ACT, t


def test_detour_figures_match_the_published_drives():
    d = driven()
    assert round(d[("S18", "ab")]["s"] / 60) == 3 and round(d[("S18", "ba")]["s"] / 60) == 12
    assert f'{d[("S24", "ba")]["m"] / 1000:.1f} km' in ACT
    assert f'{d[("S16", "ba")]["m"] / 1000:.1f} km' in ACT
    assert f'{d[("S12", "ab")]["m"] / 1000:.2f} km' in ACT
    longest = sorted(d.values(), key=lambda v: -v["m"])[:3]
    assert [round(v["m"] / 100) for v in longest] == [116, 23, 22]


def test_findings_band_count_matches_the_field_results():
    n = sum(1 for f in (ROOT / "data" / "field").glob("*-results.json")
            for p in json.loads(f.read_text(encoding="utf-8"))["passes"] if p.get("verdict") == "MATCH")
    assert re.search(rf'<p class="v hot">{n} / {n}</p><p class="k">Driven directions', HOME), n
