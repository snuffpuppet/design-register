"""Section 9 and the SUPPORTS table evaluated over a list of item dicts.

check(items) is pure: it reads the dicts and returns failures, warnings, prompts and suggestions.
It never writes. Item dicts are the shape server.parse_item produces (see the plan's file map);
baseline.as_items produces the same shape from candidates.
"""
import datetime, hashlib, re
import model as M

MONTHS = "January February March April May June July August September October November December".split()


def parse_date(s):
    m = re.match(r"^(\d{1,2}) (\w+) (\d{4})", str(s or ""))
    if not m or m.group(2) not in MONTHS:
        return None
    return datetime.date(int(m.group(3)), MONTHS.index(m.group(2)) + 1, int(m.group(1)))

LINK_ID = re.compile(r"\b([A-Z]+-\d{4}(?:\.\d+)?|[ci][0-9a-f]{8,10})\b")
TOOLING = re.compile(r"\b(build|built|report|tool|tooling|script|extract|dashboard|spreadsheet)\b", re.I)
UNMET = re.compile(r"\b(defer|deferred|later phase|out of scope|won't|will not|drop|dropped|not in this phase)\b", re.I)


def suggestion_key(rule, trigger_id):
    return "s" + hashlib.sha1(f"{rule}|{trigger_id}".encode()).hexdigest()[:10]


def link_target(link):
    m = LINK_ID.search(link)
    return m.group(1) if m else None


def links_with(item, word):
    return [l for l in item.get("links", []) if l.lower().startswith(word.lower() + " ")]


def option_lines(item):
    txt = str(item.get("options", "") or "")
    parts = re.split(r"(?:\n|\s)(?=\d+[.)]\s)", txt)
    return [p.strip() for p in parts if p.strip()]


def chosen_text(item):
    """The chosen option's text without its number and without the impact and phase clauses."""
    n = str(item.get("chosen-option", "") or "").strip().rstrip(".")
    for l in option_lines(item):
        m = re.match(r"(\d+)[.)]\s*(.*)", l)
        if m and m.group(1) == n:
            return m.group(2).split(";")[0].strip()
    return ""


def beaten_text(item):
    n = str(item.get("chosen-option", "") or "").strip().rstrip(".")
    out = []
    for l in option_lines(item):
        m = re.match(r"(\d+)[.)]\s*(.*)", l)
        if m and m.group(1) != n:
            out.append(m.group(2).split(";")[0].strip())
    return "; ".join(out)


class _Ctx(dict):
    def __missing__(self, k):
        return ""


def offer(row, trigger):
    ctx = _Ctx({k: (v if isinstance(v, str) else "") for k, v in trigger.items()})
    ctx["chosen"] = chosen_text(trigger); ctx["beaten"] = beaten_text(trigger)
    out = {}
    for key, tpl in row["fields"].items():
        val = tpl.format_map(ctx).strip()
        val = re.sub(r"\s+", " ", val).strip(" :;,")
        if val or tpl == "":
            out[key] = val
    # A required field the template left empty still belongs in the offer, as an empty box the
    # reviewer fills. Title and source are handled here; a link: entry is not a field.
    okind = row["offer"][0] if row["offer"] else None
    for key in M.REQUIRED_ON_CREATE.get(okind, []):
        if key in ("title", "source") or key.startswith("link:"):
            continue
        out.setdefault(key, "")
    if "source" not in out:
        out["source"] = f"Implied by {trigger['id']} under {row['rule']} ({row['check']})"
    return out


def _predicate(pred, item, by_id):
    """True when the predicate holds for the item."""
    if pred is None:
        return True
    if pred.startswith("link:"):
        parts = pred.split(":")
        word, kind = parts[1], (parts[2] if len(parts) > 2 else None)
        for l in links_with(item, word):
            t = link_target(l)
            if kind is None or (t and (t.startswith(kind + "-") or (t in by_id and by_id[t]["kind"] == kind))):
                return True
        return False
    if pred.startswith("linked:"):
        _, word, kind, states = pred.split(":")
        wanted = states.split("|")
        for l in links_with(item, word):
            t = by_id.get(link_target(l))
            if t and t["kind"] == kind and t["status"] in wanted:
                return True
        return False
    if pred.startswith("field:"):
        return bool(str(item.get(pred[6:], "") or "").strip())
    if pred == "tooling":
        return bool(TOOLING.search(chosen_text(item)))
    if pred == "unmet":
        return bool(UNMET.search(chosen_text(item)))
    raise ValueError(f"unknown predicate {pred}")


def suggestions(items, by_id):
    sugs, prompts = [], []
    for it in items:
        for row in M.SUPPORTS:
            kind, states = row["when"]
            if it["kind"] != kind or (states is not None and it["status"] not in states):
                continue
            if not _predicate(row["only_if"], it, by_id) or _predicate(row["unless"], it, by_id):
                continue
            if row["offer"] is None:
                prompts.append({"rule": row["rule"], "check": row["check"], "level": row["level"], "id": it["id"], "text": row["prompt"]})
                continue
            okind, ostate = row["offer"]
            fields = offer(row, it)
            word, oword = row["link"]
            sugs.append({"key": suggestion_key(row["rule"], it["id"]), "rule": row["rule"], "check": row["check"], "level": row["level"],
                         "id": it["id"], "kind": okind, "status": ostate, "fields": fields,
                         "link": word + " ", "reverse": f"{oword} {it['id']}" if oword else None,
                         "needsOwner": "owner" in M.REQUIRED_ON_CREATE[okind] and not fields.get("owner")})
    return sugs, prompts


def check(items, phases=None, stakeholders=None, today=None):
    by_id = {}
    for it in items:
        by_id.setdefault(it["id"], it)
    sugs, prompts = suggestions(items, by_id)
    failures, warnings = rules(items, by_id, phases, stakeholders, today)
    return {"failures": failures, "warnings": warnings, "prompts": prompts, "suggestions": sugs}


def rules(items, by_id, phases=None, stakeholders=None, today=None):
    F, W = [], []
    fail = lambda rule, it, text: F.append({"rule": rule, "id": it["id"], "text": text})
    warn = lambda rule, it, text: W.append({"rule": rule, "id": it["id"], "text": text})
    today = parse_date(today) if today else datetime.date.today()
    seen = set()
    for it in items:
        if it["id"] in seen:
            fail("I1", it, "id appears twice")
        seen.add(it["id"])
    names = None
    if stakeholders is not None:
        names = {s["name"] for s in stakeholders}
        mentioned = {s["name"] for s in stakeholders if str(s.get("role", "")).lower() == "mentioned"}

        def known(name):
            return not name or name in names or name.startswith("Vendor:") or name == "Joint"
    for it in items:
        k, st = it["kind"], it["status"]
        term = st in M.TERMINAL.get(k, set())
        # I2
        if st not in M.STATES.get(k, []):
            fail("I2", it, f"status {st!r} is not a {M.NAMES.get(k, k)} state")
        else:
            missing = M.missing_for(k, st, it)
            if missing:
                fail("I2", it, "missing for " + st + ": " + "; ".join(missing))
        if not str(it.get("raised-on", "")).strip():
            fail("I2", it, "no Raised on")
        if st in M.CLOSES.get(k, set()) and not str(it.get("closed-on", "")).strip():
            fail("I2", it, "no Closed on")
        # I3
        if not term and not str(it.get("owner", "")).strip():
            fail("I3", it, "no Owner")
        needs_oi = {"REQ": ["Draft"], "DEC": ["Proposed"], "LIM": ["Under assessment"], "CR": ["Proposed", "For approval", "Submitted"]}
        if st in needs_oi.get(k, []):
            words = {"REQ": "worked by", "DEC": "proposed by", "LIM": "assessed by", "CR": "worked by"}[k]
            ois = [by_id.get(link_target(l)) for l in links_with(it, words)]
            if not any(o and o["kind"] == "OI" and str(o.get("owner", "")).strip() for o in ois):
                fail("I3", it, f"no open item with an owner linked '{words}'")
        # I4
        if k == "OI" and st != "Closed" and not str(it.get("next action", "")).strip():
            fail("I4", it, "no Next action")
        # I5
        if phases is not None and k in ("REQ", "CR") and str(it.get("phase", "")).strip() and it["phase"] not in phases:
            fail("I5", it, f"phase {it['phase']!r} is not in the engagement's Phases")
        # I6
        for l in it.get("links", []):
            t = link_target(l)
            if t and t not in by_id and not l.lower().startswith("resolves into none"):
                fail("I6", it, f"link target {t} does not exist")
        # I7
        if k == "LIM":
            disp = links_with(it, "dispositioned by")
            targets = [by_id.get(link_target(l)) for l in disp]
            if st == "Accepted" and not any(t and t["kind"] == "DEC" and t["status"] == "Accepted" for t in targets):
                fail("I7", it, "Accepted without a dispositioned by link to an Accepted DEC")
            if st == "Change requested" and not any(t and t["kind"] == "CR" and t["status"] not in ("Withdrawn", "Rejected") for t in targets):
                fail("I7", it, "Change requested without a dispositioned by link to a live CR")
            if st in ("Accepted", "Change requested") and not links_with(it, "constrains"):
                fail("I7", it, "no constrains link")
            if st in ("Identified", "Under assessment") and disp:
                fail("I7", it, "dispositioned by link before disposition")
            if st == "Withdrawn" and not str(it.get("source", "")).strip():
                fail("I7", it, "Withdrawn without a reason in Source")
            for l in links_with(it, "previously dispositioned by"):
                t = by_id.get(link_target(l))
                if not (t and ((t["kind"] == "DEC" and t["status"] == "Superseded") or (t["kind"] == "CR" and t["status"] in ("Withdrawn", "Rejected")))):
                    fail("I7", it, "previously dispositioned by names a live record")
        # I8
        if k == "DEC" and st == "Superseded":
            t = [by_id.get(link_target(l)) for l in links_with(it, "superseded by")]
            if not any(x and x["kind"] == "DEC" and x["status"] in ("Accepted", "Proposed") for x in t):
                fail("I8", it, "Superseded without a superseded by link to a live DEC")
        # I9
        if k == "OI":
            if st == "Closed" and (not str(it.get("closed-on", "")).strip() or not links_with(it, "resolves into")):
                fail("I9", it, "Closed without Closed on and a resolves into link")
            if st == "Blocked" and not str(it.get("next action", "")).startswith("Blocked:"):
                fail("I9", it, "Blocked without a Next action starting 'Blocked: '")
        # I10
        if k == "CR":
            if st in ("Approved", "Submitted", "Delivered", "Deferred", "Withdrawn", "Rejected") and not (str(it.get("approved-by", "")).strip() and str(it.get("closed-on", "")).strip()):
                fail("I10", it, f"{st} without Approved by and Closed on")
            trig = [by_id.get(link_target(l)) for l in links_with(it, "triggered by")]
            if not any(t and t["kind"] in ("LIM", "REQ") for t in trig):
                fail("I10", it, "no triggered by link to a LIM or REQ")
            for t in trig:
                if t and t["kind"] == "LIM" and t["status"] == "Change requested" and not any(link_target(l) == it["id"] for l in links_with(t, "dispositioned by")):
                    fail("I10", it, f"triggered by {t['id']} in Change requested but is not its disposition")
        # I11
        if k == "DEC" and st in ("Accepted", "Rejected") and not (str(it.get("approved-by", "")).strip() and str(it.get("closed-on", "")).strip() and str(it.get("consulted", "")).strip()):
            fail("I11", it, f"{st} without Approved by, Closed on and Consulted")
        # I12
        if k in ("REQ", "DEC", "LIM", "CR") and it.get("implemented-by") not in ("Vendor", "Internal", "Both"):
            fail("I12", it, "Implemented by is not Vendor, Internal or Both")
        # I13
        if k == "RSK" and st == "Realised" and not links_with(it, "realised as"):
            fail("I13", it, "Realised without a realised as link")
        # I14
        if not str(it.get("source", "")).strip():
            fail("I14", it, "no Source")
        # I15, I16
        if (k == "DEC" and st == "Proposed") or (k == "REQ" and st == "Draft"):
            d = parse_date(it.get("raised-on"))
            if d and (today - d).days > 14:
                warn("I15", it, f"{st} for {(today - d).days} days")
        if k == "DEC" and not links_with(it, "addresses") and "accept" not in str(it.get("rationale", "")).lower():
            warn("I16", it, "no addresses link and no 'accepts' in Rationale")
        # I17
        if k == "CR" and st == "Deferred":
            if not str(it.get("phase", "")).strip() or links_with(it, "worked by"):
                fail("I17", it, "Deferred needs a Phase and no open item")
        # I19
        if names is not None:
            for key in ("owner", "approved-by"):
                v = str(it.get(key, "")).strip()
                if not known(v):
                    fail("I19", it, f"{M.LABELS.get(key, key)} {v!r} is not a known stakeholder")
                if key == "owner" and v in mentioned:
                    fail("I19", it, f"Owner {v!r} has role Mentioned")
            for name in re.split(r"[,;]", str(it.get("consulted", "") or "")):
                name = name.strip()
                if not known(name):
                    fail("I19", it, f"Consulted {name!r} is not a known stakeholder")
        # I4 (Due, warning)
        if k == "OI" and st != "Closed" and not str(it.get("due", "")).strip():
            warn("I4", it, "no Due")
        if k == "RSK" and st in ("Identified", "Mitigating") and not str(it.get("due", "")).strip():
            warn("I4", it, "no Due")
    return F, W
