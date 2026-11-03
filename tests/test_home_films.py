"""The home-page films: every film the player can pick has all five sizes and a poster.

Regression for a broken teaser: a film listed in web/index.html whose file is missing would leave
a black box for any visitor whose random pick or screen size landed on it.
"""
import re
from pathlib import Path

WEB = Path(__file__).resolve().parent.parent / "web"
TIERS = (480, 720, 1080, 1440, 2160)


def film_ids():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    block = html[html.index("var FILMS = ["):]
    block = block[: block.index("];")]
    return re.findall(r"\[\s*'([a-z]+)'", block)


def test_six_films_listed():
    assert len(film_ids()) == 6


def test_every_film_has_all_sizes_and_a_poster():
    media = WEB / "drive" / "media" / "films"
    for f in film_ids():
        assert (media / f"{f}.jpg").is_file(), f
        for t in TIERS:
            p = media / f"{f}-{t}.mp4"
            assert p.is_file(), p
            assert p.stat().st_size < 25 * 1024 * 1024, f"{p} is over the Pages 25 MiB limit"


def test_player_stores_nothing():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    block = html[html.index("var FILMS = ["):]
    block = block[: block.index("</script>")]
    for word in ("localStorage", "sessionStorage", "document.cookie", "indexedDB"):
        assert word not in block, word
