"""Regression tests for B-09 and B-10, named after the failures.

B-09: the pairing step discarded the second endpoint, so no measurement could be
re-routed. B-10: the v1.0 run measured 1,549 points outside the box it declared.

Each test states its hypothesis, the competing explanation, and the observation
that separates them (reporting rule 5).
"""

import itertools
import math
import os
import tempfile

from pipeline import pairing
from pipeline.filters import oneway_dirs, way_level
from pipeline.geometry import haversine_m
from pipeline.provenance import validate_export, validate_point_record

M_PER_DEG_LAT = 110540.0


class _Net:
    """Tiny hand-built road network. Node ids are assigned in creation order."""

    def __init__(self):
        self.coords, self.ways, self._n, self._w = {}, [], 100, 1

    def node(self, lon, lat):
        self._n += 1
        self.coords[self._n] = (lon, lat)
        return self._n

    def way(self, nodes, **tags):
        fwd, bwd = oneway_dirs(tags)
        divided = tags.get("oneway") in ("yes", "true", "1", "-1")
        self.ways.append((self._w, nodes, fwd, bwd, tags["highway"], divided, way_level(tags)))
        self._w += 1

    def divided_road(self, lon0, lat0, n=11, step_m=100.0, sep_m=30.0, u_turn=True):
        """Eastbound carriageway at lat0, westbound sep_m north, one U-turn at the
        east end. Returns (eastbound nodes, westbound nodes listed west to east)."""
        dlon = step_m / (111320.0 * math.cos(math.radians(lat0)))
        dlat = sep_m / M_PER_DEG_LAT
        east = [self.node(lon0 + k * dlon, lat0) for k in range(n)]
        west = [self.node(lon0 + k * dlon, lat0 + dlat) for k in range(n)]
        self.way(east, highway="trunk", oneway="yes")
        self.way(west[::-1], highway="trunk", oneway="yes")
        if u_turn:
            self.way([east[-1], west[-1]], highway="trunk_link")
        return east, west


CFG = pairing.PairingConfig(sample_stride=1, label="test")
INSIDE = (78.40, 17.40)          # Hyderabad core, inside the declared HMDA box
OUTSIDE = (79.05, 17.40)         # ~60 km east, outside it (cf. B-10's 79.07 E)


def test_b09_every_pair_keeps_both_endpoints_and_can_be_rerouted():
    """Hypothesis: records carry the far-kerb node, so they can be re-routed.
    Competing: they pass only because the validator is lax.
    Separates: B must be the hand-placed opposite node, straight_m must recompute
    from the emitted coordinates, re-routing from the emitted node ids must give
    the same network_m, and the validator must reject the record with B removed."""
    net = _Net()
    east, west = net.divided_road(*INSIDE)
    run = pairing.run_pairing(net.ways, net.coords, config=CFG)

    assert run.records, "a divided road must produce pairs"
    n_bad, report = validate_export(run.records)
    assert n_bad == 0, report

    opposite = dict(zip(east, west, strict=True)) | dict(zip(west, east, strict=True))
    graph = pairing.build_graph(net.ways, net.coords)
    from scipy.sparse.csgraph import dijkstra

    for r in run.records:
        assert r["b_node_id"] == opposite[r["a_node_id"]]
        assert (r["b_lon"], r["b_lat"]) == tuple(round(v, 7) for v in net.coords[r["b_node_id"]])
        assert abs(haversine_m(r["a_lon"], r["a_lat"], r["b_lon"], r["b_lat"]) - r["straight_m"]) < 0.2
        if r["network_m"] is not None:
            a, b = graph.idx_of[r["a_node_id"]], graph.idx_of[r["b_node_id"]]
            assert round(float(dijkstra(graph.G, indices=a)[b]), 1) == r["network_m"]

    stripped = {k: v for k, v in run.records[0].items() if k not in ("b_lat", "b_lon")}
    assert validate_point_record(stripped), "the validator must be able to fail"


def test_b09_eastbound_kerb_routes_via_the_u_turn_by_hand_count():
    """Hypothesis: routed distance is the drive to the U-turn and back.
    Competing: some shorter path exists in the port that the notebook lacked.
    Separates: the westmost eastbound node must route 10 x 100 m east, 30 m
    across and 10 x 100 m back: about 2,030 m (the notebook's own §8 case).
    Expected is summed segment by segment from the coordinates, independently of
    the graph; the nominal 100 m steps come out at 99.89 m under haversine."""
    net = _Net()
    east, west = net.divided_road(*INSIDE)
    run = pairing.run_pairing(net.ways, net.coords, config=CFG)
    rec = next(r for r in run.records if r["a_node_id"] == east[0])
    path = [*east, *west[::-1]]
    c = net.coords
    expected = sum(haversine_m(*c[p], *c[q]) for p, q in itertools.pairwise(path))
    assert 2000 < expected < 2060
    assert abs(rec["network_m"] - expected) < 0.1
    assert 65 < rec["detour_index"] < 70


def test_b10_point_outside_declared_box_is_excluded_and_counted():
    """Hypothesis: the clip removes pairs whose endpoint A is outside the box.
    Competing: the outside pairs vanish for some other reason (never paired).
    Separates: the same graph run with a box that includes them keeps them; with
    the declared box they are gone and the excluded count equals exactly that
    number, while the inside pairs are untouched."""
    net = _Net()
    net.divided_road(*INSIDE)
    net.divided_road(*OUTSIDE, n=3)

    wide = pairing.run_pairing(net.ways, net.coords, config=CFG, study_bbox=(77.0, 16.0, 80.0, 19.0))
    n_out = sum(1 for r in wide.records if r["a_lon"] > pairing.HMDA_BBOX[2])
    assert n_out > 0, "control: the outside road must pair when the box allows it"

    run = pairing.run_pairing(net.ways, net.coords, config=CFG)
    assert run.meta["pairs_outside_box"] == n_out
    assert run.meta["pairs_kept"] == len(wide.records) - n_out
    assert all(pairing.in_box(r["a_lon"], r["a_lat"], pairing.HMDA_BBOX) for r in run.records)
    assert run.meta["study_bbox_is_declared_hmda"] is True
    assert {r["study_bbox"] for r in run.records} == {pairing.bbox_str(pairing.HMDA_BBOX)}
    assert wide.meta["study_bbox_is_declared_hmda"] is False


def test_b10_default_box_is_the_declared_hmda_box():
    assert pairing.HMDA_BBOX == (78.050, 17.050, 78.850, 17.750)
    assert pairing.ZONES["hmda_all"] == pairing.HMDA_BBOX


def test_null_route_names_its_reason_never_a_blank():
    """Hypothesis: every null network_m carries the specific reason.
    Competing: the test passes vacuously because no null occurs.
    Separates: build one pair in a separate graph component and one whose only
    route exceeds the limit; require at least one null of EACH kind, with the
    right reason on each, and no null without one."""
    net = _Net()
    # different component: two carriageways, nothing connecting them at all
    a_side, b_side = net.divided_road(*INSIDE, n=3, u_turn=False)
    # same component, but the U-turn is 10 km away: unreachable within 5 km
    far_e, _ = net.divided_road(78.45, 17.42, n=51, step_m=200.0)

    cfg = pairing.PairingConfig(sample_stride=1, route_limit_m=5000, label="test")
    run = pairing.run_pairing(net.ways, net.coords, config=cfg)

    reasons = {r["a_node_id"]: r["null_reason"] for r in run.records if r["network_m"] is None}
    disconnected = set(a_side) | set(b_side)
    assert any(nid in disconnected for nid in reasons), "control: a cross-component null must occur"
    assert any(nid in far_e for nid in reasons), "control: a beyond-limit null must occur"
    for nid, why in reasons.items():
        assert why == ("different_component" if nid in disconnected else "unreachable")
    assert all(r["null_reason"] is None for r in run.records if r["network_m"] is not None)
    assert validate_export(run.records)[0] == 0


def test_export_with_an_invalid_record_fails_and_writes_nothing():
    """Hypothesis: write_point_file refuses an invalid set outright.
    Competing: it writes a partial file, then raises.
    Separates: after the refusal, neither the CSV nor its metadata may exist."""
    net = _Net()
    net.divided_road(*INSIDE)
    run = pairing.run_pairing(net.ways, net.coords, config=CFG)
    bad = [dict(r) for r in run.records]
    bad[0]["b_lat"] = None

    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "points.csv")
        try:
            pairing.write_point_file(bad, path, run.meta)
        except pairing.ExportValidationError:
            pass
        else:
            raise AssertionError("an invalid record must fail the export")
        assert os.listdir(d) == []

        pairing.write_point_file(run.records, path, run.meta)
        assert os.path.exists(path) and os.path.exists(path + ".meta.json")


def test_export_of_zero_records_fails():
    """B-07's shape: a header and no rows must not pass as a result."""
    with tempfile.TemporaryDirectory() as d:
        try:
            pairing.write_point_file([], os.path.join(d, "p.csv"))
        except pairing.ExportValidationError:
            return
    raise AssertionError("an empty export must fail")
