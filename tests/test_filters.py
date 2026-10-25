from pipeline.filters import (
    strip_military, way_level, levels_compatible, oneway_dirs, is_divided_proxy,
)


def test_ordinary_road_is_untouched():
    tags = {"highway": "residential", "name": "Main Road"}
    out, stripped = strip_military(tags)
    assert stripped is False
    assert out["name"] == "Main Road"


def test_defence_landuse_strips_identity_but_keeps_access():
    out, stripped = strip_military(
        {"highway": "service", "landuse": "military", "name": "Depot Road"}
    )
    assert stripped is True
    assert "landuse" not in out and "name" not in out
    assert out["access_restricted"] == "yes"
    assert out["highway"] == "service"   # geometry survives


def test_military_value_and_operator_are_stripped():
    out, stripped = strip_military(
        {"highway": "service", "military": "barracks", "operator": "Some Unit"}
    )
    assert stripped is True
    assert "military" not in out and "operator" not in out


def test_way_level_reads_layer_bridge_and_tunnel():
    assert way_level({}) == 0
    assert way_level({"bridge": "yes"}) == 1
    assert way_level({"tunnel": "yes"}) == -1
    assert way_level({"layer": "2", "bridge": "yes"}) == 2
    assert way_level({"bridge": "no"}) == 0
    assert way_level({"layer": "not-a-number"}) == 0   # must not raise


def test_flyover_overhead_is_not_across_the_road():
    """The v0.4 bug: a flyover 15 m above was paired with the road beneath."""
    assert levels_compatible({0}, {0})
    assert not levels_compatible({0}, {1})
    assert not levels_compatible({-1}, {1})


def test_oneway_directions():
    assert oneway_dirs({"oneway": "yes"}) == (True, False)
    assert oneway_dirs({"oneway": "-1"}) == (False, True)
    assert oneway_dirs({}) == (True, True)
    assert oneway_dirs({"junction": "roundabout"}) == (True, False)


def test_divided_proxy():
    assert is_divided_proxy({"oneway": "yes"})
    assert is_divided_proxy({"dual_carriageway": "yes"})
    assert not is_divided_proxy({"highway": "residential"})
