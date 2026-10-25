# STATE.md — read this first, read nothing else first

This file exists to make a fresh session cheap. A session that rebuilds its
picture of this project by reading the repository costs the owner real money for
information this file could have given in one read. Keep it under 150 lines.
Update it in the same commit as any change that makes a line here wrong.

Last updated: 26 October 2026

## Where things stand

- Repo: `github.com/rrmlogs8896/arcroad`, public. Local clone on the owner's Mac
  at `~/Documents/HMA/repo`, reachable through the device bridge at
  `$HOME/mnt/HMA/repo`.
- Site: `arcroad.org`, DNS on Cloudflare. Staging at `arcroad.pages.dev`,
  behind Cloudflare Access, owner only.
- Tests: 39 passing. `ruff` pinned at 0.16.9. CI runs lint, tests, freshness.
- Published findings: **none.** Nothing is published as a finding until a
  modelled route has been checked against a driven one.

## The one number that matters and does not exist yet

The Detour Index has **zero ground-verified values.** Every figure in this
repository is a candidate. Primary verification target: `17.5274, 78.2685`,
21 m apart, modelled at 2,344 m. Still untested — the 25 Oct GPX track came no
closer than 3,153 m.

First partial corroboration, diagnostic grade only:
`data/verification/2026-10-26-isnapur-tomtom.md`.

## What is true and robust

- The ring gradient holds across five independent treatments: 2.18x to 3.84x
  from core to beyond-ORR.
- The flagged third is mostly real severance, not mostly bad data: 79.5% of
  flagged points are under 25 m apart, median route 2,455 m, only 10.8% over
  10 km. This overturned an assumption held since v0.6.

## What is open

| id | item |
|---|---|
| B-08 | `TARGETS[:5]` slice in the v1.1 probe skips the control. Fix before rerun. |
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
