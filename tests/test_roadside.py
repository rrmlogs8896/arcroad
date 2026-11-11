"""Roadside activity and slow traffic, on label records built by hand (docs/PREREG-roadside-activity.md)."""
from pipeline.roadside import (
    combine,
    dedupe,
    exposure,
    label_agreement,
    outcome,
    stratum,
    tabulate,
    usable,
)


def rec(i, slow, act, road="arterial", hour=9, lat=17.40, lon=78.30, minute=None):
    lab = {"image_quality": "usable", "view": "windscreen", "road_type": road,
           "congestion": "queue" if slow else "free",
           "establishment_spillover": "yes" if act else "no", "parking_on_carriageway": "none",
           "vendors_on_carriageway": "no"}
    m = i if minute is None else minute
    return {"file": f"f{i}.jpg", "dt": f"2026:11:0{1 + m // 600} {hour:02d}:{(m % 600) // 10:02d}:{(m % 10) * 6:02d}",
            "lat": str(lat + i * 0.001), "lon": str(lon), "labels": lab}


def test_definitions():
    lab = {"congestion": "slow", "establishment_spillover": "no", "parking_on_carriageway": "one_lane",
           "vendors_on_carriageway": "no"}
    assert outcome(lab) is True and exposure(lab) is True
    assert exposure({"establishment_spillover": "unsure", "parking_on_carriageway": "none",
                     "vendors_on_carriageway": "no"}) is None
    assert outcome({"congestion": "unsure"}) is None
    assert stratum(rec(0, True, True, hour=18)) == "arterial · peak"
    assert stratum(rec(0, True, True, road="flyover")) is None
    assert not usable(dict(rec(0, True, True), labels={"image_quality": "poor", "view": "windscreen"}))


def test_a_queue_photographed_many_times_counts_once():
    burst = [rec(0, True, True, minute=0), dict(rec(0, True, True, minute=1), file="g.jpg")]
    burst[1]["lat"] = burst[0]["lat"]
    assert len(dedupe(burst)) == 1


def test_supported_only_with_enough_photos_and_a_clear_difference():
    recs = [rec(i, slow=i % 10 < 7, act=True) for i in range(0, 80)]          # 70% slow with activity
    recs += [rec(i, slow=i % 10 < 3, act=False) for i in range(100, 180)]     # 30% slow without
    r = combine(tabulate(recs))
    assert r["verdict"] == "supported" and r["diff"] > 0.3 and r["ci"][0] > 0
    small = combine(tabulate(recs[:20] + recs[80:100]))
    assert small["verdict"] == "not enough photos"


def test_no_difference_is_not_supported():
    recs = [rec(i, slow=i % 2 == 0, act=True) for i in range(80)] + [rec(i, slow=i % 2 == 0, act=False)
                                                                     for i in range(100, 180)]
    assert combine(tabulate(recs))["verdict"] == "not supported"


def test_label_check_passes_a_field_at_80_percent():
    model = {f"p{i}": {"congestion": "slow"} for i in range(50)}
    person = {f"p{i}": {"congestion": "slow" if i < 40 else "free"} for i in range(50)}
    a = label_agreement(model, person, fields=("congestion",))
    assert a["congestion"]["share"] == 0.8 and a["congestion"]["passes"]
