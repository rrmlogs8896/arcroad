"""Detour baseline for a proposed one-way loop (docs/PREREG-cyberabad-loop.md), on small networks whose
answers are known by hand."""

from pipeline.loopcost import (
    build_graph,
    compare,
    is_longer,
    loop_doubles_back,
    loop_network,
    loop_path,
    major_nodes,
    nearest_node,
    shortest,
    summarise,
)

# About 111 m per 0.001 degree of latitude; longitudes here are near the equator so x and y scale alike.
D = 0.001


def node(i, lon, lat):
    return {"type": "node", "id": i, "lon": lon, "lat": lat}


def way(i, nodes, **tags):
    return {"type": "way", "id": i, "nodes": nodes, "tags": {"highway": "secondary", **tags}}


def square():
    """Two-way square 1-2-3-4, each side about 111 m."""
    els = [node(1, 0, 0), node(2, D, 0), node(3, D, D), node(4, 0, D),
           way(10, [1, 2]), way(11, [2, 3]), way(12, [3, 4]), way(13, [4, 1])]
    return build_graph(els)


def test_oneway_is_obeyed_and_access_private_is_dropped():
    els = [node(1, 0, 0), node(2, D, 0), node(3, 2 * D, 0),
           way(10, [1, 2], oneway="yes"), way(11, [2, 3], access="private")]
    _, adj = build_graph(els)
    assert 2 in adj[1] and 1 not in adj.get(2, {})
    assert 3 not in adj.get(2, {})


def test_shortest_path_on_the_square():
    _, adj = square()
    d, path = shortest(adj, 1, 3)
    assert path in ([1, 2, 3], [1, 4, 3])
    assert 215 < d < 230


def test_unreachable_is_none_not_zero():
    els = [node(1, 0, 0), node(2, D, 0), node(3, 5 * D, 0), way(10, [1, 2])]
    _, adj = build_graph(els)
    assert shortest(adj, 1, 3) == (None, [])


def test_one_way_loop_makes_the_reverse_trip_go_round():
    nodes, adj = square()
    edges, missing = loop_path(adj, [1, 2, 3, 4])
    assert not missing
    assert set(edges) == {(1, 2), (2, 3), (3, 4), (4, 1)}
    loop, removed = loop_network(nodes, adj, edges)
    assert set(removed) == {(2, 1), (3, 2), (4, 3), (1, 4)}
    today, _ = shortest(adj, 2, 1)
    after, _ = shortest(loop, 2, 1)
    assert 105 < today < 116 and 325 < after < 345


def test_opposite_carriageway_of_a_divided_road_is_removed_but_a_cross_street_is_kept():
    # Loop runs east along 1-2. A separate one-way carriageway 4->3 runs west 15 m north of it: removed.
    # A cross street 5-6 runs north-south across it: kept.
    e = 0.000135  # about 15 m
    els = [node(1, 0, 0), node(2, 2 * D, 0), node(3, 0, e), node(4, 2 * D, e),
           node(5, D, -D), node(6, D, D),
           way(10, [1, 2], oneway="yes"), way(11, [4, 3], oneway="yes"), way(12, [5, 6])]
    nodes, adj = build_graph(els)
    _, removed = loop_network(nodes, adj, [(1, 2)])
    assert (4, 3) in removed
    assert (5, 6) not in removed and (6, 5) not in removed


def test_threshold_needs_both_100_m_and_10_percent():
    assert is_longer(1000, 1100) is True
    assert is_longer(1000, 1099) is False   # 99 m: under 100 m
    assert is_longer(5000, 5400) is False   # 400 m but only 8%
    assert is_longer(None, 500) is None


def test_compare_and_summary_keep_every_pair():
    nodes, adj = square()
    edges, _ = loop_path(adj, [1, 2, 3, 4])
    loop, _ = loop_network(nodes, adj, edges)
    rows = compare(adj, loop, [("A", 1), ("B", 2), ("C", 3), ("D", 4)])
    assert len(rows) == 12
    s = summarise(rows)
    assert s["pairs"] == 12 and s["judged"] == 12
    # Neighbours against the loop (4 pairs) go from one side to three: longer. Opposite corners do not change.
    assert s["longer"] == 4 and s["share_longer"] == round(4 / 12, 3)
    assert s["hypothesis"] == "not rejected"


def test_nearest_node_ignores_isolated_nodes():
    els = [node(1, 0, 0), node(2, D, 0), node(9, 0.00001, 0), way(10, [1, 2])]
    nodes, adj = build_graph(els)
    n, d = nearest_node(nodes, adj, 0.00001, 0)
    assert n == 1 and d < 2


def test_gate_snaps_to_a_main_road_not_a_campus_lane():
    # A campus lane (residential) passes 5 m from the building; the main road is 50 m away.
    els = [node(1, 0, 0.00005), node(2, D, 0.00005), node(3, 0, 0.00045), node(4, D, 0.00045),
           way(10, [1, 2], highway="residential"), way(11, [3, 4], highway="secondary")]
    nodes, adj = build_graph(els)
    n, _ = nearest_node(nodes, adj, 0, 0, allowed=major_nodes(els))
    assert n == 3


def test_gate_does_not_snap_onto_a_flyover():
    # A flyover passes right over the gate; the junction road below is 40 m away.
    els = [node(1, 0, 0), node(2, D, 0), node(3, 0, 0.00036), node(4, D, 0.00036),
           way(10, [1, 2], highway="primary", bridge="yes", layer="2"), way(11, [3, 4], highway="primary")]
    nodes, adj = build_graph(els)
    n, _ = nearest_node(nodes, adj, 0, 0, allowed=major_nodes(els))
    assert n == 3


def test_a_leg_that_u_turns_is_caught():
    # Loop edges run east 1->2, then back west on the other carriageway 4->3, 15 m away: a U-turn in the leg.
    e = 0.000135
    els = [node(1, 0, 0), node(2, 2 * D, 0), node(3, 0, e), node(4, 2 * D, e)]
    nodes, _ = build_graph(els)
    assert set(loop_doubles_back(nodes, [(1, 2), (4, 3)])) == {(1, 2), (4, 3)}
    assert loop_doubles_back(nodes, [(1, 2)]) == []
