"""Share row (19 Nov 2026): nothing leaves the visitor's device, and every QR code opens its own page."""
import importlib.util
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
spec = importlib.util.spec_from_file_location("share_block", ROOT / "tools" / "share_block.py")
sb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sb)


def test_share_row_is_on_each_page_once_and_before_the_footer():
    for rel, slug in sb.PAGES.items():
        s = (WEB / rel).read_text()
        assert s.count("<!-- share:start -->") == 1, rel
        assert s.index("<!-- share:start -->") < s.rindex("<footer"), rel
        assert f'/share/{slug}.svg' in s and f'data-url="https://arcroad.org/{slug}/"' in s, rel
        assert sb.NOTE in s, rel


def test_rerunning_changes_nothing():
    for rel, slug in sb.PAGES.items():
        s = (WEB / rel).read_text()
        assert sb.apply(s, slug) == s, rel


def test_no_form_no_input_no_network_in_the_share_row():
    for rel in sb.PAGES:
        m = re.search(r"<!-- share:start -->(.*?)<!-- share:end -->", (WEB / rel).read_text(), re.S)
        assert not re.search(r"<form|<input|tel:|sms:", m.group(1)), rel
    js = (WEB / "share.js").read_text()
    assert not re.search(r"fetch\(|XMLHttpRequest|sendBeacon|localStorage|sessionStorage|cookie", js)


def test_each_qr_code_exists_and_names_its_page():
    for slug in sb.PAGES.values():
        svg = (WEB / "share" / f"{slug}.svg").read_text()
        assert svg.startswith("<svg") and f"arcroad.org/{slug}/" in svg
