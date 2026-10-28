"""Ground-truth scoring (Phase 2b). Tracks are synthetic: no real drive is in this repo."""

import json

from pipeline import groundtruth as g
from pipeline.geometry import haversine_m

A = (17.5000, 78.2000)
B = (17.5002, 78.2000)  # ~22 m north of A: the two sides of a divided road
DEG_PER_100M = 0.0009


def gpx(points, start=1_793_000_000, step=1):
    """points: list of (lat, lon); one sample every `step` seconds."""
    from datetime import UTC, datetime

    pts = "".join(
        f'<trkpt lat="{la}" lon="{lo}"><time>'
        f"{datetime.fromtimestamp(start + k * step, UTC).strftime('%Y-%m-%dT%H:%M:%SZ')}"
        "</time></trkpt>"
        for k, (la, lo) in enumerate(points)
    )
    return f'<gpx xmlns="http://www.topografix.com/GPX/1/1"><trk><trkseg>{pts}</trkseg></trk></gpx>'


def line(p, q, n):
    return [(p[0] + (q[0] - p[0]) * k / n, p[1] + (q[1] - p[1]) * k / n) for k in range(n + 1)]


def loop_track(east_m, n=60, dwell=5):
    """Parked at A, then A -> east -> U-turn -> back to B, parked at B (detour ~2 * east_m)."""
    far = (A[0], A[1] + east_m / 100 * DEG_PER_100M / 0.954)  # 0.954 = cos(17.5 deg)
    far_b = (B[0], far[1])
    return [A] * dwell + line(A, far, n) + line(far, far_b, 2)[1:] + line(far_b, B, n)[1:] + [B] * dwell


def stop(sid="S01"):
    return {"id": sid, "a": list(A), "b": list(B)}


def test_parse_gpx_reads_points_and_times_in_any_namespace():
    track = g.parse_gpx(gpx([A, B]))
    assert [(round(la, 4), round(lo, 4)) for _, la, lo in track] == [A, B]
    assert track[1][0] - track[0][0] == 1
    bare = g.parse_gpx('<gpx><trk><trkseg><trkpt lat="1" lon="2"/></trkseg></trk></gpx>')
    assert bare == [(None, 1.0, 2.0)]


def test_detour_close_to_model_is_a_match():
    track = g.parse_gpx(gpx(loop_track(1000)))
    row = g.score_stop(track, stop(), network_m=2000.0)
    assert 1900 < row["driven_m"] < 2100
    assert row["verdict"] == "MATCH"


def test_missing_link_in_the_map_reads_shorter():
    # The competing explanation: the driver crosses straight over at a real opening.
    track = g.parse_gpx(gpx([A] * 5 + line(A, B, 9) + [B] * 5))
    row = g.score_stop(track, stop(), network_m=2344.0)
    assert row["driven_m"] < 50
    assert row["verdict"] == "SHORTER"


def test_driver_taking_a_longer_way_says_nothing_about_the_model():
    track = g.parse_gpx(gpx(loop_track(3000)))
    assert g.score_stop(track, stop(), network_m=2000.0)["verdict"] == "LONGER"


def test_between_is_left_for_review_not_forced_into_a_side():
    assert g.verdict(1200.0, 2000.0) == "BETWEEN"


def test_gate_values_are_the_preregistered_ones():
    # Changing these after a drive is scored breaks AGENTS.md rule 2.
    assert (g.MATCH_ABS_M, g.MATCH_REL, g.SHORTER_REL) == (150.0, 0.25, 0.5)
    assert g.verdict(2344 + 586, 2344) == "MATCH"
    assert g.verdict(1171, 2344) == "SHORTER"


def test_stop_never_reached_is_not_driven_and_stays_in_the_count():
    far_away = [(17.6, 78.3), (17.61, 78.3)]
    result = g.score_day(g.parse_gpx(gpx(far_away)), [stop("S01"), stop("S02")], {})
    assert result["counts"]["NOT_DRIVEN"] == 2
    assert len(result["stops"]) == 2


def test_b_before_a_is_not_an_a_to_b_pass():
    track = g.parse_gpx(gpx([B] * 5 + line(B, A, 9) + [A] * 5))
    assert g.find_pass(track, A, B) is None


def test_parked_minutes_at_a_do_not_count_as_driving():
    parked = [A] * 300 + loop_track(1000)
    row = g.score_stop(g.parse_gpx(gpx(parked)), stop(), network_m=2000.0)
    assert row["minutes"] < 3


def test_sparse_samples_are_poor_track_not_a_verdict():
    track = g.parse_gpx(gpx(loop_track(1000, n=5, dwell=3), step=30))
    assert g.score_stop(track, stop(), network_m=2000.0)["verdict"] == "POOR_TRACK"


def test_photo_only_stops_without_a_b_side_are_not_scored():
    result = g.score_day([], [{"id": "T1", "a": list(A), "b": None}], {})
    assert result["stops"] == []


def test_output_never_contains_track_coordinates():
    # A raw track shows where the driver lives: only per-stop numbers may leave.
    track = g.parse_gpx(gpx([(17.4400, 78.3500)] * 3 + loop_track(1000)))
    out = json.dumps(g.score_day(track, [stop()], {"S01": 2000.0}))
    assert "17.44" not in out and "78.35" not in out
    for row in json.loads(out)["stops"]:
        assert set(row) == {"id", "straight_m", "network_m", "driven_m", "minutes",
                            "max_gap_s", "verdict"}


def test_field_day_1_stop_file_is_well_formed():
    with open("data/field/field_day_1_stops.json", encoding="utf-8") as fh:
        stops = json.load(fh)["stops"]
    assert len(stops) == 26
    assert len({s["id"] for s in stops}) == 26
    for s in stops:
        assert 17.3 < s["a"][0] < 17.7 and 78.1 < s["a"][1] < 78.5
        if s.get("b"):
            gap = haversine_m(s["a"][1], s["a"][0], s["b"][1], s["b"][0])
            assert gap < 100, s["id"]


def test_parked_phone_flickering_towards_b_is_not_a_crossing():
    # A and B are closer than the visit radius; one jittery sample must not
    # turn a parked phone into a 10 m "drive" that would wrongly read SHORTER.
    jitter = [A, A, A, B, A, A, A, B, A, A, A]
    assert g.find_pass(g.parse_gpx(gpx(jitter)), A, B) is None
