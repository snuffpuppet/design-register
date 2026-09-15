"""Renumber one register: compact ids in raised-on order. Pure planning here; the server does the writes."""
import datetime
import subprocess
import model as M
from integrity import parse_date


def plan(items, kind):
    """Order the register's items by raised-on then id and assign 1..n. Items already at their new id are left out of the map."""
    ours = [i for i in items.values() if i["kind"] == kind]
    ours.sort(key=lambda i: (parse_date(i.get("raised-on", "")) or datetime.date.max, i["id"]))
    order = [i["id"] for i in ours]
    mapping = {}
    for n, old in enumerate(order, 1):
        new = f"{kind}-{n:04d}"
        if new != old:
            mapping[old] = new
    return {"map": mapping, "order": order}


def dirty(eng):
    """None when `eng` is a git working tree with nothing uncommitted; otherwise a reason string
    saying why renumber cannot run."""
    try:
        r = subprocess.run(["git", "-C", eng, "status", "--porcelain"], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return "The engagement folder is not a git repository the console can see; commit it in its own repository or run renumber from the host."
    if r.returncode != 0:
        return "The engagement folder is not a git repository the console can see; commit it in its own repository or run renumber from the host."
    if r.stdout.strip():
        return "Commit the engagement folder first; renumber needs a clean working tree to roll back to."
    return None
