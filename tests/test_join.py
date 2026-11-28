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


def test_quick_join_first_step_goes_to_signup_not_uturns():
    """28 Nov 2026: after the 10-second join, step 1 sent people to /uturns/ and they never chose how to help."""
    js = (WEB / "join.js").read_text()
    assert '"/volunteer/#signup"] : TASKS.filter' not in js
    assert 'data-a="done"' in js and 'data-a="skip"' in js and "helpSkipped" in js
    card = (WEB / "volunteer" / "card.js").read_text()
    assert "old && old.code ? old.code : code()" in card
    assert "form.hidden = !needs" in card


def test_long_reading_text_folds_under_the_sites_own_plus():
    """28 Nov 2026: text-heavy runs tuck under the same "+" (details.more) the pages already use; legal pages stay open."""
    nav = (WEB / "nav.js").read_text(encoding="utf-8")
    assert "d.className='more fd'" in nav and "privacy|terms" in nav
    css = (WEB / "nav.css").read_text(encoding="utf-8")
    assert 'main details:not([class])>summary::before{content:"+"' in css
    assert 'main details.more>summary::before,main details:not([class])>summary::before' in css
    assert "@media print{main details>*{display:block!important}" in css
