import pathlib
import re

from PIL import Image

WEB = pathlib.Path(__file__).resolve().parents[1] / "web"
PAGES = [p for p in WEB.rglob("index.html") if "media" not in p.parts] + [WEB / "act.html"]


def test_every_page_has_a_share_card():
    for page in PAGES:
        t = page.read_text()
        m = re.search(r'<meta property="og:image" content="https://arcroad\.org/(og/[a-z]+\.jpg)">', t)
        assert m, page
        assert 'name="twitter:card" content="summary_large_image"' in t, page
        assert 'property="og:title"' in t and 'property="og:description"' in t, page
        img = WEB / m.group(1)
        assert img.exists(), img
        assert img.stat().st_size < 300 * 1024, img
        assert Image.open(img).size == (1200, 630), img
