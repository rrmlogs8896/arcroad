# World sample cities: research and groundwork (2 Nov 2026)

Rohit's brief: expand arcroad to major world cities as a sample in a future release. Each city may have a different problem or use case, so research comes first.

**Status:** groundwork only. Nothing is collected, measured or published. Registry: `data/world/sample_cities.json`. The collector (`tools/multicity_collect.py`) can now read it for coverage and population checks only; `--detour` is blocked for world cities.

## What the research says

1. **The problem has a name and a literature.** Researchers call it *community severance* or the *barrier effect* of roads.
   - UCL's Street Mobility project built and triangulated a toolkit on Finchley Road, London (Mindell et al., *Journal of Transport Geography* 60, 2017, CC BY).
   - Columbia built a Community Severance Index for New York City and linked it to more collisions, including pedestrian and cyclist injuries (Benavides et al., *Environment International*, 2024).
   - arcroad's contribution is different: a measured, driven, per-crossing detour from open data, with pre-registered ground truth.
2. **The same driving problem exists elsewhere.**
   - **Metro Manila:** MMDA U-turn slots replaced signalised junctions, and slots are closed by advisory. Seven EDSA slots were closed for the busway in 2020, with official detours.
   - **Dhaka:** median U-turns, and unauthorised median cuts made by road users and then closed by the Roads and Highways Department.
3. **Elsewhere the cost falls on people walking.**
   - **Nairobi:** pedestrians are the largest group of road deaths. Thika Superhighway and Outer Ring Road are repeatedly ranked among the deadliest, and footbridges are blocked by hawkers or used by motorcycles.
   - **Dhaka:** a field count at eight overpasses found about 45% of pedestrians crossed without using them, mostly where the bridge was far from where people wanted to cross.
   - These match the Mumbai foot-overbridge finding already in the evidence base.
4. **In rich countries the issue is repair.** The US Reconnecting Communities programme funded highway caps and crossings in its 2022–25 rounds, and its future was in doubt in 2025. A measured before/after detour is exactly what such projects lack.
5. **The data exists, unevenly.**
   - OpenStreetMap roads were estimated at about 83% complete worldwide (Barrington-Leigh and Millard-Ball, 2017). Dense cities are among the best mapped.
   - Building footprints are far less complete in much of the Global South (Herfort et al., *Nature Communications*, 2023).
   - Mapillary (CC BY-SA) covers 190+ countries but unevenly. Coverage must be probed per city, as it was for Hyderabad.
   - GHSL population is global, so the existing population weighting works everywhere.

## The sample (7 cities, 4 roles)

| City | Role | Problem | Metric |
|---|---|---|---|
| Metro Manila | Replication | Closed U-turn slots on divided arterials | Driving detour index, before/after dated closures |
| Dhaka | Replication + walking | Median U-turns, median cuts, unused overpasses | Driving detour + walking crossing gap |
| Nairobi | New use case: walking | Highway severance, footbridges far apart or blocked | Walking detour to nearest legal crossing |
| New York City | Validation benchmark | Expressways splitting neighbourhoods | Detours compared with the published severance index |
| London | Validation benchmark | Busy arterials as walking barriers | Crossing gaps compared with the UCL case study |
| Bogotá | New use case: transit corridor | BRT corridors concentrating crossings | Walking gap along corridors |
| São Paulo | New use case: linear barrier | River expressways splitting districts | Driving and walking detour across them |

## What has to be built before any world city is measured

1. **A walking metric.** It uses the pedestrian network: footways, crossings and footbridges, with steps counted. It needs its own pre-registered rules and its own ground truth. Hyderabad's open map has too few crossings for this to work there today (see the home page FAQ).
2. **Road class everywhere.** Expressways and motorways are severance by design. They are reported as their own class, the lesson learned from Hyderabad's Outer Ring Road spots.
3. **A ground-truth plan per city before publication.** Either a local partner who walks or drives a pre-registered sample, or a sample checked against dated official advisories (Manila).
4. **Local terms.** Each city's official data has its own licence. Each is checked before ingest, as was done for India.
5. **Language.** Every city page names the authority that owns the road, never a person or community. The Hyderabad rules apply unchanged.

## Order of work (proposed)

1. **Coverage probe for all seven, desk only:** OSM road and crossing counts, GHSL population, Mapillary image count. This is the existing collector, run without `--detour`.
2. **Manila first:** it is the cleanest replication of the Hyderabad method.
3. **New York or London next,** to validate against an independent index.
4. **Walking metric,** designed and tested on Nairobi and Dhaka.
5. **Public sample page:** only cities that pass their own ground-truth gate.

## Sources (to re-check before any public use)

- Mindell J.S. et al. (2017). Using triangulation to assess a suite of tools to measure community severance. *J. Transport Geography* 60:119–129.
- Benavides J. et al. (2024). Development of a community severance index for urban areas in the United States: New York City. *Environment International*, doi:10.1016/j.envint.2024.108526.
- Barrington-Leigh C., Millard-Ball A. (2017). The world's user-generated road map is more than 80% complete. *PLoS ONE* 12(8):e0180698.
- Herfort B. et al. (2023). Completeness and inequalities of global urban building data in OpenStreetMap. *Nature Communications* 14:3985.
- MMDA U-turn slot closures, EDSA busway, Sep–Dec 2020 (Philippine Star, Inquirer).
- RHD median U-turn closures, Matuail–Sanarpar, Dhaka (The Business Standard).
- NTSA hazard mapping and 2024 crash data, Nairobi (Eastleigh Voice, The Star, Business Daily).
- US DOT Reconnecting Communities and Neighborhoods programme (Streetsblog USA, Planetizen, 2024–25).
