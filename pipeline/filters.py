"""Ingest filters: what HMA refuses to record, and what counts as 'across the road'.

The military stripper implements HMA Doc 01 section 2.2 and is enforced as a
test, not left to memory. The level logic implements fix F-1: a flyover
overhead is never adjacent to the road beneath it.
"""

MILITARY_KEYS = {"military", "military_service"}
MILITARY_LANDUSE = {"military"}
MILITARY_VALUES = {
    "danger_area",
    "barracks",
    "naval_base",
    "airfield",
    "training_area",
}

# Tags dropped alongside a defence attribute, because they identify the site.
IDENTIFYING_KEYS = ("landuse", "name", "operator", "description")


def strip_military(tags: dict):
    """Remove defence attributes, keeping the geometry as an access restriction.

    HMA never associates a location with a defence attribute. The road's
    existence and its restricted access are legitimate inputs to a detour
    calculation; the identity of the installation is not recorded at all.

    Returns (clean_tags, was_stripped).
    """
    hit = (
        any(k in MILITARY_KEYS for k in tags)
        or tags.get("landuse") in MILITARY_LANDUSE
        or tags.get("military") in MILITARY_VALUES
    )
    if not hit:
        return tags, False
    clean = {
        k: v
        for k, v in tags.items()
        if k not in MILITARY_KEYS and k not in IDENTIFYING_KEYS
    }
    clean["access_restricted"] = "yes"
    return clean, True


def way_level(tags: dict) -> int:
    """The vertical level a way occupies.

    An explicit layer tag wins. Otherwise a bridge is above the surface and a
    tunnel below it.
    """
    raw = tags.get("layer")
    if raw is not None:
        try:
            return int(float(raw))
        except (TypeError, ValueError):
            pass
    if tags.get("bridge") not in (None, "no"):
        return 1
    if tags.get("tunnel") not in (None, "no"):
        return -1
    return 0


def levels_compatible(levels_a, levels_b) -> bool:
    """Two points can only be 'across the road' if they share a level."""
    return bool(set(levels_a) & set(levels_b))


def oneway_dirs(tags: dict):
    """(forward_allowed, backward_allowed) for travel along a way."""
    ow = tags.get("oneway")
    if ow in ("yes", "true", "1"):
        return True, False
    if ow == "-1":
        return False, True
    if tags.get("junction") == "roundabout" and ow is None:
        return True, False
    return True, True


def is_divided_proxy(tags: dict) -> bool:
    """OSM rarely carries divider= directly.

    A median-divided arterial is almost always modelled as two oneway
    carriageways, sometimes with dual_carriageway=yes. This over-counts
    genuine one-way streets in old city cores — a known limitation.
    """
    return tags.get("dual_carriageway") == "yes" or tags.get("oneway") in (
        "yes",
        "true",
        "1",
        "-1",
    )
