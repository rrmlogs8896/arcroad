# Validation sweep, 26 Oct 2026: what it found instead

## What was attempted

A stratified cross-check of the v1.0 Detour Index against an independent
commercial routing engine. Rule 5 declaration, made before the attempt:

- **Hypothesis:** our OSM-based router is sound and the index values are
  approximately right.
- **Competing explanation:** the router systematically inflates, and every
  figure in the repository is wrong by a large factor.
- **Distinguishing result:** route 24 stratified pairs through both engines. A
  ratio distribution centred near 1 supports the first. A distribution
  systematically above 2 supports the second.

## The sweep could not run. B-09.

`v10_out/di_v10_points_2026-10-25.csv`, 12,645 rows, records **one endpoint per
measurement**:

    lat, lon, straight_m, network_m, detour_index, unreachable, near_limit, ...

The pairing step located two graph nodes on opposing carriageways, tested their
bearings for antiparallelism, routed between them — and then discarded the
second node, keeping only `straight_m` as a scalar.

**No measurement in that file can be re-routed by anyone, including us.** Not by
a second engine, not by a reader, not by us next month. It fails reporting rule
1 ("every number traceable") completely, and it went unnoticed for two days
because nothing had ever tried to re-check a single value.

Fix shipped: `pipeline/provenance.py` defines the schema a measurement must
carry (`a_lat, a_lon, b_lat, b_lon, straight_m, network_m, detour_index`, plus
node ids, OSM extract date and commit sha where available) and validates an
export against it. A null route must now name its reason; a blank cell is no
longer acceptable. Four regression tests. The next run cannot export the v1.0
shape without failing.

The TomTom sweep is deferred, not abandoned. It runs on the first export that
validates.

## What the attempt found instead

### B-10: 12.2% of the set is outside the declared study area

The project declares an HMDA bounding box of `78.050, 17.050, 78.850, 17.750`.
The measured set runs from **16.8495 to 17.9681 N and 77.8484 to 79.0715 E** —
1,549 points outside it, the furthest **85 km** from the centre, median distance
55.6 km. Those are rural Sangareddy, Vikarabad and Yadadri, not Hyderabad.

Direction of the error matters, so it is stated plainly: **this did not inflate
the headline, it diluted it.** The strays all sit in the "beyond the ORR" band
and they score *lower* than the true fringe. Every published ratio understated
the gradient.

That makes it a truthfulness bug rather than an exaggeration bug — the project
described an area it had not measured — and it is still a bug. The next run is
clipped to the declared box, or the declaration changes to match the data. Not
both silently.

### The gradient is not a ramp. It peaks at the fringe.

| ring | n | median index | above 50 |
|---|---|---|---|
| core city, 0–14 km | 5,521 | 18.05 | 20.5% |
| ring road band, 14–26 km | 3,955 | 33.76 | 39.9% |
| **peri-urban fringe, 26–40 km** | **1,045** | **57.52** | **53.8%** |
| rural, 40–60 km | 1,589 | 48.10 | 49.0% |
| beyond 60 km | 475 | 47.26 | 49.1% |

Core to true fringe: **3.19x**, against 2.85x for the published "beyond ORR"
figure that mixes the far rings in.

This is a better finding than a monotonic ramp, and it is checkable. The fringe
is where highway-grade divided roads already exist but the local street network
behind them has not filled in, so severance has nothing to absorb it. Further
out there are fewer divided roads and less severance.

**It has not been tested against that explanation.** The shape is consistent
with it; consistency is not evidence, and rule 5 says so. A competing
explanation that must be ruled out: OSM completeness itself varies by ring, and
a sparser map produces longer routes for reasons that have nothing to do with
road design. That test needs OSM density per ring alongside the index, and has
not been run.

Patancheru and Isnapur, where this project began, sit at roughly 36 km —
inside the peak ring. That is a coincidence worth stating out loud rather than
leaning on: the founder's grievance location scoring in the worst ring is
exactly the pattern a motivated analysis would produce by accident.

### B-11: the compliance check passed while checking nothing

`tools/check_freshness.py`, run from the wrong directory, printed
`0 page(s) checked / All verifications current.` and exited zero. The same shape
as B-07, which wrote a gap export with a header and no rows. Fixed: zero pages
checked is now a build failure.

Also noted while fixing it: `web/privacy.html`, `web/cookies.html` and
`web/terms.html` are listed in the freshness allowance but **do not exist yet**.
The checker skips absent pages by design. They are required before any public
launch and must be written against primary sources, not drafted from memory.
