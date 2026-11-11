"""Cost calculator baselines (11 Nov 2026): every card traces to arcroad's own matched drives, out-of-scope places
never count, and the published file is current."""
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_cost_baselines as b  # noqa: E402
from build_field_page import out_of_scope  # noqa: E402


def test_file_is_current():
    r = subprocess.run([sys.executable, str(ROOT / "tools/build_cost_baselines.py"), "--check"], capture_output=True,
                       text=True)
    assert r.returncode == 0, r.stderr


def test_only_matched_in_scope_passes_count():
    scope = set(out_of_scope())
    rows = b.passes()
    assert rows and not {r["place"] for r in rows} & scope
    assert all(r["extra_km"] > 0 and r["kmh"] > 0 for r in rows)


def test_cards_are_the_median_and_the_extremes_of_those_passes():
    d = json.loads((ROOT / "web/cost/baselines.json").read_text())
    km = sorted(r["extra_km"] for r in d["passes"])
    cards = {c["key"]: c["set"] for c in d["cards"]}
    assert cards["short"]["km"] == km[0] and cards["long"]["km"] == km[-1]
    assert min(km) <= cards["median"]["km"] <= max(km)
    assert cards["slow"]["spd"] == round(min(r["kmh"] for r in d["passes"]))
    assert all(c["set"]["veh"] == "tw" for c in d["cards"])


def test_the_page_loads_the_cards_and_offers_them_as_buttons():
    page = (ROOT / "web/cost/index.html").read_text()
    assert 'id="bases-grid"' in page and 'fetch("baselines.json"' in page


def test_every_card_value_lands_exactly_on_the_sliders():
    """11 Nov 2026: the distance slider moved in 0.05 km steps, so a 2.28 km card loaded as 2.30 km and showed a
    different yearly cost from the one on the card."""
    import re
    page = (ROOT / "web/cost/index.html").read_text()
    step = {m.group(1): float(m.group(2)) for m in re.finditer(r'<input type="range" id="(\w+)"[^>]*step="([\d.]+)"', page)}
    for c in json.loads((ROOT / "web/cost/baselines.json").read_text())["cards"]:
        for k in ("km", "spd"):
            v = c["set"][k]
            assert abs(round(v / step[k]) * step[k] - v) < 1e-9, (c["key"], k, v, step[k])
