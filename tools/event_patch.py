"""Event patch, 26 Nov 2026: shortlist banner, date and work scrub, authorship line, no fixed turnaround promise.

Idempotent. Run from anywhere: python3 tools/event_patch.py [repo_root]
Remove the banner after the event with: python3 tools/event_patch.py [repo_root] --remove-banner
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else
                       os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
REMOVE = "--remove-banner" in sys.argv
WEB = os.path.join(ROOT, "web")

BANNER = '<!-- event:start --><div class="ev-banner" role="note" style="background:#0f1720;color:#e9eef2;font:500 13px/1.45 Inter,system-ui,sans-serif;text-align:center;padding:9px 16px;border-bottom:1px solid rgba(255,255,255,.08)"><span style="display:inline-block;margin-right:8px;padding:1px 9px;border:1px solid #e8b86a;border-radius:999px;color:#e8b86a;font-weight:600;letter-spacing:.02em">Shortlisted</span><a href="https://cyberabadmoves.in/" target="_blank" rel="noopener noreferrer" style="color:inherit;text-decoration:underline;text-decoration-color:rgba(233,238,242,.35);text-underline-offset:3px">Cyberabad Moves 2026</a>, Citizens Innovation Challenge. On display at T-Hub, Raidurg, 26 to 28 November · <a href="/moves/" style="color:#e8b86a;text-decoration:underline;text-underline-offset:3px">See our entry</a></div><!-- event:end -->'
EVENT = re.compile(r"<!-- event:start -->.*?<!-- event:end -->\n?", re.S)

TEXT_SWAPS = [
    ("1, 2, 3, 4, 6, 7, 20 and 21 Nov 2026", "November 2026"),
    ("within 24 hours", "promptly"),
    ("GPS-tracked on a Sunday evening, 1 Nov 2026", "GPS-tracked on 1 Nov 2026"),
    ("Ordinary commutes that were not recorded", "Ordinary trips that were not recorded"),
    ("on a Sunday afternoon and evening; weekday peaks will differ", "on a weekend; weekday peaks will differ"),
]

DRIVE_WHAT = {
    "commute to work, recorded": "ordinary trip, recorded",
    "drive home with planned checks": "ordinary trip with planned checks",
    "commute with checks, distance estimated": "ordinary trip with planned checks, distance estimated",
    "Sunday reading through the study corridor on a personal trip; only the corridor part is counted":
        "reading through the study corridor; only the corridor part is counted",
    "night reading through the study corridor on the way back from a personal trip; only the corridor part is counted":
        "reading through the study corridor; only the corridor part is counted",
    "repeat drives until one crossing counted, then the drive home; time parked with the recorder still on is not counted":
        "repeat drives until one crossing counted; time parked with the recorder still on is not counted",
    "first look at the problem near home": "first look at the problem",
}

AGG = ('<h3>The drives</h3><p class="note">13 days of driving: one in late October and 12 in November 2026, '
       'including ordinary trips with planned checks along the way.</p>')
DRIVES_HTML = re.compile(r"<h3>Drive by drive</h3><ul>.*?</ul>", re.S)
REUSE_OLD = "<!-- reuse:start --><span class=\"sn-reuse\">© 2026 arcroad."
REUSE_NEW = "<!-- reuse:start --><span class=\"sn-reuse\">Made by Rohit and Team arcroad. © 2026 arcroad."

changed = []


def write(path, new, old):
    if new != old:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new)
        changed.append(os.path.relpath(path, ROOT))


for path in glob.glob(os.path.join(WEB, "**", "*.html"), recursive=True):
    with open(path, encoding="utf-8") as f:
        old = f.read()
    new = EVENT.sub("", old)
    for a, b in TEXT_SWAPS:
        new = new.replace(a, b)
    new = DRIVES_HTML.sub(AGG, new)
    if REUSE_NEW not in new:
        new = new.replace(REUSE_OLD, REUSE_NEW)
    if not REMOVE:
        m = re.search(r"<body[^>]*>", new)
        if m:
            new = new[:m.end()] + "\n" + BANNER + "\n" + new[m.end():].lstrip("\n")
    write(path, new, old)

for path in (glob.glob(os.path.join(ROOT, "tools", "*.py")) + glob.glob(os.path.join(ROOT, "data", "field", "*.json"))):
    if path.endswith("event_patch.py"):
        continue
    with open(path, encoding="utf-8") as f:
        old = f.read()
    new = old
    for a, b in TEXT_SWAPS:
        new = new.replace(a, b)
    if path.endswith("build_field_page.py"):
        new = new.replace("f'<h3>Drive by drive</h3><ul>{dl}</ul>'", repr(AGG))
    if path.endswith("site_nav.py"):
        new = new.replace("'<!-- reuse:start --><span class=\"sn-reuse\">© 2026 arcroad. ",
                          "'<!-- reuse:start --><span class=\"sn-reuse\">Made by Rohit and Team arcroad. © 2026 arcroad. ")
    write(path, new, old)

ep = os.path.join(ROOT, "data", "field", "effort.json")
if os.path.exists(ep):
    with open(ep, encoding="utf-8") as f:
        old = f.read()
    d = json.loads(old)
    for x in d.get("drives", []):
        x["what"] = DRIVE_WHAT.get(x["what"], x["what"])
    write(ep, json.dumps(d, ensure_ascii=False, indent=2) + "\n", old)

print(f"event_patch: {len(changed)} file(s) changed in {ROOT}")
for c in sorted(changed):
    print("  " + c)
