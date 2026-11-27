"""arcroad research runner: runs the night's jobs one after another and hands each result to the Worker.

GET /start   start the queue (ignored if already running)
GET /status  {"running": bool, "done": [job, ...], "failed": {job: reason}, "log": [...]}
GET /result/<job>  the job's output (a JSON or a .tar.gz), once done
Only the Worker can reach this server; it has no public address.
"""
from __future__ import annotations

import datetime as dt
import re
import urllib.parse
import json
import shutil
import subprocess
import tarfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import adminmap
import areascan
import corridor3d
import filer
import hotspots
import mapwatch
import entryscan
import openings
import remote
import routercheck
import structures
import viability
import eyelab
import socialreach

OUT = Path("/tmp/out")
STATE = {"running": False, "done": [], "failed": {}, "log": [], "boot": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}  # boot: a new value means the container restarted
FILES = {}


def log(msg):
    STATE["log"].append(time.strftime("%H:%M:%S ") + msg)
    STATE["log"] = STATE["log"][-200:]
    print(msg, flush=True)


def job_openings():
    OUT.mkdir(exist_ok=True)
    p = OUT / "openings-guidance-v1.json"
    p.write_bytes(openings.run(log))
    return p


SNAPSHOT = Path(__file__).resolve().parent / "repo"  # tools, pipeline, data + COMMIT, copied in at deploy time


def repo():
    """The code the jobs run: the snapshot baked into the image at deploy (tools/runner_snapshot.sh), so no
    job depends on GitHub. Without a snapshot, falls back to a fresh shallow clone of the public repo."""
    if (SNAPSHOT / "COMMIT").exists():
        return SNAPSHOT
    work = Path("/tmp/arcroad")
    if not (work / ".git").exists():
        if work.exists():
            shutil.rmtree(work)
        subprocess.run(["git", "clone", "--depth", "1", "https://github.com/rrmlogs8896/arcroad.git", str(work)],
                       check=True)
    return work


def job_adminmap():
    """One-off: open administrative map of Telangana (districts, mandals, places) for a district drill-down."""
    return adminmap.run(log, OUT)


def job_corridor3d():
    """Open layers for the 3D corridor model: roads, buildings, points, ground height, bus stops."""
    return corridor3d.run(log, OUT)


def job_routercheck():
    OUT.mkdir(exist_ok=True)
    p = OUT / "routercheck-v1.json"
    p.write_bytes(routercheck.run(log))
    return p


def job_mapwatch():
    OUT.mkdir(exist_ok=True)
    p = OUT / "mapwatch-v1.json"
    p.write_bytes(mapwatch.run(log))
    return p


def job_structures():
    OUT.mkdir(exist_ok=True)
    p = OUT / "structures-v1.json"
    p.write_bytes(structures.run(log))
    return p


def job_remote():
    OUT.mkdir(exist_ok=True)
    p = OUT / "remote-v1.json"
    earlier = {k: FILES[k].read_bytes() if k in FILES else None for k in ("routercheck", "mapwatch")}
    p.write_bytes(remote.run(log, earlier))
    return p


def job_hotspots():
    OUT.mkdir(exist_ok=True)
    p = OUT / "hotspots-v1.json"
    p.write_bytes(hotspots.run(log, repo()))
    return p


def job_bengaluru():
    """Bengaluru candidate collection: the same code and config as the monthly GitHub workflow."""
    work = repo()
    out = work / "out"
    cmd = ["python", "tools/multicity_collect.py", "bengaluru", "--out", "out", "--cache", "/tmp/cache", "--detour"]
    with subprocess.Popen(cmd, cwd=work, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) as pr:
        for line in pr.stdout:
            log("bengaluru " + line.rstrip()[:200])
    if pr.returncode != 0:
        raise RuntimeError(f"collector exited {pr.returncode}")
    OUT.mkdir(exist_ok=True)
    tgz = OUT / "bengaluru-candidate.tar.gz"
    with tarfile.open(tgz, "w:gz") as t:
        t.add(out, arcname="bengaluru")
    return tgz


def job_viability():
    """Sunday, Tuesday and Thursday nights: the viability brief, inside the constitution and secret sauce."""
    OUT.mkdir(exist_ok=True)
    p = OUT / "viability-v1.json"
    rules = "\n\n".join(t for t in (filer.get("AGENT-BRIEF.md", log), filer.get("SECRET-SAUCE.md", log)) if t)
    last = viability.previous_run_day(dt.date.fromisoformat(STATE["night"])).isoformat()
    try:
        previous = json.loads(filer.get(f"nights/{last}/viability.json", log) or "{}").get("brief", "")
    except ValueError:
        previous = ""
    p.write_bytes(viability.run(log, previous, rules))
    return p


def job_socialreach():
    """One night only (17 Nov 2026): where to share 13point8 for the most reach, and each community's rules. USD 2 cap."""
    OUT.mkdir(exist_ok=True)
    p = OUT / "socialreach-v1.json"
    p.write_bytes(socialreach.run(log))
    return p


def job_eyelab():
    """Saturday nights: the 13point8 research scan (colour, speed, visual brain, return), USD 5 a month cap."""
    OUT.mkdir(exist_ok=True)
    p = OUT / "eyelab-v1.json"
    last = eyelab.previous_run_day(dt.date.fromisoformat(STATE["night"])).isoformat()
    try:
        previous = json.loads(filer.get(f"nights/{last}/eyelab.json", log) or "{}").get("brief", "")
    except ValueError:
        previous = ""
    p.write_bytes(eyelab.run(log, previous))
    return p


def job_entryscan():
    """Pre-registered (docs/PREREG-entryscan.md): one-sided entries that make residents drive past their road."""
    OUT.mkdir(exist_ok=True)
    p = OUT / "entryscan-v1.json"
    p.write_bytes(entryscan.run(log))
    return p


def job_areascan():
    """Pre-registered (docs/PREREG-areascan.md): the area table on the latest map, checked on three routers."""
    OUT.mkdir(exist_ok=True)
    p = OUT / "areascan-v1.json"
    p.write_bytes(areascan.run(log, repo()))
    return p


def job_bengaluru_remote():
    """One night only: the remote checks on 8 Bengaluru candidate places, approved by Rohit on 6 Nov (run 7 Nov).

    The places file is private (arcroad-internal data/bengaluru/places-candidate.json) and names the night it
    runs on ("run_on"). Same jobs and rules as Hyderabad's: mapwatch, openings, structures, then photos.
    """
    import tempfile
    places = json.loads(filer.get("data/bengaluru/places-candidate.json", log) or "{}")
    if not places.get("spots"):
        raise RuntimeError("places file unavailable")
    f = Path(tempfile.gettempdir()) / "bengaluru-places.json"
    f.write_text(json.dumps(places))
    url = f.as_uri()
    mods = (openings, mapwatch, structures, remote)
    saved = [m.PLACES_URL for m in mods]
    try:
        for m in mods:
            m.PLACES_URL = url
        out = {"city": "bengaluru", "status": places.get("status"), "selection": places.get("selection")}
        for name, fn in (("mapwatch", lambda: mapwatch.run(log)), ("openings", lambda: openings.run(log)),
                         ("structures", lambda: structures.run(log, "bengaluru"))):
            try:
                out[name] = json.loads(fn())
            except Exception as e:
                out[name] = {"error": str(e)[:300]}
                log(f"bengaluru_remote {name} failed: {e}")
        mw = json.dumps(out["mapwatch"]).encode() if "error" not in out["mapwatch"] else None
        out["remote"] = json.loads(remote.run(log, {"routercheck": None, "mapwatch": mw}))
    finally:
        for m, u in zip(mods, saved, strict=True):
            m.PLACES_URL = u
    OUT.mkdir(exist_ok=True)
    p = OUT / "bengaluru-remote-v1.json"
    p.write_bytes(json.dumps(out, indent=1).encode())
    return p


def tonight(night):
    """The night's queue: a one-off Bengaluru check first, the standing jobs, then the Sunday brief."""
    first = [("bengaluru_remote", job_bengaluru_remote)] if night == BENGALURU_REMOTE_NIGHT else []
    if socialreach.is_run_night(night):
        first = [("socialreach", job_socialreach), *first]  # first, so the long jobs cannot delay it
    last = [("viability", job_viability)] if viability.is_run_day(dt.date.fromisoformat(night)) else []
    if eyelab.is_run_day(dt.date.fromisoformat(night)):
        last = [*last, ("eyelab", job_eyelab)]
    if night == ADMINMAP_NIGHT:
        last = [*last, ("adminmap", job_adminmap)]  # after the standing jobs, so it cannot delay them
    if night in AREASCAN_NIGHTS:
        first = [("areascan", job_areascan), *first]  # after entryscan: about 1.5 to 2.5 hours
    if night in ENTRYSCAN_NIGHTS:
        first = [("entryscan", job_entryscan), *first]  # first: a one-off, about an hour
    return first + JOBS + last


AREASCAN_NIGHTS = {"2026-11-26", "2026-11-27"}  # second night repeats the first as a stability check
ENTRYSCAN_NIGHTS = {"2026-11-26", "2026-11-27"}  # second night repeats the first as a stability check
ADMINMAP_NIGHT = "2026-11-15"  # one night only: Sunday 15 Nov, 22:00 IST
BENGALURU_REMOTE_NIGHT = "2026-11-07"  # moved from 6 Nov: that night ran the earlier version  # matches run_on in the private places file

# Quick jobs first; openings (about 4.5 h on 4 Nov) last. remote reads tonight's routercheck and mapwatch.
# Bengaluru left the nightly queue on 6 Nov: the 5 Nov run was killed for memory (exit -9) on the 4 GB
# container. It runs in the Multi-city collection GitHub workflow instead (monthly, or on demand), which
# has 16 GB. job_bengaluru stays for a one-off run on a larger instance.
JOBS = [("routercheck", job_routercheck), ("mapwatch", job_mapwatch), ("remote", job_remote),
        ("corridor3d", job_corridor3d), ("structures", job_structures), ("hotspots", job_hotspots), ("openings", job_openings)]


def run_all(night=None, skip=()):
    # Same key as the Worker's R2 folder: the UTC date when the night starts (16:30 UTC = 22:00 IST).
    # After a container restart the Worker calls /start again with the night and the jobs already
    # filed (and any job that crashed the container twice), so the night resumes instead of ending.
    STATE.update(running=True, done=[], failed={}, night=night or time.strftime("%Y-%m-%d", time.gmtime()),
                 resumed=bool(skip), skipped=list(skip))
    jobs = [(n, f) for n, f in tonight(STATE["night"]) if n not in set(skip)]
    if skip:
        log(f"resumed night {STATE['night']}, skipping {', '.join(skip)}")
    for name, fn in jobs:
        log(f"start {name}")
        try:
            FILES[name] = fn()
            STATE["done"].append(name)
            log(f"done {name} ({FILES[name].stat().st_size} bytes)")
        except Exception as e:
            STATE["failed"][name] = str(e)[:300]
            log(f"FAILED {name}: {e}")
        filer.file_result(STATE["night"], name, FILES.get(name, ""), STATE, log)
    STATE["running"] = False
    filer.put(f"nights/{STATE['night']}/status.json", json.dumps(STATE, indent=1).encode(),
              f"night {STATE['night']}: finished", log)


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/start"):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            night = (q.get("night") or [None])[0]
            skip = tuple(j for j in (q.get("skip") or [""])[0].split(",") if j)
            if night and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", night):
                night = None
            if not STATE["running"]:
                threading.Thread(target=run_all, args=(night, skip), daemon=True).start()
            return self.send(202, b'{"started":true}', "application/json")
        if self.path == "/status":
            return self.send(200, json.dumps(STATE).encode(), "application/json")
        if self.path.startswith("/result/"):
            f = FILES.get(self.path.split("/")[-1])
            if not f:
                return self.send(404, b"not ready", "text/plain")
            ctype = "application/json" if f.suffix == ".json" else "application/gzip"
            return self.send(200, f.read_bytes(), ctype)
        return self.send(404, b"not found", "text/plain")

    def send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8080), H).serve_forever()
