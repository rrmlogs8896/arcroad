import json
import pathlib
import sys
import typing
import urllib.parse

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


def test_a_photo_showing_a_gap_goes_to_a_person_even_when_routers_disagree(monkeypatch):
    """5 Nov review: 'gap visible' contradicts the model, so a person must see it; the AI never closes it alone."""
    monkeypatch.setenv("MAPILLARY_TOKEN", "t")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    places = {"spots": [{"id": "S1", "a": [78.38, 17.47], "b": [78.3801, 17.4701]},
                        {"id": "S2", "a": [78.39, 17.48], "b": [78.3901, 17.4801]}]}
    monkeypatch.setattr(remote, "get", lambda url, data=None: json.dumps(places).encode())
    monkeypatch.setattr(remote, "photos", lambda lat, lon, token, now: [{"id": "p", "url": "u", "link": "l"}])
    monkeypatch.setattr(remote, "sort_photo",
                        lambda url, key: {"median_visible": True, "gap": "yes" if url == "u" else "no", "why": "x"})
    out = json.loads(remote.run(lambda m: None, {"routercheck": None, "mapwatch": None}))
    assert out["dispute_list"] == ["S1", "S2"]
    assert out["review_list"] == []


def test_photos_are_sent_as_bytes_not_links(monkeypatch):
    """5 Nov night: every photo failed with HTTP 400 when the API was asked to fetch the Mapillary link."""
    import io

    sent = {}

    class Resp(io.BytesIO):
        headers: typing.ClassVar[dict] = {"Content-Type": "image/jpeg"}

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def urlopen(req, timeout=0):
        if urllib.parse.urlsplit(req.full_url).hostname == "api.anthropic.com":
            sent["body"] = json.loads(req.data)
            return Resp(json.dumps({"content": [{"type": "text", "text": '{"median_visible": true, "gap": "no", "why": "x"}'}]}).encode())
        return Resp(b"\xff\xd8jpegbytes")

    monkeypatch.setattr(remote.urllib.request, "urlopen", urlopen)
    out = remote.sort_photo("https://scontent.example/photo.jpg", "k")
    src = sent["body"]["messages"][0]["content"][0]["source"]
    assert src["type"] == "base64" and src["media_type"] == "image/jpeg" and "url" not in src
    assert out["gap"] == "no"
