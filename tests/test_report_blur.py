"""28 Nov 2026: "Save blurred copy" gave back the same photo on a phone.

The share sheet was opened from inside an async callback, so the phone no longer saw it as a tap
and refused it silently. The copy is now made at once (no wait), shown on the page so it can be
saved by press-and-hold, and Save stays off until at least one box is drawn.
"""
from pathlib import Path

JS = (Path(__file__).resolve().parent.parent / "web" / "report" / "blur.js").read_text(encoding="utf-8")


def test_save_needs_a_box():
    assert "saveB.disabled = !rects.length" in JS


def test_copy_is_made_inside_the_tap():
    assert 'cv.toDataURL("image/jpeg"' in JS
    assert "cv.toBlob(" not in JS


def test_blurred_copy_is_shown_for_press_and_hold():
    assert "press and hold it, then choose Save to Photos" in JS
