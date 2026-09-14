# Rationalise in Place Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The freeze writes every candidate that is not rejected, merged or discarded, and the rationalising work (duplicates, merge, delete, missing supports, off-list scopes, mark reviewed) continues over the real item files in a Rationalise view.

**Architecture:** `baseline.py` loses two freeze gates and reports counts instead. `server.py` gains merge, delete and a `delete` target in `commit()`, plus `unreviewed` ids and `dupes` clusters in `/api/state`, and two small rationalise endpoints. `app.js` swaps its stage test to "any item exists", renders Baseline before that and Rationalise after, and gives the drawer Merge into and Delete. Model bumps to 2.28.

**Tech Stack:** Python 3.12 standard library, vanilla JS, `unittest` run through `make test` in Docker. No new dependencies.

**Spec:** `docs/superpowers/specs/2026-09-15-rationalise-in-place-design.md`

## Global Constraints

- Australian English, no em dashes, no rhyming patterns of three, no "not x but y" framing, in code comments and docs alike.
- Every Live write goes through `commit()` in `server.py`. Merge and Delete are callers of it.
- Merge and Delete refuse in change-sets mode with a message saying the ingester has no block for them.
- Item files stay exactly section 7. No new frontmatter key. "Unreviewed" is derived from `baseline/verdicts.json`.
- Tests run with `make test` (Docker). Never start a host python server.
- Commits end with the attribution lines the session provides.
- Documents carry a version and date near the top and are bumped on change.

---

## File map

| File | Responsibility in this plan |
|---|---|
| `solution-register-model.md` | 2.28 note, section 7 sentence, section 11 paragraph. |
| `console/baseline.py` | `assemble()` and `as_items()` treat an undecided candidate as written; `freeze()` drops two gates, returns and writes four counts; `frozen()` reads them; `clusters()` works over items; `mark_reviewed()`. |
| `console/server.py` | `commit()` `delete` target; `merge()`, `delete()`; `load_dup_dismissed()`, `dismiss_dup()`; `unreviewed_ids()`; `state()` adds `unreviewed` and `dupes`; routes. |
| `console/static/app.js` | `stage()`, nav, `rationaliseView()` and `wireRationalise()`, drawer Merge into and Delete, freeze toast. |
| `console/tests/test_baseline_supports.py` | Freeze tests rewritten for the new behaviour. |
| `console/tests/test_rationalise.py` | New: merge, delete, unreviewed, dupes over items, mark reviewed. |
| `console/README.md`, `console/confluence-runbook.md`, `console/static/guide.html`, `CLAUDE.md` | Stage boundary and the Rationalise view. |

---

### Task 1: Model 2.28

**Files:**
- Modify: `solution-register-model.md:1-5` (header and version notes), section 7 (around line 196), section 11 Imports paragraph (around line 297)

- [ ] **Step 1: Bump the header and add the note**

Change line 3 to `Version 2.28, 15 September 2026. Owner: Adam Moyes.` and insert after it, before the 2.27 note:

```markdown
Version 2.28 lets an import be written into the registers before its review is complete and rationalised in place. Section 11 says a row that was neither rejected nor folded becomes an item and the review continues over the items, with the tool keeping its own record of what is still unreviewed. Section 7 says what a merge or a delete leaves behind in History and in version control. Nothing in sections 4, 5 or 9 changes.
```

- [ ] **Step 2: Section 7 sentence**

In section 7, after the sentence ending `...together with the file's history in version control.`, add:

```markdown
When a tool merges one item into another or deletes one, the surviving item's History line says what was folded in or removed, every item whose Links named the removed id has that link rewritten or dropped with a History line of its own, and version control holds the removed file.
```

- [ ] **Step 3: Section 11 Imports paragraph**

After the paragraph beginning `**Imports.**`, add:

```markdown
An import may be written into the registers before its review is complete. Every row that was neither rejected nor folded into another becomes an item, in the mapped status where the source's status is one of the type's own states and otherwise in the first state, and the review continues over the items: duplicates are merged, rows that were never register items are deleted, and the records the states imply are created or linked. A tool that does this keeps its own record of which items are still unreviewed and shows it; the record is the tool's, never a field on the item.
```

- [ ] **Step 4: Commit**

```bash
git add solution-register-model.md
git commit -m "Model 2.28: an import may be rationalised in place after the freeze"
```

---

### Task 2: The freeze writes undecided candidates and reports counts

**Files:**
- Modify: `console/baseline.py` (`as_items` ~442, `assemble` ~552, `frozen` ~615, `freeze` ~655)
- Test: `console/tests/test_baseline_supports.py`

**Interfaces:**
- Produces: `freeze(...)` returns `{"ok", "written", "rejected", "counts", "unreviewed", "supportsFail", "supportsWarn", "offScope"}`. `frozen(bdir)` returns those four keys too (0 when the line is absent). `WRITTEN = ("Accept", "")` module constant naming the verdicts that reach the registers.

- [ ] **Step 1: Write the failing tests**

Replace `test_freeze_refuses_with_undecided_failures_and_remaps_links` in `console/tests/test_baseline_supports.py` with:

```python
    def test_freeze_writes_with_undecided_failures_and_reports_them(self):
        eng = os.path.join(self.d, "eng"); os.makedirs(eng)
        fails = [x for x in B.suggestions(B.load_candidates(self.b), B.load_verdicts(self.b))["suggestions"] if x["level"] == "fail"]
        self.assertTrue(fails)
        r = B.freeze(eng, self.b, B.load_candidates(self.b), B.load_verdicts(self.b), "13 September 2026", "Adam")
        self.assertTrue(r["ok"])
        self.assertEqual(r["supportsFail"], len(fails))
        self.assertEqual(r["unreviewed"], 0)
        lim = open(os.path.join(eng, "limitations", "LIM-0001.md")).read()
        self.assertIn("constrains REQ-0001", lim)
        self.assertNotIn("constrains c", lim)
        fz = B.frozen(self.b)
        self.assertEqual(fz["supportsFail"], len(fails))
        self.assertIn("- Unreviewed: 0", open(os.path.join(self.b, "frozen.md")).read())

    def test_freeze_writes_undecided_candidates_and_counts_them(self):
        eng = os.path.join(self.d, "eng"); os.makedirs(eng)
        B.apply_verdict(self.b, [self.cands[0]["id"]], "")
        r = B.freeze(eng, self.b, B.load_candidates(self.b), B.load_verdicts(self.b), "13 September 2026", "Adam")
        self.assertEqual(r["unreviewed"], 1)
        self.assertEqual(r["written"], 3)
        v = B.load_verdicts(self.b)
        self.assertTrue(v[self.cands[0]["id"]]["frozenAs"].startswith("LIM-"))
        self.assertEqual(v[self.cands[0]["id"]].get("verdict", ""), "")

    def test_freeze_skips_reject_merge_and_discard(self):
        eng = os.path.join(self.d, "eng"); os.makedirs(eng)
        ids = [c["id"] for c in self.cands]
        B.apply_verdict(self.b, [ids[0]], "Discard")
        B.apply_verdict(self.b, [ids[1]], "Reject", reason="duplicate")
        r = B.freeze(eng, self.b, B.load_candidates(self.b), B.load_verdicts(self.b), "13 September 2026", "Adam")
        self.assertEqual(r["written"], 1)
        self.assertEqual(r["rejected"], 1)
```

In `ScopeFreeze`, replace the two refusal tests with:

```python
    def test_freeze_reports_a_blank_scope_when_scopes_declared(self):
        r = self.run_freeze("", ["Access"])
        self.assertTrue(r["ok"]); self.assertEqual(r["offScope"], 3)

    def test_freeze_reports_an_off_list_scope(self):
        r = self.run_freeze("Nonsense", ["Access"])
        self.assertTrue(r["ok"]); self.assertEqual(r["offScope"], 3)
```

and add to `test_freeze_accepts_a_listed_scope`: `self.assertEqual(self.run_freeze("Access", ["Access"])["offScope"], 0)` in place of the existing assertion, keeping `["ok"]` checked too.

- [ ] **Step 2: Run to verify they fail**

Run: `make test 2>&1 | grep -E "FAIL|ERROR|Ran"`
Expected: the new tests fail with `ValueError` from the freeze refusal or `KeyError: 'supportsFail'`.

- [ ] **Step 3: Implement in `baseline.py`**

Near `IMPLIED_KEY` add:

```python
WRITTEN = ("Accept", "")   # the verdicts that reach the registers at the freeze: accepted, and not yet decided
```

In `as_items()`, change `if c["verdict"] != "Accept": continue` to `if c["verdict"] not in WRITTEN: continue`.

In `assemble()`, change `if c["verdict"] != "Accept": continue` to `if c["verdict"] not in WRITTEN: continue`, and add `"unreviewed": c["verdict"] == ""` to the record dict.

In `freeze()`, delete the `pending = ...` block and its `raise`, and the `if scopes:` block that raises. After `records, rejects = assemble(...)` and the `if not records` check, keep going. After the write loop and before `save_verdicts`, compute:

```python
    sugg = suggestions(cands, v)["suggestions"]
    n_fail = sum(1 for s in sugg if s["level"] == "fail")
    n_warn = sum(1 for s in sugg if s["level"] == "warn")
    n_unrev = sum(1 for r in out if r.get("unreviewed"))
    n_scope = sum(1 for r in out if str(r.get("scope", "")).strip() not in scopes) if scopes else 0
```

In the `frozen.md` write, after the `- Rejected:` line add:

```python
                f"- Unreviewed: {n_unrev}\n- Supports missing: {n_fail} needed, {n_warn} suggested\n- Off-list scopes: {n_scope}\n\n"
```

(replacing the `\n\n` that followed `- Rejected`). Change the sentence `Every change since is a change set.` to `Every change since is a write to an item file, held in version control.`

Return `{"ok": True, "written": len(out), "rejected": len(rejects), "counts": counter, "unreviewed": n_unrev, "supportsFail": n_fail, "supportsWarn": n_warn, "offScope": n_scope}`.

In `frozen()`, initialise `out` with `"unreviewed": 0, "supportsFail": 0, "supportsWarn": 0, "offScope": 0` and add:

```python
        m = re.match(r"- Unreviewed: (\d+)", ln)
        if m: out["unreviewed"] = int(m.group(1))
        m = re.match(r"- Supports missing: (\d+) needed, (\d+) suggested", ln)
        if m: out["supportsFail"], out["supportsWarn"] = int(m.group(1)), int(m.group(2))
        m = re.match(r"- Off-list scopes: (\d+)", ln)
        if m: out["offScope"] = int(m.group(1))
```

Update the module docstring line 2 and the `freeze()` docstring: the freeze writes every candidate not rejected, merged or discarded, and reports what is left to rationalise.

- [ ] **Step 4: Run the suite**

Run: `make test 2>&1 | tail -5`
Expected: `OK`. If `test_freeze_lists_implied` or the `LinkExisting` freeze test now count differently because undecided rows are written, read the assertion and adjust the count only if the new behaviour explains it.

- [ ] **Step 5: Commit**

```bash
git add console/baseline.py console/tests/test_baseline_supports.py
git commit -m "Freeze writes undecided candidates and reports unreviewed, supports and scope counts"
```

---

### Task 3: Duplicates over items, dismissed beside the register

**Files:**
- Modify: `console/baseline.py:302-320` (`clusters`)
- Modify: `console/server.py` (`load_dismissed` area ~239, `state()` ~227, routes ~296)
- Create: `console/tests/test_rationalise.py`

**Interfaces:**
- Produces: `B.clusters(rows, dismissed)` accepts item dicts (no `ref` key) as well as candidates. `server.DUP_PATH`, `server.load_dup_dismissed() -> dict`, `server.dismiss_dup(ids, undo=False)`. `state()["dupes"]` is a list of id lists.

- [ ] **Step 1: Write the failing tests**

Create `console/tests/test_rationalise.py`:

```python
import unittest, tempfile, os, json, shutil
import server as S
import items as IT
import baseline as B
from tests.test_server_direct import write_item, Stub


def use(eng):
    S.ENG = eng; S.CS_DIR = os.path.join(eng, "change-sets"); S.B_DIR = os.path.join(eng, "baseline")
    S.DISMISSED_PATH = os.path.join(eng, "supports-dismissed.json"); S.DUP_PATH = os.path.join(eng, "duplicates-dismissed.json")


class Base(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); self.saved = (S.ENG, S.CS_DIR, S.B_DIR, S.DISMISSED_PATH, S.DUP_PATH); use(self.d)
        self.h = Stub()

    def tearDown(self):
        S.ENG, S.CS_DIR, S.B_DIR, S.DISMISSED_PATH, S.DUP_PATH = self.saved; shutil.rmtree(self.d)

    def read(self, id):
        return IT.parse_item(IT.item_path(self.d, id))

    def req(self, **k):
        return {"madeBy": "Adam", "evidence": "", **k}


class Dupes(Base):
    def test_clusters_over_items_find_overlapping_titles(self):
        write_item(self.d, "REQ-0001", "Bulk number porting for operations", "Draft")
        write_item(self.d, "REQ-0002", "Operations bulk porting of numbers", "Draft")
        write_item(self.d, "REQ-0003", "Email alerts", "Draft")
        groups = S.state()["dupes"]
        self.assertEqual(groups, [["REQ-0001", "REQ-0002"]])

    def test_dismissed_group_stays_out(self):
        write_item(self.d, "REQ-0001", "Bulk number porting for operations", "Draft")
        write_item(self.d, "REQ-0002", "Operations bulk porting of numbers", "Draft")
        S.dismiss_dup(["REQ-0002", "REQ-0001"])
        self.assertEqual(S.state()["dupes"], [])
        self.assertTrue(os.path.exists(S.DUP_PATH))
        S.dismiss_dup(["REQ-0001", "REQ-0002"], undo=True)
        self.assertEqual(len(S.state()["dupes"]), 1)
```

Note `Stub` in `test_server_direct.py` lists the handler methods it copies; Task 4 adds `merge` and `delete` to that list.

- [ ] **Step 2: Run to verify they fail**

Run: `make test 2>&1 | grep -E "FAIL|ERROR|Ran"`
Expected: `AttributeError` on `S.DUP_PATH` or `KeyError: 'dupes'`.

- [ ] **Step 3: Implement**

`baseline.py` `clusters()`: change `same_ref = a["ref"] and a["ref"] == b["ref"]` to `same_ref = a.get("ref") and a.get("ref") == b.get("ref")`. Docstring: add "Works over candidates and over items; an item has no ref."

`server.py`: after `DISMISSED_PATH` add `DUP_PATH = os.path.join(ENG, "duplicates-dismissed.json")`. After `load_dismissed()` add:

```python
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
```

In `state()`, add to the returned dict: `"dupes": B.clusters([i for i in items.values() if not i.get("provisional")], set(load_dup_dismissed()))`.

Route in `do_POST`, beside `/api/baseline/not-duplicates`:

```python
                if p == "/api/rationalise/not-duplicates":
                    dismiss_dup(req["ids"], req.get("undo", False))
                    return self.send_json({"ok": True})
```

- [ ] **Step 4: Run the suite**

Run: `make test 2>&1 | tail -3`
Expected: `OK`.

- [ ] **Step 5: Commit**

```bash
git add console/baseline.py console/server.py console/tests/test_rationalise.py
git commit -m "Duplicate groups over the live items, set aside in duplicates-dismissed.json"
```

---

### Task 4: Merge and Delete through `commit()`

**Files:**
- Modify: `console/server.py` (`commit` ~375, routes ~296, new methods after `edit` ~551)
- Modify: `console/tests/test_server_direct.py:20` (`Stub` list)
- Test: `console/tests/test_rationalise.py`

**Interfaces:**
- Produces: `H.merge(req) -> {"ok", "survivor", "removed": [ids], "touched": [ids]}` with `req = {survivor, losers, madeBy, evidence}`. `H.delete(req) -> {"ok", "removed", "touched"}` with `req = {id, reason, madeBy, evidence}`. `commit(kind, target_id, {}, [], req, gist, delete=True)` removes the file and returns `{"item": id, "removed": path, "ref": id}`. `H.rewrite_links(items, old, new_or_None, gist, req) -> [ids touched]`.

- [ ] **Step 1: Add `merge` and `delete` to `Stub`**

In `console/tests/test_server_direct.py` line 20, add `"merge", "delete"` to the tuple.

- [ ] **Step 2: Write the failing tests**

Append to `console/tests/test_rationalise.py`:

```python
class Merge(Base):
    def setUp(self):
        super().setUp()
        write_item(self.d, "REQ-0001", "Bulk porting", "Draft", source="page A", notes="", moscow="", links=["constrained by LIM-0001"])
        write_item(self.d, "REQ-0002", "Bulk number porting", "Agreed", source="page B", notes="from the vendor", moscow="Must", links=["constrained by LIM-0001"])
        write_item(self.d, "LIM-0001", "No bulk port", "Identified", links=["constrains REQ-0002", "constrains REQ-0001"])
        write_item(self.d, "DEC-0001", "Manual port", "Proposed", links=["dispositions LIM-0001", "affects REQ-0002"])

    def test_merge_folds_rewrites_and_removes(self):
        r = self.h.merge(self.req(survivor="REQ-0001", losers=["REQ-0002"]))
        self.assertEqual(r["removed"], ["REQ-0002"])
        self.assertFalse(os.path.exists(IT.item_path(self.d, "REQ-0002")))
        s = self.read("REQ-0001")
        self.assertEqual(s["status"], "Draft")            # never taken from the loser
        self.assertEqual(s["moscow"], "Must")             # blank on the survivor, filled from the loser
        self.assertIn("page B", s["source"]); self.assertIn("page A", s["source"])
        self.assertIn("Merged in from REQ-0002: from the vendor", s["notes"])
        self.assertEqual(s["links"], ["constrained by LIM-0001"])
        self.assertTrue(any("merged REQ-0002 into this item" in h for h in s["history"]))
        lim = self.read("LIM-0001")
        self.assertEqual(lim["links"], ["constrains REQ-0001"])
        self.assertTrue(any("merged REQ-0002 into REQ-0001" in h for h in lim["history"]))
        dec = self.read("DEC-0001")
        self.assertIn("affects REQ-0001", dec["links"]); self.assertNotIn("affects REQ-0002", dec["links"])
        self.assertIn("DEC-0001", r["touched"]); self.assertIn("LIM-0001", r["touched"])

    def test_merge_refuses_across_types_and_writes_nothing(self):
        with self.assertRaises(ValueError):
            self.h.merge(self.req(survivor="REQ-0001", losers=["LIM-0001"]))
        self.assertTrue(os.path.exists(IT.item_path(self.d, "LIM-0001")))
        self.assertEqual(self.read("REQ-0001")["history"], [])

    def test_merge_refuses_in_change_sets_mode(self):
        open(os.path.join(self.d, "engagement.md"), "w").write("# Engagement: x\n\n- Writes: change-sets\n")
        with self.assertRaises(ValueError) as e:
            self.h.merge(self.req(survivor="REQ-0001", losers=["REQ-0002"]))
        self.assertIn("change set", str(e.exception).lower())
        self.assertTrue(os.path.exists(IT.item_path(self.d, "REQ-0002")))


class Delete(Base):
    def setUp(self):
        super().setUp()
        write_item(self.d, "REQ-0002", "Bulk number porting", "Agreed")
        write_item(self.d, "LIM-0001", "No bulk port", "Identified", links=["constrains REQ-0002"])

    def test_delete_drops_links_and_removes_file(self):
        r = self.h.delete(self.req(id="REQ-0002", reason="not a requirement"))
        self.assertFalse(os.path.exists(IT.item_path(self.d, "REQ-0002")))
        lim = self.read("LIM-0001")
        self.assertEqual(lim["links"], [])
        self.assertTrue(any("dropped link to REQ-0002, deleted: not a requirement" in h for h in lim["history"]))
        self.assertEqual(r["touched"], ["LIM-0001"])

    def test_delete_needs_a_reason(self):
        with self.assertRaises(ValueError):
            self.h.delete(self.req(id="REQ-0002", reason=""))
        self.assertTrue(os.path.exists(IT.item_path(self.d, "REQ-0002")))

    def test_delete_refuses_in_change_sets_mode(self):
        open(os.path.join(self.d, "engagement.md"), "w").write("# Engagement: x\n\n- Writes: change-sets\n")
        with self.assertRaises(ValueError):
            self.h.delete(self.req(id="REQ-0002", reason="x"))
```

- [ ] **Step 3: Run to verify they fail**

Run: `make test 2>&1 | grep -E "FAIL|ERROR|Ran"`
Expected: `TypeError: 'NoneType' object is not callable` (Stub copied `None`) or `AttributeError`.

- [ ] **Step 4: Implement `commit()` delete and the two methods**

`commit()` signature becomes `def commit(self, kind, target, fields, links, req, gist, frm=None, based_on=None, delete=False):`. Docstring gains: "`delete=True` removes the target's file instead of writing it; direct mode only, the caller has already refused otherwise." After `ev = self.evidence(req)` and the change-sets branch, add:

```python
        if delete:
            p = item_path(ENG, target)
            if not os.path.exists(p):
                raise ValueError(f"No file for {target}.")
            os.remove(p)
            return {"item": target, "removed": p, "ref": target}
```

Also make an empty `fields` with no links a legal write when a gist is given (it already is: the loop just runs zero times). Confirm by reading the function; no change needed.

Add after `edit()`:

```python
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
                    kept.append(l); continue
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
```

Note `fields["Notes"] = notes or ""`: `commit()` writes every field it is given, so an empty Notes string is written as empty, which is what the survivor already had. Where the survivor's Notes and the loser's are both blank the key is still set and harmless.

Routes in `do_POST`, after `/api/edit`:

```python
                if p == "/api/merge":
                    return self.send_json(self.merge(req))
                if p == "/api/delete":
                    return self.send_json(self.delete(req))
```

- [ ] **Step 5: Run the suite**

Run: `make test 2>&1 | tail -3`
Expected: `OK`. If `test_merge_folds_rewrites_and_removes` fails on `s["links"]`, check that the loser's `constrained by LIM-0001` was excluded as already held.

- [ ] **Step 6: Commit**

```bash
git add console/server.py console/tests/test_server_direct.py console/tests/test_rationalise.py
git commit -m "Merge and Delete: direct-mode writes through commit() that fold, rewrite links and remove the file"
```

---

### Task 5: Unreviewed ids and Mark reviewed

**Files:**
- Modify: `console/baseline.py` (near `mark_exported`, end of file)
- Modify: `console/server.py` (`state()`, routes)
- Test: `console/tests/test_rationalise.py`

**Interfaces:**
- Produces: `B.unreviewed_ids(bdir) -> set` of item ids frozen from a candidate with no verdict. `B.mark_reviewed(bdir, item_id) -> bool`. `state()["unreviewed"]` sorted list. Route `/api/rationalise/reviewed {id}`.

- [ ] **Step 1: Write the failing tests**

Append to `console/tests/test_rationalise.py`:

```python
class Unreviewed(Base):
    def setUp(self):
        super().setUp()
        os.makedirs(S.B_DIR)
        json.dump({"c1": {"frozenAs": "REQ-0001"}, "c2": {"frozenAs": "REQ-0002", "verdict": "Accept"},
                   "c3": {"frozenAs": "REQ-0002", "verdict": "Merge", "mergedInto": "c2"}},
                  open(os.path.join(S.B_DIR, "verdicts.json"), "w"))
        write_item(self.d, "REQ-0001", "One", "Draft"); write_item(self.d, "REQ-0002", "Two", "Draft"); write_item(self.d, "REQ-0003", "Raised here", "Draft")

    def test_unreviewed_is_the_frozen_from_candidate_with_no_verdict(self):
        self.assertEqual(S.state()["unreviewed"], ["REQ-0001"])

    def test_mark_reviewed_sets_accept(self):
        self.assertTrue(B.mark_reviewed(S.B_DIR, "REQ-0001"))
        self.assertEqual(S.state()["unreviewed"], [])
        self.assertEqual(B.load_verdicts(S.B_DIR)["c1"]["verdict"], "Accept")

    def test_mark_reviewed_on_a_console_item_is_a_no_op(self):
        self.assertFalse(B.mark_reviewed(S.B_DIR, "REQ-0003"))

    def test_no_baseline_folder_means_nothing_unreviewed(self):
        shutil.rmtree(S.B_DIR)
        self.assertEqual(S.state()["unreviewed"], [])
```

- [ ] **Step 2: Run to verify they fail**

Run: `make test 2>&1 | grep -E "FAIL|ERROR|Ran"`
Expected: `KeyError: 'unreviewed'`.

- [ ] **Step 3: Implement**

`baseline.py`, after `mark_exported`:

```python
def unreviewed_ids(bdir):
    """Items frozen from a candidate that still has no verdict. The review ledger is the verdicts file;
    nothing in an item file says whether it was reviewed."""
    if not os.path.isdir(bdir):
        return set()
    v = load_verdicts(bdir)
    return {e["frozenAs"] for k, e in v.items() if not k.startswith("_") and isinstance(e, dict)
            and e.get("frozenAs") and not e.get("verdict")}


def mark_reviewed(bdir, item_id):
    """Accept every candidate frozen as this item. Returns False when none was."""
    v = load_verdicts(bdir)
    hit = False
    for k, e in v.items():
        if not k.startswith("_") and isinstance(e, dict) and e.get("frozenAs") == item_id and not e.get("verdict"):
            e["verdict"] = "Accept"; hit = True
    if hit:
        save_verdicts(bdir, v)
    return hit
```

`server.py` `state()`: add `"unreviewed": sorted(B.unreviewed_ids(B_DIR) & set(items))`.

Route beside the not-duplicates one:

```python
                if p == "/api/rationalise/reviewed":
                    if not B.mark_reviewed(B_DIR, req["id"]):
                        raise ValueError("That item was not frozen from a candidate; nothing to mark.")
                    return self.send_json({"ok": True})
```

- [ ] **Step 4: Run the suite**

Run: `make test 2>&1 | tail -3`
Expected: `OK`.

- [ ] **Step 5: Commit**

```bash
git add console/baseline.py console/server.py console/tests/test_rationalise.py
git commit -m "Unreviewed items derived from the baseline ledger, with Mark reviewed"
```

---

### Task 6: Stage, nav and the Rationalise view

**Files:**
- Modify: `console/static/app.js` (`stage` 27, `loadOnce` 35-44, `render` nav 62-72 and dispatch 80, baseline section 590-806)

No automated coverage exists for `app.js`; the check is the browser pass in Task 8. Keep each function small and each edit exact.

- [ ] **Step 1: Stage and banner**

Replace line 27:

```js
/* Baselining until any register holds an item; live from then on, whether or not a freeze has run. */
function stage() { return S.baseline?.present && !S.items.length ? "baseline" : "live"; }
```

In `loadOnce`, the `#stage` text stays. Change the Live banner for direct mode to:

```js
    : "This view is the registers <strong>as they stand</strong>: every move, edit, merge or delete writes the item files, and git holds the history."
```

- [ ] **Step 2: Nav**

Replace the Source group line in `render()`:

```js
    B?.present ? group("Source", [st === "baseline"
      ? link("baseline", "Baseline", B.candidates.filter(c => !c.verdict).length, "--c:var(--cs)")
      : link("rationalise", "Rationalise", S.unreviewed.length, "--c:var(--cs)")]) : "",
```

Add to the dispatch chain after the `baseline` line:

```js
  else if (view === "rationalise") { m.innerHTML = rationaliseView(); wireRationalise(m); }
```

Keep the `dim` line; it only fires in the baseline stage.

- [ ] **Step 3: Baseline view text**

In `baselineView()`:
- Freeze confirm text: `Writes ${cs.filter(c => ["Accept", ""].includes(c.verdict)).length} items into the registers, undecided rows included, and opens them for work.`
- Freeze button title: `Write every candidate not rejected, merged or discarded as the registers' first items. Runs once, only into empty registers.`
- Help step 4: replace `The freeze waits until this list is empty of failures.` with `What is still missing at the freeze is carried into the Rationalise view.`
- Help step 6: `<b>Freeze</b> when you want the registers open. Anything undecided is written and stays flagged as unreviewed.`
- Supports tab summary text `${fails.length} needed before the freeze` becomes `${fails.length} needed`.
- The freeze toast in `wireBaseline`: 

```js
toast(`Frozen: ${r.written} items written, ${r.rejected} rejected, ${r.unreviewed} unreviewed, ${r.supportsFail} supports needed, ${r.offScope} off-list scopes`); BF.tab = "dups"; view = "rationalise"; await load();
```

- [ ] **Step 4: The Rationalise view**

Add after `wireBaseline` (end of the baseline section):

```js
/* ---------- rationalise: the same work as the baseline tabs, over the item files ---------- */
let RF = {tab: "dups", kind: "REQ", pos: 0, onlyUnrev: true, merge: null};
function rationaliseView() {
  const scopes = S.engagement.scopes || [], unrev = new Set(S.unreviewed);
  const fails = (S.integrity?.suggestions || []).filter(s => s.level === "fail"), warns = (S.integrity?.suggestions || []).filter(s => s.level === "warn");
  const offScope = scopes.length ? S.items.filter(i => !scopes.includes(i.scope || "")) : [];
  const fz = S.baseline.frozen;
  return `<div class="toolbar"><div><h2>Rationalise</h2><div class="small muted">${fz ? `Frozen ${esc(fz.on)} by ${esc(fz.by)} · ` : ""}${S.items.length} items · <b>${unrev.size} unreviewed</b> · ${S.dupes.length} duplicate group(s) · ${fails.length} support(s) needed${scopes.length ? ` · ${offScope.length} off-list scope(s)` : ""}</div></div></div>
    <div class="tabs"><button data-rtab="dups" class="${RF.tab === "dups" ? "on" : ""}">Duplicates <span class="n">${S.dupes.length}</span></button><button data-rtab="rows" class="${RF.tab === "rows" ? "on" : ""}">Row by row <span class="n">${unrev.size}</span></button><button data-rtab="supports" class="${RF.tab === "supports" ? "on" : ""}">Missing supports <span class="n">${fails.length}</span></button>${scopes.length ? `<button data-rtab="scopes" class="${RF.tab === "scopes" ? "on" : ""}">Scopes <span class="n">${offScope.length}</span></button>` : ""}</div>
    ${RF.tab === "dups" ? rDupes(unrev) : RF.tab === "rows" ? rRows(unrev) : RF.tab === "supports" ? rSupports(fails, warns) : rScopes(offScope, scopes)}`;
}
function rDupes(unrev) {
  if (!S.dupes.length) return `<p class="muted">No duplicate groups left to decide.</p>`;
  return `<div class="section"><p class="small muted">Groups whose titles overlap. Tick the items that are the same, then choose which one leads; the rest fold into it and their files are removed.</p>
    ${S.dupes.slice(0, 25).map(g => `<div class="cs"><div class="small muted"><button class="ghost" data-rnotdup="${g.join(",")}">Not duplicates</button></div>
      ${g.map(id => { const i = S.byId[id]; if (!i) return ""; return `<div class="blk"><label class="dup"><input type="checkbox" data-rdup="${id}" checked> same</label> <button class="ghost" data-rlead="${id}">This one leads</button> ${idTag(i)} ${esc(i.title)} <span class="small muted">${esc(i.status)}${unrev.has(id) ? " · unreviewed" : ""}</span></div>`; }).join("")}</div>`).join("")}</div>`;
}
function rRows(unrev) {
  const q = S.items.filter(i => i.kind === RF.kind && (!RF.onlyUnrev || unrev.has(i.id)));
  const bar = `<div class="toolbar bl-filters"><select id="rf-kind">${KINDS.map(k => `<option value="${k}" ${RF.kind === k ? "selected" : ""}>${S.model.names[k]}s</option>`).join("")}</select>
    <label class="small"><input type="checkbox" id="rf-unrev" ${RF.onlyUnrev ? "checked" : ""}> unreviewed only</label><span class="small muted">${q.length} to walk</span></div>`;
  if (!q.length) return bar + `<p class="muted">Nothing here.</p>`;
  RF.pos = Math.min(RF.pos, q.length - 1);
  const i = q[RF.pos], same = S.items.filter(x => x.kind === i.kind && x.id !== i.id);
  const near = S.dupes.find(g => g.includes(i.id))?.filter(id => id !== i.id).map(id => S.byId[id]).filter(Boolean) || [];
  return bar + `<div class="progress"><div style="width:${Math.round(100 * RF.pos / q.length)}%"></div></div>
    <div class="triage"><div class="tq-main">${itemPanel(i, false)}
      <div class="moves" style="--c:var(--cs)">
        <button data-rv="reviewed" title="a">Mark reviewed <kbd>a</kbd></button>
        <select id="rf-merge"><option value="">merge into…</option>${same.map(x => `<option value="${x.id}">${x.id} ${esc(x.title.slice(0, 50))}</option>`).join("")}</select><button data-rv="merge" title="m">Merge <kbd>m</kbd></button>
        <input id="rf-reason" placeholder="reason to delete" style="width:200px"><button class="ghost" data-rv="delete" title="d">Delete <kbd>d</kbd></button>
        <span class="sep"></span><button class="ghost" data-rv="prev" title="k">← <kbd>k</kbd></button><button class="ghost" data-rv="next" title="j">Skip <kbd>j</kbd> →</button></div>
      <span class="small muted">${RF.pos + 1} of ${q.length}</span></div>
      <div class="tq-side"><h3>Looks like</h3>${near.map(n => `<div class="ctx">${idTag(n)}<div>${esc(n.title)}</div></div>`).join("") || '<p class="small muted">No suggested duplicate.</p>'}</div></div>`;
}
function rSupports(fails, warns) {
  const one = s => { const t = S.byId[s.id]; return `<div class="cs blk-support"><div class="small muted"><b>${esc(s.rule)}</b> · ${t ? idTag(t) + " " + esc(t.title) : esc(s.id)} needs a <span class="id" style="${COLOR(s.kind)}">${s.kind}</span>: <i>${esc(s.fields.title || "")}</i></div>
    <div class="moves" style="${COLOR(s.kind)}"><button data-ropen="${esc(s.id)}" data-key="${esc(s.key)}">Open and accept</button></div></div>`; };
  return `<div class="section"><p class="small muted">${fails.length} needed · ${warns.length} suggested · ${S.integrity.dismissed} dismissed. Opening the item shows the offer with Accept, Dismiss and Link existing.</p>
    ${fails.map(one).join("") || '<p class="muted">Nothing needed.</p>'}${warns.length ? `<h3>Suggested, not required</h3>${warns.map(one).join("")}` : ""}</div>`;
}
function rScopes(offScope, scopes) {
  return `<div class="section"><p class="small muted">Items whose Scope is blank or not one of the engagement's. Choosing one writes the item.</p>
    ${offScope.map(i => `<div class="blk">${idTag(i)} ${esc(i.title)} <span class="small muted">${esc(i.scope || "(blank)")}</span> <select data-rscope="${i.id}"><option value="">set scope…</option>${scopes.map(s => `<option>${esc(s)}</option>`).join("")}</select></div>`).join("") || '<p class="muted">Every item has a listed scope.</p>'}</div>`;
}
async function rPost(url, body, msg) { const y = window.scrollY; try { await post(url, body); if (msg) toast(msg); await load(); window.scrollTo(0, y); } catch (e) { toast(e.message); } }
async function rAct(what) {
  const unrev = new Set(S.unreviewed), q = S.items.filter(i => i.kind === RF.kind && (!RF.onlyUnrev || unrev.has(i.id)));
  const i = q[Math.min(RF.pos, q.length - 1)]; if (!i) return;
  if (what === "next") { RF.pos = Math.min(q.length - 1, RF.pos + 1); render(); return; }
  if (what === "prev") { RF.pos = Math.max(0, RF.pos - 1); render(); return; }
  if (what === "reviewed") return rPost("/api/rationalise/reviewed", {id: i.id}, `${i.id} marked reviewed`);
  if (what === "merge") { const into = $("#rf-merge")?.value; if (!into) return toast("Pick the item to merge into"); return rPost("/api/merge", {survivor: into, losers: [i.id], evidence: ""}, `${i.id} folded into ${into}`); }
  if (what === "delete") { const reason = $("#rf-reason")?.value.trim(); if (!reason) return toast("Give a reason to delete"); return rPost("/api/delete", {id: i.id, reason, evidence: ""}, `${i.id} deleted`); }
}
function wireRationalise(m) {
  m.querySelectorAll("[data-rtab]").forEach(el => el.onclick = () => { RF.tab = el.dataset.rtab; RF.pos = 0; render(); });
  const on = (sel, ev, fn) => { const el = $(sel, m); if (el) el[ev] = fn; };
  on("#rf-kind", "onchange", e => { RF.kind = e.target.value; RF.pos = 0; render(); });
  on("#rf-unrev", "onchange", e => { RF.onlyUnrev = e.target.checked; RF.pos = 0; render(); });
  m.querySelectorAll("[data-rv]").forEach(el => el.onclick = () => rAct(el.dataset.rv));
  m.querySelectorAll("[data-rnotdup]").forEach(el => el.onclick = () => rPost("/api/rationalise/not-duplicates", {ids: el.dataset.rnotdup.split(",")}, "Group set aside"));
  m.querySelectorAll("[data-rlead]").forEach(el => el.onclick = () => {
    const keep = el.dataset.rlead, losers = [...el.closest(".cs").querySelectorAll("[data-rdup]")].filter(x => x.checked && x.dataset.rdup !== keep).map(x => x.dataset.rdup);
    if (!losers.length) return toast("Tick the items to fold in");
    rPost("/api/merge", {survivor: keep, losers, evidence: ""}, `Folded ${losers.length} into ${keep}`);
  });
  m.querySelectorAll("[data-ropen]").forEach(el => el.onclick = () => { view = S.byId[el.dataset.ropen]?.kind || view; open = el.dataset.ropen; form = {mode: "support", key: el.dataset.key, fields: {}, links: []}; render(); });
  m.querySelectorAll("[data-rscope]").forEach(el => el.onchange = () => { if (el.value) rPost("/api/edit", {id: el.dataset.rscope, fields: {scope: el.value}, links: [], evidence: "", gist: "scope set in Rationalise"}, `${el.dataset.rscope} scope set`); });
}
document.addEventListener("keydown", e => {
  if (view !== "rationalise" || RF.tab !== "rows" || ["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement.tagName)) return;
  const k = {a: "reviewed", m: "merge", d: "delete", j: "next", k: "prev"}[e.key]; if (k) { e.preventDefault(); rAct(k); }
});
```

`itemPanel(i, false)` inside the row walk renders the drawer content inline, including its Supports needed panel; `wire()` is not called on it there, so its buttons are inert in the walk. That is acceptable: the walk's own buttons do the work, and the Missing supports tab opens the drawer proper.

- [ ] **Step 5: Drawer Merge into and Delete**

In `itemPanel()`, replace the last line's edit button fragment:

```js
    ${form && form.mode === "edit" ? editForm(i) : form && form.mode === "merge" ? mergeForm(i) : form && form.mode === "delete" ? deleteForm(i) : `<div class="form"><button id="edit-btn">Edit fields</button> ${S.engagement.writes === "direct" ? `<button class="ghost" id="merge-btn">Merge into…</button> <button class="ghost" id="delete-btn">Delete…</button>` : `<button class="ghost" disabled title="This engagement writes change sets, which have no block for a merge">Merge into…</button> <button class="ghost" disabled title="This engagement writes change sets, which have no block for a delete">Delete…</button>`}</div>`}`;
```

Add after `editForm` (find it with `grep -n "function editForm"`):

```js
function mergeForm(i) {
  const same = S.items.filter(x => x.kind === i.kind && x.id !== i.id);
  return `<div class="form"><h3>Merge ${i.id} into</h3><div class="field"><label>Survivor</label><select data-f="__into"><option value="">choose…</option>${same.map(x => `<option value="${x.id}" ${form.fields.__into === x.id ? "selected" : ""}>${x.id} ${esc(x.title.slice(0, 60))}</option>`).join("")}</select></div>
    <p class="small muted">This item's source, notes, links and any field the survivor leaves blank fold into the survivor. Links elsewhere that name this item are rewritten. This file is removed; git keeps it.</p>${tail()}</div>`;
}
function deleteForm(i) {
  return `<div class="form"><h3>Delete ${i.id}</h3><div class="field"><label>Reason</label><input data-f="__reason" value="${esc(form.fields.__reason || "")}"></div>
    <p class="small muted">Links elsewhere that name this item are dropped, each with a History line carrying the reason. The file is removed; git keeps it.</p>${tail()}</div>`;
}
```

In `wire()`, after the `#edit-btn` line:

```js
  $("#merge-btn", d)?.addEventListener("click", () => { form = {mode: "merge", fields: {}, links: []}; renderDetail(); });
  $("#delete-btn", d)?.addEventListener("click", () => { form = {mode: "delete", fields: {}, links: []}; renderDetail(); });
```

`data-f` selects need `onchange` as well as `oninput`; add after the `[data-f]` oninput line in `wire()`:

```js
  d.querySelectorAll("select[data-f]").forEach(el => el.onchange = () => form.fields[el.dataset.f] = el.value);
```

In `submit()`, before the `if (form.mode === "create")` line:

```js
    if (form.mode === "merge") { if (!form.fields.__into) throw new Error("Choose the survivor."); r = await post("/api/merge", {survivor: form.fields.__into, losers: [open], evidence: form.evidence || ""}); toast(`${open} folded into ${r.survivor}`); open = r.survivor; form = null; await load(); return; }
    if (form.mode === "delete") { if (!form.fields.__reason) throw new Error("Give a reason."); r = await post("/api/delete", {id: open, reason: form.fields.__reason, evidence: form.evidence || ""}); toast(`${open} deleted`); open = null; form = null; await load(); return; }
```

- [ ] **Step 6: Syntax check in Docker**

Run: `docker run --rm -v "$PWD/console/static:/s" node:22-alpine node --check /s/app.js`
Expected: no output.

- [ ] **Step 7: Commit**

```bash
git add console/static/app.js
git commit -m "Console: Live from the first item, Rationalise view over the registers, Merge into and Delete in the drawer"
```

---

### Task 7: Docs

**Files:**
- Modify: `console/README.md` (version line 3, model ref line 5, the stage paragraph in "What it shows", the Baseline bullet)
- Modify: `console/confluence-runbook.md` (the baseline and freeze steps; find with `grep -n -i "freeze" console/confluence-runbook.md`)
- Modify: `console/static/guide.html` (the freeze paragraph; find with `grep -n -i "freeze" console/static/guide.html`)
- Modify: `CLAUDE.md` (Rules bullet on freeze, model version 2.26 to 2.28 in two places, Open threads)
- Modify: `console/make-sample.py:45` (model version written into the sample, to 2.28)

- [ ] **Step 1: README**

Version to `0.5, 15 September 2026`, model to `2.28`. Rewrite the stage sentence: "The console knows its stage: **Baselining** while the baseline folder is present and no register holds an item, when it opens on Baseline; **Live** from the first item, when it opens on Outstanding and the header shows the freeze date if one ran." Replace the Baseline bullet's last two sentences with: "The freeze writes every candidate not rejected, merged or discarded and reports what is left: unreviewed rows, supports still missing, scopes off the list. From then on the same work continues on the **Rationalise** view over the items: Duplicates (groups set aside go to `duplicates-dismissed.json`), Row by row with Mark reviewed, Merge and Delete, Missing supports, and Scopes where the engagement declares any. Merge folds the loser into the survivor, rewrites links that named it and removes its file; Delete drops links naming the item and removes its file; both are direct-mode only and refuse in change-sets mode." Add `duplicates-dismissed.json` to the Files table row for the engagement folder if one exists, otherwise a sentence under "What it writes".

- [ ] **Step 2: Runbook and guide**

Replace any sentence saying the freeze waits for supports or scopes with one saying it reports them and the Rationalise view works them down. Bump each document's version and date.

- [ ] **Step 3: CLAUDE.md**

Rules bullet: change "Freeze baseline (`baseline.freeze`) is the same in both modes: it writes the accepted candidates as the registers' first item files, refuses to run if any register already has an item" to "Freeze baseline (`baseline.freeze`) is the same in both modes: it writes every candidate not rejected, merged or discarded as the registers' first item files, refuses to run if any register already has an item, reports what is left unreviewed or missing". Add a bullet: "**Merge and Delete are direct-mode writes through `commit(..., delete=True)` and `rewrite_links()`.** They refuse in change-sets mode. `duplicates-dismissed.json` holds set-aside groups; `baseline/verdicts.json` remains the review ledger, and `unreviewed` in `/api/state` is derived from it." Model 2.26 to 2.28 in the two places. Open threads: the ingester line to "2.28".

- [ ] **Step 4: make-sample.py**

Line 45: model version string to `2.28`.

- [ ] **Step 5: Commit**

```bash
git add console/README.md console/confluence-runbook.md console/static/guide.html CLAUDE.md console/make-sample.py
git commit -m "Docs: the registers as the working space after the freeze"
```

---

### Task 8: Browser verification on engagements/test

**Files:** none modified unless a defect is found.

- [ ] **Step 1: Snapshot and start**

```bash
cd /Users/adam/projects/design-register && cp -r engagements/test /tmp/test-before && make down; make up ENG=engagements/test
```

Wait two seconds. `curl -s localhost:8085/api/state | python3 -c "import sys,json;d=json.load(sys.stdin);print(len(d['items']), d['unreviewed'][:3], len(d['dupes']))"` should print `0 [] 0`.

- [ ] **Step 2: Freeze with undecided rows**

Open `http://localtest.me:8085/` in Chrome via the extension. Stage reads Baselining. Type a name in Made by. On Baseline, press Freeze baseline, then Yes, freeze. Expect the toast with the five counts and the view to land on Rationalise with the stage reading Live. Check with:

```bash
curl -s localhost:8085/api/state | python3 -c "import sys,json;d=json.load(sys.stdin);print(len(d['items']), len(d['unreviewed']), len(d['dupes']))"
grep -E "Unreviewed|Supports missing|Off-list" engagements/test/baseline/frozen.md
```

- [ ] **Step 3: Raise, merge, delete**

Open Requirements, press New requirement, fill title and owner, submit. Confirm a new file under `engagements/test/requirements/`. On Rationalise, Duplicates: pick a group, This one leads. Confirm the loser file is gone and the survivor's History has the merged line. Row by row: Mark reviewed on one item and see the badge drop by one. Delete one with a reason; check the file is gone and `git status` under `engagements/test` shows the removal and the touched files. Scopes tab is absent because the test engagement declares none.

- [ ] **Step 4: Restore**

```bash
make down; rm -rf engagements/test && cp -r /tmp/test-before engagements/test
```

- [ ] **Step 5: Run the suite one last time and report**

Run: `make test 2>&1 | tail -3`
Expected: `OK`. Report the counts observed in step 2 and anything that misbehaved.
