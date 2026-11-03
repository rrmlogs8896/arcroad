from pipeline.groundtruth import find_pass


def test_jitter_pass_shorter_than_half_the_straight_line_is_skipped():
    # A and B 17 m apart across a median; a stopped car's GPS hops between points 7 m apart.
    a, b = (17.461402, 78.30809), (17.46154, 78.308026)

    def at(f):
        return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)

    track = [(t, *at(0.3)) for t in range(5)] + [(5 + t, *at(0.7)) for t in range(5)]
    assert find_pass(track, a, b) is None


def test_a_real_straight_crossing_still_counts():
    a, b = (17.461402, 78.30809), (17.46154, 78.308026)
    track = [(t, *a) for t in range(5)] + [(5 + t, *b) for t in range(5)]
    assert find_pass(track, a, b) == (4, 5)
