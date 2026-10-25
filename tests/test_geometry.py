import math
from pipeline.geometry import (
    haversine_m, bearing_deg, angle_between, is_antiparallel, zone_of,
)


def test_haversine_known_distance():
    # 0.0009 degrees of latitude is almost exactly 100 m
    assert abs(haversine_m(78.4, 17.4, 78.4, 17.4009) - 100) < 3


def test_haversine_is_symmetric_and_zero_at_a_point():
    assert haversine_m(78.4, 17.4, 78.5, 17.5) == haversine_m(78.5, 17.5, 78.4, 17.4)
    assert haversine_m(78.4, 17.4, 78.4, 17.4) == 0


def test_bearing_cardinal_directions():
    assert abs(bearing_deg(78.4, 17.4, 78.4, 17.41) - 0) < 1      # north
    assert abs(bearing_deg(78.4, 17.4, 78.41, 17.4) - 90) < 1     # east
    assert abs(bearing_deg(78.4, 17.4, 78.4, 17.39) - 180) < 1    # south


def test_angle_between_wraps_correctly():
    assert angle_between(10, 350) == 20
    assert angle_between(0, 180) == 180


def test_antiparallel_accepts_opposite_headings():
    assert is_antiparallel(0, 180, 35)
    assert is_antiparallel(0, 200, 35)
    assert is_antiparallel(350, 170, 35)


def test_antiparallel_rejects_the_v04_failures():
    # Perpendicular roads meeting at a corner are not two carriageways.
    assert not is_antiparallel(45, 135, 35)
    # Parallel roads running the SAME way are not two carriageways either.
    assert not is_antiparallel(0, 10, 35)


def test_zones_overlap_by_design():
    zones = {"wide": (0, 0, 20, 20), "narrow": (5, 5, 10, 10)}
    assert sorted(zone_of(7, 7, zones)) == ["narrow", "wide"]
    assert zone_of(1, 1, zones) == ["wide"]
    assert zone_of(50, 50, zones) == []
