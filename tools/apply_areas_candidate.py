"""Apply a reviewed area-table candidate to web/index.html (only on Rohit's go).

Usage, from the repo root: python3 tools/apply_areas_candidate.py data/candidates/areas-2026-11-26.json
Rewrites the AREAS rows, adds the "routers disagree" note for unconfirmed rows, states the map date
and the three-router check in the label above the table, then rebuilds the CSP hashes.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
page = ROOT / "web" / "index.html"
cand = json.loads(Path(sys.argv[1]).read_text())
html = page.read_text()

rows = ",\n".join(
    f'    [{json.dumps(n)}, {di:.1f}, "{m:,} m", {pts}, {"true" if gap else "false"}, {"true" if unc else "false"}]'
    for n, di, m, pts, gap, unc in cand["rows"])
new_block = "var AREAS = [\n" + rows + "\n  ];"
html, k = re.subn(r"var AREAS = \[.*?\];", new_block, html, count=1, flags=re.S)
assert k == 1, "AREAS block not found"

old_note = '''      tr.className = "flagrow";
    }
'''
add_note = old_note + '''    if (a[5]) {
      var u = document.createElement("div");
      u.className = "gapnote";
      u.textContent = "routers disagree: not yet confirmed";
      name.appendChild(u);
    }
'''
if "routers disagree" not in html:
    assert html.count(old_note) == 1, "render anchor not found"
    html = html.replace(old_note, add_note)

old_tag = '<p class="mtag"><span>Modelled</span> from OpenStreetMap, not yet driven. <a href="field/">Driven results</a></p>\n    <div class="scroll">'
new_tag = ('<p class="mtag"><span>Modelled</span> from OpenStreetMap (map of 25 November 2026), checked on three '
           'separate route planners, not yet driven. <a href="field/">Driven results</a></p>\n    <div class="scroll">')
if old_tag in html:
    html = html.replace(old_tag, new_tag)

page.write_text(html)
subprocess.run([sys.executable, str(ROOT / "tools" / "build_csp.py")], check=True)
print("area table updated; review locally, then deploy with: bash tools/deploy_site.sh")
