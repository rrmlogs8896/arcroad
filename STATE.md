# STATE.md — read this first, read nothing else first

> **Session note, 26 Oct 2026 ~11:45 IST — B-09 and B-10 CLOSED; first re-checkable export exists.**
> `c29d9c1` pushed, CI #16 green. The v08 Colab rerun reproduced v1.0 exactly: same graph
> (1,234,503 nodes / 2,618,735 edges), 12,645 pairs, 1,549 outside the HMDA box, 11,096 kept,
> in-box median 25.67, 9 null routes all `unreachable`. File checked independently: 0 invalid
> records, straight_m recomputes from A/B to 0.05 m, one extract date/commit/box throughout.
> Output: Drive `AI PROJECTS — MASTER WORKSPACE/Anthropic/Hyderabad Mobility Atlas/phase2a_detour_v08/`
> `di_points_2026-10-26_c29d9c1.csv` + `.meta.json`. Ledger Doc 03 §36.13–36.16.
> This commit: B-13 (notebook saved to a stale Drive path and created duplicate folders; now
> `DRIVE_BASE` in cell 2, mounted and checked up front). B-12 (calculator diesel option)
> fixed in the artefact, not the repo. Calculator recorded below (P-44).
> **Next session:** (1) cloud session runs the TomTom sweep on that file, private only (D-02).
> (2) Mapillary probe is BUILT (this commit); run it in Colab once the token is in Secrets. Use imagery to correct OSM
> upstream, never import CC-BY-SA into the ODbL set. (3) Dependabot PR #5 (numpy 2.5.4)
> fails CI — read before merging. Untested in CI: `load_network`/`extract_date` (need
> osmium) — both ran correctly in Colab on 26 Oct.

This file exists to make a fresh session cheap. A session that rebuilds its
picture of this project by reading the repository costs the owner real money for
information this file could have given in one read. Keep it under 150 lines.
Update it in the same commit as any change that makes a line here wrong.

Last updated: 26 October 2026 (11:45 IST)

## Where things stand

- Repo: `github.com/rrmlogs8896/arcroad`, public. Local clone on the owner's Mac
  at `~/Documents/HMA/repo`, reachable through the device bridge at
  `$HOME/mnt/HMA/repo`.
- Site: **arcroad.org serves nothing yet: the zone is active on Cloudflare but has no DNS records**
  (read via the Cloudflare API connector, 26 Oct). Staging is `arcroad.pages.dev`.
  **Private since 26 Oct 12:15 IST.** It had been public: the Access app protected
  `arcroad.arcroad.pages.dev` (name doubled). Now `arcroad.pages.dev` + `*.arcroad.pages.dev`,
  policy "me only"; anonymous fetches of the bare host and two hash URLs all hit the Access
  login. While open, its content (incl. an individual DI value) was copied by at least one crawler.
- **Pages has never deployed from Git.** Source is linked (rrmlogs8896/arcroad, deployments
  enabled) but its only deployments are three manual uploads of `62b48fd` on 25 Oct. None of
  the 26 Oct pushes reached the site.
- Tests: 62 passing. `ruff` pinned at 0.16.9. CI runs lint, tests, freshness.
- Published findings: **none.** Nothing is published as a finding until a
  modelled route has been checked against a driven one.

## The one number that matters and does not exist yet

The Detour Index has **zero ground-verified values.** Every figure in this
repository is a candidate. Primary verification target: `17.5274, 78.2685`,
21 m apart, modelled at 2,344 m. Still untested — the 25 Oct GPX track came no
closer than 3,153 m.

First partial corroboration, diagnostic grade only:
`data/verification/2026-10-26-isnapur-tomtom.md` — NH-65 at Isnapur, two points
17 m apart, 1,630 m driven, 3,031 m routed by TomTom. n = 1, unpublishable.

**The validation sweep against a second engine can now run.** The v08 export
(`di_points_2026-10-26_c29d9c1.csv`) carries both endpoints for all 11,096 pairs.
Background: `data/verification/2026-10-26-validation-sweep.md`.

## What is true and robust

- The ring gradient holds across five independent treatments: 2.18x to 3.84x
  from core to beyond-ORR. As of 26 Oct the better reading is a **non-monotonic
  profile peaking in the 26-40 km fringe** (median 57.52, core 18.05, ratio
  3.19x), with rural rings scoring LOWER. Not yet tested against the competing
  explanation that OSM density varies by ring.
- The flagged third is mostly real severance, not mostly bad data: 79.5% of
  flagged points are under 25 m apart, median route 2,455 m, only 10.8% over
  10 km. This overturned an assumption held since v0.6.

## What is open

| id | item |
|---|---|
| B-08 | `TARGETS[:5]` slice in the v1.1 probe skips the control. Fix before rerun. |
| B-09 | **Closed 26 Oct.** Both endpoints kept; v08 rerun reproduced v1.0 exactly; export validated. |
| B-10 | **Closed 26 Oct.** Clip removed exactly the 1,549 strays; box recorded per record. |
| B-13 | **Fixed in this commit.** Notebook Drive path is `DRIVE_BASE` (cell 2), mounted and checked before the run. |
| P-44 | Cost calculator exists only as the artefact "What the detour costs you" (claude.ai, private; ledger §23). Not in `web/` by design: gates G-1, G-2, G-4, G-6 open, and `*.arcroad.pages.dev` hash URLs are not behind Access, so even a "draft" would be public. B-12 (diesel option broken) fixed in the artefact 26 Oct. |
| — | Dependabot PR #5 (numpy >=2.5.4) fails CI. Do not merge until read. |
| — | Test the fringe peak against OSM density per ring before it is published as a finding. |
| — | `web/privacy.html`, `web/cookies.html`, `web/terms.html` do not exist. Required before launch, written from primary sources. |
| — | Pages Git auto-deploy has never fired (only manual uploads of `62b48fd`). Check Cloudflare's GitHub app installation on the repo, then confirm a push produces a `github:push` deployment. |
| — | Branch protection on `main` requiring CI. |
| — | Cloudflare Web Analytics (cookieless) and Email Routing for `hello@arcroad.org`. |
| — | Mapillary probe **built; live runs 1–2 (26 Oct) got HTTP 500 "Please reduce the amount of data" on the Amsterdam control and stopped as designed. Run 2 lowered only the limit and failed identically, so the API counts AREA, not limit. Retries now shrink the box about its centre (never below ~55 m half-width) and lower the limit; failures carry the API's own message.** (`pipeline/mapillary.py`, 9 tests, `notebooks/arcroad_Probe_Mapillary_v01.ipynb`). Controls (Amsterdam, London, ~0.004°) must return ≥ 20 images or the run stops; 100 flagged + 100 unflagged pairs, seed 26; thresholds fixed in the module. Token in Colab Secrets as `MAPILLARY_TOKEN`; runs in Colab only. |
| — | NH-65 Vijayawada baseline capture. Works begin January; the pre-works state is lost permanently once they start. Harness must record per-segment OSM version ids and a control corridor before it runs. |
| P-17 | GitHub PAT expires 23 Jan 2027. |
| P-19 | Legal entity required before any Stage B (citizen photo) work. |
| P-20 | Consent copy needed in Telugu and Hindi. |

## Dead ends, do not re-attempt

- **Panoramax**: zero coverage for Hyderabad. API works, the data is not there.
- **Terrain on the globe**: 32 m elevation spread citywide against a 100 m
  threshold set before the test. There is no relief to render.
- **`edge_km` as a boundary test**: collinear with distance-from-centre at
  r = -0.889 over this study area. It cannot separate the two explanations.

## Rules that govern everything

`AGENTS.md`. Read it before changing code. The five reporting rules, what this
project must never claim, and the thresholds with the failure that set each.
