"""Open data for the 3D corridor model (docs/PREREG-street-ledger.md, "Presentation").

Fetches, for the IT-corridor box only, the open layers the model is built from, and packs them with a
manifest that records every source, its licence and when it was fetched:

- roads with lanes, one-way, layer, bridge and name (OpenStreetMap, ODbL)
- building outlines with height or levels where mapped (OpenStreetMap, ODbL)
- signals, bus stops, metro stations, street lamps, barriers (OpenStreetMap, ODbL)
- ground height, clipped to the box (Copernicus DEM GLO-30, free licence; ESA / Airbus)
- TGSRTC bus stops in the box (Telangana open GTFS via OpenCity)

Nothing here is a finding. It is the base the photo-checked layers are later placed on. Nothing about
walking is fetched (AGENTS.md). Private data never enters this job: no photo, no GPS track.
"""
from __future__ import annotations

import csv
import datetime as dt
import io
import json
import tarfile
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

BOX = (17.40, 78.33, 17.47, 78.42)  # south, west, north, east: the pre-registered study area
OVERPASS = "https://overpass-api.de/api/interpreter"
MIRRORS = (OVERPASS, "https://overpass.kumi.systems/api/interpreter", "https://overpass.private.coffee/api/interpreter")
DEM_URL = ("https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N17_00_E078_00_DEM/"
           "Copernicus_DSM_COG_10_N17_00_E078_00_DEM.tif")
GTFS_URL = ("https://data.opencity.in/dataset/88e2d145-7ec6-4666-88dd-6cf18b18312e/resource/"
            "1b0d18bb-b2fb-4a79-8ed0-1e071da5790c/download/telangana_opendata_gtfs_tgsrtc_08_february_2026.zip")
UA = "arcroad-research/1.0 (+https://arcroad.org)"
ROADS = ("motorway|motorway_link|trunk|trunk_link|primary|primary_link|secondary|secondary_link|"
         "tertiary|tertiary_link|unclassified|residential|service|living_street")
POINTS = ('node["highway"="traffic_signals"]', 'node["highway"="bus_stop"]', 'node["highway"="street_lamp"]',
          'nwr["railway"="station"]', 'nwr["station"="subway"]', 'nwr["public_transport"="station"]',
          'node["barrier"]')


def get(url, data=None, tries=4, timeout=600):
    urls = MIRRORS if url == OVERPASS else (url,)
    for k in range(tries):
        try:
            req = urllib.request.Request(urls[k % len(urls)], data=data, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except OSError:
            if k == tries - 1:
                raise
            time.sleep(10 if url == OVERPASS else 30 * (k + 1))
    raise RuntimeError("unreachable")


def bbox_str(box=BOX):
    return "{},{},{},{}".format(*box)


def tiles(box=BOX, n=2):
    s, w, nn, e = box
    dy, dx = (nn - s) / n, (e - w) / n
    return [(round(s + i * dy, 6), round(w + j * dx, 6), round(s + (i + 1) * dy, 6), round(w + (j + 1) * dx, 6))
            for i in range(n) for j in range(n)]


def queries(box=BOX):
    """Layer name -> list of Overpass queries. Buildings come in four tiles so no single reply is too large."""
    b = bbox_str(box)
    return {
        "roads": [f'[out:json][timeout:600];way["highway"~"^({ROADS})$"]({b});out geom;'],
        "buildings": [f'[out:json][timeout:600];way["building"]({bbox_str(t)});out geom;' for t in tiles(box)],
        "points": ["[out:json][timeout:600];(" + "".join(f"{p}({b});" for p in POINTS) + ");out center;"],
    }


def slim(osm):
    """Keep only id, tags and geometry: about half the size of the raw reply, nothing the model needs is lost."""
    out = []
    for e in osm.get("elements", []):
        x = {"type": e["type"], "id": e["id"], "tags": e.get("tags", {})}
        if "geometry" in e:
            x["geometry"] = [[round(g["lon"], 7), round(g["lat"], 7)] for g in e["geometry"]]
        elif "lon" in e:
            x["point"] = [round(e["lon"], 7), round(e["lat"], 7)]
        elif "center" in e:
            x["point"] = [round(e["center"]["lon"], 7), round(e["center"]["lat"], 7)]
        out.append(x)
    return out


def stops_in_box(gtfs_zip: bytes, box=BOX):
    s, w, n, e = box
    with zipfile.ZipFile(io.BytesIO(gtfs_zip)) as z, z.open("stops.txt") as f:
        rows = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig"))
        return [{"id": r["stop_id"], "name": r.get("stop_name", ""), "point": [float(r["stop_lon"]), float(r["stop_lat"])]}
                for r in rows if r.get("stop_lat") and s <= float(r["stop_lat"]) <= n and w <= float(r["stop_lon"]) <= e]


def dem_clip(tif_path: Path, box=BOX):
    """Ground height in the box as a list of rows (metres), with its grid. Uses rasterio."""
    import rasterio
    from rasterio.windows import from_bounds

    s, w, n, e = box
    with rasterio.open(tif_path) as ds:
        win = from_bounds(w, s, e, n, ds.transform).round_offsets().round_lengths()
        a = ds.read(1, window=win)
        t = ds.window_transform(win)
    return {"origin_lonlat": [t.c, t.f], "step_deg": [t.a, t.e], "rows": a.shape[0], "cols": a.shape[1],
            "height_m": [[round(float(v), 1) for v in row] for row in a]}


def run(log, out_dir: Path):
    started = dt.datetime.now(dt.UTC).isoformat()
    layers, sources = {}, []
    missing = []
    for name, qs in queries().items():
        seen, items = set(), []
        try:
            for q in qs:
                for x in slim(json.loads(get(OVERPASS, urllib.parse.urlencode({"data": q}).encode()))):
                    if (x["type"], x["id"]) not in seen:
                        seen.add((x["type"], x["id"]))
                        items.append(x)
        except (OSError, ValueError) as e:
            missing.append(name)
            log(f"corridor3d {name} skipped, the map servers did not answer: {e}")
            continue
        layers[name] = items
        log(f"corridor3d {name} {len(items)}")
    sources.append({"layers": list(layers), "source": "OpenStreetMap via the Overpass API (main instance, with public mirrors as fallback)", "licence": "ODbL 1.0",
                    "fetched": dt.datetime.now(dt.UTC).isoformat(), "queries": queries()})
    try:
        stops = stops_in_box(get(GTFS_URL, timeout=300))
        layers["bus_stops_gtfs"] = stops
        sources.append({"layers": ["bus_stops_gtfs"], "source": GTFS_URL, "licence": "as published by OpenCity",
                        "fetched": dt.datetime.now(dt.UTC).isoformat()})
        log(f"corridor3d gtfs stops {len(stops)}")
    except (OSError, KeyError, ValueError, zipfile.BadZipFile) as e:
        log(f"corridor3d gtfs skipped: {e}")
    try:
        tif = Path("/tmp/cop30.tif")
        tif.write_bytes(get(DEM_URL, timeout=900))
        layers["ground"] = dem_clip(tif)
        sources.append({"layers": ["ground"], "source": DEM_URL,
                        "licence": "Copernicus DEM GLO-30, free and open (ESA; produced using Copernicus WorldDEM-30, "
                                   "© DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018)",
                        "fetched": dt.datetime.now(dt.UTC).isoformat()})
        log(f"corridor3d ground {layers['ground']['rows']}x{layers['ground']['cols']}")
    except (OSError, ImportError, ValueError) as e:
        log(f"corridor3d ground skipped: {e}")
    manifest = {"job": "corridor3d-v1", "prereg": "docs/PREREG-street-ledger.md", "status": "BASE DATA, NOT A FINDING",
                "box_south_west_north_east": list(BOX), "started": started, "layers_missing": missing,
                "finished": dt.datetime.now(dt.UTC).isoformat(), "sources": sources,
                "counts": {k: (len(v) if isinstance(v, list) else 1) for k, v in layers.items()}}
    out_dir.mkdir(exist_ok=True)
    tgz = out_dir / "corridor3d.tar.gz"
    with tarfile.open(tgz, "w:gz") as t:
        for name, obj in {"manifest": manifest, **layers}.items():
            b = json.dumps(obj, separators=(",", ":")).encode()
            info = tarfile.TarInfo(f"corridor3d/{name}.json")
            info.size = len(b)
            t.addfile(info, io.BytesIO(b))
    return tgz
