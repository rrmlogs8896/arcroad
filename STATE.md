# arcroad — STATE

Read this first; it replaces reconstructing status from the history. Update it in
the same commit as any change that makes it wrong. Longer history and decisions
live in the ledger (Drive: Anthropic / Hyderabad Mobility Atlas, Doc 03).

Last updated: 28 Oct 2026.

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
