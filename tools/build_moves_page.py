"""Build web/moves/index.html, arcroad's Cyberabad Moves 2026 entry, from a loopcost results file.

    python3 tools/build_moves_page.py RESULTS.json

Publishes only today's network (modelled, cross-checked by two open routers). No loop figure is published
until the route is confirmed (docs/PREREG-cyberabad-loop.md, change of 11 Nov 14:20).
"""

from __future__ import annotations

import html
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "web/moves/index.html"
MARK = '<meta name="arcroad:build" content="ar-000000000000">'  # replaced by the fingerprint tool before deploy


def km(m):
    return "—" if m is None else (f"{m / 1000:.2f} km" if m >= 1000 else f"{m:.0f} m")


def rows_html(rows):
    out = []
    for r in rows:
        flag = r["router_flag"]
        note = "Routers differ by more than 10%: to be driven before any use" if flag else "Agree within 10%"
        out.append(
            f'<tr{" class=flag" if flag else ""}><td>{html.escape(r["from"])}</td><td>{html.escape(r["to"])}</td>'
            f'<td class="n"><b>{km(r["today_m"])}</b></td><td class="n">{km(r.get("osrm_m"))}</td>'
            f'<td class="n">{km(r.get("valhalla_m"))}</td><td>{note}</td></tr>')
    return "".join(out)


def build(res):
    rows = res["rows"]
    agree = sum(not r["router_flag"] for r in rows)
    gates = ", ".join(f'{html.escape(g["name"])} ({g["snap_m"]:.0f} m)' for g in res["gates"])
    fetched = res["extract"]["fetched"][:10]
    commit = res["commit"][:7]
    return f"""<!doctype html>
<html lang="en">
<head>
{MARK}
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>arcroad · Measure the loop before it opens · Cyberabad Moves 2026</title>
<meta name="description" content="An open, pre-registered way to measure how much extra distance the proposed Hi-Tech City one-way loop adds, before it opens. arcroad's entry to the Cyberabad Moves 2026 Innovation Challenge.">
<link rel="canonical" href="https://arcroad.org/moves/">
<meta property="og:type" content="website">
<meta property="og:site_name" content="arcroad">
<meta property="og:title" content="Measure the loop before it opens">
<meta property="og:description" content="An open, pre-registered detour check for the proposed Hi-Tech City one-way loop.">
<meta property="og:url" content="https://arcroad.org/moves/">
<meta property="og:image" content="https://arcroad.org/og/moves.jpg">
<meta property="og:image:type" content="image/jpeg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="arcroad: measure the loop before it opens">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://arcroad.org/og/moves.jpg">
<meta name="theme-color" content="#0B0D10">
<meta name="color-scheme" content="dark">
<meta name="format-detection" content="telephone=no">
<style>
:root{{--bg:#0B0D10;--fg:#E8EAED;--mute:#9AA0A6;--line:#1C2026;--accent:#E8A87C;--ok:#7CC5A0}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 Inter,system-ui,-apple-system,sans-serif;-webkit-font-smoothing:antialiased;overflow-wrap:break-word}}
html{{-webkit-text-size-adjust:100%;text-size-adjust:100%}}
main{{max-width:980px;margin:0 auto;padding:48px 22px 80px}}a{{color:var(--accent)}}
.eyebrow{{font:500 12px/1.4 ui-monospace,SFMono-Regular,monospace;letter-spacing:.08em;text-transform:uppercase;color:var(--mute);margin:28px 0 10px}}
h1{{font-size:clamp(28px,5vw,44px);line-height:1.12;margin:0 0 14px;font-weight:600;letter-spacing:-.01em}}
h2{{font-size:20px;margin:44px 0 10px;font-weight:600}}p.lead{{font-size:18px;color:#C9CDD2;max-width:720px}}
p,li{{max-width:720px}}
.stats{{display:flex;flex-wrap:wrap;gap:28px;margin:28px 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:20px 0}}
.stats b{{display:block;font:600 30px/1.1 ui-monospace,SFMono-Regular,monospace}}.stats span{{color:var(--mute);font-size:13px}}
.wrap{{overflow-x:auto;-webkit-overflow-scrolling:touch;border:1px solid var(--line);border-radius:10px}}
table{{border-collapse:collapse;width:100%;min-width:760px;font-size:14px;font-variant-numeric:tabular-nums}}
th,td{{padding:10px 12px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}th{{color:var(--mute);font-weight:500;font-size:12px}}
td.n,th.n{{text-align:right;font-family:ui-monospace,SFMono-Regular,monospace;white-space:nowrap}}
tr.flag td:first-child{{box-shadow:inset 3px 0 0 var(--accent)}}
ol,ul{{padding-left:20px}}li{{margin:6px 0}}.note{{color:var(--mute);font-size:13px}}
.ask{{border:1px solid var(--line);border-radius:12px;padding:20px 22px;margin:28px 0}}.ask h2{{margin-top:0}}
details.more{{margin-top:28px;border-top:1px solid var(--line)}}details.more summary{{cursor:pointer;padding:14px 0;color:var(--mute);font-size:14px;min-height:44px}}
details.more p,details.more li{{font-size:14px;color:#C9CDD2}}
footer{{margin-top:56px;color:var(--mute);font-size:13px;border-top:1px solid var(--line);padding-top:18px}}
@media (prefers-reduced-motion:reduce){{*{{transition-duration:.01ms!important}}}}
</style>
<link rel="stylesheet" href="../nav.css" id="sn-css">
<script src="../nav.js" defer id="sn-js"></script>
</head>
<body>
<main>
<!-- nav:start --><nav aria-label="arcroad"></nav><!-- nav:end -->
<p class="eyebrow">arcroad · Cyberabad Moves 2026 · Citizens Innovation Challenge · Smart mobility and open data</p>
<h1>Measure the loop before it opens.</h1>
<p class="lead">Cyberabad Police have proposed turning the roads between Biodiversity Junction, IKEA, Mindspace, Knowledge City and Dallas Center into a one-way loop, and plan to judge it by vehicle speed and traffic density. One thing is not on that list: how much further each journey becomes. arcroad brings a ready, tested and open way to measure it, before the trial, during it and after.</p>
<div class="stats"><div><b>{len(rows)}</b><span>trips between five loop points, modelled on today's roads</span></div><div><b>{agree}/{len(rows)}</b><span>agree with two independent open routers within 10%</span></div><div><b>0</b><span>loop figures published until the route is confirmed</span></div></div>

<h2>The gap</h2>
<p>A one-way loop can make traffic flow faster and still make many trips longer: a trip that today runs against the loop's direction has to go round it. Speed and density measure the first. Nothing in the published plans measures the second. When the KBR Park one-way loop was made permanent in 2026, we could find no published before-and-after figures for distance or travel time.</p>
<p>The distance is the part a resident feels every day, in fuel, time and the extra kilometres buses and office shuttles run. It is also the part that open data can measure well.</p>

<h2>What we will measure</h2>
<ol>
<li><b>Driving distance</b> between every pair of loop points, on today's roads and on the loop as proposed, from OpenStreetMap with a published method.</li>
<li><b>Bus route length</b> for every TGSRTC route that uses a loop road against its direction, from the open GTFS feed on Open Data Telangana.</li>
<li><b>Before, during and after:</b> a baseline now, the same trips driven during the trial at the same hours, and again once it is permanent. Published whatever they show.</li>
</ol>
<p class="note">We make no claim about walking. OpenStreetMap's footpath and crossing data for Hyderabad is not complete enough to support one, so we leave it out rather than guess.</p>

<h2>Today's roads: the baseline</h2>
<p>Shortest legal driving route between the five loop points we could locate on OpenStreetMap, computed by arcroad's own code and checked against the public OSRM and Valhalla routers. These are modelled lengths, not yet driven.</p>
<div class="wrap"><table>
<thead><tr><th>From</th><th>To</th><th class="n">arcroad</th><th class="n">OSRM</th><th class="n">Valhalla</th><th>Check</th></tr></thead>
<tbody>{rows_html(rows)}</tbody></table></div>
<p class="note">Points and their distance to the main road each was placed on: {gates}. My Home Bhooja could not be found on OpenStreetMap under that name and is left out rather than guessed. OpenStreetMap extract fetched {fetched}; code at commit {commit}.</p>

<div class="ask">
<h2>What we ask of the city</h2>
<p>The proposed route, as the roads and the direction of travel, and the trial dates. With those, the loop figures for every pair above are computed the same day and published here with the method, the code and the limits. We will share the results with Cyberabad Traffic Police, SCSC and CMC before anyone else.</p>
</div>

<h2>Why the route has to come from the city</h2>
<p>On 11 November we tried to infer the loop from the reported list of landmarks. Our own pre-registered check failed: the inferred route doubled back on itself, so its results were withdrawn before they were shown anywhere. The map also shows the link between the Mindspace and Knowledge City corners as one-way in the opposite direction to the reported order. Any route we drew would be a guess, and a guess is not something to put in front of a city.</p>

<h2>Why it can be trusted</h2>
<ul>
<li><b>Written before it was run.</b> The question, the threshold for "longer" (at least 100 m and 10%), the hypothesis and the competing explanation were fixed in a dated pre-registration before any distance was computed. Every later change is dated and applied to every result.</li>
<li><b>Open.</b> OpenStreetMap data (ODbL), open routers, MIT-licensed code. Anyone can rerun it.</li>
<li><b>Checked against the road.</b> arcroad has already driven its modelled detours at six Hyderabad places: 8 of 8 directions matched the model. <a href="../field/">See every pass</a>.</li>
<li><b>Cheap to run.</b> A laptop, about three minutes, no paid data. The city could run it on any future change.</li>
</ul>

<details class="more"><summary>Method in detail</summary>
<p>Both networks are routed by arcroad's own shortest-path code on one OpenStreetMap extract: motorway to residential roads and their links, access=no and access=private excluded, one-way tags obeyed, turn restrictions not modelled. Loop points are located with OpenStreetMap's search and placed on the nearest main road at ground level (never on a flyover); each match is checked by a person. On the loop network, loop roads become one-way in the loop's direction across their full width, as the police describe, and nothing changes off the route. A pair counts as longer only if it grows by at least 100 m and 10%. The loop network must pass a check that no part of the route doubles back on itself, or no figure is published.</p>
<p>The competing explanation we test against: a loop can make trips longer but faster, by removing waiting at junctions. Distance alone does not settle that, so timed drives at the same hours before and during the trial are part of the plan.</p>
</details>

<footer>Team arcroad · <a href="mailto:hello@arcroad.org">hello@arcroad.org</a> · An independent, non-commercial civic project. Map data © OpenStreetMap contributors (ODbL). Measurements by arcroad (ODbL). No Google Maps data is used anywhere.</footer>
</main>
</body>
</html>
"""


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    res = json.loads(pathlib.Path(sys.argv[1]).expanduser().read_text())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    text = build(res)
    if OUT.exists():  # keep the build mark the fingerprint tool gave this page
        import re
        m = re.search(r'<meta name="arcroad:build" content="ar-[0-9a-f]{12}">', OUT.read_text())
        if m:
            text = text.replace(MARK, m.group(0), 1)
    OUT.write_text(text)
    print(f"wrote {OUT.relative_to(ROOT)}")
