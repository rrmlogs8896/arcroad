"""Render the home-page films frame by frame and encode them.

  python3 tools/films/render.py thread [--frames 0,90,200] [--still]
Renders tools/films/films.html?film=<id> at 1920x1080 CSS px x2 (3840x2160) in headless Chromium,
steps the film's clock at 30 fps, and pipes JPEG frames to ffmpeg as a high-quality 4K master.
Tier encodes (480..2160) are made from the master by tools/films/encode.sh.
"""
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
OUT = Path("/home/claude/films-out")


def main():
    film = sys.argv[1]
    stills = None
    if "--frames" in sys.argv:
        stills = [int(x) for x in sys.argv[sys.argv.index("--frames") + 1].split(",")]
    OUT.mkdir(exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        pg = b.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=2)
        if film == "drive":
            return render_drive(pg, stills)
        pg.goto((ROOT / "films.html").as_uri() + f"?film={film}")
        pg.wait_for_function("window.FILM && document.fonts.status === 'loaded'", timeout=120000)
        D, fps = pg.evaluate("[FILM.D, FILM.fps]")
        n = int(round(D * fps))
        if stills is not None:
            for f in stills:
                pg.evaluate(f"FILM.set({f / fps})")
                pg.screenshot(path=str(OUT / f"{film}-{f:04d}.jpg"), type="jpeg", quality=90)
            return
        master = OUT / f"{film}-master.mp4"
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(fps), "-c:v", "mjpeg", "-i", "-",
                               "-c:v", "libx264", "-preset", "veryfast", "-crf", "12", "-pix_fmt", "yuv420p", str(master)], stdin=subprocess.PIPE)
        for f in range(n):
            pg.evaluate(f"FILM.set({f / fps})")
            ff.stdin.write(pg.screenshot(type="jpeg", quality=94))
            if f % 30 == 0:
                print(film, f, "/", n, flush=True)
        ff.stdin.close()
        ff.wait()
        print("master", master)
        b.close()


def render_drive(pg, stills):
    """Film 1: the /drive/ scene itself (above view, S18 west to east), through the page's capture hooks."""
    import base64
    pg.goto((ROOT.parent.parent / "web" / "drive" / "index.html").as_uri())
    pg.wait_for_function("window.__arcroadDrive", timeout=120000)
    pg.add_style_tag(content=".stage{position:fixed!important;inset:0!important;width:1920px!important;height:1080px!important;margin:0!important;border-radius:0!important;aspect-ratio:auto!important;z-index:99;border:0!important}")
    pg.wait_for_timeout(500)
    pg.evaluate("(() => { const d = window.__arcroadDrive; d.capture(); d.S.above = true; d.S.rate = 18.4; window.__n = 0; for (let i = 0; i < 90; i++) d.frame(1 / 30, i * 1000 / 30); })()")
    fps, n = 30, 343
    def frame():
        url = pg.evaluate("(() => { const d = window.__arcroadDrive; window.__n++; if (window.__n === 15) d.play(); return d.frame(1 / 30, (window.__n + 90) * 1000 / 30); })()")
        return base64.b64decode(url.split(",", 1)[1])
    if stills is not None:
        for f in range(max(stills) + 1):
            data = frame()
            if f in stills:
                (OUT / f"drive-{f:04d}.jpg").write_bytes(data)
        return
    master = OUT / "drive-master.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(fps), "-c:v", "mjpeg", "-i", "-",
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "12", "-pix_fmt", "yuv420p", str(master)], stdin=subprocess.PIPE)
    for f in range(n):
        ff.stdin.write(frame())
        if f % 30 == 0:
            print("drive", f, "/", n, flush=True)
    ff.stdin.close()
    ff.wait()
    print("master", master)


if __name__ == "__main__":
    main()
