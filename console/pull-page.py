#!/usr/bin/env python3
"""pull-page.py <raw.json> <out-dir>

Writes one pulled Confluence page as <out-dir>/<title>.md in the baseline page format: frontmatter with
page id, title, version, url, parent id and pulled-on date, then the page prose as plain text and every
table as a Markdown table, cell for cell. Nothing is renamed or dropped.

raw.json is what the import skill saves from the connector:
  {"id": "401", "title": "Requirements", "version": 7, "url": "https://…", "parentId": "400", "body": "<storage html>"}
Run inside the console image so nothing is installed on the host:
  docker run --rm -v "$PWD:/work" -w /work register-console python /app/pull-page.py raw.json out/
"""
import sys, os, json, re, datetime
from html.parser import HTMLParser

MONTHS = "January February March April May June July August September October November December".split()


class Page(HTMLParser):
    """Linear walk: headings and paragraphs become text blocks, tables become row lists."""
    def __init__(self):
        super().__init__(); self.blocks = []; self.table = None; self.row = None; self.cell = None; self.text = []; self.h = None
    def flush_text(self):
        t = " ".join("".join(self.text).split())
        if t: self.blocks.append(("p", t))
        self.text = []
    def handle_starttag(self, tag, a):
        if tag == "table": self.flush_text(); self.table = []
        elif tag == "tr" and self.table is not None: self.row = []
        elif tag in ("td", "th") and self.row is not None: self.cell = []
        elif tag in ("h1", "h2", "h3", "h4"): self.flush_text(); self.h = (int(tag[1]), [])
        elif tag == "br":
            if self.cell is not None: self.cell.append("<br>")
            else: self.text.append("\n")
        elif tag in ("p", "li", "div") and self.cell is None: self.flush_text()
    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cell is not None:
            self.row.append(" ".join("".join(self.cell).split()).replace("|", "\\|")); self.cell = None
        elif tag == "tr" and self.row is not None: self.table.append(self.row); self.row = None
        elif tag == "table" and self.table is not None: self.blocks.append(("table", self.table)); self.table = None
        elif tag in ("h1", "h2", "h3", "h4") and self.h: self.blocks.append(("h", self.h[0], " ".join("".join(self.h[1]).split()))); self.h = None
        elif tag in ("p", "li", "div") and self.cell is None: self.flush_text()
    def handle_data(self, d):
        if self.cell is not None: self.cell.append(d)
        elif self.h: self.h[1].append(d)
        else: self.text.append(d)


def today():
    d = datetime.date.today(); return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


def render(raw):
    p = Page(); p.feed(raw.get("body", "")); p.flush_text()
    out = ["---", f"page-id: {raw['id']}", f"page-title: {raw['title']}", f"page-version: {raw.get('version', '')}",
           f"page-url: {raw.get('url', '')}", f"parent-page-id: {raw.get('parentId', '')}", f"pulled-on: {today()}", "---", "", f"# {raw['title']}", ""]
    for n, b in enumerate(p.blocks):
        if b[0] == "h" and n == 0 and b[2].strip().lower() == raw["title"].strip().lower():
            continue
        if b[0] == "h": out += ["#" * max(2, b[1]) + " " + b[2], ""]
        elif b[0] == "p": out += [b[1], ""]
        else:
            rows = [r for r in b[1] if any(c.strip() for c in r)]
            if not rows: continue
            w = max(len(r) for r in rows)
            rows = [r + [""] * (w - len(r)) for r in rows]
            out.append("| " + " | ".join(rows[0]) + " |"); out.append("|" + "---|" * w)
            out += ["| " + " | ".join(r) + " |" for r in rows[1:]]; out.append("")
    return "\n".join(out)


if __name__ == "__main__":
    raw = json.load(open(sys.argv[1], encoding="utf-8")); outdir = sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    name = re.sub(r"[^\w\- ]+", "", raw["title"]).strip() or raw["id"]
    path = os.path.join(outdir, name + ".md")
    open(path, "w", encoding="utf-8").write(render(raw))
    print(path)
