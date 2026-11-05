"""Pre-registered job: remote corroboration (docs/PREREG-remote.md, constitution Art 4g).

For each place, gathers three independent checks that need no one on the ground:
  1. routers: tonight's routercheck — do OSRM and Valhalla both agree with the model (within 15%)?
  2. map edits: tonight's mapwatch — any road, turn-rule or signal edit within 1 km in 48 h?
  3. street photos: recent Mapillary photos within 40 m of the place, sorted by an AI model into
     "gap visible", "no gap visible" or "unclear" — sorting only, for a person to confirm.

It never upgrades a place by itself. It writes a review list; a place becomes "Corroborated
remotely" only after Rohit confirms a photo (docs/PREREG-remote.md). No image is stored: only
photo ids, dates and links. The AI is told not to describe people or vehicles.
"""
from __future__ import annotations

import json
import math
import os
import urllib.parse
import urllib.request
from datetime import UTC, datetime, timedelta

from openings import PLACES_URL, get

MAPILLARY = "https://graph.mapillary.com/images"
ANTHROPIC = "https://api.anthropic.com/v1/messages"
MODEL = "claude-haiku-5-5"
NEAR_M = 40.0
MAX_AGE_DAYS = 730
PER_PLACE = 4
NIGHT_CAP = 96          # pre-registered spending cap: at most this many photos sorted per night
PROMPT = (
    "This is a street-level photo taken on a road in India. Look only at the road layout. "
    "Is a central median (divider) visible, and is there an opening or gap in it where vehicles "
    "could cross or turn? Do not describe people, faces, vehicles or number plates. "
    'Reply with JSON only: {"median_visible": true|false, "gap": "yes"|"no"|"unclear", "why": "<at most 12 words>"}'
)


def metres(a_lat, a_lon, b_lat, b_lon):
    k = math.cos(math.radians(a_lat))
    return math.hypot((a_lon - b_lon) * 111320 * k, (a_lat - b_lat) * 110574)


def bbox_around(lat, lon, m):
    dlat = m / 110574
    dlon = m / (111320 * math.cos(math.radians(lat)))
    return lon - dlon, lat - dlat, lon + dlon, lat + dlat


def parse_label(text):
    """The model's reply -> a label dict; anything unparseable is 'unclear', never a guess."""
    try:
        s = text[text.index("{"): text.rindex("}") + 1]
        d = json.loads(s)
        gap = d.get("gap") if d.get("gap") in ("yes", "no", "unclear") else "unclear"
        return {"median_visible": bool(d.get("median_visible")), "gap": gap, "why": str(d.get("why", ""))[:120]}
    except (ValueError, TypeError):
        return {"median_visible": False, "gap": "unclear", "why": "reply not readable"}


def photos(lat, lon, token, now):
    w, s, e, n = bbox_around(lat, lon, NEAR_M)
    q = urllib.parse.urlencode({"access_token": token, "bbox": f"{w},{s},{e},{n}", "limit": 30,
                                "fields": "id,captured_at,compass_angle,thumb_1024_url,computed_geometry"})
    d = json.loads(get(MAPILLARY + "?" + q))
    out = []
    for im in d.get("data", []):
        g = (im.get("computed_geometry") or {}).get("coordinates")
        if not g or not im.get("captured_at"):
            continue
        when = datetime.fromtimestamp(im["captured_at"] / 1000, UTC)
        if now - when > timedelta(days=MAX_AGE_DAYS):
            continue
        out.append({"id": im["id"], "captured": when.date().isoformat(), "dist_m": round(metres(lat, lon, g[1], g[0]), 1),
                     "url": im.get("thumb_1024_url"), "link": f"https://www.mapillary.com/app/?pKey={im['id']}"})
    out.sort(key=lambda x: (x["dist_m"], x["captured"]))
    return out[:PER_PLACE]


def sort_photo(url, key):
    body = json.dumps({"model": MODEL, "max_tokens": 120, "messages": [{"role": "user", "content": [
        {"type": "image", "source": {"type": "url", "url": url}}, {"type": "text", "text": PROMPT}]}]}).encode()
    req = urllib.request.Request(ANTHROPIC, data=body, headers={
        "x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.loads(r.read())
    return parse_label("".join(c.get("text", "") for c in d.get("content", [])))


def router_agree(rc, sid):
    if not rc:
        return None
    rows = [r for r in rc.get("rows", []) if r["id"] == sid]
    ok = [r for r in rows if r["osrm"]["class"] == "AGREES" and r["valhalla"]["class"] == "AGREES"]
    return {"directions": len(rows), "both_agree": len(ok)}


def run(log, earlier):
    """earlier: {'routercheck': bytes|None, 'mapwatch': bytes|None} from tonight's run."""
    now = datetime.now(UTC)
    spots = json.loads(get(PLACES_URL))["spots"]
    rc = json.loads(earlier["routercheck"]) if earlier.get("routercheck") else None
    mw = json.loads(earlier["mapwatch"]) if earlier.get("mapwatch") else None
    recheck = set(mw.get("recheck", [])) if mw else None
    token, key = os.environ.get("MAPILLARY_TOKEN", ""), os.environ.get("ANTHROPIC_API_KEY", "")
    out = {"job": "remote-v1", "prereg": "docs/PREREG-remote.md", "status": "REVIEW LIST, NOT PUBLISHED",
           "started": now.isoformat(), "model": MODEL, "photos": "Mapillary (CC BY-SA 4.0)",
           "photo_source": "on" if token else "SKIPPED: no Mapillary token set",
           "ai_sorting": "on" if key else "SKIPPED: no API key set", "places": []}
    sorted_n = 0
    for s in spots:
        lat, lon = (s["a"][1] + s["b"][1]) / 2, (s["a"][0] + s["b"][0]) / 2
        row = {"id": s["id"], "routers": router_agree(rc, s["id"]),
               "map_edits_48h": None if recheck is None else s["id"] in recheck, "photos": []}
        if token:
            try:
                for ph in photos(lat, lon, token, now):
                    if key and sorted_n < NIGHT_CAP and ph["url"]:
                        try:
                            ph["ai"] = sort_photo(ph["url"], key)
                            sorted_n += 1
                        except Exception as e:  # recorded, never dropped
                            ph["ai"] = {"gap": "unclear", "why": "sorting failed: " + str(e)[:80]}
                    ph.pop("url", None)   # thumbnail links expire; keep the permanent link only
                    row["photos"].append(ph)
            except Exception as e:
                row["photo_error"] = str(e)[:200]
        r = row["routers"] or {}
        row["ready_for_review"] = bool(r.get("both_agree")) and row["map_edits_48h"] is False and any(
            p.get("ai", {}).get("gap") in ("no", "unclear") for p in row["photos"])
        row["possible_dispute"] = any(p.get("ai", {}).get("gap") == "yes" for p in row["photos"])
        out["places"].append(row)
        log(f"remote {s['id']} photos={len(row['photos'])} ready={row['ready_for_review']}")
    out["sorted_photos"] = sorted_n
    out["review_list"] = [p["id"] for p in out["places"] if p["ready_for_review"]]
    out["dispute_list"] = [p["id"] for p in out["places"] if p["possible_dispute"]]
    out["finished"] = datetime.now(UTC).isoformat()
    return json.dumps(out, indent=1).encode()
