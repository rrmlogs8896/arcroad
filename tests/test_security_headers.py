"""Security headers on every page (11 Nov 2026): no framing, no sniffing, HTTPS only, no hotlinking of arcroad's
films and images by other sites, and a Content Security Policy that lets only arcroad's own scripts run."""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_csp  # noqa: E402


def test_headers_file_is_current_so_every_inline_script_is_hashed():
    r = subprocess.run([sys.executable, str(ROOT / "tools/build_csp.py"), "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_the_protections_that_matter_are_all_there():
    h = (ROOT / "web/_headers").read_text()
    for needle in ("X-Frame-Options: DENY", "frame-ancestors 'none'", "X-Content-Type-Options: nosniff",
                   "Strict-Transport-Security: max-age=", "Cross-Origin-Resource-Policy: same-origin",
                   "object-src 'none'", "base-uri 'self'"):
        assert needle in h, needle


def test_scripts_may_come_only_from_arcroad():
    script_src = next(d for d in build_csp.policy().split("; ") if d.startswith("script-src"))
    assert "'unsafe-inline'" not in script_src and "'unsafe-eval'" not in script_src
    assert "http" not in script_src, "no third-party script host may be allowed"
