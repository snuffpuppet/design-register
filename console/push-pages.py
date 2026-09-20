#!/usr/bin/env python3
"""push-pages.py <engagement-dir> [--config confluence.json] [--out <dir>]

Builds what goes back to Confluence from the registers as they stand, one file per register page, and
writes nothing to Confluence itself. The import skill pushes the files through the connector under the write
gate in confluence.json; this script only prepares them, so what will be written can be read first.

Input is the engagement: its item files, the pulled pages under baseline/, and when the baseline was
frozen, baseline/frozen.md (the id map) and baseline/verdicts.json. Each item knows the page it came from (the "Baseline import from"
line in its Notes), so a page gets back the items that came from it, now with the model's ids, columns
and status words, plus a Source id column carrying the knowledge base's own id for its pipeline.

Output, under <engagement>/push/ unless --out says otherwise:
  manifest.json          one entry per page: id, title, version pulled, mode, items, file
  <page-id>.json         {"id", "title", "version", "parentId", "mode", "body"} ready for the connector
                         body is Confluence storage format. In replace-tables mode it is the pulled page's
                         own body with the register table swapped and a note added; in new-child mode it
                         is a fresh page body and the entry carries the new title.

Run inside the console image so nothing is installed on the host:
  docker run --rm -v "$PWD:/work" -w /work register-console python /app/push-pages.py engagements/<name>
"""
import sys, os, re, json, glob, datetime, html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model as M
from baseline import guess_kind, LINK_RE, load_candidates

MONTHS = "January February March April May June July August September October November December".split()


def today():
    d = datetime.date.today(); return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


# ---------- reading the engagement ----------

def parse_item(path):
    """Section 7 item file: frontmatter, then one section per long field. Same shape server.py reads."""
    lines = open(path, encoding="utf-8").read().split("\n")
    item, i, cur = {"links": []}, 1, None
    while i < len(lines) and lines[i] != "---":
        ln = lines[i]
        if ln.startswith("  - ") and cur: item[cur].append(ln[4:].strip())
        elif re.match(r"^[a-z-]+:", ln):
            k, _, v = ln.partition(":"); v = v.strip()
            if k == "links": cur = "links"
            else: cur = None; item[k] = v
        i += 1
    sec, buf = None, []
    for ln in lines[i + 1:]:
        if ln.startswith("## "):
            if sec: item[sec] = "\n".join(buf).strip()
            sec, buf = ln[3:].strip().lower(), []
        elif sec is not None: buf.append(ln)
    if sec: item[sec] = "\n".join(buf).strip()
    if "kind" in item: item["risk-kind"] = item.pop("kind")
    item["kind"] = item["id"].split("-")[0]
    return item


def load_items(eng):
    out = []
    for kind, d in M.DIRS.items():
        for p in sorted(glob.glob(os.path.join(eng, d, f"{kind}-*.md"))):
            out.append(parse_item(p))
    return out


def id_map(bdir):
    """Source id -> our id, from frozen.md. Returns (map, frozen-on); both empty when the baseline was never frozen."""
    p = os.path.join(bdir, "frozen.md")
    if not os.path.exists(p):
        return {}, ""
    m, on = {}, ""
    for ln in open(p, encoding="utf-8"):
        d = re.match(r"- Frozen on: (.*)", ln)
        if d: on = d.group(1).strip()
        r = re.match(r"\| ([^|]+) \| ([A-Z]+-\d+) \|", ln)
        if r and r.group(1).strip() != "Source id": m[r.group(1).strip()] = r.group(2)
    return m, on


def pulled_pages(bdir):
    """Every pulled page: frontmatter plus the markdown body, and the raw storage body if the audit copy exists."""
    pages = []
    for p in sorted(glob.glob(os.path.join(bdir, "*.md"))):
        text = open(p, encoding="utf-8").read()
        if not text.startswith("---\npage-id:"):
            continue
        fm, body = text.split("\n---\n", 1)
        meta = dict(ln.split(":", 1) for ln in fm.split("\n")[1:] if ":" in ln)
        meta = {k.strip(): v.strip() for k, v in meta.items()}
        raw = os.path.join(bdir, ".raw", meta["page-id"] + ".json")
        pages.append({"id": meta["page-id"], "title": meta.get("page-title", ""), "version": meta.get("page-version", ""),
                      "parentId": meta.get("parent-page-id", ""), "url": meta.get("page-url", ""), "md": body,
                      "raw": json.load(open(raw, encoding="utf-8")) if os.path.exists(raw) else None, "file": os.path.basename(p)})
    return pages


def source_page(item):
    m = re.search(r"Baseline import from (.+?)(?:, table .*)?$", item.get("notes", ""), re.M)
    return m.group(1).strip() if m else ""


# ---------- the normalised table ----------

def columns(kind, scopes=None):
    cols = [("ID", "id"), ("Title", "title"), ("Status", "status")]
    cols += [(M.LABELS.get(k, k), k) for k in M.SHORT[kind] if k != "scope" or scopes]
    cols += [("Raised on", "raised-on"), ("Closed on", "closed-on"), ("Links", "links"), ("Source", "source"), ("Source id", "source-id")]
    return cols


def engagement_scopes(eng):
    """The engagement's declared scopes. This script has its own reader rather than importing the
    server, as it does for the rest of engagement.md."""
    p = os.path.join(eng, "engagement.md")
    if not os.path.exists(p):
        return []
    out, on = [], False
    for ln in open(p, encoding="utf-8"):
        if ln.startswith("## Scopes"):
            on = True; continue
        if ln.startswith("## "):
            on = False
        if on and ln.startswith("- "):
            out.append(ln[2:].strip())
    return out


def cell(v):
    if isinstance(v, list): v = "; ".join(v)
    return html.escape(str(v or "")).replace("\n", "<br />")


def table_html(kind, items, refs, scopes=None):
    cols = columns(kind, scopes)
    rows = ["<tr>" + "".join(f"<th><p><strong>{html.escape(lab)}</strong></p></th>" for lab, _ in cols) + "</tr>"]
    for it in items:
        vals = {k: it.get(k, "") for _, k in cols}
        vals["source-id"] = "; ".join(refs.get(it["id"], []))
        rows.append("<tr>" + "".join(f"<td><p>{cell(vals[k])}</p></td>" for _, k in cols) + "</tr>")
    return "<table data-layout=\"full-width\"><tbody>" + "".join(rows) + "</tbody></table>"


def note_html(text):
    return f"<p><em>{html.escape(text)}</em></p>"


# ---------- the page bodies ----------

TABLE_RE = re.compile(r"<table\b.*?</table>", re.S | re.I)


def header_is_register(cells):
    """A register table names its rows: an id or a row number, and a title of some kind."""
    cells = [c.strip().lower() for c in cells]
    return any(c in cells for c in ("id", "#", "ref", "key")) and any(c in cells for c in ("title", "requirement", "decision", "limitation", "risk", "action", "item", "description", "change proposal", "change request"))


def is_register_table(table_html_text):
    head = re.findall(r"<t[hd]\b[^>]*>(.*?)</t[hd]>", TABLE_RE.search(table_html_text).group(0).split("</tr>")[0], re.S | re.I)
    return header_is_register([re.sub(r"<[^>]+>", "", h) for h in head])


def replace_in_raw(body, new_table, note):
    """Swap the first register table in a storage body; the rest of the page is kept byte for byte."""
    for m in TABLE_RE.finditer(body):
        if is_register_table(m.group(0)):
            return body[:m.start()] + (note + "\n" if note else "") + new_table + body[m.end():], True
    return body, False


def md_to_storage(md, new_table, note):
    """Rebuild a page body from the pulled markdown when no raw copy exists: headings, paragraphs and tables,
    with the register table swapped. Formatting the pull flattened is not recovered, and the manifest says so."""
    out, cur, swapped = [], [], False
    def flush_table():
        nonlocal swapped
        if not cur: return
        rows = [[c.strip() for c in r.strip().strip("|").split("|")] for r in cur if not re.fullmatch(r"\|(\s*:?-{2,}:?\s*\|)+", r.strip())]
        head = [c.lower() for c in rows[0]] if rows else []
        if not swapped and header_is_register(head):
            out.append((note + "\n" if note else "") + new_table); swapped = True
        else:
            t = "<tr>" + "".join(f"<th><p><strong>{html.escape(c)}</strong></p></th>" for c in rows[0]) + "</tr>"
            t += "".join("<tr>" + "".join(f"<td><p>{html.escape(c).replace('&lt;br&gt;', '<br />')}</p></td>" for c in r) + "</tr>" for r in rows[1:])
            out.append(f"<table><tbody>{t}</tbody></table>")
        cur.clear()
    for ln in md.split("\n"):
        if ln.strip().startswith("|"): cur.append(ln); continue
        flush_table()
        s = ln.strip()
        if not s: continue
        if "derived from the rendered row number" in s: continue   # the pull's own note about a column it added
        m = re.match(r"(#+) (.*)", s)
        if m:
            if len(m.group(1)) == 1: continue   # the page title, which Confluence holds outside the body
            out.append(f"<h{min(len(m.group(1)), 6)}>{html.escape(m.group(2))}</h{min(len(m.group(1)), 6)}>")
        else: out.append(f"<p>{html.escape(s)}</p>")
    flush_table()
    return "\n".join(out), swapped


def guard(eng, cfg, pages):
    """Only the engagement the config names, pulled from the configured parent page, is ever pushed. A copy,
    a transposed test set or a stale folder fails here, before anything is built."""
    name = os.path.basename(os.path.abspath(eng))
    want = cfg.get("push", {}).get("engagement", "")
    if not want:
        sys.exit("confluence.json push.engagement is blank: name the one engagement that may be pushed, then run again")
    if name != want:
        sys.exit(f"refusing: this is engagement '{name}' but confluence.json allows pushing only '{want}'")
    m = re.search(r"/pages/(\d+)", cfg.get("parent_page_url", ""))
    parent = m.group(1) if m else ""
    wrong = [p["title"] for p in pages if p["parentId"] != parent]
    if not parent or wrong:
        sys.exit(f"refusing: these pages were not pulled from the configured parent page {parent or '(unset)'}: " + "; ".join(wrong or [p["title"] for p in pages]))
    if not any(e.get("action") == "pull" and e.get("engagement") == name for e in cfg.get("log", [])):
        sys.exit(f"refusing: confluence.json has no pull logged for '{name}'")


def build(eng, cfg, outdir):
    bdir = os.path.join(eng, cfg.get("local_copy", "baseline"))
    pages = pulled_pages(bdir)
    guard(eng, cfg, pages)
    items = load_items(eng); scopes = engagement_scopes(eng); idmap, frozen_on = id_map(bdir)
    verdicts = json.load(open(os.path.join(bdir, "verdicts.json"), encoding="utf-8")) if os.path.exists(os.path.join(bdir, "verdicts.json")) else {}
    alias_path = os.path.join(eng, 'aliases.json')
    aliases = json.load(open(alias_path, encoding='utf-8')) if os.path.exists(alias_path) else {}
    def survivors(id, seen=None):
        seen = set() if seen is None else seen
        if id in seen: raise ValueError('Alias cycle in source ID mapping.')
        if id not in aliases: return [id]
        return [target for next_id in aliases[id]['targets'] for target in survivors(next_id, seen | {id})]
    refs = {}
    for ref, nid in idmap.items():
        for target in survivors(nid):
            refs.setdefault(target, []).append(ref.split(" · ")[-1])
    mode = cfg.get("push", {}).get("mode", "replace-tables"); add_note = cfg.get("push", {}).get("add_note", True)
    by_title = {p["title"]: p for p in pages}
    imported = {}
    for c in load_candidates(bdir):
        if verdicts.get(c['id'], {}).get('frozenAs'):
            imported.setdefault(c['page'], set()).add(c['kind'])
    placed, unplaced = {p['id']: [] for p in pages if p['title'] in imported}, []
    for it in items:
        src = source_page(it)
        original = by_title.get(src)
        if original and guess_kind(original['title']) not in ('', None, it['kind']): original = None
        page = original or next((p for p in pages if guess_kind(p["title"]) == it["kind"]), None)
        if page: placed.setdefault(page["id"], []).append(it)
        else: unplaced.append(it["id"])
    merged = sum(1 for e in verdicts.values() if isinstance(e, dict) and e.get("verdict") == "Merge")
    rejected = sum(1 for e in verdicts.values() if isinstance(e, dict) and e.get("verdict") == "Reject")
    os.makedirs(outdir, exist_ok=True)
    manifest = {"engagement": os.path.basename(os.path.abspath(eng)), "built": today(), "as_of": today(), **({"frozen": frozen_on} if frozen_on else {}), "mode": mode, "pages": [], "unplaced": unplaced,
                "untouched": [p["title"] for p in pages if p["id"] not in placed]}
    for page in pages:
        its = placed.get(page["id"])
        if its is None: continue
        kinds = sorted(set(i["kind"] for i in its) or imported.get(page['title'], set()))
        note = (f"Register as at {today()} from this page; {len(its)} items in the engagement register"
                f"{', baselined ' + frozen_on if frozen_on else ''}{', ' + str(merged) + ' merged' if merged else ''}{', ' + str(rejected) + ' rejected across the baseline' if rejected else ''}. "
                "Source of truth is now the engagement register; ids are the register's, Source id is the id this page had.") if add_note else ""
        tables = "\n".join(table_html(k, [i for i in its if i["kind"] == k], refs, scopes) for k in kinds)
        entry = {"id": page["id"], "title": page["title"], "version": page["version"], "parentId": page["parentId"], "url": page["url"], "items": len(its), "kinds": kinds}
        if mode == "new-child":
            body = (note_html(note) + "\n" if note else "") + tables
            doc = {"id": None, "parentId": page["parentId"], "title": f"{page['title']} (baselined)", "version": None, "mode": mode, "body": body, "replaces": page["id"]}
            entry["title"] = doc["title"]
        else:
            if page["raw"]:
                body, ok = replace_in_raw(page["raw"].get("body", ""), tables, note_html(note) if note else "")
                entry["from"] = "raw storage body"
            else:
                body, ok = md_to_storage(page["md"], tables, note_html(note) if note else "")
                entry["from"] = "pulled markdown (no .raw audit copy; the pull's flattening of formatting is carried into the page)"
            if not ok:
                body = body + "\n" + (note_html(note) if note else "") + tables
                entry["warning"] = "no register table found on the page; the new table is appended at the end"
            doc = {"id": page["id"], "parentId": page["parentId"], "title": page["title"], "version": page["version"], "mode": mode, "body": body}
        f = os.path.join(outdir, f"{page['id']}.json")
        json.dump(doc, open(f, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        entry["file"] = os.path.basename(f); manifest["pages"].append(entry)
    rej = os.path.join(bdir, "rejections.md")
    if os.path.exists(rej) and rejected:
        body, _ = md_to_storage(open(rej, encoding="utf-8").read(), "", "")
        f = os.path.join(outdir, "rejections.json")
        json.dump({"id": None, "parentId": pages[0]["parentId"] if pages else "", "title": "Baseline rejections", "version": None, "mode": "new-child", "body": body}, open(f, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        manifest["rejections"] = os.path.basename(f)
    json.dump(manifest, open(os.path.join(outdir, "manifest.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    return manifest


if __name__ == "__main__":
    args = sys.argv[1:]
    cfgpath, out = "confluence.json", None
    if "--config" in args:
        i = args.index("--config"); cfgpath = args[i + 1]; del args[i:i + 2]
    if "--out" in args:
        i = args.index("--out"); out = args[i + 1]; del args[i:i + 2]
    if not args: sys.exit(__doc__)
    if "--unguarded" in args:
        args.remove("--unguarded"); guard.__code__ = (lambda eng, cfg, pages: None).__code__   # for a dry run on a copy; never for a real push
    eng = args[0]
    cfg = json.load(open(cfgpath, encoding="utf-8")) if os.path.exists(cfgpath) else {}
    m = build(eng, cfg, out or os.path.join(eng, "push"))
    for p in m["pages"]:
        print(f"{p['title']}: {p['items']} items ({', '.join(p['kinds'])}) -> {p['file']}" + (f"  WARNING {p['warning']}" if p.get("warning") else ""))
    if m["untouched"]: print("untouched:", "; ".join(m["untouched"]))
    if m["unplaced"]: print("unplaced items (no page of their type):", ", ".join(m["unplaced"]))
    if m.get("rejections"): print("rejections page:", m["rejections"])
