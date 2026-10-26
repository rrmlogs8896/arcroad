# AGENTS.md

Instructions for any agent or person working in this repository.

arcroad measures what road geometry costs the people who live beside it, from
open data, with the method published so any claim can be checked. Its only
asset is that its numbers are reproducible and its errors are visible. Code
that weakens either is worse than no code.

Read this before changing anything. The rules below exist because each one was
broken once and cost something.

---

## The five reporting rules

These govern every number this project publishes. Rules 1 to 4 are in
`README.md`; rule 5 was added on 25 October 2026 after being broken three times
in a single day.

1. Every number traceable to a named dataset, a dated extract and a commit hash.
2. Gate thresholds written **before** the run, never after seeing results.
3. Known limitations published alongside results, not buried.
4. A dramatic number that supports the project's thesis gets **more** scrutiny,
   not less.
5. **Before a test runs, state the hypothesis, the most likely competing
   explanation, and what result would distinguish them. A test that cannot
   separate the two is not run until it can.**

Rule 5 in practice: a probe that samples only the cases you expect to be
interesting will find them interesting. It needs a control. Three failures in
one day, all the same shape:

- **v0.9** predicted the sector ranking was confounded by sampling distance.
  Tested it. Wrong (r = 0.13).
- **v1.0** built an edge test to ask whether flagging was a boundary artefact.
  The test could not answer its own question: edge distance and
  distance-from-centre correlate at r = -0.889 over this study area, and every
  core point is 20 km+ from the edge by construction.
- **v1.1** probed whether the worst points lacked pedestrian crossings and
  queried only the worst points. The control was in the target list and the
  loop stopped before reaching it. When the control finally ran, it showed
  Abids and Secunderabad station also record zero — the result was the citywide
  default, not a property of those places.

`pipeline/diagnostics.stratified_compare` is rule 5 expressed as code.

---

## What this project must never claim

**Nothing about walking.** OpenStreetMap does not hold usable pedestrian data
for Hyderabad: 407 recorded crossings and 212 footbridges across a metropolitan
area of roughly ten million people, with zero recorded within 400 m of Abids or
Secunderabad station. Absence in the map is not absence on the ground. Every
published claim is about **driving**.

**Nothing about intent.** We publish what an authority recorded and what we
measured. Never what we think that means about anyone's motives, competence or
honesty. A date eighteen months past its promise needs one document to prove
and no adjective to land.

**Nothing about an individual outcome.** No death, injury or emergency is ever
attributed to an individual road feature. Open data cannot carry that causal
weight.

**No absolute Detour Index value**, until a modelled route has been checked
against a driven one. Ratios between areas hold. Individual values do not.

---

## Hard constraints

- **Zero Google Maps data, ever.** No scraping, no tracing, no screenshots, no
  tiles. Google Open Buildings is separately licensed and permitted; Street
  View and Maps are not.
- **Defence attributes are stripped on ingest**, enforced by
  `tests/test_privacy.py`. That test must pass or nothing ships.
- **Citizen reports never enter a published figure.** They live in a separate,
  labelled layer. A number that mixes in unverifiable reports cannot be
  reproduced, and reproducibility is the whole claim.
- **Sub-metre-derived data goes to India-region storage**, never the global
  edge. Anything from Open Buildings falls under this.

---

## Licensing

- Code: MIT (`LICENSE`).
- Derived measurements: ODbL 1.0 (`DATA-LICENSE.md`), inherited from
  OpenStreetMap and not optional.

Attribution on anything published:

> Map data © OpenStreetMap contributors (ODbL). Measurements by arcroad (ODbL).

---

## Layout

```
pipeline/     importable code — the source of truth
  geometry.py     haversine, bearing, antiparallel test, zones
  filters.py      defence-attribute stripper, grade levels, oneway, divided proxy
  metrics.py      detour index, headline statistics, worst-N
  diagnostics.py  rings, sectors, gap export, clustering, stratified comparison
tests/        unit tests, including a regression for every shipped bug
notebooks/    thin wrappers that import pipeline/ and display results
web/          front end
data/         provenance records and small fixtures only, never large extracts
```

**Notebooks are a presentation format, never the source of truth.** Code that
lives only in a notebook cannot be versioned, diffed, tested on push or tied to
a published number. If a notebook cell computes something a published figure
depends on, it belongs in `pipeline/` with a test before that figure is used.

---

## Before you change anything

- Run `ruff check pipeline tests` and the test suite. Both must pass.
- `ruff` is pinned in CI. Do not unpin it to make a check go away.
- If a check fails, fix the code. **Narrowing a check until it stops reporting
  is how the v0.5 censoring bug happened**, and a lint config was very nearly
  used the same way on 25 October 2026 to hide a real dead cast.
- A new bug gets a regression test named after the failure, not after the
  function.

## Thresholds, and why they are what they are

- `DI_SEVERE_DEFAULT = 50.0` — was 5.0, which labelled 77% of the core city
  severe and carried no information. See D-12.
- `DI_REVIEW_DEFAULT = 50.0` — marks points for verification. **It must never
  remove them from the headline.** v0.5 let it censor 34% of points and
  published 12.90 where the true median was 28.70.
- `GAP_ROUTE_M = 10_000.0` — above this, to cross a crossing-width gap, a hole
  in the map is likelier than a real detour. A threshold for routing a point to
  review, not a verdict.
- `CROSSING_MAX_M = 25.0` — below this separation the pair is a road crossing.

## Proprietary sources

Proprietary maps and routers are never the source of a published figure, a
derived dataset or a map tile. Every published number comes from open data.

## Status

The Detour Index is checked against driven routes before any value is published.
Until then every figure here is a candidate, labelled as such.
