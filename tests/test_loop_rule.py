import itertools
import math

from pipeline import groundtruth as g

A = (17.50000, 78.30000)   # east side of a north-south divided road
B = (17.50000, 78.29985)   # west side, ~16 m away


def walk(points, step_m=8.0):
    out, t = [], 0
    for (la1, lo1), (la2, lo2) in itertools.pairwise(points):
        d = g.haversine_m(lo1, la1, lo2, la2)
        n = max(1, int(d / step_m))
        for k in range(n):
            out.append((t, la1 + (la2 - la1) * k / n, lo1 + (lo2 - lo1) * k / n))
            t += 1
    out.append((t, *points[-1]))
    return out


def test_southbound_on_the_east_side_then_back_north_is_a_to_b():
    # Keep left: southbound traffic uses the east carriageway (A); after the U-turn, northbound uses west (B).
    track = walk([(17.5040, 78.30000), A, (17.4960, 78.30000), (17.4960, 78.29985), B, (17.5040, 78.29985)])
    loops = g.find_loops(track, A, B)
    assert len(loops) == 1 and loops[0]["dir"] == "ab"
    assert 880 < loops[0]["driven_m"] < 920


def test_northbound_on_the_west_side_is_b_to_a():
    track = walk([(17.4960, 78.29985), B, (17.5040, 78.29985), (17.5040, 78.30000), A, (17.4960, 78.30000)])
    loops = g.find_loops(track, A, B)
    assert [x["dir"] for x in loops] == ["ba"]


def test_passing_by_or_stopping_is_not_a_loop():
    straight_on = walk([(17.5040, 78.30000), A, (17.4960, 78.30000)])
    assert g.find_loops(straight_on, A, B) == []
    parked = [(t, A[0] + 0.00002 * (t % 2), A[1]) for t in range(60)]
    assert g.find_loops(parked, A, B) == []


def test_rule_only_applies_where_gps_cannot_separate_the_sides():
    far_b = (17.50000, 78.29950)   # ~53 m away
    track = walk([(17.5040, 78.30000), A, (17.4960, 78.30000)])
    assert g.find_loops(track, A, far_b) == []
    assert math.isclose(g.LOOP_MAX_STRAIGHT_M, 40.0)
