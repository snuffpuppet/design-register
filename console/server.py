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
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
import model as M
import baseline as B

HERE = os.path.dirname(os.path.abspath(__file__))
ENG = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "test-data/puppy-gloves")
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
CS_DIR = os.path.join(ENG, "change-sets")
B_DIR = os.path.join(ENG, "baseline")
TOOL = "solution-workflows console 0.1"
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

def parse_item(path):
    text = open(path, encoding="utf-8").read()
    item, links = {}, []
    lines = text.split("\n")
    i = 0
    if lines and lines[0] == "---":
        i = 1
        cur_list = None
        while i < len(lines) and lines[i] != "---":
            ln = lines[i]
            if ln.startswith("  - ") and cur_list is not None:
                item[cur_list].append(ln[4:].strip())
            elif re.match(r"^[a-z-]+:", ln):
                k, _, v = ln.partition(":")
                v = v.strip()
                if v == "" and i + 1 < len(lines) and lines[i + 1].startswith("  - "):
                    cur_list = k
                    item[k] = []
                elif v == "":
                    cur_list = None
                    item[k] = ""
                else:
                    cur_list = None
                    item[k] = v
            i += 1
        i += 1
    sec, buf = None, []
    def flush():
        if sec is not None:
            item[sec] = "\n".join(buf).strip()
    for ln in lines[i:]:
        if ln.startswith("## "):
            flush(); sec = ln[3:].strip().lower(); buf = []
        elif sec is not None:
            buf.append(ln)
    flush()
    if isinstance(item.get("links"), str):
        item["links"] = [item["links"]]
    item["links"] = [l for l in item.get("links", []) if str(l).strip()]
    if "kind" in item:
        item["risk-kind"] = item.pop("kind")   # the RSK Kind field; "kind" on an item means its type in the console
    item["kind"] = item["id"].split("-")[0]
    item["pending"] = []
    return item


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
    eng = {"name": os.path.basename(ENG), "phases": [], "current": ""}
    p = os.path.join(ENG, "engagement.md")
    if os.path.exists(p):
        on = False
        for ln in open(p, encoding="utf-8"):
            if ln.startswith("# Engagement:"):
                eng["name"] = ln.split(":", 1)[1].strip()
            if ln.startswith("## Phases"):
                on = True; continue
            if ln.startswith("## "):
                on = False
            if on and ln.startswith("- "):
                name = ln[2:].strip()
                if name.endswith("(current)"):
                    name = name[:-9].strip(); eng["current"] = name
                eng["phases"].append(name)
    return eng


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
    return n


def state():
    items = overlay(load_registers(), load_change_sets())
    return {"engagement": load_engagement(), "items": list(items.values()), "stakeholders": load_stakeholders(),
            "change_sets": load_change_sets(), "today": today(),
            "model": {"states": M.STATES, "terminal": {k: sorted(v) for k, v in M.TERMINAL.items()},
                      "transitions": M.TRANSITIONS, "short": M.SHORT, "long": M.LONG, "labels": M.LABELS,
                      "choices": M.CHOICES, "required": M.REQUIRED_ON_ENTRY, "create": M.REQUIRED_ON_CREATE,
                      "first": M.FIRST_STATE, "names": M.NAMES, "linkWords": M.LINK_WORDS, "closes": {k: sorted(v) for k, v in M.CLOSES.items()}}}


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
                if p == "/api/close-session":
                    return self.send_json(self.close_session(req))
                if p == "/api/baseline/verdict":
                    B.apply_verdict(B_DIR, req["ids"], req.get("verdict"), req.get("reason", ""), req.get("mergedInto"), req.get("fields"), req.get("kind"))
                    return self.send_json({"ok": True})
                if p == "/api/baseline/export":
                    return self.send_json(self.baseline_export(req))
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

    def transition(self, req):
        items = overlay(load_registers(), load_change_sets())
        it = items.get(req["id"])
        if not it:
            raise ValueError("No such item.")
        kind, frm, to = it["kind"], it["status"], req["to"]
        if to not in M.TRANSITIONS.get(kind, {}).get(frm, []):
            raise ValueError(f"{frm} → {to} is not an allowed move for a {M.NAMES[kind]} (I20).")
        merged = dict(it); merged.update({field_key(k): v for k, v in req.get("fields", {}).items()})
        merged["links"] = it["links"] + req.get("links", [])
        missing = M.missing_for(kind, to, merged)
        if kind == "OI" and to == "Blocked" and not merged.get("next action", "").startswith("Blocked:"):
            missing.append('Next action starting "Blocked: "')
        if kind == "CR" and to == "Submitted" and merged.get("implemented-by") == "Vendor" and not merged.get("vendor-ref"):
            missing.append("Vendor ref")
        if missing:
            raise ValueError("Before " + to + " you need: " + "; ".join(missing))
        fields = {"Status": to}
        for k, v in req.get("fields", {}).items():
            fields[label_of(field_key(k))] = v
        if to in M.CLOSES[kind]:
            fields["Closed on"] = today()
        cs = current_change_set(req["madeBy"])
        n = append_block(cs, kind, it["id"], fields, req.get("links", []), self.evidence(req), req.get("gist", "") or f"{frm} to {to}", frm=frm, based_on=it.get("updated", ""))
        return {"ok": True, "changeSet": cs["id"], "item": n}

    def create(self, req):
        kind = req["kind"]
        if kind not in M.DIRS:
            raise ValueError("Unknown type.")
        f = {field_key(k): v for k, v in req.get("fields", {}).items()}
        f["links"] = req.get("links", [])
        missing = []
        for r in M.REQUIRED_ON_CREATE[kind]:
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
        cs = current_change_set(req["madeBy"])
        n = append_block(cs, kind, "new", fields, f["links"], self.evidence(req), req.get("gist", "") or "raised in console")
        return {"ok": True, "changeSet": cs["id"], "item": n, "ref": f"item {n}"}

    def edit(self, req):
        items = overlay(load_registers(), load_change_sets())
        it = items.get(req["id"])
        if not it:
            raise ValueError("No such item.")
        fields = {label_of(field_key(k)): v for k, v in req.get("fields", {}).items() if str(v).strip() != ""}
        if not fields and not req.get("links"):
            raise ValueError("Nothing changed.")
        cs = current_change_set(req["madeBy"])
        n = append_block(cs, it["kind"], it["id"], fields, req.get("links", []), self.evidence(req), req.get("gist", "") or "fields updated", frm=None, based_on=it.get("updated", ""))
        return {"ok": True, "changeSet": cs["id"], "item": n}

    def baseline_state(self):
        if not os.path.isdir(B_DIR):
            return {"present": False, "candidates": [], "clusters": [], "reasons": B.REJECT_REASONS}
        cands = B.load_candidates(B_DIR); v = B.load_verdicts(B_DIR)
        return {"present": True, "candidates": [B.effective(c, v) for c in cands], "clusters": B.clusters(cands),
                "reasons": B.REJECT_REASONS, "pages": sorted(set(c["page"] for c in cands))}

    def baseline_export(self, req):
        cands = B.load_candidates(B_DIR); v = B.load_verdicts(B_DIR)
        blocks, rejects = B.export_blocks(cands, v, today())
        if not blocks and not rejects:
            raise ValueError("Nothing accepted or rejected yet.")
        cs = current_change_set(req["madeBy"])
        for b in blocks:
            append_block(cs, b["kind"], "new", b["fields"], [], self.evidence({**req, "evidence": "baseline of generated registers"}), b["gist"])
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
    HTTPServer(("0.0.0.0", PORT), H).serve_forever()
