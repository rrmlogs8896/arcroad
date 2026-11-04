import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "research" / "runner" / "app"))
import structures as st

# A north-south divided road: northbound on the west, southbound on the east, 24 m apart.
WEST_NB = [(17.4900, 78.31440), (17.5000, 78.31440)]
EAST_SB = [(17.5000, 78.31462), (17.4900, 78.31462)]


def test_structure_between_the_carriageways_is_in_the_median():
    assert st.in_median((17.4950, 78.31451), [WEST_NB, EAST_SB], 17.495)


def test_structure_beside_the_road_is_not():
    assert not st.in_median((17.4950, 78.31480), [WEST_NB, EAST_SB], 17.495)
    assert not st.in_median((17.4950, 78.31451), [WEST_NB], 17.495)


def test_same_direction_lanes_do_not_make_a_median():
    west_sb = list(reversed(WEST_NB))
    assert not st.in_median((17.4950, 78.31451), [west_sb, EAST_SB], 17.495)


def test_every_kind_is_counted_the_same_way():
    assert st.kind_of({"amenity": "place_of_worship", "religion": "any"}) == "place_of_worship"
    assert st.kind_of({"historic": "wayside_shrine"}) == "memorial_or_shrine"
    assert st.kind_of({"amenity": "police"}) == "police_post"
