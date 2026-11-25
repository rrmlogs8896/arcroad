"""Build web/ask-index.json for Ask arcroad: every page's title and sections, plain text, from the built HTML.

Stdlib only. Run: python3 build_ask_index.py <web_dir>
"""
import json
import os
import re
import sys
from html.parser import HTMLParser

WEB = os.path.abspath(sys.argv[1])
SKIP_TAGS = {"script", "style", "nav", "footer", "svg", "noscript", "template", "button", "select"}
BLOCK = {"p", "li", "td", "th", "figcaption", "blockquote", "dd", "dt", "small"}
HEAD = {"h1", "h2", "h3"}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.in_title = False
        self.skip = 0
        self.cur = None
        self.buf = []
        self.sections = []
        self.head = ""
        self.hid = ""
        self.mode = None
        self.stack = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title":
            self.in_title = True
        if tag in VOID:
            return
        start_skip = tag in SKIP_TAGS or "ev-banner" in (a.get("class") or "") or "hidden" in a
        self.stack.append((tag, start_skip))
        if start_skip:
            self.skip += 1
            return
        if self.skip:
            return
        if tag in HEAD:
            self.flush()
            self.mode = "h"
            self.buf = []
            self.hid = a.get("id") or self.hid
        elif tag in BLOCK and self.mode != "h":
            self.mode = "p"
        if tag in ("section", "article") and a.get("id"):
            self.hid = a["id"]

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if tag in VOID:
            return
        was_skip = False
        while self.stack:
            t, sk = self.stack.pop()
            if sk:
                self.skip = max(0, self.skip - 1)
            if t == tag:
                was_skip = sk
                break
        if was_skip or self.skip:
            return
        if tag in HEAD and self.mode == "h":
            self.head = " ".join("".join(self.buf).split())
            self.buf = []
            self.mode = None
            self.sections.append({"h": self.head, "id": self.hid, "t": ""})
        elif tag in BLOCK and self.mode == "p":
            self.buf.append(" ")

    def handle_data(self, data):
        if self.in_title:
            self.title += data
            return
        if self.skip:
            return
        self.buf.append(data)

    def flush(self):
        text = " ".join("".join(self.buf).split())
        if text:
            if not self.sections:
                self.sections.append({"h": "", "id": "", "t": ""})
            s = self.sections[-1]
            s["t"] = (s["t"] + " " + text).strip()
        self.buf = []

    def close(self):
        self.flush()
        super().close()


pages = []
for root, _, files in os.walk(WEB):
    for f in files:
        if not f.endswith(".html") or f == "404.html":
            continue
        path = os.path.join(root, f)
        rel = os.path.relpath(path, WEB).replace(os.sep, "/")
        url = "/" + (rel[:-10] if rel.endswith("index.html") else rel)
        with open(path, encoding="utf-8") as fh:
            html = fh.read()
        if re.search(r'<meta[^>]+name="robots"[^>]+noindex', html):
            continue
        p = Page()
        p.feed(html)
        p.close()
        secs = []
        for s in p.sections:
            t = re.sub(r"\b([01]?[0-9]|2[0-3]):[0-5][0-9]\b", "", s["t"])
            t = re.sub(r"\s+", " ", t)[:900]
            if len(t) < 40 and not s["h"]:
                continue
            secs.append({"h": s["h"][:140], "id": s["id"], "t": t})
        title = " ".join(p.title.split()).replace("arcroad · ", "")
        if secs:
            pages.append({"u": url, "title": title[:120], "s": secs[:40]})

pages.sort(key=lambda x: (x["u"].count("/"), x["u"]))
out = os.path.join(WEB, "ask-index.json")
with open(out, "w", encoding="utf-8") as fh:
    json.dump({"_build": "ar-" + __import__("hashlib").sha256(json.dumps(pages, sort_keys=True).encode()).hexdigest()[:12], "built": "2026-11-26", "pages": pages}, fh, ensure_ascii=False, separators=(",", ":"))
print(f"ask-index: {len(pages)} pages, {sum(len(p['s']) for p in pages)} sections, {os.path.getsize(out)//1024} KB")
