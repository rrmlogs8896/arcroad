"""A crash-reduction percentage from a study abroad never reads as an expected result here.

Devil's-advocate review, 4 Nov 2026 (overclaim watch): the FHWA -35% / -54% J-turn figures on the
/drive/3d/ fix cards are US results and must not read as an expected result for Hyderabad. Reporting
rule 3 (limitations beside results) for the fix cards: any card text in web/drive/3d/drive.js that
quotes a percentage must say in the same text that it is not an expected result for this place.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JS = (ROOT / "web" / "drive" / "3d" / "drive.js").read_text(encoding="utf-8")
CAVEAT = "not an expected result for Hyderabad"


def card_texts():
    block = JS[JS.index("var OPT = {"): JS.index("function nearDist()")]
    return re.findall(r"(?:guide|trade): '((?:[^'\\]|\\.)*)'", block)


def test_fix_cards_are_found():
    assert len(card_texts()) >= 10


def test_us_crash_percentages_carry_the_not_for_hyderabad_caveat():
    with_pct = [t for t in card_texts() if re.search(r"\d+\s?%", t)]
    assert with_pct, "expected the J-turn card's FHWA figures"
    for t in with_pct:
        assert CAVEAT in t, t


def test_map_view_fix_text_that_claims_safety_carries_the_caveat():
    """5 Nov review: the 2D /drive/ said 'A recognised safety design' with no source or caveat."""
    page = (ROOT / "web" / "drive" / "index.html").read_text(encoding="utf-8")
    texts = re.findall(r"\w+: '((?:[^'\\]|\\.)*)'", page)
    claims = [t for t in texts if re.search(r"safety design|stud(?:y|ies)|found fewer", t, re.I)]
    assert claims, "expected the J-turn text"
    for t in claims:
        assert CAVEAT in t, t
