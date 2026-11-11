# Pre-registration: detour baseline for the proposed Hi-Tech City one-way loop

Written 11 Nov 2026 at 11:30 IST, before any distance for this study was computed. Nothing below may change once results are seen without a dated entry under "Changes", applied to every result on file.

## Question
Cyberabad Police have proposed turning the roads between Biodiversity Junction, IKEA, Mindspace, Knowledge City and Dallas Center into a single one-way loop, and will judge it by vehicle speed and traffic density. This study measures what that leaves out: how much longer each journey through the area becomes for people driving, and for the buses that serve it. It makes no claim about walking: OpenStreetMap's pedestrian data for Hyderabad is not good enough to carry one (see AGENTS.md).

## Status of the loop
At the time of writing the loop is a proposal at the study stage, with a trial run promised and no date set. The route used here is the one reported on 29 Oct 2026: Biodiversity Junction, IKEA Rotary, Raheja Mindspace (C-Gate), Knowledge City, Dallas Center, a right turn at My Home Bhooja, and back to Biodiversity Junction. If the police publish a different route, the scenario is rebuilt on the published route, the change is dated below, and every figure is recomputed.

## Places (gates)
Six gates: Biodiversity Junction, IKEA Rotary, Mindspace C-Gate, Knowledge City, Dallas Center, My Home Bhooja. Each is snapped to the nearest OpenStreetMap junction node; the node IDs and the extract date are written into the results file when the computation runs, before any distance is read.

## Two networks
- **Today:** the OpenStreetMap extract for the area as downloaded on the day of computation (date recorded).
- **Loop:** the same extract, with every way on the loop route set one-way in the loop's direction and nothing else changed. No new turns, closures or openings are invented.

## Measures
1. **Driving.** For all 30 ordered pairs of the six gates: legal shortest route length on each network (OSRM, car profile, the router arcroad already uses), cross-checked with Valhalla. Reported per pair: added metres (loop minus today) and the ratio. Summary: the share of pairs that get longer, the median and largest increase. Threshold, fixed now: a pair counts as longer only if the loop route is at least 100 m and at least 10% longer than today's; smaller differences are reported but counted as unchanged. Where the two routers differ by more than 10% on a pair, the pair is flagged and shown with both figures, never dropped.
2. **Buses.** For each TGSRTC route in the GTFS feed whose shape uses a loop road against the loop's direction: the extra route length needed to serve the same stops on the loop network.

## Hypothesis
The loop makes most journeys between its gates longer, because a trip that today goes against the loop's direction must go round it. Most likely competing explanation: today's network already forces those trips round through U-turns, so the loop adds little. What separates them: the share of pairs whose route gets longer by more than the threshold above. If fewer than a third do, the hypothesis is rejected and that is reported.

## Validation
Today's driving figures are checked by GPS drives under arcroad's existing rules (match within 150 m or 25%, the pairing and loop rules unchanged). A pair with no drive is labelled "model only", and no absolute figure for it is published as measured. Loop figures are scenario figures until the trial: they are labelled as such everywhere they appear and are never called measured effects.

## After the trial
When the trial runs, the same pairs are driven again under the same rules, and the before-and-after is published whatever it shows.

## What is not used
No Google Maps data or any other closed routing data. No walking figures. No personal data: drive tracks stay private, only route lengths are published, and no photo shows a person or a number plate.

## Competing explanation, and what would settle it
A one-way loop can make trips longer and still make them faster, by removing waiting at four junctions. This study measures distance, not time, so a longer route is not by itself evidence that the loop is worse. What would settle it: timed drives of the same pairs before and during the trial, at the same hours. Those are planned and will be reported alongside the distances.

## Changes
**11 Nov 2026, 14:10 IST, before any distance was computed.** How the two networks and routes are made, fixed now because a public router cannot be given a changed network:
- Both networks are routed by arcroad's own shortest-path code (`pipeline/loopcost.py`) on one OpenStreetMap extract fetched once from Overpass (query and download time recorded). Drivable classes only: motorway to residential, their links, and living streets; `access=no` and `access=private` excluded; one-way tags obeyed; turn restrictions not modelled (the same limitation as arcroad's detour model). Today's 30 routes are cross-checked against the public OSRM and Valhalla servers; a pair where either differs by more than 10% is flagged and shown with all figures.
- The gates are located by OpenStreetMap's Nominatim search; every match (name found, OSM id, coordinates) is written to `data/loop/gates.json` and checked by a person before any route is computed. A gate that cannot be matched is left out and listed, not guessed.
- The loop route is found, not drawn: the shortest legal path from each gate to the next in loop order on today's network. The loop network then drops every road segment that runs against the loop's direction within 30 m of that path, both the reverse of a two-way road and the opposite carriageway of a divided road (bearing within 60° of opposite). Nothing is added. If the police publish the route, it replaces this one (see "Status of the loop").
- Buses (measure 2) need the TGSRTC GTFS feed; they are computed in a second step and are not part of the first results file.
**11 Nov 2026, 14:40 IST, before any distance was computed.** The search for the gates returns buildings and campuses (the IKEA store, a Mindspace building), not junctions. Snapping those to the nearest road of any class could put a gate on a lane inside a campus. A gate now snaps to the nearest node on a road of class tertiary or above, the class of every road on the reported loop. The snap distance is recorded and anything over 60 m is flagged.
**11 Nov 2026, 14:55 IST, before any distance was computed.** The search found Biodiversity Junction only as its level-2 flyover. A gate may not snap to a bridge or a road above ground level: it snaps to the junction road beneath. The search for My Home Bhooja returned a different building (My Home Twitza), so Bhooja is left out and listed; the loop closes from Dallas Center to Biodiversity Junction by the shortest legal path. Five gates, 20 ordered pairs.
