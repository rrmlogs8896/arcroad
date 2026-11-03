# Pre-registration: the loop rule for close-set places (3 Nov 2026)

Written 3 Nov 2026 at 23:20 IST. It was written after the 3 Nov drive was seen, so it is a declared post-hoc method change: it is stated here, applied to every drive on file, and the results it produces are marked as counted under a rule changed after the drive.

## Problem
At places where the two sides (A and B) are under about 40 m apart, phone GPS (about ±8 m) cannot tell the carriageways apart. The pairing rule then finds only a few metres of GPS wobble while stopped near the median, which is rejected, and misses the real U-turn loop.

## Rule
Applies only where A and B are 40 m apart or less, and only where the pairing rule finds no valid pass.
1. A loop starts at a closest approach to the place (midpoint of A and B) within 10 m.
2. The drive must then go at least 60 m away, turn round (direction of travel changes by 120° or more), and come back to within 10 m, all within 30 minutes.
3. Driven distance = track length between the two closest approaches.
4. Which side the loop started on comes from the direction of travel at the first approach: traffic keeps left, so the car is on the carriageway to its left. That decides A → B or B → A.
5. Verdict thresholds are unchanged (MATCH within 150 m or 25%).
6. If two recordings of the same drive exist, the one with the smaller largest gap between samples is used.

## Applied to every drive on file
- 1 Nov: to be re-run on the iMac (tracks are private and not in this workspace). Its published passes are at places where the pairing rule already found valid passes, so the rule does not apply to them.
- 2 Nov: finds S12 A → B, 1,990 m, the same direction as the published pairing result (1,951 m). Published figure unchanged.
- 3 Nov: finds S10 A → B, 1,121 m (model 1,126 m) and S08 B → A, 404 m (model 432 m). Both MATCH.

## Changes
(none yet)
