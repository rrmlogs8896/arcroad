"""Open administrative map of Telangana for a district drill-down: districts, mandals, and a census of
what the open map holds below them (villages, wards).

One-off base-data job. Everything comes from OpenStreetMap through the Overpass API (ODbL 1.0), fetched
politely: one request per district, a pause between requests, mirrors as fallback. Nothing here is a
finding, and nothing private enters this job. Boundaries in the open map are volunteers' work: the
manifest records counts so gaps are visible, and nothing is filled in by guessing.
"""
from __future__ import annotations

import datetime as dt
import io
import json
import tarfile
import time
import urllib.parse
from pathlib import Path

from corridor3d import OVERPASS, get

STATE = "Telangana"
PAUSE = 8  # seconds between requests
HEAD = "[out:json][timeout:300][maxsize:536870912];"


def q_state():
    return HEAD + f'rel["boundary"="administrative"]["admin_level"="4"]["name"="{STATE}"];out ids;'


def q_level(area_rel, level, how="geom"):
    return HEAD + (f'rel(area:{3600000000 + area_rel})["boundary"="administrative"]["admin_level"="{level}"];'
                   f"out {how};")


def q_places(area_rel):
    return HEAD + f'node(area:{3600000000 + area_rel})["place"~"^(village|hamlet|town|suburb|neighbourhood)$"];out;'


def ask(q):
    return json.loads(get(OVERPASS, urllib.parse.urlencode({"data": q}).encode())).get("elements", [])


def rings(rel):
    """Outer rings of a boundary relation as lists of [lon, lat], built from its member ways."""
    from shapely.geometry import LineString
    from shapely.ops import polygonize, unary_union
    lines = [LineString([(p["lon"], p["lat"]) for p in m["geometry"]]) for m in rel.get("members", [])
             if m.get("type") == "way" and m.get("role") in ("outer", "") and len(m.get("geometry") or []) >= 2]
    if not lines:
        return []
    polys = sorted(polygonize(unary_union(lines)), key=lambda p: -p.area)
    out = []
    for p in polys:
        s = p.simplify(0.0004, preserve_topology=True)  # about 40 m
        if not s.is_empty and s.geom_type == "Polygon":
            out.append([[round(x, 5), round(y, 5)] for x, y in s.exterior.coords])
    return out


def feature(rel, parent=None):
    t = rel.get("tags", {})
    return {"id": rel["id"], "name": t.get("name:en") or t.get("name"), "name_te": t.get("name:te"),
            "level": t.get("admin_level"), "parent": parent, "rings": rings(rel)}


def run(log, out_dir: Path):
    started = dt.datetime.now(dt.UTC).isoformat()
    notes, layers = [], {"districts": [], "mandals": [], "places": [], "lower_levels": {}}
    state = ask(q_state())
    if not state:
        raise RuntimeError("the open map returned no state boundary")
    sid = state[0]["id"]
    time.sleep(PAUSE)
    drels = ask(q_level(sid, 5))
    layers["districts"] = [feature(r) for r in drels]
    log(f"adminmap districts {len(drels)}")
    for d in drels:
        name = d.get("tags", {}).get("name", d["id"])
        for key, q, keep in (("mandals", q_level(d["id"], 6), lambda r, did=d["id"]: feature(r, did)),
                             ("places", q_places(d["id"]), lambda n, did=d["id"]: {"id": n["id"], "name": n.get("tags", {}).get("name"),
                                                                      "kind": n.get("tags", {}).get("place"), "district": did,
                                                                      "at": [round(n["lon"], 5), round(n["lat"], 5)]})):
            time.sleep(PAUSE)
            try:
                got = ask(q)
            except (OSError, ValueError) as e:
                notes.append(f"{name}: {key} not fetched ({e})")
                log(f"adminmap {name} {key} skipped: {e}")
                continue
            seen = {x["id"] for x in layers[key]}
            layers[key] += [keep(x) for x in got if x["id"] not in seen]
        log(f"adminmap {name}: mandals {sum(1 for m in layers['mandals'] if m['parent'] == d['id'])}")
    for level in ("7", "8", "9", "10"):  # what exists below the mandal: counted, with centres, not drawn yet
        time.sleep(PAUSE)
        try:
            got = ask(q_level(sid, level, "tags center"))
            layers["lower_levels"][level] = [{"id": r["id"], "name": r.get("tags", {}).get("name"),
                                              "at": [round(r["center"]["lon"], 5), round(r["center"]["lat"], 5)] if r.get("center") else None}
                                             for r in got]
        except (OSError, ValueError) as e:
            notes.append(f"level {level} not counted ({e})")
    manifest = {"job": "adminmap-v1", "status": "BASE DATA, NOT A FINDING", "state": STATE, "started": started,
                "finished": dt.datetime.now(dt.UTC).isoformat(),
                "source": "OpenStreetMap via the Overpass API (main instance, public mirrors as fallback)",
                "licence": "ODbL 1.0, © OpenStreetMap contributors",
                "counts": {"districts": len(layers["districts"]), "mandals": len(layers["mandals"]),
                           "districts_without_shape": sum(1 for x in layers["districts"] if not x["rings"]),
                           "mandals_without_shape": sum(1 for x in layers["mandals"] if not x["rings"]),
                           "places": len(layers["places"]),
                           "lower_levels": {k: len(v) for k, v in layers["lower_levels"].items()}},
                "expected": {"districts": 33, "mandals_about": 620},
                "notes": notes,
                "caveat": "Open-map boundaries are volunteers' work and may be missing or out of date. Indian "
                          "external boundaries are not taken from this job."}
    out_dir.mkdir(exist_ok=True)
    tgz = out_dir / "adminmap.tar.gz"
    with tarfile.open(tgz, "w:gz") as t:
        for name, obj in {"manifest": manifest, **layers}.items():
            b = json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode()
            info = tarfile.TarInfo(f"adminmap/{name}.json")
            info.size = len(b)
            t.addfile(info, io.BytesIO(b))
    return tgz
