"""Baseline mode: turn generated register tables (Confluence HTML, Markdown, CSV) into candidates,
hold verdicts on them, and export the accepted set as a change set for the ingester.

Resilience rules: every table row is a candidate whatever it claims to be. Ids in the source are kept
as references, never used as ours. Statuses are noted, never trusted. Unknown columns go to Notes.
Nothing here writes an item file; state lives in <baseline>/verdicts.json.
"""
import os, re, csv, json, glob, hashlib, io
from html.parser import HTMLParser
import model as M

KIND_WORDS = {
    "REQ": ["requirement", "req", "need", "shall", "user story"],
    "DEC": ["decision", "dec", "adr"],
    "LIM": ["limitation", "lim", "constraint", "gap", "shortfall"],
    "RSK": ["risk", "rsk", "issue"],
    "OI":  ["open item", "action", "open question", "question", "todo", "oi"],
    "CR":  ["change request", "cr", "change"],
}
# column heuristics: model key -> words that a source header may use
COLS = {
    "title": ["title", "name", "summary", "requirement", "decision", "limitation", "risk", "action", "item", "statement"],
    "ref": ["id", "ref", "key", "#", "number", "identifier"],
    "kind": ["type", "kind", "category", "class"],
    "status": ["status", "state"],
    "owner": ["owner", "raised by", "assignee", "responsible", "accountable", "stakeholder", "requested by", "assigned to"],
    "approved-by": ["approved by", "decided by", "approver", "decision maker"],
    "moscow": ["moscow", "priority", "must/should"],
    "phase": ["phase", "release", "iteration", "target"],
    "implemented-by": ["implemented by", "implementer", "delivery"],
    "rationale": ["rationale", "reason", "justification", "why"],
    "impact": ["impact", "consequence", "effect"],
    "description": ["description", "detail", "details", "notes", "note", "comment", "comments"],
    "source": ["source", "evidence", "reference", "citation", "page", "origin", "transcript"],
    "confidence": ["confidence", "certainty", "grade"],
    "inferred": ["inferred", "derived", "basis"],
    "trigger": ["trigger"], "mitigation": ["mitigation", "treatment", "response"],
    "likelihood": ["likelihood", "probability"],
    "options": ["options", "alternatives"],
    "next action": ["next action", "next step", "action required"],
    "due": ["due", "date", "deadline", "review"],
}
REJECT_REASONS = ["duplicate", "inferred, no evidence", "not a requirement (present tense)", "legacy practice", "out of scope",
                  "vendor detail", "too vague to act on", "already covered by design", "other"]


class TableParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.tables = []; self.t = None; self.row = None; self.cell = None; self.title = ""; self.in_title = False; self.h = None; self.last_heading = ""
    def handle_starttag(self, tag, attrs):
        if tag == "table": self.t = []
        elif tag == "tr" and self.t is not None: self.row = []
        elif tag in ("td", "th") and self.row is not None: self.cell = []
        elif tag == "title": self.in_title = True
        elif tag in ("h1", "h2", "h3"): self.h = []
        elif tag == "br" and self.cell is not None: self.cell.append("\n")
    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cell is not None: self.row.append(" ".join("".join(self.cell).split(" ")).strip()); self.cell = None
        elif tag == "tr" and self.row is not None: self.t.append(self.row); self.row = None
        elif tag == "table" and self.t is not None: self.tables.append((self.last_heading, self.t)); self.t = None
        elif tag == "title": self.in_title = False
        elif tag in ("h1", "h2", "h3") and self.h is not None: self.last_heading = "".join(self.h).strip(); self.h = None
    def handle_data(self, d):
        if self.cell is not None: self.cell.append(d)
        if self.in_title: self.title += d
        if self.h is not None: self.h.append(d)


def md_tables(text):
    out, heading, cur = [], "", []
    for ln in text.split("\n") + [""]:
        if ln.startswith("#"): heading = ln.lstrip("# ").strip()
        if ln.strip().startswith("|"):
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c): continue
            cur.append(cells)
        elif cur:
            out.append((heading, cur)); cur = []
    return out


def read_source(path):
    """Return (page title, [(heading, rows)])."""
    ext = os.path.splitext(path)[1].lower()
    text = open(path, encoding="utf-8", errors="replace").read()
    if ext in (".html", ".htm", ".xml"):
        p = TableParser(); p.feed(text)
        return (p.title.strip() or os.path.basename(path), p.tables)
    if ext == ".csv":
        rows = list(csv.reader(io.StringIO(text)))
        return (os.path.basename(path), [("", rows)])
    m = re.search(r"^page-title:\s*(.+)$", text, re.M)
    return ((m.group(1).strip() if m else os.path.splitext(os.path.basename(path))[0]), md_tables(text))


def guess_kind(*texts):
    for t in texts:
        low = (t or "").lower()
        for k, words in KIND_WORDS.items():
            for w in words:
                if re.search(r"\b" + re.escape(w) + r"s?\b", low):
                    return k
    return None


def map_header(cells):
    mapping = []
    for c in cells:
        low = c.lower().strip()
        hit = None
        for key, words in COLS.items():
            if any(low == w or low.startswith(w + " ") or low.endswith(" " + w) or low == w + "s" for w in words):
                hit = key; break
        if hit is None:
            for key, words in COLS.items():
                if any(re.search(r"\b" + re.escape(w) + r"s?\b", low) for w in words):
                    hit = key; break
        mapping.append(hit or c)
    return mapping


def load_candidates(bdir):
    cands = []
    for path in sorted(glob.glob(os.path.join(bdir, "*"))):
        if os.path.basename(path).startswith(("verdicts", "rejections", "README")) or os.path.isdir(path):
            continue
        page, tables = read_source(path)
        for heading, rows in tables:
            if len(rows) < 2:
                continue
            header = map_header(rows[0]); page_kind = guess_kind(heading, page)
            for r in rows[1:]:
                if not any(c.strip() for c in r):
                    continue
                rec = {}; extra = []
                for i, c in enumerate(r):
                    key = header[i] if i < len(header) else f"col{i}"
                    if key in COLS: rec[key] = (rec.get(key, "") + "\n" + c).strip() if key in rec else c
                    elif c.strip(): extra.append(f"{key}: {c}")
                title = rec.get("title") or rec.get("description", "").split("\n")[0][:120]
                if not title:
                    continue
                kind = guess_kind(rec.get("kind", "")) or page_kind or guess_kind(rec.get("ref", "")) or "REQ"
                owner = rec.get("owner", "") or (rec.get("approved-by", "") if kind != "DEC" else "")
                cid = "c" + hashlib.sha1((page + heading + title + rec.get("ref", "")).encode()).hexdigest()[:8]
                inferred = bool(re.search(r"inferred|derived|implied|assumed", (rec.get("inferred", "") + " " + rec.get("confidence", "") + " " + rec.get("source", "")).lower()))
                conf = rec.get("confidence", "").strip()
                notes = [f"Baseline import from {page}" + (f", table {heading}" if heading else "")]
                if rec.get("ref"): notes.append(f"Source id: {rec['ref']}")
                if rec.get("status"): notes.append(f"Source status: {rec['status']}")
                notes += extra
                cands.append({
                    "id": cid, "page": page, "table": heading, "kind": kind, "title": title, "ref": rec.get("ref", ""),
                    "source_status": rec.get("status", ""), "owner": owner, "approved-by": rec.get("approved-by", "") if kind == "DEC" else "", "moscow": norm_moscow(rec.get("moscow", "")),
                    "phase": rec.get("phase", ""), "implemented-by": rec.get("implemented-by", ""),
                    "rationale": rec.get("rationale", ""), "impact": norm_lmh(rec.get("impact", "")) if kind == "RSK" else rec.get("impact", ""), "description": rec.get("description", ""),
                    "source": rec.get("source", "") or f"{page}{(' / ' + heading) if heading else ''}{(' / ' + rec['ref']) if rec.get('ref') else ''}",
                    "confidence": conf, "inferred": inferred, "trigger": rec.get("trigger", ""), "mitigation": rec.get("mitigation", ""),
                    "likelihood": norm_lmh(rec.get("likelihood", "")), "options": rec.get("options", ""), "next action": rec.get("next action", ""),
                    "due": rec.get("due", ""), "notes": "\n".join(notes),
                })
    return cands


def norm_moscow(v):
    low = (v or "").strip().lower()
    return {"must": "Must", "high": "Must", "critical": "Must", "should": "Should", "medium": "Should", "med": "Should", "could": "Could", "low": "Could", "nice to have": "Could", "won't": "Won't", "wont": "Won't", "out of scope": "Won't"}.get(low, v.strip().title() if low in ("must", "should", "could") else v.strip())


def norm_lmh(v):
    low = (v or "").strip().lower()
    return {"l": "L", "low": "L", "m": "M", "med": "M", "medium": "M", "h": "H", "high": "H"}.get(low, v.strip())


def tokens(s):
    stop = {"the", "and", "for", "with", "that", "this", "from", "must", "shall", "should", "will", "can", "are", "not", "system", "solution"}
    return set(re.sub(r"(ies|es|s|ed|ing)$", "", w) or w for w in re.findall(r"[a-z0-9]+", s.lower()) if len(w) > 2 and w not in stop)


def clusters(cands):
    """Suggested duplicate groups: same ref, or stemmed title token Jaccard >= 0.3. Suggestions only."""
    groups, seen = [], set()
    for i, a in enumerate(cands):
        if a["id"] in seen: continue
        g = [a["id"]]; ta = tokens(a["title"])
        for b in cands[i + 1:]:
            if b["id"] in seen: continue
            same_ref = a["ref"] and a["ref"] == b["ref"]
            tb = tokens(b["title"]); j = len(ta & tb) / len(ta | tb) if ta | tb else 0
            if same_ref or j >= 0.3:
                g.append(b["id"])
        if len(g) > 1:
            seen.update(g); groups.append(g)
    return groups


def load_verdicts(bdir):
    p = os.path.join(bdir, "verdicts.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}


def save_verdicts(bdir, v):
    json.dump(v, open(os.path.join(bdir, "verdicts.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)


def apply_verdict(bdir, ids, verdict=None, reason="", merged_into=None, fields=None, kind=None):
    v = load_verdicts(bdir)
    for cid in ids:
        e = v.setdefault(cid, {})
        if verdict is not None:
            e["verdict"] = verdict
            e["reason"] = reason if verdict == "Reject" else ""
            e["mergedInto"] = merged_into if verdict == "Merge" else None
        if kind: e["kind"] = kind
        if fields:
            e.setdefault("fields", {}).update({k: val for k, val in fields.items() if val is not None})
    save_verdicts(bdir, v)
    return v


def effective(c, v):
    """Candidate with verdict overrides applied."""
    e = v.get(c["id"], {}); out = dict(c)
    if e.get("kind"): out["kind"] = e["kind"]
    out.update(e.get("fields", {}))
    out["verdict"] = e.get("verdict", ""); out["reason"] = e.get("reason", ""); out["mergedInto"] = e.get("mergedInto")
    return out


def export_blocks(cands, v, today):
    """Return (blocks for a change set, rejection log lines). Merged candidates fold into their survivor."""
    eff = {c["id"]: effective(c, v) for c in cands}
    merged_into = {}
    for c in eff.values():
        if c["verdict"] == "Merge" and c["mergedInto"] in eff:
            merged_into.setdefault(c["mergedInto"], []).append(c)
    blocks, rejects = [], []
    for c in eff.values():
        if c["verdict"] == "Reject":
            rejects.append(f"| {c['page']} | {c['ref'] or ''} | {c['title']} | {c['reason']} |")
        if c["verdict"] != "Accept":
            continue
        k = c["kind"]
        fields = {"Title": c["title"], "Status": M.FIRST_STATE[k], "Raised on": today}
        for key in M.SHORT[k]:
            if c.get(key): fields[M.LABELS.get(key, key)] = c[key]
        long_map = {"rationale": "Rationale", "impact": "Impact", "trigger": "Trigger", "mitigation": "Mitigation", "options": "Options", "next action": "Next action"}
        for key, lab in long_map.items():
            if key in M.LONG[k] and c.get(key): fields[lab] = c[key]
        if k == "CR" and c.get("rationale"): fields["Reason"] = c["rationale"]
        if k == "OI" and not c.get("next action") and c.get("description"): fields["Next action"] = c["description"].split("\n")[0]
        src = [c["source"]] + [m["source"] for m in merged_into.get(c["id"], [])]
        fields["Source"] = "; ".join(dict.fromkeys(s for s in src if s))
        notes = [c["notes"]] + ([f"Merged in at baseline: " + "; ".join(m["title"] for m in merged_into[c["id"]])] if c["id"] in merged_into else [])
        if c.get("description") and k != "OI": notes.insert(0, c["description"])
        fields["Notes"] = " ⏎ ".join(n.replace("\n", " ⏎ ") for n in notes if n)
        blocks.append({"kind": k, "fields": fields, "gist": f"Baseline accept from {c['page']}" + (", inferred" if c["inferred"] else ""), "cid": c["id"]})
    return blocks, rejects
