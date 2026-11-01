"""Field kit: turn one day of driving (GPX + Sensor Logger + photos) into per-spot scene specs.

The scene spec is the "model engine" for everything built from a drive: the ground-truth
score, the immersive detour ride (driver's-eye replay), the pothole record and photo-based
checks of the road. One spec per spot, all derived from the same drive, so every visual
can be traced back to measured data.

Rule 5, written before any field day is ingested (1 Nov 2026):

  Hypothesis   A jolt in the phone's vertical acceleration above the threshold, at speed,
               marks a road defect (pothole, broken patch) or a speed breaker.
  Competing    Phone handling: picking up, dropping or re-seating a loose phone makes the
  explanation  same spike, and so do expansion joints and rail crossings.
  What         A real defect repeats at the same place on a second pass (or is visible in a
  separates    photo); handling does not repeat and comes with large rotation on the
  them         gyroscope. Until a second pass or a photo confirms it, a jolt is a candidate.

Thresholds are fixed here and never tuned after seeing results.

Privacy: outputs contain track coordinates and photo positions, so they are written only
to the private field folder (field/<date>/), which is git-ignored. Nothing here is published
directly; public output is derived later with faces and plates blurred and metadata stripped.
"""

from __future__ import annotations

import csv
import io
import json
import math
import os
import subprocess
import zipfile
from bisect import bisect_left
from datetime import UTC, datetime
from itertools import pairwise

from pipeline.geometry import haversine_m
from pipeline.groundtruth import find_pass, parse_gpx, path_length_m


def _dist(lat1, lon1, lat2, lon2):
    """Metres between two lat/lon points (geometry.haversine_m takes lon first)."""
    return haversine_m(lon1, lat1, lon2, lat2)

# --- pre-registered thresholds (do not tune after results) ---
PHOTO_SPOT_RADIUS_M = 150.0   # a photo belongs to a spot if taken within this of side A or B
JOLT_MIN_MS2 = 3.0            # vertical acceleration spike, m/s^2, after gravity is removed
JOLT_SIGMA = 4.0              # and at least this many robust sigmas above the local noise
JOLT_MIN_SPEED_KMH = 8.0      # below this, spikes are mostly handling, not the road
JOLT_MERGE_S = 1.0            # spikes closer than this are one event
HANDLING_GYRO_RADS = 2.5      # big rotation at the same moment = phone handling, not road
STOP_SPEED_KMH = 3.0          # a wait (queue, U-turn gap) = slower than this
STOP_MIN_S = 15.0             # for at least this long


# ---------------------------------------------------------------- readers
def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def read_sensor_logger(path: str) -> dict:
    """Sensor Logger export (zip or folder) -> {'location': [...], 'accel': [...], 'gravity': [...], 'gyro': [...]}.

    Rows are (unix_seconds, ...). Sensor Logger writes `time` in nanoseconds since epoch.
    Unknown or missing files are simply absent; nothing is guessed.
    """
    files = {}
    if os.path.isdir(path):
        for name in os.listdir(path):
            if name.lower().endswith(".csv"):
                with open(os.path.join(path, name), newline="", encoding="utf-8") as fh:
                    files[name.lower()] = fh.read()
    else:
        with zipfile.ZipFile(path) as z:
            for name in z.namelist():
                if name.lower().endswith(".csv"):
                    files[os.path.basename(name).lower()] = z.read(name).decode("utf-8", "replace")

    def rows(name):
        text = files.get(name)
        return list(csv.DictReader(io.StringIO(text))) if text else []

    def t(r):
        v = _f(r.get("time"))
        return v / 1e9 if v and v > 1e12 else v

    out = {}
    loc = rows("location.csv")
    if loc:
        out["location"] = [(t(r), _f(r.get("latitude")), _f(r.get("longitude")), _f(r.get("speed")),
                            _f(r.get("bearing")), _f(r.get("horizontalAccuracy")), _f(r.get("altitude"))) for r in loc]
    for key, name in (("accel", "accelerometer.csv"), ("gravity", "gravity.csv"), ("gyro", "gyroscope.csv")):
        rs = rows(name)
        if rs:
            out[key] = [(t(r), _f(r.get("x")), _f(r.get("y")), _f(r.get("z"))) for r in rs]
    return out


def read_photo_meta(paths: list[str]) -> list[dict]:
    """EXIF for each photo via exiftool (handles HEIC and JPEG). Missing fields stay None."""
    if not paths:
        return []
    cmd = ["exiftool", "-n", "-json", "-DateTimeOriginal", "-OffsetTimeOriginal", "-GPSLatitude", "-GPSLongitude",
           "-GPSAltitude", "-GPSImgDirection", "-GPSSpeed", "-Model", "-LensModel", "-ImageWidth", "-ImageHeight", *paths]
    raw = json.loads(subprocess.run(cmd, capture_output=True, text=True, check=True).stdout or "[]")
    out = []
    for r in raw:
        ts = None
        if r.get("DateTimeOriginal"):
            s = str(r["DateTimeOriginal"]).replace(":", "-", 2) + (r.get("OffsetTimeOriginal") or "+05:30")
            try:
                ts = datetime.fromisoformat(s).timestamp()
            except ValueError:
                ts = None
        out.append({"file": os.path.basename(r.get("SourceFile", "")), "t": ts, "lat": _f(r.get("GPSLatitude")),
                    "lon": _f(r.get("GPSLongitude")), "alt": _f(r.get("GPSAltitude")), "heading": _f(r.get("GPSImgDirection")),
                    "model": r.get("Model"), "lens": r.get("LensModel"), "w": r.get("ImageWidth"), "h": r.get("ImageHeight")})
    return out


# ---------------------------------------------------------------- analysis
def _interp_pos(track, ts):
    times = [p[0] for p in track]
    i = bisect_left(times, ts)
    if i <= 0:
        return track[0][1], track[0][2]
    if i >= len(track):
        return track[-1][1], track[-1][2]
    (t0, a0, o0), (t1, a1, o1) = track[i - 1][:3], track[i][:3]
    f = 0 if t1 == t0 else (ts - t0) / (t1 - t0)
    return a0 + (a1 - a0) * f, o0 + (o1 - o0) * f


def speeds_kmh(track) -> list[float]:
    out = [0.0]
    for p, q in pairwise(track):
        dt = (q[0] - p[0]) if p[0] is not None and q[0] is not None else None
        out.append(_dist(p[1], p[2], q[1], q[2]) / dt * 3.6 if dt else 0.0)
    return out


def stops(track, i=0, j=None) -> list[dict]:
    """Waits (queues, U-turn gaps) inside track[i:j]."""
    j = len(track) - 1 if j is None else j
    sp, out, start = speeds_kmh(track), [], None
    for k in range(i, j + 1):
        slow = sp[k] < STOP_SPEED_KMH
        if slow and start is None:
            start = k
        if (not slow or k == j) and start is not None:
            dur = (track[k][0] or 0) - (track[start][0] or 0)
            if dur >= STOP_MIN_S:
                out.append({"t": track[start][0], "seconds": round(dur), "lat": track[start][1], "lon": track[start][2]})
            start = None
    return out


def turnaround(track, i, j, a) -> dict | None:
    """The U-turn: the point of the pass farthest (straight-line) from side A."""
    best, bk = -1.0, None
    for k in range(i, j + 1):
        d = _dist(track[k][1], track[k][2], a[1], a[0])
        if d > best:
            best, bk = d, k
    return None if bk is None else {"t": track[bk][0], "lat": track[bk][1], "lon": track[bk][2], "from_a_m": round(best)}


def _vertical(accel, gravity):
    """Linear acceleration projected on the gravity direction (phone orientation independent)."""
    if not gravity:
        return [(t, z) for t, x, y, z in accel]
    gt = [g[0] for g in gravity]
    out = []
    for t, x, y, z in accel:
        k = min(max(bisect_left(gt, t), 0), len(gravity) - 1)
        _, gx, gy, gz = gravity[k]
        n = math.sqrt(gx * gx + gy * gy + gz * gz) or 1.0
        out.append((t, (x * gx + y * gy + z * gz) / n))
    return out


def jolts(sensors: dict, track) -> list[dict]:
    """Candidate road defects. Every one is a candidate until a repeat pass or a photo confirms it."""
    acc = sensors.get("accel") or []
    if not acc or not track:
        return []
    v = _vertical(acc, sensors.get("gravity"))
    vals = sorted(abs(x) for _, x in v if x is not None)
    med = vals[len(vals) // 2]
    mad = sorted(abs(x - med) for x in vals)[len(vals) // 2] or 0.05
    thr = max(JOLT_MIN_MS2, med + JOLT_SIGMA * 1.4826 * mad)
    gyro = sensors.get("gyro") or []
    gt = [g[0] for g in gyro]
    sp, tt = speeds_kmh(track), [p[0] for p in track]
    events, last = [], -1e18
    for t, a in v:
        if a is None or abs(a) < thr or t - last < JOLT_MERGE_S:
            continue
        k = min(max(bisect_left(tt, t), 0), len(track) - 1)
        if sp[k] < JOLT_MIN_SPEED_KMH:
            continue
        handling = False
        if gyro:
            g = gyro[min(max(bisect_left(gt, t), 0), len(gyro) - 1)]
            handling = math.sqrt((g[1] or 0) ** 2 + (g[2] or 0) ** 2 + (g[3] or 0) ** 2) > HANDLING_GYRO_RADS
        lat, lon = _interp_pos(track, t)
        events.append({"t": t, "lat": lat, "lon": lon, "peak_ms2": round(abs(a), 2), "speed_kmh": round(sp[k]),
                       "status": "handling?" if handling else "candidate"})
        last = t
    return events


# ---------------------------------------------------------------- scenes
def photos_for_spot(photos, spot) -> list[dict]:
    a, b = spot["a"], spot.get("b") or spot["a"]
    out = []
    for p in photos:
        if p.get("lat") is None:
            continue
        d = min(_dist(p["lat"], p["lon"], a[1], a[0]), _dist(p["lat"], p["lon"], b[1], b[0]))
        if d <= PHOTO_SPOT_RADIUS_M:
            out.append({**p, "dist_m": round(d)})
    return sorted(out, key=lambda p: p["t"] or 0)


def scene(spot, track, photos, jolt_events, network_m=None) -> dict:
    """Everything the immersive ride, the score and the road record need for one spot."""
    a, b = tuple(spot["a"]), tuple(spot["b"])          # places.json order: [lon, lat]
    sc = {"spot": spot["id"], "a": spot["a"], "b": spot["b"],
          "straight_m": round(_dist(a[1], a[0], b[1], b[0]), 1), "network_m": network_m,
          "driven": None, "photos": photos_for_spot(photos, spot)}
    found = find_pass(track, (a[1], a[0]), (b[1], b[0])) if track else None  # find_pass wants (lat, lon)
    if found:
        i, j = found
        t0, t1 = track[i][0], track[j][0]
        sc["driven"] = {
            "metres": round(path_length_m(track, i, j), 1),
            "seconds": round(t1 - t0) if t0 and t1 else None,
            "turnaround": turnaround(track, i, j, a),
            "waits": stops(track, i, j),
            "path_1hz": [[round(p[0] - (t0 or 0), 1), round(p[1], 6), round(p[2], 6)] for p in track[i:j + 1]],
            "jolts": [e for e in jolt_events if t0 and t1 and t0 <= e["t"] <= t1],
        }
    return sc


def build_day(folder: str, spots: list[dict], network: dict | None = None) -> dict:
    """Ingest everything in folder (*.gpx, Sensor Logger *.zip or folder, photos) -> field/<day>/scenes/*.json."""
    network = network or {}
    names = sorted(os.listdir(folder))
    track = []
    for n in names:
        if n.lower().endswith(".gpx"):
            with open(os.path.join(folder, n), encoding="utf-8") as fh:
                track += [p for p in parse_gpx(fh.read()) if p[0] is not None]
    sensors = {}
    for n in names:
        p = os.path.join(folder, n)
        if n.lower().endswith(".zip") or (os.path.isdir(p) and any(f.lower() == "location.csv" for f in os.listdir(p))):
            for k, v in read_sensor_logger(p).items():
                sensors.setdefault(k, []).extend(v)
    if not track and sensors.get("location"):
        track = [(r[0], r[1], r[2]) for r in sensors["location"] if r[0] and r[1] is not None]
    track.sort(key=lambda p: p[0])
    pics = [os.path.join(folder, n) for n in names if n.lower().endswith((".heic", ".jpg", ".jpeg", ".png", ".dng"))]
    photos = read_photo_meta(pics)
    jl = jolts(sensors, track)
    outdir = os.path.join(folder, "scenes")
    os.makedirs(outdir, exist_ok=True)
    summary = {"made": datetime.now(UTC).isoformat(timespec="seconds"), "track_points": len(track),
               "photos": len(photos), "photos_without_gps": sum(p["lat"] is None for p in photos),
               "jolts": len(jl), "spots": []}
    for s in spots:
        if not s.get("b"):
            continue
        sc = scene(s, track, photos, jl, network.get(s["id"]))
        with open(os.path.join(outdir, f"{s['id']}.json"), "w", encoding="utf-8") as fh:
            json.dump(sc, fh, ensure_ascii=False)
        summary["spots"].append({"id": s["id"], "driven": bool(sc["driven"]), "photos": len(sc["photos"]),
                                 "metres": sc["driven"]["metres"] if sc["driven"] else None})
    with open(os.path.join(outdir, "_summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=1)
    return summary


if __name__ == "__main__":  # python -m pipeline.fieldkit <field folder> <places.json>
    import sys
    folder, places = sys.argv[1], sys.argv[2]
    with open(places, encoding="utf-8") as fh:
        sp = json.load(fh)["spots"]
    print(json.dumps(build_day(folder, sp), indent=1))
