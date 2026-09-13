# Direct Writes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The console writes item files in place by default, keeps change sets as a per-engagement mode, and the push builds from the registers as they stand.

**Architecture:** One `commit()` in `server.py` is the only place a Live write decides between appending a change set block and rewriting an item file. A new `items.py` owns the item file layout (parse and render) so the server and the freeze share it. `push-pages.py` stops requiring `frozen.md`.

**Tech Stack:** Python 3.12 standard library, vanilla JS, unittest run through `make test` in Docker. No host installs.

**Spec:** `docs/superpowers/specs/2026-09-14-direct-writes-design.md`

## Global Constraints

- Everything runs in Docker: `make test`, `make up ENG=test-data/puppy-gloves`. No host python server.
- Australian English, no em dashes, no patterns of three, no "not x but y" framing, in code comments and docs alike.
- Documents carry a version and date near the top and are bumped on change.
- Commits end with the attribution lines the session provides.
- `model.py` is the only place the console learns the model; the model document is bumped when the layout changes.
- Nothing in `../solution-register` is edited.

---

### Task 1: items.py, the item file layout in one place

**Files:**
- Create: `console/items.py`
- Modify: `console/server.py:45-90` (parse_item moves out), `console/baseline.py:626-640` (item_text delegates)
- Test: `console/tests/test_items.py`

**Interfaces:**
- Produces: `items.parse_item(path) -> dict` (same shape server.parse_item returns today, plus `history: list[str]` when the file has a `## History` section), `items.render_item(item: dict) -> str`, `items.item_path(eng, id) -> str`.

- [ ] **Step 1: Write the failing tests**

```python
# console/tests/test_items.py
import unittest, tempfile, os, shutil
import items as IT


class RoundTrip(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_every_field_and_history_survive_a_round_trip(self):
        it = {"id": "CR-0007", "kind": "CR", "title": "Vendor adds bulk port", "status": "Proposed", "owner": "Tom Okafor",
              "chosen-option": "1", "estimate": "$20k", "approved-by": "", "phase": "Day one", "implemented-by": "Vendor", "vendor-ref": "CR2-3",
              "links": ["triggered by LIM-0002", "worked by OI-0009"], "raised-on": "1 September 2026", "closed-on": "", "updated": "14 September 2026",
              "reason": "Ops cannot port in bulk", "options": "1. Vendor adds bulk\n2. Manual", "source": "workshop", "notes": "Baseline import from CRs",
              "history": ["14 September 2026 | Adam Moyes | Proposed → For approval | ready | console session"]}
        p = os.path.join(self.d, "CR-0007.md"); open(p, "w", encoding="utf-8").write(IT.render_item(it))
        back = IT.parse_item(p)
        for k, v in it.items():
            self.assertEqual(back[k], v, k)

    def test_risk_kind_is_written_as_kind_and_read_back(self):
        it = {"id": "RSK-0001", "kind": "RSK", "title": "Slip", "status": "Identified", "risk-kind": "Risk", "owner": "P", "likelihood": "L", "impact": "H", "due": "",
              "links": [], "raised-on": "1 September 2026", "closed-on": "", "updated": "1 September 2026", "trigger": "t", "mitigation": "m", "source": "", "notes": ""}
        text = IT.render_item(it)
        self.assertIn("\nkind: Risk\n", text); self.assertNotIn("risk-kind", text)
        p = os.path.join(self.d, "RSK-0001.md"); open(p, "w", encoding="utf-8").write(text)
        self.assertEqual(IT.parse_item(p)["risk-kind"], "Risk")

    def test_no_history_section_when_empty(self):
        it = {"id": "OI-0001", "kind": "OI", "title": "x", "status": "Open", "owner": "P", "due": "", "links": [], "raised-on": "1 September 2026", "closed-on": "", "updated": "1 September 2026", "next action": "do", "source": "", "notes": ""}
        self.assertNotIn("## History", IT.render_item(it))
        self.assertEqual(IT.parse_item.__doc__ is not None, True)

    def test_item_path(self):
        self.assertEqual(IT.item_path("/e", "LIM-0003"), "/e/limitations/LIM-0003.md")
```

- [ ] **Step 2: Run to verify it fails**

Run: `make test 2>&1 | grep -E "^(ERROR|FAIL|Ran|OK)"`
Expected: ImportError for `items`.

- [ ] **Step 3: Write items.py**

```python
# console/items.py
"""The item file layout of model section 7, read and written in one place.

parse_item reads a file into the dict the console works with: frontmatter keys as they are, long sections
under their lower-cased heading, links as a list, the RSK Kind field as risk-kind, and History as a list of
lines. render_item writes that dict back in the model's order so a read then a write changes nothing.
"""
import os, re
import model as M

LONG_ORDER = ["rationale", "impact", "options", "reason", "trigger", "mitigation", "next action", "description"]


def item_path(eng, id):
    return os.path.join(eng, M.DIRS[id.split("-")[0]], id + ".md")


def parse_item(path):
    """One item file into a dict. Shape: frontmatter keys, long fields by heading, links list, history list, kind from the id."""
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
        item["risk-kind"] = item.pop("kind")
    item["kind"] = item["id"].split("-")[0]
    item["history"] = [re.sub(r"^- ", "", l).strip() for l in str(item.get("history", "")).split("\n") if l.strip()]
    item["pending"] = []
    return item


def render_item(it):
    """The dict back as a file: frontmatter in section 7 order, then the long fields the type has, Source, Notes, History."""
    kind = it["kind"]
    lines = ["---", f"id: {it['id']}", f"title: {it.get('title', '')}", f"status: {it.get('status', '')}"]
    for k in M.SHORT[kind]:
        key = "kind" if k == "risk-kind" else k
        lines.append(f"{key}: {it.get(k, '')}")
    lines += [f"raised-on: {it.get('raised-on', '')}", f"closed-on: {it.get('closed-on', '')}", f"updated: {it.get('updated', '')}", "links:"]
    lines += [f"  - {l}" for l in it.get("links", [])]
    lines += ["---", ""]
    longs = [k for k in LONG_ORDER if k in M.LONG[kind]] + [k for k in M.LONG[kind] if k not in LONG_ORDER]
    for k in dict.fromkeys(longs + ["source", "notes"]):
        lines += [f"## {M.LABELS.get(k, k.capitalize())}", "", str(it.get(k, "") or ""), ""]
    if it.get("history"):
        lines += ["## History", ""] + [f"- {h}" for h in it["history"]] + [""]
    return "\n".join(lines)
```

Check `M.LABELS` has "next action" and "description" labels; if `M.LONG` for a kind lists keys not in `LONG_ORDER` they still render, after the ordered ones.

- [ ] **Step 4: Point server and baseline at it**

In `server.py` delete `parse_item` (lines 45 to 90) and add `from items import parse_item, render_item, item_path` after `import integrity as I`. In `baseline.py`, leave `item_text` as it is for now; Task 4 makes the freeze write through `render_item` if the round trip is exact, otherwise it stays. Run the suite.

- [ ] **Step 5: Run tests to verify they pass**

Run: `make test 2>&1 | grep -E "^(ERROR|FAIL|Ran|OK)"`
Expected: `OK`, 81 tests.

- [ ] **Step 6: Commit**

```bash
git add console/items.py console/server.py console/tests/test_items.py
git commit -m "items.py: the item file layout parsed and rendered in one place"
```

---

### Task 2: The Writes mode, read from engagement.md

**Files:**
- Modify: `console/server.py:108-127` (load_engagement), `console/server.py:245-253` (state)
- Test: `console/tests/test_server_direct.py` (new)

**Interfaces:**
- Produces: `load_engagement()["writes"]` is `"direct"` or `"change-sets"`; `writes_direct() -> bool`.

- [ ] **Step 1: Write the failing tests**

```python
# console/tests/test_server_direct.py
import unittest, tempfile, os, shutil
import server as S


def use(eng):
    S.ENG = eng; S.CS_DIR = os.path.join(eng, "change-sets"); S.DISMISSED_PATH = os.path.join(eng, "supports-dismissed.json")


class Mode(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); self.saved = (S.ENG, S.CS_DIR, S.DISMISSED_PATH); use(self.d)

    def tearDown(self):
        S.ENG, S.CS_DIR, S.DISMISSED_PATH = self.saved; shutil.rmtree(self.d)

    def test_no_line_means_direct(self):
        open(os.path.join(self.d, "engagement.md"), "w").write("# Engagement: x\n\n## Phases\n\n- P1 (current)\n")
        self.assertEqual(S.load_engagement()["writes"], "direct"); self.assertTrue(S.writes_direct())

    def test_no_file_means_direct(self):
        self.assertEqual(S.load_engagement()["writes"], "direct")

    def test_change_sets_line(self):
        open(os.path.join(self.d, "engagement.md"), "w").write("# Engagement: x\n\n- Writes: change-sets\n")
        self.assertEqual(S.load_engagement()["writes"], "change-sets"); self.assertFalse(S.writes_direct())

    def test_unknown_value_is_refused(self):
        open(os.path.join(self.d, "engagement.md"), "w").write("# Engagement: x\n\n- Writes: sideways\n")
        with self.assertRaises(ValueError): S.load_engagement()
```

- [ ] **Step 2: Run to verify it fails**

Run: `make test 2>&1 | grep -E "^(ERROR|FAIL|Ran|OK)"`
Expected: KeyError `writes` and AttributeError `writes_direct`.

- [ ] **Step 3: Implement**

In `load_engagement()` initialise `eng = {"name": ..., "phases": [], "current": "", "writes": "direct"}` and inside the loop, before the phases handling:

```python
            m = re.match(r"- Writes:\s*(\S+)", ln)
            if m:
                if m.group(1) not in ("direct", "change-sets"):
                    raise ValueError(f"engagement.md says Writes: {m.group(1)}; it must be direct or change-sets")
                eng["writes"] = m.group(1)
```

Add after `load_engagement`:

```python
def writes_direct():
    return load_engagement()["writes"] == "direct"
```

`state()` already returns `load_engagement()` under `engagement`, so the page gets `S.engagement.writes` for free.

- [ ] **Step 4: Run tests to verify they pass**

Expected: `OK`, 85 tests.

- [ ] **Step 5: Commit**

```bash
git add console/server.py console/tests/test_server_direct.py
git commit -m "Engagement Writes mode: direct by default, change-sets on request"
```

---

### Task 3: commit(), one write layer with two modes

**Files:**
- Modify: `console/server.py` (append_block callers at 446, 462, 482, 485, 500-546, write_offer at 391-403)
- Test: `console/tests/test_server_direct.py`

**Interfaces:**
- Produces: `H.commit(self, kind, target, fields, links, req, gist, frm=None, based_on=None) -> dict`. In change-sets mode returns `{"changeSet", "item", "ref"}`; in direct mode `{"item": id, "written": path}`. Every existing caller uses `r["item"]` and `r.get("changeSet")`.

- [ ] **Step 1: Write the failing tests** (append to `test_server_direct.py`)

```python
def write_item(eng, id, title, status, **f):
    import items as IT
    kind = id.split("-")[0]
    it = {"id": id, "kind": kind, "title": title, "status": status, "owner": "Priya Nair", "raised-on": "1 September 2026", "closed-on": "",
          "updated": "1 September 2026", "implemented-by": "Vendor", "source": "workshop", "notes": "", "links": [], "history": []}
    it.update(f)
    p = IT.item_path(eng, id); os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(IT.render_item(it))


class Stub:
    for _n in ("evidence", "commit", "transition", "create", "edit", "support_accept", "support_link", "supports_preview", "offer_fields", "write_offer"):
        locals()[_n] = getattr(S.H, _n)


class DirectWrites(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); self.saved = (S.ENG, S.CS_DIR, S.DISMISSED_PATH); use(self.d)
        write_item(self.d, "LIM-0001", "No bulk port", "Change requested", impact="Ops", options="1. Vendor adds bulk; 2. Manual", **{"chosen-option": "1"})
        write_item(self.d, "OI-0001", "Chase it", "Open", **{"next action": "ring"})
        self.h = Stub()

    def tearDown(self):
        S.ENG, S.CS_DIR, S.DISMISSED_PATH = self.saved; shutil.rmtree(self.d)

    def read(self, id):
        import items as IT
        return IT.parse_item(IT.item_path(self.d, id))

    def test_create_assigns_the_next_id_and_writes_the_file(self):
        r = self.h.create({"kind": "OI", "fields": {"Title": "New thing", "Owner": "Priya Nair", "Next action": "start"}, "madeBy": "Adam"})
        self.assertEqual(r["item"], "OI-0002")
        it = self.read("OI-0002")
        self.assertEqual(it["title"], "New thing"); self.assertEqual(it["status"], "Open"); self.assertEqual(it["raised-on"], S.today())
        self.assertEqual(len(it["history"]), 1); self.assertIn("Adam", it["history"][0])
        self.assertFalse(os.path.exists(S.CS_DIR) and os.listdir(S.CS_DIR))

    def test_edit_rewrites_fields_bumps_updated_and_appends_history(self):
        self.h.edit({"id": "OI-0001", "fields": {"Next action": "email instead"}, "links": ["worked by LIM-0001"], "madeBy": "Adam", "evidence": "call"})
        it = self.read("OI-0001")
        self.assertEqual(it["next action"], "email instead"); self.assertEqual(it["updated"], S.today())
        self.assertIn("worked by LIM-0001", it["links"]); self.assertTrue(it["history"][-1].endswith("| fields updated | call"))

    def test_transition_moves_sets_closed_on_and_records_the_move(self):
        self.h.transition({"id": "OI-0001", "to": "Closed", "fields": {}, "links": ["resolves into none: done"], "madeBy": "Adam"})
        it = self.read("OI-0001")
        self.assertEqual(it["status"], "Closed"); self.assertEqual(it["closed-on"], S.today())
        self.assertIn("Open → Closed", it["history"][-1])

    def test_ticked_offer_is_written_first_with_a_real_id_the_move_links(self):
        items = S.overlay(S.load_registers(), S.load_change_sets())
        s = next(x for x in S.integrity_of(items)["suggestions"] if x["rule"] == "S6" and x["id"] == "LIM-0001")
        self.h.transition({"id": "LIM-0001", "to": "Change requested", "fields": {}, "links": [], "madeBy": "Adam",
                           "supports": [{"key": s["key"], "fields": {"Owner": "Tom Okafor"}}]}) if False else None
        # S6 fires in the current state, so accept it from the panel instead
        r = self.h.support_accept({"id": "LIM-0001", "key": s["key"], "fields": {"Owner": "Tom Okafor"}, "madeBy": "Adam"})
        self.assertEqual(r["item"], "CR-0001")
        self.assertIn("dispositioned by CR-0001", self.read("LIM-0001")["links"])
        self.assertIn("triggered by LIM-0001", self.read("CR-0001")["links"])

    def test_support_link_writes_both_files(self):
        write_item(self.d, "CR-0001", "Vendor adds bulk port", "Proposed", reason="Ops")
        items = S.overlay(S.load_registers(), S.load_change_sets())
        s = next(x for x in S.integrity_of(items)["suggestions"] if x["rule"] == "S6" and x["id"] == "LIM-0001")
        self.h.support_link({"id": "LIM-0001", "key": s["key"], "target": "CR-0001", "madeBy": "Adam"})
        self.assertIn("dispositioned by CR-0001", self.read("LIM-0001")["links"])
        self.assertIn("triggered by LIM-0001", self.read("CR-0001")["links"])

    def test_change_sets_mode_still_appends_blocks(self):
        open(os.path.join(self.d, "engagement.md"), "w").write("# Engagement: x\n\n- Writes: change-sets\n")
        r = self.h.edit({"id": "OI-0001", "fields": {"Next action": "email"}, "madeBy": "Adam"})
        self.assertEqual(r["changeSet"], "CS-0001"); self.assertEqual(self.read("OI-0001")["next action"], "ring")
```

Replace the odd `if False` line in the fourth test with nothing: the test accepts the offer from the panel. Keep a move-with-ticked-offer test too:

```python
    def test_move_with_ticked_offer_links_the_real_id(self):
        write_item(self.d, "RSK-0001", "Slip", "Identified", **{"risk-kind": "Risk", "likelihood": "L", "impact": "H", "mitigation": "watch it", "trigger": "t"})
        pv = self.h.supports_preview({"id": "RSK-0001", "to": "Mitigating", "fields": {}, "links": []})["suggestions"]
        s = next(x for x in pv if x["rule"] == "S17")
        self.h.transition({"id": "RSK-0001", "to": "Mitigating", "fields": {}, "links": [], "madeBy": "Adam", "supports": [{"key": s["key"], "fields": {}}]})
        self.assertIn("mitigated by OI-0002", self.read("RSK-0001")["links"])
        self.assertEqual(self.read("OI-0002")["status"], "Open")
```

- [ ] **Step 2: Run to verify it fails**

Expected: AttributeError `commit`, then assertion failures on files not written.

- [ ] **Step 3: Implement commit and route every caller through it**

Add to `H`, above `transition`:

```python
    def commit(self, kind, target, fields, links, req, gist, frm=None, based_on=None):
        """The one place a Live write lands. Change-sets mode appends a block; direct mode writes the item file
        and one History line. Callers build fields by label and links as text, the same in both modes."""
        ev = self.evidence(req)
        if not writes_direct():
            cs = current_change_set(req["madeBy"])
            n = append_block(cs, kind, target, fields, links, ev, gist, frm=frm, based_on=based_on)
            return {"changeSet": cs["id"], "item": n, "ref": f"item {n}"}
        if target == "new":
            n = max([int(os.path.basename(p)[len(kind) + 1:-3]) for p in glob.glob(os.path.join(ENG, M.DIRS[kind], f"{kind}-*.md"))] + [0]) + 1
            it = {"id": f"{kind}-{n:04d}", "kind": kind, "links": [], "history": [], "raised-on": today(), "closed-on": ""}
        else:
            it = parse_item(item_path(ENG, target))
        for k, v in fields.items():
            it[field_key(k)] = v
        for l in links:
            if l not in it["links"]:
                it["links"].append(l)
        it["updated"] = today()
        move = f"{frm} → {it['status']}" if frm is not None else ""
        it["history"].append(" | ".join(x for x in [today(), req["madeBy"].strip(), move, gist, ev[0].split(" | ", 2)[2]] if x))
        p = item_path(ENG, it["id"]); os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w", encoding="utf-8").write(render_item(it))
        return {"item": it["id"], "written": p, "ref": it["id"]}
```

Then in each caller replace the `current_change_set` + `append_block` pair with `self.commit(...)` and use `r["ref"]` where a link needs to name a new item:

- `write_offer`: `return self.commit(kind, "new", fields, links, req, f"{sugg['rule']}: implied by {sugg['id']}")["ref"]` and rename the local to say it returns a ref. `transition` builds `support_links.append(f"{s['link']}{ref}")`. Drop `cs` from its signature and from `support_accept`.
- `transition`: `r = self.commit(kind, it["id"], fields, req.get("links", []) + support_links, req, req.get("gist", "") or f"{frm} to {to}", frm=frm, based_on=it.get("updated", ""))` and return `{"ok": True, "changeSet": r.get("changeSet"), "item": r["item"], "supports": len(support_links)}`.
- `create`: `r = self.commit(kind, "new", fields, f["links"], req, req.get("gist", "") or "raised in console")`; return `{"ok": True, **r}`.
- `edit`: same shape with `frm=None, based_on=it.get("updated", "")`.
- `support_accept`: `ref = self.write_offer(req, s, req.get("fields"))`, then `r = self.commit(it["kind"], it["id"], {}, [f"{s['link']}{ref}"], req, f"{s['rule']}: linked to the implied {s['kind']}", based_on=it.get("updated", ""))`; return `{"ok": True, "changeSet": r.get("changeSet"), "item": ref, "linkBlock": r["item"]}`.
- `support_link`: two `commit` calls, the second only when `s["reverse"]`.

The `self.evidence(req)` calls that ran early "before a change set is opened" stay, since they refuse a missing Made by before anything is written in either mode.

Note on `field_key` for direct mode: `fields` arrive by label ("Next action", "Closed on"); `field_key` maps "Closed on" to `closed-on` and "Next action" to `next-action`. Check `M.LABELS`: if the key is `next action` with a space, `field_key` returns `next action` because it is in `M.LABELS`. Confirm with the edit test.

- [ ] **Step 4: Run tests to verify they pass**

Expected: `OK`. The existing `test_server_supports.py` (change-sets path) must still pass: give its `setUp` an `engagement.md` with `- Writes: change-sets`.

- [ ] **Step 5: Commit**

```bash
git add console/server.py console/tests/test_server_direct.py console/tests/test_server_supports.py
git commit -m "commit(): one write layer; direct mode writes item files with a History line"
```

---

### Task 4: Freeze writes through render_item

**Files:**
- Modify: `console/baseline.py:626-640, 700-716`
- Test: existing `test_baseline_supports.py` freeze tests

- [ ] **Step 1: Add a test** that a frozen file parses back through `items.parse_item` with an empty `history` and the same fields as the record (extend `test_freeze_leaves_no_candidate_id_in_any_item_file`: parse every written file with `items.parse_item` and assert `history == []` and `updated == raised-on`).
- [ ] **Step 2: Run, see it fail** only if `item_text`'s output differs from `render_item`'s; if it already passes, keep the test and go to step 3 anyway.
- [ ] **Step 3: Make `item_text` build an item dict** (`{key: fields[label]}` for each label the type has, `links`, `raised-on`, `closed-on`, `updated = raised-on`, `history: []`) and `return I_.render_item(it)` with `import items as I_`. Delete the hand-rolled lines.
- [ ] **Step 4: Run tests**, expected `OK`.
- [ ] **Step 5: Commit** `"Freeze writes item files through items.render_item"`.

---

### Task 5: Console: mode banner, toasts, History, Close session

**Files:**
- Modify: `console/static/app.js:33-40, 64, 140, 172-180, 218, 346, 357, 374`, `console/static/index.html` (Close session button id `close-session`)

- [ ] **Step 1: Banner.** At line 39, choose the sentence by `S.engagement.writes`: direct gives `This view is the registers <strong>as they stand</strong>: every move, edit or new item writes the item file, and git holds the history.` The change-sets sentence stays as it is.
- [ ] **Step 2: Close session.** After `load()`, `$("#close-session").hidden = S.engagement.writes === "direct"` and hide the "no open change set" label the same way.
- [ ] **Step 3: Change sets nav.** At line 64, render the Changes group only when `S.change_sets.length || S.engagement.writes !== "direct"`.
- [ ] **Step 4: Toasts.** Add `const said = r => r.changeSet ? `${r.changeSet} item ${r.item}` : `${r.item} written`;` near `post()` and use it at lines 218, 346 and 357 and in the transition toast.
- [ ] **Step 5: History in the detail panel.** In `renderDetail` after the long fields: `${i.history?.length ? `<div class="field"><label>History</label><ul class="small muted">${i.history.map(h => `<li>${esc(h)}</li>`).join("")}</ul></div>` : ""}`.
- [ ] **Step 6: Verify in Chrome** on `make up ENG=test-data/puppy-gloves` (its `engagement.md` has no Writes line so it is direct): move OI-0046 to Blocked with a Next action starting "Blocked: ", confirm the file under `test-data/puppy-gloves/open-items/` changed and History shows in the panel; then `git checkout test-data/` to reset.
- [ ] **Step 7: Commit** `"Console: direct mode banner, item toasts, History panel, Close session hidden"`.

---

### Task 6: Push builds from the registers as they stand

**Files:**
- Modify: `console/push-pages.py:69-80, 208-232`, `.claude/skills/push-confluence/SKILL.md`
- Test: `console/tests/test_push_pages.py` (new)

- [ ] **Step 1: Write the failing test**

```python
# console/tests/test_push_pages.py
import unittest, tempfile, os, shutil, json, importlib.util
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("push_pages", os.path.join(HERE, "push-pages.py")); PP = importlib.util.module_from_spec(spec); spec.loader.exec_module(PP)
import items as IT

PAGE = "---\npage-id: 401\npage-title: Requirements\npage-version: 3\npage-url: https://x/401\nparent-page-id: 400\n---\n\n# Requirements\n\n| Ref | Requirement |\n|---|---|\n| R1 | old |\n"


class BuildWithoutFreeze(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); self.eng = os.path.join(self.d, "abb-nokia"); b = os.path.join(self.eng, "baseline"); os.makedirs(b)
        open(os.path.join(b, "Requirements.md"), "w").write(PAGE)
        it = {"id": "REQ-0001", "kind": "REQ", "title": "Email", "status": "Agreed", "moscow": "Must", "phase": "", "owner": "P", "implemented-by": "Vendor",
              "links": [], "raised-on": "1 September 2026", "closed-on": "", "updated": "14 September 2026", "description": "d", "source": "", "notes": "Baseline import from Requirements", "history": []}
        p = IT.item_path(self.eng, "REQ-0001"); os.makedirs(os.path.dirname(p)); open(p, "w").write(IT.render_item(it))
        self.cfg = {"parent_page_url": "https://x/400", "push": {"engagement": "abb-nokia", "mode": "replace-tables"}, "log": [{"action": "pull", "engagement": "abb-nokia"}]}

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_builds_with_as_of_and_no_source_ids(self):
        out = os.path.join(self.eng, "push"); PP.build(self.eng, self.cfg, out)
        m = json.load(open(os.path.join(out, "manifest.json")))
        self.assertIn("as_of", m); self.assertNotIn("frozen", m); self.assertEqual(m["pages"][0]["items"], 1)
        body = json.load(open(os.path.join(out, "401.json")))["body"]
        self.assertIn("REQ-0001", body); self.assertIn("Register as at", body)
```

Check `guard()`'s parent check against `parent-page-id` and `parent_page_url` and shape `PAGE` and `cfg` so it passes; read `guard` before running.

- [ ] **Step 2: Run, expect** `SystemExit` from `id_map`.
- [ ] **Step 3: Implement.** `id_map` returns `({}, "")` when `frozen.md` is missing instead of exiting. In `build`, `manifest["as_of"] = today()` replaces `"frozen": frozen_on`; add `manifest["frozen"]` only when `frozen_on`. The note becomes `f"Register as at {today()} from this page; {len(its)} items in the engagement register" + (f", baselined {frozen_on}" if frozen_on else "") + ...`. The docstring's "after a baseline freeze" and "Input is the frozen engagement" lines change to say the registers as they stand, with `frozen.md` optional.
- [ ] **Step 4: Skill.** In `SKILL.md`: description and title drop "frozen"; step 2 drops "or the baseline is not frozen"; the Never list drops "Push an engagement that is not frozen"; version message becomes `Register as at <date> by <user>`; add to Send after recording `sent_version`: "Write `sent_version` into the pulled page file's `page-version` line under `engagements/<engagement>/baseline/`, so the next build's moved-since check compares against the version the console sent." Bump `usage:` wording.
- [ ] **Step 5: Run tests**, expected `OK`.
- [ ] **Step 6: Commit** `"Push builds from the registers as they stand; frozen.md optional; sent version written back"`.

---

### Task 7: Model 2.26 and the docs

**Files:**
- Modify: `solution-register-model.md` (top note, section 7, section 11), `CLAUDE.md`, `README.md`, `ARCHITECTURE.md`, `console/README.md`, `console/confluence-runbook.md`, `console/static/guide.html`, `console/model.py` docstring version, `handoffs/baseline-abb-nokia.md`, `test-data/puppy-gloves/engagement.md` (Model version line)

- [ ] **Step 1: Model.** Top line to `Version 2.26, 14 September 2026` with a note: "Version 2.26 lets a tool write item files directly. Section 7 adds an optional History section, one line per write, and section 11 says change sets are one of two ways a tool may write, chosen per engagement." Section 7: after the Notes list add `History (optional; one line per write by a tool: date | person | move | gist | evidence)` and change the last sentence to "the item's history is that section together with the file's history in version control." Section 11 first paragraph: "A tool that lets a person run the lifecycle writes item files in one of two ways, chosen per engagement: directly, stamping Updated and appending a History line, or as a change set the ingester applies through the stage below."
- [ ] **Step 2: CLAUDE.md.** Replace the first rule with: "**The console has two write modes, chosen by `- Writes:` in `engagement.md`.** `direct`, the default, rewrites the item file on every move, edit or new item and appends a History line; git holds the history. `change-sets` appends blocks to `<engagement>/change-sets/CS-nnnn.md` for the ingester and never touches item files. Freeze baseline is the same in both: it writes the accepted candidates as the registers' first item files, refuses if any register already has an item, and records the id map in `baseline/frozen.md`. All writes go through `commit()` in `server.py`; do not add a write path beside it." Update the `console/server.py` layout row, the open threads (push from live registers; ingester port now optional), and the model version to 2.26.
- [ ] **Step 3: Other docs.** README, ARCHITECTURE (write table rows for item files and the modes), console README (mode, History, toasts), runbook (push from live registers, sent version written back), guide.html (the "writes item files once" paragraph at line 379). Bump each version line.
- [ ] **Step 4: Handoff.** Add to Decisions taken: "Direct writes are the default (14 September 2026); change sets stay as a per-engagement mode for when the ingester is ported." Add to step 8 that changes are written in place and pushed with `/push-confluence`.
- [ ] **Step 5: Run `make test`**, then `grep -rn "writes item files once\|never again" --include=*.md --include=*.html --include=*.py .` and fix any stragglers.
- [ ] **Step 6: Commit** `"Model 2.26 and docs: direct writes, History section, push from live registers"`.

---

## Self-review

Spec coverage: mode (Task 2), write layer and items.py (Tasks 1, 3), freeze unchanged but sharing the renderer (Task 4), console (Task 5), push and skill (Task 6), model and docs (Task 7), tests in each. Out of scope items untouched. Names used across tasks: `items.parse_item`, `items.render_item`, `items.item_path`, `server.writes_direct`, `H.commit`, `r["item"]`, `r["ref"]`, `r.get("changeSet")`, manifest `as_of`.
