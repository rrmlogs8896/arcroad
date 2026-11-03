"""Build tools/films/land.js: points on a sphere that fall on land, for the orbit film.

Source: Natural Earth 1:50m land (public domain) via the npm package world-atlas@2 (ISC),
converted to GeoJSON with topojson-client@3. Not published; only the rendered film is.

  npm pack world-atlas@2 topojson-client@3   (then untar each)
  node -e "<topojson-client feature(topo, topo.objects.land) -> land.geojson>"
  python3 tools/films/make_land.py /path/to/land.geojson
"""
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

W, H, N = 4096, 2048, 160_000


def main(src):
    gj = json.loads(Path(src).read_text())
    img = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(img)

    def px(lon, lat):
        return ((lon + 180) / 360 * W, (90 - lat) / 180 * H)

    feats = gj["features"] if gj["type"] == "FeatureCollection" else [gj]
    geoms = []
    for f in feats:
        g = f["geometry"]
        geoms += g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    for poly in geoms:
        for i, ring in enumerate(poly):
            d.polygon([px(*c) for c in ring], fill=0 if i else 255)
    pts = []
    golden = math.pi * (3 - math.sqrt(5))
    for i in range(N):
        y = 1 - 2 * (i + 0.5) / N
        lat = math.degrees(math.asin(y))
        lon = math.degrees((i * golden) % (2 * math.pi)) - 180
        x, yy = px(lon, lat)
        if img.getpixel((min(W - 1, int(x)), min(H - 1, int(yy)))):
            pts.append(f"{lat:.2f},{lon:.2f}")
    out = Path(__file__).with_name("land.js")
    out.write_text("window.LAND=[" + ",".join(pts) + "];\n")
    print(len(pts), "land points ->", out)


if __name__ == "__main__":
    main(sys.argv[1])
