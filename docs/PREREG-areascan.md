# Pre-registration: areascan-v1 (refresh of "Worst areas measured")

Written before the first run (26 November 2026). Nothing below is tuned after seeing results.

## Question
On the latest OpenStreetMap extract, which named areas inside the declared HMDA box have the
highest median Detour Index, and do two independent routers agree with ours?

## Method (unchanged from the published table)
1. Latest Geofabrik extract(s) covering the HMDA box plus 0.20 degrees, clipped with osmium.
2. pipeline/pairing.py run_pairing with the V10 config; endpoint A inside the HMDA box.
3. Routed points only (no different-component pairs). Each point goes to the nearest named
   place (city, town, suburb, neighbourhood, village, hamlet, quarter) within 3 km.
4. Areas with at least 30 points. Median Detour Index and median driven distance per area.
   A median driven distance over 10 km is flagged as a likely map gap, as on the site.

## Three-router check (new)
For the 15 worst areas, 10 points each (seed 26) are routed again on the OSRM public server and
the FOSSGIS Valhalla server. An area agrees when both routers' median distance is within 25% of
ours. Areas that disagree are shown as unconfirmed, not dropped.

## Stability
The job runs on 26 and 27 November. An area that moves more than 20% between the two nights is
reported as unstable.

## Publication
Output is a candidate. The site table changes only after review and Rohit's go.
