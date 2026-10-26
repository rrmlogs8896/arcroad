"""M2 access to essentials (pipeline/access.py). Sample data only, all invented."""

import math

import pytest

from pipeline.access import (
    SNAP_MAX_M,
    access_record,
    add_population,
    cell_of,
    export_problems,
    grid_cells,
    hospital_layers,
    is_govt_hospital,
    nearest_by_line,
    people_summary,
)
from pipeline.geometry import haversine_m

BBOX = (78.20, 17.50, 78.21, 17.51)


def test_grid_cells_are_about_250_m_apart_and_cover_the_bbox():
    cells, steps = grid_cells(BBOX)
    a = next(c for c in cells if c["cell_id"] == "r0c0")
    b = next(c for c in cells if c["cell_id"] == "r0c1")
    assert 245 < haversine_m(a["lon"], a["lat"], b["lon"], b["lat"]) < 255
    assert all(cell_of(c["lon"], c["lat"], BBOX, steps) == c["cell_id"] for c in cells)


def test_bad_bbox_is_refused():
    with pytest.raises(ValueError):
        grid_cells((78.21, 17.50, 78.20, 17.51))


def test_population_outside_the_bbox_is_reported_not_lost():
    cells, steps = grid_cells(BBOX)
    pixels = [{"lon": 78.2001, "lat": 17.5001, "pop": 40}, {"lon": 79.0, "lat": 17.5, "pop": 7}]
    out, outside = add_population(cells, pixels, BBOX, steps)
    assert sum(c["pop"] for c in out) == 40
    assert outside == 7


@pytest.mark.parametrize("ftype,expected", [
    ("District Hospital", True),
    ("Area Hospital", True),
    ("Community Health Centre", True),
    ("CHC", True),
    ("Primary Health Centre", False),
    ("Urban Health Centre", False),
    ("Sub Centre", False),
    ("Ayurveda Hospital", False),
    ("Ayush Dispensary", False),
])
def test_only_government_hospitals_count(ftype, expected):
    f = {"ownership": "Government", "status": "Functional", "facility_type": ftype}
    assert is_govt_hospital(f) is expected


def test_private_and_non_functional_official_rows_are_not_government_hospitals():
    assert not is_govt_hospital({"ownership": "Private", "status": "Functional", "facility_type": "Hospital"})
    assert not is_govt_hospital({"ownership": "Government", "status": "Non-Functional", "facility_type": "District Hospital"})


def test_an_osm_hospital_next_to_an_official_one_is_not_counted_twice_or_as_private():
    official = [{"id": "1", "ownership": "Government", "status": "Functional",
                 "facility_type": "Area Hospital", "lon": 78.2050, "lat": 17.5050}]
    osm = [
        {"id": 10, "lon": 78.2051, "lat": 17.5051, "tags": {"amenity": "hospital", "name": "Same place"}},
        {"id": 11, "lon": 78.2090, "lat": 17.5090, "tags": {"amenity": "hospital", "name": "Private"}},
        {"id": 12, "lon": 78.2010, "lat": 17.5010, "tags": {"amenity": "hospital", "operator:type": "government"}},
        {"id": 13, "lon": 78.2020, "lat": 17.5020, "tags": {"amenity": "clinic"}},
    ]
    layers = hospital_layers(official, osm)
    assert [d["dest_id"] for d in layers["government"]] == ["tg:1", "osm:12"]
    assert [d["dest_id"] for d in layers["private"]] == ["osm:11"]


DESTS = [
    {"dest_id": "near", "lon": 78.2060, "lat": 17.5050},
    {"dest_id": "far", "lon": 78.2090, "lat": 17.5050},
]
CELL = {"cell_id": "r0c0", "lon": 78.2050, "lat": 17.5050, "pop": 100}


def test_nearest_by_line():
    d, m = nearest_by_line(CELL["lon"], CELL["lat"], DESTS)
    assert d["dest_id"] == "near" and 100 < m < 110


def test_excess_is_road_to_the_reachable_hospital_minus_the_nearest_on_the_map():
    # The nearest by line is across a median (3 km by road); the far one is 600 m by road.
    rec = access_record(CELL, "government", DESTS, {"near": 3000.0, "far": 600.0}, snap_m=20)
    assert rec["status"] == "measured"
    assert rec["line_dest_id"] == "near"
    assert rec["road_dest_id"] == "far"
    assert rec["road_m"] == 600.0
    assert rec["excess_m"] == pytest.approx(600.0 - rec["line_m"])
    assert rec["road_dest_line_m"] > rec["line_m"]
    assert rec["ratio"] == pytest.approx(600.0 / rec["line_m"])


def test_unmeasured_is_none_never_zero():
    gap = access_record(CELL, "government", DESTS, {"near": 500.0}, snap_m=SNAP_MAX_M + 1)
    assert gap["status"] == "gap_no_road" and gap["excess_m"] is None
    unreach = access_record(CELL, "government", DESTS, {"near": None, "far": float("inf")}, snap_m=10)
    assert unreach["status"] == "unreachable" and unreach["excess_m"] is None
    none = access_record(CELL, "government", [], {}, snap_m=10)
    assert none["status"] == "no_destinations"


def test_summary_counts_every_person_including_the_unmeasured():
    recs = [
        {"status": "measured", "pop": 300, "excess_m": 100.0},
        {"status": "measured", "pop": 100, "excess_m": 2500.0},
        {"status": "gap_no_road", "pop": 50, "excess_m": None},
        {"status": "unreachable", "pop": 25, "excess_m": None},
    ]
    s = people_summary(recs)
    assert s["people_total"] == 475
    assert s["people_measured"] == 400
    assert s["people_unmeasured_by_status"] == {"gap_no_road": 50, "unreachable": 25}
    assert s["median_excess_m"] == 100.0
    assert s["pct_people_excess_ge_2000m"] == 25.0


def test_a_measured_row_without_provenance_cannot_be_exported():
    rec = access_record(CELL, "government", DESTS, {"near": 300.0}, snap_m=10)
    assert "missing graph_hash" in export_problems(rec)
    rec.update(extract_date="2026-10-25", graph_hash="abc", population_source="GHS-POP",
               destination_source="TG health centres")
    assert export_problems(rec) == []


# The staging page (web/access.html, web/m2/access.js) is held to the kit's rules.
def _page_files():
    import pathlib
    web = pathlib.Path(__file__).resolve().parents[1] / "web"
    return [web / "access.html", web / "m2" / "access.js"]


def test_access_page_makes_no_network_or_storage_call():
    import re

    from tests.test_kit import FORBIDDEN
    for path in _page_files():
        hits = [pat for pat in FORBIDDEN if re.search(pat, path.read_text())]
        assert not hits, f"{path.name} uses {hits}"


def test_access_page_is_flagged_and_labelled_sample():
    html, js = (p.read_text() for p in _page_files())
    assert "get('m2') !== '1'" in js, "page must stay closed without ?m2=1"
    assert "noindex" in html
    assert "invented sample" in html and "Sample · invented figures" in html


# ---- city-scale run on a synthetic town (needs numpy and scipy, as CI has) ----
# 100 m street grid, 3 km x 2 km, cut by a divided road between y=1000 and
# y=1100 that can be crossed only at x=500 and x=2500. Hospitals are south of it.

LAT0, LON0 = 17.5, 78.3
KLON = 111_320.0 * math.cos(math.radians(LAT0))


def _ll(x, y):
    return LON0 + x / KLON, LAT0 + y / 111_320.0


def _town():
    import numpy as np
    from scipy.sparse import csr_matrix

    xs, ys = range(0, 3001, 100), range(0, 2001, 100)
    idx = {(x, y): i for i, (x, y) in enumerate((x, y) for y in ys for x in xs)}
    lon = np.empty(len(idx))
    lat = np.empty(len(idx))
    for (x, y), i in idx.items():
        lon[i], lat[i] = _ll(x, y)
    rows, cols, vals = [], [], []

    def edge(a, b):
        rows.extend([idx[a], idx[b]])
        cols.extend([idx[b], idx[a]])
        vals.extend([100.0, 100.0])

    for (x, y) in idx:
        if (x + 100, y) in idx:
            edge((x, y), (x + 100, y))
        if (x, y + 100) in idx:
            if y == 1000 and x not in (500, 2500):
                continue  # the median
            edge((x, y), (x, y + 100))
    G = csr_matrix((vals, (rows, cols)), shape=(len(idx), len(idx)))
    return G, lon, lat


def _cells():
    out = []
    for i, (x, y) in enumerate([(1500, 1900), (1500, 300), (2950, 1950)]):
        lon, lat = _ll(x, y)
        out.append({"cell_id": f"c{i}", "lon": lon, "lat": lat, "pop": 500})
    return out


def _hosp():
    lon, lat = _ll(1500, 600)
    far_lon, far_lat = _ll(1500, 5000)  # 3 km from any road: must be dropped, not used
    return [{"dest_id": "H1", "lon": lon, "lat": lat}, {"dest_id": "HX", "lon": far_lon, "lat": far_lat}]


def test_the_far_side_of_the_median_pays_the_detour_and_the_near_side_does_not():
    from pipeline.access import measure_layer

    G, lon, lat = _town()
    recs, dropped = measure_layer(_cells(), "government", _hosp(), lon, lat, G)
    north, south = recs[0], recs[1]
    assert [d["dest_id"] for d in dropped] == ["HX"]
    assert north["status"] == south["status"] == "measured"
    assert south["excess_m"] < 1  # straight down the grid: no extra
    # north: straight line 1300 m; by road it must go to x=500 or 2500 and back
    assert north["line_m"] == pytest.approx(1300, abs=2)
    assert north["road_m"] == pytest.approx(1000 + 1300 + 1000, abs=2)
    assert north["excess_m"] == pytest.approx(2000, abs=3)


def test_one_way_streets_are_driven_the_legal_way():
    from scipy.sparse import csr_matrix

    from pipeline.access import nearest_reachable

    # 0 -> 1 -> 2 one way; destination is node 0. Node 2 cannot reach it.
    G = csr_matrix(([10.0, 10.0], ([0, 1], [1, 2])), shape=(3, 3))
    dist, _src = nearest_reachable(G, [0])
    assert dist[0] == 0 and dist[1] == float("inf") and dist[2] == float("inf")
    G2 = csr_matrix(([10.0, 10.0], ([2, 1], [1, 0])), shape=(3, 3))
    dist2, src2 = nearest_reachable(G2, [0])
    assert dist2[2] == 20.0 and src2[2] == 0


def test_vectorised_population_matches_the_reference():
    from pipeline.access import assign_population

    cells, steps = grid_cells(BBOX)
    px = [{"lon": 78.2001 + i * 0.0007, "lat": 17.5001 + i * 0.0006, "pop": i + 1} for i in range(14)]
    px.append({"lon": 79.0, "lat": 17.5, "pop": 9})
    ref, ref_out = add_population(cells, px, BBOX, steps)
    got, got_out = assign_population([p["lon"] for p in px], [p["lat"] for p in px], [p["pop"] for p in px], BBOX, steps)
    assert {c["cell_id"]: c["pop"] for c in ref if c["pop"]} == got
    assert ref_out == got_out == 9


def _strat_records(adj_excess, not_excess, strata=4, n=40):
    recs = []
    for s in range(strata):
        for adj, ex in ((True, adj_excess), (False, not_excess)):
            recs += [{"status": "measured", "pop": 100, "excess_m": ex, "adjacent": adj, "stratum": f"s{s}"}] * n
    return recs


def test_rule5_verdicts():
    from pipeline.access import rule5_verdict

    assert rule5_verdict(_strat_records(900, 200))["verdict"] == "SUPPORTED"
    assert rule5_verdict(_strat_records(200, 900))["verdict"] == "REJECTED"
    assert rule5_verdict(_strat_records(900, 200, strata=2))["verdict"] == "INSUFFICIENT"
    thin = _strat_records(900, 200, n=10)
    assert rule5_verdict(thin)["comparable_strata"] == 0


def test_strata_are_tagged():
    from pipeline.access import add_strata, densify

    G, lon, lat = _town()
    from pipeline.access import measure_layer

    recs, _ = measure_layer(_cells(), "government", _hosp(), lon, lat, G)
    art = densify([[_ll(0, 1050), _ll(3000, 1050)]])
    add_strata(recs, art, lon, lat, centre=_ll(1500, 1000))
    assert recs[0]["adjacent"] is False and recs[0]["arterial_m"] > 800
    assert all("stratum" in r and r["density"] in ("low", "mid", "high") for r in recs)
