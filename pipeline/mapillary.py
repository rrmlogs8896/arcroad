"""Mapillary coverage probe: is there street-level imagery where we need it?

Why. The Detour Index's biggest known weakness is a median opening or U-turn that
exists on the road but not in OpenStreetMap, which makes a modelled detour longer
than the real one. Mapillary imagery (CC-BY-SA 4.0, with explicit permission to
derive data for OSM) can show whether an opening is there. The plan is to use it
to CORRECT OSM UPSTREAM, never to import CC-BY-SA data into arcroad's ODbL set.
This module only measures whether imagery exists near our measured pairs.

The 25 Oct probe returned zero images even for central London: the query was
broken, not the data. Two likely causes, both guarded here: a search box larger
than the API's 0.01 square-degree limit, and the token sent the wrong way. The
documented method for entity calls is the header ``Authorization: OAuth <token>``.

Reporting rule 5, declared before the probe runs:
- Hypothesis: Hyderabad has usable imagery near our flagged pairs.
- Competing: any zero comes from a broken query, as on 25 Oct.
- Separates: the same code first queries CONTROL boxes with known dense coverage.
  If a control returns nothing, the query is broken and no Hyderabad result is
  read. Flagged and unflagged pairs are sampled equally, so "imagery exists" is
  not mistaken for "imagery exists where the detours are" (the v1.1 failure).

Thresholds, written before the run (rule 2):
- CONTROL_MIN_IMAGES: a control box must return at least this many images.
- A pair is COVERED if an image lies within NEAR_M of the pair's midpoint and was
  captured within MAX_AGE_YEARS of the probe date.
- Coverage is USEFUL for verification if at least USEFUL_SHARE of sampled
  flagged pairs are covered.

No image is downloaded or stored: only ids, positions and capture times.
"""

from __future__ import annotations

import json
import random
import time
import urllib.parse
import urllib.request

from pipeline.geometry import haversine_m

API_URL = "https://graph.mapillary.com/images"
MAX_BBOX_AREA_DEG2 = 0.01          # API limit, documented: area must be SMALLER than this
SAFE_BBOX_AREA_DEG2 = 0.009        # what we allow: a 0.1 x 0.1 box computes as 0.00999...
                                   # in floating point, so a check AT the limit lets it through
FIELDS = "id,captured_at,geometry"
LIMIT = 2000                       # API maximum, documented
# 26 Oct, live runs 1 and 2: HTTP 500 on the Amsterdam control with the API's own
# message "Please reduce the amount of data you're asking for". Run 2 lowered only
# the limit (2000, 500, 100) and failed identically, so the limit is not what the
# API counts; the AREA is. Each retry therefore shrinks the box about its centre
# AND lowers the limit. (scale of the side length, limit).
RETRY_STEPS = ((1.0, 2000), (0.5, 500), (0.25, 200), (0.1, 100))
MIN_HALF_DEG = 0.0005              # never shrink below ~55 m half-width: the 50 m
                                   # coverage test needs the whole 50 m circle in the box

CONTROL_MIN_IMAGES = 20
NEAR_M = 50.0
MAX_AGE_YEARS = 5.0
USEFUL_SHARE = 0.25
PAIR_HALF_DEG = 0.0008             # ~90 m each way: covers the 50 m test with margin,
                                   # and keeps each request light (26 Oct HTTP 500)

# Control boxes: places with dense, long-standing Mapillary coverage. Kept small
# because dense areas are exactly where the API refuses large requests.
CONTROLS = {
    "amsterdam_centre": (4.890, 52.371, 4.894, 52.375),    # ~0.004 deg: dense even when small
    "london_trafalgar": (-0.130, 51.506, -0.126, 51.510),
}

# The project's primary verification target and the core-city reference.
FIXED_TARGETS = {
    "isnapur_target_17.5274_78.2685": (78.2635, 17.5224, 78.2735, 17.5324),
    "charminar_core": (78.4817, 17.3566, 78.4917, 17.3666),
}


class ProbeError(RuntimeError):
    pass


def bbox_area(bbox) -> float:
    x0, y0, x1, y1 = bbox
    return (x1 - x0) * (y1 - y0)


def check_bbox(bbox) -> None:
    """Refuse a box the API would reject or silently mis-serve."""
    x0, y0, x1, y1 = bbox
    if not (x0 < x1 and y0 < y1):
        raise ProbeError(f"bbox must be minLon, minLat, maxLon, maxLat: {bbox}")
    if bbox_area(bbox) > SAFE_BBOX_AREA_DEG2:
        raise ProbeError(f"bbox area {bbox_area(bbox):.6f} deg² exceeds the safe limit "
                         f"{SAFE_BBOX_AREA_DEG2} (API limit: under {MAX_BBOX_AREA_DEG2})")


def bbox_around(lon, lat, half_deg=PAIR_HALF_DEG):
    return (lon - half_deg, lat - half_deg, lon + half_deg, lat + half_deg)


def build_request(bbox, token, fields=FIELDS, limit=LIMIT):
    """(url, headers). The token goes in the header, never in the URL."""
    check_bbox(bbox)
    if not token:
        raise ProbeError("no Mapillary token")
    query = urllib.parse.urlencode({
        "bbox": ",".join(f"{v:.6f}" for v in bbox),
        "fields": fields,
        "limit": int(limit),
    })
    return f"{API_URL}?{query}", {"Authorization": f"OAuth {token}"}


def parse_images(payload) -> list[dict]:
    """Image records from an API response: id, lon, lat, captured_at (ms)."""
    if isinstance(payload, dict) and "error" in payload:
        raise ProbeError(f"API error: {payload['error']}")
    out = []
    for item in (payload or {}).get("data", []):
        geom = item.get("geometry") or {}
        coords = geom.get("coordinates") or [None, None]
        if coords[0] is None:
            continue
        out.append({"id": str(item.get("id")), "lon": float(coords[0]), "lat": float(coords[1]),
                    "captured_at": item.get("captured_at")})
    return out


def shrink(bbox, scale, min_half_deg=0.0):
    """The box scaled about its centre, never below ``min_half_deg`` half-width."""
    x0, y0, x1, y1 = bbox
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    hx = max((x1 - x0) / 2 * scale, min(min_half_deg, (x1 - x0) / 2))
    hy = max((y1 - y0) / 2 * scale, min(min_half_deg, (y1 - y0) / 2))
    return (cx - hx, cy - hy, cx + hx, cy + hy)


def fetch_images(bbox, token, opener=None, timeout=30, steps=RETRY_STEPS,
                 min_half_deg=MIN_HALF_DEG, pause=1.0):
    """Images in ``bbox``. On a server error (5xx) retry with a smaller box and limit;
    a client error (4xx: bad token, bad box) is raised at once with the API's own
    message. A failure is never returned as an empty list. ``opener`` is injectable
    so tests never touch the network."""
    import urllib.error
    opener = opener or urllib.request.urlopen
    errors, tried = [], set()
    for scale, limit in steps:
        box = shrink(bbox, scale, min_half_deg)
        key = (tuple(round(v, 7) for v in box), limit)
        if key in tried:
            continue
        tried.add(key)
        url, headers = build_request(box, token, limit=limit)
        req = urllib.request.Request(url, headers=headers)
        try:
            with opener(req, timeout=timeout) as resp:
                return parse_images(json.loads(resp.read().decode("utf-8")))
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8", "replace")[:200]
            except Exception:
                pass
            side = box[2] - box[0]
            errors.append(f"side={side:.4f} deg, limit={limit}: HTTP {e.code} {body}".strip())
            if e.code < 500:
                raise ProbeError(f"Mapillary refused the request: {errors[-1]}") from e
            if pause:
                time.sleep(pause)
    raise ProbeError("Mapillary returned a server error at every box size and limit tried. "
                     "Read its message below before concluding anything: "
                     + " | ".join(errors))


def nearest(images, lon, lat, now_ms=None, max_age_years=MAX_AGE_YEARS):
    """(distance_m, age_years) of the nearest image, or (None, None) if there is none.
    Images older than max_age_years are ignored."""
    now_ms = now_ms if now_ms is not None else time.time() * 1000
    best = (None, None)
    for im in images:
        age = None
        if im.get("captured_at") is not None:
            age = (now_ms - float(im["captured_at"])) / (365.25 * 86400 * 1000)
            if age > max_age_years:
                continue
        d = haversine_m(lon, lat, im["lon"], im["lat"])
        if best[0] is None or d < best[0]:
            best = (d, age)
    return best


def sample_pairs(records, n_per_group=100, seed=26, flag_key="flagged_high"):
    """Equal random samples of flagged and unflagged routed pairs (rule 5)."""
    def is_flag(r):
        v = r.get(flag_key)
        return v is True or str(v) == "True"
    routed = [r for r in records if r.get("network_m") not in (None, "")]
    flagged = [r for r in routed if is_flag(r)]
    unflagged = [r for r in routed if not is_flag(r)]
    rng = random.Random(seed)
    pick = lambda xs: rng.sample(xs, min(n_per_group, len(xs)))  # noqa: E731
    return pick(flagged), pick(unflagged)


def midpoint(r):
    return ((float(r["a_lon"]) + float(r["b_lon"])) / 2, (float(r["a_lat"]) + float(r["b_lat"])) / 2)


def coverage(pairs, fetch, now_ms=None, near_m=NEAR_M):
    """For each pair: nearest recent image to its midpoint. ``fetch(bbox)`` -> images."""
    rows = []
    for r in pairs:
        lon, lat = midpoint(r)
        imgs = fetch(bbox_around(lon, lat))
        d, age = nearest(imgs, lon, lat, now_ms=now_ms)
        rows.append({"a_node_id": r.get("a_node_id"), "b_node_id": r.get("b_node_id"),
                     "mid_lon": round(lon, 6), "mid_lat": round(lat, 6),
                     "images_in_box": len(imgs), "nearest_m": None if d is None else round(d, 1),
                     "nearest_age_years": None if age is None else round(age, 2),
                     "covered": d is not None and d <= near_m})
    return rows


def share_covered(rows) -> float:
    return sum(r["covered"] for r in rows) / len(rows) if rows else 0.0


def verdict(control_counts, flagged_share, unflagged_share):
    """The pre-registered reading of the probe. Returns (status, sentence)."""
    dead = [k for k, n in control_counts.items() if n < CONTROL_MIN_IMAGES]
    if dead:
        return ("QUERY_BROKEN", f"control box(es) {dead} returned fewer than "
                f"{CONTROL_MIN_IMAGES} images; no Hyderabad result may be read.")
    useful = flagged_share >= USEFUL_SHARE
    gap = flagged_share - unflagged_share
    return ("USEFUL" if useful else "NOT_USEFUL",
            f"{flagged_share:.0%} of flagged and {unflagged_share:.0%} of unflagged pairs have an "
            f"image within {NEAR_M:.0f} m taken in the last {MAX_AGE_YEARS:.0f} years "
            f"(threshold {USEFUL_SHARE:.0%}; flagged minus unflagged {gap:+.0%}).")
