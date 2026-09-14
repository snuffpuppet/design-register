#!/usr/bin/env python3
"""Register lifecycle console.

Reads an engagement folder (one markdown file per item, model 2.22 section 7) and every
unapplied change set under <engagement>/change-sets/. Serves a view of the registers as they
would be once those change sets are applied. Every edit made in the console is appended as
an item block to the current session's change set file (model section 11). Item files are
never written.

Usage: server.py <engagement-dir> [port]
"""
import json, os, re, sys, glob, datetime, threading
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
import model as M
import baseline as B
import integrity as I
from items import parse_item, render_item, item_path

HERE = os.path.dirname(os.path.abspath(__file__))
ENG = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "test-data/puppy-gloves")
PORT = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 8080
CS_DIR = os.path.join(ENG, "change-sets")
B_DIR = os.path.join(ENG, "baseline")
DISMISSED_PATH = os.path.join(ENG, "supports-dismissed.json")
DUP_PATH = os.path.join(ENG, "duplicates-dismissed.json")
TOOL = "design-register console 0.1"
LOCK = threading.Lock()

MONTHS = "January February March April May June July August September October November December".split()


def today():
    d = datetime.date.today()
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


def parse_date(s):
    m = re.match(r"\s*(\d{1,2}) (\w+) (\d{4})", s or "")
    if not m or m.group(2) not in MONTHS:
        return None
    return datetime.date(int(m.group(3)), MONTHS.index(m.group(2)) + 1, int(m.group(1)))


# ---------- item files (section 7) ----------

def load_registers():
    items = {}
    for kind, d in M.DIRS.items():
        for p in sorted(glob.glob(os.path.join(ENG, d, f"{kind}-*.md"))):
            it = parse_item(p)
            items[it["id"]] = it
    return items


def load_stakeholders():
    out = []
    for p in sorted(glob.glob(os.path.join(ENG, "stakeholders", "STK-*.md"))):
        it = parse_item(p)
        out.append({k: it.get(k, "") for k in ("id", "name", "role", "organisation", "standing")})
    return out


def load_engagement():
    eng = {"name": os.path.basename(ENG), "phases": [], "current": "", "writes": "direct", "scopes": []}
    p = os.path.join(ENG, "engagement.md")
    if os.path.exists(p):
        sect = None
        for ln in open(p, encoding="utf-8"):
            if ln.startswith("# Engagement:"):
                eng["name"] = ln.split(":", 1)[1].strip()
            m = re.match(r"- Writes:\s*(\S+)", ln)
            if m:
                if m.group(1) not in ("direct", "change-sets"):
                    raise ValueError(f"engagement.md says Writes: {m.group(1)}; it must be direct or change-sets")
                eng["writes"] = m.group(1)
            if ln.startswith("## Phases"):
                sect = "phases"; continue
            if ln.startswith("## Scopes"):
                sect = "scopes"; continue
            if ln.startswith("## "):
                sect = None
            if sect and ln.startswith("- "):
                name = ln[2:].strip()
                if sect == "phases":
                    if name.endswith("(current)"):
                        name = name[:-9].strip(); eng["current"] = name
                    eng["phases"].append(name)
                else:
                    eng["scopes"].append(name)
    return eng


def writes_direct():
    """Direct mode rewrites item files; change-sets mode appends blocks for the ingester. Per engagement."""
    return load_engagement()["writes"] == "direct"


def required_on_create(kind, scopes=None):
    """The model's required fields, less Scope where the engagement names no scopes. Scope is the one
    field the model makes conditional on the engagement rather than on the type. Pass scopes where the
    caller already holds the engagement, so a six-type loop reads engagement.md once rather than six times."""
    if scopes is None:
        scopes = load_engagement()["scopes"]
    req = list(M.REQUIRED_ON_CREATE[kind])
    if not scopes:
        req = [r for r in req if r != "scope"]
    return req


# ---------- change sets (section 11) ----------

def parse_change_set(path):
    cs = {"id": os.path.basename(path)[:-3], "file": os.path.basename(path), "header": {}, "blocks": []}
    blk = None; in_list = None
    for ln in open(path, encoding="utf-8").read().split("\n"):
        if ln.startswith("### Item "):
            parts = [p.strip() for p in ln[4:].split("|")]
            blk = {"n": int(parts[0].replace("Item", "").strip()), "kind": parts[1], "fields": {}, "links": [], "evidence": []}
            cs["blocks"].append(blk); in_list = None
        elif blk is None and ln.startswith("- "):
            k, _, v = ln[2:].partition(":"); cs["header"][k.strip()] = v.strip()
        elif blk is not None and ln.startswith("  - ") and in_list:
            blk[in_list].append(ln[4:].strip())
        elif blk is not None and ln.startswith("- "):
            k, _, v = ln[2:].partition(":"); k = k.strip(); v = v.strip()
            if k in ("Links", "Evidence") and v == "":
                in_list = k.lower(); continue
            in_list = None
            blk["fields"][k] = v
    cs["closed"] = bool(cs["header"].get("Session closed"))
    cs["applied"] = bool(cs["header"].get("Applied on"))
    return cs


def load_change_sets():
    os.makedirs(CS_DIR, exist_ok=True)
    return [parse_change_set(p) for p in sorted(glob.glob(os.path.join(CS_DIR, "CS-*.md")))]


def field_key(label):
    low = label.strip().lower()
    if low == "kind":
        return "risk-kind"
    return low if low in M.LABELS or low in ("title", "status") else low.replace(" ", "-")


def overlay(items, change_sets):
    """Apply every unapplied change set to a copy of the items. New items get provisional ids."""
    for cs in change_sets:
        if cs["applied"]:
            continue
        provisional = {}
        for b in cs["blocks"]:
            target = b["fields"].get("Target", "new")
            if target == "new":
                pid = f"{b['kind']}-{cs['id'][3:]}.{b['n']}"   # e.g. LIM-0002.3 : change set 2, item 3
                provisional[b["n"]] = pid
        for b in cs["blocks"]:
            target = b["fields"].get("Target", "new")
            def resolve(link):
                m = re.search(r"\bitem (\d+)$", link)
                return link[:m.start()] + provisional.get(int(m.group(1)), link[m.start():]) if m else link
            links = [resolve(l) for l in b["links"]]
            if target == "new":
                pid = provisional[b["n"]]
                it = {"id": pid, "kind": b["kind"], "links": links, "pending": [], "provisional": True,
                      "status": M.FIRST_STATE[b["kind"]], "raised-on": cs["header"].get("Session date", "")}
                items[pid] = it
            else:
                it = items.get(target)
                if it is None:
                    continue
                for l in links:
                    if l not in it["links"]:
                        it["links"].append(l)
            for k, v in b["fields"].items():
                if k in ("Target", "Grade", "Verdict", "From", "Based on", "Gist", "Episode"):
                    continue
                it[field_key(k)] = v
            it["pending"].append({"cs": cs["id"], "n": b["n"], "gist": b["fields"].get("Gist", ""),
                                  "status": b["fields"].get("Status"), "from": b["fields"].get("From")})
            it["updated"] = cs["header"].get("Session date", it.get("updated", ""))
    return items


# ---------- writing blocks ----------

def current_change_set(made_by):
    """The open change set for this maker, or a new one."""
    sets = load_change_sets()
    for cs in reversed(sets):
        if not cs["closed"] and not cs["applied"] and cs["header"].get("Made by") == made_by:
            return cs
    n = max([int(cs["id"][3:]) for cs in sets] + [0]) + 1
    cs_id = f"CS-{n:04d}"
    path = os.path.join(CS_DIR, cs_id + ".md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Change set: {cs_id}\n\n- Change set: {cs_id}\n- Session: {TOOL}\n- Session date: {today()}\n"
                f"- Made by: {made_by}\n- Meeting: \n- Approver:\n- Approved on:\n\n")
    return parse_change_set(path)


def append_block(cs, kind, target, fields, links, evidence, gist, frm=None, based_on=None):
    n = max([b["n"] for b in cs["blocks"]] + [0]) + 1
    lines = [f"### Item {n} | {kind} | Confident", f"- Target: {target}", "- Grade: Confident", "- Verdict:"]
    if frm is not None:
        lines += [f"- From: {frm}", f"- Based on: {based_on or ''}"]
    for k, v in fields.items():
        if v is None or str(v).strip() == "":
            continue
        v = str(v).strip().replace("\n", " ⏎ ")
        lines.append(f"- {k}: {v}")
    if links:
        lines.append("- Links:")
        lines += [f"  - {l}" for l in links]
    lines.append("- Evidence:")
    lines += [f"  - {e}" for e in evidence]
    lines.append(f"- Gist: {gist}")
    with open(os.path.join(CS_DIR, cs["file"]), "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n\n")
    # keep the parsed change set in step with the file, so a second block in the same request
    # takes the next number rather than repeating this one.
    cs["blocks"].append({"n": n, "kind": kind, "fields": dict(fields, Target=target), "links": list(links), "evidence": list(evidence)})
    return n


def state():
    items = overlay(load_registers(), load_change_sets())
    eng = load_engagement()
    return {"engagement": eng, "items": list(items.values()), "stakeholders": load_stakeholders(),
            "integrity": integrity_of(items),
            "dupes": B.clusters([i for i in items.values() if not i.get("provisional")], set(load_dup_dismissed())),
            "unreviewed": sorted(B.unreviewed_ids(B_DIR) & set(items)),
            "change_sets": load_change_sets(), "today": today(),
            "model": {"states": M.STATES, "terminal": {k: sorted(v) for k, v in M.TERMINAL.items()},
                      "transitions": M.TRANSITIONS, "short": M.SHORT, "long": M.LONG, "labels": M.LABELS,
                      "choices": M.CHOICES, "required": M.REQUIRED_ON_ENTRY, "create": {k: required_on_create(k, eng["scopes"]) for k in M.DIRS},
                      "first": M.FIRST_STATE, "names": M.NAMES, "linkWords": M.LINK_WORDS, "closes": {k: sorted(v) for k, v in M.CLOSES.items()}}}


def load_dismissed():
    """The dismissed suggestions. A file that will not parse is treated as empty rather than taken as far
    as /api/state, where it would stop the console dead over a hand edit."""
    if not os.path.exists(DISMISSED_PATH):
        return {}
    try:
        gone = json.load(open(DISMISSED_PATH, encoding="utf-8"))
    except (ValueError, OSError):
        return {}
    return gone if isinstance(gone, dict) else {}


def load_dup_dismissed():
    """Duplicate groups the reviewer has set aside, keyed by baseline.cluster_key. Unparseable means empty."""
    if not os.path.exists(DUP_PATH):
        return {}
    try:
        gone = json.load(open(DUP_PATH, encoding="utf-8"))
    except (ValueError, OSError):
        return {}
    return gone if isinstance(gone, dict) else {}


def dismiss_dup(ids, undo=False):
    gone = load_dup_dismissed()
    key = B.cluster_key(ids)
    if undo:
        gone.pop(key, None)
    else:
        gone[key] = {"ids": sorted(ids), "on": today()}
    json.dump(gone, open(DUP_PATH, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


def integrity_of(items):
    """Section 9 and the SUPPORTS table over the overlaid items, less the suggestions already dismissed."""
    eng = load_engagement()
    res = I.check(list(items.values()), phases=eng["phases"] or None, stakeholders=load_stakeholders() or None, today=today(), scopes=eng["scopes"] or None)
    gone = load_dismissed()
    res["suggestions"] = [s for s in res["suggestions"] if s["key"] not in gone]
    res["dismissed"] = len(gone)
    return res


def label_of(key):
    return M.LABELS.get(key, key.capitalize())


class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=os.path.join(HERE, "static"), **kw)

    def log_message(self, *a):
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def send_json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

    def do_GET(self):
        p = urlparse(self.path).path
        if p == "/api/state":
            return self.send_json(state())
        if p.startswith("/api/change-set/"):
            f = os.path.join(CS_DIR, os.path.basename(p) + ".md")
            if not os.path.exists(f):
                return self.send_json({"error": "no such change set"}, 404)
            body = open(f, encoding="utf-8").read().encode()
            self.send_response(200); self.send_header("Content-Type", "text/markdown; charset=utf-8"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body); return
        if p == "/api/baseline":
            return self.send_json(self.baseline_state())
        if p == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        p = urlparse(self.path).path
        n = int(self.headers.get("Content-Length", 0))
        req = json.loads(self.rfile.read(n) or b"{}")
        with LOCK:
            try:
                if p == "/api/transition":
                    return self.send_json(self.transition(req))
                if p == "/api/create":
                    return self.send_json(self.create(req))
                if p == "/api/edit":
                    return self.send_json(self.edit(req))
                if p == "/api/merge":
                    return self.send_json(self.merge(req))
                if p == "/api/delete":
                    return self.send_json(self.delete(req))
                if p == "/api/close-session":
                    return self.send_json(self.close_session(req))
                if p == "/api/baseline/verdict":
                    B.apply_verdict(B_DIR, req["ids"], req.get("verdict"), req.get("reason", ""), req.get("mergedInto"), req.get("fields"), req.get("kind"))
                    return self.send_json({"ok": True})
                if p == "/api/baseline/skip-page":
                    B.set_skip(B_DIR, req["page"], req.get("undo", False))
                    return self.send_json({"ok": True})
                if p == "/api/baseline/not-duplicates":
                    B.dismiss_cluster(B_DIR, req["ids"], req.get("undo", False))
                    return self.send_json({"ok": True})
                if p == "/api/rationalise/not-duplicates":
                    dismiss_dup(req["ids"], req.get("undo", False))
                    return self.send_json({"ok": True})
                if p == "/api/rationalise/reviewed":
                    if not B.mark_reviewed(B_DIR, req["id"]):
                        raise ValueError("That item was not frozen from a candidate; nothing to mark.")
                    return self.send_json({"ok": True})
                if p == "/api/baseline/support":
                    sugg = next((x for x in B.suggestions(B.load_candidates(B_DIR), B.load_verdicts(B_DIR))["suggestions"] if x["key"] == req["key"]), None)
                    if req["verdict"] != "Dismiss" and not sugg:
                        raise ValueError("That suggestion is no longer current; reload.")
                    if req["verdict"] == "Reassess" and (not sugg or sugg["rule"] not in ("S5", "S6")):
                        raise ValueError("Reassess applies only to a limitation the source calls Accepted or Change requested.")
                    B.support_verdict(B_DIR, req["key"], req["verdict"], req.get("reason", ""), req.get("fields"), sugg, target=req.get("target"))
                    return self.send_json({"ok": True})
                if p == "/api/supports":
                    return self.send_json(self.supports_preview(req))
                if p == "/api/support/accept":
                    return self.send_json(self.support_accept(req))
                if p == "/api/support/dismiss":
                    return self.send_json(self.support_dismiss(req))
                if p == "/api/support/link":
                    return self.send_json(self.support_link(req))
                if p == "/api/baseline/export":
                    return self.send_json(self.baseline_export(req))
                if p == "/api/baseline/freeze":
                    who = req.get("madeBy", "").strip()
                    if not who:
                        raise ValueError("Say who you are first (Made by).")
                    return self.send_json(B.freeze(ENG, B_DIR, B.load_candidates(B_DIR), B.load_verdicts(B_DIR), today(), who,
                                                    scopes=load_engagement()["scopes"] or None))
            except ValueError as e:
                return self.send_json({"error": str(e)}, 400)
        self.send_json({"error": "unknown"}, 404)

    # -- operations. Each validates against the model, then appends one block. --
    def evidence(self, req):
        who = req.get("madeBy", "").strip()
        if not who:
            raise ValueError("Say who you are first (Made by).")
        note = req.get("evidence", "").strip() or "console session"
        return [f"{today()} | {who} | {note}"]

    def supports_preview(self, req):
        """The suggestions the item would raise once the given move, fields and links are in place."""
        items = overlay(load_registers(), load_change_sets())
        it = items.get(req["id"])
        if not it:
            raise ValueError("No such item.")
        merged = dict(it); merged.update({field_key(k): v for k, v in req.get("fields", {}).items()})
        merged["links"] = it["links"] + req.get("links", [])
        merged["status"] = req.get("to") or it["status"]
        items[it["id"]] = merged
        res = integrity_of(items)
        return {"suggestions": [s for s in res["suggestions"] if s["id"] == it["id"]]}

    def offer_fields(self, sugg, overrides):
        """The offer's fields with the reviewer's overrides, refused when it needs an owner and has none."""
        f = dict(sugg["fields"]); f.update({field_key(k): v for k, v in (overrides or {}).items() if v is not None})
        if sugg["needsOwner"] and not str(f.get("owner", "")).strip():
            raise ValueError("Set the owner before accepting this one; the engine does not guess stakeholders.")
        return f

    def commit(self, kind, target, fields, links, req, gist, frm=None, based_on=None, delete=False):
        """The one place a Live write lands. Change-sets mode appends a block to the maker's open change set;
        direct mode rewrites the item file, stamps Updated and appends one History line. Callers build fields
        by label and links as text, the same in both modes. Returns item (block number or id) and ref, the
        text a link uses to name what was written. `delete=True` removes the target's file instead of writing
        it; direct mode only, the caller has already refused otherwise."""
        ev = self.evidence(req)
        if not writes_direct():
            cs = current_change_set(req["madeBy"])
            n = append_block(cs, kind, target, fields, links, ev, gist, frm=frm, based_on=based_on)
            return {"changeSet": cs["id"], "item": n, "ref": f"item {n}"}
        if delete:
            p = item_path(ENG, target)
            if not os.path.exists(p):
                raise ValueError(f"No file for {target}.")
            os.remove(p)
            return {"item": target, "removed": p, "ref": target}
        if target == "new":
            taken = [int(os.path.basename(p)[len(kind) + 1:-3]) for p in glob.glob(os.path.join(ENG, M.DIRS[kind], f"{kind}-*.md"))]
            it = {"id": f"{kind}-{max(taken + [0]) + 1:04d}", "kind": kind, "links": [], "history": [], "raised-on": today(), "closed-on": ""}
        else:
            it = parse_item(item_path(ENG, target))
        for k, v in fields.items():
            it[field_key(k)] = v
        for l in links:
            if l not in it["links"]:
                it["links"].append(l)
        it["updated"] = today()
        move = f"{frm} → {it['status']}" if frm is not None else ""
        if move and gist == f"{frm} to {it['status']}":
            gist = ""   # the default gist only repeats the move
        it["history"].append(" | ".join(x for x in [today(), req["madeBy"].strip(), move, gist, ev[0].split(" | ", 2)[2]] if x))
        p = item_path(ENG, it["id"]); os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w", encoding="utf-8").write(render_item(it))
        return {"item": it["id"], "written": p, "ref": it["id"]}

    def write_offer(self, req, sugg, overrides):
        """One new item for an offer. Returns the ref a link uses to name it."""
        f = self.offer_fields(sugg, overrides)
        kind = sugg["kind"]
        fields = {"Title": f.get("title", ""), "Status": sugg["status"], "Raised on": today()}
        for k in M.SHORT[kind] + M.LONG[kind]:
            if f.get(k):
                fields[label_of(k)] = f[k]
        if kind == "RSK":
            fields["Kind"] = f.get("risk-kind", "Risk")
        links = [sugg["reverse"]] if sugg["reverse"] else []
        return self.commit(kind, "new", fields, links, req, f"{sugg['rule']}: implied by {sugg['id']}")["ref"]

    def transition(self, req):
        items = overlay(load_registers(), load_change_sets())
        it = items.get(req["id"])
        if not it:
            raise ValueError("No such item.")
        kind, frm, to = it["kind"], it["status"], req["to"]
        if to not in M.TRANSITIONS.get(kind, {}).get(frm, []):
            raise ValueError(f"{frm} → {to} is not an allowed move for a {M.NAMES[kind]} (I20).")
        chosen = []
        wanted = req.get("supports") or []
        if wanted:
            preview = {s["key"]: s for s in self.supports_preview({**req, "to": to})["suggestions"]}
            seen = set()
            for w in wanted:
                if w["key"] in seen:   # one offer per suggestion, however many times it was sent
                    continue
                seen.add(w["key"])
                s = preview.get(w["key"])
                if not s:
                    raise ValueError("A chosen support is no longer current; reload and try again.")
                self.offer_fields(s, w.get("fields"))   # refuse early, before anything is written
                chosen.append((s, w.get("fields")))
        self.evidence(req)   # the maker must be named before a change set is opened
        merged = dict(it); merged.update({field_key(k): v for k, v in req.get("fields", {}).items()})
        merged["links"] = it["links"] + req.get("links", []) + [s["link"] + "item ?" for s, _ in chosen]
        missing = M.missing_for(kind, to, merged)
        if kind == "OI" and to == "Blocked" and not merged.get("next action", "").startswith("Blocked:"):
            missing.append('Next action starting "Blocked: "')
        if kind == "CR" and to == "Submitted" and merged.get("implemented-by") == "Vendor" and not merged.get("vendor-ref"):
            missing.append("Vendor ref")
        if missing:
            raise ValueError("Before " + to + " you need: " + "; ".join(missing))
        support_links = []
        for s, f in chosen:
            support_links.append(s["link"] + self.write_offer(req, s, f))
        fields = {"Status": to}
        for k, v in req.get("fields", {}).items():
            fields[label_of(field_key(k))] = v
        if to in M.CLOSES[kind]:
            fields["Closed on"] = today()
        r = self.commit(kind, it["id"], fields, req.get("links", []) + support_links, req, req.get("gist", "") or f"{frm} to {to}", frm=frm, based_on=it.get("updated", ""))
        return {"ok": True, "changeSet": r.get("changeSet"), "item": r["item"], "supports": len(support_links)}

    def support_accept(self, req):
        """Write one offer the live registers are missing and link the trigger to it."""
        items = overlay(load_registers(), load_change_sets())
        it = items.get(req["id"])
        if not it:
            raise ValueError("No such item.")
        s = next((x for x in integrity_of(items)["suggestions"] if x["key"] == req["key"]), None)
        if not s:
            raise ValueError("That suggestion is no longer current; reload.")
        self.offer_fields(s, req.get("fields"))   # refuse early, before anything is written
        self.evidence(req)
        ref = self.write_offer(req, s, req.get("fields"))
        r = self.commit(it["kind"], it["id"], {}, [s["link"] + ref], req, f"{s['rule']}: linked to the implied {s['kind']}", based_on=it.get("updated", ""))
        return {"ok": True, "changeSet": r.get("changeSet"), "item": ref if writes_direct() else int(ref.split()[1]), "linkBlock": r["item"]}

    def support_link(self, req):
        """Point the trigger at a record the registers already hold instead of creating one: an edit block
        with the link on the trigger, and one with the reverse on the target where the model names one."""
        items = overlay(load_registers(), load_change_sets())
        it = items.get(req["id"])
        if not it:
            raise ValueError("No such item.")
        s = next((x for x in integrity_of(items)["suggestions"] if x["key"] == req["key"]), None)
        if not s:
            raise ValueError("That suggestion is no longer current; reload.")
        target = items.get(str(req.get("target", "")).strip())
        if not target or target["id"] == it["id"]:
            raise ValueError("Pick the record to link.")
        if target["kind"] != s["kind"]:
            raise ValueError(f"{target['id']} is a {M.NAMES[target['kind']]}; this offer needs a {M.NAMES[s['kind']]}.")
        r = self.commit(it["kind"], it["id"], {}, [f"{s['link']}{target['id']}"], req, f"{s['rule']}: linked to the existing {target['id']}", based_on=it.get("updated", ""))
        m = None
        if s["reverse"]:
            m = self.commit(target["kind"], target["id"], {}, [s["reverse"]], req, f"{s['rule']}: reverse link from {it['id']}", based_on=target.get("updated", ""))["item"]
        return {"ok": True, "changeSet": r.get("changeSet"), "item": r["item"], "reverseBlock": m}

    def support_dismiss(self, req):
        who = req.get("madeBy", "").strip()
        if not who:
            raise ValueError("Say who you are first (Made by).")
        reason = req.get("reason", "").strip()
        if not reason:
            raise ValueError("Give a reason; it is kept beside the register.")
        gone = load_dismissed()
        gone[req["key"]] = {"id": req.get("id", ""), "rule": req.get("rule", ""), "reason": reason, "by": who, "on": today()}
        json.dump(gone, open(DISMISSED_PATH, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        return {"ok": True}

    def create(self, req):
        kind = req["kind"]
        if kind not in M.DIRS:
            raise ValueError("Unknown type.")
        f = {field_key(k): v for k, v in req.get("fields", {}).items()}
        f["links"] = req.get("links", [])
        missing = []
        for r in required_on_create(kind):
            if r.startswith("link:"):
                if not any(l.lower().startswith(r[5:]) for l in f["links"]):
                    missing.append(f"Links: {r[5:]} …")
            elif not str(f.get(r, "")).strip():
                missing.append(label_of(r))
        if missing:
            raise ValueError("A new " + M.NAMES[kind].lower() + " needs: " + "; ".join(missing))
        status = req.get("status") or M.FIRST_STATE[kind]
        first = M.FIRST_STATE[kind]
        if status != first:
            if status not in M.TRANSITIONS.get(kind, {}).get(first, []):
                raise ValueError(f"A new {M.NAMES[kind].lower()} can start in {first} or move straight to one of: " + ", ".join(M.TRANSITIONS.get(kind, {}).get(first, [])))
            f["links"] = f["links"]
            more = M.missing_for(kind, status, f)
            if more:
                raise ValueError(f"To start in {status} you need: " + "; ".join(more))
        fields = {"Title": f.get("title", ""), "Status": status, "Raised on": today()}
        if status in M.CLOSES[kind]:
            fields["Closed on"] = today()
        for k in M.SHORT[kind] + M.LONG[kind]:
            if f.get(k):
                fields[label_of(k)] = f[k]
        r = self.commit(kind, "new", fields, f["links"], req, req.get("gist", "") or "raised in console")
        return {"ok": True, "changeSet": r.get("changeSet"), "item": r["item"], "ref": r["ref"]}

    def edit(self, req):
        items = overlay(load_registers(), load_change_sets())
        it = items.get(req["id"])
        if not it:
            raise ValueError("No such item.")
        fields = {label_of(field_key(k)): v for k, v in req.get("fields", {}).items() if str(v).strip() != ""}
        if not fields and not req.get("links"):
            raise ValueError("Nothing changed.")
        r = self.commit(it["kind"], it["id"], fields, req.get("links", []), req, req.get("gist", "") or "fields updated", based_on=it.get("updated", ""))
        return {"ok": True, "changeSet": r.get("changeSet"), "item": r["item"]}

    def rewrite_links(self, items, old, new, gist, req):
        """Every item whose Links name `old` gets them rewritten to `new`, or dropped when new is None, with a
        History line. Returns the ids touched. A rewritten link that duplicates one already held is dropped."""
        touched = []
        pat = re.compile(r"\b" + re.escape(old) + r"\b")
        for it in items.values():
            if it["id"] in (old, new) or not any(pat.search(l) for l in it["links"]):
                continue
            kept = []
            for l in it["links"]:
                if not pat.search(l):
                    if l not in kept:
                        kept.append(l)
                    continue
                if new is None:
                    continue
                nl = pat.sub(new, l)
                if nl not in kept:
                    kept.append(nl)
            path = item_path(ENG, it["id"]); cur = parse_item(path)
            cur["links"] = kept; cur["updated"] = today()
            cur["history"].append(" | ".join([today(), req["madeBy"].strip(), gist, self.evidence(req)[0].split(" | ", 2)[2]]))
            open(path, "w", encoding="utf-8").write(render_item(cur))
            touched.append(it["id"])
        return touched

    def merge(self, req):
        """Fold each loser into the survivor, rewrite every link that named the loser, remove the loser's file.
        Direct mode only: the ingester's change set format has no block for a merge."""
        if not writes_direct():
            raise ValueError("Merge is a direct write; this engagement writes change sets, which have no block for it.")
        self.evidence(req)
        items = load_registers()
        surv = items.get(req.get("survivor", ""))
        losers = [items.get(x) for x in req.get("losers", [])]
        if not surv or not losers or any(l is None for l in losers):
            raise ValueError("Pick the survivor and at least one item to fold into it.")
        if any(l["id"] == surv["id"] for l in losers):
            raise ValueError("An item cannot be merged into itself.")
        for l in losers:
            if l["kind"] != surv["kind"]:
                raise ValueError(f"{l['id']} is a {M.NAMES[l['kind']]}; {surv['id']} is a {M.NAMES[surv['kind']]}. Merge only folds items of one type.")
        removed, touched = [], []
        for l in losers:
            surv = load_registers()[surv["id"]]
            fields = {}
            for k in M.SHORT[surv["kind"]] + M.LONG[surv["kind"]] + ["description"]:
                if k in ("scope", "status", "source", "notes"):
                    continue
                if not str(surv.get(k, "") or "").strip() and str(l.get(k, "") or "").strip():
                    fields[label_of(k)] = l[k]
            src = [s for s in (surv.get("source", "") + "\n" + l.get("source", "")).split("\n") if s.strip()]
            fields["Source"] = "\n".join(dict.fromkeys(src))
            notes = surv.get("notes", "") or ""
            if str(l.get("notes", "") or "").strip():
                notes = (notes + "\n" if notes else "") + f"Merged in from {l['id']}: {l['notes']}"
            fields["Notes"] = notes or ""
            links = [x for x in l["links"] if x not in surv["links"] and not re.search(r"\b" + re.escape(surv["id"]) + r"\b", x)]
            self.commit(surv["kind"], surv["id"], fields, links, req, f"merged {l['id']} into this item", based_on=surv.get("updated", ""))
            touched += self.rewrite_links(load_registers(), l["id"], surv["id"], f"merged {l['id']} into {surv['id']}", req)
            self.commit(l["kind"], l["id"], {}, [], req, "", delete=True)
            removed.append(l["id"])
        return {"ok": True, "survivor": surv["id"], "removed": removed, "touched": sorted(set(touched))}

    def delete(self, req):
        """Remove one item's file after dropping every link that named it. Direct mode only, reason required."""
        if not writes_direct():
            raise ValueError("Delete is a direct write; this engagement writes change sets, which have no block for it.")
        self.evidence(req)
        reason = str(req.get("reason", "")).strip()
        if not reason:
            raise ValueError("Give a reason; it goes into the History of every item that loses a link.")
        items = load_registers()
        it = items.get(req.get("id", ""))
        if not it:
            raise ValueError("No such item.")
        touched = self.rewrite_links(items, it["id"], None, f"dropped link to {it['id']}, deleted: {reason}", req)
        self.commit(it["kind"], it["id"], {}, [], req, "", delete=True)
        return {"ok": True, "removed": it["id"], "touched": touched}

    def baseline_state(self):
        if not os.path.isdir(B_DIR):
            return {"present": False, "candidates": [], "clusters": [], "reasons": B.REJECT_REASONS, "frozen": None,
                    "suggestions": {"suggestions": [], "prompts": [], "failures": [], "warnings": [], "dismissed": 0}}
        cands = B.load_candidates(B_DIR); v = B.load_verdicts(B_DIR)
        return {"present": True, "candidates": [B.effective(c, v) for c in cands],
                "clusters": B.clusters([c for c in cands if not c.get("implied")], set(v.get(B.DISMISSED, []))),
                "suggestions": B.suggestions(cands, v),
                "dismissed": len(v.get(B.DISMISSED, [])), "frozen": B.frozen(B_DIR), "states": M.STATES,
                "reasons": B.REJECT_REASONS, "pages": sorted(set(c["page"] for c in cands)),
                "skipped": B.load_skips(B_DIR), "allPages": B.page_titles(B_DIR)}

    def baseline_export(self, req):
        cands = B.load_candidates(B_DIR); v = B.load_verdicts(B_DIR)
        blocks, rejects = B.export_blocks(cands, v, today())
        if not blocks and not rejects:
            raise ValueError("Nothing accepted or rejected yet.")
        ev = self.evidence({**req, "evidence": "baseline of generated registers"})   # named maker first
        cs = current_change_set(req["madeBy"])
        for b in blocks:
            append_block(cs, b["kind"], "new", b["fields"], [], ev, b["gist"])
        B.mark_exported(B_DIR, [b["cid"] for b in blocks] + [c["id"] for c in cands if v.get(c["id"], {}).get("verdict") in ("Reject", "Merge")], cs["id"])
        with open(os.path.join(B_DIR, "rejections.md"), "w", encoding="utf-8") as f:
            f.write(f"# Baseline rejections\n\nWritten {today()} by {req['madeBy']}. For the knowledge base pipeline to learn from.\n\n| Page | Source id | Title | Reason |\n|---|---|---|---|\n" + "\n".join(rejects) + "\n")
        return {"ok": True, "changeSet": cs["id"], "accepted": len(blocks), "rejected": len(rejects)}

    def close_session(self, req):
        cs = current_change_set(req["madeBy"])
        path = os.path.join(CS_DIR, cs["file"])
        text = open(path, encoding="utf-8").read()
        text = text.replace("- Approver:\n", f"- Session closed: {today()}\n- Approver:\n", 1)
        open(path, "w", encoding="utf-8").write(text)
        return {"ok": True, "changeSet": cs["id"]}


if __name__ == "__main__":
    os.makedirs(CS_DIR, exist_ok=True)
    print(f"console: engagement {ENG}\nconsole: http://localhost:{PORT}/")
    # threaded: one slow or stuck client must not freeze the console for everyone.
    # Writes stay serialised on LOCK in do_POST, so only reads actually run concurrently.
    ThreadingHTTPServer(("0.0.0.0", PORT), H).serve_forever()
