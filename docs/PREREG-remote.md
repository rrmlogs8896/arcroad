# Pre-registration: remote corroboration (remote-v1)

Written 4 Nov 2026, before any request was sent. Implements constitution Art 4g. Changes are dated below and made before a run, never after.

## Purpose
Check a modelled detour without anyone on the ground, and say exactly how it was checked.

## The three checks, per place
1. Routers: in tonight's router cross-check, OSRM and Valhalla both within ±15% of the model in at least one direction.
2. Map edits: no road, turn-rule or signal edit within 1 km in the last 48 hours (tonight's map-edit watch).
3. Street photos: Mapillary photos (CC BY-SA 4.0) within 40 m of the place, taken in the last two years, at most 4 per place.

## AI sorting, and its limits
- A Claude model sorts each photo into "gap visible", "no gap visible" or "unclear". It is told to ignore people, vehicles and number plates and to describe only the road layout.
- Sorting decides only what a person looks at first. It never sets a level, a number or a label on the site.
- An unreadable reply counts as "unclear", never as a guess.
- Spending cap: at most 96 photos sorted per night.

## Gate to "Corroborated remotely"
A place is put on the review list when check 1 passes, check 2 shows no edits, and at least one photo is sorted "no gap visible" or "unclear". It becomes "Corroborated remotely" on the site only when Rohit (or a named reviewer) has looked at the photo itself and confirmed the median is closed at the place, with the photo's date shown beside the label. The label never says "verified" or "100%".

## Privacy and keys
- No image is stored, only the photo id, date, distance and a link to the photo on Mapillary.
- The Mapillary token and the API key are Cloudflare secrets typed into a hidden prompt; they are never in a file, the repo or a chat.

## Known limitations
- Photo coverage in Hyderabad is thin; most places will have no photo.
- A photo shows the road on the day it was taken; openings change. The date always travels with the label.

## Changes
(none yet)

**Amendment, 5 Nov 2026, before any photo was sorted.** A place where any photo is sorted "gap visible" goes on a separate dispute list for a person, whatever the routers or map edits say: a photo that contradicts the model is exactly the case a person must see. Without this, the AI's "gap visible" label decided on its own that nothing needed looking at. The dispute list is never published; a place becomes "Disputed" only after a person has looked at the photo.
