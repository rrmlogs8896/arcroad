# Pre-registration: roadside activity and slow traffic, from arcroad's own drive photos

Written 11 Nov 2026 at 19:20 IST. The photo labels already exist (an AI model labelled about 1,800 drive photos, 1 to 7 Nov 2026), but no tabulation of congestion against any other label has been run or seen. Nothing below changes once results are seen except by a dated entry under "Changes", applied to every result.

## Question

On the roads arcroad drove, is traffic more often slow where establishments spill onto the road (shops, stalls, parking on the carriageway, vendors) than where they do not, at the same kind of road and the same time of day?

## What this study does not claim

- It does not claim that roadside activity causes jams. It reports an association in our own photos.
- It does not claim that jams are rising: one set of drives in one week cannot show a trend. A trend needs the same places photographed again, which is a later study.
- No photo is published. Photos show people and number plates; only counts derived from them are published.
- Nothing about walking.

## Data

- Labels: `_work/labels-v1.jsonl` and `_work/n7/labels-2026-11-07.jsonl` (private), one line per photo, model and time recorded.
- **Usable photo:** `image_quality` = usable, `view` = windscreen, a parsed label set, and a GPS fix. Photos whose model output did not parse (207 of 1,817 when this was written) are left out and their count is published; they are not re-parsed by hand.
- **Time:** the camera clock (IST), as recorded in `dt`.
- **De-duplication:** photos from the same drive within 50 m and 2 minutes of each other count as one (the first), so a single queue photographed many times counts once.

## Definitions (fixed now)

- **Slow (outcome):** `congestion` is slow, queue or standstill. **Free:** `congestion` is free. Unsure is left out.
- **Roadside activity (exposure):** `establishment_spillover` = yes, or `parking_on_carriageway` is one_lane_partly, one_lane or more, or `vendors_on_carriageway` = yes. **None:** all three are explicit no or none. Any unsure, with no yes, is left out.
- **Strata:** road type (highway, arterial, street, service_road) × time band (peak: 08:00–11:00 and 17:00–21:00 IST; off-peak: otherwise). Flyovers are left out.

## Hypothesis, competing explanation, and what separates them (rule 5)

- **Hypothesis H.** Within the same road type and time band, a larger share of photos is slow where there is roadside activity.
- **Competing explanation C.** Roadside activity and slow traffic merely occur at the same places and hours (busy commercial streets at peak), so the raw association is confounding.
- **What separates them.** The comparison is made only within strata, using strata with at least 30 usable photos in each arm (the minimum `pipeline.diagnostics.stratified_compare` uses). In each stratum the difference is the slow share with activity minus the slow share without; strata are combined by inverse-variance weighting (Wald variance; a share of exactly 0 or 1 is computed as if 0.5 photo were moved, so its variance is not zero), with a 95% interval of ±1.96 standard errors (`pipeline/roadside.py`). H is supported if the combined difference is at least 10 percentage points and its interval excludes zero. Below 10 points, or an interval including zero: not supported, reported as such. If no stratum reaches 30 per arm, the study reports "not enough photos" and nothing else.

Even if H is supported, C is only partly answered: the strata fix road type and hour, not the place. A busy commercial street could be slow for reasons other than its roadside activity. The result is therefore reported as an association within strata, never as a cause.

## The labels are checked before anything is published

The labels come from an AI model. Before any figure is published, 50 usable photos are drawn at random (seed recorded first) and labelled by a person for `congestion` and the three exposure fields, without seeing the model's labels or any result. The sample is drawn and labelled before the comparison is run (`tools/roadside_study.py sample`, then `run`). Each field must agree with the person on at least 80% of the 50. A field below 80% is dropped from the study, and that is published.

## Changes

(none yet)

## Record

- 11 Nov 2026, before writing the analysis: a format check counted parsed and unparsed records and displayed the first record of each file (one of them unparsed). No label was counted against another.
