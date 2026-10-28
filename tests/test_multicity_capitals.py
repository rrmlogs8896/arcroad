"""State and UT capitals (28 Oct 2026): every capital is either collected or excluded
with a written reason, every collection box is sane, and the workflow's city list
matches the code, so no capital can be silently dropped."""

import importlib.util
import json
import pathlib
import re

import pytest

_ROOT = pathlib.Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def mc():
    pytest.importorskip("osmium")
    spec = importlib.util.spec_from_file_location("multicity_collect", _ROOT / "tools" / "multicity_collect.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_capitals_register_covers_all_36_states_and_uts(mc):
    # 28 states + 8 UTs = 36; J&K has two seasonal capitals, so 37 entries.
    assert len(mc.CAPITALS) == 37


def test_capitals_register_points_at_real_cities_or_a_reason(mc):
    for place, target in mc.CAPITALS.items():
        assert target in mc.CITIES or target.startswith("EXCLUDED: "), place


def test_capitals_hill_exclusions_are_exactly_the_decided_set(mc):
    hill = sorted(p for p, t in mc.CAPITALS.items() if t.startswith("EXCLUDED"))
    assert len(hill) == 8, hill


def test_capitals_boxes_are_sane(mc):
    for name, (x0, y0, x1, y1) in mc.CITIES.items():
        assert x0 < x1 and y0 < y1, name
        assert 68 <= x0 and x1 <= 98 and 6 <= y0 and y1 <= 38, f"{name} outside India's extent"
        assert (x1 - x0) <= 0.8 and (y1 - y0) <= 0.8, f"{name} box larger than the HMDA-sized cap"


def test_capitals_workflow_list_matches_code(mc):
    wf = (_ROOT / ".github" / "workflows" / "multicity.yml").read_text()
    listed = json.loads(re.search(r"ALL='(\[[^']*\])'", wf).group(1))
    assert sorted(listed) == sorted(mc.CITIES)
