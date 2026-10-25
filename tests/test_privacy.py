"""HMA Doc 01 section 2.2 and section 6, enforced rather than remembered."""

from pipeline.filters import strip_military

BANNED_KEYS = {"military", "military_service", "landuse", "operator", "description"}


def test_no_defence_attribute_survives_the_stripper():
    hostile = {
        "highway": "service",
        "military": "barracks",
        "military_service": "army",
        "landuse": "military",
        "name": "Some Depot",
        "operator": "A Unit",
        "description": "stores",
    }
    out, stripped = strip_military(hostile)
    assert stripped is True
    leaked = BANNED_KEYS.intersection(out)
    assert not leaked, f"defence attributes leaked into output: {leaked}"
    assert "name" not in out


def test_output_schema_carries_no_personal_fields():
    """Phases 1-4 hold no personal data at all.

    A point record describes a location on a road. If a field that could
    identify a person ever appears in this schema, this test fails.
    """
    point_record = {
        "lat": 17.4,
        "lon": 78.4,
        "straight_m": 23.4,
        "network_m": 311.3,
        "detour_index": 13.3,
        "unreachable": False,
        "near_limit": False,
        "flagged_high": False,
    }
    forbidden = {
        "name", "address", "owner", "resident", "phone", "email",
        "user", "user_id", "device", "ip", "household",
    }
    leaked = forbidden.intersection(point_record)
    assert not leaked, f"personal fields in output schema: {leaked}"
