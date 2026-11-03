"""Render the 1200x630 share cards in web/og/ from the film posters.

Run from the repo root: python3 tools/og/make_og.py
"""
import html
import pathlib
import subprocess
import tempfile

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[2]
WEB = ROOT / "web"
OUT = WEB / "og"

CARDS = {
    "home": ("drive", "The other side is 13 metres away.", "The legal way round is 1.58 km.", "5 of 5 driven directions matched the model"),
    "drive": ("drive", "Ride the detour we drove.", "13 m across the median, 1.58 km around it.", "Day, night and 3D dive"),
    "evidence": ("timelapse", "Civic sense, measured.", "What studies and official crash data actually show.", "Peer-reviewed and official sources only"),
    "cost": ("drive", "What does crossing your own road cost you?", "In rupees, minutes and fuel, over ten years.", "Cost calculator"),
    "globe": ("orbit", "From orbit to your street.", "29 cities, measured from open data.", "Explore the globe"),
    "glare": ("night", "Blinded by an oncoming high beam.", "Sit in the driver's seat and see what disappears.", "Built on CIE glare equations"),
    "field": ("timelapse", "Every pass we drove, matched or not.", "Hyderabad, 1 and 2 November 2026.", "Driven results"),
}

LOGO = ('<svg viewBox="0 0 32 32"><g fill="none" stroke="#E2743B" stroke-linecap="round">'
        '<path d="M12 25 A 10 10 0 1 1 20 25" stroke-width="2.8"/></g>'
        '<circle cx="12" cy="25" r="2.4" fill="#E2743B"/><circle cx="20" cy="25" r="2.4" fill="#E2743B"/></svg>')
SEEK = {"blueprint": 10, "orbit": 1.5, "night": 6, "timelapse": 6, "drive": 3}
SEEK_CARD = {"evidence": 11, "cost": 8, "globe": 4.5}

PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:Inter;font-weight:400;src:url('{f}/inter-latin-400-normal.woff2')}}
@font-face{{font-family:Inter;font-weight:600;src:url('{f}/inter-latin-600-normal.woff2')}}
@font-face{{font-family:Mono;font-weight:500;src:url('{f}/jetbrains-mono-latin-500-normal.woff2')}}
html,body{{margin:0;width:1200px;height:630px;background:#0B0D10;overflow:hidden}}
.bg{{position:absolute;inset:0;background:url('{img}') right center/cover no-repeat;filter:saturate(1.1)}}
.sh{{position:absolute;inset:0;background:linear-gradient(90deg,#0B0D10 0%,#0B0D10 40%,rgba(11,13,16,.55) 66%,rgba(11,13,16,.15) 88%,rgba(11,13,16,.1) 100%),linear-gradient(0deg,rgba(11,13,16,.85) 0%,rgba(11,13,16,0) 40%)}}
.c{{position:absolute;left:72px;top:64px;right:420px;bottom:64px;display:flex;flex-direction:column;font-family:Inter}}
.brand{{display:flex;align-items:center;gap:14px;color:#E6E8EB;font-weight:600;font-size:30px;letter-spacing:-.01em}}
.brand svg{{width:44px;height:44px}}
h1{{margin:auto 0 0;color:#F5F6F7;font-weight:600;font-size:64px;line-height:1.04;letter-spacing:-.025em}}
p{{margin:22px 0 0;color:#C9CDD2;font-size:28px;line-height:1.3}}
.tag{{margin-top:34px;display:flex;gap:18px;align-items:center;font-family:Mono;font-size:19px;letter-spacing:.07em;text-transform:uppercase;color:#E2743B}}
.tag i{{width:40px;height:2px;background:#E2743B}}
.url{{position:absolute;right:56px;bottom:52px;font-family:Mono;font-size:20px;color:#E6E8EB;opacity:.85}}
</style></head><body><div class="bg"></div><div class="sh"></div>
<div class="c"><div class="brand">{logo}arcroad</div><h1>{h}</h1><p>{s}</p><div class="tag"><i></i>{t}</div></div>
<div class="url">arcroad.org</div></body></html>"""


def main():
    OUT.mkdir(exist_ok=True)
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1200, "height": 630}, device_scale_factor=1)
        for name, (film, h, s, t) in CARDS.items():
            src = WEB / "drive/media/films" / f"{film}-1440.mp4"
            img = pathlib.Path(tempfile.gettempdir()) / f"og-{name}.png"
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(SEEK_CARD.get(name, SEEK[film])), "-i", str(src),
                            "-frames:v", "1", str(img)], check=True)
            doc = PAGE.format(f=(WEB / "fonts").as_uri(), img=img.as_uri(), logo=LOGO,
                              h=html.escape(h), s=html.escape(s), t=html.escape(t))
            tmp = OUT / f".{name}.html"
            tmp.write_text(doc)
            pg.goto(tmp.as_uri())
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(150)
            pg.screenshot(path=str(OUT / f"{name}.jpg"), type="jpeg", quality=86)
            tmp.unlink()
        b.close()


if __name__ == "__main__":
    main()
