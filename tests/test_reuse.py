"""Every public page says what may be reused, and the site cannot be framed by a look-alike.

5 Nov 2026: Rohit asked to safeguard the sites against copying. Blocking copy or right-click would not stop
it (the page source is always readable), would break accessibility, and would contradict the ODbL and MIT
licences arcroad publishes under. Instead: a clear reuse notice on every page, a /reuse/ page, no framing,
and AI-training crawlers asked not to collect the pages.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
PUBLIC = [p for p in WEB.rglob("*.html") if "globe" not in p.parts and "kit" not in p.parts and "m2" not in p.parts]


def test_every_public_page_carries_the_reuse_line():
    missing = [str(p.relative_to(WEB)) for p in PUBLIC
               if "<!-- reuse:start -->" not in p.read_text(encoding="utf-8")]
    assert not missing, missing


def test_reuse_link_resolves_from_each_page():
    for p in PUBLIC:
        m = re.search(r'class="sn-reuse">.*?<a href="([^"]+)"', p.read_text(encoding="utf-8"))
        assert m and (p.parent / m.group(1) / "index.html").resolve() == (WEB / "reuse" / "index.html").resolve(), p


def test_site_refuses_to_be_framed():
    h = (WEB / "_headers").read_text()
    assert "X-Frame-Options: DENY" in h and "frame-ancestors 'none'" in h


def test_copy_and_right_click_are_not_blocked():
    """Blocking them breaks screen readers and text selection and stops no one."""
    for p in PUBLIC:
        t = p.read_text(encoding="utf-8")
        assert not re.search(r"oncontextmenu|oncopy|user-select:\s*none\s*[;}](?![^{]*\bbutton)", t), p


def test_ai_training_crawlers_are_disallowed_but_search_is_not():
    r = (WEB / "robots.txt").read_text()
    for bot in ("GPTBot", "CCBot", "Google-Extended", "ClaudeBot"):
        assert f"User-agent: {bot}" in r
    assert "User-agent: *\nAllow: /" in r
