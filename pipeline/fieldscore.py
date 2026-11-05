"""Field-day results: driven passes -> per place, per direction verdict, evidence level and triangulation.

Inputs are public-safe pass summaries (no track coordinates): for each place and direction,
the driven metres, seconds, the largest sampling gap and how many usable geotagged photos were
taken at the place during the pass. The raw tracks and photos stay private (AGENTS.md).

Rules, fixed before scoring (1 Nov 2026, from the field-day review):
  - A pass shorter than the straight line between A and B is physically impossible as a
    crossing: it means one carriageway passed near both points. It is rejected (B-15 class).
  - The verdict compares the drive with the model (groundtruth.verdict, unchanged thresholds).
  - The evidence level comes from evidence.grade with the drive as own_drive evidence.
  - Triangulation kinds (docs/ENGINE.md): S = a timed drive; P = at least one usable photo
    (edge score >= PHOTO_USABLE) within 150 m of the place during the pass; R = another pass at the
    same place in the same direction on another day, or at least REPEAT_MIN_S apart on the same day.
    Amended 5 Nov 2026 (docs/PREREG-repeat-rule.md): until then R also counted the opposite
    direction, which is a different route, so it over-stated a single measurement.
    The model (M) is what is tested, never evidence for itself.
    1 kind = candidate, 2 = corroborated, 3+ with P or O = triangulated.
"""

from __future__ import annotations

from datetime import date

from pipeline.evidence import grade
from pipeline.groundtruth import MAX_SAMPLE_GAP_S, verdict

PHOTO_USABLE = 500.0      # edge-variance score; set on 1 Nov after viewing 12 photos (exploratory)
REPEAT_MIN_S = 1800       # two passes count as a repeat only if 30+ minutes apart (ENGINE rule 2)


def score_pass(p: dict, model: dict, today: date) -> dict:
    """p: {id, dir ('ab'|'ba'), driven_m, seconds, max_gap_s, date, start_s, photos_usable}.
    model: {id: {'straight': m, 'ab': m|None, 'ba': m|None}}."""
    m = model.get(p["id"]) or {}
    straight, network = m.get("straight"), m.get(p["dir"])
    row = {k: p.get(k) for k in ("id", "dir", "driven_m", "seconds", "date", "photos_usable")}
    row.update({"straight_m": straight, "model_m": network})
    if straight is not None and p["driven_m"] < straight:
        row.update(verdict="REJECTED", reason="driven shorter than the straight line: not a crossing")
    elif p.get("max_gap_s") is None or p["max_gap_s"] > MAX_SAMPLE_GAP_S:
        row.update(verdict="POOR_TRACK", reason="gaps in the recording")
    elif network is None:
        row.update(verdict="NO_MODEL", reason="the model has no route in this direction")
    else:
        row.update(verdict=verdict(p["driven_m"], network), reason="")
    ev = []
    if row["verdict"] in ("MATCH", "SHORTER"):
        ev.append({"source": "own_drive", "verdict": row["verdict"], "observed": p["date"], "driven_m": p["driven_m"]})
    g = grade(ev, {}, today)
    row.update(level=g["level"], label=g["label"])
    return row


def triangulate(rows: list[dict], passes: list[dict]) -> None:
    """Adds kinds and tri_level to each accepted row (in place)."""
    by_place = {}
    for r, p in zip(rows, passes, strict=True):
        if r["verdict"] not in ("REJECTED", "POOR_TRACK"):
            by_place.setdefault((p["id"], p["dir"]), []).append(p)
    for r, p in zip(rows, passes, strict=True):
        if r["verdict"] in ("REJECTED", "POOR_TRACK"):
            r.update(kinds="", tri_level="none")
            continue
        kinds = ["S"]
        if (p.get("photos_usable") or 0) > 0:
            kinds.append("P")
        others = [q for q in by_place.get((p["id"], p["dir"]), []) if q is not p]
        if any(q["date"] != p["date"] or abs(q["start_s"] - p["start_s"]) >= REPEAT_MIN_S for q in others):
            kinds.append("R")
        n = len(kinds)
        r["kinds"] = "+".join(kinds)
        r["tri_level"] = "triangulated" if n >= 3 and "P" in kinds else "corroborated" if n == 2 else "candidate"


def score(passes: list[dict], model: dict, today: date) -> list[dict]:
    rows = [score_pass(p, model, today) for p in passes]
    triangulate(rows, passes)
    return rows
