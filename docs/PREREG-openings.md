# Pre-registration: where a median opening is consistent with the guidance

Written 3 Nov 2026, before the job has run against any place. It must not be changed after results are seen. A change goes in as a dated amendment that is applied to every place, as with B-15.

## Question

At each Hyderabad place where the model finds a long detour, is there an intersection with a public road? India's access-control guidance (IRC:62) limits median openings to intersections, so this decides which fixes are guidance-consistent.

## Hypothesis, competing explanation, and what separates them (rule 5)

- **Hypothesis H.** The places are mostly mid-block, with no public road meeting the divided road. The guidance itself explains the closed median, and the guidance-consistent fixes are a nearer U-turn at an existing intersection or grade separation.
- **Competing explanation C.** The places sit at intersections where an opening (U-turn-only, or signal-controlled after an IRC:93 study) would be guidance-consistent, so the closure is a choice rather than a rule.
- **What separates them.** The share of places with a public-road intersection within 100 m of the A–B midpoint, compared with control points 350–450 m away along the same divided road.
  - If the places' share is at least 20 percentage points above the controls' share, that supports C.
  - If it is at least 20 points below, that supports H.
  - Anything in between is inconclusive and is reported as such.

## Definitions (fixed now)

- **Divided road.** The OSM way nearest to A or to B among motorway, trunk, primary, secondary and tertiary ways, plus every way within 900 m of the midpoint with the same highway class and the same name or ref. If neither name nor ref is set, the way nearest A and the way nearest B.
- **Public-road intersection.** A node of the divided road that also belongs to a way of class motorway to residential or unclassified, excluding *_link, service, track, path and footway, and excluding the divided road's own ways.
- **Intersection within 100 m.** Straight-line distance from the A–B midpoint (or from the control point) to the nearest public-road intersection node is 100 m or less.
- **Signal nearby.** A highway=traffic_signals node within 300 m of the midpoint.
- **Intersection spacing.** The number of public-road intersection nodes within 750 m of the midpoint. 750 m is IRC:62's spacing for highways, used only as a description.

- **Traffic calming (descriptive only).** Mapped traffic_calming nodes (humps, bumps, tables) within 750 m of the midpoint. These are counted, not tested: OSM under-maps speed breakers, so a count of zero says nothing. This feeds the vehicle-wear research only.

## Per-place classification (descriptive, not a recommendation)

- **At an intersection** (≤ 100 m). Guidance-consistent forms are a U-turn-only opening, or a signal if an IRC:93 study warrants one.
- **Mid-block** (> 100 m). Guidance does not support a full opening here. Consistent forms are a nearer U-turn at the nearest intersection (its distance is reported), a signal-free directional U-turn (J-turn), or grade separation.
- **Signal nearby** is flagged on its own. A new signal within 300 m of an existing one makes queues and coordination likelier, so signal-free forms come first.

## Limits, published with the result

- OpenStreetMap shows where roads meet. It does not show traffic volumes, so nothing here says where jams occur.
- Signals are under-mapped in OSM, so "no signal nearby" is weaker evidence than "signal nearby".
- Nothing here concerns walking (AGENTS.md).
- Every output is a candidate and is not published until reviewed.

## Data

- Overpass API (OpenStreetMap, ODbL), queried the night of the run; the query time is recorded in the output.
- Places from arcroad.org/globe/data/places.json, as published on that date.
