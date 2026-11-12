# Pre-registration: the street ledger (what occupies the IT-corridor roads, and what it costs)

Written 12 Nov 2026, before any photo is labelled with the fields below and before any v1 label is counted
for this study. Builds on the street evidence report specification (6 Nov 2026) and the roadside-activity
study (`docs/PREREG-roadside-activity.md`), which stays as written.

## What this is

A record of what the photos from arcroad's drives show on the road: what takes space from moving traffic,
where, and at what hour. It is placed against open map data and against arcroad's measured detours, so that
proposals for the roads rest on what was seen rather than on opinion.

It covers the roads that were driven, at the hours they were driven. It is not a survey of Hyderabad, and no
figure from it is presented as one. A map of which roads and hours the photos cover is published with every
result.

## The photos

- Every drive photo from 1 Nov 2026 onwards, including later drives, labelled once with the fields below
  (schema v3). Earlier labels (v1, v2) are not reused; the v3 run labels every photo again, so all photos are
  labelled the same way.
- Place: the photo's own GPS. If it has none, its time placed on that day's GPS track, within 5 seconds of a
  track point; otherwise the photo is left out and counted.
- Usable: `image_quality` usable and `view` windscreen. Unusable photos are counted and published as a count.
- Duplicates: as in the roadside study, photos within 50 m and 2 minutes of an earlier kept photo are dropped.
- Road: each photo is matched to the nearest OpenStreetMap road within 25 m (extract dated at run time);
  photos further away are counted as unmatched.

## Fields (schema v3)

The labeller records objects and space only. It never describes a person, reads a number plate or a face, or
judges intent. Every field allows "unsure", which is never counted as yes or no.

Kept from v2: image quality, light, view, road type, congestion, signs, signal visible, median, U-turn queue,
vehicle against the flow, parking on the carriageway, establishment spill-over, footpath, surface, vendors on
the carriageway.

New in v3:

| Field | Values |
|---|---|
| `u_turn_queue_spill` | none, into_through_lane, unsure |
| `lanes_blocked` | 0, 1, 2_or_more, unsure (through lanes not usable because something is stationary in them) |
| `parked_against_flow` | yes, no, unsure |
| `construction` | none, barricades_only, active_work, material_or_debris, unsure |
| `construction_stage` | not_applicable, excavation, structure, surfacing, complete_not_open, unsure |
| `construction_vehicle_on_carriageway` | yes, no, unsure |
| `stationary_vehicle_in_lane` | none, hazard_or_bonnet_up, other_stopped, unsure |
| `animal_on_carriageway` | none, live, carcass, unsure |
| `oncoming_glare` | not_night, none, strong, unsure |
| `street_lighting` | not_night, lit, partly_lit, dark, unsure |
| `surface` | adds `waterlogged` |

Left out: people walking or crossing, and foot over-bridges. arcroad's standing rules say nothing about
walking. They change only if Rohit changes that rule, and then by a dated amendment here, before any label is
counted.

## The labels are checked before anything is counted

- Rohit labels 60 photos drawn at random with a recorded seed (40 by day, 20 at night) without seeing the
  model's labels or any result.
- A field is used only if the model agrees with him on at least 80% of the photos where he gave a definite
  answer. Fields that fail are named in every result and not used.
- Rare items (animals, carcasses, broken-down vehicles, construction vehicles) are too rare for a random
  sample to check. Rohit reviews every photo the model marks positive for them. Only the positives he
  confirms are counted, and they are reported as "seen N times at these places", never as a rate.

## What is reported

1. **How often, where, when.** For each field that passed, the share of usable photos showing it, by road and
   by time band (peak 08–11 and 17–21 IST, off-peak, night), with a 95% interval (Wilson). A cell is shown
   only with at least 30 photos.
2. **Map against street.** How often the photos agree with OpenStreetMap on median openings and signals.
   Disagreements are listed privately as map-lag candidates and checked before any is published.
3. **Hypotheses**, each with its competing explanation and the test that separates them (rule 5):

   **H1 (lane loss at U-turn openings).** On the same road type and time band, a through lane is blocked more
   often within 150 m of a U-turn opening than elsewhere. *Competing:* openings sit at busy frontages, so the
   blockage comes from frontage activity, not from the opening. *Test:* the comparison is repeated within
   strata of establishment spill-over and carriageway parking. H1 is supported only if the difference is at
   least 10 percentage points with a 95% interval above zero overall and also within those strata (method of
   `pipeline/roadside.py`, at least 30 photos in each arm of a stratum). If it holds overall but vanishes within
   strata, the competing explanation is the one reported.

   **H2 (speed at openings).** On the same pass along the same carriageway, GPS speed within 150 m of a U-turn
   opening is lower than 300–600 m away. *Competing:* openings sit near junctions and bus stops that slow
   traffic anyway. *Test:* passes with a signal (OSM) or a bus stop (TGSRTC timetable) within 150 m of the
   opening are left out. H2 is supported if the median within-pass speed ratio is 0.85 or lower with a 95%
   bootstrap interval below 1, over at least 30 passes.

   The roadside-activity hypothesis is tested separately, as already registered.
4. **Cost.** The detour cost per crossing (measured detours, cost calculator) is reported as now. Time lost at
   openings is costed only if H2 is supported, as minutes × a stated, sourced value of time, with low,
   central and high values.

## What this study will not claim

- That anything caused a crash, an injury, a death or an animal's death, or that glare caused a crash.
  Photos show what was present, not what it caused.
- That anything is rising or falling; that needs the same places photographed again later.
- That any person or vehicle broke a rule. The labels record space and objects, not violations.
- Anything about Hyderabad as a whole.

## Proposals

Each proposal names a stretch, what the evidence there shows, the change, and the measurement that would show
whether it worked (before and after, same method). Proposals are tests to run, not conclusions.

## Privacy

No photo, face, number plate or raw GPS is published. Results are published only for cells of at least 30
photos. No result is published for any place within 1 km of the driver's home. Photos are labelled on the
driver's computer; they leave it only for the labelling model.

## Presentation

A stylised 3D model of the driven corridors may show the fields that passed the label check, placed where
they were seen. It is an illustration of the counted results, built from them; it carries no new evidence
and copies no scene.

## Running order

1. This document is committed.
2. The v3 labeller is committed, with the schema above.
3. The 60-photo check is drawn and labelled by Rohit.
4. The model labels every photo.
5. The agreement is scored; failing fields are dropped.
6. Analysis runs once, on the committed code.

## Amendments

(none yet)
