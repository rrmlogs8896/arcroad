"""One site navigation for every arcroad page. Run from the repo root: python tools/site_nav.py

Rewrites the block between <!-- nav:start --> and <!-- nav:end --> (or the page's first nav, the first
time) and makes sure the page links web/nav.css and web/nav.js. The field page builder imports nav()
so a rebuild emits the same markup.

SUPPORT_URL stays None until the Razorpay payment page is live AND Razorpay has confirmed in writing
that optional support for a free information site is allowed. With None, no payment button is shown.
"""

from __future__ import annotations

import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")

SUPPORT_URL: str | None = None      # Razorpay Payment Page link; None = button hidden

GROUPS = [
    ("findings", "Findings", [
        ("field/", "Driven results", "Every pass we drove, by direction"),
        ("evidence/", "Evidence", "What studies show about roads and behaviour"),
        ("globe/", "Globe", "29 cities, from orbit to your street"),
        ("data/", "Open data", "Download the counts, free to use"),
    ]),
    ("cost", "Your cost", [
        ("cost/", "Cost calculator", "Your crossing in rupees and minutes"),
        ("roads/", "What else the road costs", "Barricades, works, parking, surface"),
        ("roads/glare/", "Night glare", "An oncoming high beam, from the driver's seat"),
        ("act.html", "Write to the people responsible", "A ready letter for each place"),
    ]),
    ("part", "Take part", [
        ("volunteer/", "Volunteer", "Measure your own city"),
        ("report/", "Report a change", "A median opening opened or closed"),
    ]),
]


def nav(prefix: str, current: str, brand: bool = True) -> str:
    """Markup for one page. prefix: path to web root ('', '../', '../../'); current: the page's path
    from web root (e.g. 'field/'); brand: include the arcroad home link (pages with their own logo pass False)."""
    def cur(path: str) -> str:
        return ' aria-current="page"' if path == current else ""

    out = ['<!-- nav:start -->', f'<nav class="sn{" inline" if brand else ""}" aria-label="arcroad">']
    if brand:
        out.append(f'<a class="sn-home" href="{prefix or "./"}"{cur("")}>arcroad</a>')
    out.append(f'<a class="sn-i" href="{prefix}drive/"{cur("drive/")}>Drive it</a>')
    for gid, label, items in GROUPS:
        here = any(p == current for p, _, _ in items)
        out.append(f'<div class="sn-g{" cur" if here else ""}">'
                   f'<button class="sn-i" type="button" aria-expanded="false" aria-controls="sn-{gid}">{label}</button>'
                   f'<div class="sn-p" id="sn-{gid}">')
        for p, title, sub in items:
            out.append(f'<a href="{prefix}{p}"{cur(p)}><b>{title}</b><span>{sub}</span></a>')
        out.append('</div></div>')
    out.append(f'<a class="sn-i" href="{prefix}help/"{cur("help/")}>Help</a>')
    if SUPPORT_URL:
        out.append(f'<a class="sn-pay" href="{SUPPORT_URL}" rel="noopener" target="_blank">Support arcroad</a>')
    out.append('</nav>')
    out.append('<!-- nav:end -->')
    return "".join(out)


def reuse(prefix: str) -> str:
    """One line in every footer: what is free to reuse (data, code) and what is not (name, logo, films, design)."""
    return ('<!-- reuse:start --><span class="sn-reuse">© 2026 arcroad. Data (ODbL) and code (MIT) are free to reuse with credit; '
            'the arcroad name, logo, films and design are not. '
            f'<a href="{prefix}reuse/">What you may reuse</a></span><!-- reuse:end -->')


REUSE = re.compile(r"<!-- reuse:start -->.*?<!-- reuse:end -->", re.S)


def apply_reuse(html: str, prefix: str) -> str:
    markup = reuse(prefix)
    if REUSE.search(html):
        return REUSE.sub(lambda m: markup, html, count=1)
    i = html.rfind("</footer>")
    if i < 0:
        return html
    head = html[:i].rstrip()
    j = len(head) - len("</div>") if head.endswith("</div>") else i
    return html[:j] + markup + html[j:]


def head_tags(prefix: str) -> str:
    return (f'<link rel="stylesheet" href="{prefix}nav.css" id="sn-css">\n'
            f'<script src="{prefix}nav.js" defer id="sn-js"></script>\n')


# page file -> (prefix, current, brand)
PAGES = {
    "index.html": ("", "", False),
    "access.html": ("", "access.html", False),
    "act.html": ("", "act.html", False),
    "cost/index.html": ("../", "cost/", False),
    "data/index.html": ("../", "data/", True),
    "drive/index.html": ("../", "drive/", True),
    "drive/3d/index.html": ("../../", "drive/", True),
    "evidence/index.html": ("../", "evidence/", True),
    "help/index.html": ("../", "help/", True),
    "report/index.html": ("../", "report/", True),
    "roads/index.html": ("../", "roads/", True),
    "roads/glare/index.html": ("../../", "roads/glare/", True),
    "volunteer/index.html": ("../", "volunteer/", True),
    "reuse/index.html": ("../", "reuse/", True),
}

FIRST_NAV = re.compile(r'<nav class="top" aria-label="arcroad">.*?</nav>|<nav class="sitenav" aria-label="arcroad">.*?</nav>'
                       r'|<nav aria-label="arcroad">.*?</nav>', re.S)
BLOCK = re.compile(r"<!-- nav:start -->.*?<!-- nav:end -->", re.S)
OLD_STYLES = re.compile(r'<style id="sitenav(-css)?">.*?</style>\n?', re.S)


def apply(html: str, prefix: str, current: str, brand: bool) -> str:
    markup = nav(prefix, current, brand)
    if BLOCK.search(html):
        html = BLOCK.sub(lambda m: markup, html, count=1)
    else:
        html, n = FIRST_NAV.subn(lambda m: markup, html, count=1)
        if n != 1:
            raise SystemExit("no nav found to replace")
    html = OLD_STYLES.sub("", html)
    if 'id="sn-css"' not in html:
        html = html.replace("</head>", head_tags(prefix) + "</head>", 1)
    return apply_reuse(html, prefix)


def main() -> None:
    for rel, (prefix, current, brand) in PAGES.items():
        path = os.path.join(WEB, rel)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as fh:
            html = fh.read()
        new = apply(html, prefix, current, brand)
        if new != html:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(new)
            print("nav:", rel)


if __name__ == "__main__":
    main()
