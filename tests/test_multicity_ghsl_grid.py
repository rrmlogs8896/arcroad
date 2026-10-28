"""Regression: "Could not calibrate the GHSL tile grid" (Oct 2026).

bengaluru, delhi_ncr, kolkata and ahmedabad failed twice because the tile grid
was calibrated from a live JRC download, which the server throttled. The grid is
now hard-coded from a measured tile (R8_C26). The first attempt assumed a clean
whole-degree grid and the in-run self-check caught it: the real grid is offset
(R1_C1 at lon -180.0079, lat +89.0996). These tests pin it without network.
"""

import importlib.util
import pathlib

import pytest

_PATH = pathlib.Path(__file__).resolve().parents[1] / "tools" / "multicity_collect.py"


@pytest.fixture(scope="module")
def mc():
    pytest.importorskip("osmium")  # the tool imports pipeline, which needs it
    spec = importlib.util.spec_from_file_location("multicity_collect", _PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_calibrate_failure_hyderabad_is_r8_c26(mc):
    # R8_C26 was the first tile the old calibration probed for Hyderabad.
    assert mc.ghsl_tiles_for(mc.CITIES["hyderabad"]) == [(8, 26)]


@pytest.mark.parametrize(
    ("city", "tiles"),
    [
        ("bengaluru", [(8, 26)]),     # 12.65-13.30 N, 77.30-77.95 E
        ("delhi_ncr", [(7, 26)]),     # 28.35-28.90 N, 76.85-77.55 E
        ("kolkata", [(7, 27)]),       # 22.35-22.80 N, 88.15-88.60 E
        ("ahmedabad", [(7, 26)]),     # 22.85-23.20 N, 72.40-72.80 E
        ("mumbai_mmr", [(7, 26), (8, 26)]),  # box crosses the 19.0996 N tile edge
        ("chennai", [(8, 26), (8, 27)]),  # box crosses 80 E
    ],
)
def test_calibrate_failure_cities_map_without_network(mc, city, tiles):
    assert mc.ghsl_tiles_for(mc.CITIES[city]) == tiles


def test_calibrate_failure_grid_matches_measured_tile(mc):
    g = mc.GHSL_GRID
    # Bounds JRC actually served for R8_C26 on 28 Oct 2026.
    assert g["ox"] + 25 * g["dx"] == pytest.approx(69.9920830785043, abs=1e-6)
    assert g["oy"] - 7 * g["dy"] == pytest.approx(19.099583459366997, abs=1e-6)


def test_calibrate_failure_grid_is_not_whole_degree(mc):
    # The bug the self-check caught: assuming tiles start at -180 / +90.
    assert mc.GHSL_GRID["ox"] != -180.0
    assert mc.GHSL_GRID["oy"] != 90.0
