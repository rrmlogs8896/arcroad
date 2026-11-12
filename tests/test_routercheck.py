import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "research" / "runner" / "app"))
import mapwatch
import routercheck as rc


def test_ratio_and_classes_follow_the_preregistration():
    assert rc.ratio(None, 1000) is None and rc.ratio(1000, 0) is None
    assert rc.classify(None) == "NO_ROUTE"
    assert rc.classify(1.10) == "AGREES" and rc.classify(0.86) == "AGREES"
    assert rc.classify(1.25) == "ROUTER_LONGER"
    assert rc.classify(0.80) == "ROUTER_SHORTER"
    assert rc.classify(1.17) == "DIFFERS"


def test_summary_counts_every_class_so_the_counts_add_up():
    rows = [{"osrm": {"class": rc.classify(r)}} for r in (None, 1.0, 1.17, 1.25, 0.8, 1.16)]
    s = rc.summarise(rows, "osrm")
    assert s["DIFFERS"] == 2 and sum(s[k] for k in rc.CLASSES) == s["n"] == 6


def test_mapwatch_query_and_summary_hold_no_mapper_names():
    q = mapwatch.query(17.47, 78.38, "2026-11-01T00:00:00Z")
    assert 'newer:"2026-11-01T00:00:00Z"' in q and "around:1000" in q
    s = mapwatch.summarise({"type": "way", "id": 1, "version": 3, "timestamp": "t", "changeset": 9,
                            "user": "someone", "uid": 5, "tags": {"highway": "primary"}})
    assert "user" not in s and "uid" not in s and s["what"] == "primary"
