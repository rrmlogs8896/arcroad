"""Collect candidate data for one city, outside Colab.

Runs the same steps as notebooks/arcroad_MultiCity_CatchUp_v01.ipynb on any Linux
machine (GitHub Actions runs it monthly): OSM extract clipped to a collection box,
GHSL population for the box, a Phase 1 coverage snapshot and, optionally, Phase 2a
candidate Detour Index points from the same ``pipeline/`` code and V10 config.

Every output is a CANDIDATE. Nothing here is published, ranked or compared across
cities. Collection boxes are approximate metro extents, not official boundaries.

Usage:
    python tools/multicity_collect.py pune --out out [--detour]
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pipeline import metrics, pairing
from pipeline.filters import is_divided_proxy, strip_military

# (min_lon, min_lat, max_lon, max_lat). Approximate metro extents sized near the
# HMDA box. Replace with a declared study area before any figure is used.
CITIES = {
    "hyderabad": pairing.HMDA_BBOX,
    "bengaluru": (77.300, 12.650, 77.950, 13.300),
    "chennai": (79.950, 12.700, 80.350, 13.350),
    "mumbai_mmr": (72.750, 18.850, 73.250, 19.450),
    "delhi_ncr": (76.850, 28.350, 77.550, 28.900),
    "pune": (73.600, 18.350, 74.100, 18.750),
    "kolkata": (88.150, 22.350, 88.600, 22.800),
    "ahmedabad": (72.400, 22.850, 72.800, 23.200),
}

CLIP_BUFFER_DEG = 0.20  # F-3: graph clipped wider than we measure
GEOFABRIK_INDEX = "https://download.geofabrik.de/index-v1.json"
GHSL_TILES = (
    "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_POP_GLOBE_R2023A/"
    "GHS_POP_E2020_GLOBE_R2023A_4326_3ss/V1-0/tiles/"
)
GHSL_NAME = "GHS_POP_E2020_GLOBE_R2023A_4326_3ss_V1_0_R{r}_C{c}"
LAST_FETCH_ERROR = [""]  # most recent download failure, for the error message
STATUS = "CANDIDATE - UNVERIFIED, NOT FOR PUBLICATION"


def fetch(url: str, dest: pathlib.Path) -> pathlib.Path | None:
    """Download once. Returns None on failure instead of leaving a partial file."""
    if dest.exists() and dest.stat().st_size > 1000:
        return dest
    tmp = dest.with_suffix(dest.suffix + ".part")
    for attempt in range(5):
        try:
            urllib.request.urlretrieve(url, tmp)
            os.replace(tmp, dest)
            return dest
        except urllib.error.HTTPError as exc:
            tmp.unlink(missing_ok=True)
            LAST_FETCH_ERROR[0] = f"{url} -> HTTP {exc.code}"
            if exc.code == 404:  # a tile that does not exist: not worth retrying
                return None
        except Exception as exc:
            tmp.unlink(missing_ok=True)
            LAST_FETCH_ERROR[0] = f"{url} -> {exc}"
        wait = 15 * 2**attempt  # 15s, 30s, 60s, 120s, 240s: servers throttle parallel jobs
        print(f"  fetch retry {attempt + 1}/5 in {wait}s: {LAST_FETCH_ERROR[0]}")
        time.sleep(wait)
    return None


def zones_for(bbox, cache: pathlib.Path):
    """Geofabrik India zones intersecting the box, from Geofabrik's own index."""
    from shapely.geometry import box, shape

    idx = fetch(GEOFABRIK_INDEX, cache / "geofabrik_index-v1.json")
    if idx is None:
        raise SystemExit("Could not download the Geofabrik index.")
    feats = json.loads(idx.read_text())["features"]
    b = box(*bbox)
    hits = []
    for f in feats:
        url = f["properties"].get("urls", {}).get("pbf", "")
        if "/asia/india/" in url and shape(f["geometry"]).intersects(b):
            hits.append((f["properties"]["id"], url))
    if not hits:
        raise SystemExit(f"No Geofabrik India zone intersects {bbox}.")
    return hits


def clip(srcs, bbox, out: pathlib.Path, work: pathlib.Path) -> pathlib.Path:
    x0, y0, x1, y1 = bbox
    parts = []
    for i, src in enumerate(srcs):
        p = work / f"_part{i}.osm.pbf"
        subprocess.run(["osmium", "extract", "-b", f"{x0},{y0},{x1},{y1}", str(src),
                        "-o", str(p), "--overwrite", "-s", "complete_ways"], check=True)
        parts.append(p)
    if len(parts) == 1:
        shutil.move(parts[0], out)
    else:
        subprocess.run(["osmium", "merge", *map(str, parts), "-o", str(out), "--overwrite"],
                       check=True)
    return out


def ghsl_tile(r: int, c: int, cache: pathlib.Path):
    name = GHSL_NAME.format(r=r, c=c)
    z = fetch(GHSL_TILES + name + ".zip", cache / f"{name}.zip")
    if z is None:
        return None
    tifs = [n for n in zipfile.ZipFile(z).namelist() if n.endswith(".tif")]
    return f"zip://{z}!{tifs[0]}" if tifs else None


def ghsl_grid(cache: pathlib.Path) -> dict:
    """Tile grid calibrated from a real tile's bounds rather than assumed."""
    import rasterio

    for r, c in [(8, 26), (7, 26), (8, 25), (7, 25)]:
        t = ghsl_tile(r, c, cache)
        if t:
            with rasterio.open(t) as ds:
                b = ds.bounds
            dx, dy = b.right - b.left, b.top - b.bottom
            return {"dx": dx, "dy": dy, "ox": b.left - (c - 1) * dx, "oy": b.top + (r - 1) * dy}
    raise SystemExit(f"Could not calibrate the GHSL tile grid. Last download error: {LAST_FETCH_ERROR[0]}")


def ghsl_clip(bbox, out_tif: pathlib.Path, cache: pathlib.Path):
    import rasterio
    from rasterio.merge import merge

    g = ghsl_grid(cache)
    x0, y0, x1, y1 = bbox
    rows = range(int((g["oy"] - y1) // g["dy"]) + 1, int((g["oy"] - y0) // g["dy"]) + 2)
    cols = range(int((x0 - g["ox"]) // g["dx"]) + 1, int((x1 - g["ox"]) // g["dx"]) + 2)
    tiles = [t for r in rows for c in cols if (t := ghsl_tile(r, c, cache))]
    if not tiles:
        raise SystemExit("No GHSL tile covers this box.")
    srcs = [rasterio.open(t) for t in tiles]
    arr, transform = merge(srcs, bounds=bbox)
    meta = srcs[0].meta.copy()
    for s in srcs:
        s.close()
    meta.update(height=arr.shape[1], width=arr.shape[2], transform=transform, compress="deflate")
    with rasterio.open(out_tif, "w", **meta) as dst:
        dst.write(arr)
    a = arr[0]
    nodata = meta.get("nodata")
    valid = (a > 0) if nodata is None else (a != nodata) & (a > 0)
    return round(float(a[valid].sum())), len(tiles)


MAIN = {
    "motorway", "trunk", "primary", "secondary", "tertiary", "motorway_link", "trunk_link",
    "primary_link", "secondary_link", "tertiary_link", "unclassified", "residential",
    "living_street",
}
ARTERIAL = {"motorway", "trunk", "primary", "secondary"}


def coverage(pbf: pathlib.Path) -> dict:
    """Phase 1 coverage snapshot (condensed audit v0.3). Feeds no published figure."""
    import osmium

    class Coverage(osmium.SimpleHandler):
        def __init__(self):
            super().__init__()
            self.km = 0.0
            self.art_km = 0.0
            self.art_div_km = 0.0
            self.nodes = collections.Counter()
            self.restrictions = collections.Counter()
            self.footbridges = 0
            self.stripped = 0

        def node(self, n):
            hw = n.tags.get("highway")
            if hw in ("crossing", "traffic_signals"):
                self.nodes[hw] += 1

        def way(self, w):
            tags = dict(w.tags)
            hw = tags.get("highway")
            if hw == "footway" and tags.get("bridge") == "yes":
                self.footbridges += 1
            if hw not in MAIN:
                return
            tags, stripped = strip_military(tags)
            self.stripped += int(stripped)
            try:
                km = osmium.geom.haversine_distance(w.nodes) / 1000
            except Exception:
                return
            self.km += km
            if hw in ARTERIAL:
                self.art_km += km
                if is_divided_proxy(tags):
                    self.art_div_km += km

        def relation(self, r):
            if r.tags.get("type") == "restriction":
                v = r.tags.get("restriction") or r.tags.get("restriction:motorcar") or "unspecified"
                self.restrictions[v] += 1

    h = Coverage()
    h.apply_file(str(pbf), locations=True)
    return {
        "road_km": round(h.km, 1),
        "arterial_km": round(h.art_km, 1),
        "arterial_divided_pct": round(100 * h.art_div_km / h.art_km, 1) if h.art_km else 0.0,
        "crossings": h.nodes["crossing"],
        "traffic_signals": h.nodes["traffic_signals"],
        "footbridges": h.footbridges,
        "turn_restrictions": sum(h.restrictions.values()),
        "u_turn_restrictions": sum(v for k, v in h.restrictions.items() if "u_turn" in k),
        "military_tagged_stripped": h.stripped,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("city", choices=sorted(CITIES))
    ap.add_argument("--out", default="out")
    ap.add_argument("--cache", default="cache")
    ap.add_argument("--detour", action="store_true", help="also run Phase 2a candidate points")
    args = ap.parse_args(argv)

    city, bbox = args.city, CITIES[args.city]
    stamp = dt.date.today().isoformat()
    sha = pairing.commit_sha(str(pathlib.Path(__file__).resolve().parents[1]))
    out = pathlib.Path(args.out) / city / stamp
    cache = pathlib.Path(args.cache)
    out.mkdir(parents=True, exist_ok=True)
    cache.mkdir(parents=True, exist_ok=True)
    print(f"[{city}] box {bbox} | pipeline {sha}")

    zones = zones_for(bbox, cache)
    srcs = []
    for zid, url in zones:
        p = fetch(url, cache / f"{zid}-latest.osm.pbf")
        if p is None:
            raise SystemExit(f"Download failed: {url}")
        srcs.append(p)
    extract_date = pairing.extract_date(str(srcs[0]))
    b = CLIP_BUFFER_DEG
    clip_path = clip(srcs, (bbox[0] - b, bbox[1] - b, bbox[2] + b, bbox[3] + b),
                     out / f"{city}_buffered.osm.pbf", cache)
    print(f"  OSM {[z for z, _ in zones]}: {clip_path.stat().st_size / 1e6:.1f} MB, dated {extract_date}")

    pop, ntiles = ghsl_clip(bbox, out / f"{city}_ghs_pop_e2020_3ss.tif", cache)
    print(f"  GHSL: {ntiles} tile(s), population in box ~ {pop:,}")

    cov = coverage(clip_path)
    print(f"  coverage: {cov}")

    manifest = {
        "city": city, "status": STATUS, "run_date": stamp, "collection_box": list(bbox),
        "box_is_official_boundary": city == "hyderabad", "clip_buffer_deg": b,
        "osm_zones": [z for z, _ in zones], "osm_extract_date": extract_date, "commit_sha": sha,
        "ghsl_product": "GHS_POP_E2020_GLOBE_R2023A_4326_3ss_V1_0 (CC BY 4.0)",
        "ghsl_pop_in_box": pop, "coverage_on_buffered_extract": cov,
        "attribution": ("Map data (c) OpenStreetMap contributors (ODbL). "
                        "GHSL (c) European Union, JRC (CC BY 4.0)."),
    }

    # Save collection results first, so a detour failure never loses them.
    (out / "MANIFEST.json").write_text(json.dumps(manifest, indent=2, default=str))

    if args.detour:
        g = pairing.load_network(str(clip_path))
        graph = pairing.build_graph(g.ways, g.coords)
        run = pairing.run_pairing(g.ways, g.coords, config=pairing.V10,
                                  zones={f"{city}_all": bbox}, study_bbox=bbox,
                                  osm_extract_date=extract_date, sha=sha, graph=graph)
        routed = [r["detour_index"] for r in run.records
                  if r["detour_index"] is not None and not r["diff_component"]]
        if run.records:
            pairing.write_point_file(run.records,
                                     str(out / f"di_points_{city}_{stamp}_{(sha or 'nosha')[:7]}.csv"),
                                     run.meta)
        h = metrics.headline_stats(routed) if routed else {}
        manifest["detour_candidate"] = {
            "pairs_kept": len(run.records), "routed": len(routed),
            "uncensored_median": h.get("median"),
            "note": "ratio use within this city only; no absolute value until a drive",
        }
        print(f"  detour: {len(run.records):,} pairs, {len(routed):,} routed")

    (out / "MANIFEST.json").write_text(json.dumps(manifest, indent=2, default=str))
    print(f"  done -> {out}")
    return 0


def _report(exc: BaseException) -> None:
    """Surface the failure as a GitHub annotation, readable through the API even
    where the full job log is not."""
    import traceback

    tb = "".join(traceback.format_exception(exc))[-3000:]
    print(tb, file=sys.stderr)
    if os.environ.get("GITHUB_ACTIONS") == "true":
        enc = tb.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        print(f"::error title=multicity_collect failed::{enc}")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit as stop:
        if isinstance(stop.code, str) and os.environ.get("GITHUB_ACTIONS") == "true":
            print(f"::error title=multicity_collect stopped::{stop.code}")
        raise
    except BaseException as exc:
        _report(exc)
        raise SystemExit(1) from exc
