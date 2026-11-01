# The arcroad engine — what a street is like to live with

Set 1 Nov 2026 from Rohit's brief: the engine combines citizen behaviour, civic sense, vehicle behaviour, potholes, ad-hoc cut-ins, temporary stops, barricades and construction stages, mapped against official government data, plus the fixed things in the road that obstruct daily life (structures of any kind, trees, poles, kiosks). Everything is combined into one model per stretch of road, which drives the score, the immersive ride and the public record.

## Layers

| Layer | What it captures | How it is measured | Code |
|---|---|---|---|
| 1. Network | Legal paths, median gaps, U-turns, one-ways | OSM network + driven ground truth | `groundtruth.py`, `filters.py` |
| 2. Detour | What crossing your own road costs: metres, minutes, waits | Driven pass per spot | `fieldkit.scene` |
| 3. Surface | Potholes, broken patches, speed breakers | Vertical jolts at speed, repeat passes, photos | `fieldkit.jolts` |
| 4. Behaviour | Sudden stops, cut-ins and jinks, wrong-side driving, stops in the carriageway | Hard braking (GPS), short yaw spikes at speed (gyro), photos | `fieldkit.hard_brakes`, `fieldkit.swerves` |
| 5. Works | Barricades, diversions, construction stage (dug, half-built, finished, abandoned) | Photos dated by EXIF, matched to official works records | planned |
| 6. Fixed obstructions | Anything permanent in the carriageway or footpath: a structure, a tree, a transformer, a pole, a kiosk | OSM tags and photos, checked against official encroachment and works lists | planned |
| 7. Civic | Who is responsible for this stretch, and what they have said or promised | Road owner (NHAI, ORR operator, corporation), works orders, court directions | `directory.py` |

## Rules that make the combination trustworthy

1. **Every event is a candidate until confirmed** by a second pass, a photo or an official record. Thresholds are fixed in code before any data is looked at (rule 5).
2. **Behaviour is aggregate, never personal.** No number plates, faces or identifiable vehicles are stored or shown. A stretch can be "frequent sudden stops at 6 pm"; a person or vehicle never appears.
3. **Fixed obstructions are described by what they do, never by who they belong to.**
   - A structure in the carriageway is recorded as "permanent structure, narrows the road from 3 lanes to 2", whatever its kind. A place of worship is never labelled as an obstruction by faith, and no faith or community is singled out.
   - Where it matters legally, the record cites the official position. The Supreme Court's interim order of 29 Sep 2009 in *Union of India v. State of Gujarat* (SLP (C) 8519/2006) bars new unauthorised religious construction of any faith on public streets, parks and public places, and later orders made each state responsible for review. The record cites the order and the responsible office, not the structure's religion.
   - Trees are recorded the same way, and never with a suggestion to cut them: the city's tree and works authorities decide.
4. **Official data wins on facts, measurement wins on conditions.** A works order says what was planned and when. A dated photo says what is there today. Where they disagree, both are shown with their dates.
5. **Every published item keeps its provenance:** source, date observed, pass count, method version.

## Official data to map against (licence check before ingest)

- **Works and diversions:** corporation (GHMC/CMC/MMC) e-procurement works orders, Hyderabad Traffic Police diversion advisories, HMRL works notices, NHAI project status and NH concession maintenance duties.
- **Road ownership:** NHAI (national highways), HMDA/IRB Golconda (ORR), corporations (city roads).
- **Encroachment policy:** the Supreme Court orders in SLP (C) 8519/2006 (primary: main.sci.gov.in/judgment/judis/35617.pdf) and Telangana's compliance policy or GO under it (to find and verify).
- **Trees:** Telangana's Water, Land and Trees Act 2002 and the corporation's tree-felling permission process (to verify).

## Status (1 Nov 2026)

- Layers 2 to 4 are built in `fieldkit` with tests. Layers 5 and 6 are designed here. Their sources still need checking, and nothing in them is published before that.
- The first real data is today's field day (8 spots). It is scored with the thresholds above and not adjusted afterwards.
