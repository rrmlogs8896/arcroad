"""The research runner files each night's results into the private repo for the morning agent.

5 Nov 2026: Rohit approved a night-results reader agent. It cannot reach Cloudflare storage, so the runner
files its JSON results into arcroad-internal. Filing must never fail a job, must do nothing without a token,
and must write only under nights/.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "research" / "runner" / "app"))
import filer


def test_no_token_files_nothing(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr(filer, "_req", lambda *a, **k: (_ for _ in ()).throw(AssertionError("called")))
    assert filer.put("nights/2026-11-05/x.json", b"{}", "m", lambda m: None) is False


def test_files_under_nights_into_the_private_repo_only(monkeypatch, tmp_path):
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    calls = []

    def req(method, url, token, body=None):
        calls.append((method, url, body))
        if method == "GET":
            import urllib.error
            raise urllib.error.HTTPError(url, 404, "nf", {}, None)
        return {}

    monkeypatch.setattr(filer, "_req", req)
    p = tmp_path / "routercheck-v1.json"
    p.write_text('{"ok": 1}')
    filer.file_result("2026-11-05", "routercheck", p, {"running": True}, lambda m: None)
    puts = [c for c in calls if c[0] == "PUT"]
    assert [u.split("/contents/")[1] for _, u, _ in puts] == ["nights/2026-11-05/routercheck.json", "nights/2026-11-05/status.json"]
    assert all("/repos/rrmlogs8896/arcroad-internal/contents/nights/" in u for _, u, _ in puts)
    assert json.loads(__import__("base64").b64decode(puts[0][2]["content"])) == {"ok": 1}


def test_a_filing_error_never_fails_the_job(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    monkeypatch.setattr(filer, "_req", lambda *a, **k: (_ for _ in ()).throw(OSError("network down")))
    msgs = []
    assert filer.put("nights/2026-11-05/x.json", b"{}", "m", msgs.append) is False
    assert msgs and "could not file" in msgs[0]


def test_large_results_stay_in_r2(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    monkeypatch.setattr(filer, "_req", lambda *a, **k: (_ for _ in ()).throw(AssertionError("called")))
    assert filer.put("nights/d/x.json", b"x" * (filer.MAX_BYTES + 1), "m", lambda m: None) is False


def test_missing_token_is_logged_once(monkeypatch):
    import filer
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr(filer, "_WARNED", [])
    logs = []
    assert filer.put("nights/x/a.json", b"{}", "m", logs.append) is False
    assert filer.put("nights/x/b.json", b"{}", "m", logs.append) is False
    assert len([m for m in logs if "no GITHUB_TOKEN" in m]) == 1
