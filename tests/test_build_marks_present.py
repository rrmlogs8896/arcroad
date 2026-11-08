"""Every published page, script, stylesheet and data file carries its build mark (8 Nov 2026)."""
import json
import pathlib
import re

WEB = pathlib.Path(__file__).resolve().parents[1] / "web"
TOKEN = r"ar-[0-9a-f]{12}"


def _files(ext):
    return [p for p in WEB.rglob(f"*.{ext}") if "vendor" not in p.parts]


def test_html_pages_carry_a_build_mark():
    for p in _files("html"):
        assert re.search(rf'<meta name="arcroad:build" content="{TOKEN}">', p.read_text()), p


def test_scripts_and_styles_carry_a_build_mark():
    for p in _files("js") + _files("css"):
        assert re.search(TOKEN, p.read_text()), p


def test_data_files_carry_a_build_mark():
    for p in _files("json") + _files("geojson"):
        d = json.loads(p.read_text())
        if isinstance(d, dict):
            assert re.fullmatch(TOKEN, d.get("_build", "")), p
