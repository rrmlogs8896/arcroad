"""M2 access to essentials (pipeline/access.py). Sample data only, all invented."""

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


def test_excess_is_against_the_hospital_actually_reached_by_road():
    # The nearest by line is across a median (3 km by road); the far one is 600 m by road.
    rec = access_record(CELL, "government", DESTS, {"near": 3000.0, "far": 600.0}, snap_m=20)
    assert rec["status"] == "measured"
    assert rec["line_dest_id"] == "near"
    assert rec["road_dest_id"] == "far"
    assert rec["road_m"] == 600.0
    assert rec["excess_m"] == pytest.approx(600.0 - rec["road_dest_line_m"])


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
