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
| `large_vehicle_turning` | none, bus, truck, other_large, unsure (a large vehicle making a U-turn or turn in view) |
| `multi_point_turn` | yes, no, unsure (a vehicle visibly reversing or stopped across lanes to complete a turn) |
| `surface` | adds `waterlogged` |

Added by amendment (13 Nov 2026), under the narrow exception now in AGENTS.md:

| Field | Values |
|---|---|
| `people_on_carriageway` | none, crossing, along_the_edge, both, unsure |
| `foot_over_bridge` | none, visible, unsure |

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

- 12 Nov 2026, 18:20 IST, before any v3 label exists and before any opening is scored: added the section
  "U-turn openings: where one may not be needed, and where one may be missing" below.
- 12 Nov 2026, 19:40 IST, before any v3 label exists: added the two large-vehicle fields above and the section
  "Room to turn" below, after a public post by ITS India's president on U-turns too tight for trucks.
- 12 Nov 2026, 20:15 IST, before any opening is scored: H3's bus requirement registered, and room to turn
  redefined to match the source the requirement comes from (see "Room to turn: the registered values").
- 12 Nov 2026, 23:40 IST, before any v3 label exists: which photos are labelled. From the Baseline v1 drives
  (1–6 Nov), only the 1,188 photos marked for labelling in Baseline v1 are labelled; that thinning was made
  before any label existed, so it cannot follow a result. The 7 Nov photos and every photo from later drives
  are all labelled. The count from each drive day is published with every result.
- 12 Nov 2026, 23:59 IST, before any v3 label exists: the 60-photo check was drawn (seed recorded) from the
  1,620 photos of 1–7 Nov, before the 12 Nov photos were added; they are labelled but are not in the check. The
  model labels before Rohit fills the check: he fills it without opening the label file or any result, and the
  scoring tool alone reads both. Only photos taken during the drive and placed by their own GPS inside the study
  corridors are labelled; no other photo is sent to the model.
- 13 Nov 2026, 00:35 IST, before any label is counted: Rohit lifted "nothing about walking" for two
  photo-observed fields (people on the carriageway, a visible foot over-bridge), as a narrow exception written
  into AGENTS.md. The schema becomes v3.1; about 180 photos labelled under v3 that night are labelled again so
  every photo has the same fields. Glare is recorded as present or not; it is never linked to a crash.
- 13 Nov 2026, 17:15 IST, before any photo from the area below is labelled or any of its speeds is examined:
  an exploratory area is added, the highway approach between the study corridors and the edge of the city,
  first recorded on a 13 Nov trip by auto-rickshaw (a passenger trip counts as a drive). Photos and speeds from
  it are labelled and reported separately, marked "exploratory, not tested", and never pooled into H1–H3 or
  any registered result. The same privacy rules apply: nothing within 1 km of home, no people, no number
  plates. Photos are chosen by trip time window, starting after the trip leaves the 1 km home zone.
- 13 Nov 2026, 17:15 IST, correction of a citation, no change to any threshold: the 500 m spacing benchmark
  for median openings is IRC:SP:84 cl. 2.14.1 (a highway concession manual, used here as a benchmark only);
  IRC:SP:87 cl. 2.14 concerns emergency crossings and is no longer cited for it.
- 14 Nov 2026, 13:30 IST, after the v3 label check and before any v3 result was computed: the v3 check failed.
  Of 28 fields only light, view and animal on carriageway reached 80% agreement; the model mostly answered
  "unsure" where Rohit was definite, and it had been given no definitions. No v3 field except those three is
  used anywhere. Schema v4 keeps the same fields and adds a written definition for each, an instruction to
  answer "unsure" only when the relevant part of the scene is not visible, and larger images (1,568 px). The
  definitions were written after seeing where v3 disagreed with Rohit's 60 answers, so those 60 photos are no
  longer a fair test: v4 is scored on a fresh draw of 40 photos (27 day, 13 night, seed recorded), excluding
  the 60 and the exploratory trip, which Rohit labels without seeing any model label. The 80% threshold and
  every other rule are unchanged. The v3 scores are kept and published with the result.
- 14 Nov 2026, 18:30 IST, after scoring v4 and before any v4 result is computed: v4 reached 80% overall agreement
  on 16 of 28 fields, but on the photos where Rohit saw the item (U-turn queue 3, vehicle against flow 2,
  stationary vehicle 2, large vehicle turning 1, multi-point turn 1) the model caught none, and parking 1 of 5.
  Overall agreement is therefore not enough when an item is rare. Rule added for every future check: a field is
  used only if it reaches 80% overall agreement AND the model finds at least 80% of the items the person saw,
  with at least 10 such items in the check. No v4 field meets it, so no photo-derived rate is reported. Photos
  are used only as person-verified evidence at named sites, chosen by GPS, never by model label.

## U-turn openings: where one may not be needed, and where one may be missing

Every median opening in the study area (`pipeline/medians.py`, as registered in
`docs/PREREG-uturn-spacing.md`) gets one record, built from four sources:

| Source | What it gives for each opening |
|---|---|
| OpenStreetMap road graph | **Detour saved:** the extra distance a U-turn movement would need if this opening were closed (shortest legal route with and without it) |
| Drive recordings (GPS 1 per second, speed, heading) | **Time paid:** every U-turn made on a drive is found from the heading (a turn of 150° or more within 50 m), and the time from slowing below 10 km/h to leaving the turn is the wait at that opening. Also the within-pass speed ratio of H2 |
| Photos (schema v3) | **Space taken:** queue spill into through lanes and lanes blocked within 150 m |
| Open population and destination data | **Need:** residents (GHSL) and destinations (OpenStreetMap) within 500 m, used only as a ranking, since the population cross-check has not yet passed |

**"Worth a second look: may not be needed."** An opening is listed only if all three hold: closing it adds
less than 500 m to the U-turn movement (another opening or junction serves it); and it shows a cost, meaning
a median wait of at least 60 seconds over at least 5 recorded U-turns, or queue spill in at least 20% of at
least 10 photos; and a person checks it on the ground (the spacing study's ground check) before it is named.

**"Worth a second look: a crossing may be missing."** A stretch of divided road is listed if crossing it
needs at least 2 km of extra driving (model, and both public routers within 15% of the model), and at least
2 photos within 300 m show a vehicle against the flow. *Competing explanation:* vehicles go against the flow
to reach a gate or shop on the same side, not to cross. *Test:* the share of photos with a vehicle against
the flow is compared between stretches with long crossings (2 km or more) and short ones (under 500 m) on the
same road type and time band. The "missing crossing" reading is used only if it is at least 10 percentage
points higher on the long stretches, with a 95% interval above zero. Otherwise the list is not published and
the result says the photos cannot tell the two apart.

Neither list says an opening causes a jam or that anyone should be blamed. Each is a list of places to
check, with the measurement that would show whether a change helped.

## Room to turn

A U-turn a car makes in one sweep may need a bus or truck to stop across lanes and reverse. For every opening,
the room to turn is measured from OpenStreetMap: the separation between the two carriageways plus the width of
the carriageway being turned into (its mapped `width`, or its `lanes` at 3.5 m each where width is not mapped;
which one was used is recorded per opening). Openings on TGSRTC bus routes are marked from the timetable.

**H3.** Where the room to turn is less than a bus needs to turn in one sweep, photos show a multi-point turn or
queue spill into through lanes more often than at openings with enough room. *Competing:* tight openings sit on
busier stretches, so more blockage there comes from traffic, not geometry. *Test:* the comparison is made within
road type and time band, and repeated with congestion (`congestion` slow or worse) as a further stratum; the
same pass bar as H1. The bus turning width used is taken from published Indian design guidance, cited here by an
amendment before the openings are scored. Until then H3 is not run.

Openings with too little room are reported as places to check, not as design faults.

### Room to turn: the registered values

No Indian code found gives a U-turn width for a bus. IRC:86-2018 (cl. 5.6) says only that "even greater widths
are required for U-turns". The registered requirement is therefore an international one, labelled as such
wherever it is used:

- **Source:** Michigan DOT minimum median widths for U-turns, Table 1 in FHWA-HRT-07-033 (US Federal Highway
  Administration). Design vehicle: a 12.2 m bus.
- **Measure:** M, the median width between the two carriageways' inner edges, as that source defines it. This
  replaces the earlier "separation plus receiving carriageway" measure; the receiving carriageway's lane count
  is used instead, as below.
- **A bus can turn in one sweep** if M is at least 24.4 m (into the near lane), 20.7 m (into the second lane,
  where the receiving carriageway has at least 2 lanes) or 17.7 m (into the third, where it has 3 or more).
  An opening is "too little room for a bus" if M is below the value for the farthest lane its receiving
  carriageway has.
- **Indian cross-check, reported beside it, not used for H3:** IRC:SP:41-1994 Table 4.5 gives a 12.2 m minimum
  turning radius for the WB-12 semi-trailer and single-unit bus. The printed table is to be checked before it is
  quoted.
- **Spacing benchmark, reported for every opening:** IRC:SP:84-2014 cl. 2.14 and IRC:SP:87-2019 cl. 2.14 (four-
  and six-laning of national highways) place median openings at least 500 m apart in built-up areas. These codes
  apply to national highways (such as NH65), so for other roads the distance is reported as context, not as a
  breach.

Where M is not mapped, it is taken from the distance between the two carriageway centrelines minus half of each
carriageway's width (lanes × 3.5 m), and the opening is marked as estimated. H3 is run on mapped and estimated
openings separately as well as together.
