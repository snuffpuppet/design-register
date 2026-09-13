"""Section 9 and the SUPPORTS table evaluated over a list of item dicts.

check(items) is pure: it reads the dicts and returns failures, warnings, prompts and suggestions.
It never writes. Item dicts are the shape server.parse_item produces (see the plan's file map);
baseline.as_items produces the same shape from candidates.
"""
import hashlib, re
import model as M

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


def check(items, phases=None, stakeholders=None):
    by_id = {it["id"]: it for it in items}
    sugs, prompts = suggestions(items, by_id)
    failures, warnings = rules(items, by_id, phases, stakeholders)
    return {"failures": failures, "warnings": warnings, "prompts": prompts, "suggestions": sugs}


def rules(items, by_id, phases=None, stakeholders=None):
    return [], []
