# arcroad — STATE

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
5. Immersive detour ride: driver's-eye 3D replay of a real drive (GPS path + timing + bumps), procedural original vehicles (trucks, buses, autos, two-wheelers), road rebuilt from photos as reference only (no faces/plates/brands shown); end card with distance, time, fuel vs "walk across in 15 s"; first prototype S01 Patancheru.
6. Photo pipeline: EXIF (time, GPS, heading, altitude) read in place on the iMac; originals private; web copies ~200 KB with faces/plates blurred and metadata stripped.
7. Colab: read secrets in the first cell while Rohit is present (v04 Mapillary step timed out on a locked screen).
8. Claude's own ideas to add after ingesting the drive data (to be proposed for yes/no).

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
