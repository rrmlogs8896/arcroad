"""Evidence levels: how sure arcroad is about one place, in one direction of travel.

Every modelled detour is graded on its own, per direction, from the evidence that
exists for it. The grade decides what the website may say. It is written here,
before the 1 Nov 2026 v04 results were read, and is never tuned to make a result
look better (reporting rule 2).

Levels
  1  Driven by arcroad    arcroad's own timed GPS drive passed the ground-truth gate.
                          If the drive was much shorter than the model, the map was
                          wrong: the driven distance is published as a correction.
  2  Confirmed by others  at least one independent timed drive (street-photo runs)
                          from a source that proved itself on the controls, recent,
                          and nothing disputes it.
  3  Modelled             only the map's own calculation, or weak evidence. Shown
                          as a candidate, never as a finding.
  4  Disputed             a usable drive came out much shorter, another source shows
                          a link the map lacks, or a sign says U-turns are allowed
                          there. The model's number is withheld until it is checked.

How a source earns trust (the part that is measured, not assumed)
  Each drive source is scored on control pairs, ordinary two-way roads where no
  detour is expected. Its trust is the Wilson lower bound (95%) of how often it
  reproduced the expected result. A source counts only with at least
  MIN_CONTROLS scored controls and a lower bound of at least MIN_TRUST. arcroad's
  own drives are the reference and always count.

Freshness
  Roads change. Evidence observed before the map's last edit at that place, or more
  than MAX_AGE_DAYS before today, cannot lift a place above level 3, and cannot
  dispute it either; it is listed as history.

Independence
  Several photo runs by the same contributor on the same day count once.
"""

from __future__ import annotations

import math
from datetime import date

MIN_CONTROLS = 3
MIN_TRUST = 0.5
MAX_AGE_DAYS = 730
Z95 = 1.96

DRIVE_SOURCES = {"own_drive", "mapillary", "kartaview", "osm_traces"}
DISPUTE_ONLY = {"ms_imagery": "IMAGERY_SHOWS_LINK", "overture": "OTHER_MAP_SHOWS_LINK"}

LABELS = {1: "Driven by arcroad", 2: "Confirmed by others' drives", 3: "Modelled", 4: "Disputed"}


def wilson_lower(successes: int, n: int, z: float = Z95) -> float:
    """Lower bound of the Wilson score interval: a cautious estimate of a hit rate."""
    if n <= 0:
        return 0.0
    p = successes / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (centre - margin) / denom


def source_trust(controls_scored: int, reproduced: int) -> dict:
    lb = wilson_lower(reproduced, controls_scored)
    return {"controls_scored": controls_scored, "reproduced": reproduced, "trust": round(lb, 3),
            "usable": controls_scored >= MIN_CONTROLS and lb >= MIN_TRUST}


def _fresh(item: dict, map_last_edit: date | None, today: date) -> bool:
    seen = item.get("observed")
    if seen is None:
        return False
    if isinstance(seen, str):
        seen = date.fromisoformat(seen[:10])
    if map_last_edit is not None and seen < map_last_edit:
        return False
    return (today - seen).days <= MAX_AGE_DAYS


def grade(evidence: list[dict], quality: dict, today: date, map_last_edit: date | None = None) -> dict:
    """Grade one place in one direction.

    evidence: items {source, verdict, observed (ISO date), contributor (optional),
              driven_m (optional)}.
    quality:  {source: {"controls_scored": n, "reproduced": k}} measured on controls.
    Returns {level, label, reasons, history, corrected_m}.
    """
    reasons, history = [], []
    usable = {s: (s == "own_drive") or source_trust(**q)["usable"] for s, q in quality.items()}
    usable.setdefault("own_drive", True)

    own = [e for e in evidence if e["source"] == "own_drive" and e.get("verdict") in ("MATCH", "SHORTER")]
    if own:
        last = sorted(own, key=lambda e: e.get("observed", ""))[-1]
        if last["verdict"] == "MATCH":
            return {"level": 1, "label": LABELS[1], "reasons": ["arcroad drove it; the map's distance held"],
                    "history": history, "corrected_m": None}
        return {"level": 1, "label": LABELS[1], "reasons": ["arcroad drove it; the real trip was much shorter, so the map is out of date here"],
                "history": history, "corrected_m": last.get("driven_m")}

    fresh, seen_runs = [], set()
    for e in evidence:
        if not _fresh(e, map_last_edit, today):
            history.append(e)
            continue
        if e["source"] in DRIVE_SOURCES and not usable.get(e["source"], False):
            history.append(e)
            continue
        key = (e["source"], e.get("contributor"), str(e.get("observed", ""))[:10])
        if e["source"] in DRIVE_SOURCES and e.get("contributor") and key in seen_runs:
            continue  # same contributor, same day: counted once
        seen_runs.add(key)
        fresh.append(e)

    drives = [e for e in fresh if e["source"] in DRIVE_SOURCES]
    match = [e for e in drives if e.get("verdict") == "MATCH"]
    shorter = [e for e in drives if e.get("verdict") == "SHORTER"]
    disputes = [e for e in fresh if DISPUTE_ONLY.get(e["source"]) == e.get("verdict")]
    u_turn_sign = [e for e in fresh if e.get("verdict") == "U_TURN_SIGN"]
    no_u_turn_sign = [e for e in fresh if e.get("verdict") == "NO_U_TURN_SIGN"]

    if shorter:
        reasons.append(f"{len(shorter)} recent drive(s) by others were much shorter than the map")
    if disputes:
        reasons.append("another map or aerial imagery shows a link the map lacks")
    if u_turn_sign:
        reasons.append("a sign photographed here allows U-turns")
    if shorter or disputes or u_turn_sign:
        if match:
            reasons.append(f"{len(match)} other drive(s) agreed with the map, so the evidence conflicts")
        return {"level": 4, "label": LABELS[4], "reasons": reasons, "history": history, "corrected_m": None}

    if match:
        reasons.append(f"{len(match)} recent independent drive(s) matched the map's distance")
        if no_u_turn_sign:
            reasons.append("a 'no U-turn' sign was photographed here")
        return {"level": 2, "label": LABELS[2], "reasons": reasons, "history": history, "corrected_m": None}

    reasons.append("only the map's own calculation so far")
    if no_u_turn_sign:
        reasons.append("a 'no U-turn' sign was photographed here, which fits the detour")
    return {"level": 3, "label": LABELS[3], "reasons": reasons, "history": history, "corrected_m": None}
