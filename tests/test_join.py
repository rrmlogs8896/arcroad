from pathlib import Path

from tools import place_join

WEB = Path(__file__).resolve().parent.parent / "web"


def test_place_is_idempotent():
    page = "<main><p>x</p></main>"
    once = place_join.place(page, "cost", "</main>")
    assert place_join.place(once, "cost", "</main>") == once
    assert once.count('data-join="cost"') == 1


def test_every_page_carries_one_strip():
    for rel, (slot, _) in place_join.PAGES.items():
        text = (WEB / rel).read_text(encoding="utf-8")
        assert text.count(place_join.START) == 1, rel
        assert f'data-join="{slot}"' in text, rel


def test_strip_asks_for_nothing_personal():
    js = (WEB / "join.js").read_text(encoding="utf-8")
    for word in ('type="email"', 'type="tel"', "name=\"name\"", "phone\" name"):
        assert word not in js


def test_music_button_is_gone():
    assert "ak-snd" not in (WEB / "ask.js").read_text(encoding="utf-8")
    assert "ak-snd" not in (WEB / "ask.css").read_text(encoding="utf-8")
