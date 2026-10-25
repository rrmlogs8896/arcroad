"""Fail the build when a page's verification has gone stale.

Compliance is a CI concern, not a document somebody wrote once. Every page
making a legal, privacy or data claim carries a `data-verified` date. This
script fails when one is older than its allowance, which turns "we should
re-check that" into a red build somebody has to answer.

It cannot check whether a claim is still TRUE -- only a person reading the
primary source can do that. What it guarantees is that nobody can forget to
look.
"""

import datetime as dt
import pathlib
import re
import sys

# page glob -> how many days a verification is good for
ALLOWANCE = {
    "web/privacy.html": 90,
    "web/cookies.html": 90,
    "web/terms.html": 180,
    "web/index.html": 180,
}

TODAY = dt.date.today()
PATTERN = re.compile(r'data-verified="(\d{4}-\d{2}-\d{2})"')


def main() -> int:
    failures, checked = [], 0
    for rel, days in ALLOWANCE.items():
        p = pathlib.Path(rel)
        if not p.exists():
            continue  # page not built yet; its absence is not a failure
        m = PATTERN.search(p.read_text())
        if not m:
            failures.append(f"{rel}: no data-verified date on the page")
            continue
        checked += 1
        age = (TODAY - dt.date.fromisoformat(m.group(1))).days
        status = "stale" if age > days else "ok"
        print(f"  {rel:22s} verified {m.group(1)}  {age:>4}d  allowance {days:>3}d  {status}")
        if age > days:
            failures.append(
                f"{rel}: verified {age} days ago, allowance is {days}. "
                f"Re-check it against the primary source, then update the date."
            )

    print(f"\n{checked} page(s) checked")
    if failures:
        print("\nSTALE:")
        for f in failures:
            print("  -", f)
        print("\nA stale verification is a build failure, not a warning.")
        return 1
    print("All verifications current.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
