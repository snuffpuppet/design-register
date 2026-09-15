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
    """True unless `eng` is a git working tree with nothing uncommitted."""
    try:
        r = subprocess.run(["git", "-C", eng, "status", "--porcelain"], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return True
    return r.returncode != 0 or bool(r.stdout.strip())
