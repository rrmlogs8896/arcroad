from datetime import date

from pipeline.fieldscore import score

TODAY = date(2026, 11, 2)
MODEL = {"X1": {"straight": 20.0, "ab": 1500.0, "ba": 1400.0}, "X2": {"straight": 28.0, "ab": 700.0, "ba": None}}


def p(i, d, m, start, photos=0, day="2026-11-01"):
    return {"id": i, "dir": d, "driven_m": m, "seconds": 300, "max_gap_s": 1.0, "date": day, "start_s": start, "photos_usable": photos}


def test_match_becomes_level_1_and_single_pass_is_a_candidate():
    r = score([p("X1", "ab", 1580.0, 0)], MODEL, TODAY)[0]
    assert r["verdict"] == "MATCH" and r["level"] == 1
    assert r["kinds"] == "S" and r["tri_level"] == "candidate"


def test_photo_makes_it_corroborated_and_a_late_repeat_triangulates():
    rows = score([p("X1", "ab", 1580.0, 0, photos=2), p("X1", "ba", 1500.0, 4000)], MODEL, TODAY)
    assert rows[0]["kinds"] == "S+P+R" and rows[0]["tri_level"] == "triangulated"
    assert rows[1]["kinds"] == "S+R" and rows[1]["tri_level"] == "corroborated"


def test_quick_back_to_back_passes_are_not_a_repeat():
    rows = score([p("X1", "ab", 1580.0, 0), p("X1", "ba", 1500.0, 600)], MODEL, TODAY)
    assert all(r["kinds"] == "S" for r in rows)


def test_pass_shorter_than_straight_line_is_rejected_and_never_graded():
    r = score([p("X2", "ba", 12.6, 0)], MODEL, TODAY)[0]
    assert r["verdict"] == "REJECTED" and r["level"] == 3 and r["tri_level"] == "none"


def test_no_model_route_stays_level_3():
    r = score([p("X2", "ba", 11000.0, 0)], MODEL, TODAY)[0]
    assert r["verdict"] == "NO_MODEL" and r["level"] == 3


def test_poor_track_is_not_graded():
    q = p("X1", "ab", 1580.0, 0)
    q["max_gap_s"] = 999.0
    r = score([q], MODEL, TODAY)[0]
    assert r["verdict"] == "POOR_TRACK" and r["level"] == 3
