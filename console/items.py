"""The item file layout of model section 7, read and written in one place.

parse_item reads a file into the dict the console works with: frontmatter keys as they are, long sections
under their lower-cased heading, links as a list, the RSK Kind field as risk-kind, and History as a list of
lines. render_item writes that dict back in the model's order, so a read then a write changes nothing.
"""
import os, re
import model as M


def item_path(eng, id):
    return os.path.join(eng, M.DIRS[id.split("-")[0]], id + ".md")


def parse_item(path):
    """One item file into a dict: frontmatter keys, long fields by heading, links and history as lists, kind from the id."""
    text = open(path, encoding="utf-8").read()
    item, lines, i = {}, text.split("\n"), 0
    if lines and lines[0] == "---":
        i = 1; cur_list = None
        while i < len(lines) and lines[i] != "---":
            ln = lines[i]
            if ln.startswith("  - ") and cur_list is not None:
                item[cur_list].append(ln[4:].strip())
            elif re.match(r"^[a-z-]+:", ln):
                k, _, v = ln.partition(":"); v = v.strip()
                if v == "" and i + 1 < len(lines) and lines[i + 1].startswith("  - "):
                    cur_list = k; item[k] = []
                elif v == "":
                    cur_list = None; item[k] = ""
                else:
                    cur_list = None; item[k] = v
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
    item["history"] = [re.sub(r"^- ", "", l).strip() for l in str(item.get("history", "")).split("\n") if l.strip()]
    item["pending"] = []
    return item


def render_item(it):
    """The dict back as a file: frontmatter in section 7 order, Description when the item has one, then the
    type's long fields ending in Source and Notes, then History when there is any."""
    kind = it["kind"]
    lines = ["---", f"id: {it['id']}", f"title: {it.get('title', '')}", f"status: {it.get('status', '')}"]
    for k in M.SHORT[kind]:
        lines.append(f"{'kind' if k == 'risk-kind' else k}: {it.get(k, '')}")
    lines += [f"raised-on: {it.get('raised-on', '')}", f"closed-on: {it.get('closed-on', '')}", f"updated: {it.get('updated', '')}", "links:"]
    lines += [f"  - {l}" for l in it.get("links", [])]
    lines += ["---", ""]
    longs = (["description"] if str(it.get("description", "") or "").strip() else []) + list(M.LONG[kind])
    for k in longs:
        lines += [f"## {M.LABELS.get(k, k.capitalize())}", "", str(it.get(k, "") or ""), ""]
    if it.get("history"):
        lines += ["## History", ""] + [f"- {h}" for h in it["history"]] + [""]
    return "\n".join(lines)
