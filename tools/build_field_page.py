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
MARK = '<meta name="arcroad:build" content="ar-000000000000">'  # replaced by the fingerprint tool before deploy
DIRS = {"ab": "A → B", "ba": "B → A"}
VERDICT = {"MATCH": "Matched the model", "SHORTER": "Much shorter than the model", "LONGER": "Longer than the model",
           "BETWEEN": "Differed from the model", "NO_MODEL": "No model route to compare",
           "REJECTED": "Rejected: not a crossing", "POOR_TRACK": "Rejected: gaps in the recording"}


def short_date(d):
    if not d:
        return ""
    _y, m, dd = d.split("-")
    return f"{int(dd)} {['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][int(m) - 1]}"


def day_list(isos: list) -> str:
    """'1, 2, 3, 4 and 6 Nov 2026' when the days share a month, else each day with its month."""
    parts = [short_date(x) for x in isos]
    if len({x[:7] for x in isos}) == 1:
        nums = [p.split()[0] for p in parts]
        lead = ", ".join(nums[:-1]) + " and " + nums[-1] if len(nums) > 1 else nums[0]
        return f"{lead} {parts[-1].split()[1]} {isos[-1][:4]}"
    return (", ".join(parts[:-1]) + " and " + parts[-1] if len(parts) > 1 else parts[0]) + " " + isos[-1][:4]


def out_of_scope() -> dict:
    """Places left out by the 8 Nov 2026 road-class rule (docs/PREREG-road-class-rule.md), id -> reason."""
    with open(os.path.join(ROOT, "web", "globe", "data", "places.json"), encoding="utf-8") as fh:
        d = json.load(fh)
    return {p["id"]: p.get("scope_reason", "out of scope") for p in (d.get("out_of_scope") or {}).get("places", [])}


def combine(days: list) -> dict:
    """All field days on one page: every pass keeps its own date; limits are listed once."""
    scope = out_of_scope()
    out = {"day": day_list([d["day"] for d in days]), "days": [d["day"] for d in days],
           "model": days[-1]["model"], "passes": [], "not_scored": [], "limitations": [], "out_of_scope": [], "photos": []}
    for d in days:
        out["passes"] += [r for r in d["passes"] if r["id"] not in scope]
        out["out_of_scope"] += [dict(r, reason=scope[r["id"]]) for r in d["passes"] if r["id"] in scope]
        out["not_scored"] += [dict(x, date=d["day"]) for x in d["not_scored"]]
        out["photos"] += d.get("photos", [])
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
    # Headline uses the strict count: matches under rules fixed before the drive (18 Nov 2026 decision).
    n_strict = sum(r["verdict"] == "MATCH" and not r.get("posthoc_rule") for r in day["passes"])
    n_graded = sum(r["verdict"] in ("MATCH", "SHORTER", "LONGER", "BETWEEN") for r in day["passes"])
    places = sorted({r["id"] for r in day["passes"] if r["level"] == 1})
    # Always name the direction: "S08 B → A, S10 A → B" (7 Nov review: a shared "A → B" read as applying to all).
    ph = sorted({f"{r['id']} {DIRS.get(r['dir'], '')}".strip() for r in day["passes"] if r.get("posthoc_rule")})
    if not ph:
        posthoc_note = ""
    else:
        names = ph[0] if len(ph) == 1 else f"{', '.join(ph[:-1])} and {ph[-1]}"
        judged = "was judged under a rule" if len(ph) == 1 else "were judged under rules"
        posthoc_note = (f" {names} {judged} changed after the drive was seen; see the limits below.")
    if n_match == n_graded:
        lead_main = (f"All {n_graded} comparable directions matched the model, and none failed."
                     f" {n_strict} of them were judged under the rules and tolerance fixed before the drive.")
    else:
        lead_main = (f"{n_match} of {n_graded} comparable directions matched the model;"
                     f" {n_strict} of them under the rules and tolerance fixed before the drive.")
    li = lambda xs: "".join(f"<li>{e(x)}</li>" for x in xs)  # noqa: E731
    eff = {}
    effp = os.path.join(ROOT, "data", "field", "effort.json")
    if os.path.exists(effp):
        with open(effp, encoding="utf-8") as fh:
            eff = json.load(fh)
    effort = ""
    if eff:
        drives = eff["drives"]
        km_all = sum(x["km"] for x in drives)
        km_gps = sum(x["km"] for x in drives if x["how"] == "GPS") + sum(x.get("gps_km", 0) for x in drives if x["how"] == "GPS and photos")
        lo = round(km_all / eff["kmpl_high"] * eff["petrol_inr_per_l"], -2)
        hi = round(km_all / eff["kmpl_low"] * eff["petrol_inr_per_l"], -2)
        tries = len(day["passes"]) + len(day.get("not_scored", []))
        ddays = len({x["date"] for x in drives})
        cells = [(str(ddays), "days of driving"), (str(len(places)), "places driven"),
                 (str(tries), "crossing attempts, including the ones that did not count"),
                 (f"{int(km_all)}+ km", f"driven, at least ({int(km_gps)} km on GPS)"),
                 (f"{eff['hours_recorded']}+ h", "of recorded driving"),
                 (f"₹{int(lo):,} to ₹{int(hi):,}", "fuel, estimated"),
                 (f"{eff['photos_labelled'] + eff['photos_reviewed']:,}", "photos taken on the drives"),
                 (str(eff["changes_saved"]), f"changes saved to the site since {eff['since']}")]
        crow = []
        ctot_lo = ctot_hi = 0
        for c in eff.get("costs", []):
            if "inr" in c:
                a = b = c["inr"]
            elif "lo" in c:
                a, b = c["lo"], c["hi"]
            else:
                a, b = int(lo), int(hi)
            ctot_lo += a
            ctot_hi += b
            amt = f"₹{a:,}" if a == b else f"₹{a:,} to ₹{b:,}"
            crow.append(f'<li><b>{e(amt)}</b>: {e(c["item"])} ({e(c["basis"])})</li>')
        costs_html = (f'<h3>What it has cost so far</h3><p class="note">{e(eff.get("cost_period", ""))}, paid personally.</p>'
                      f'<div class="stats"><div><b>₹{round(ctot_lo, -2):,.0f} to ₹{round(ctot_hi, -2):,.0f}</b><span>self-funded so far</span></div></div>'
                      f'<ul>{"".join(crow)}</ul><p class="note">{e(eff.get("costs_share_note", ""))} {e(eff.get("costs_not_counted", ""))}</p>') if eff.get("costs") else ""
        effort = ('<h2>The work behind these numbers</h2><div class="stats">'
                  + "".join(f"<div><b>{e(v)}</b><span>{e(k)}</span></div>" for v, k in cells) + "</div>"
                  + '<h3>The drives</h3><p class="note">13 days of driving: one in late October and 12 in November 2026, including ordinary trips with planned checks along the way.</p>'
                  + costs_html
                  + f'<p class="note">{e(eff["funding"])} {e(eff["method"])} Petrol at ₹{eff["petrol_inr_per_l"]} a litre ({e(eff["petrol_date"])}). Updated {e(short_date(eff["updated"]))} {eff["updated"][:4]}.</p>')
    hot = ""
    hp = os.path.join(ROOT, "data", "field", "hotspots.json")
    if os.path.exists(hp):
        with open(hp, encoding="utf-8") as fh:
            hj = json.load(fh)
        rows = "".join(
            f'<li><b>{e(r["place"])}</b>: {r["minutes"]:g} min crawling over {r["metres"]:,} m,'
            f' about {r["metres"] / 1000 / (r["minutes"] / 60):.0f} km/h.</li>'
            for r in hj["hotspots"])
        hot = (f'<h2>Where the {e(short_date(hj["date"]))} drive slowed down</h2><p>Measured on the drive.</p><ul>{rows}</ul><p class="note">{e(hj["note"])}</p>')
    ns = "".join(f'<li><b>{e(x["id"])}</b> ({e(short_date(x.get("date")))}): {e(x["why"])}</li>' for x in day["not_scored"])
    oos = "".join(f'<li><b>{e(r["id"])} {DIRS.get(r["dir"], "")}</b> ({e(short_date(r.get("date")))}): driven {km(r["driven_m"])}'
                  f' against a model of {km(r.get("model_m"))}; {e(r["reason"])}, not counted.</li>'
                  for r in day.get("out_of_scope", []))
    figs = "".join(f'<figure><img src="{e(p["src"])}" srcset="{e(p["src"][:-4])}-640.jpg 640w, {e(p["src"])} 1280w" sizes="(max-width: 700px) 100vw, 470px"'
                   f' alt="{e(p["alt"])}" width="{p["w"]}" height="{p["h"]}" loading="lazy" decoding="async">'
                   f'<figcaption>{e(p["caption"])}</figcaption></figure>' for p in day.get("photos", []))
    photos = (f'<h2>Photos from the drives</h2><div class="figs">{figs}</div>'
              '<p class="note">Photos, not renders. Number plates, faces and phone numbers are blurred; the dashboard is cropped out.</p>') if figs else ""
    nr = "".join(f'<li><b>{e(r["id"])} {DIRS.get(r["dir"], "")}</b>: {e(r["reason"])}</li>' for r in rejected)
    return f"""<!doctype html>
<html lang="en">
<head>
{MARK}
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
:root{{--bg:#0B0D10;--fg:#E8EAED;--mute:#9AA0A6;--line:#1C2026;--accent:#E8A87C;--ok:#7CC5A0}}/* art1q-oklch */@supports (color:oklch(0% 0 0)){{:root{{--bg:oklch(15.82% 0.0072 258.37);--fg:oklch(93.64% 0.0046 258.33);--mute:oklch(70.28% 0.0111 247.99);--line:oklch(24.21% 0.0129 258.37);--accent:oklch(78.23% 0.0957 55.34)}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 Inter,system-ui,-apple-system,sans-serif;}}
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
.figs{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}}figure{{margin:0}}figure img{{display:block;width:100%;height:auto;border-radius:10px;border:1px solid var(--line)}}figcaption{{color:var(--mute);font-size:13px;margin-top:8px}}
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
<p class="lead">{lead_main}{posthoc_note}</p>
<div class="stats"><div><b>{len(places)}</b><span>places now driven by arcroad</span></div><div><b>{n_match}/{n_graded}</b><span>matched the model; {n_strict} of them under rules fixed before the drive</span></div><div><b>{len(rejected)}</b><span>passes rejected</span></div></div>
<h2>Every pass</h2>
<div class="wrap"><table>
<thead><tr><th>Place</th><th>Date</th><th>Direction</th><th class="n">Straight across</th><th class="n">Model</th><th class="n">Driven</th><th class="n">Time</th><th>Verdict</th><th>Evidence level</th><th>Evidence kinds</th></tr></thead>
<tbody>{"".join(rows)}</tbody></table></div>
<p class="note">Times include waits at signals and U-turn queues. <a href="../cost/">What would this cost you?</a></p>
{photos}
{effort}
{hot}
<p class="note" id="codes">Place codes: S01 to S24 are the 24 places in arcroad&#39;s first field sample, drawn at random from the model before any drive (16 the model flagged as long detours, 8 ordinary controls, at least 500 m apart). S23 and S24 are on the Outer Ring Road and have been left out since 8 Nov 2026, because turning round on an expressway needs an interchange by design. T1 and T2 are two named stops on NH-65. A and B are the two sides of the median; A &rarr; B means driving from side A to the point straight across on side B.</p>
<details class="more"><summary>Rejected passes, places not scored, limits and how this was scored</summary>
<h3>Evidence kinds</h3><p>S a timed drive, P a usable photo at the place during the pass, R a repeat pass in the same direction. One kind is a candidate, two corroborated, three with a photo or an official record triangulated.</p>
<h3>Outside scope since 8 Nov 2026</h3><ul>{oos or "<li>None.</li>"}</ul>
<h3>Rejected passes</h3><ul>{nr or "<li>None.</li>"}</ul>
<h3>Visited but not scored</h3><ul>{ns}</ul>
<h3>Limits</h3><ul>{li(day["limitations"])}</ul>
<h3>How this was scored</h3>
<p>The match tolerance was written before the first drive and has never changed. Four rules were added or changed after a drive had been seen (pairing, 2 Nov; loops, 3 Nov; repeats, 5 Nov; road class, 8 Nov, which leaves motorways out). Each is dated under Limits and was re-applied to every drive on file, and every pass that counts only because of one is marked. A drive matches when it is within the larger of 150 m or 25% of the model's distance. Raw recordings stay private; only these per-pass numbers are published.</p>
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
    path = os.path.join(out, "index.html")
    text = render(day)
    if os.path.exists(path):  # keep the build mark the fingerprint tool gave this page
        import re
        with open(path, encoding="utf-8") as fh:
            m = re.search(r'<meta name="arcroad:build" content="ar-[0-9a-f]{12}">', fh.read())
        if m:
            text = text.replace(MARK, m.group(0), 1)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    print("wrote web/field/index.html for", day["day"])


if __name__ == "__main__":
    main()
