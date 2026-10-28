"""Field-day helpers: route sheet, track quality check, model distance export.

Tracks and export rows here are synthetic. No real drive is in this repository.
"""

import csv
import importlib.util
import json
import pathlib

import pytest

from pipeline import groundtruth as g

_ROOT = pathlib.Path(__file__).resolve().parents[1]
STOPS = _ROOT / "data" / "field" / "field_day_1_stops.json"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, _ROOT / "tools" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def plan():
    return _load("field_plan")


@pytest.fixture(scope="module")
def tq():
    return _load("track_quality")


@pytest.fixture(scope="module")
def ex():
    return _load("export_network")


@pytest.fixture(scope="module")
def stops():
    return json.loads(STOPS.read_text())["stops"]


def gpx(samples):
    """samples: (seconds, lat, lon)."""
    from datetime import UTC, datetime

    pts = "".join(
        f'<trkpt lat="{la}" lon="{lo}"><time>'
        f"{datetime.fromtimestamp(1_793_000_000 + t, UTC).strftime('%Y-%m-%dT%H:%M:%SZ')}"
        "</time></trkpt>"
        for t, la, lo in samples
    )
    return f"<gpx><trk><trkseg>{pts}</trkseg></trk></gpx>"


# --- route sheet -------------------------------------------------------------

def test_route_visits_every_stop_once_with_fixed_ends(plan, stops):
    order = plan.order_stops(stops, "S04", "S13")
    assert sorted(order) == sorted(s["id"] for s in stops)
    assert order[0] == "S04" and order[-1] == "S13"


def test_route_is_reproducible_and_no_longer_than_nearest_neighbour(plan, stops):
    by_id = {s["id"]: s for s in stops}
    a = plan.order_stops(stops, "S04", "S13")
    assert a == plan.order_stops(stops, "S04", "S13")
    assert plan.path_m(by_id, a) <= plan.path_m(by_id, [s["id"] for s in stops]) + 1e-6


def test_field_sheet_never_shows_model_distances(plan, stops):
    # A driver who sees the expected detour can be steered to it (STATE.md).
    text = plan.render_table(plan.sheet_rows(stops, plan.order_stops(stops, "S04", "S13")))
    low = text.lower()
    for word in ("network", "detour", "map_gap", "gap_m"):
        assert word not in low
    for s in stops:
        if "map_gap_m" in s:
            assert f"{s['map_gap_m']} m" not in text


def test_committed_route_doc_carries_no_model_distances(plan):
    doc = (_ROOT / "docs" / "field" / "field_day_1_route.md").read_text().lower()
    assert "network_m," not in doc and "detour index" not in doc
    assert "map_gap" not in doc


def test_compass_points_the_right_way(plan):
    assert plan.compass([17.5, 78.2], [17.6, 78.2]) == "N"
    assert plan.compass([17.5, 78.2], [17.5, 78.1]) == "W"
    assert plan.compass([17.5, 78.2], [17.4, 78.3]) == "SE"


def test_estimate_is_a_range_and_counts_photo_targets(plan, stops):
    e = plan.estimate(stops, plan.order_stops(stops, "S04", "S13"))
    assert e["stops"] == 26 and e["photos"] == 1 and e["crossings"] == 25
    assert e["total_km"][0] < e["total_km"][1]
    assert e["hours"][0] < e["hours"][1]


# --- track quality -------------------------------------------------------------

def test_distance_filtered_logger_is_caught(tq):
    # Rides 1 s samples, then sits still at a red light for 40 s with no points written.
    moving = [(t, 17.5 + t * 0.0001, 78.2) for t in range(30)]
    resumed = [(70 + t, 17.503 + t * 0.0001, 78.2) for t in range(30)]
    s = tq.summarise(g.parse_gpx(gpx(moving + resumed)))
    assert s["holes_over_limit"] == 1
    assert s["holes_over_limit_while_still"] == 1
    assert any("distance filter" in t for t in tq.advice(s))


def test_time_based_logger_passes_clean(tq):
    still = [(t, 17.5, 78.2) for t in range(40)]
    moving = [(40 + t, 17.5 + t * 0.0001, 78.2) for t in range(40)]
    s = tq.summarise(g.parse_gpx(gpx(still + moving)))
    assert s["holes_over_limit"] == 0 and s["median_step_s"] == 1
    assert tq.advice(s) == []


def test_quality_report_contains_no_coordinates(tq):
    s = tq.summarise(g.parse_gpx(gpx([(t, 17.123456, 78.654321 + t * 1e-4) for t in range(10)])))
    assert "17.12" not in repr(s) and "78.65" not in repr(s)


def test_speed_spike_and_duplicate_time_are_counted(tq):
    pts = [(0, 17.5, 78.2), (1, 17.5001, 78.2), (1, 17.5002, 78.2), (2, 17.51, 78.2)]
    s = tq.summarise(g.parse_gpx(gpx(pts)))
    assert s["duplicate_times"] == 1
    assert s["speed_spikes"] == 1


# --- model distance export -------------------------------------------------------

def _rec(a, b, net, why=""):
    return {"a_lat": str(a[0]), "a_lon": str(a[1]), "b_lat": str(b[0]), "b_lon": str(b[1]),
            "network_m": "" if net is None else str(net), "null_reason": why}


def test_export_matches_on_both_sides_and_skips_photo_targets(ex):
    stops = [
        {"id": "S01", "a": [17.526092, 78.270136], "b": [17.526217, 78.269716]},
        {"id": "T1", "a": [17.5269, 78.26913], "b": None},
    ]
    records = [
        _rec((17.5260921, 78.2701358), (17.5262172, 78.2697161), 2344.5),
        _rec((17.5260921, 78.2701358), (17.5300000, 78.2697161), 99.0),  # wrong B
    ]
    rows, problems = ex.match_stops(records, stops)
    assert [(r["id"], r["network_m"]) for r in rows] == [("S01", 2344.5)]
    assert problems == []


def test_export_reports_unmatched_and_unrouted_stops(ex):
    stops = [{"id": "S02", "a": [17.52984, 78.253969], "b": [17.530027, 78.25397]},
             {"id": "T2", "a": [17.5458, 78.21596], "b": [17.5455, 78.21579]}]
    records = [_rec((17.52984, 78.253969), (17.530027, 78.25397), None, "unreachable")]
    rows, problems = ex.match_stops(records, stops)
    assert rows == []
    assert dict(problems)["S02"].endswith("(unreachable)")
    assert "no export record" in dict(problems)["T2"]


def test_export_writes_only_to_out_inside_the_repo(ex):
    repo = str(_ROOT)
    assert ex.safe_out_path(f"{repo}/out/model_network.csv", repo)
    assert not ex.safe_out_path(f"{repo}/docs/field/model_network.csv", repo)
    assert not ex.safe_out_path(f"{repo}/web/model_network.csv", repo)
    assert not ex.safe_out_path(f"{repo}/model_network.csv", repo)


def test_export_csv_is_what_score_drive_reads(ex, tmp_path):
    pts = tmp_path / "points.csv"
    with pts.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(_rec((0, 0), (0, 0), 1).keys()))
        w.writeheader()
        w.writerow(_rec((17.526092, 78.270136), (17.526217, 78.269716), 1500.0))
    out = tmp_path / "model_network.csv"
    assert ex.main([str(pts), str(STOPS), "--out", str(out)]) == 0
    got = {r["id"]: float(r["network_m"]) for r in csv.DictReader(out.open())}
    assert got == {"S01": 1500.0}
