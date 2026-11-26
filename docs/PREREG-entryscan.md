# Pre-registration: entries that make residents drive past their own road (entryscan-v1)

Registered 26 Nov 2026, before any result of this method was read.

## Question

Where in Cyberabad does a residential road join a divided main road on one side only, so that a resident
arriving on the other carriageway must drive past their own entry to the next legal U-turn and back?
How far is that extra drive, and roughly how many homes lie behind the entry?

## Data

OpenStreetMap (Geofabrik extract, ODbL), clipped to the box 78.15 E to 78.52 E, 17.38 N to 17.62 N
(Cyberabad and the NH-65 corridor to Isnapur). Motorways (Outer Ring Road) are out of scope.

## Method (fixed before reading results)

1. Main roads: trunk, primary and secondary ways mapped as one-way carriageways.
2. Entries: a residential, unclassified, living-street, service or tertiary road whose end node lies on one
   carriageway and that a vehicle may enter there.
3. The other carriageway: the nearest point 6 to 60 m away on a different one-way main-road carriageway
   whose direction differs by at least 135 degrees.
4. Extra distance: shortest legal driving distance (one-way rules obeyed, turn restrictions not modelled,
   as in arcroad's model) from that point to the first node inside the entry road, minus the straight line
   between the same two points. Searched up to 12 km.
5. Candidate: extra distance of at least 1,000 m. Entries within 150 m on the same carriageway count once;
   the worst is kept.
6. Homes behind the entry: within 400 m on the entry's side of the main road, apartment buildings count 10,
   other home buildings 1, residential land 1 per 1,000 square metres (capped at 200 per area).
7. Ranking: extra distance in km multiplied by the natural log of (1 + homes index).
8. Cross-check: the top 20 are routed with OSRM and Valhalla (public servers, one request at a time),
   which obey turn restrictions.

## Method check (pass or fail, stated now)

Benchmark: the entry to the societies near Isnapur X Road on NH-65, driven privately twice in November 2026
at about 3.4 km extra. The method passes if it reports an entry within 200 m of that point with an extra
distance within 25 percent of 3.4 km (2.55 to 4.25 km). A failure is reported as a failure; the method is
not tuned and re-run to pass.

## Output and use

A private candidate list (research runner, nights of 26 and 27 Nov 2026; the second run repeats the first as
a stability check). Nothing is published until a place is driven. Home locations, drive dates and times are
never published.
