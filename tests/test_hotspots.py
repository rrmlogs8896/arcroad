import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "research" / "runner" / "app"))
import hotspots as h


def test_disk_sum_counts_only_cells_inside_the_radius():
    a = np.ones((200, 200))
    step = 1 / 1200  # 3 arc-seconds
    tr = (step, 0, 78.0, 0, -step, 17.6)
    lon, lat = 78.0 + 100 * step, 17.6 - 100 * step
    mx, my = h.m_per_deg(lat)
    cell_area = (step * mx) * (step * my)
    got = h.disk_sum(a, tr, lon, lat, 1000)
    assert abs(got - math.pi * 1000 ** 2 / cell_area) / got < 0.03


def test_disk_sum_ignores_nodata_and_off_raster():
    a = np.full((50, 50), np.nan)
    assert h.disk_sum(a, (0.001, 0, 78, 0, -0.001, 17.5), 78.02, 17.48, 500) == 0
    assert h.disk_sum(np.ones((5, 5)), (0.001, 0, 78, 0, -0.001, 17.5), 80, 10, 500) == 0


def test_spearman_and_ranks():
    assert abs(h.spearman([1, 2, 3, 4, 5], [10, 20, 30, 40, 50]) - 1) < 1e-9
    assert abs(h.spearman([1, 2, 3, 4, 5], [5, 4, 3, 2, 1]) + 1) < 1e-9
    assert h.spearman([1, 2, 3], [1, 2, 3]) is None
    assert list(h.pct_rank([30, 10, 20])) == [1.0, 0.0, 0.5]


def test_grid_spacing_is_close_to_500_m():
    cells = h.grid_cells((78.3, 17.4, 78.33, 17.43))
    (x0, y0), (x1, _) = cells[0], cells[1]
    mx, _ = h.m_per_deg(y0)
    assert abs((x1 - x0) * mx - 500) < 1


def test_kd_tree_matches_brute_force():
    rng = np.random.default_rng(1)
    pts = [(78.3 + rng.random() * 0.05, 17.45 + rng.random() * 0.05) for _ in range(300)]
    lines = [[(78.3 + i * 0.001, 17.47), (78.3 + i * 0.001 + 0.001, 17.47)] for i in range(40)]
    n = h.Near(pts, lines, 17.47)
    for lon, lat in [(78.32, 17.47), (78.33, 17.48)]:
        assert n.count(lon, lat, 1000) == h.count_near(pts, lon, lat, 1000)
        assert abs(n.road_km(lon, lat, 1000) - h.line_km_near(lines, lon, lat, 1000)) < 0.05
