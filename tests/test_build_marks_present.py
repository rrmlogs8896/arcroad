"""Every published page, script, stylesheet and data file carries its build mark (8 Nov 2026)."""
import datetime as _dt
import json
import pathlib
import re

WEB = pathlib.Path(__file__).resolve().parents[1] / "web"
TOKEN = r"ar-[0-9a-f]{12}"

# The jury preview is private (passcode, noindex) until 6 Dec 2026, so it is held to the public-page
# rules only from that date. The date check makes this exclusion expire on its own.
def _public(p):
    return "jury" not in p.parts or _dt.date.today() >= _dt.date(2026, 12, 6)


def _files(ext):
    return [p for p in WEB.rglob(f"*.{ext}") if "vendor" not in p.parts and _public(p)]


def test_html_pages_carry_a_build_mark():
    for p in _files("html"):
        assert re.search(rf'<meta name="arcroad:build" content="{TOKEN}">', p.read_text()), p


def test_scripts_and_styles_carry_a_build_mark():
    for p in _files("js") + _files("css"):
        assert re.search(TOKEN, p.read_text()), p


def test_data_files_carry_a_build_mark():
    for p in _files("json") + _files("geojson"):
        d = json.loads(p.read_text())
        if isinstance(d, dict):
            assert re.fullmatch(TOKEN, d.get("_build", "")), p


def test_site_has_a_root_favicon():
    """9 Nov 2026: 13 pages had no icon link, so browsers asked for /favicon.ico and got a 404."""
    assert (WEB / "favicon.ico").stat().st_size > 0


def test_unknown_addresses_get_a_real_not_found_page():
    """11 Nov 2026: with no 404.html, Cloudflare Pages served the home page at any unknown address, and its
    relative links (nav.js, fonts.css) resolved under that path and failed, so the page loaded broken."""
    page = (WEB / "404.html").read_text()
    assert 'name="robots" content="noindex"' in page
    assert '<base href="/">' in page, "404.html is served at any path, so its links must resolve from the root"
