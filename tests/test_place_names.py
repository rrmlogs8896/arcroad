"""Place names and codes readers can understand (Rohit, 7 Nov 2026).

The area at S18 is KPHB Colony locally, not APHB as the address lookup says; and every page that shows
S-codes explains them.
"""
from pathlib import Path

WEB = Path(__file__).resolve().parent.parent / "web"


def test_no_aphb_anywhere_on_the_site():
    hits = [str(p) for p in WEB.rglob("*") if p.suffix in {".html", ".js", ".json"} and "APHB" in p.read_text(errors="ignore")]
    assert not hits, hits


def test_lookup_maps_the_osm_name_to_the_local_one():
    import sys
    sys.path.insert(0, str(WEB.parent / "tools"))
    import road_names
    assert road_names.AREA_LOCAL["APHB Colony"] == "KPHB Colony"


def test_place_codes_are_explained_where_they_appear():
    for page in ("field/index.html", "drive/index.html", "index.html"):
        assert "S01 to S24" in (WEB / page).read_text(), page


def test_commit_sha_reads_a_snapshot_stamp(tmp_path):
    """10 Nov 2026: the runner image has no .git, so the commit travels in a COMMIT file."""
    from pipeline import pairing
    (tmp_path / "COMMIT").write_text("abc1234\n", encoding="utf-8")
    assert pairing.commit_sha(str(tmp_path)) == "abc1234"
