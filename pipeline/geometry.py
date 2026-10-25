"""Geometric primitives for the Hyderabad Mobility Atlas.

Pure maths, no OSM dependency, so every function here can be tested against
cases whose answers are known independently.
"""

import math

EARTH_RADIUS_M = 6371008.8


def haversine_m(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Great-circle distance in metres between two lon/lat points."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = (
        math.sin((p2 - p1) / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    )
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def bearing_deg(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Compass bearing from point 1 to point 2, in degrees from 0 to 360."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0


def angle_between(b1: float, b2: float) -> float:
    """Smallest absolute difference between two bearings, 0 to 180."""
    d = abs(b1 - b2) % 360.0
    return d if d <= 180.0 else 360.0 - d


def is_antiparallel(b1: float, b2: float, tol_deg: float) -> bool:
    """True when two headings are opposite within tol_deg.

    Two carriageways of one divided road run antiparallel. Requiring this
    stops unrelated or crossing roads being paired as if they were one road
    — the error that inflated the v0.4 Detour Index.
    """
    return abs(angle_between(b1, b2) - 180.0) <= tol_deg


def zone_of(lon: float, lat: float, zones: dict) -> list:
    """Every zone whose bounding box contains this point.

    Zones overlap by design: the pilot corridor sits inside the study area.
    """
    return [
        name
        for name, (x0, y0, x1, y1) in zones.items()
        if x0 <= lon <= x1 and y0 <= lat <= y1
    ]
