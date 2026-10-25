# STATE.md — read this first, read nothing else first

> **Session note, 26 Oct 2026 ~04:30 IST — B-09 and B-10 fixed in code; rerun pending.**
> Changed: `pipeline/pairing.py` (pairing, graph, routing and records ported from
> the notebooks; both endpoints kept; study box a parameter, clipped and recorded;
> export refuses invalid records), `tests/test_pairing.py` (7 regression tests),
> `tools/check_pairing_port.py` (runs the notebook cells verbatim against the port
> on synthetic networks; all identical; 4 planted mutations all caught), and
> `notebooks/arcroad_Phase2a_DetourIndex_v08.ipynb` (thin; supersedes v07).
> Source was `~/Documents/HMA/HMA_Phase2a_DetourIndex_v07.ipynb`, outside git; the
> producing run's notebook (`arcroad_Phase2e_Diagnostics_v10`) has identical
> graph/routing/record cells and a pairing cell differing by one `FOCUS_ZONE` guard.
> What v10 changed was config (stride 4, cap 16,000, limit 25 km): kept as preset
> `pairing.V10`, the default. (`kept.append` is in v10's `dedupe_worst`, not in pairing.)
> **Next session:** (1) push — neither the cloud container nor the device bridge
> reaches GitHub (proxy 403); push from the Mac's own terminal, then check CI.
> (2) Rohit runs v08 in Colab. Expect 12,645 pairs before the clip, 1,549 outside,
> 11,096 kept on the same extract; a different count means the extract changed.
> (3) Then the cloud session runs the TomTom sweep on that validated export.
> Untested here (no osmium available): `load_network` (verbatim port) and
> `extract_date` — watch Colab cells 3-4. `osm_way_ids` along the route is not yet
> emitted; endpoint ways are (`a_way_ids`, `b_way_ids`).

This file exists to make a fresh session cheap. A session that rebuilds its
picture of this project by reading the repository costs the owner real money for
information this file could have given in one read. Keep it under 150 lines.
Update it in the same commit as any change that makes a line here wrong.

Last updated: 26 October 2026 (04:30 IST)

## Where things stand

- Repo: `github.com/rrmlogs8896/arcroad`, public. Local clone on the owner's Mac
  at `~/Documents/HMA/repo`, reachable through the device bridge at
  `$HOME/mnt/HMA/repo`.
- Site: `arcroad.org`, DNS on Cloudflare. Staging at `arcroad.pages.dev`,
  behind Cloudflare Access, owner only.
- Tests: 52 passing. `ruff` pinned at 0.16.9. CI runs lint, tests, freshness.
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

**The validation sweep against a second engine waits for the v08 rerun.** The
v1.0 export records one endpoint per measurement (B-09) and cannot be swept; the
fix is in code, the data is not yet regenerated. See
`data/verification/2026-10-26-validation-sweep.md`.

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
| B-09 | **Fixed, rerun pending.** `pipeline/pairing.py` keeps both endpoints, node ids, extract date, commit; null routes name a reason; `write_point_file` refuses invalid records. Needs the v08 Colab run, then unblocks the TomTom sweep. |
| B-10 | **Fixed, rerun pending.** Study box is a parameter (default declared HMDA), clipped on endpoint A after pairing and before routing, excluded pairs counted, box recorded per record and in `.meta.json`. |
| — | Test the fringe peak against OSM density per ring before it is published as a finding. |
| — | `web/privacy.html`, `web/cookies.html`, `web/terms.html` do not exist. Required before launch, written from primary sources. |
| — | Reconnect Cloudflare Pages to Git if pushes stop auto-deploying. |
| — | Extend Access policy to `*.arcroad.pages.dev`; hash URLs are currently open. |
| — | Branch protection on `main` requiring CI. |
| — | Cloudflare Web Analytics (cookieless) and Email Routing for `hello@arcroad.org`. |
| — | Mapillary returns zero even for central London: the query is broken, not the data. Retry with an `Authorization: OAuth <token>` header. |
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
