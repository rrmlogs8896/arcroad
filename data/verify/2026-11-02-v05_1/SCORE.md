# v05.1 remote verification, scored (2 Nov 2026)

Run: notebook v05.1 standalone, OSM via Overpass at 2026-11-02 07:06Z, results saved 09:17Z.
Files: `verify.csv` (96 rows: 24 flagged places and 24 controls, both directions; identical to the Drive copy, 18,310 bytes) and `meta.json`.
Thresholds were fixed before the run (rule 5): MATCH within 150 m or 25%, SHORTER below 50%, max snap gap 60 m.

## Controls (should show no detour)
- 46 of 48 control directions show 11 m or less (car).
- C01 shows 135 m in both directions. Its two points are 481 m apart, far wider than any other control, so it is probably a placement problem, not the model. Re-check C01 on a drive.

## Own drives (ground truth)
All five driven directions MATCH:

| Place | Direction | Driven | Model (car) | Gap |
|---|---|---|---|---|
| S16 | B→A | 2,298 m | 2,382 m | −3.5% |
| S18 | A→B | 1,580 m | 1,572 m | +0.5% |
| S18 | B→A | 1,546 m | 1,378 m | +12.2% |
| S24 | A→B | 1,773 m | 1,554 m | +14.1% |
| S24 | B→A | 11,601 m | 10,492 m | +10.6% |

The model tends to come in slightly short of the real drive (U-turn bays, service-road entries).

## Flagged places
- Both directions under 60 m extra: S03 (52 m / 9 m) and S20 (13 m / 41 m). Recommended: downgrade to "no meaningful detour" unless a drive shows otherwise.
- Short in one direction only (the other is long): S07, S09, S15.
- No legal route found in one direction: S04 (B→A), S23 (B→A, car).
- S23 and S24: two-wheelers get roughly zero detour while cars face 1.5–10 km (access-controlled road). Either a real two-wheeler gap or an open-map fault. Needs a photo or a drive.

## Outside evidence
- Mapillary (B, B2): not usable this run; no passes or photos at any place.
- C (crossings data): no data. D (links): none seen.
- E (U-turn signs): only S16 (no-U-turn sign, both directions).
- F (OSM turn restrictions): none.

## Tiers
3 places "Driven by arcroad" (S16, S18, S24), 21 "Unverified". Raising tiers needs drives, not more remote passes. Next drives: S23, S20, C01.
