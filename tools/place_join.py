"""Place the volunteer join strip on the pages where a reader has just seen the problem.

Idempotent: each page gets one block between join markers, rewritten on every run, so page
builders that regenerate a page never lose it. Run from the repo root (deploy_site.sh does).
"""

import re
import sys
from pathlib import Path

WEB = Path(__file__).resolve().parent.parent / "web"
START, END = "<!-- join:start -->", "<!-- join:end -->"
# page -> (slot name, anchor the block goes before)
PAGES = {
    "index.html": ("home", '<section id="help"'),
    "cost/index.html": ("cost", "</main>"),
    "roads/index.html": ("roads", "</main>"),
    "field/index.html": ("field", "</main>"),
    "moves/index.html": ("moves", "</main>"),
    "uturns/index.html": ("uturns", "</main>"),
    "report/index.html": ("report", "</main>"),
}
BLOCK = re.compile(re.escape(START) + r".*?" + re.escape(END) + r"\n?", re.S)


def block(slot: str) -> str:
    return f'{START}<section data-join="{slot}"></section><script src="/join.js" defer></script>{END}\n'


def place(text: str, slot: str, anchor: str) -> str:
    text = BLOCK.sub("", text)
    if text.count(anchor) < 1:
        raise SystemExit(f"anchor not found: {anchor}")
    i = text.index(anchor)
    return text[:i] + block(slot) + text[i:]


def main() -> int:
    for rel, (slot, anchor) in PAGES.items():
        p = WEB / rel
        old = p.read_text(encoding="utf-8")
        new = place(old, slot, anchor)
        if new != old:
            p.write_text(new, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
