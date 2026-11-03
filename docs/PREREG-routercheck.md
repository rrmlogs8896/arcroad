# Pre-registration: router cross-check and map-edit watch (routercheck-v1, mapwatch-v1)

Written 3 Nov 2026, before any request was sent. Changes are dated below and made before a run, never after.

## Why
arcroad's detour model routes on OpenStreetMap but does not obey OSM turn restrictions (it counts them only). Where a U-turn is banned, the model could route through it and understate the detour. Two independent open routers that do obey restrictions, OSRM (car profile) and Valhalla (auto), test the model by a different method.

## Part 1: router cross-check
- For each of the 24 places, both directions (48 routes per router), route from one side to the other with a 25 m snap radius and no U-turn at the start point.
- Ratio = router distance ÷ model distance. AGREES if within ±15%. ROUTER_LONGER if 20% or more longer. ROUTER_SHORTER if shorter by more than 15%.
- Decision rules, fixed now:
  1. A direction where both routers are ROUTER_LONGER is flagged as "possible banned U-turn in the model" and goes on the next drive list. It is not changed on the site until a drive or a declared method change settles it.
  2. On the driven directions, the mean absolute error against the drive is compared for the model, OSRM and Valhalla. If either router beats the model by 10 percentage points or more, a method change (obeying turn restrictions) is proposed as a dated amendment, applied to every place and re-checked against every drive. Until then the model stays as is.
  3. If the routers disagree with each other on more than a third of directions, the cross-check is reported as inconclusive.
- Servers: the public OSRM demo server and the FOSSGIS Valhalla server, one request at a time with a 1.5 s pause. If either server's usage policy changes, the job stops using it.

## Part 2: map-edit watch
- Each night, road ways, turn-restriction relations and signal or turning nodes within 1 km of each place edited in the last 48 hours. Any hit puts the place on a re-check list. Mapper names are not collected.
- A hit never changes a figure by itself.

## Known limitations
- Public demo servers may be a few days behind OSM and may be rate-limited.
- Routers snap to the nearest road within 25 m; at complex junctions they can pick a service road. Such rows are kept and marked, not dropped.

## Changes
(none yet)
