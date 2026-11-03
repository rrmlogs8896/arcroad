# arcroad — STATE

> **3 Nov 2026 00:21 IST — v0.2 LIVE.** Production e8466501 (main e0318b5, PR #48). Rollback: ee5f8a1f (street search). Preview 0b3de616 checked by Rohit on his phone. In it: write to the people responsible (officials directory, hi/te drafts), glare drive, report-a-change form, headline tied to driven place S18 with its selection rule, per-direction calculator links, declared scorer change (S12 counted, disclosed). Not yet on the site: S12 as a 4th driven place (needs the field page rebuild).

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

