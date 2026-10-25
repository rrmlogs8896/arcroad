import math
from pipeline.metrics import detour_index, headline_stats, worst_n, pct


def test_detour_index_basic():
    assert detour_index(1000.0, 50.0) == 20.0


def test_detour_index_returns_none_not_zero_for_no_measurement():
    assert detour_index(100.0, 0) is None
    assert detour_index(float("inf"), 50.0) is None
    assert detour_index(None, 50.0) is None


def test_pct_guards_zero():
    assert pct(1, 4) == 25.0
    assert pct(0, 0) == 0.0


def test_headline_is_computed_on_the_uncensored_set():
    """The v0.5 reporting bug, locked in as a regression test.

    Five low values and four high ones. Censoring at 50 would report a median
    of 3.0. The true median is 5.0 and that is what must be published.
    """
    values = [1, 2, 3, 4, 5, 60, 70, 80, 90]
    s = headline_stats(values, di_review=50.0)
    assert s["median"] == 5.0, "headline must use every measured point"
    assert s["censored_median"] == 3.0, "censored view kept only for comparison"
    assert s["n"] == 9
    assert s["n_flagged"] == 4


def test_flagging_never_removes_points():
    values = [1, 100, 200]
    s = headline_stats(values, di_review=50.0)
    assert s["n"] == 3
    assert s["max"] == 200, "the worst value must survive into the headline"


def test_none_values_are_excluded_but_not_counted_as_zero():
    s = headline_stats([None, 10, 20, None])
    assert s["n"] == 2
    assert s["median"] == 15.0


def test_worst_n_comes_from_the_uncensored_set():
    records = [{"detour_index": v} for v in [1, 5, 49, 90, 200]]
    top = worst_n(records, n=2)
    assert [r["detour_index"] for r in top] == [200, 90], (
        "v0.5 listed points nearest the cutoff instead of the worst ones"
    )


def test_worst_n_ignores_unmeasured_records():
    records = [{"detour_index": None}, {"detour_index": 7}]
    assert len(worst_n(records, n=5)) == 1
