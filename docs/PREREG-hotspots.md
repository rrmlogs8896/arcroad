# Pre-registration: crossing-pressure hotspots (hotspots-v1)

Written 3 Nov 2026, before any data was fetched. Changes are dated below and made before a run, never after.

## Question
Where across Hyderabad, and at which of arcroad's 24 places, is the pressure to cross a divided road likely highest, judged only from where people live, where they go during the day, and how much main road serves them?

## What this is not
No open source in India publishes counted traffic. This job measures exposure, not traffic, congestion or crashes. Every output is labelled as a pressure proxy. Nothing is published without review, and no crash or violation is ever attributed to a place.

## Sources (all open, all cited)
- Residents: GHSL GHS-POP R2023A, epoch 2020, 3 arc-seconds (European Commission JRC, CC BY 4.0). The tile grid is the fixed, self-checking one in `tools/multicity_collect.py`.
- Cross-check: WorldPop 2020 constrained, UN-adjusted, India, 100 m (University of Southampton, CC BY 4.0).
- Main roads (motorway, trunk, primary, secondary) and daytime destinations (schools, colleges, universities, hospitals, clinics, markets, malls, supermarkets, offices, bus, rail and metro stations): OpenStreetMap via Overpass (ODbL).
- Not used: Google Maps or any Google data; TomTom (private checks only, never in an output); any paid source.

## Measures
- Per place (midpoint of the two sides): residents within 500 m and 1 km; destinations within 1 km; main-road km within 1 km; mean excess detour (mean of the driven-or-modelled A→B and B→A legs, minus the straight distance); exposure index = residents within 1 km × mean excess detour km.
- City grid: 500 m cells over the Hyderabad box; each cell's 1 km catchment gives residents, destinations and residents per km of main road (floor 0.5 km). Composite score = mean of the three percentile ranks. The top 25 cells are reported.

## Gates, fixed now
1. Triangulation: Spearman rank correlation of GHSL and WorldPop residents within 1 km across the 24 places must be at least 0.70. Below that, or if WorldPop cannot be read, the run is NOT REPORTABLE.
2. Competing explanation ("it is only where people live"): if 80% or more of the composite top 25 cells are also in the population-only top 25, the composite adds nothing and the run is reported as POPULATION ONLY.
3. Only a run that passes both gates is REPORTABLE, and even then it is reviewed by Rohit before anything is shown on the site.

## Known limitations, published with any result
- 2020 population, not 2026. Daytime destinations from OSM are incomplete and uneven by area.
- A 1 km circle ignores the median, so residents on both sides count for every place.
- Exposure is a ranking aid for where to drive and count next, not an estimate of trips.

## Changes
(none yet)
