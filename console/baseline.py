"""Baseline mode: turn generated register tables (Confluence HTML, Markdown, CSV) into candidates,
hold verdicts on them, and export the accepted set as a change set for the ingester.

Resilience rules: every table row is a candidate whatever it claims to be. Ids in the source are kept
as references, never used as ours. Statuses are noted, never trusted. Unknown columns go to Notes.
Nothing here writes an item file; state lives in <baseline>/verdicts.json.
"""
import os, re, csv, json, glob, hashlib, io
from html.parser import HTMLParser
import model as M

MONTHS = "January February March April May June July August September October November December".split()
# a source writes one of these where it means the cell is empty; carrying it through would invent a value
PLACEHOLDERS = {"—", "–", "-", "--", "n/a", "na", "tbd", "tba", "?", "none", "none set", "not set", "not yet set", "nil", "unknown"}

KIND_WORDS = {
    "REQ": ["requirement", "req", "need", "shall", "user story"],
    "DEC": ["decision", "dec", "adr"],
    "LIM": ["limitation", "lim", "constraint", "gap", "shortfall"],
    "RSK": ["risk", "rsk", "issue", "assumption", "dependency", "dependencies", "raid"],
    "OI":  ["open item", "action", "open question", "question", "todo", "oi"],
    "CR":  ["change request", "cr", "change"],
}
# column heuristics: model key -> words that a source header may use
COLS = {
    # order matters: the first key whose word matches wins, so a narrow header goes above a broad one
    "next action": ["next action", "next step", "action required"],
    "raised-on": ["raised on", "identified on", "created on", "logged on", "opened on"],
    "consulted": ["consulted"],
    "title": ["title", "name", "summary", "requirement", "decision", "limitation", "risk", "assumption", "dependency", "action", "item", "statement", "change request"],
    "vendor-ref": ["vendor ref", "vendor reference", "vendor id", "supplier ref", "external ref", "external id"],
    "ref": ["id", "ref", "key", "#", "number", "identifier"],
    "kind": ["type", "kind", "category", "class"],
    "status": ["status", "state"],
    "owner": ["owner", "assignee", "responsible", "accountable", "stakeholder", "assigned to", "from", "provider"],
    "raised-by": ["raised by", "requested by", "reported by"],
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
    "due": ["due", "date", "deadline", "review", "needed by"],
}
# headers a model word would otherwise swallow; these belong in Notes
NEVER_MAP = {"financial impact", "business impact", "customer impact"}

REJECT_REASONS = ["duplicate", "inferred, no evidence", "verified, no longer an assumption", "delivered, no longer a dependency", "not a requirement (present tense)", "legacy practice", "out of scope",
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


def ref_kind(ref):
    """A source id written in the model's own form (REQ-012, OI-3) names its type; a bare number says nothing."""
    m = re.match(r"\s*(REQ|DEC|LIM|RSK|OI|CR)-?\d", (ref or "").upper())
    return m.group(1) if m else None


def map_header(cells):
    mapping = []
    for c in cells:
        low = c.lower().strip()
        if low in NEVER_MAP:
            mapping.append(c); continue
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


def skip_table(heading, rows):
    """Prior-id appendices map an item's old id to its new one. They are not candidates."""
    if re.fullmatch(r"prior ids?", heading.strip(), re.I):
        return True
    return [c.lower().strip() for c in rows[0]] == ["prior", "now"]


def load_candidates(bdir):
    cands = []
    for path in sorted(glob.glob(os.path.join(bdir, "*"))):
        if os.path.basename(path).startswith(("verdicts", "rejections", "README")) or os.path.isdir(path):
            continue
        page, tables = read_source(path)
        for heading, rows in tables:
            if len(rows) < 2 or skip_table(heading, rows):
                continue
            header = map_header(rows[0]); page_kind = guess_kind(heading, page)
            for r in rows[1:]:
                r = [blank(c) for c in r]
                if not any(r):
                    continue
                rec = {}; extra = []
                for i, c in enumerate(r):
                    key = header[i] if i < len(header) else f"col{i}"
                    if key in COLS: rec[key] = (rec.get(key, "") + "\n" + c).strip() if key in rec else c
                    elif c.strip(): extra.append(f"{key}: {c}")
                title = rec.get("title") or rec.get("description", "").split("\n")[0][:120]
                if not title:
                    continue
                kind = guess_kind(rec.get("kind", "")) or ref_kind(rec.get("ref", "")) or page_kind or guess_kind(rec.get("ref", "")) or "REQ"
                owner = rec.get("owner", "") or rec.get("raised-by", "") or (rec.get("approved-by", "") if kind != "DEC" else "")
                rkind = ""
                if kind == "RSK":
                    src = (rec.get("kind", "") + " " + heading + " " + page).lower()
                    rkind = "Assumption" if "assumption" in src else "Dependency" if "dependenc" in src else "Risk"
                cid = "c" + hashlib.sha1((page + heading + title + rec.get("ref", "")).encode()).hexdigest()[:8]
                inferred = bool(re.search(r"inferred|derived|implied|assumed", (rec.get("inferred", "") + " " + rec.get("confidence", "") + " " + rec.get("source", "")).lower()))
                conf = rec.get("confidence", "").strip()
                notes = [f"Baseline import from {page}" + (f", table {heading}" if heading else "")]
                if rec.get("ref"): notes.append(f"Source id: {rec['ref']}")
                if rec.get("status"): notes.append(f"Source status: {rec['status']}")
                if rec.get("raised-by") and rec.get("owner"): notes.append(f"Raised by: {rec['raised-by']}")
                vref = rec.get("vendor-ref", "")
                if vref and kind != "CR":  # model 4.1: Vendor ref is a change request field; elsewhere it is a note
                    notes.append(f"Vendor ref: {vref}"); vref = ""
                notes += extra
                cands.append({
                    "id": cid, "page": page, "table": heading, "kind": kind, "title": title, "ref": rec.get("ref", ""),
                    "source_status": rec.get("status", ""), "owner": owner, "approved-by": rec.get("approved-by", "") if kind == "DEC" else "", "moscow": norm_moscow(rec.get("moscow", "")),
                    "phase": rec.get("phase", ""), "implemented-by": rec.get("implemented-by", ""), "vendor-ref": vref,
                    "raised-on": norm_date(rec.get("raised-on", "")), "consulted": rec.get("consulted", ""),
                    "rationale": rec.get("rationale", ""), "impact": norm_lmh(rec.get("impact", "")) if kind == "RSK" else rec.get("impact", ""), "description": rec.get("description", ""),
                    "source": rec.get("source", "") or f"{page}{(' / ' + heading) if heading else ''}{(' / ' + rec['ref']) if rec.get('ref') else ''}",
                    "confidence": conf, "inferred": inferred, "trigger": rec.get("trigger", ""), "mitigation": rec.get("mitigation", ""),
                    "likelihood": norm_lmh(rec.get("likelihood", "")), "risk-kind": rkind, "options": rec.get("options", ""), "next action": rec.get("next action", ""),
                    "due": rec.get("due", ""), "notes": "\n".join(notes),
                })
    return cands


def norm_moscow(v):
    low = (v or "").strip().lower()
    return {"must": "Must", "high": "Must", "critical": "Must", "should": "Should", "medium": "Should", "med": "Should", "could": "Could", "low": "Could", "nice to have": "Could", "won't": "Won't", "wont": "Won't", "out of scope": "Won't"}.get(low, v.strip().title() if low in ("must", "should", "could") else v.strip())


def blank(v):
    """A placeholder standing for an empty cell is an empty cell."""
    v = re.sub(r"<br\s*/?>", "\n", v or "", flags=re.I).strip()
    return "" if v.lower() in PLACEHOLDERS else v


def norm_date(v):
    """A source date in ISO becomes the register's own form. Anything else is left as it was written."""
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", (v or "").strip())
    if not m: return (v or "").strip()
    y, mo, d = (int(x) for x in m.groups())
    return f"{d} {MONTHS[mo - 1]} {y}" if 1 <= mo <= 12 else v.strip()


def norm_lmh(v):
    low = (v or "").strip().lower()
    return {"l": "L", "low": "L", "m": "M", "med": "M", "medium": "M", "h": "H", "high": "H"}.get(low, v.strip())


def tokens(s):
    stop = {"the", "and", "for", "with", "that", "this", "from", "must", "shall", "should", "will", "can", "are", "not", "system", "solution",
            "support", "supported", "change", "changes", "modify", "new", "via", "when", "any", "all", "only", "into", "per", "use", "used", "need", "needed"}
    return set(re.sub(r"(ies|es|s|ed|ing)$", "", w) or w for w in re.findall(r"[a-z0-9]+", s.lower()) if len(w) > 2 and w not in stop)


def related_kinds():
    """Type pairs the model relates (section 5, mirrored in model.py). A CR delivers a REQ, a LIM constrains
    one, a DEC addresses one: those read alike by design and are never each other's duplicate."""
    pairs = set()
    for src, words in M.LINK_WORDS.items():
        for targets in words.values():
            for t in targets.split("|"):
                if t == "ANY":
                    pairs |= {frozenset((src, k)) for k in M.LINK_WORDS if k != src}
                elif t in M.LINK_WORDS and t != src:
                    pairs.add(frozenset((src, t)))
    return pairs


RELATED = related_kinds()


DISMISSED = "_not-duplicates"


def cluster_key(ids):
    """Stable name for a suggested group. Candidate ids are deterministic, so the key survives a reload."""
    return hashlib.sha1("|".join(sorted(ids)).encode()).hexdigest()[:10]


def dismiss_cluster(bdir, ids, undo=False):
    v = load_verdicts(bdir)
    keys = set(v.get(DISMISSED, []))
    keys.discard(cluster_key(ids)) if undo else keys.add(cluster_key(ids))
    v[DISMISSED] = sorted(keys)
    save_verdicts(bdir, v)
    return v


def clusters(cands, dismissed=()):
    """Suggested duplicate groups: same ref, or stemmed title token Jaccard >= 0.3. Suggestions only.
    Two types the model relates are never grouped; merging one into the other would lose the relationship.
    A group the reviewer has called not duplicates stays out until its membership changes."""
    groups, seen = [], set()
    for i, a in enumerate(cands):
        if a["id"] in seen: continue
        g = [a["id"]]; ta = tokens(a["title"])
        for b in cands[i + 1:]:
            if b["id"] in seen: continue
            if frozenset((a["kind"], b["kind"])) in RELATED: continue
            same_ref = a["ref"] and a["ref"] == b["ref"]
            tb = tokens(b["title"]); j = len(ta & tb) / len(ta | tb) if ta | tb else 0
            if same_ref or (j >= 0.3 and len(ta & tb) >= 2):
                g.append(b["id"])
        if len(g) > 1:
            seen.update(g)
            if cluster_key(g) not in dismissed: groups.append(g)
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
    out["verdict"] = e.get("verdict", ""); out["reason"] = e.get("reason", ""); out["mergedInto"] = e.get("mergedInto"); out["exported"] = e.get("exported", "")
    return out


FOLD_SKIP = {"title", "status", "source", "notes", "raised-on"}


def fold_merged(surv, merged, kind):
    """A merge keeps the survivor's own values and takes what only the merged rows carry, so nothing is
    lost to the choice of survivor. Where both hold a value and they differ, the survivor wins and the
    other is written into Notes rather than dropped. Returns (filled survivor, notes about what was not taken)."""
    if not merged:
        return surv, []
    out, kept_back = dict(surv), []
    keys = [f for f in M.SHORT[kind] + M.LONG[kind] if f not in FOLD_SKIP] + ["description", "impact", "rationale"]
    for key in dict.fromkeys(keys):
        mine = str(out.get(key, "") or "").strip()
        for m in merged:
            theirs = str(m.get(key, "") or "").strip()
            if not theirs or theirs == mine:
                continue
            if not mine:
                out[key] = theirs; mine = theirs
            else:
                kept_back.append(f"{M.LABELS.get(key, key)} on the merged {m['vendor-ref'] or m['ref'] or m['page']}: {theirs}")
    return out, kept_back


def export_blocks(cands, v, today):
    """Return (blocks for a change set, rejection log lines). Merged candidates fold into their survivor."""
    eff = {c["id"]: effective(c, v) for c in cands}
    merged_into = {}
    for c in eff.values():
        if c["verdict"] == "Merge" and c["mergedInto"] in eff:
            merged_into.setdefault(c["mergedInto"], []).append(c)
    blocks, rejects = [], []
    for c in eff.values():
        if v.get(c["id"], {}).get("exported"):
            continue
        if c["verdict"] == "Reject":
            rejects.append(f"| {c['page']} | {c['ref'] or ''} | {c['title']} | {c['reason']} |")
        if c["verdict"] != "Accept":
            continue
        k = c["kind"]
        c, kept_back = fold_merged(c, merged_into.get(c["id"], []), k)
        fields = {"Title": c["title"], "Status": M.FIRST_STATE[k], "Raised on": c.get("raised-on") or today}
        for key in M.SHORT[k]:
            if key == "risk-kind":
                fields["Kind"] = c.get("risk-kind") or "Risk"
                continue
            if c.get(key): fields[M.LABELS.get(key, key)] = c[key]
        long_map = {"rationale": "Rationale", "impact": "Impact", "trigger": "Trigger", "mitigation": "Mitigation", "options": "Options", "next action": "Next action"}
        for key, lab in long_map.items():
            if key in M.LONG[k] and c.get(key): fields[lab] = c[key]
        if k == "CR" and c.get("rationale"): fields["Reason"] = c["rationale"]
        if k == "OI" and not c.get("next action") and c.get("description"): fields["Next action"] = c["description"].split("\n")[0]
        if k == "DEC" and c.get("approved-by"): fields["Approved by"] = c["approved-by"]
        src = [c["source"]] + [m["source"] for m in merged_into.get(c["id"], [])]
        fields["Source"] = "; ".join(dict.fromkeys(s for s in src if s))
        notes = [c["notes"]] + ([f"Merged in at baseline: " + "; ".join(m["title"] for m in merged_into[c["id"]])] if c["id"] in merged_into else []) + kept_back
        if c.get("description") and k != "OI": notes.insert(0, c["description"])
        fields["Notes"] = " ⏎ ".join(n.replace("\n", " ⏎ ") for n in notes if n)
        blocks.append({"kind": k, "fields": fields, "gist": f"Baseline accept from {c['page']}" + (", inferred" if c["inferred"] else ""), "cid": c["id"]})
    return blocks, rejects


def mark_exported(bdir, cids, cs_id):
    v = load_verdicts(bdir)
    for cid in cids:
        v.setdefault(cid, {})["exported"] = cs_id
    save_verdicts(bdir, v)
