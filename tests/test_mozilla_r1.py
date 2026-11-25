"""18 Nov 2026 release: honest headline, short descriptions, Terms and Privacy on every page."""
import html
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
WEB = ROOT / "web"


def _pages():
    return [p for p in WEB.rglob("*.html") if "vendor" not in p.parts]


def test_descriptions_fit_search_results():
    """Art 1g: a description over 155 characters is cut off by Google; every one ends in a full stop."""
    for p in _pages():
        m = re.search(r'<meta name="description" content="([^"]*)"', p.read_text())
        if m:
            d = html.unescape(m.group(1))
            assert len(d) <= 155 and d.endswith("."), (p, len(d))


def test_every_reuse_footer_links_terms_and_privacy():
    for p in _pages():
        s = p.read_text()
        m = re.search(r"<!-- reuse:start -->(.*?)<!-- reuse:end -->", s, re.S)
        if m:
            assert 'terms/">Terms' in m.group(1) and 'privacy/">Privacy' in m.group(1), p


def test_terms_and_privacy_pages_exist_and_are_in_the_sitemap():
    sm = (WEB / "sitemap.xml").read_text()
    for slug in ("terms", "privacy"):
        assert (WEB / slug / "index.html").exists()
        assert f"https://arcroad.org/{slug}/" in sm


def test_headline_uses_the_strict_count_everywhere():
    """18 Nov 2026: the strict count (rules fixed before the drive) is always stated.
    22 Nov 2026 (independent review): all scored directions matched, so the headline says so
    and gives the strict count beside it; "S of N" must never be shown as if the rest failed."""
    field = (WEB / "field" / "index.html").read_text()
    m = re.search(r'<p class="lead">All (\d+) comparable directions matched the model, and none failed\. (\d+) of them were judged under the rules', field)
    assert m, "field lead must state the full count and the strict count"
    n, strict = m.group(1), m.group(2)
    for rel in ("index.html", "moves/index.html"):
        s = (WEB / rel).read_text()
        assert f"all {n}" in s.lower(), rel
        assert f"{strict} " in s, rel
        for loose in re.findall(r"(\d+) of (\d+) (?:comparable )?directions matched", s):
            assert loose[0] == loose[1], (rel, loose)
