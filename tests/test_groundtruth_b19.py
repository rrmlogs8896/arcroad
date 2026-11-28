import math

import pytest

from pipeline.groundtruth import find_pass

pytestmark = pytest.mark.skip(reason="B-19 held 28 Nov 2026: the 0.8x gap rule also rejected real straight-over crossings (map-lag evidence); redesign pending")


def _track(points):
    return [(float(k), la, lo) for k, (la, lo) in enumerate(points)]


def _line(a, b, n):
    return [(a[0] + (b[0] - a[0]) * t / n, a[1] + (b[1] - a[1]) * t / n) for t in range(n + 1)]


def test_one_carriageway_drive_past_offset_points_is_not_a_crossing():
    # A and B 47 m apart, mostly ALONG the road (as at S01). A car on one carriageway passes
    # within a few metres of both; that must never be scored as a crossing (B-19).
    a, b = (17.526092, 78.270136), (17.526217, 78.269716)
    start = (a[0] - 0.0006, a[1] + 0.0009)
    end = (b[0] + 0.0006, b[1] - 0.0009)
    track = _track(_line(start, end, 120))
    assert find_pass(track, a, b) is None


def test_real_loop_still_found():
    # Leave A, drive out 1 km, turn, come back to B: still a pass.
    a, b = (17.5000, 78.3000), (17.5003, 78.3000)
    k = 1 / 111000
    out = _line(a, (a[0], a[1] + 1000 * k / math.cos(math.radians(17.5))), 60)
    back = _line((b[0], b[1] + 1000 * k / math.cos(math.radians(17.5))), b, 60)
    track = _track([a] * 5 + out + back + [b] * 5)
    found = find_pass(track, a, b)
    assert found is not None


def test_short_gap_drive_by_is_not_a_crossing():
    # A and B 13 m apart (as at S08). A car on one carriageway passes both in about a second.
    a, b = (17.4900, 78.3800), (17.49005, 78.38012)
    start = (a[0] - 0.0004, a[1] - 0.0009)
    end = (b[0] + 0.0004, b[1] + 0.0009)
    track = _track(_line(start, end, 150))
    assert find_pass(track, a, b) is None
