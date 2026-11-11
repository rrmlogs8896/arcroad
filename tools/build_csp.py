"""Write arcroad's security headers into web/_headers (11 Nov 2026).

    python3 tools/build_csp.py          # rewrite web/_headers
    python3 tools/build_csp.py --check  # exit 1 if web/_headers is out of date (CI)

The Content Security Policy allows only arcroad's own scripts, plus each inline script by its SHA-256 hash, so an
injected or altered script will not run. It ships as Report-Only first: browsers log what it would block without
blocking it. Once every page shows no reports, ENFORCE is switched to True in a separate, declared change.
"""

from __future__ import annotations

import base64
import hashlib
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
HEADERS = WEB / "_headers"
ENFORCE = True
TILES = "https://tiles.openfreemap.org"
INLINE = re.compile(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", re.S)


def inline_hashes():
    out = set()
    for p in sorted(WEB.rglob("*.html")):
        for body in INLINE.findall(p.read_text(encoding="utf-8")):
            out.add("'sha256-" + base64.b64encode(hashlib.sha256(body.encode("utf-8")).digest()).decode() + "'")
    return sorted(out)


def policy():
    return "; ".join([
        "default-src 'self'",
        "script-src 'self' " + " ".join(inline_hashes()),
        "style-src 'self' 'unsafe-inline'",
        f"img-src 'self' data: blob: {TILES}",
        f"connect-src 'self' {TILES}",
        "worker-src 'self' blob:",
        "font-src 'self' data:",
        "media-src 'self' blob:",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
        "upgrade-insecure-requests",
    ])


def headers():
    csp_name = "Content-Security-Policy" if ENFORCE else "Content-Security-Policy-Report-Only"
    lines = [
        "/*",
        "  X-Frame-Options: DENY",
        "  Content-Security-Policy: frame-ancestors 'none'",
        f"  {csp_name}: {policy()}",
        "  X-Content-Type-Options: nosniff",
        "  Referrer-Policy: strict-origin-when-cross-origin",
        "  Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=(), usb=(), interest-cohort=()",
        "  Strict-Transport-Security: max-age=31536000",
        "  Cross-Origin-Opener-Policy: same-origin",
        "  Cross-Origin-Resource-Policy: same-origin",
        "  X-Robots-Tag: noai, noimageai",
        "",
    ]
    if ENFORCE:
        lines[2] = "  " + lines[3].strip()
        del lines[3]
    return "\n".join(lines)


if __name__ == "__main__":
    text = headers()
    if "--check" in sys.argv:
        sys.exit(0 if HEADERS.read_text() == text else "web/_headers is out of date: run python3 tools/build_csp.py")
    HEADERS.write_text(text)
    print(f"wrote {HEADERS.relative_to(ROOT)} ({len(inline_hashes())} inline scripts hashed)")
