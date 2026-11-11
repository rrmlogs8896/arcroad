"""Median openings on a divided road built by hand (docs/PREREG-uturn-spacing.md)."""
from pipeline.medians import (
    find_openings,
    flag,
    ground_sample,
    ground_verdict,
    junctions,
    summarise,
)

E = 0.0009   # about 100 m of longitude here
N = 0.000135  # about 15 m of latitude


def node(i, lon, lat, **tags):
    d = {"type": "node", "id": i, "lon": lon, "lat": lat}
    if tags:
        d["tags"] = tags
    return d


def way(i, nodes, **tags):
    return {"type": "way", "id": i, "nodes": nodes, "tags": tags}


def divided_road(gaps, cross_at=None, duplicate=False, bridge=False):
    """Eastbound carriageway on y=0, westbound 15 m north; a gap at each x index in gaps (x * 100 m)."""
    xs = range(0, 8)
    els = [node(100 + x, x * E, 0) for x in xs] + [node(200 + x, x * E, N) for x in xs]
    main = {"highway": "primary", "name": "Old Mumbai Highway", "oneway": "yes"}
    if bridge:
        main = dict(main, bridge="yes", layer="1")
    els += [way(1, [100 + x for x in xs], **main), way(2, [200 + x for x in reversed(xs)], **main)]
    for k, x in enumerate(gaps):
        els.append(way(10 + k, [100 + x, 200 + x], highway="primary_link"))
        if duplicate:
            els.append(way(50 + k, [200 + x, 100 + x], highway="primary_link"))
    if cross_at is not None:
        els += [node(300, cross_at * E, -5 * N), way(3, [300, 100 + cross_at], highway="residential", name="Lane 4")]
    return els


def test_each_gap_is_one_opening_even_when_mapped_once_per_direction():
    assert len(find_openings(divided_road([1, 5]))) == 2
    assert len(find_openings(divided_road([1, 5], duplicate=True))) == 2


def test_two_way_roads_and_flyovers_have_no_openings():
    els = divided_road([1])
    for e in els:
        if e["type"] == "way" and e["id"] in (1, 2):
            del e["tags"]["oneway"]
    assert find_openings(els) == []
    assert find_openings(divided_road([1], bridge=True)) == []


def test_flags_close_spacing_and_junctions():
    els = divided_road([1, 2, 6], cross_at=6)
    ops = flag(find_openings(els), junctions(els, find_openings(els)))
    by_x = {round(o["lon"] / E): o for o in ops}
    assert by_x[1]["close_to_opening"] and by_x[2]["close_to_opening"]   # 100 m apart
    assert by_x[6]["at_junction"] and not by_x[6]["second_look"]          # the opening is the junction itself
    s = summarise(ops)
    assert s["openings"] == 3 and s["second_look"] == 2 and s["at_junction"] == 1


def test_an_opening_60_m_before_a_junction_is_next_to_it():
    """11 Nov 2026: the first rule flagged openings 4 to 20 m from a junction, which are the junction itself."""
    els = divided_road([3], cross_at=6)
    # move the cross road 60 m east of gap 3 by placing it between nodes: reuse node 103 + 0.6 * E via a new node
    els = [e for e in els if not (e["type"] == "way" and e["id"] == 3)]
    els += [node(301, 3.6 * E, -5 * N), node(302, 3.6 * E, 0), way(4, [301, 302], highway="residential", name="Lane 9")]
    for e in els:
        if e["type"] == "way" and e["id"] == 1:
            e["nodes"] = [100, 101, 102, 103, 302, 104, 105, 106, 107]
    ops = flag(find_openings(els), junctions(els, find_openings(els)))
    assert len(ops) == 1 and not ops[0]["at_junction"] and ops[0]["next_to_junction"]
    assert 50 < ops[0]["nearest_junction_m"] < 70


def test_signal_counts_as_a_junction():
    els = [*divided_road([4]), node(400, 4 * E + 0.0005, 0, highway="traffic_signals")]
    ops = find_openings(els)
    assert flag(ops, junctions(els, ops))[0]["next_to_junction"]   # signal about 55 m along the road


def test_ground_check_draw_is_fixed_by_its_seed_and_needs_seven_in_ten():
    ops = [{"second_look": i % 2 == 0} for i in range(40)]
    assert ground_sample(ops, 7) == ground_sample(ops, 7) and len(ground_sample(ops, 7)) == 10
    assert ground_verdict([True] * 7 + [False] * 3, 20) == "pass"
    assert ground_verdict([True] * 6 + [False] * 4, 20) == "fail: mapping finding"
    assert ground_verdict([True] * 5, 20) == "incomplete"
    assert ground_verdict([True, True, False], 3) == "fail: mapping finding"
    assert ground_verdict([True, True, True], 3) == "pass"
