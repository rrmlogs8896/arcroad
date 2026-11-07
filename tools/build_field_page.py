"""Render web/field/index.html from data/field/*-results.json (deterministic; run before deploy).

Usage: python3 tools/build_field_page.py
"""

from __future__ import annotations

import glob
import html
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from site_nav import nav, reuse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIRS = {"ab": "A → B", "ba": "B → A"}
VERDICT = {"MATCH": "Matched the model", "SHORTER": "Much shorter than the model", "LONGER": "Longer than the model",
           "BETWEEN": "Differed from the model", "NO_MODEL": "No model route to compare",
           "REJECTED": "Rejected: not a crossing", "POOR_TRACK": "Rejected: gaps in the recording"}


def short_date(d):
    if not d:
        return ""
    y, m, dd = d.split("-")
    return f"{int(dd)} {['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][int(m) - 1]}"


def day_list(isos: list) -> str:
    """'1, 2, 3, 4 and 6 Nov 2026' when the days share a month, else each day with its month."""
    parts = [short_date(x) for x in isos]
    if len({x[:7] for x in isos}) == 1:
        nums = [p.split()[0] for p in parts]
        lead = ", ".join(nums[:-1]) + " and " + nums[-1] if len(nums) > 1 else nums[0]
        return f"{lead} {parts[-1].split()[1]} {isos[-1][:4]}"
    return (", ".join(parts[:-1]) + " and " + parts[-1] if len(parts) > 1 else parts[0]) + " " + isos[-1][:4]


def combine(days: list) -> dict:
    """All field days on one page: every pass keeps its own date; limits are listed once."""
    out = {"day": day_list([d["day"] for d in days]),
           "model": days[-1]["model"], "passes": [], "not_scored": [], "limitations": []}
    for d in days:
        out["passes"] += d["passes"]
        out["not_scored"] += [dict(x, date=d["day"]) for x in d["not_scored"]]
        out["limitations"] += [x for x in d["limitations"] if x not in out["limitations"]]
    return out


def km(m):
    return "—" if m is None else (f"{m / 1000:.2f} km" if m >= 1000 else f"{round(m)} m")


def mins(s):
    return "—" if s is None else f"{s / 60:.1f} min"


def render(day: dict) -> str:
    NAV = nav("../", "field/", True)
    e = html.escape
    rows = []
    for r in day["passes"]:
        if r["verdict"] in ("REJECTED", "POOR_TRACK"):
            continue
        lvl = "driven" if r["level"] == 1 else "candidate"
        rows.append(
            f'<tr class="{lvl}"><td>{e(r["id"])}</td><td>{e(short_date(r.get("date")))}</td><td>{DIRS.get(r["dir"], r["dir"])}</td>'
            f'<td class="n">{km(r.get("straight_m"))}</td><td class="n">{km(r.get("model_m"))}</td>'
            f'<td class="n"><b>{km(r["driven_m"])}</b></td><td class="n">{mins(r["seconds"])}</td>'
            f'<td>{e(VERDICT.get(r["verdict"], r["verdict"]))}</td><td>{e(r["label"])}</td>'
            f'<td>{e(r.get("kinds") or "")} · {e(r.get("tri_level") or "")}</td></tr>')
    rejected = [r for r in day["passes"] if r["verdict"] in ("REJECTED", "POOR_TRACK")]
    n_match = sum(r["verdict"] == "MATCH" for r in day["passes"])
    n_graded = sum(r["verdict"] in ("MATCH", "SHORTER", "LONGER", "BETWEEN") for r in day["passes"])
    places = sorted({r["id"] for r in day["passes"] if r["level"] == 1})
    # Always name the direction: "S08 B → A, S10 A → B" (7 Nov review: a shared "A → B" read as applying to all).
    ph = sorted({f"{r['id']} {DIRS.get(r['dir'], '')}".strip() for r in day["passes"] if r.get("posthoc_rule")})
    if not ph:
        posthoc_note = ""
    elif len(ph) == 1:
        posthoc_note = f" {ph[0]} counts only under a rule changed after its drive was seen; see the limits below."
    else:
        posthoc_note = (f" {', '.join(ph[:-1])} and {ph[-1]} count only under rules changed after their drives"
                        " were seen; see the limits below.")
    li = lambda xs: "".join(f"<li>{e(x)}</li>" for x in xs)  # noqa: E731
    ns = "".join(f'<li><b>{e(x["id"])}</b> ({e(short_date(x.get("date")))}): {e(x["why"])}</li>' for x in day["not_scored"])
    nr = "".join(f'<li><b>{e(r["id"])} {DIRS.get(r["dir"], "")}</b>: {e(r["reason"])}</li>' for r in rejected)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>arcroad · driven results, {e(day["day"])}</title>
<meta name="description" content="arcroad drove its modelled detours in Hyderabad. Every pass, matched or not, with the method and the limits.">
<link rel="canonical" href="https://arcroad.org/field/">
<meta property="og:type" content="website">
<meta property="og:site_name" content="arcroad">
<meta property="og:title" content="arcroad · driven results, {e(day["day"])}">
<meta property="og:description" content="arcroad drove its modelled detours in Hyderabad. Every pass, matched or not, with the method and the limits.">
<meta property="og:url" content="https://arcroad.org/field/">
<meta property="og:image" content="https://arcroad.org/og/field.jpg">
<meta property="og:image:type" content="image/jpeg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="arcroad: every pass we drove, matched or not">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://arcroad.org/og/field.jpg">
<style>
:root{{--bg:#0B0D10;--fg:#E8EAED;--mute:#9AA0A6;--line:#1C2026;--accent:#E8A87C;--ok:#7CC5A0}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 Inter,system-ui,-apple-system,sans-serif;-webkit-font-smoothing:antialiased}}
main{{max-width:980px;margin:0 auto;padding:48px 22px 80px}}a{{color:var(--accent)}}
.eyebrow{{font:500 12px/1.4 ui-monospace,SFMono-Regular,monospace;letter-spacing:.08em;text-transform:uppercase;color:var(--mute);margin:0 0 10px}}
h1{{font-size:clamp(28px,5vw,44px);line-height:1.12;margin:0 0 14px;font-weight:600;letter-spacing:-.01em}}
h2{{font-size:20px;margin:44px 0 10px;font-weight:600}}p.lead{{font-size:18px;color:#C9CDD2;max-width:720px}}
.stats{{display:flex;flex-wrap:wrap;gap:28px;margin:28px 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:20px 0}}
.stats b{{display:block;font:600 30px/1.1 ui-monospace,SFMono-Regular,monospace}}.stats span{{color:var(--mute);font-size:13px}}
.wrap{{overflow-x:auto;border:1px solid var(--line);border-radius:10px}}table{{border-collapse:collapse;width:100%;min-width:960px;font-size:14px}}td.n,td:nth-child(2),td:nth-child(3){{white-space:nowrap}}
th,td{{padding:10px 12px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}th{{color:var(--mute);font-weight:500;font-size:12px}}
td.n,th.n{{text-align:right;font-family:ui-monospace,SFMono-Regular,monospace;font-variant-numeric:tabular-nums}}
tr.driven td:first-child{{box-shadow:inset 3px 0 0 var(--ok)}}ul{{padding-left:20px}}li{{margin:4px 0}}
.note{{color:var(--mute);font-size:13px}}
.top{{display:flex;gap:16px;flex-wrap:wrap;font-size:14px;margin-bottom:28px}}.top a{{color:var(--mute);text-decoration:none}}.top a:hover{{color:var(--fg)}}
details.more{{margin-top:28px;border-top:1px solid var(--line)}}details.more summary{{cursor:pointer;padding:14px 0;color:var(--mute);font-size:14px}}details.more summary:hover{{color:var(--fg)}}
details.more h3{{font-size:15px;margin:18px 0 6px;font-weight:600}}details.more p,details.more li{{font-size:14px;color:#C9CDD2}}footer{{margin-top:56px;color:var(--mute);font-size:13px;border-top:1px solid var(--line);padding-top:18px}}
</style>
<meta name="theme-color" content="#0B0D10">
<meta name="color-scheme" content="dark">
<meta name="format-detection" content="telephone=no">
<style id="mobile-base">
/* Shared mobile and cross-browser base (Safari iOS, Chrome/Samsung Android, Firefox) */
html{{-webkit-text-size-adjust:100%;text-size-adjust:100%}}
body{{overflow-wrap:break-word;padding-left:env(safe-area-inset-left,0px);padding-right:env(safe-area-inset-right,0px)}}
a,button,summary,select,label{{-webkit-tap-highlight-color:rgba(232,168,124,.22);touch-action:manipulation}}
details>summary{{cursor:pointer;min-height:44px;box-sizing:border-box;align-items:center}}
details>summary::-webkit-details-marker{{display:none}}
input[type=range]{{min-height:36px;touch-action:pan-y;cursor:pointer}}
table{{font-variant-numeric:tabular-nums}}
.wrap,.scroll{{-webkit-overflow-scrolling:touch}}
img,svg,canvas,video{{max-width:100%}}
@media (max-width:720px){{
  input,select,textarea{{font-size:16px!important}}
  h1{{overflow-wrap:anywhere}}
  .top,header nav{{flex-wrap:nowrap!important;overflow-x:auto;scrollbar-width:none;white-space:nowrap;margin-left:0!important;max-width:100%}}
  .top::-webkit-scrollbar,header nav::-webkit-scrollbar,.presets::-webkit-scrollbar{{display:none}}
  .presets{{flex-wrap:nowrap!important;overflow-x:auto;scrollbar-width:none;white-space:nowrap}}
  .presets .reset{{margin-left:0!important}}
}}
@media (pointer:coarse){{nav a,.top a{{padding-block:10px;display:inline-block}} .srcbtn{{padding:10px 0}}}}
@media (prefers-reduced-motion:reduce){{*,*::before,*::after{{animation-duration:.01ms!important;animation-iteration-count:1!important;transition-duration:.01ms!important;scroll-behavior:auto!important}}}}
</style>
<link rel="stylesheet" href="../nav.css" id="sn-css">
<script src="../nav.js" defer id="sn-js"></script>
</head>
<body>
<main>
{NAV}
<p class="eyebrow">arcroad · Hyderabad · driven {e(day["day"])}</p>
<h1>We drove the detours the map predicted.</h1>
<p class="lead">{n_match} of {n_graded} comparable directions matched the model, within a tolerance fixed before the drive.{posthoc_note}</p>
<div class="stats"><div><b>{len(places)}</b><span>places now driven by arcroad</span></div><div><b>{n_match}/{n_graded}</b><span>directions matched the model</span></div><div><b>{len(rejected)}</b><span>passes rejected</span></div></div>
<h2>Every pass</h2>
<div class="wrap"><table>
<thead><tr><th>Place</th><th>Date</th><th>Direction</th><th class="n">Straight across</th><th class="n">Model</th><th class="n">Driven</th><th class="n">Time</th><th>Verdict</th><th>Evidence level</th><th>Evidence kinds</th></tr></thead>
<tbody>{"".join(rows)}</tbody></table></div>
<p class="note">Times include waits at signals and U-turn queues. <a href="../cost/">What would this cost you?</a></p>
<p class="note" id="codes">Place codes: S01 to S24 are the 24 places in arcroad&#39;s first field sample, drawn at random from the model before any drive (16 the model flagged as long detours, 8 ordinary controls, at least 500 m apart). T1 and T2 are two named stops on NH-65. A and B are the two sides of the median; A &rarr; B means driving from side A to the point straight across on side B.</p>
<details class="more"><summary>Rejected passes, places not scored, limits and how this was scored</summary>
<h3>Evidence kinds</h3><p>S a timed drive, P a usable photo at the place during the pass, R a repeat pass in the same direction. One kind is a candidate, two corroborated, three with a photo or an official record triangulated.</p>
<h3>Rejected passes</h3><ul>{nr or "<li>None.</li>"}</ul>
<h3>Visited but not scored</h3><ul>{ns}</ul>
<h3>Limits</h3><ul>{li(day["limitations"])}</ul>
<h3>How this was scored</h3>
<p>The match tolerance was written before the first drive and has never changed. Three counting rules were added or changed after a drive had been seen (pairing, 2 Nov; loops, 3 Nov; repeats, 5 Nov). Each is dated under Limits and was re-applied to every drive on file, and every pass that counts only because of one is marked. A drive matches when it is within the larger of 150 m or 25% of the model's distance. Raw recordings stay private; only these per-pass numbers are published.</p>
</details>
<footer>Map data © OpenStreetMap contributors (ODbL). Measurements by arcroad (ODbL). Model: {e(day["model"])}. No Google Maps data is used anywhere.{reuse("../")}</footer>
</main>
</body>
</html>
"""


def main():
    files = sorted(glob.glob(os.path.join(ROOT, "data", "field", "*-results.json")))
    if not files:
        raise SystemExit("no results files")
    days = []
    for f in files:
        with open(f, encoding="utf-8") as fh:
            days.append(json.load(fh))
    day = combine(days)
    out = os.path.join(ROOT, "web", "field")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(render(day))
    print("wrote web/field/index.html for", day["day"])


if __name__ == "__main__":
    main()
