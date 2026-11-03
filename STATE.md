# arcroad — STATE

> **3 Nov 2026 — wrong-way riding (PR, this change):** evidence page gains three sources for the "Wrong-side driving" lesson (Mohanty & Bhushan 2026: most wrong-way movements at Indian crash sites intentional, mostly 2W/3W, to save distance; young riders: a far U-turn makes it feel easier; MoRTH series: wrong-side deaths 8,764 → 9,432, 2018–2023) and states arcroad never counts it per place or links a crash to a road feature. /drive/ gets a short "The shortcut against traffic" section linking there. Draft docs/METHOD-street-counts.md (not live): two-counter volunteer tallies of wrong-way vehicles and people crossing on foot, with a pre-registered place-vs-control comparison; the only route by which foot-overbridge/underpass options could ever appear.

> **3 Nov 2026 — Dive into 3D + signal-free fix (PR, this change):** /drive/ gets a **Dive into 3D** button (full screen via the Fullscreen API with a full-window CSS fallback for iPhone; drag to look around in any view, eases back to the road after 2.5 s; Exit 3D button and Esc), deep links from the home films (?dive=1 pulses the button and scrolls to the stage — the browser needs a tap to go full screen; ?place=S12; ?fix=auto opens the fixes on Auto; ?light=night|day), and a fifth fix, **A signal-free U-turn with a bay** (U-turn-only opening ~300 m away with a loon; US J-turn / RCUT, FHWA proven safety countermeasure, Missouri study −35% crashes, −54% injury crashes, FHWA-HRT-17-082; notes IRC:62 keeps openings to intersections). Home teaser link reads "Dive into 3D →" and each film opens its matching scene. Pedestrian FOB/underpass options declined for now (AGENTS.md: nothing about walking) pending a measured crossing-count method.

> **3 Nov 2026 — home films (PR, this change):** the home teaser plays six films, never the same twice in a row, starting on a random one each visit; nothing is stored (test_home_films.py checks no storage APIs, all five sizes and a poster per film, every file under the Pages 25 MiB limit). Films (tools/films/, rendered offline frame by frame at 3840×2160, encoded 480/720/1080/1440/2160 by encode.sh): **drive** (the /drive/ scene, re-rendered at 4K), **night** (S12, 1.95 km to cross 17 m, after dark as driven 2 Nov; drawn level), **orbit** (dot globe from Natural Earth land via world-atlas, 29 cities, down to S18), **thread** (the S18 a→b route drawn as one line of light, 0 → 1,580 m, then 13 m), **blueprint** (nearer U-turn 410 m, signal 27 m, underpass 230 m: lengths measured on the same drawing as /drive/, "illustration, not a design"), **timelapse** (one day on S18, then a year of crossing: 818 km, 65 h, ₹1,901 two-wheeler fuel, same inputs as ticker.js). Every on-screen number is measured or derived (sources in films.js header). Teaser widened to the 1,068 px content column; size picked from box width × screen density, one step sharper on a fast link, smallest on slow links, none under reduced motion or data saver; per-film caption and link (orbit → globe, blueprint → /drive/#fix, timelapse → cost). Old preview-*.mp4 removed. 67 MB of media in the repo.

> **3 Nov 2026 — v0.5 drive modes (PR, this change):** LIVE 92c212be (v0.4 solutions, deployed 10:53 IST); rollback 8e42686c. /drive/ gets: a **place picker** (driven, matched passes only: S18 both ways, S12 north→south after dark; the other 22 Hyderabad places listed disabled as "not driven yet" with a Volunteer link; page text, pins, result card, facts and method notes follow the place; S12 notes that it is drawn level though the real road is a flyover; its other direction says "not driven yet", no modelled figure); **Day / Night** (same road and clock; sodium lamps with road pools, lit windows, head and tail lights as one point cloud each, own headlight beam; S12 opens at night because it was driven at night); **High-beam glare** (night, driver's view: veil from the CIE 146:2002 young-eye term Lveil = 10·E/θ², two 30,000 cd lamps, same equation as /roads/glare/, labelled an illustration); **fixes play by themselves** in random order every 9 s when opened from "What could fix this" (an Auto toggle in the tabs; choosing an option or moving the slider stops it; the cards below still open one option). Bug fixed on the way: the Back and Auto buttons in the option tabs also fired the option handler (SOL.k = null, a console error). New test tests/test_drive_places.py ties every offered pass to data/field/*-results.json.

> **3 Nov 2026 00:21 IST — v0.2 LIVE.** Production e8466501 (main e0318b5, PR #48). Rollback: ee5f8a1f (street search). Preview 0b3de616 checked by Rohit on his phone. In it: write to the people responsible (officials directory, hi/te drafts), glare drive, report-a-change form, headline tied to driven place S18 with its selection rule, per-direction calculator links, declared scorer change (S12 counted, disclosed). Not yet on the site: S12 as a 4th driven place (needs the field page rebuild).

> **3 Nov 2026 10:30 IST — LIVE 8e42686c** (S12 fourth place); rollback 0cae9efd. **v0.4 solutions (this change):** /drive/ gets "What could fix this": the same 3D street switches to a dark blueprint view and transforms per option. 1 a nearer U-turn opening with a live slider (detour = the route length on the drawing), 2 a signal-controlled opening at the place (signal heads cycling), 3 a U-turn underpass (x-ray road, ghost box and ramps, route dips under), 4 why not a gap everywhere (pulsing conflict rings). Every option: guidance citation (IRC:62, IRC:93, IRC:SP:87; IIT course text for 500 m; directional-opening crash research abroad), one-line trade-off, "illustration, not a design", road owner named, link to the letter kit. Opening the median is now rebuildable (buildMedian(gaps)); route(L) lane-change length scales for short U-turns. Sources still to read in full before any figure moves from the drawing into a claim.

> **3 Nov 2026 10:15 IST — LIVE 0cae9efd** (nav v2, help, HD preview; main 10022c2); rollback 94e5b02d. **S12 (this change):** 2 Nov night GPX (from Rohit's phone, kept private, not in git) scored with the amended pairing rule: S12 A→B 1,951 m in 245 s vs model 2,028.9 m (places.json; the 2,031.1 in the field-day sample CSV was a different export) = MATCH, level 1, candidate; S06 A→B 10.8 m < 36.9 m straight = REJECTED (pair runs along NH-65, geometry review open). data/field/2026-11-02-results.json; field page now combines all days with a Date column and states the post-hoc rule in its lead; globe shows each place's own drive date and S12's note; home counts 4 places / 6 of 6. Open: Cloudflare Email Address Obfuscation is on for arcroad.org (Rohit to switch off).

> **3 Nov 2026 — nav v2 + help (PR, this change):** one menu built by tools/site_nav.py on every page (the field builder imports it): arcroad · Drive it · Findings ▾ · Your cost ▾ · Take part ▾ · Help, sub-pages with one-line descriptions; desktop panel on hover/focus/click (no dimming), phones slide sub-links into the same row; Escape and outside click close. New /help/ page (contact, corrections, report, accessibility, privacy facts checked against the code). hello@arcroad.org live (Cloudflare Email Routing, 3 Nov) and on the home page. Razorpay "Support arcroad" button built but OFF (SUPPORT_URL = None) until the payment page exists and Razorpay confirms in writing that optional support for a free information site is allowed; overrides the 16 Nov rule for arcroad by Rohit's choice (Web Analytics is off here, so that rule had no data for arcroad).

> **3 Nov 2026 09:48 IST — LIVE 94e5b02d** (main 133db33, PR #53, yearly S18 cost on the home page); rollback dacd9533.

> **3 Nov 2026 09:45 IST — v0.3 polish LIVE** (production dacd9533, main b9a425a, PR #52; rollback 3f46de04). **Ticker (this change):** supersedes branch v03-ticker. Shipped as a static "a year at this rate" figure, not a running counter "since 1 January": nobody has measured how long the crossing has been closed, and a running cost counter sits close to the Art 1c red line on counters. Fuel figures now match the cost calculator (50 / 16 km a litre). Open: the kit and globe still use 45 / 15 km a litre, so the site carries two fuel-economy sets; unify as a declared method change (needs Rohit's yes).

> **3 Nov 2026 — v0.3 polish (PR, this change):** one nav on every page (home link on the globe, cost, access and act; current page marked); home-page drive preview (self-rendered 11 s loop, 0.9 MB, poster first, plays only when visible, never under reduced motion or data saver); tighter copy on the home and drive intros (no fact or caveat removed); Google Fonts replaced by self-hosted Inter and JetBrains Mono (OFL), so the site makes no third-party font requests. Still waiting on inputs: S12 4th-place field rebuild (needs the public-safe pass summary from the iMac), S06/S11 pairing geometry and map-lag list (model data), ticker (Rohit's go), hello@arcroad.org (Rohit sets up routing).

> **3 Nov 2026 09:30 IST — /drive/ LIVE.** Production 3f46de04 (main 07d17de, PR #50). Rollback: e8466501 (v0.2). /drive/ added: immersive 3D ride of the S18 detour (both directions), distances and clock from data/field/2026-11-01-results.json, road drawn straight at driven length (OSM geometry is a v1.1 swap), made-up traffic matched to each pass's average speed, no walking claim. Open check (rule 4): the S18 b→a 692 s pass needs the personal-stop check before more is built on it.

Read this first; it replaces reconstructing status from the history. Update it in
the same commit as any change that makes it wrong. Longer history and decisions
live in the ledger (Drive: Anthropic / Hyderabad Mobility Atlas, Doc 03).

Last updated: 1 Nov 2026.

## Where things stand

- **Site:** arcroad.org on Cloudflare. Nothing modelled is published as a
  finding: every Detour Index value is a **candidate** until the drive below.
- **Hyderabad model:** the 25 Oct extract (v08 export) is the current model.
- **Multi-city:** all 29 cities (21 state/UT capitals, 8 hill capitals
  excluded with reasons) collected green with detour on 28 Oct, run
  40637057361 (`multicity.yml`), wall 40 min at 4 in parallel. Raised to 6 in
  parallel (PR #11); go to 8 only after a green run at 6.

## The one blocker: Phase 2b, ground truth

Nothing publishes until a driven track confirms or refutes the model. Field
Day 1 (west corridor, 26 stops: 2 photo targets + 24 crossings, seed 20261031)
is planned for the week of 28 Oct.

- Stops: `data/field/field_day_1_stops.json`.
- Scoring: `pipeline/groundtruth.py`, run with `tools/score_drive.py`.
- The gate (MATCH / SHORTER / LONGER / BETWEEN / NOT_DRIVEN / POOR_TRACK) and
  its hypothesis vs competing explanation are written in the module docstring,
  **before** any drive was scored. Do not change them after seeing results.
- Raw GPX never enters this repo (`.gitignore`); only per-stop numbers leave
  the scoring step.
- Still needed before scoring: the model's A -> B `network_m` for each stop,
  exported from v08 as `id,network_m` and kept off the field page.

## Remote verification, 31 Oct to 1 Nov 2026 (notebook v02, results in Drive)

- 96 checks (24 flagged stops + 24 generated controls, both directions).
- Public OSM traces: no passes anywhere. Microsoft imagery and Overture: failed to load
  (notebook bugs; Overture geometry must be read back with `ST_AsWKB`).
- Mapillary: 25 "SHORTER" passes, all physically impossible (3-21 m "driven" against
  13-58 m straight). Cause **B-15**: `find_pass` took "nearer to B" for "at B", so a car
  on one carriageway, with A and B offset along the road, made a false pass. Fixed: a
  pass must come within `END_REACH_M` (10 m) of both points, and callers can veto a side
  with `accept` (the notebook checks the sample sits on side B's carriageway in the
  graph). Added after seeing the run, as a bug fix that can only remove passes.
- Net: zero independent confirmations. Every value stays a **candidate**.
- Rohit is driving 8 stops (S04, S01, S24, S23, S11, S12, S18, S16) on 1 Nov; those
  drives also measure how often the fixed remote check agrees with a real drive.

## Next, in order

1. Score Field Day 1 when the track arrives; publish nothing until the
   results are reviewed against the gate.
2. NH-65 Vijayawada baseline capture: the pre-works state disappears when
   works start in January.
3. B-08: the v1.1 street-level probe slices `TARGETS[:5]` and skips the
   controls. Move the probe logic into `pipeline/` with a test (the notebook
   is presentation only), then fix.
4. Mapillary probe: the query returned zero even for London; retry with the
   `Authorization: OAuth` header.
5. Performance budget and viewport/a11y checks in CI.
6. Next multi-city run at 6 in parallel; record its wall time here.

## Decisions (Claude API features, 28 Oct 2026)

Recorded in "arcroad × Claude API" (Claude Docs). Claude handles language
only; every measured number stays in code.

- Retention: the visitor chooses 3, 12 or 24 months (12 pre-selected); never
  beyond 24; the delete code works at any time.
- Display: a point's total shows from 5 answers; breakdowns and themes from 10.
- Language: the visitor picks; English and Telugu first, each city's language
  added at that city's launch after a fluent reader checks the templates.
- Spending: one shared USD 100/month across Rohit's projects, funded by the
  Max plan's monthly API credit (auto-reload off, so requests stop at zero);
  each project's Worker cap sits inside it.

## Build backlog from the 1 Nov 2026 field day (Rohit approved "add them to the build")
1. Ground-truth lock: every driven spot becomes a fixed CI fixture (MATCH/SHORTER/LONGER + driven distance); a model change that flips one fails the build.
2. Evidence: driven spots shown as level 1 "Driven by arcroad" with date; model-vs-driven gap used to correct similar spots, labelled as estimate.
3. Commute campaign: scheduled morning message (Mon-Fri 07:47 IST) batches 4 spots per leg; D1-D2 cover the remaining 16 of 24; later batches added as "QUEUE D<n>" lines in Drive doc "arcroad commute drives", including no-detour control spots (rule 5).
4. Potholes: 100 Hz accelerometer + GPS -> speed-normalised vertical-jolt events; pothole vs speed-breaker classifier; candidate until a second pass or photo; routed to the road owner (NHAI / ORR operator / corporation).
5. Immersive detour ride (v1 shipped 3 Nov 2026 at /drive/, S18 instead of S01 because S01 did not pass the 10 m gate; the end card drops "walk across" per the never-claim rule): driver's-eye 3D replay of a real drive (GPS path + timing + bumps), procedural original vehicles (trucks, buses, autos, two-wheelers), road rebuilt from photos as reference only (no faces/plates/brands shown); end card with distance, time, fuel vs "walk across in 15 s"; first prototype S01 Patancheru.
6. Photo pipeline: EXIF (time, GPS, heading, altitude) read in place on the iMac; originals private; web copies ~200 KB with faces/plates blurred and metadata stripped.
7. Colab: read secrets in the first cell while Rohit is present (v04 Mapillary step timed out on a locked screen).
8. Claude's own ideas: proposed 2 Nov 2026 after the first commute recording; Rohit approved "all that is necessary" (Claude's call). Order, after v0.2 goes live:
   a. Drop-and-forget drive uploads (smaller Sensor Logger export: Location, Barometer, Accelerometer, Gravity, Gyroscope; processed on the iMac; one short message afterwards).
   b. NH-65 before/after: commute drives are the baseline before the January works (time-limited).
   c. Measured time cost per stretch and time of day (feeds the cost calculator; Patancheru crawl 2 Nov: ~300 m in 4 min).
   d. Detour minutes on driven places (queues included), beside the model distance.
   e. Wait-time map: stops over 15 s split into signal waits and jams.
   f. Waterlogging watch: barometer low points (2 Nov: a ~13 m dip on the Isnapur-Patancheru stretch) + dated rain reports.
   g. Road roughness map once the phone is mounted; feeds the letters.
   h. Private weekly commute card (later, shareable pattern once volunteers join).
9. Further ideas, all approved by Rohit 2 Nov 2026 (19:06 IST), after items 8a-8h:
   a. Places near schools (OSM schools within 500 m of a long-detour place; the letter says so).
   b. Bus stops with no way across (facing stops on a divided road, no crossing between them).
   c. Ambulance minutes (detour as extra minutes to the nearest hospital; reuses the hospital module).
   d. Letters-sent count (opt-in, anonymous) and a 30-day no-reply prompt to the RTI request.
   e. One-page constituency report per MLA seat (places, detours, cost, letters sent).
   f. "Report a dark streetlight" (reuses /report/; pairs with the glare experience).
   g. Embeddable place card for journalists (always shows date and evidence level).
   Drive 2 Nov 2026 17:48-18:45 IST Isnapur -> Hafeezpet, 20.4 km, avg ~21 km/h; no crossings driven (pass-by only at S01, S04, S06, S11, S12); S11 needs a deliberate U-turn check; motion sensors unusable (phone handled); scorer pass-by fix 6a3199a.

## Field day 1 lessons (1 Nov 2026; detail in the private field report, not in git)

- **Confirmed passes:** T2 (both directions), S16, S18 (both directions), S23, S24.
- **Not confirmed under the fixed rule:** S01 and S04. The B side was reached within 15 m, but the rule is 10 m. This is kept as is; the threshold is not changed.
- **Not recorded:** S11 and S12. Both apps stopped at 18:19 and restarted at 19:36.
- **Road class:** S23 and S24 are on the ORR mainline (access-controlled). Their detours go via an interchange by design. Tag road class before scoring, and never present access-controlled detours as civic failures.
- **Surface:** the repeat-confirmed rough stretch is on NH-65 Isnapur–Chitkul (about 2 km, 3 passes). It needs photos and a pass with the phone mounted. A phone handheld for photos inflates jolts.
- **Behaviour:** a hard-brake hotspot near the NH-65 Muthangi U-turn repeats across 31 Oct and 1 Nov (3 passes). It is the first behaviour candidate confirmed by repeat passes.
- **Fieldkit fixes to make, with tests:**
  - photo EXIF fallback when exiftool is missing;
  - try both pass directions and keep every pass;
  - one primary GPS source with gap fill only (two interleaved sources make false brakes);
  - swerve v2 with smoothing and event spacing, declared as a method change; the 1 Nov swerves are not used;
  - flag passes that contain a personal stop;
  - tag road class.
- **Next drives:**
  - mount the phone;
  - Sensor Logger at 50 Hz, with the camera, orientation, magnetometer and uncalibrated sensors off;
  - a fresh GPX file per day;
  - use the annotation tap for potholes and barricades.

## Field day 1 published (2 Nov 2026)

- **Scoring:** `pipeline/fieldscore.py` (tests in `tests/test_fieldscore.py`) scores public-safe pass summaries with the unchanged groundtruth thresholds, evidence levels and triangulation kinds.
- **Results:** `data/field/2026-11-01-results.json`.
- **Public page:** `web/field/` (built by `tools/build_field_page.py`).
- **Globe:** `web/globe/` is now in the repo, with the driven places marked.
- **What the drive showed:**
  - 5 of 5 comparable directions matched the model: S16 B→A, S18 both directions, S24 both directions. That is 3 places at evidence level 1.
  - S18 B→A is corroborated (S+P). Every other drive so far is a single kind (candidate) until repeated.
- **Gate:** the AGENTS.md gate ("no absolute value until a modelled route is checked against a driven one") is now met for the model as a whole. Candidate values may be shown labelled as candidates, per docs/METHOD-evidence.md.
- **Still open:**
  - tag road class (S23 and S24 are ORR mainline);
  - repeat passes on other days;
  - the site is still noindex until the home page copy moves off "staging".

- **Notebook v05** (2 Nov 2026): notebooks/arcroad_Verify_Remote_v05.ipynb. Changes from v04:
  - secrets are read in cell 1;
  - Mapillary sanity rules: reject passes shorter than the straight line or with no heading reversal, and cap the match radius at half the A–B gap;
  - Mapillary U-turn signs (Evidence E) and OSM turn restrictions (F) added;
  - own drives read in from data/field;
  - road class per place;
  - KartaView stub, off by default.
  - Run 2 Nov 2026 as v05.1 (results 09:17Z), scored in data/verify/2026-11-02-v05_1/SCORE.md: controls 46/48 clean (C01 placement), all 5 driven directions MATCH, S03 and S20 show no meaningful detour, outside evidence empty this run.
- **Street search** (2 Nov 2026): web/search.js + web/search.css on the home page and the globe list; road and area names from OpenStreetMap via tools/road_names.py (run on any machine with internet; writes web/globe/data/road_names.json); results link to the globe (?spot=) and the cost calculator (prefilled km, and minutes for driven places); no match points to Volunteer.
- **v0.2 "Write to the people responsible"** (2 Nov 2026, branch v02-write, preview only): letter, email (To: owning office, CC: regional head, traffic police, MLA, MP), WhatsApp/X share, draft Hindi/Telugu, /report/ page. Officials directory data/officials/2026-11-02.json (official sources only, each dated; built by tools/build_kit_data.py into web/kit/pairs.js; entries named on official pages without a mailbox are named, not addressed). Facts: GHMC split 11 Feb 2026 (GO 55) into GHMC, Cyberabad MC (Serilingampally, Kukatpally, Quthbullapur zones; commissioner G. Srijana) and Malkajgiri MC. Gaps: 5 places without assembly/Lok Sabha (S07, S17, S18, S19, S23), NH65 owner unconfirmed, no CMC/NHAI mailbox, no RTI officers, no corporators. Network from the cloud blocked several official sites; re-check from the iMac.


## 3 Nov 2026 — share cards and logged-crash evidence
- Every page now has Open Graph and Twitter tags pointing at a 1200×630 card in `web/og/` (7 cards, rendered by `tools/og/make_og.py` from the films). Links shared on WhatsApp, LinkedIn and X now show a thumbnail.
- `/evidence/#logged`: official Hyderabad and Cyberabad crash totals (MoRTH 2023 city tables; Cyberabad 2025 annual report and Q1 2026 figures as reported). City-wide totals only; no place attribution.

## 3 Nov 2026 — phone interface pass (all mobile browsers)
- /drive/: phone layout with a taller stage, a two-row dash (Fixes · Above · Skip / Dive · Drive) that fits 320 px, intro card clamped to two lines (tap to expand), slimmer progress rail, wider intro orbit in portrait so both pins are in frame, touch wording in Dive.
- Device tier like 13point8: starting resolution from screen, density and memory (`?q=low` forces low), then frame time steps it down or up by 0.25 between 1 and the cap.
- /report/: form no longer wider than the screen (was 480 px on a 320 px phone).
- /globe/: place and city buttons are 40 px tall on touch screens.
- Nav: fades at the right edge while there is more to scroll.

## 3 Nov 2026 — hotspots job in the research runner
- New nightly job `hotspots` (research/runner/app/hotspots.py, docs/PREREG-hotspots.md): crossing-pressure proxies from GHSL residents (WorldPop cross-check), OSM daytime destinations and main-road supply; per place and on a 500 m city grid. Two pre-registered gates (triangulation ρ ≥ 0.70; composite must differ from population-only). Output to R2 `nights/<date>/hotspots.json`, not published.
- Dockerfile now installs rasterio (the bengaluru job also needed it for GHSL).

## 3 Nov 2026 — router cross-check and map-edit watch
- Found: the detour model counts OSM turn restrictions but does not obey them, so it could route through a banned U-turn. Declared in docs/PREREG-routercheck.md; any fix is a dated method change applied to every place and drive.
- New nightly jobs: `mapwatch` (edits within 1 km in 48 h, re-check list) and `routercheck` (OSRM + Valhalla vs model vs drives, ±15% agreement, both-longer flag). Order: openings, mapwatch, routercheck, hotspots, bengaluru.
- Standing rule (Rohit, 3 Nov): input from other AI tools is sorted critically; useful parts are adopted and the rest set aside with reasons.

## 3 Nov 2026 — drive 3 (night, west belt) and B-16
- Drive 3, 21:13–22:14 IST (Open GPX Tracker + Sensor Logger at 1 Hz, both private). Passed S11 and S09 along the road only (no crossing). Two U-turn loops found by hand: S10 A→B 1,115 m (model 1,126 m) and S08 B→A 402 m (model 432 m). NOT yet scored or published: the scorer cannot pair them because at places where A and B are under ~20 m apart, phone GPS cannot tell the two carriageways apart. A "loop rule" (leave, U-turn, return within 10 m; side from heading and left-hand traffic) is to be pre-registered before it is applied to any drive.
- B-16 (declared method change): a pass shorter than max(straight − 20 m, half the straight) is GPS jitter and is skipped, so it cannot beat a real loop. Re-applied to the 2 Nov drive: unchanged (S12 only). The 1 Nov drive must be re-scored on the iMac; its published passes are 1.5–11.6 km, far above the bound, so none can change.
