"""Roadside activity and slow traffic, from arcroad's drive-photo labels (docs/PREREG-roadside-activity.md).

Pure functions on the label records. Thresholds and definitions are fixed in the pre-registration.
"""

from __future__ import annotations

import math
import random
from datetime import datetime

from pipeline.geometry import haversine_m

SLOW = {"slow", "queue", "standstill"}
PARKED = {"one_lane_partly", "one_lane", "more"}
ROAD_TYPES = {"highway", "arterial", "street", "service_road"}
DEDUP_M, DEDUP_S = 50.0, 120
MIN_PER_ARM = 30
SUPPORT_PP = 0.10
LABEL_CHECK_N, LABEL_AGREE = 50, 0.80


def _when(dt):
    return datetime.strptime(dt, "%Y:%m:%d %H:%M:%S")


def usable(rec):
    lab = rec.get("labels") or {}
    if lab.get("image_quality") != "usable" or lab.get("view") != "windscreen":
        return False
    try:
        float(rec["lat"]), float(rec["lon"]), _when(rec["dt"])
    except (KeyError, TypeError, ValueError):
        return False
    return True


def dedupe(recs):
    """Keep the first photo of any run within DEDUP_M metres and DEDUP_S seconds of a kept one, per drive day."""
    kept = []
    for r in sorted(recs, key=lambda r: r["dt"]):
        t, lon, lat = _when(r["dt"]), float(r["lon"]), float(r["lat"])
        if any(abs((t - k[0]).total_seconds()) <= DEDUP_S and haversine_m(lon, lat, k[1], k[2]) <= DEDUP_M
               for k in kept[-50:]):
            continue
        kept.append((t, lon, lat, r))
    return [k[3] for k in kept]


def outcome(lab):
    c = lab.get("congestion")
    return True if c in SLOW else False if c == "free" else None


def exposure(lab):
    vals = (lab.get("establishment_spillover"), lab.get("parking_on_carriageway"), lab.get("vendors_on_carriageway"))
    if vals[0] == "yes" or vals[1] in PARKED or vals[2] == "yes":
        return True
    if vals[0] == "no" and vals[1] == "none" and vals[2] == "no":
        return False
    return None


def stratum(rec):
    lab = rec["labels"]
    if lab.get("road_type") not in ROAD_TYPES:
        return None
    h = _when(rec["dt"]).hour
    band = "peak" if 8 <= h < 11 or 17 <= h < 21 else "off-peak"
    return f"{lab['road_type']} · {band}"


def tabulate(recs):
    """stratum -> {"with": [slow, n], "without": [slow, n]} over usable, de-duplicated, classifiable photos."""
    out = {}
    for r in dedupe([r for r in recs if usable(r)]):
        lab, s = r["labels"], stratum(r)
        y, x = outcome(lab), exposure(lab)
        if s is None or y is None or x is None:
            continue
        cell = out.setdefault(s, {"with": [0, 0], "without": [0, 0]})["with" if x else "without"]
        cell[0] += y
        cell[1] += 1
    return out


def _var(k, n):
    p = (k + (0.5 if k in (0, n) else 0)) / (n + (1 if k in (0, n) else 0))
    return p * (1 - p) / n


def combine(table, min_n=MIN_PER_ARM):
    """Inverse-variance weighted within-stratum difference (with minus without), 95% interval, verdict."""
    used, num, den = {}, 0.0, 0.0
    for s, c in table.items():
        (k1, n1), (k0, n0) = c["with"], c["without"]
        if n1 < min_n or n0 < min_n:
            continue
        d = k1 / n1 - k0 / n0
        v = _var(k1, n1) + _var(k0, n0)
        used[s] = {"diff": round(d, 3), "with": [k1, n1], "without": [k0, n0]}
        num += d / v
        den += 1 / v
    if not den:
        return {"strata_used": used, "diff": None, "ci": None, "verdict": "not enough photos"}
    d, se = num / den, math.sqrt(1 / den)
    lo, hi = d - 1.96 * se, d + 1.96 * se
    ok = d >= SUPPORT_PP and lo > 0
    return {"strata_used": used, "diff": round(d, 3), "ci": [round(lo, 3), round(hi, 3)],
            "verdict": "supported" if ok else "not supported"}


def label_check_sample(recs, seed, n=LABEL_CHECK_N):
    pool = [r["file"] for r in dedupe([r for r in recs if usable(r)])]
    return sorted(random.Random(seed).sample(pool, min(n, len(pool))))


def label_agreement(model, person, fields=("congestion", "establishment_spillover", "parking_on_carriageway",
                                           "vendors_on_carriageway")):
    """model, person: {file: labels}. Share of photos where each field agrees; a field passes at LABEL_AGREE."""
    files = [f for f in person if f in model]
    out = {}
    for fld in fields:
        agree = sum((model[f].get(fld) == person[f].get(fld)) for f in files)
        share = agree / len(files) if files else None
        out[fld] = {"agree": agree, "n": len(files), "share": share,
                    "passes": share is not None and share >= LABEL_AGREE}
    return out
