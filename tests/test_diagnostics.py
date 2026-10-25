"""Tests for pipeline.diagnostics.

Four of these exist because the code, or the project's reasoning, got it wrong
in production. Each names the failure it locks out.
"""

import math

from pipeline.diagnostics import (
    CROSSING_MAX_M,
    band_of,
    cluster_dedup,
    data_gaps,
    decompose_flagged,
    edge_km,
    sector_of,
    stratified_compare,
)
from pipeline.metrics import DI_REVIEW_DEFAULT, DI_SEVERE_DEFAULT, headline_stats

HMDA = (78.050, 17.050, 78.850, 17.750)
CITY = (78.4867, 17.3850)


# --------------------------------------------------------------------------
# B-07: the data-gap export wrote a header and no rows while 60 unreachable
# points sat in the measured set. Those points are the most valuable output of
# a run. This test fails if that export can ever come back empty when gaps exist.
# --------------------------------------------------------------------------


def test_unreachable_points_always_reach_the_gap_export():
    records = [
        {"lon": 78.3, "lat": 17.5, "unreachable": True, "straight_m": 20.0, "network_m": None},
        {"lon": 78.4, "lat": 17.4, "unreachable": False, "straight_m": 20.0, "network_m": 800.0},
    ]
    gaps = data_gaps(records)
    assert len(gaps) == 1, "an unreachable point must appear in the gap export"
    assert gaps[0]["gap_reason"] == "unreachable"


def test_gap_export_is_not_empty_when_the_set_contains_gaps():
    """The exact shape of B-07: many gaps present, export returns nothing."""
    records = [
        {"lon": 78.3, "lat": 17.5, "unreachable": True, "straight_m": 20.0, "network_m": None}
        for _ in range(60)
    ]
    assert len(data_gaps(records)) == 60


def test_gap_reasons_are_distinguished():
    records = [
        {"lon": 78.3, "lat": 17.5, "unreachable": True, "straight_m": 20.0, "network_m": None},
        {"lon": 78.3, "lat": 17.5, "unreachable": False, "near_limit": True,
         "straight_m": 20.0, "network_m": 24_900.0},
        {"lon": 78.3, "lat": 17.5, "unreachable": False, "near_limit": False,
         "straight_m": 20.0, "network_m": 14_000.0},
        {"lon": 78.3, "lat": 17.5, "unreachable": False, "near_limit": False,
         "straight_m": 20.0, "network_m": 2_400.0},
    ]
    reasons = [g["gap_reason"] for g in data_gaps(records)]
    assert reasons == ["unreachable", "near_limit", "long_route"]


def test_a_long_route_between_distant_points_is_not_a_gap():
    """A 12 km route between points 900 m apart is a detour, not a hole."""
    records = [{"lon": 78.3, "lat": 17.5, "unreachable": False, "near_limit": False,
                "straight_m": 900.0, "network_m": 12_000.0}]
    assert data_gaps(records) == []


# --------------------------------------------------------------------------
# D-12: the severity threshold must discriminate. At 5.0 it labelled 77% of the
# core city severe, which told a reader nothing.
# --------------------------------------------------------------------------


def test_severity_threshold_discriminates_between_core_and_periphery():
    core = [6.0, 8.0, 12.0, 15.0, 18.0, 22.0, 30.0, 45.0, 60.0, 90.0]
    beyond = [20.0, 35.0, 48.0, 55.0, 70.0, 90.0, 120.0, 160.0, 220.0, 400.0]
    c = headline_stats(core)["pct_over_severe"]
    b = headline_stats(beyond)["pct_over_severe"]
    assert c < 50.0, (
        f"at the current threshold {DI_SEVERE_DEFAULT} a core-like sample reports "
        f"{c}% severe; a measure that labels most of the best zone severe is useless"
    )
    assert b >= 2 * c, "the measure must separate periphery from core, not flatten them"


def test_review_threshold_still_does_not_censor_the_headline():
    """The v0.5 failure, re-asserted now that the two thresholds are equal."""
    values = [10.0] * 40 + [500.0] * 60
    s = headline_stats(values, di_review=DI_REVIEW_DEFAULT)
    assert s["n"] == 100, "every measured point stays in the headline set"
    assert s["median"] == 500.0, "the true median is pulled up by the high values"
    assert s["censored_median"] == 10.0, "censoring would have reported 10.0"
    assert s["median"] != s["censored_median"], (
        "this gap IS the v0.5 bug: the censored figure was published as the headline"
    )


# --------------------------------------------------------------------------
# Reporting rule 5: a comparison needs comparable groups.
# v0.9 published a sector median of 354.64 computed over twenty points.
# --------------------------------------------------------------------------


def test_small_groups_are_marked_inadequate_not_silently_ranked():
    records = (
        [{"sector": "Tiny", "detour_index": 350.0} for _ in range(20)]
        + [{"sector": "Real", "detour_index": 30.0} for _ in range(200)]
    )
    out = stratified_compare(records, "sector", min_n=30)
    assert out["Tiny"]["adequate"] is False
    assert out["Real"]["adequate"] is True
    first = next(iter(out))
    assert first == "Real", "an inadequate group must never top the ranking"


def test_stratified_compare_keeps_the_numbers_visible():
    """Inadequate groups are flagged, never dropped. Hiding them is censoring."""
    records = [{"z": "a", "detour_index": 10.0}] * 5
    out = stratified_compare(records, "z", min_n=30)
    assert out["a"]["n"] == 5
    assert out["a"]["median"] == 10.0
    assert out["a"]["adequate"] is False


# --------------------------------------------------------------------------
# edge_km: correctness, plus the confound that made the v1.0 edge test useless.
# --------------------------------------------------------------------------


def test_edge_km_is_small_at_the_boundary_and_large_at_the_centre():
    west = edge_km(78.051, 17.400, HMDA)
    centre = edge_km(78.450, 17.400, HMDA)
    assert west < 1.0
    assert centre > 30.0


def test_edge_distance_and_centre_distance_are_nearly_collinear():
    """Why edge_km cannot answer the boundary question on its own.

    Sampled over the study area these two move together almost perfectly, so a
    difference attributed to the boundary is equally well explained by distance
    from the city. The v1.0 edge test ignored this. The docstring on edge_km
    warns about it; this test proves the warning is still true of the real box.
    """
    pts = [
        (78.05 + 0.08 * i, 17.05 + 0.07 * j) for i in range(10) for j in range(10)
    ]
    e = [edge_km(lon, lat, HMDA) for lon, lat in pts]
    c = [
        math.hypot((lon - CITY[0]) * 106.0, (lat - CITY[1]) * 110.5)
        for lon, lat in pts
    ]
    n = len(e)
    me, mc = sum(e) / n, sum(c) / n
    cov = sum((x - me) * (y - mc) for x, y in zip(e, c, strict=True))
    r = cov / math.sqrt(
        sum((x - me) ** 2 for x in e) * sum((y - mc) ** 2 for y in c)
    )
    assert r < -0.75, f"expected strong negative correlation, got r={r:.3f}"


# --------------------------------------------------------------------------
# Rings, sectors, clustering, flagged decomposition.
# --------------------------------------------------------------------------


def test_band_boundaries():
    assert band_of(5.0, 14.0, 26.0) == "core (inside ORR)"
    assert band_of(14.0, 14.0, 26.0) == "core (inside ORR)"
    assert band_of(20.0, 14.0, 26.0) == "ORR band"
    assert band_of(40.0, 14.0, 26.0) == "beyond the ORR"


def test_sector_wraps_correctly_across_north():
    """A bearing of 2 degrees belongs to the exit at 359, not the one at 41."""
    exits = [("Medchal", 359), ("Keesara", 41), ("Shamshabad", 212)]
    assert sector_of(2.0, exits) == "Medchal"
    assert sector_of(358.0, exits) == "Medchal"
    assert sector_of(200.0, exits) == "Shamshabad"


def test_cluster_dedup_collapses_one_junction_sampled_many_times():
    """The v0.6 worst-15: one location, eight entries."""
    base = [
        {"lon": 78.2685, "lat": 17.5274 + 0.00008 * i, "detour_index": 110.0 - i}
        for i in range(8)
    ]
    far = [{"lon": 78.3500, "lat": 17.6000, "detour_index": 90.0}]
    kept = cluster_dedup(base + far, radius_m=150.0)
    assert len(kept) == 2
    assert kept[0]["detour_index"] == 110.0


def test_decompose_flagged_separates_real_severance_from_map_holes():
    records = (
        [{"detour_index": 120.0, "straight_m": 20.0, "network_m": 2_400.0}] * 80
        + [{"detour_index": 900.0, "straight_m": 20.0, "network_m": 18_000.0}] * 20
    )
    d = decompose_flagged(records, di_review=DI_REVIEW_DEFAULT)
    assert d["n"] == 100
    assert d["pct_true_crossings"] == 100.0
    assert d["pct_long_route"] == 20.0
    assert d["median_network_m"] == 2_400.0


def test_crossing_width_constant_matches_what_we_call_a_crossing():
    assert CROSSING_MAX_M == 25.0


# --------------------------------------------------------------------------
# B-09: the v1.0 export recorded one endpoint per measurement, so nothing in
# it could be re-routed. These lock the schema that makes a record checkable.
# --------------------------------------------------------------------------


def test_a_record_without_the_second_endpoint_is_rejected():
    """The exact shape of B-09."""
    from pipeline.provenance import validate_point_record

    v10_shape = {
        "lat": 17.5274, "lon": 78.2685, "straight_m": 21.0,
        "network_m": 2344.0, "detour_index": 111.6,
    }
    problems = validate_point_record(v10_shape)
    assert problems, "a record with no b_lat/b_lon must not validate"
    assert any("b_lat" in p for p in problems)


def test_a_complete_record_validates():
    from pipeline.provenance import validate_point_record

    rec = {
        "a_lat": 17.5274, "a_lon": 78.2685,
        "b_lat": 17.5276, "b_lon": 78.2685,
        "straight_m": 21.0, "network_m": 2344.0, "detour_index": 111.6,
    }
    assert validate_point_record(rec) == []


def test_a_null_route_must_carry_a_reason():
    from pipeline.provenance import validate_point_record

    rec = {
        "a_lat": 17.5, "a_lon": 78.3, "b_lat": 17.5002, "b_lon": 78.3,
        "straight_m": 22.0, "network_m": None, "detour_index": None,
    }
    assert any("null_reason" in p for p in validate_point_record(rec))
    rec["null_reason"] = "unreachable"
    assert validate_point_record(rec) == []


def test_identical_endpoints_measure_nothing():
    from pipeline.provenance import validate_point_record

    rec = {
        "a_lat": 17.5, "a_lon": 78.3, "b_lat": 17.5, "b_lon": 78.3,
        "straight_m": 0.0, "network_m": 0.0, "detour_index": 0.0,
    }
    assert any("identical" in p for p in validate_point_record(rec))


# --------------------------------------------------------------------------
# B-10 and the ring shape.
# --------------------------------------------------------------------------


def test_points_outside_the_declared_area_are_found_not_assumed():
    from pipeline.diagnostics import outside_declared_area

    records = [
        {"lon": 78.4, "lat": 17.4},      # inside
        {"lon": 78.5306, "lat": 16.8495},  # a real v1.0 stray, 60 km south
        {"lon": 79.0715, "lat": 17.9681},  # a real v1.0 stray, north-east corner
    ]
    strays = outside_declared_area(records, HMDA)
    assert len(strays) == 2


def test_ring_profile_does_not_force_a_monotonic_ramp():
    """The v1.0 shape: the peak is the fringe, not the farthest ring."""
    from pipeline.diagnostics import ring_profile

    def ring(dist_km, value, n):
        lat = CITY[1] + dist_km / 110.5
        return [{"lon": CITY[0], "lat": lat, "detour_index": value} for _ in range(n)]

    records = ring(7, 18.0, 100) + ring(20, 34.0, 100) + ring(33, 57.0, 100) + ring(50, 48.0, 100)
    edges = [(0, 14, "core"), (14, 26, "ORR"), (26, 40, "fringe"), (40, 60, "rural")]
    prof = ring_profile(records, CITY, edges)
    assert prof["fringe"]["median"] > prof["rural"]["median"], (
        "the measured shape peaks at the fringe; a ring profile must be able to show that"
    )
    assert all(prof[k]["adequate"] for k in prof)
