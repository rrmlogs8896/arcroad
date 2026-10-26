"""Regression tests for the Mapillary probe, named after how the 25 Oct probe failed.

On 25 Oct the probe returned zero images even for central London: a broken query
read as "no coverage". Every test here guards a way that can happen again.
No test touches the network; the HTTP opener is injected.
"""

import io
import json

from pipeline import mapillary as m

NOW_MS = 1_793_000_000_000  # fixed "now" so age checks are deterministic


def _raises(fn, *a):
    try:
        fn(*a)
    except m.ProbeError:
        return True
    return False


def test_oversized_bbox_is_refused_before_any_request():
    """Hypothesis: a box over the 0.01 deg² limit is stopped locally.
    Competing: it reaches the API and comes back as an empty, 'no coverage' result.
    Separates: build_request must raise for 0.1 x 0.1 and pass for 0.01 x 0.0099."""
    assert _raises(m.build_request, (78.0, 17.0, 78.1, 17.1), "tok"), \
        "exactly at the limit: floating point makes this 0.00999..., so it must still be refused"
    assert _raises(m.build_request, (78.0, 17.0, 78.2, 17.1), "tok")
    url, _ = m.build_request((78.0, 17.0, 78.01, 17.0099), "tok")
    assert "bbox=78.000000%2C17.000000%2C78.010000%2C17.009900" in url
    assert _raises(m.build_request, (78.1, 17.0, 78.0, 17.1), "tok"), "inverted box must fail"


def test_token_travels_in_header_never_in_url():
    url, headers = m.build_request(m.CONTROLS["amsterdam_centre"], "MLY|secret")
    assert headers == {"Authorization": "OAuth MLY|secret"}
    assert "secret" not in url and "access_token" not in url
    assert _raises(m.build_request, m.CONTROLS["amsterdam_centre"], "")


def test_api_error_payload_raises_instead_of_returning_no_images():
    """An auth failure must not look like an empty map."""
    assert _raises(m.parse_images, {"error": {"message": "Invalid OAuth access token"}})
    assert m.parse_images({"data": []}) == []


def test_fetch_parses_through_injected_opener_without_network():
    payload = {"data": [{"id": 1, "captured_at": NOW_MS,
                         "geometry": {"type": "Point", "coordinates": [78.2685, 17.5274]}}]}
    seen = {}

    class _Resp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def opener(req, timeout):
        seen["auth"] = req.get_header("Authorization")
        return _Resp(json.dumps(payload).encode())

    imgs = m.fetch_images(m.FIXED_TARGETS["isnapur_target_17.5274_78.2685"], "tok", opener=opener)
    assert seen["auth"] == "OAuth tok"
    assert imgs == [{"id": "1", "lon": 78.2685, "lat": 17.5274, "captured_at": NOW_MS}]


def test_zero_images_in_a_control_box_means_query_broken_not_no_coverage():
    """The 25 Oct failure as a test. Hypothesis: a dead control blocks any reading.
    Competing: the verdict still reports Hyderabad coverage figures.
    Separates: one control at zero must give QUERY_BROKEN whatever the shares are."""
    status, _ = m.verdict({"amsterdam_centre": 0, "london_trafalgar": 500}, 0.9, 0.9)
    assert status == "QUERY_BROKEN"
    status, sentence = m.verdict({"amsterdam_centre": 800, "london_trafalgar": 500}, 0.30, 0.10)
    assert status == "USEFUL" and "+20%" in sentence
    assert m.verdict({"a": 50, "b": 50}, 0.10, 0.40)[0] == "NOT_USEFUL"


def test_old_or_distant_images_do_not_count_as_coverage():
    """An image from 2014, or one 300 m away, cannot show today's median opening."""
    year_ms = 365.25 * 86400 * 1000
    old = {"id": "o", "lon": 78.0, "lat": 17.0, "captured_at": NOW_MS - 12 * year_ms}
    far = {"id": "f", "lon": 78.003, "lat": 17.0, "captured_at": NOW_MS - year_ms}
    assert m.nearest([old], 78.0, 17.0, now_ms=NOW_MS) == (None, None)
    d, age = m.nearest([old, far], 78.0, 17.0, now_ms=NOW_MS)
    assert 300 < d < 330 and abs(age - 1.0) < 0.01

    pair = {"a_lon": 78.0, "a_lat": 17.0, "b_lon": 78.0, "b_lat": 17.0002,
            "a_node_id": 1, "b_node_id": 2}
    rows = m.coverage([pair], lambda bbox: [old, far], now_ms=NOW_MS)
    assert rows[0]["covered"] is False and rows[0]["images_in_box"] == 2


def test_sample_takes_flagged_and_unflagged_pairs_equally():
    """The v1.1 failure: probing only the interesting points finds them interesting."""
    recs = [{"network_m": 1000.0, "flagged_high": "True" if i % 4 == 0 else "False"}
            for i in range(400)]
    recs.append({"network_m": "", "flagged_high": "True"})   # unrouted: never sampled
    flagged, unflagged = m.sample_pairs(recs, n_per_group=50, seed=1)
    assert len(flagged) == len(unflagged) == 50
    assert all(r["flagged_high"] == "True" for r in flagged)
    assert all(r["flagged_high"] == "False" for r in unflagged)
    assert m.sample_pairs(recs, 50, seed=1) == (flagged, unflagged), "seeded, reproducible"


def test_every_fixed_box_is_inside_the_api_limit():
    for name, bbox in {**m.CONTROLS, **m.FIXED_TARGETS}.items():
        m.check_bbox(bbox), name
    m.check_bbox(m.bbox_around(78.3, 17.5))


def _http_error(code, body=b'{"error":{"message":"x"}}'):
    import urllib.error
    return urllib.error.HTTPError("https://graph.mapillary.com/images", code, "err", {}, io.BytesIO(body))


def test_server_error_on_dense_box_retries_with_a_smaller_box_not_just_a_smaller_limit():
    """Live runs 1 and 2, 26 Oct: HTTP 500 "Please reduce the amount of data" at
    limits 2000, 500 and 100 on the SAME box. Lowering the limit alone could not
    separate "too much area" from "service down".
    Hypothesis: a smaller box succeeds. Competing: only the limit matters.
    Separates: the fake API fails while the box side exceeds 0.003 deg whatever the
    limit, so success requires the box to shrink; the retry must also never shrink
    a pair box below the 50 m test radius, and a total failure must raise with the
    API's message, never claim a cause, and never return []."""
    seen = []
    payload = json.dumps({"data": [{"id": 9, "captured_at": NOW_MS,
                                    "geometry": {"coordinates": [4.892, 52.373]}}]}).encode()

    class _Resp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def area_limited(req, timeout):
        q = req.full_url
        x0, _, x1, _ = (float(v) for v in q.split("bbox=")[1].split("&")[0].replace("%2C", ",").split(","))
        limit = int(q.split("limit=")[1].split("&")[0])
        seen.append((round(x1 - x0, 4), limit))
        if x1 - x0 > 0.003:
            raise _http_error(500, b'{"error":{"message":"Please reduce the amount of data"}}')
        return _Resp(payload)

    imgs = m.fetch_images(m.CONTROLS["amsterdam_centre"], "tok", opener=area_limited, pause=0)
    assert len(imgs) == 1
    assert seen[0] == (0.004, 2000) and seen[-1][0] <= 0.003, seen

    side = lambda b: b[2] - b[0]  # noqa: E731
    pair_box = m.bbox_around(78.3, 17.5)
    assert side(m.shrink(pair_box, 0.1, m.MIN_HALF_DEG)) >= 2 * m.MIN_HALF_DEG - 1e-12

    def down(req, timeout):
        raise _http_error(500, b'{"error":{"message":"Please reduce the amount of data"}}')

    try:
        m.fetch_images(m.CONTROLS["amsterdam_centre"], "tok", opener=down, pause=0)
    except m.ProbeError as e:
        msg = str(e)
        assert "Please reduce the amount of data" in msg and "limit=100" in msg
        assert "service" not in msg.lower(), "must not assert a cause it has not shown"
    else:
        raise AssertionError("a failure must raise, not return no images")


def test_auth_error_is_raised_at_once_with_the_api_message():
    calls = []

    def unauthorised(req, timeout):
        calls.append(1)
        raise _http_error(401, b'{"error":{"message":"Invalid OAuth access token"}}')

    try:
        m.fetch_images(m.CONTROLS["london_trafalgar"], "bad", opener=unauthorised, pause=0)
    except m.ProbeError as e:
        assert "Invalid OAuth access token" in str(e) and len(calls) == 1
    else:
        raise AssertionError("a 401 must raise")
