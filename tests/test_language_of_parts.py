"""Hindi and Telugu text must not be read out in an English voice.

The failure this prevents (found 20 Nov 2026): the letter kit's language
buttons ("हिन्दी", "తెలుగు") and the translated letter itself carried no `lang`
attribute, so the page's `lang="en"` applied to them. Screen readers then read
Devanagari and Telugu with an English voice (garbled or skipped), and print and
font fallback had no language hint. WCAG 2.2 SC 3.1.2 "Language of Parts".

1. Every page under web/ declares its language on <html>.
2. Any static text in Devanagari, Telugu or Arabic script sits inside an
   element whose nearest `lang` matches that script.
3. The letter preview marks every translated part (subject, body, options,
   closing lines, sign-off) with the letter's own language.

Competing explanation for a pass: the check could pass because it never looks
at the non-Latin text. The control is test_check_sees_the_language_buttons,
which fails if the scan finds no Indian-script text on act.html at all.
"""

import html.parser
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
PAGES = sorted(p for p in WEB.rglob("*.html") if "vendor" not in p.parts)

SCRIPTS = {
    "Devanagari": (re.compile("[ऀ-ॿ]"), {"hi", "mr", "ne", "sa"}),
    "Telugu": (re.compile("[ఀ-౿]"), {"te"}),
    "Arabic": (re.compile("[؀-ۿ]"), {"ur", "ar", "fa"}),
}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


class _LangScan(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []  # (tag, lang or None)
        self.root_lang = None
        self.found = []  # (script, effective lang, text)
        self.skip = 0

    def _lang(self):
        for _, lang in reversed(self.stack):
            if lang:
                return lang.split("-")[0].lower()
        return None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html":
            self.root_lang = a.get("lang")
        if tag in ("script", "style"):
            self.skip += 1
        if tag not in VOID:
            self.stack.append((tag, a.get("lang")))
        for name in ("aria-label", "title", "alt", "placeholder"):
            if a.get(name):
                self._check(a[name], a.get("lang") or self._lang())

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip:
            self.skip -= 1
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if not self.skip:
            self._check(data, self._lang())

    def _check(self, text, lang):
        for script, (rx, _) in SCRIPTS.items():
            if rx.search(text):
                self.found.append((script, lang, text.strip()[:40]))


def _scan(page):
    s = _LangScan()
    s.feed(page.read_text(encoding="utf-8"))
    return s


def test_every_page_declares_its_language():
    missing = [str(p.relative_to(ROOT)) for p in PAGES if not _scan(p).root_lang]
    assert not missing, f"<html> without lang: {missing}"


def test_indian_script_text_is_not_read_as_english():
    wrong = []
    for p in PAGES:
        for script, lang, text in _scan(p).found:
            if lang not in SCRIPTS[script][1]:
                wrong.append(f"{p.relative_to(ROOT)}: {script} text {text!r} has lang={lang!r}")
    assert not wrong, "\n".join(wrong)


def test_check_sees_the_language_buttons():
    found = {(script, lang) for script, lang, _ in _scan(WEB / "act.html").found}
    assert ("Devanagari", "hi") in found and ("Telugu", "te") in found, found


def test_letter_preview_marks_translated_parts():
    js = (WEB / "kit" / "act.js").read_text(encoding="utf-8")
    assert re.search(r"function inLang\(e, code\) \{[^}]*setAttribute\('lang', code\)", js), "inLang helper missing"
    m = re.search(r"function renderLetter\(\) \{(.*?)\n  \}", js, re.S)
    assert m, "renderLetter not found"
    body = m.group(1)
    for part in ("L.subject", "L.body", "L.options", "L.close", "L.signoff"):
        lines = [ln for ln in body.splitlines() if part in ln]
        assert lines, f"{part} is no longer rendered"
        assert all("inLang(" in ln and "L.lang" in ln for ln in lines), f"{part} rendered without its language"
