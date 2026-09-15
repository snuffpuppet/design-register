"""Saved views: a name, a filter, columns, group-by and report sections, kept in <engagement>/views.json.
The summary() text is the email draft the SLT report offers; pure so it can be tested."""
import json, os, re, datetime
import model as M

MONTHS = "January February March April May June July August September October November December".split()


def parse_date(s):
    m = re.match(r"^(\d{1,2}) (\w+) (\d{4})", str(s or ""))
    if not m or m.group(2) not in MONTHS:
        return None
    return datetime.date(int(m.group(3)), MONTHS.index(m.group(2)) + 1, int(m.group(1)))


def blank_filter():
    return {"types": [], "statuses": [], "scopes": [], "owners": [], "rule": "", "since": "", "q": ""}


def default_views():
    return [
        {"name": "SLT weekly", "filter": {**blank_filter()}, "columns": ["id", "title", "status", "owner", "due"], "groupBy": "",
         "sections": ["moved", "raised", "outstanding", "gaps"]},
        {"name": "Vendor owes", "filter": {**blank_filter(), "types": ["CR", "REQ"], "statuses": ["Approved", "Submitted", "Designed", "Delivered"]},
         "columns": ["id", "title", "status", "phase", "vendor-ref"], "groupBy": "type", "sections": ["table"]},
        {"name": "By scope", "filter": blank_filter(), "columns": ["id", "title", "status", "owner"], "groupBy": "scope", "sections": ["table"]},
    ]


def load(path):
    if not os.path.exists(path):
        return default_views()
    try:
        vs = json.load(open(path, encoding="utf-8"))
    except (ValueError, OSError):
        return default_views()
    return vs if isinstance(vs, list) and vs else default_views()


def save(path, vs):
    json.dump(vs, open(path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


def apply_filter(items, filter):
    """The saved view's chip filter, the parts a plain list of item dicts can answer without the browser's
    own state: types, statuses, scopes and owners. `rule` needs integrity failures and `q` free text search,
    both already loaded client-side, so those stay the browser's job; `since` keeps its own role below as the
    section's change window rather than a row filter here."""
    types = filter.get("types") or []
    statuses = filter.get("statuses") or []
    scopes = filter.get("scopes") or []
    owners = filter.get("owners") or []
    out = items
    if types:
        out = [i for i in out if i.get("kind") in types]
    if statuses:
        out = [i for i in out if i.get("status") in statuses]
    if scopes:
        out = [i for i in out if (i.get("scope") or "") in scopes]
    if owners:
        out = [i for i in out if (i.get("owner") or "") in owners]
    return out


def sections(view, items, integrity, today):
    """The four SLT sections as lists of rows. `moved`: items with a History move line on or after `since`.
    `raised`: raised-on on or after since. `outstanding`: DEC Proposed, CR For approval, OI Blocked, anything overdue.
    `gaps`: the integrity failures."""
    items = apply_filter(items, view["filter"])
    since = parse_date(view["filter"].get("since")) or (parse_date(today) - datetime.timedelta(days=7))
    now = parse_date(today)
    moved, raised, outstanding = [], [], []
    for it in items:
        for h in it.get("history", []):
            d = parse_date(h)
            move = next((seg for seg in h.split(" | ") if " → " in seg), None)
            if d and d >= since and move:
                frm, to = move.split(" → ", 1)
                moved.append({"id": it["id"], "title": it["title"], "from": frm, "to": to, "owner": it.get("owner", "")})
        rd = parse_date(it.get("raised-on"))
        if rd and rd >= since:
            raised.append({"id": it["id"], "title": it["title"], "status": it["status"], "owner": it.get("owner", "")})
        due = parse_date(it.get("due"))
        overdue = due is not None and due < now and it["status"] not in M.TERMINAL.get(it["kind"], set())
        if (it["kind"], it["status"]) in (("DEC", "Proposed"), ("CR", "For approval"), ("OI", "Blocked")) or overdue:
            outstanding.append({"id": it["id"], "title": it["title"], "status": it["status"], "due": it.get("due", ""),
                                "overdue": (now - due).days if overdue else 0})
    return {"moved": moved, "raised": raised, "outstanding": outstanding, "gaps": integrity.get("failures", [])}


def summary(view, items, integrity, today):
    s = sections(view, items, integrity, today)
    out = [f"Design register, week to {today}.", ""]
    if s["moved"]:
        out.append(f"{len(s['moved'])} moved. " + " ".join(f"{m['id']} ({m['title']}) {m['from']} to {m['to']}." for m in s["moved"]))
    if s["raised"]:
        out.append(f"{len(s['raised'])} raised: " + ", ".join(f"{r['id']} {r['title']}" for r in s["raised"]) + ".")
    if s["outstanding"]:
        bits = []
        for o in s["outstanding"]:
            b = f"{o['id']} ({o['title']}) {o['status']}"
            if o["overdue"]:
                b += f", overdue {o['overdue']} days"
            elif o["due"]:
                b += f", due {o['due']}"
            bits.append(b)
        out.append("For SLT: " + "; ".join(bits) + ".")
    n = len(s["gaps"])
    out.append(f"Register clean-up: {n} gap{'' if n == 1 else 's'} remain.")
    out += ["", "Full tables on the Confluence Design Register."]
    return "\n".join(out)
