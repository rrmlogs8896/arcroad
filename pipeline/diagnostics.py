"""Diagnostics: the questions asked of a measured set before it is believed.

Everything here was a notebook cell first. It moved into the package because
notebook code cannot be versioned, diffed or tested on push, and three of the
functions below exist to stop errors that a notebook let through.

The governing rule, added 25 Oct 2026 after it was broken three times in one
day (reporting rule 5 in README.md):

    Before a test runs, state the hypothesis, the most likely competing
    explanation, and what result would distinguish them. A test that cannot
    separate the two is not run until it can.

`stratified_compare` and `data_gaps` are that rule expressed as code.
"""

import math

from pipeline.geometry import bearing_deg, haversine_m

# A route far longer than this, to cross a few metres, is more likely a hole in
# the map than a real detour. Not a certainty — a threshold for routing a point
# into the right bucket for review.
GAP_ROUTE_M = 10_000.0

# Below this separation the pair really is a road crossing rather than two
# places that merely happen to be near each other.
CROSSING_MAX_M = 25.0


def edge_km(lon: float, lat: float, bbox) -> float:
    """Straight-line distance in km to the nearest edge of the measured area.

    CAUTION, recorded because it misled us. For a rectangular bbox around a
    roughly radial city this is close to the inverse of distance-from-centre:
    measured over the Hyderabad study area the two correlate at r = -0.889, and
    every core-band point is 20 km+ from the edge by construction.

    So this value CANNOT, on its own, separate "artefact of the boundary" from
    "genuinely worse further out". Use it only inside a ring band, never across
    the whole set. The v1.0 edge test ignored that and produced a result that
    looked like a finding and meant nothing.
    """
    x0, y0, x1, y1 = bbox
    dx = min(abs(lon - x0), abs(x1 - lon)) * 111.320 * math.cos(math.radians(lat))
    dy = min(abs(lat - y0), abs(y1 - lat)) * 110.540
    return round(min(dx, dy), 2)


def km_from(lon: float, lat: float, centre) -> float:
    """Distance in km from a reference point, usually the city centre."""
    return haversine_m(centre[0], centre[1], lon, lat) / 1000.0


def band_of(km: float, inner_km: float, band_km: float) -> str:
    """Which ring a point falls in, by distance from the centre."""
    if km <= inner_km:
        return "core (inside ORR)"
    if km <= band_km:
        return "ORR band"
    return "beyond the ORR"


def sector_of(bearing: float, exits) -> str:
    """Nearest named exit by compass bearing, wrapping correctly at 360.

    `exits` is a sequence of (name, bearing). The bearings are measured from
    real interchange positions and are NOT evenly spaced — gaps run from 7 to
    29 degrees. An evenly-spaced version of this put Patancheru in the wrong
    wedge, which is why the real bearings are carried in the data.
    """
    best, best_d = None, 999.0
    for name, eb in exits:
        d = abs(((bearing - eb + 180.0) % 360.0) - 180.0)
        if d < best_d:
            best, best_d = name, d
    return best


def bearing_from(lon: float, lat: float, centre) -> float:
    """Compass bearing of a point as seen from the centre."""
    return bearing_deg(centre[0], centre[1], lon, lat)


def data_gaps(records, gap_route_m: float = GAP_ROUTE_M):
    """Every record that is a candidate hole in the map rather than a finding.

    B-07: the v1.0 export wrote a header and zero rows while 60 unreachable
    points sat in the measured set. Those points are the most valuable output
    of a run — each is a place the open map may be missing a connection, and
    correcting it improves every navigation app in the city. Losing them to a
    filter that could never match was a real loss, not a cosmetic one.

    Returns a list, each record tagged with `gap_reason`:
      unreachable  - no route was found at all
      near_limit   - the route hit the routing cap, so its true length is unknown
      long_route   - a route over gap_route_m to cross a crossing-width gap

    A record can satisfy more than one; the first matching reason is recorded.
    """
    out = []
    for r in records:
        reason = None
        if r.get("unreachable"):
            reason = "unreachable"
        elif r.get("near_limit"):
            reason = "near_limit"
        else:
            net = r.get("network_m")
            straight = r.get("straight_m")
            if (
                net is not None
                and straight is not None
                and net > gap_route_m
                and straight <= CROSSING_MAX_M
            ):
                reason = "long_route"
        if reason:
            rec = dict(r)
            rec["gap_reason"] = reason
            out.append(rec)
    return out


def cluster_dedup(records, radius_m: float, key="detour_index"):
    """Collapse records within radius_m of one another, keeping the worst.

    v0.6 published a worst-15 table in which one junction appeared eight times
    because eight sampled points sat a few metres apart along it. A list of
    places must contain places, not samples.
    """
    kept = []
    for r in sorted(
        (x for x in records if x.get(key) is not None),
        key=lambda x: x[key],
        reverse=True,
    ):
        if all(
            haversine_m(r["lon"], r["lat"], k["lon"], k["lat"]) > radius_m for k in kept
        ):
            kept.append(r)
    return kept


def stratified_compare(records, stratum_key, value_key="detour_index", min_n=30):
    """Compare a value across strata, refusing to compare what cannot be compared.

    This is reporting rule 5 as code. A comparison between groups is only
    meaningful when each group holds enough measurements to have a stable
    middle. Groups below min_n are returned with `adequate` false and their
    statistics present but explicitly not for publication — the v0.9 sector
    table carried a median of 354.64 computed over twenty points, which is
    noise wearing the costume of a finding.

    Returns a dict of stratum -> {n, median, adequate}, sorted by median
    descending among the adequate ones.
    """
    from pipeline.metrics import _median  # local import keeps the dependency one-way

    groups = {}
    for r in records:
        v = r.get(value_key)
        if v is None:
            continue
        groups.setdefault(r.get(stratum_key), []).append(v)

    out = {}
    for name, vals in groups.items():
        out[name] = {
            "n": len(vals),
            "median": _median(vals),
            "adequate": len(vals) >= min_n,
        }
    return dict(
        sorted(
            out.items(),
            key=lambda kv: (kv[1]["adequate"], kv[1]["median"] or 0),
            reverse=True,
        )
    )


def decompose_flagged(records, di_review, gap_route_m: float = GAP_ROUTE_M):
    """What the flagged population is actually made of.

    Run on the v1.0 set this overturned a standing assumption: 79.5% of flagged
    points were separated by under 25 m, their median route was 2,455 m, and
    only 10.8% exceeded 10 km. The flagged third was mostly real severance, not
    mostly bad data, and the project had believed the opposite since v0.6.
    """
    flagged = [
        r
        for r in records
        if r.get("detour_index") is not None and r["detour_index"] >= di_review
    ]
    n = len(flagged)
    if not n:
        return {"n": 0}
    from pipeline.metrics import _median, pct

    nets = [r["network_m"] for r in flagged if r.get("network_m") is not None]
    return {
        "n": n,
        "pct_true_crossings": pct(
            sum(1 for r in flagged if (r.get("straight_m") or 1e9) <= CROSSING_MAX_M), n
        ),
        "pct_long_route": pct(
            sum(1 for r in flagged if (r.get("network_m") or 0) > gap_route_m), n
        ),
        "pct_short_route": pct(
            sum(1 for r in flagged if (r.get("network_m") or 1e9) <= 2000), n
        ),
        "median_network_m": _median(nets),
    }


# --------------------------------------------------------------------------
# B-10 / ring structure, 26 Oct 2026.
# --------------------------------------------------------------------------

def outside_declared_area(records, bbox):
    """Records that fall outside the area the project SAYS it measured.

    B-10. The v1.0 set of 12,645 points ran from 16.8495 to 17.9681 N and
    77.8484 to 79.0715 E — 1,549 points (12.2%) outside the HMDA box the
    project declared, the furthest 85 km from the centre. Their median detour
    index was 44.83 against 25.67 inside.

    This did NOT inflate the headline. It diluted it: every stray sits in the
    "beyond the ORR" band, and the strays score LOWER than the true 26-40 km
    periphery, so including them understated the gradient. The bug is a
    truthfulness bug rather than an exaggeration bug — the project described an
    area it had not measured — but it is a bug, and it was found by checking
    rather than by assuming.
    """
    x0, y0, x1, y1 = bbox
    return [
        r for r in records
        if not (x0 <= r["lon"] <= x1 and y0 <= r["lat"] <= y1)
    ]


def ring_profile(records, centre, edges, value_key="detour_index", min_n=30):
    """Median value per concentric ring, with each ring's n and adequacy.

    `edges` is a sequence of (inner_km, outer_km, label). Rings are declared
    before the run, never fitted to the result.

    Run on the v1.0 set this showed the gradient is NOT monotonic. It peaks in
    the peri-urban fringe and falls beyond it:

        core      0-14 km   n=5521   median 18.05
        ORR      14-26 km   n=3955   median 33.76
        fringe   26-40 km   n=1045   median 57.52   <- peak
        rural    40-60 km   n=1589   median 48.10
        far        60+ km   n=475    median 47.26

    That shape is more coherent than a ramp, and it is checkable: the fringe is
    where highway-grade divided roads already exist but the local street network
    has not filled in behind them, so there is severance and nothing to absorb
    it. Further out there are fewer divided roads, so less severance. Patancheru
    and Isnapur sit at roughly 36 km, inside the peak ring.
    """
    from pipeline.metrics import _median, pct

    out = {}
    for inner, outer, label in edges:
        vals = []
        for r in records:
            v = r.get(value_key)
            if v is None:
                continue
            d = km_from(r["lon"], r["lat"], centre)
            if inner < d <= outer:
                vals.append(v)
        out[label] = {
            "n": len(vals),
            "median": _median(vals),
            "pct_severe": pct(sum(1 for v in vals if v >= 50.0), len(vals)),
            "adequate": len(vals) >= min_n,
            "inner_km": inner,
            "outer_km": outer,
        }
    return out
