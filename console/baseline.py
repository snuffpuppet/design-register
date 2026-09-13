"""Baseline mode: turn generated register tables (Confluence HTML, Markdown, CSV) into candidates,
hold verdicts on them, and export the accepted set as a change set for the ingester.

Resilience rules: every table row is a candidate whatever it claims to be. Ids in the source are kept
as references, never used as ours. Statuses are noted, never trusted. Unknown columns go to Notes.
Nothing here writes an item file; state lives in <baseline>/verdicts.json.
"""
import os, re, csv, json, glob, hashlib, io
from html.parser import HTMLParser
import model as M
import integrity as I
import items as I_

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
    "scope": ["scope", "domain", "service", "area"],
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
    "chosen-option": ["chosen option", "chosen", "disposition"],
    "options": ["options", "alternatives"],
    "due": ["due", "date", "deadline", "review", "needed by"],
}
# headers a model word would otherwise swallow; these belong in Notes
# "Disposition record" names the decision or change request that dispositioned a limitation, not a chosen
# option; LINK_NOTE_WORDS already reads it as a link column, so it stays out of the mapping
NEVER_MAP = {"financial impact", "business impact", "customer impact", "disposition record"}

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


SKIP_FILE = "skip-pages.txt"


def load_skips(bdir):
    """Pages named as views of the registers rather than registers. One title per line; # starts a comment.
    A named list is a person saying so, once; the console never guesses which pages are views."""
    p = os.path.join(bdir, SKIP_FILE)
    if not os.path.exists(p): return []
    return [ln.strip() for ln in open(p, encoding="utf-8") if ln.strip() and not ln.startswith("#")]


def set_skip(bdir, page, undo=False):
    skips = [x for x in load_skips(bdir) if x != page]
    if not undo: skips.append(page)
    with open(os.path.join(bdir, SKIP_FILE), "w", encoding="utf-8") as f:
        f.write("# Pages under this folder that restate register rows (summaries, outstanding views, conventions).\n"
                "# They are still pulled and kept, but produce no baseline candidates. One page title per line.\n" + "\n".join(skips) + ("\n" if skips else ""))
    return skips


def page_titles(bdir):
    """Every pulled page title, skipped or not."""
    out = []
    for path in sorted(glob.glob(os.path.join(bdir, "*"))):
        if os.path.basename(path).startswith(("verdicts", "rejections", "frozen", "README", "skip-pages")) or os.path.isdir(path):
            continue
        out.append(read_source(path)[0])
    return out


def load_candidates(bdir):
    cands = []
    skips = set(load_skips(bdir))
    for path in sorted(glob.glob(os.path.join(bdir, "*"))):
        if os.path.basename(path).startswith(("verdicts", "rejections", "frozen", "README", "skip-pages")) or os.path.isdir(path):
            continue
        page, tables = read_source(path)
        if page in skips:
            continue
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
                    "likelihood": norm_lmh(rec.get("likelihood", "")), "risk-kind": rkind, "chosen-option": rec.get("chosen-option", ""), "options": rec.get("options", ""), "next action": rec.get("next action", ""),
                    "due": rec.get("due", ""), "notes": "\n".join(notes),
                })
    return cands + load_implied(bdir)


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


tokens = I.tokens


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


def apply_verdict(bdir, ids, verdict=None, reason="", merged_into=None, fields=None, kind=None, links=None):
    v = load_verdicts(bdir)
    for cid in ids:
        e = v.setdefault(cid, {})
        if links is not None:
            e["links"] = list(links)
        if verdict is not None:
            e["verdict"] = verdict
            e["reason"] = reason if verdict == "Reject" else ""
            e["mergedInto"] = merged_into if verdict == "Merge" else None
        if kind: e["kind"] = kind
        if fields:
            e.setdefault("fields", {}).update({k: val for k, val in fields.items() if val is not None and k in EDITABLE})
    save_verdicts(bdir, v)
    return v


def effective(c, v):
    """Candidate with verdict overrides applied."""
    e = v.get(c["id"], {}); out = dict(c)
    if e.get("kind"): out["kind"] = e["kind"]
    out.update(e.get("fields", {}))
    out["verdict"] = e.get("verdict", ""); out["reason"] = e.get("reason", ""); out["mergedInto"] = e.get("mergedInto"); out["exported"] = e.get("exported", ""); out["frozenAs"] = e.get("frozenAs", "")
    # a trigger's links are held on its verdict; an implied candidate carries its own as well
    out["links"] = list(e.get("links", [])) + (list(c.get("links", [])) if c.get("implied") else [])
    out["implied"] = bool(c.get("implied"))
    return out


# what the reviewer may change on a candidate before the freeze
EDITABLE = {"title", "status", "owner", "moscow", "phase", "implemented-by", "approved-by", "consulted", "vendor-ref", "likelihood", "impact", "due", "risk-kind", "chosen-option",
            "description", "rationale", "trigger", "mitigation", "options", "next action", "notes", "raised-on", "scope"}

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


IMPLIED_KEY = "_implied"
SUPPORTS_KEY = "_supports"
# a note that came from a link column ("Links: delivers REQ-030", "Delivers: REQ-030") reads as links
LINK_NOTE_WORDS = {"Links": "", "Delivers": "delivers", "Resolves into": "resolves into", "Disposition record": "dispositioned by",
                   "Blocked by": "blocked by", "Supersedes": "supersedes", "Addresses": "addresses"}


def load_implied(bdir):
    """Candidates the reviewer accepted off the Missing supports tab. They live with the verdicts, never
    in the source pages, and join the candidate list so the rest of the baseline treats them alike."""
    return list(load_verdicts(bdir).get(IMPLIED_KEY, []))


def status_of(c):
    """The status this candidate would be frozen with: an edited status, else a source status that is one
    of the model's own states for its type, else the type's first state."""
    k = c["kind"]
    return c.get("status") or next((st for st in M.STATES[k] if st.lower() == (c.get("source_status") or "").lower()), M.FIRST_STATE[k])


def refmap_of(cands):
    """Source ref -> candidate id, the way the freeze maps refs to new ids: a full model-form id is unique
    across the source, a bare number only within its page."""
    m = {}
    for c in cands:
        if c["ref"]:
            m[c["ref"] if LINK_RE.fullmatch(c["ref"]) else f"{c['page']} \u00b7 {c['ref']}"] = c["id"]
    return m


def source_links(c, refmap):
    """The links a candidate's Notes carry, with source ids read as candidate ids. A source id that names
    no candidate is dropped: the engine never links to something the baseline does not hold."""
    out = []
    for n in (c.get("notes") or "").split("\n"):
        m = re.match(r"(" + "|".join(LINK_NOTE_WORDS) + r"): (.+)", n)
        if not (m and LINK_RE.search(m.group(2))):
            continue
        word = LINK_NOTE_WORDS[m.group(1)]
        for part in re.split(r"[;,]\s*", m.group(2)):
            part = part.strip()
            idm = LINK_RE.search(part)
            if not idm:
                continue
            ref = f"{idm.group(1)}-{idm.group(2)}"
            cid = refmap.get(ref) or refmap.get(f"{idm.group(1)}{idm.group(2)}") or refmap.get(f"{c['page']} \u00b7 {ref}")
            if not cid:
                continue
            lead = part[:idm.start()].strip().lower()
            out.append(((lead or word) + " " + cid).strip() if (lead or word) else cid)
    return out


def as_items(cands, v):
    """The accepted candidates and the implied ones as item dicts for integrity.check. Ids are candidate
    ids, so a suggestion points at a row the reviewer can still see on the baseline tabs."""
    refmap = refmap_of(cands)
    eff = {c["id"]: effective(c, v) for c in cands}
    merged_into = {}
    for c in eff.values():
        if c["verdict"] == "Merge" and c["mergedInto"] in eff:
            merged_into.setdefault(c["mergedInto"], []).append(c)
    items = []
    for c in eff.values():
        if c["verdict"] != "Accept":
            continue
        k = c["kind"]
        merged = merged_into.get(c["id"], [])
        it, _ = fold_merged(c, merged, k)
        it = dict(it)
        it["status"] = status_of(it)
        it["links"] = list(dict.fromkeys(list(c.get("links") or []) + source_links(c, refmap)
                                         + sum((source_links(m, refmap) for m in merged), [])))
        if k == "CR" and not it.get("reason"):
            it["reason"] = it.get("rationale", "")
        items.append(it)
    return items


def suggestions(cands, v):
    """integrity.check over the accepted set, with dismissed rows dropped and each offer told which
    candidate triggered it. Recommend says what the row reads like: a limitation that already carries a
    rationale or a chosen option is a record to reconstruct, one that carries neither is a claim to reassess."""
    res = I.check(as_items(cands, v))
    done = v.get(SUPPORTS_KEY, {})
    byc = {c["id"]: c for c in cands}
    kept = []
    for s in res["suggestions"]:
        if done.get(s["key"], {}).get("verdict") == "Dismiss":
            continue
        trig = byc.get(s["id"])
        e = effective(trig, v) if trig else {}
        s["triggerTitle"] = e.get("title", "")
        s["triggerPage"] = e.get("page", "")
        if s["rule"] in ("S5", "S6"):
            s["recommend"] = "Reconstruct" if (e.get("rationale") or e.get("chosen-option")) else "Reassess"
        kept.append(s)
    res["suggestions"] = kept
    res["dismissed"] = sum(1 for e in done.values() if e.get("verdict") == "Dismiss")
    return res


def support_verdict(bdir, key, verdict, reason="", fields=None, sugg=None, target=None):
    """A reviewer's answer to one missing support. Accept writes the offered item as an implied candidate
    and links it both ways; Link points the trigger at an accepted candidate that already exists, with the reverse
    where the model names one, and creates nothing; Reassess drops the trigger back to Under assessment;
    Dismiss hides the row."""
    v = load_verdicts(bdir)
    fields = fields or {}
    if verdict == "Link":
        if not sugg:
            raise ValueError("Link needs the suggestion.")
        if not target or target == sugg["id"]:
            raise ValueError("Pick the record to link.")
        t = next((c for c in load_candidates(bdir) if c["id"] == target), None)
        te = effective(t, v) if t else None
        if not te or te["verdict"] != "Accept":
            raise ValueError("Link existing only points at an accepted candidate.")
        if te["kind"] != sugg["kind"]:
            raise ValueError(f"That candidate is a {M.NAMES[te['kind']]}; this offer needs a {M.NAMES[sugg['kind']]}.")
        trig = v.setdefault(sugg["id"], {})
        trig["links"] = list(dict.fromkeys(trig.get("links", []) + [sugg["link"] + target]))
        if sugg["reverse"]:
            tv = v.setdefault(target, {})
            tv["links"] = list(dict.fromkeys(tv.get("links", []) + [sugg["reverse"]]))
        v.setdefault(SUPPORTS_KEY, {})[key] = {"verdict": "Link", "target": target}
    elif verdict == "Dismiss":
        v.setdefault(SUPPORTS_KEY, {})[key] = {"verdict": "Dismiss", "reason": reason}
    elif verdict == "Reassess":
        if not sugg:
            raise ValueError("Reassess needs the suggestion.")
        e = v.setdefault(sugg["id"], {}); e.setdefault("fields", {})["status"] = "Under assessment"
        e["links"] = [l for l in e.get("links", []) if not l.lower().startswith("dispositioned by")]
        v.setdefault(SUPPORTS_KEY, {})[key] = {"verdict": "Reassess"}
    elif verdict == "Accept":
        if not sugg:
            raise ValueError("Accept needs the suggestion.")
        f = dict(sugg["fields"]); f.update({k: x for k, x in fields.items() if x is not None})
        if sugg["needsOwner"] and not str(f.get("owner", "")).strip():
            raise ValueError("Set the owner before accepting this one; the engine does not guess stakeholders.")
        iid = "i" + key[1:]
        cand = {"id": iid, "page": "Implied at baseline", "table": "", "kind": sugg["kind"], "title": f.get("title", ""), "ref": "",
                "scope": f.get("scope", ""),
                "source_status": sugg["status"], "owner": f.get("owner", ""), "approved-by": "", "moscow": f.get("moscow", ""), "phase": f.get("phase", ""),
                "implemented-by": f.get("implemented-by", ""), "vendor-ref": "", "raised-on": "", "consulted": f.get("consulted", ""),
                "rationale": f.get("rationale", "") if sugg["kind"] != "CR" else f.get("reason", ""), "impact": f.get("impact", ""), "description": "",
                "source": f.get("source", ""), "confidence": "", "inferred": False, "trigger": "", "mitigation": "", "likelihood": "",
                "risk-kind": "Risk" if sugg["kind"] == "RSK" else "", "chosen-option": f.get("chosen-option", ""), "options": "",
                "next action": f.get("next action", ""), "due": f.get("due", ""),
                "notes": f"Implied at baseline by {sugg['id']} under {sugg['rule']}",
                "links": [sugg["reverse"]] if sugg["reverse"] else [], "implied": True}
        v[IMPLIED_KEY] = [c for c in v.get(IMPLIED_KEY, []) if c["id"] != iid] + [cand]
        v.setdefault(iid, {})["verdict"] = "Accept"
        trig = v.setdefault(sugg["id"], {})
        trig["links"] = list(dict.fromkeys(trig.get("links", []) + [sugg["link"] + iid]))
        v.setdefault(SUPPORTS_KEY, {})[key] = {"verdict": "Accept", "created": iid}
    else:
        raise ValueError("Unknown support verdict.")
    save_verdicts(bdir, v)
    return v


def assemble(cands, v, today):
    """The accepted set as it would enter the registers: one record per accepted candidate with its merged
    rows folded in. Returns (records, rejection rows). Each record is {"kind", "fields", "gist", "cid", "refs"}
    where refs are the source ids it carries (its own and those folded into it)."""
    eff = {c["id"]: effective(c, v) for c in cands}
    merged_into = {}
    for c in eff.values():
        if c["verdict"] == "Merge" and c["mergedInto"] in eff:
            merged_into.setdefault(c["mergedInto"], []).append(c)
    records, rejects = [], []
    for c in eff.values():
        if c["verdict"] == "Reject":
            rejects.append(f"| {c['page']} | {c['ref'] or ''} | {c['title']} | {c['reason']} |")
        if c["verdict"] != "Accept":
            continue
        k = c["kind"]
        c, kept_back = fold_merged(c, merged_into.get(c["id"], []), k)
        # a source status that is one of the model's own states for this type is kept; anything else starts the item at its first state
        status = status_of(c)
        fields = {"Title": c["title"], "Status": status, "Raised on": c.get("raised-on") or today}
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
        refs = [r for r in [c["ref"]] + [m["ref"] for m in merged_into.get(c["id"], [])] if r]
        records.append({"kind": k, "fields": fields, "gist": f"Baseline accept from {c['page']}" + (", inferred" if c["inferred"] else ""), "cid": c["id"],
                        "refs": refs, "page": c["page"], "merged_cids": [m["id"] for m in merged_into.get(c["id"], [])],
                        "links": list(dict.fromkeys(c.get("links") or [])), "implied": bool(c.get("implied")),
                        "scope": c.get("scope", "")})
    return records, rejects


def export_blocks(cands, v, today):
    """Return (blocks for a change set, rejection log lines), skipping what an earlier export already carried."""
    records, rejects = assemble(cands, v, today)
    return [r for r in records if not v.get(r["cid"], {}).get("exported")], rejects


FROZEN = "frozen.md"
LINK_RE = re.compile(r"\b(REQ|DEC|LIM|RSK|OI|CR)-?(\d+)\b")
# a candidate id, or an implied candidate id, as integrity.LINK_ID reads them
CAND_RE = re.compile(r"\b[ci][0-9a-f]{8,10}\b")


def frozen(bdir):
    """The freeze record if the baseline has been frozen: {"on", "by", "counts", "map"}."""
    p = os.path.join(bdir, FROZEN)
    if not os.path.exists(p):
        return None
    out = {"on": "", "by": "", "counts": {}, "map": {}}
    for ln in open(p, encoding="utf-8"):
        m = re.match(r"- Frozen on: (.*)", ln)
        if m: out["on"] = m.group(1).strip()
        m = re.match(r"- Frozen by: (.*)", ln)
        if m: out["by"] = m.group(1).strip()
        m = re.match(r"- Items by type: (.*)", ln)
        if m:
            out["counts"] = {k: int(n) for k, n in re.findall(r"([A-Z]+)=(\d+)", m.group(1))}
        m = re.match(r"\| ([^|]+) \| ([A-Z]+-\d+) \|", ln)
        if m and m.group(1).strip() not in ("Source id", "---"): out["map"][m.group(1).strip()] = m.group(2)
    if not out["counts"]:
        # a baseline frozen before the counts line was written: the id map named every item then
        for nid in out["map"].values():
            out["counts"][nid.split("-")[0]] = out["counts"].get(nid.split("-")[0], 0) + 1
    return out


def item_text(id, fields, links):
    """One item file in the model's section 7 layout, rendered by items.render_item so the freeze and the
    console write the same file. Fields arrive by label; Updated starts equal to Raised on."""
    kind = id.split("-")[0]
    keys = {lab: key for key, lab in M.LABELS.items()}
    keys.update({"Title": "title", "Status": "status", "Kind": "risk-kind"})
    it = {"id": id, "kind": kind, "links": list(links), "history": []}
    for lab, val in fields.items():
        key = keys.get(lab, lab.lower())
        it[key] = (val or "").replace(" ⏎ ", "\n") if isinstance(val, str) else val
    it["updated"] = it.get("raised-on", "")
    return I_.render_item(it)


IMPLIED_BY = re.compile(r"by (\S+) under (S\d+)")


def implied_section(records):
    """What the freeze wrote that no source page held: one row per implied item, the rule that offered it
    and the item that triggered it. The write loop has already turned the candidate id in these fields
    into an item id, so the id is read as it stands. Nothing is written when the baseline implied nothing."""
    rows = []
    for r in records:
        if not r.get("implied"):
            continue
        m = IMPLIED_BY.search(r["fields"].get("Notes", "") + " " + r["fields"].get("Source", ""))
        rows.append(f"| {r['id']} | {m.group(2) if m else ''} | {m.group(1) if m else ''} |")
    if not rows:
        return ""
    return "\n\n## Implied at baseline\n\nItems the registers needed that no source page held.\n\n| Item | Rule | Implied by |\n|---|---|---|\n" + "\n".join(rows) + "\n"


def freeze(eng, bdir, cands, v, today, who, scopes=None):
    """Write the accepted set as item files, the first content of the registers. Refuses if any item file
    exists, so a live register is never overwritten. Source ids become the model's ids in order of acceptance,
    a Links note whose source ids all map becomes real links, and the id map is written to baseline/frozen.md."""
    if frozen(bdir):
        raise ValueError("The baseline is already frozen.")
    for d in M.DIRS.values():
        if glob.glob(os.path.join(eng, d, "*.md")):
            raise ValueError(f"The {d} register already has items; freeze only runs into empty registers.")
    pending = [x for x in suggestions(cands, v)["suggestions"] if x["level"] == "fail"]
    if pending:
        raise ValueError(f"{len(pending)} missing support(s) still undecided on the Missing supports tab; accept or dismiss them before the freeze.")
    records, rejects = assemble(cands, v, today)
    if not records:
        raise ValueError("Nothing accepted yet.")
    if scopes:
        bad = [r for r in records if str(r.get("scope", "")).strip() not in scopes]
        if bad:
            vals = sorted({str(r.get("scope", "")).strip() or "(blank)" for r in bad})
            raise ValueError(f"{len(bad)} accepted item(s) have a Scope that is not one of the engagement's: "
                             + ", ".join(vals) + ". Fix them on the Candidates tab before the freeze.")
    counter, idmap, out, cids = {}, {}, [], set()
    for r in records:
        counter[r["kind"]] = counter.get(r["kind"], 0) + 1
        nid = f"{r['kind']}-{counter[r['kind']]:04d}"
        r["id"] = nid
        idmap[r["cid"]] = nid; cids.add(r["cid"])
        for mc in r["merged_cids"]:
            idmap[mc] = nid; cids.add(mc)
        for ref in r["refs"]:
            # a bare number is only unique within its page; an id in the model's form is unique across the source
            idmap[ref if LINK_RE.fullmatch(ref) else f"{r['page']} · {ref}"] = nid
    def remap(txt):
        # source ids first, then candidate ids: both name items that now carry one of the model's ids
        return CAND_RE.sub(lambda m: idmap.get(m.group(0), m.group(0)),
                           LINK_RE.sub(lambda m: idmap.get(f"{m.group(1)}-{m.group(2)}", idmap.get(f"{m.group(1)}{m.group(2)}", m.group(0))), txt))
    for r in records:
        # links held on the verdict, and an implied candidate's own, are already ours. A link whose target
        # was not accepted still reads as a candidate id after the remap, and is dropped rather than written dangling
        links = [l for l in (remap(x) for x in r.get("links", [])) if not CAND_RE.search(l)]
        notes = []
        for n in r["fields"].get("Notes", "").split(" ⏎ "):
            m = re.match(r"(" + "|".join(LINK_NOTE_WORDS) + r"): (.+)", n)
            if not (m and LINK_RE.search(m.group(2))):
                notes.append(n); continue
            for part in re.split(r"[;,]\s*", m.group(2)):
                part = part.strip()
                if not LINK_RE.search(part): continue
                word = LINK_NOTE_WORDS[m.group(1)]
                links.append((word + " " + remap(part)).strip() if word and not re.match(r"[a-z]", part) else remap(part))
            notes.append(n + " (as written in the source)")
        r["fields"]["Notes"] = " ⏎ ".join(notes)
        links = list(dict.fromkeys(links))
        if r.get("implied"):
            # an implied item's fields are the engine's own words about the candidate that triggered it,
            # never source text. Offer templates put the trigger's id in Title, Rationale, Reason, Next
            # action and Source alike, so every one of them reads the candidate id as the item's id
            r["fields"] = {lab: (remap(val) if isinstance(val, str) else val) for lab, val in r["fields"].items()}
        os.makedirs(os.path.join(eng, M.DIRS[r["kind"]]), exist_ok=True)
        open(os.path.join(eng, M.DIRS[r["kind"]], r["id"] + ".md"), "w", encoding="utf-8").write(item_text(r["id"], r["fields"], links))
        out.append(r)
    for r in out:
        e = v.setdefault(r["cid"], {}); e["frozenAs"] = r["id"]
        for mc in r["merged_cids"]:
            v.setdefault(mc, {})["frozenAs"] = r["id"]
    save_verdicts(bdir, v)
    with open(os.path.join(bdir, "rejections.md"), "w", encoding="utf-8") as f:
        f.write(f"# Baseline rejections\n\nWritten {today} by {who}. For the knowledge base pipeline to learn from.\n\n| Page | Source id | Title | Reason |\n|---|---|---|---|\n" + "\n".join(rejects) + "\n")
    counts = ", ".join(f"{n} {M.NAMES[k].lower()}{'s' if n != 1 else ''}" for k, n in sorted(counter.items()))
    with open(os.path.join(bdir, FROZEN), "w", encoding="utf-8") as f:
        by_type = ", ".join(f"{k}={n}" for k, n in sorted(counter.items()))
        f.write(f"# Baseline frozen\n\n- Frozen on: {today}\n- Frozen by: {who}\n- Items written: {counts}\n"
                f"- Items by type: {by_type}\n- Rejected: {len(rejects)}\n\n"
                "The registers above this folder started from these items. Every change since is a change set.\n\n"
                "## Id map\n\n| Source id | Item |\n|---|---|\n"
                + "\n".join(f"| {ref} | {nid} |" for ref, nid in idmap.items() if ref not in cids) + "\n"
                + implied_section(out))
    return {"ok": True, "written": len(out), "rejected": len(rejects), "counts": counter}


def mark_exported(bdir, cids, cs_id):
    v = load_verdicts(bdir)
    for cid in cids:
        v.setdefault(cid, {})["exported"] = cs_id
    save_verdicts(bdir, v)
