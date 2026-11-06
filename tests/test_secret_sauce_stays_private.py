"""The public repo never carries arcroad's private edge.

6 Nov 2026: Rohit asked that the core logic behind the numbers stay protected. The method stays public (it is
what makes the numbers checkable); the edge lives only in arcroad-internal (SECRET-SAUCE.md). This test fails
CI if any private asset, raw drive or not-for-publication output lands in the public repo or on the site.
"""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FORBIDDEN_PATHS = [
    r"(^|/)gpx_scan/", r"(^|/)maplag/", r"(^|/)pro/", r"data/verification/tracks/", r"(^|/)outreach/",
    r"private-names", r"places-candidate", r"\.gpx$", r"\.fit$", r"(^|/)drives?/raw", r"SECRET-SAUCE",
    r"AGENT-BRIEF", r"(^|/)nights/", r"drive-photos", r"baseline-v1", r"labels-v1", r"label_photos",
    r"STREET-EVIDENCE", r"pick_bengaluru", r"scene-cards",
]
FORBIDDEN_TEXT = ["NOT FOR PUBLICATION", "tomtom.com/routing"]
TEXT_SUFFIXES = {".html", ".js", ".json", ".css", ".txt", ".md", ".csv", ".xml", ".svg"}


def tracked():
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return [p for p in out.splitlines() if p]


def test_no_private_asset_paths():
    bad = [p for p in tracked() if any(re.search(rx, p) for rx in FORBIDDEN_PATHS)]
    assert not bad, f"private assets in the public repo: {bad}"


def test_site_carries_no_unpublishable_output():
    hits = []
    for p in tracked():
        if not p.startswith("web/") or Path(p).suffix not in TEXT_SUFFIXES:
            continue
        text = (ROOT / p).read_text(errors="ignore")
        hits += [f"{p}: {t}" for t in FORBIDDEN_TEXT if t in text]
    assert not hits, f"not-for-publication content on the site: {hits}"
