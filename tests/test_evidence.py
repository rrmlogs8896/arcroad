"""Evidence levels (pipeline/evidence.py). Synthetic evidence only."""

from datetime import date

from pipeline import evidence as ev

TODAY = date(2026, 11, 1)
GOOD = {"mapillary": {"controls_scored": 20, "reproduced": 19}}
WEAK = {"mapillary": {"controls_scored": 2, "reproduced": 2}}


def item(source, verdict, observed="2026-06-01", **kw):
    return {"source": source, "verdict": verdict, "observed": observed, **kw}


def test_wilson_lower_is_cautious_with_few_controls():
    assert ev.wilson_lower(2, 2) < 0.5
    assert ev.wilson_lower(19, 20) > 0.7
    assert ev.wilson_lower(0, 0) == 0.0


def test_model_alone_is_level_3():
    assert ev.grade([], GOOD, TODAY)["level"] == 3


def test_own_drive_match_is_level_1():
    g = ev.grade([item("own_drive", "MATCH")], GOOD, TODAY)
    assert g["level"] == 1 and g["corrected_m"] is None


def test_own_drive_much_shorter_is_a_correction_with_the_driven_distance():
    g = ev.grade([item("own_drive", "SHORTER", driven_m=188.0)], GOOD, TODAY)
    assert g["level"] == 1 and g["corrected_m"] == 188.0


def test_independent_fresh_match_from_a_proven_source_is_level_2():
    assert ev.grade([item("mapillary", "MATCH")], GOOD, TODAY)["level"] == 2


def test_source_that_never_proved_itself_on_controls_cannot_lift_a_place():
    assert ev.grade([item("mapillary", "MATCH")], WEAK, TODAY)["level"] == 3


def test_old_evidence_or_evidence_before_a_map_edit_is_history_only():
    old = ev.grade([item("mapillary", "MATCH", observed="2023-01-01")], GOOD, TODAY)
    assert old["level"] == 3 and old["history"]
    before_edit = ev.grade([item("mapillary", "MATCH", observed="2026-03-01")], GOOD, TODAY, map_last_edit=date(2026, 5, 1))
    assert before_edit["level"] == 3


def test_a_shorter_drive_or_a_dispute_makes_it_disputed_even_with_matches():
    g = ev.grade([item("mapillary", "MATCH"), item("mapillary", "SHORTER", contributor="x")], GOOD, TODAY)
    assert g["level"] == 4 and any("conflicts" in r for r in g["reasons"])
    assert ev.grade([item("overture", "OTHER_MAP_SHOWS_LINK")], GOOD, TODAY)["level"] == 4
    assert ev.grade([item("signs", "U_TURN_SIGN")], GOOD, TODAY)["level"] == 4


def test_same_contributor_same_day_counts_once():
    g = ev.grade([item("mapillary", "MATCH", contributor="a"), item("mapillary", "MATCH", contributor="a")], GOOD, TODAY)
    assert "1 recent independent drive" in g["reasons"][0]
