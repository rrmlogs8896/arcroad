"""arcroad research runner: runs the night's jobs one after another and hands each result to the Worker.

GET /start   start the queue (ignored if already running)
GET /status  {"running": bool, "done": [job, ...], "failed": {job: reason}, "log": [...]}
GET /result/<job>  the job's output (a JSON or a .tar.gz), once done
Only the Worker can reach this server; it has no public address.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tarfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import hotspots
import mapwatch
import openings
import remote
import routercheck
import structures

OUT = Path("/tmp/out")
STATE = {"running": False, "done": [], "failed": {}, "log": []}
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


def repo():
    """A fresh shallow clone of the public repo, made once per night and shared by the jobs."""
    work = Path("/tmp/arcroad")
    if not (work / ".git").exists():
        if work.exists():
            shutil.rmtree(work)
        subprocess.run(["git", "clone", "--depth", "1", "https://github.com/rrmlogs8896/arcroad.git", str(work)],
                       check=True)
    return work


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


# Quick jobs first; openings (about 4.5 h on 4 Nov) last. remote reads tonight's routercheck and mapwatch.
JOBS = [("routercheck", job_routercheck), ("mapwatch", job_mapwatch), ("remote", job_remote),
        ("structures", job_structures), ("bengaluru", job_bengaluru), ("hotspots", job_hotspots),
        ("openings", job_openings)]


def run_all():
    STATE.update(running=True, done=[], failed={})
    for name, fn in JOBS:
        log(f"start {name}")
        try:
            FILES[name] = fn()
            STATE["done"].append(name)
            log(f"done {name} ({FILES[name].stat().st_size} bytes)")
        except Exception as e:
            STATE["failed"][name] = str(e)[:300]
            log(f"FAILED {name}: {e}")
    STATE["running"] = False


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/start":
            if not STATE["running"]:
                threading.Thread(target=run_all, daemon=True).start()
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
