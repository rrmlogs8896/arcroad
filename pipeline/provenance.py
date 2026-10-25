"""The schema a measured point must carry to be re-checkable, and its validator.

B-09, found 26 Oct 2026. The v1.0 export (`di_v10_points_2026-10-25.csv`,
12,645 rows) recorded ONE endpoint per measurement:

    lat, lon, straight_m, network_m, detour_index, ...

The pairing step found two nodes on opposing carriageways, routed between them,
and then discarded the second node. The consequence is that **no measurement in
that file can be re-routed by anyone, including us.** An independent router
cannot check it, a reader cannot reproduce it, and a correction to the map
cannot be tied back to it. That breaks reporting rule 1 outright, and it was
only noticed when a validation sweep against a second routing engine was
attempted and found it had nothing to route.

This module does not rewrite the pairing. It defines the schema that pairing
must emit and gives CI a validator, so a run missing the second endpoint fails
on export instead of three weeks later.
"""

from __future__ import annotations

# Every one of these must be present and non-null on an exported measurement.
REQUIRED_FIELDS = (
    "a_lat",        # endpoint A, the side the resident is on
    "a_lon",
    "b_lat",        # endpoint B, the side they are trying to reach
    "b_lon",
    "straight_m",   # haversine A->B
    "network_m",    # routed A->B, or null WITH a reason
    "detour_index",
)

# Present where the source graph can supply them. Absence is recorded, not
# silently tolerated: the NH-65 pre-works baseline is worthless without them,
# because "the road as it was in December" has to mean a specific OSM version.
PROVENANCE_FIELDS = (
    "a_node_id",
    "b_node_id",
    "osm_way_ids",
    "osm_extract_date",
    "commit_sha",
)

# When network_m is null, one of these must say why. "No route" is a finding
# about the map; a blank cell is a finding about us.
VALID_NULL_REASONS = ("unreachable", "near_limit", "different_component", "no_bearing")


def validate_point_record(rec) -> list[str]:
    """Return a list of problems with one measured record. Empty means usable."""
    problems = []
    for f in REQUIRED_FIELDS:
        if f not in rec:
            problems.append(f"missing field: {f}")
    if problems:
        return problems

    if rec.get("network_m") is None and not rec.get("null_reason"):
        problems.append("network_m is null with no null_reason")
    if rec.get("null_reason") and rec["null_reason"] not in VALID_NULL_REASONS:
        problems.append(f"null_reason not recognised: {rec['null_reason']}")

    for f in ("a_lat", "a_lon", "b_lat", "b_lon"):
        if rec.get(f) is None:
            problems.append(f"{f} is null — the measurement cannot be re-routed")

    if rec.get("a_lat") == rec.get("b_lat") and rec.get("a_lon") == rec.get("b_lon"):
        problems.append("both endpoints identical — nothing was measured")

    return problems


def validate_export(records, max_report=20):
    """Validate a whole export. Returns (n_bad, sample_of_problems).

    Intended for CI and for the end of any run that writes a point file. A run
    that cannot pass this does not get to produce a published figure.
    """
    bad, report = 0, []
    for i, rec in enumerate(records):
        probs = validate_point_record(rec)
        if probs:
            bad += 1
            if len(report) < max_report:
                report.append((i, probs))
    return bad, report
