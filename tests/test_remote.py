import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "research" / "runner" / "app"))
import remote


def test_unreadable_or_odd_replies_become_unclear_never_a_guess():
    assert remote.parse_label("no json here")["gap"] == "unclear"
    assert remote.parse_label('{"median_visible": true, "gap": "maybe"}')["gap"] == "unclear"
    assert remote.parse_label('Sure: {"median_visible": true, "gap": "no", "why": "solid divider"}')["gap"] == "no"


def test_search_box_is_about_40_m_each_way():
    _w, _s, e, n = remote.bbox_around(17.47, 78.38, 40)
    assert abs(remote.metres(17.47, 78.38, n, 78.38) - 40) < 0.5
    assert abs(remote.metres(17.47, 78.38, 17.47, e) - 40) < 0.5


def test_router_agreement_needs_both_routers():
    rc = {"rows": [{"id": "S1", "osrm": {"class": "AGREES"}, "valhalla": {"class": "AGREES"}},
                   {"id": "S1", "osrm": {"class": "AGREES"}, "valhalla": {"class": "ROUTER_LONGER"}}]}
    assert remote.router_agree(rc, "S1") == {"directions": 2, "both_agree": 1}
    assert remote.router_agree(None, "S1") is None


def test_without_keys_the_job_skips_and_says_so(monkeypatch):
    monkeypatch.delenv("MAPILLARY_TOKEN", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    places = {"spots": [{"id": "S1", "a": [78.38, 17.47], "b": [78.3801, 17.4701]}]}
    monkeypatch.setattr(remote, "get", lambda url, data=None: json.dumps(places).encode())
    out = json.loads(remote.run(lambda m: None, {"routercheck": None, "mapwatch": None}))
    assert out["photo_source"].startswith("SKIPPED") and out["ai_sorting"].startswith("SKIPPED")
    assert out["review_list"] == []
