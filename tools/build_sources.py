"""Build web/data/sources.csv: every outside source the public pages cite, one row per link.
Run from the repo root: python3 tools/build_sources.py [--check]"""
import csv, html, io, os, re, sys
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")
OUT = os.path.join(WEB, "data", "sources.csv")
SKIP_HOSTS = {"wa.me", "twitter.com", "x.com", "www.linkedin.com", "www.facebook.com", "t.me",
              "arcroad.org", "www.arcroad.org", "cyberabadmoves.in"}
SKIP_DIRS = {"jury", "_to_delete"}
URL = re.compile(r"https?://[A-Za-z0-9.-]+\.[a-z]{2,}[^\s\"'<>`]*")
DATA_ONLY = {"www.w3.org", "tiles.openfreemap.org"}
A = re.compile(r'<a\b[^>]*href="(https?://[^"]+)"[^>]*>(.*?)</a>', re.S | re.I)
BLOCKS = re.compile(r"<!-- (share|nav|event):start -->.*?<!-- \1:end -->", re.S)


def page_url(rel):
    rel = rel.replace(os.sep, "/")
    return "/" + (rel[:-10] if rel.endswith("index.html") else rel)


def collect():
    rows = {}
    for d, dirs, files in os.walk(WEB):
        dirs[:] = sorted(x for x in dirs if x not in SKIP_DIRS)
        for f in sorted(files):
            rel = os.path.relpath(os.path.join(d, f), WEB)
            if f.endswith((".json", ".js")) and f != "ask-index.json":
                raw = open(os.path.join(d, f), encoding="utf-8", errors="ignore").read()
                for url in set(URL.findall(raw)):
                    url = url.rstrip(".,);'")
                    host = urlparse(url).netloc.lower()
                    if host in SKIP_HOSTS or host in DATA_ONLY or "github.com/rrmlogs8896/arcroad" in url and "arcroad-open" not in url:
                        continue
                    r = rows.setdefault(url, {"title": host, "host": host, "pages": set()})
                    r["pages"].add("data file " + page_url(rel))
                continue
            if not f.endswith(".html"):
                continue
            s = BLOCKS.sub("", open(os.path.join(d, f), encoding="utf-8").read())
            s = re.sub(r"<script.*?</script>|<style.*?</style>", "", s, flags=re.S)
            for url, text in A.findall(s):
                url = html.unescape(url).strip()
                host = urlparse(url).netloc.lower()
                if host in SKIP_HOSTS or "github.com/rrmlogs8896/arcroad" in url and "arcroad-open" not in url:
                    continue
                title = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", text))).strip() or host
                r = rows.setdefault(url, {"title": title, "host": host, "pages": set()})
                if len(title) > len(r["title"]):
                    r["title"] = title
                r["pages"].add(page_url(rel))
    return rows


def render(rows):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["source", "website", "link", "cited on arcroad pages"])
    for url, r in sorted(rows.items(), key=lambda kv: (kv[1]["host"], kv[1]["title"].lower())):
        w.writerow([r["title"], r["host"], url, " ".join(sorted(r["pages"]))])
    return buf.getvalue()


if __name__ == "__main__":
    text = render(collect())
    if "--check" in sys.argv:
        sys.exit(0 if os.path.exists(OUT) and open(OUT, encoding="utf-8").read() == text
                 else "web/data/sources.csv is out of date: run tools/build_sources.py")
    open(OUT, "w", encoding="utf-8").write(text)
    print("wrote", OUT, text.count("\n") - 1, "sources")
