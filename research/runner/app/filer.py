"""Files each night's results into the private repo, so a scheduled agent can read them without Cloudflare access.

Needs GITHUB_TOKEN: a fine-grained token limited to rrmlogs8896/arcroad-internal, Contents read and write.
Without it, nothing is filed and the night runs exactly as before. A filing error never fails a job.
Writes only nights/<date>/<job>.json and nights/<date>/status.json in arcroad-internal.
get() reads a file from the same repo (the weekly viability job reads the agent brief and secret-sauce index).
"""
from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request

REPO = "rrmlogs8896/arcroad-internal"
API = f"https://api.github.com/repos/{REPO}/contents/"
MAX_BYTES = 900_000
AUTHOR = {"name": "rrmlogs8896", "email": "345888225+rrmlogs8896@users.noreply.github.com"}


def _req(method, url, token, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
        "User-Agent": "arcroad-research/1.0", "X-GitHub-Api-Version": "2022-11-28"})
    with urllib.request.urlopen(r, timeout=60) as resp:
        return json.loads(resp.read() or b"{}")


def put(path: str, content: bytes, message: str, log) -> bool:
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        return False
    if len(content) > MAX_BYTES:
        log(f"filer: {path} is {len(content)} bytes, too large to file; kept in R2 only")
        return False
    try:
        sha = None
        try:
            sha = _req("GET", API + path, token).get("sha")
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
        body = {"message": message, "content": base64.b64encode(content).decode(), "branch": "main",
                "committer": AUTHOR, "author": AUTHOR}
        if sha:
            body["sha"] = sha
        _req("PUT", API + path, token, body)
        return True
    except Exception as e:  # filing is a convenience; the night's results are already in R2
        log(f"filer: could not file {path}: {str(e)[:120]}")
        return False


def get(path: str, log) -> str:
    """A text file from arcroad-internal, or "" (no token, missing file or any error)."""
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        return ""
    try:
        return base64.b64decode(_req("GET", API + path, token).get("content", "")).decode()
    except Exception as e:
        log(f"filer: could not read {path}: {str(e)[:120]}")
        return ""


def file_result(night: str, job: str, path, state: dict, log) -> None:
    if str(path).endswith(".json"):
        put(f"nights/{night}/{job}.json", path.read_bytes(), f"night {night}: {job}", log)
    put(f"nights/{night}/status.json", json.dumps(state, indent=1).encode(), f"night {night}: status", log)
