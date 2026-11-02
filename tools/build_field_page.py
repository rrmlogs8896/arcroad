"""Render web/field/index.html from data/field/*-results.json (deterministic; run before deploy).

Usage: python3 tools/build_field_page.py
"""

from __future__ import annotations

import glob
import html
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIRS = {"ab": "A → B", "ba": "B → A"}
VERDICT = {"MATCH": "Matched the model", "SHORTER": "Much shorter than the model", "LONGER": "Longer than the model",
           "BETWEEN": "Differed from the model", "NO_MODEL": "No model route to compare",
           "REJECTED": "Rejected: not a crossing", "POOR_TRACK": "Rejected: gaps in the recording"}


def km(m):
    return "—" if m is None else (f"{m / 1000:.2f} km" if m >= 1000 else f"{round(m)} m")


def mins(s):
    return "—" if s is None else f"{s / 60:.1f} min"


def render(day: dict) -> str:
    e = html.escape
    rows = []
    for r in day["passes"]:
        if r["verdict"] in ("REJECTED", "POOR_TRACK"):
            continue
        lvl = "driven" if r["level"] == 1 else "candidate"
        rows.append(
            f'<tr class="{lvl}"><td>{e(r["id"])}</td><td>{DIRS.get(r["dir"], r["dir"])}</td>'
            f'<td class="n">{km(r.get("straight_m"))}</td><td class="n">{km(r.get("model_m"))}</td>'
            f'<td class="n"><b>{km(r["driven_m"])}</b></td><td class="n">{mins(r["seconds"])}</td>'
            f'<td>{e(VERDICT.get(r["verdict"], r["verdict"]))}</td><td>{e(r["label"])}</td>'
            f'<td>{e(r.get("kinds") or "")} · {e(r.get("tri_level") or "")}</td></tr>')
    rejected = [r for r in day["passes"] if r["verdict"] in ("REJECTED", "POOR_TRACK")]
    n_match = sum(r["verdict"] == "MATCH" for r in day["passes"])
    n_graded = sum(r["verdict"] in ("MATCH", "SHORTER", "LONGER", "BETWEEN") for r in day["passes"])
    places = sorted({r["id"] for r in day["passes"] if r["level"] == 1})
    li = lambda xs: "".join(f"<li>{e(x)}</li>" for x in xs)  # noqa: E731
    ns = "".join(f'<li><b>{e(x["id"])}</b>: {e(x["why"])}</li>' for x in day["not_scored"])
    nr = "".join(f'<li><b>{e(r["id"])} {DIRS.get(r["dir"], "")}</b>: {e(r["reason"])}</li>' for r in rejected)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>arcroad · driven results, {e(day["day"])}</title>
<meta name="description" content="arcroad drove its modelled detours in Hyderabad. Every pass, matched or not, with the method and the limits.">
<style>
:root{{--bg:#0B0D10;--fg:#E8EAED;--mute:#9AA0A6;--line:#1C2026;--accent:#E8A87C;--ok:#7CC5A0}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 Inter,system-ui,-apple-system,sans-serif;-webkit-font-smoothing:antialiased}}
main{{max-width:980px;margin:0 auto;padding:48px 22px 80px}}a{{color:var(--accent)}}
.eyebrow{{font:500 12px/1.4 ui-monospace,SFMono-Regular,monospace;letter-spacing:.08em;text-transform:uppercase;color:var(--mute);margin:0 0 10px}}
h1{{font-size:clamp(28px,5vw,44px);line-height:1.12;margin:0 0 14px;font-weight:600;letter-spacing:-.01em}}
h2{{font-size:20px;margin:44px 0 10px;font-weight:600}}p.lead{{font-size:18px;color:#C9CDD2;max-width:720px}}
.stats{{display:flex;flex-wrap:wrap;gap:28px;margin:28px 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:20px 0}}
.stats b{{display:block;font:600 30px/1.1 ui-monospace,SFMono-Regular,monospace}}.stats span{{color:var(--mute);font-size:13px}}
.wrap{{overflow-x:auto;border:1px solid var(--line);border-radius:10px}}table{{border-collapse:collapse;width:100%;min-width:820px;font-size:14px}}
th,td{{padding:10px 12px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}th{{color:var(--mute);font-weight:500;font-size:12px}}
td.n,th.n{{text-align:right;font-family:ui-monospace,SFMono-Regular,monospace;font-variant-numeric:tabular-nums}}
tr.driven td:first-child{{box-shadow:inset 3px 0 0 var(--ok)}}ul{{padding-left:20px}}li{{margin:4px 0}}
.note{{color:var(--mute);font-size:13px}}
.top{{display:flex;gap:16px;flex-wrap:wrap;font-size:14px;margin-bottom:28px}}.top a{{color:var(--mute);text-decoration:none}}.top a:hover{{color:var(--fg)}}
details.more{{margin-top:28px;border-top:1px solid var(--line)}}details.more summary{{cursor:pointer;padding:14px 0;color:var(--mute);font-size:14px}}details.more summary:hover{{color:var(--fg)}}
details.more h3{{font-size:15px;margin:18px 0 6px;font-weight:600}}details.more p,details.more li{{font-size:14px;color:#C9CDD2}}footer{{margin-top:56px;color:var(--mute);font-size:13px;border-top:1px solid var(--line);padding-top:18px}}
</style>
</head>
<body>
<main>
<nav class="top"><a href="../">arcroad home</a><a href="../cost/">Your cost</a><a href="../roads/">Road costs</a><a href="../evidence/">Evidence</a><a href="../globe/">Globe</a></nav>
<p class="eyebrow">arcroad · Hyderabad · driven {e(day["day"])}</p>
<h1>We drove the detours the map predicted.</h1>
<p class="lead">{n_match} of {n_graded} comparable directions matched the model, within a tolerance fixed before the drive.</p>
<div class="stats"><div><b>{len(places)}</b><span>places now driven by arcroad</span></div><div><b>{n_match}/{n_graded}</b><span>directions matched the model</span></div><div><b>{len(rejected)}</b><span>passes rejected</span></div></div>
<h2>Every pass</h2>
<div class="wrap"><table>
<thead><tr><th>Place</th><th>Direction</th><th class="n">Straight across</th><th class="n">Model</th><th class="n">Driven</th><th class="n">Time</th><th>Verdict</th><th>Evidence level</th><th>Evidence kinds</th></tr></thead>
<tbody>{"".join(rows)}</tbody></table></div>
<p class="note">Times include waits at signals and U-turn queues. <a href="../cost/">What would this cost you?</a></p>
<details class="more"><summary>Rejected passes, places not scored, limits and how this was scored</summary>
<h3>Evidence kinds</h3><p>S a timed drive, P a usable photo at the place during the pass, R a repeat pass. One kind is a candidate, two corroborated, three with a photo or an official record triangulated.</p>
<h3>Rejected passes</h3><ul>{nr or "<li>None.</li>"}</ul>
<h3>Visited but not scored</h3><ul>{ns}</ul>
<h3>Limits</h3><ul>{li(day["limitations"])}</ul>
<h3>How this was scored</h3>
<p>Thresholds were written before the drive and not changed after seeing results. A drive matches when it is within the larger of 150 m or 25% of the model's distance. Raw recordings stay private; only these per-pass numbers are published.</p>
</details>
<footer>Map data © OpenStreetMap contributors (ODbL). Measurements by arcroad (ODbL). Model: {e(day["model"])}. No Google Maps data is used anywhere.</footer>
</main>
</body>
</html>
"""


def main():
    files = sorted(glob.glob(os.path.join(ROOT, "data", "field", "*-results.json")))
    if not files:
        raise SystemExit("no results files")
    with open(files[-1], encoding="utf-8") as fh:
        day = json.load(fh)
    out = os.path.join(ROOT, "web", "field")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(render(day))
    print("wrote web/field/index.html for", day["day"])


if __name__ == "__main__":
    main()
