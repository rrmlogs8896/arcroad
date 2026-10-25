"""Check that pipeline/pairing.py reproduces the notebook it was ported from.

B-09, 26 Oct 2026. The pairing logic was ported out of
HMA_Phase2a_DetourIndex_v07.ipynb and arcroad_Phase2e_Diagnostics_v10.ipynb, which
live outside the repository. This script builds a random synthetic road network
(divided arterials at random headings and 8-60 m separations, bridges, U-turns,
shared nodes, random local streets, and dyadic-coordinate carriageways that
produce EXACT distance ties), runs the notebook's own cells verbatim on it, runs
pipeline.pairing on it, and requires identical pairs, distances, flags and
rejection counts.

Rule 5. Hypothesis: the port is faithful. Competing: it differs in ordering,
tie-breaking, stride, de-duplication or the sample cap in a way small graphs hide.
Separates: any single mismatch. Sensitivity was checked on 26 Oct by planting four
mutations (tie-break < to <=, no de-duplication, minimum distance, sample cap);
every one was caught.

    python tools/check_pairing_port.py PATH/TO/notebook.ipynb [seed ...]

Needs numpy, scipy and pandas. The preset (V10 or V07) is chosen from the
notebook's own FOCUS_ZONE line. Exit status 1 on any mismatch.
"""

import collections
import json
import math
import os
import random
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline import pairing

# Notebook cells: 4 config, 8 algorithm, 12 graph, 14 components, 16 pairing,
# 20 routing, 22 records. Identical indices in v07 and v10.
CONFIG_CELL, ALGO_CELL, STEP_CELLS = 4, 8, (12, 14, 16, 20, 22)
COLUMNS = ("straight_m", "network_m", "detour_index", "unreachable", "near_limit",
           "flagged_high", "diff_component", "core_city", "patancheru", "lat", "lon")


def synthetic_network(seed):
    rnd = random.Random(seed)
    coords, ways = {}, []
    nid, wid = [1000], [1]

    def node(lon, lat):
        nid[0] += rnd.randint(1, 3)
        coords[nid[0]] = (lon, lat)
        return nid[0]

    def way(nodes, tags):
        fwd, bwd = pairing.oneway_dirs(tags)
        div = tags.get("oneway") in ("yes", "true", "1", "-1") or tags.get("dual_carriageway") == "yes"
        ways.append((wid[0], nodes, fwd, bwd, tags["highway"], div, pairing.way_level(tags)))
        wid[0] += 1

    for _ in range(40):
        lon0, lat0 = 77.9 + rnd.random() * 1.0, 17.0 + rnd.random() * 0.8   # some outside HMDA
        h = rnd.random() * 2 * math.pi
        sep = rnd.uniform(8, 60)
        n = rnd.randint(5, 25)
        step = rnd.uniform(40, 120) / 111000
        dx, dy = math.cos(h) * step, math.sin(h) * step
        ox, oy = -math.sin(h) * sep / 111000, math.cos(h) * sep / 111000
        hw = rnd.choice(["trunk", "primary", "secondary", "motorway", "tertiary"])
        lvl = {"bridge": "yes"} if rnd.random() < 0.15 else {}
        c1 = [node(lon0 + k * dx + rnd.uniform(-2e-5, 2e-5), lat0 + k * dy) for k in range(n)]
        c2 = [node(lon0 + k * dx + ox, lat0 + k * dy + oy) for k in range(n)][::-1]
        way(c1, {"highway": hw, "oneway": "yes", **lvl})
        way(c2, {"highway": hw, "oneway": rnd.choice(["yes", "-1"]) if rnd.random() < 0.3 else "yes"})
        if rnd.random() < 0.7:
            way([c1[-1], c2[0]], {"highway": hw + "_link" if hw != "tertiary" else "tertiary"})
        if rnd.random() < 0.5:
            way([c2[-1], c1[0]], {"highway": "unclassified"})
        if rnd.random() < 0.4:
            mid = c1[n // 2]
            way([mid, node(coords[mid][0] + 3e-4, coords[mid][1] + 3e-4)], {"highway": "residential"})
    for r in range(6):   # exact ties: dyadic coordinates, far-kerb nodes at half steps
        lon0, lat0, dx = 78.25 + r * 0.0625, 17.375, 2.0 ** -12
        sep = 2.0 ** -14 * (1 + r % 3)
        c1 = [node(lon0 + k * dx, lat0) for k in range(8)]
        c2 = [node(lon0 + (k + 0.5) * dx, lat0 + sep) for k in range(-1, 8)][::-1]
        way(c1, {"highway": "trunk", "oneway": "yes"})
        way(c2, {"highway": "trunk", "oneway": "yes"})
        way([c1[-1], c2[0]], {"highway": "trunk_link"})
    ids = list(coords)
    for _ in range(60):
        a, b = rnd.sample(ids, 2)
        way([a, b], {"highway": "residential"})
    return coords, ways


def check(cells, seed):
    src = ["".join(c["source"]) for c in cells]
    coords, ways = synthetic_network(seed)

    ns = {"display": lambda *a, **k: None, "print": lambda *a, **k: None,
          "collections": collections}
    exec(src[CONFIG_CELL], ns)
    exec(src[ALGO_CELL], ns)
    ns["g"] = types.SimpleNamespace(ways=ways, coords=coords)
    for i in STEP_CELLS:
        exec(src[i], ns)
    res = ns["res"]

    cfg = pairing.V10 if "FOCUS_ZONE    = None" in src[CONFIG_CELL] else pairing.V07
    run = pairing.run_pairing(ways, coords, config=cfg, study_bbox=(-180, -90, 180, 90))

    nb_pairs = [(int(ns["node_ids"][s]), int(ns["node_ids"][t]))
                for s, t in zip(ns["sources"], ns["targets"], strict=True)]
    po_pairs = [(r["a_node_id"], r["b_node_id"]) for r in run.records]
    if nb_pairs != po_pairs:
        return f"seed {seed}: pair lists differ ({len(nb_pairs)} notebook, {len(po_pairs)} port)"
    for k, r in enumerate(run.records):
        for c in COLUMNS:
            a, b = res.iloc[k][c], r[c]
            a_null = a is None or (isinstance(a, float) and math.isnan(a))
            if not ((a_null and b is None) or a == b):
                return f"seed {seed}: row {k} column {c}: notebook {a!r}, port {b!r}"
    if dict(ns["rej"]) != dict(run.rejections):
        return f"seed {seed}: rejection counts differ"
    n_null = sum(r["network_m"] is None for r in run.records)
    print(f"seed {seed} [{cfg.label}]: {len(po_pairs)} pairs identical, {n_null} null, "
          "rejections identical")
    return None


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    cells = json.load(open(argv[1]))["cells"]
    seeds = [int(s) for s in argv[2:]] or [1, 2, 3, 4, 5]
    failures = [f for f in (check(cells, s) for s in seeds) if f]
    for f in failures:
        print("MISMATCH", f)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
