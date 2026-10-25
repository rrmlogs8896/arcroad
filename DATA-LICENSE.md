# Licence for data, as distinct from code

Two different licences apply to this repository, because two different things
live in it.

## Code — MIT

Everything in `pipeline/`, `tests/`, `notebooks/` and `web/` is MIT licensed.
See `LICENSE`. Use it for anything, including commercially, without obligation
beyond keeping the notice.

## Data — ODbL 1.0

The measurements this project produces are a derived database built from
OpenStreetMap, and they are published under the **Open Database License 1.0**,
the same licence OSM itself carries.

- Source: map data © OpenStreetMap contributors, ODbL 1.0.
- arcroad's derived measurements — detour indices, ring bands, sector
  aggregates, area rankings — are a Derivative Database under ODbL §4.
- If you publicly use these measurements, attribute both OpenStreetMap and
  arcroad, and share any adapted database under ODbL.

### What the share-alike obligation does not reach

ODbL distinguishes a Derivative Database from a **Produced Work** — a map
image, a chart, an article. A Produced Work made from this data needs
attribution but does not itself have to be ODbL. So a newspaper may publish a
chart drawn from these numbers without licensing the newspaper under ODbL.

### Attribution text

> Map data © OpenStreetMap contributors (ODbL). Measurements by arcroad (ODbL).

## Why the split

The code is a method and spreads further if it is free of obligation. The data
inherits ODbL from OpenStreetMap and could not be relicensed even if we wanted
to — and share-alike is the right outcome anyway: a corrected or extended road
access dataset should return to the commons it came from.
