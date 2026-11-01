# How sure are we? arcroad's evidence levels

This page is published on arcroad.org as written. The code that applies it is
`pipeline/evidence.py`; the two must always say the same thing.

Every place on arcroad is graded on its own, **separately for each direction of
travel**, because the trip from one side of a road can be very different from the
trip back.

| Level | What it means | What the site shows |
|---|---|---|
| **1 · Driven by arcroad** | We drove it ourselves with a GPS recording, and the trip passed our pre-set test. If the real trip was much shorter, the map was out of date there. | The distance, with the date we drove it. When the map was wrong, the distance we actually drove, labelled as a correction. |
| **2 · Confirmed by others' drives** | At least one recent drive by someone else (a street-photo run with timestamps) matched the map's distance, from a source that has proved itself (see below), and nothing contradicts it. | The distance, with the date and a link to the photos. |
| **3 · Modelled** | Only the map's own calculation so far. | The distance, clearly marked **candidate, not yet confirmed**. |
| **4 · Disputed** | Something disagrees with the map: a recent drive was much shorter, another map or aerial imagery shows a crossing the map lacks, or a photographed sign allows U-turns there. | No distance. The place is marked for checking, with the reason. |

## How a source earns our trust

We don't assume a data source is right. We test it.

For every place we check, we also check a **control**: two points along an
ordinary two-way road, where no detour should exist. A source that is reliable
should agree with the map on those. We count how often it does, and take a
deliberately cautious estimate of that rate (the lower end of a 95% Wilson
interval). A source is used only if it has been tested on at least 3 controls
and that cautious estimate is at least 50%. Each source's score is published next
to the results.

## Freshness

Roads change: median openings are cut and closed. Evidence from before the map's
last edit at a place, or more than two years old, can't raise or dispute a place.
It is shown as history.

## Independence

Several photo runs by the same person on the same day count as one.

## What never happens

- A threshold is never changed after seeing results. Changes are dated and
  explained in the repository.
- Nothing is called a finding at level 3 or 4.
- Reports from the public never enter a published distance. They decide where we
  check next.
- No Google Maps data is used anywhere, ever.

Map data © OpenStreetMap contributors (ODbL). Street-level imagery © Mapillary
contributors (CC BY-SA 4.0). Measurements by arcroad (ODbL).
