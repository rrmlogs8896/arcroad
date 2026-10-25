# arcroad

*Working title in earlier documents: Hyderabad Mobility Atlas (HMA).*

Measuring what road geometry costs the people who live beside it, from open data,
with the method published so any claim can be checked.

## The question

A destination 400 m away across a divided highway can cost 4 km of driving, because the
nearest legal median opening is far off. Highway engineering optimises for movement
along a corridor. Nobody measures what that costs the people trying to cross it — so
nobody is accountable for it.

**Detour Index** = shortest legal driving distance ÷ straight-line distance, measured
from a point on a divided arterial to the far kerb.

## What this measures, and what it does not

- **Distance and geometry only. Never travel time.** Congestion and construction are
  deliberately absent. A median will still be there after the roadworks finish; that is
  what makes the claim survive "wait for 2028".
- **What OpenStreetMap records, not what exists on the ground.** Hyderabad's OSM
  coverage is thin (see the Phase 1 coverage audit). A missing service-road link looks
  exactly like a severed neighbourhood. Every high-DI point is a **candidate to verify**,
  not a finding.
- **Nothing about walking.** OpenStreetMap does not hold usable pedestrian data for
  Hyderabad — 407 recorded crossings and 212 footbridges across a metro area of
  roughly ten million, with zero within 400 m of Abids or Secunderabad station.
  Absence in the map is not absence on the ground. Every claim here is about driving.
- **No personal data.** Phases 1–4 hold none at all: no accounts, no location
  permission, no identifying analytics. Enforced by `tests/test_privacy.py`.

## Layout

```
pipeline/     importable code — the source of truth
  geometry.py   haversine, bearing, antiparallel test, zones
  filters.py    defence-attribute stripper, grade levels, oneway, divided proxy
  metrics.py    detour index, headline statistics, worst-N
  diagnostics.py  rings, sectors, gap export, clustering, stratified comparison
tests/        unit tests, including regressions for every shipped bug
notebooks/    thin wrappers that import pipeline/ and display results
web/          front end
data/         provenance records and small fixtures only, never large extracts
```

Notebooks are a presentation format. They are not the source of truth, because code
that lives only in a notebook cannot be versioned, diffed, tested on push, or tied to a
published number.

## Running the tests

```
pip install -r requirements.txt pytest
pytest -q
```

Three of these tests exist because the code got it wrong in production:

| Test | The bug it locks out |
|---|---|
| `test_filters.test_flyover_overhead_is_not_across_the_road` | v0.4 paired a road with the flyover 15 m above it |
| `test_geometry.test_antiparallel_rejects_the_v04_failures` | v0.4 paired perpendicular and same-direction roads as carriageways |
| `test_metrics.test_headline_is_computed_on_the_uncensored_set` | v0.5 let a review flag censor 34% of points out of the published median |
| `test_diagnostics.test_gap_export_is_not_empty_when_the_set_contains_gaps` | v1.0 wrote a header and zero rows while 60 unreachable points sat in the set |
| `test_diagnostics.test_severity_threshold_discriminates_between_core_and_periphery` | a threshold of 5.0 labelled 77% of the core city severe |
| `test_diagnostics.test_small_groups_are_marked_inadequate_not_silently_ranked` | v0.9 topped a sector ranking with a median computed over twenty points |
| `test_diagnostics.test_edge_distance_and_centre_distance_are_nearly_collinear` | v1.0 built an edge test that could not answer its own question |

## Reporting rules

1. Every number traceable to a named dataset, a dated extract and a commit hash.
2. Gate thresholds written **before** the run, never after seeing results.
3. Known limitations published alongside results, not buried.
4. A dramatic number that supports the project's thesis gets **more** scrutiny, not
   less. v0.4 produced exactly such a number and it was wrong.
5. Before a test runs, state the hypothesis, the most likely competing explanation,
   and what result would distinguish them. A test that cannot separate the two is
   not run until it can. Added 25 Oct 2026 after this was broken three times in one
   day; see `AGENTS.md`.

## Licence and attribution

Two licences, because two different things live here. **Code is MIT** (`LICENSE`).
**Data is ODbL 1.0** (`DATA-LICENSE.md`), inherited from OpenStreetMap.

> Map data © OpenStreetMap contributors (ODbL). Measurements by arcroad (ODbL).

arcroad is an independent citizen project. It is not affiliated with GHMC, HMDA, NHAI, the
Government of Telangana, or any political party.
