"""The 3D corridor base job: open data only, nothing about walking, the pre-registered box."""
import io
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research" / "runner" / "app"))
import corridor3d as c  # noqa: E402


def test_box_is_the_registered_study_area():
    assert c.BOX == (17.40, 78.33, 17.47, 78.42)
    assert "AREA = (17.40, 78.33, 17.47, 78.42)" in (ROOT / "tools" / "uturn_study.py").read_text()


def test_nothing_about_walking_is_fetched():
    q = " ".join(c.queries().values()).lower()
    for word in ("footway", "pedestrian", "crossing", "path", "steps", "sidewalk"):
        assert word not in q, word


def test_slim_keeps_tags_and_geometry_only():
    raw = {"elements": [
        {"type": "way", "id": 1, "tags": {"highway": "trunk", "lanes": "3"}, "nodes": [1, 2],
         "geometry": [{"lat": 17.4, "lon": 78.3}, {"lat": 17.41, "lon": 78.31}]},
        {"type": "node", "id": 2, "lat": 17.4, "lon": 78.3, "tags": {"highway": "traffic_signals"}},
        {"type": "way", "id": 3, "center": {"lat": 17.4, "lon": 78.3}}]}
    s = c.slim(raw)
    assert s[0]["geometry"][1] == [78.31, 17.41] and "nodes" not in s[0]
    assert s[1]["point"] == [78.3, 17.4] and s[2]["point"] == [78.3, 17.4] and s[2]["tags"] == {}


def test_bus_stops_are_clipped_to_the_box():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("stops.txt", "stop_id,stop_name,stop_lat,stop_lon\nA,In,17.43,78.38\nB,Out,17.50,78.38\n")
    stops = c.stops_in_box(buf.getvalue())
    assert [s["id"] for s in stops] == ["A"]
