import pathlib
import re
import struct

WEB = pathlib.Path(__file__).resolve().parents[1] / "web"


def jpeg_size(path):
    b = path.read_bytes()
    i = 2
    while i < len(b):
        marker, length = b[i + 1], struct.unpack(">H", b[i + 2:i + 4])[0]
        if marker in (0xC0, 0xC1, 0xC2):
            h, w = struct.unpack(">HH", b[i + 5:i + 9])
            return w, h
        i += 2 + length
    raise ValueError(path)


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
        assert jpeg_size(img) == (1200, 630), img
