# Diagnostic: Isnapur, NH-65 — 17 m apart, 1.6 km driven, 3.0 km routed

**Status: PRIVATE DIAGNOSTIC. Not publishable. See "Licensing boundary" below.**

Date recorded: 26 October 2026
Recorded by: automated session, pushed to `main`

## What was tested

A GPX track driven by the project owner on 25-26 October 2026 (Open GPX Tracker,
iOS, 3,949 points, 36.85 km, 16:13-00:35 IST) contained one manoeuvre that
survived filtering: at 21:29 the vehicle travelled 1,630 m to end up 17.0 m from
where it started, at `17.55328, 78.19603`.

The obvious competing explanation, volunteered by the driver, was that he parked
partway through — in which case the 1,630 m is a route choice around a stop, not
a forced crossing, and the event must be withdrawn.

## Reporting rule 5 declaration, stated BEFORE the test ran

- **Hypothesis:** the 1,630 m was forced by divided-road geometry.
- **Competing explanation:** it was a chosen route around a parking stop.
- **Distinguishing result:** route the two endpoints through an independent
  engine that has no knowledge of the stop. A result near 30 m supports the
  parking explanation and the event is withdrawn. A result near 1,600 m or above
  supports the geometry and the event stands.

## Result

| measure | value |
|---|---|
| straight-line separation | 17.0 m |
| driven (GPX) | 1,630 m |
| TomTom routing, `routeType=short`, historical traffic | **3,031 m** |
| TomTom travel time | 377 s |
| TomTom traffic delay | 0 s |
| TomTom road attribution | Mumbai Highway, NH65 |

Reverse geocode of `17.55328, 78.19603`:
`Mumbai Highway, Isnapur, Patancheru 502307, Telangana` (Sangareddy district,
route number NH65).

**The parking explanation is not sufficient.** Parking explains why the vehicle
stopped. It does not explain why returning to a point 17 m away required 1.6 km,
when an independent router with no knowledge of the stop puts the shortest legal
path at 3.0 km.

## What this does NOT establish

1. **n = 1.** One manoeuvre, one vehicle, one night. This is a single
   corroborated instance, not a verified Detour Index value, and it does not
   change the project's position that the DI has zero ground-verified values.
2. **The two engines disagree by a factor of 1.9.** TomTom routed 3,031 m where
   the vehicle drove 1,630 m. The likeliest explanation is that the driver used
   a median opening or informal turn that TomTom's turn restrictions do not
   permit. An alternative is that the GPX endpoints snap to different
   carriageways under each engine. Until that is resolved, neither figure is
   the length of this detour — only the order of magnitude is agreed.
3. **It is not the primary verification target.** That remains
   `17.5274, 78.2685`, 21 m apart, modelled at 2,344 m. The closest this track
   came to it was 3,153 m, so that prediction is still untested.
4. **The OSM-based pipeline has not been run on this pair.** Doing so is the
   next step, and is the only one of the three numbers that could ever be
   published.

## Licensing boundary

TomTom is proprietary. Under decision D-02 it sits in the same category as
Google Maps: usable to check our own work in private, never as a source for a
published figure, a derived dataset, or a map tile. This file exists so the
check is on the record and reproducible by anyone with their own TomTom key —
not so the number can be quoted.

The publishable verification of this location still requires either an
OpenStreetMap-based route or a measured ground truth. This diagnostic raises
confidence that such a measurement is worth taking. It does not substitute for it.
