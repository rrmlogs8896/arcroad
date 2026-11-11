# Pre-registration: U-turn openings worth a second look

Written 11 Nov 2026 at 19:30 IST, before any OpenStreetMap data was read for this study. Nothing below changes once results are seen except by a dated entry under "Changes", applied to every result.

## Question

On Cyberabad's divided roads, how many median openings (U-turn gaps) sit very close to another opening, or right next to a junction where traffic can already turn? Openings like these add places where vehicles cut across or wait in a fast lane, and guidance (IRC:62) prefers openings at intersections and well spaced. This study finds them from open data so they can be checked on the road and reviewed by the authorities.

## What this study does not claim

It does not say that any opening causes jams or accidents, or that any opening is unnecessary. Open data has no traffic speeds, counts or crash records for these points (AGENTS.md: nothing about an individual outcome). It identifies openings worth a second look and says why. It makes no claim about walking.

## Area

The Cyberabad IT corridor first: longitude 78.33 to 78.42, latitude 17.40 to 17.47 (Gachibowli to Madhapur). Any wider area is a dated change.

## Definitions (fixed now)

- **Carriageway.** A one-way OpenStreetMap way of class trunk, primary, secondary or tertiary, at ground level (not a bridge, not layer above 0).
- **Divided road.** Two carriageways whose segments run in opposite directions (bearings within 30° of opposite) and lie 6 to 45 m apart.
- **Median opening.** A drivable way (motorway to residential, links, living streets, unclassified) no longer than 45 m whose two ends lie on the two carriageways of one divided road. Openings whose midpoints are within 25 m of each other count as one, so a gap mapped once per direction is not counted twice.
- **Junction.** A node of a carriageway that also belongs to a public road (motorway to residential or unclassified, not a link, service way or path) that is not itself a median opening. A **signal** is a highway=traffic_signals node.
- **Flags, per opening.**
  - **Close to another opening:** the nearest other opening on the same divided road is less than 150 m away.
  - **Next to a junction:** a junction or signal is within 100 m.
  - An opening with either flag is **worth a second look**.

## Hypothesis, competing explanation, and what separates them (rule 5)

- **Hypothesis H.** Openings worth a second look are common in the IT corridor: at least a quarter of all openings carry a flag.
- **Competing explanation C.** The flags are mostly mapping artefacts: duplicate or misplaced connectors in OpenStreetMap, not real gaps on the road.
- **What separates them.** A ground check. Ten flagged openings are drawn at random (seed written in the results file before the draw) and checked on the road or in dated photos. If at least 7 of 10 are real openings that match the map, the share is published, with the check. If fewer than 7, C stands: the result is withdrawn as a mapping finding, and that is published instead.

## Output

Per opening: position, road name, the two flags with their distances, and whether it was ground-checked. A summary: number of openings, share flagged, by road. Every figure is a candidate until the ground check passes. Map data © OpenStreetMap contributors (ODbL).

## Changes

(none yet)
