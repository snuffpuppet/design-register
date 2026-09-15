# Console Rethink Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the console's front end with one model-driven table, a side panel and a bulk bar, backed by a handful of new server endpoints, so that single, whole-item and bulk edits all go through one generated move form.

**Architecture:** The server stays standard-library Python and every write still lands in `commit()`. New endpoints (`/api/model`, `/api/needs`, `/api/bulk`, `/api/items`, `/api/views`, `/api/renumber`, `/api/report/summary`) are thin callers of the existing single operations. The browser gets Preact and htm from cdnjs as UMD globals, no build step, and `app.js` is replaced by nine small modules. The old front end moves to `console/static/old/` until Task 15 deletes it.

**Tech Stack:** Python 3.12 standard library, `unittest`, Docker (`make test`, `make up`), Preact 10.19.3, htm 3.1.1, vanilla CSS with the existing tokens.

**Spec:** `docs/superpowers/specs/2026-09-15-console-rethink-design.md`

## Global Constraints

- Everything runs in Docker. `make test` runs the unit tests; `make up` and `make reload` run the console. Never start a host python server.
- Every Live write goes through `H.commit()` in `console/server.py`. Do not add a write path beside it.
- `console/model.py` is the only place the console knows the model. New model facts go there as data.
- Change-sets mode: bulk, merge, delete and renumber refuse with a message that says so. Single moves and creates keep working.
- Australian English, no em dashes, no "not x but y" framing, in code comments and UI copy alike.
- The mockups are at https://claude.ai/artifact/NNJWAReYeP3DuHXqtetw3V. Screen numbers below refer to them.
- Browser checks use `http://localtest.me:8085/`. After `make reload` wait two seconds before loading.
- Commit messages end with `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.
- CDN files, verified reachable on 15 September 2026:
  - `https://cdnjs.cloudflare.com/ajax/libs/preact/10.19.3/preact.umd.js` (global `preact`)
  - `https://cdnjs.cloudflare.com/ajax/libs/preact/10.19.3/hooks.umd.js` (global `preactHooks`, needs `preact` loaded first)
  - `https://cdnjs.cloudflare.com/ajax/libs/htm/3.1.1/htm.umd.js` (global `htm`)

## Conventions the tests use

Server tests live in `console/tests/`, use `unittest`, and set the engagement folder to a temp dir with `use()` and `write_item()` from `test_server_direct.py`. Copy those two helpers into any new test file rather than importing them, so each file runs alone. Handler methods are called on a `Stub` that has no socket; the pattern is:

```python
class Stub:
    for _n in ("evidence", "commit", "transition", "create", "edit", "merge", "delete", "rewrite_links", "supports_preview", "offer_fields", "write_offer"):
        locals()[_n] = getattr(S.H, _n, None)
```

Add each new handler method name to that tuple in the test that calls it. Run one file with:

```bash
docker run --rm -v "$PWD/console:/app" -w /app python:3.12-slim python -m unittest tests.test_bulk -v
```

## File map

| File | Responsibility | Task |
|---|---|---|
| `console/model.py` | `SPECIAL_ON_ENTRY`, `WITHDRAWS`, `BACKWARD`, `FORWARD`; `missing_for` reads specials | 1 |
| `console/integrity.py` | `provenance(items, by_id)` | 2 |
| `console/server.py` | `/api/model`, `/api/needs`, `/api/items`, `/api/bulk`, `/api/views`, `/api/report/summary`, `/api/renumber`; `provenance` in state | 2 to 7 |
| `console/views.py` | Saved views file and the summary text | 6 |
| `console/renumber.py` | The id map and the rewrite plan | 7 |
| `console/static/index.html` | Shell, CDN scripts, module scripts | 8 |
| `console/static/app.js` | Boot and hash routing | 8 |
| `console/static/store.js` | State, fetch, filter, selection | 8 |
| `console/static/rail.js` | Left rail | 8 |
| `console/static/table.js` | Table, chips, keyboard | 8 |
| `console/static/panel.js` | Side panel | 9 |
| `console/static/cells.js` | Inline cell editors | 10 |
| `console/static/move-form.js` | Generated move and create form | 10 |
| `console/static/picker.js` | Link picker | 11 |
| `console/static/bulk.js` | Bulk bar | 12 |
| `console/static/report.js` | Saved view renderer, summary, push | 14 |
| `console/static/old/` | The previous front end, served at `/old/` | 8, deleted 15 |

---

### Task 1: Model data for specials, withdrawals and provenance directions

**Files:**
- Modify: `console/model.py` (append after `RULES`, and replace `missing_for`)
- Modify: `console/server.py:483-490` (the two inline special cases in `transition()`)
- Test: `console/tests/test_model.py`

**Interfaces:**
- Produces: `M.SPECIAL_ON_ENTRY` list of dicts `{kind, state, field, check, value}` where `check` is `"prefix"` or `"required_if"`; `M.WITHDRAWS` dict type to state; `M.BACKWARD` and `M.FORWARD` dict type to list of link words; `M.missing_for(kind, state, item)` now also returns the special cases.

- [ ] **Step 1: Write the failing tests**

Append to `console/tests/test_model.py`:

```python
class Specials(unittest.TestCase):
    def test_blocked_needs_the_prefix(self):
        it = {"kind": "OI", "status": "Open", "next action": "wait", "owner": "x", "links": []}
        self.assertIn('Next action starting "Blocked: "', M.missing_for("OI", "Blocked", it))
        it["next action"] = "Blocked: waiting"
        self.assertEqual(M.missing_for("OI", "Blocked", it), [])

    def test_vendor_cr_needs_vendor_ref_for_submitted(self):
        it = {"kind": "CR", "status": "Approved", "approved-by": "x", "phase": "P1", "implemented-by": "Vendor", "links": []}
        self.assertIn("Vendor ref", M.missing_for("CR", "Submitted", it))
        it["implemented-by"] = "Internal"
        self.assertEqual(M.missing_for("CR", "Submitted", it), [])

    def test_withdraws_names_a_terminal_state_per_type(self):
        for k, st in M.WITHDRAWS.items():
            self.assertIn(st, M.TERMINAL[k], k)
        self.assertEqual(M.WITHDRAWS["DEC"], "Rejected")

    def test_provenance_words_are_link_words(self):
        for k, words in list(M.BACKWARD.items()) + list(M.FORWARD.items()):
            for w in words:
                self.assertIn(w, M.LINK_WORDS[k], f"{k} {w}")
```

- [ ] **Step 2: Run to verify it fails**

Run: `docker run --rm -v "$PWD/console:/app" -w /app python:3.12-slim python -m unittest tests.test_model -v`
Expected: FAIL, `AttributeError: module 'model' has no attribute 'WITHDRAWS'` and the Blocked assertion.

- [ ] **Step 3: Add the data and extend `missing_for`**

Append to `console/model.py` after `RULES`:

```python
# Conditions on entry that are not a plain "field is filled". `prefix`: the field must start with `value`.
# `required_if`: the field is required when the item's `when` field equals `equals`.
SPECIAL_ON_ENTRY = [
    dict(kind="OI", state="Blocked", field="next action", check="prefix", value="Blocked: ",
         text='Next action starting "Blocked: "'),
    dict(kind="CR", state="Submitted", field="vendor-ref", check="required_if", when="implemented-by", equals="Vendor",
         text="Vendor ref"),
]

# The withdrawing terminal state per type, for the bulk bar's Withdraw.
WITHDRAWS = {"REQ": "Withdrawn", "LIM": "Withdrawn", "CR": "Withdrawn", "DEC": "Rejected", "RSK": "Retired", "OI": "Closed"}

# Link words that read as provenance. BACKWARD walks to what an item came from; FORWARD to what it produced.
BACKWARD = {
    "REQ": ["replaces"], "DEC": ["proposed by"], "LIM": ["introduced by", "constrains"],
    "RSK": ["raised by"], "OI": [], "CR": ["triggered by", "part of"],
}
FORWARD = {
    "REQ": ["worked by"], "DEC": ["addresses", "introduces", "raises", "supersedes"],
    "LIM": ["dispositioned by", "assessed by", "needs"], "RSK": ["realised as", "mitigated by"],
    "OI": ["resolves into"], "CR": ["delivers", "worked by"],
}
```

Replace `missing_for` with:

```python
def missing_for(kind, state, item):
    """Return the list of required fields (labels) that are empty for entering `state`, including the special conditions."""
    req = REQUIRED_ON_ENTRY.get(kind, {}).get(state, [])
    out = []
    for f in req:
        if f.startswith("link:"):
            word = f[5:]
            if not any(l.lower().startswith(word) for l in item.get("links", [])):
                out.append(f"Links: {word} …")
        elif f == "options":
            opts = [l for l in item.get("options", "").splitlines() if l.strip()]
            if len(opts) < 2:
                out.append("Options (at least two)")
        elif not str(item.get(f, "")).strip():
            out.append(LABELS.get(f, f))
    for sp in SPECIAL_ON_ENTRY:
        if sp["kind"] != kind or sp["state"] != state:
            continue
        val = str(item.get(sp["field"], "") or "")
        if sp["check"] == "prefix" and not val.startswith(sp["value"]):
            out.append(sp["text"])
        if sp["check"] == "required_if" and item.get(sp["when"]) == sp["equals"] and not val.strip():
            out.append(sp["text"])
    return out
```

In `console/server.py` `transition()`, delete these four lines:

```python
        if kind == "OI" and to == "Blocked" and not merged.get("next action", "").startswith("Blocked:"):
            missing.append('Next action starting "Blocked: "')
        if kind == "CR" and to == "Submitted" and merged.get("implemented-by") == "Vendor" and not merged.get("vendor-ref"):
            missing.append("Vendor ref")
```

Update the docstring at the top of `model.py` to say 2.29 and mention `SPECIAL_ON_ENTRY`, `WITHDRAWS`, `BACKWARD`, `FORWARD`.

- [ ] **Step 4: Run all tests**

Run: `make test`
Expected: all pass, including the existing transition tests in `test_server_direct.py`.

- [ ] **Step 5: Commit**

```bash
git add console/model.py console/server.py console/tests/test_model.py
git commit -m "Model data: special entry conditions, withdrawing states, provenance directions

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 2: Provenance chains in state

**Files:**
- Modify: `console/integrity.py` (append `provenance`)
- Modify: `console/server.py:228-240` (`state()` adds `provenance`)
- Test: `console/tests/test_provenance.py`

**Interfaces:**
- Produces: `I.provenance(items, by_id) -> {id: {"back": [{"id", "word", "title", "status", "kind"}], "forward": [...], "dangling": ["word ID"]}}`. `items` is a list of item dicts; `by_id` a dict. Walks one hop only; the panel steps further by opening the neighbour.
- `state()["provenance"]` carries that dict.

- [ ] **Step 1: Write the failing test**

Create `console/tests/test_provenance.py`:

```python
import unittest
import integrity as I


def it(id, status, links=(), title=""):
    return {"id": id, "kind": id.split("-")[0], "status": status, "title": title or id, "links": list(links)}


class Provenance(unittest.TestCase):
    def setUp(self):
        self.items = [
            it("DEC-0003", "Accepted", ["introduces LIM-0004"]),
            it("LIM-0004", "Change requested", ["introduced by DEC-0003", "constrains REQ-0042", "dispositioned by CR-0009"]),
            it("REQ-0042", "Agreed"),
            it("CR-0009", "For approval", ["triggered by LIM-0004", "worked by OI-0011", "delivers REQ-0099"]),
            it("OI-0011", "Open"),
        ]
        self.by = {x["id"]: x for x in self.items}
        self.p = I.provenance(self.items, self.by)

    def test_backward_hop_carries_word_and_neighbour(self):
        back = self.p["CR-0009"]["back"]
        self.assertEqual([(b["word"], b["id"], b["status"]) for b in back], [("triggered by", "LIM-0004", "Change requested")])

    def test_forward_hop(self):
        fwd = self.p["CR-0009"]["forward"]
        self.assertEqual([(f["word"], f["id"]) for f in fwd], [("worked by", "OI-0011")])

    def test_dangling_link_is_reported_not_walked(self):
        self.assertEqual(self.p["CR-0009"]["dangling"], ["delivers REQ-0099"])

    def test_reverse_of_a_backward_word_appears_forward_on_the_target(self):
        # LIM-0004 introduced by DEC-0003; DEC-0003 also writes introduces. One entry, not two.
        fwd = self.p["DEC-0003"]["forward"]
        self.assertEqual([(f["word"], f["id"]) for f in fwd], [("introduces", "LIM-0004")])

    def test_item_with_no_links_has_empty_chains(self):
        self.assertEqual(self.p["OI-0011"], {"back": [], "forward": [], "dangling": []})
```

- [ ] **Step 2: Run to verify it fails**

Run: `docker run --rm -v "$PWD/console:/app" -w /app python:3.12-slim python -m unittest tests.test_provenance -v`
Expected: FAIL, `AttributeError: module 'integrity' has no attribute 'provenance'`.

- [ ] **Step 3: Implement**

Append to `console/integrity.py`:

```python
def provenance(items, by_id):
    """One hop each way for every item. `back` follows the item's own BACKWARD words; `forward` its FORWARD words.
    A link whose target is not in `by_id` goes to `dangling` as written. Words are matched case-insensitively
    on the link's start; the target id is the first id-looking token after the word."""
    out = {}
    for it in items:
        k = it["kind"]
        back, fwd, dang = [], [], []
        for l in it.get("links", []):
            low = l.lower()
            word = next((w for w in sorted(M.LINK_WORDS.get(k, {}), key=len, reverse=True) if low.startswith(w)), None)
            if not word:
                continue
            m = LINK_ID.search(l[len(word):])
            tid = m.group(1) if m else None
            tgt = by_id.get(tid) if tid else None
            if tid and not tgt:
                if word in M.BACKWARD.get(k, []) or word in M.FORWARD.get(k, []):
                    dang.append(l)
                continue
            if not tgt:
                continue
            hop = {"id": tgt["id"], "word": word, "title": tgt.get("title", ""), "status": tgt.get("status", ""), "kind": tgt["kind"]}
            if word in M.BACKWARD.get(k, []) and hop["id"] not in [b["id"] for b in back]:
                back.append(hop)
            elif word in M.FORWARD.get(k, []) and hop["id"] not in [f["id"] for f in fwd]:
                fwd.append(hop)
        out[it["id"]] = {"back": back, "forward": fwd, "dangling": dang}
    return out
```

`integrity.py` already imports `model as M`; confirm with `grep -n "^import\|^from" console/integrity.py` and add `import model as M` if it is missing.

In `console/server.py` `state()`, add to the returned dict, after `"integrity": integrity_of(items),`:

```python
            "provenance": I.provenance(list(items.values()), items),
```

- [ ] **Step 4: Run all tests**

Run: `make test`
Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add console/integrity.py console/server.py console/tests/test_provenance.py
git commit -m "Provenance: one hop back and forward per item in /api/state

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 3: `/api/model`, `/api/needs` and `/api/items`

**Files:**
- Modify: `console/server.py` (`do_GET`, `do_POST`, new methods `model_payload`, `needs`, `search_items`)
- Test: `console/tests/test_needs.py`

**Interfaces:**
- Produces: `GET /api/model` returns `state()["model"]` plus `specials`, `withdraws`, `backward`, `forward`, `rules`, `scopes`, `phases`, `owners` (stakeholder names sorted).
- `POST /api/needs {ids: [..], to: "State"}` returns `{"needs": {id: {"ok": bool, "missing": [labels], "from": state}}}`. An id whose type cannot reach `to` from its state gets `ok: False` and `missing: ["<from> → <to> is not an allowed move"]`.
- `GET /api/items?q=text&types=REQ,CR&exclude=ID` returns `{"items": [{"id","kind","title","status"}]}`, at most 50, ordered by id.

- [ ] **Step 1: Write the failing tests**

Create `console/tests/test_needs.py`:

```python
import unittest, tempfile, os, shutil
import server as S
import items as IT


def use(eng):
    S.ENG = eng; S.CS_DIR = os.path.join(eng, "change-sets"); S.DISMISSED_PATH = os.path.join(eng, "supports-dismissed.json")


def write_item(eng, id, title, status, **f):
    kind = id.split("-")[0]
    it = {"id": id, "kind": kind, "title": title, "status": status, "owner": "Priya Nair", "raised-on": "1 September 2026", "closed-on": "",
          "updated": "1 September 2026", "implemented-by": "Vendor", "source": "workshop", "notes": "", "links": [], "history": []}
    it.update(f)
    p = IT.item_path(eng, id); os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(IT.render_item(it))


class Stub:
    for _n in ("needs", "search_items", "model_payload"):
        locals()[_n] = getattr(S.H, _n, None)


class Needs(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); self.saved = (S.ENG, S.CS_DIR, S.DISMISSED_PATH); use(self.d); self.h = Stub()
        write_item(self.d, "REQ-0001", "One", "Draft", moscow="Must")
        write_item(self.d, "REQ-0002", "Two", "Draft", moscow="Must", phase="P1")
        write_item(self.d, "REQ-0003", "Three", "Verified", moscow="Must", phase="P1")
        write_item(self.d, "CR-0001", "Vendor CR", "Approved", **{"approved-by": "Board", "phase": "P1", "reason": "r"})
        write_item(self.d, "OI-0001", "Wait", "Open", **{"next action": "wait"})

    def tearDown(self):
        S.ENG, S.CS_DIR, S.DISMISSED_PATH = self.saved; shutil.rmtree(self.d)

    def test_needs_lists_missing_per_item(self):
        r = self.h.needs({"ids": ["REQ-0001", "REQ-0002"], "to": "Agreed"})["needs"]
        self.assertEqual(r["REQ-0001"], {"ok": False, "missing": ["Phase"], "from": "Draft"})
        self.assertEqual(r["REQ-0002"], {"ok": True, "missing": [], "from": "Draft"})

    def test_needs_refuses_a_move_the_model_forbids(self):
        r = self.h.needs({"ids": ["REQ-0003"], "to": "Agreed"})["needs"]["REQ-0003"]
        self.assertFalse(r["ok"]); self.assertIn("not an allowed move", r["missing"][0])

    def test_needs_includes_specials(self):
        self.assertEqual(self.h.needs({"ids": ["CR-0001"], "to": "Submitted"})["needs"]["CR-0001"]["missing"], ["Vendor ref"])
        self.assertEqual(self.h.needs({"ids": ["OI-0001"], "to": "Blocked"})["needs"]["OI-0001"]["missing"], ['Next action starting "Blocked: "'])

    def test_search_filters_by_type_and_text_and_excludes(self):
        r = self.h.search_items({"q": "o", "types": ["REQ"], "exclude": "REQ-0001"})["items"]
        self.assertEqual([x["id"] for x in r], ["REQ-0002"])   # "Two" contains o; "Three" does not; REQ-0001 excluded
        r = self.h.search_items({"q": "0001", "types": [], "exclude": ""})["items"]
        self.assertEqual([x["id"] for x in r], ["CR-0001", "OI-0001", "REQ-0001"])

    def test_model_payload_carries_the_new_tables(self):
        m = self.h.model_payload()
        self.assertEqual(m["withdraws"]["DEC"], "Rejected")
        self.assertIn("triggered by", m["backward"]["CR"])
        self.assertEqual(m["specials"][0]["kind"], "OI")
        self.assertIn("Priya Nair", m["owners"])
```

- [ ] **Step 2: Run to verify it fails**

Run: `docker run --rm -v "$PWD/console:/app" -w /app python:3.12-slim python -m unittest tests.test_needs -v`
Expected: FAIL, `TypeError: 'NoneType' object is not callable` (the Stub has no `needs`).

- [ ] **Step 3: Implement**

In `console/server.py`, add to the `H` class after `baseline_state`:

```python
    def model_payload(self):
        eng = load_engagement()
        items = overlay(load_registers(), load_change_sets())
        owners = {s["name"] for s in load_stakeholders()} | {i.get("owner", "") for i in items.values()}
        m = dict(state_model(eng))
        m.update({"specials": M.SPECIAL_ON_ENTRY, "withdraws": M.WITHDRAWS, "backward": M.BACKWARD, "forward": M.FORWARD,
                  "rules": M.RULES, "scopes": eng["scopes"], "phases": eng["phases"], "owners": sorted(o for o in owners if o)})
        return m

    def needs(self, req):
        """What each id still lacks to enter `to`, without writing anything. The move form draws itself from this."""
        items = overlay(load_registers(), load_change_sets())
        to, out = req["to"], {}
        for id in req.get("ids", []):
            it = items.get(id)
            if not it:
                out[id] = {"ok": False, "missing": ["No such item"], "from": ""}
                continue
            frm = it["status"]
            if to not in M.TRANSITIONS.get(it["kind"], {}).get(frm, []):
                out[id] = {"ok": False, "missing": [f"{frm} → {to} is not an allowed move for a {M.NAMES[it['kind']]} (I20)"], "from": frm}
                continue
            merged = dict(it); merged.update({field_key(k): v for k, v in req.get("fields", {}).items() if str(v).strip()})
            missing = M.missing_for(it["kind"], to, merged)
            out[id] = {"ok": not missing, "missing": missing, "from": frm}
        return {"needs": out}

    def search_items(self, req):
        items = overlay(load_registers(), load_change_sets())
        q = str(req.get("q", "")).strip().lower()
        types = [t for t in req.get("types", []) if t]
        ex = req.get("exclude", "")
        hits = [i for i in items.values() if i["id"] != ex and (not types or i["kind"] in types)
                and (not q or q in i["id"].lower() or q in str(i.get("title", "")).lower())]
        hits.sort(key=lambda i: i["id"])
        return {"items": [{"id": i["id"], "kind": i["kind"], "title": i.get("title", ""), "status": i.get("status", "")} for i in hits[:50]]}
```

Pull the model dict out of `state()` into a module-level function so both callers share it. Replace the `"model": {...}` value in `state()` with `"model": state_model(eng)` and add above `state()`:

```python
def state_model(eng):
    return {"states": M.STATES, "terminal": {k: sorted(v) for k, v in M.TERMINAL.items()},
            "transitions": M.TRANSITIONS, "short": M.SHORT, "long": M.LONG, "labels": M.LABELS,
            "choices": M.CHOICES, "required": M.REQUIRED_ON_ENTRY, "create": {k: required_on_create(k, eng["scopes"]) for k in M.DIRS},
            "first": M.FIRST_STATE, "names": M.NAMES, "linkWords": M.LINK_WORDS, "closes": {k: sorted(v) for k, v in M.CLOSES.items()}}
```

Routes. In `do_GET`, before `if p == "/":`:

```python
        if p == "/api/model":
            return self.send_json(self.model_payload())
        if p == "/api/items":
            qs = parse_qs(urlparse(self.path).query)
            return self.send_json(self.search_items({"q": qs.get("q", [""])[0], "types": [t for t in qs.get("types", [""])[0].split(",") if t], "exclude": qs.get("exclude", [""])[0]}))
```

Change the import line to `from urllib.parse import urlparse, parse_qs`.

In `do_POST`, after the `/api/edit` route:

```python
                if p == "/api/needs":
                    return self.send_json(self.needs(req))
```

- [ ] **Step 4: Run all tests**

Run: `make test`
Expected: pass.

- [ ] **Step 5: Check the live endpoints**

```bash
make reload; sleep 2
curl -s localhost:8085/api/model | python3 -c "import json,sys; m=json.load(sys.stdin); print(sorted(m)[:6], m['withdraws'])"
curl -s -X POST localhost:8085/api/needs -H 'Content-Type: application/json' -d '{"ids":["REQ-0001"],"to":"Agreed"}'
curl -s 'localhost:8085/api/items?q=ribbon&types=REQ'
```

Expected: the model keys, a needs dict for REQ-0001, and a short items list.

- [ ] **Step 6: Commit**

```bash
git add console/server.py console/tests/test_needs.py
git commit -m "API: /api/model, /api/needs and /api/items for the generated form and picker

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 4: `/api/bulk`

**Files:**
- Modify: `console/server.py` (`do_POST`, new method `bulk`)
- Test: `console/tests/test_bulk.py`

**Interfaces:**
- Produces: `POST /api/bulk {ids, op, madeBy, evidence?, gist?, fields?, to?, links?}`. `op` is one of `set` (applies `fields` through `edit`), `transition` (applies `to` and `fields` through `transition`), `link` (appends `links` through `edit`), `withdraw` (transition to `M.WITHDRAWS[kind]` with `fields`). Returns `{"written": [ids], "failed": {"id": id, "error": text} | None}`. Stops at the first `ValueError`. Refuses in change-sets mode.

- [ ] **Step 1: Write the failing tests**

Create `console/tests/test_bulk.py` with the `use`, `write_item` helpers copied from `test_needs.py`, and:

```python
class Stub:
    for _n in ("evidence", "commit", "transition", "edit", "bulk", "supports_preview", "offer_fields", "write_offer"):
        locals()[_n] = getattr(S.H, _n, None)


class Bulk(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); self.saved = (S.ENG, S.CS_DIR, S.DISMISSED_PATH); use(self.d); self.h = Stub()
        write_item(self.d, "REQ-0001", "One", "Draft", moscow="Must", phase="P1")
        write_item(self.d, "REQ-0002", "Two", "Draft", moscow="Must", phase="P1")
        write_item(self.d, "REQ-0003", "Three", "Draft", moscow="Must")   # no phase: Agreed will refuse

    def tearDown(self):
        S.ENG, S.CS_DIR, S.DISMISSED_PATH = self.saved; shutil.rmtree(self.d)

    def read(self, id):
        return IT.parse_item(IT.item_path(self.d, id))

    def test_set_writes_a_field_on_each(self):
        r = self.h.bulk({"ids": ["REQ-0001", "REQ-0002"], "op": "set", "fields": {"Owner": "Tom Okafor"}, "madeBy": "Adam"})
        self.assertEqual(r, {"written": ["REQ-0001", "REQ-0002"], "failed": None})
        self.assertEqual(self.read("REQ-0002")["owner"], "Tom Okafor")
        self.assertTrue(any("Adam" in h for h in self.read("REQ-0002")["history"]))

    def test_transition_stops_at_the_first_refusal_and_reports_what_was_written(self):
        r = self.h.bulk({"ids": ["REQ-0001", "REQ-0003", "REQ-0002"], "op": "transition", "to": "Agreed", "madeBy": "Adam"})
        self.assertEqual(r["written"], ["REQ-0001"])
        self.assertEqual(r["failed"]["id"], "REQ-0003"); self.assertIn("Phase", r["failed"]["error"])
        self.assertEqual(self.read("REQ-0002")["status"], "Draft")

    def test_transition_with_shared_fields_fills_the_gap(self):
        r = self.h.bulk({"ids": ["REQ-0003"], "op": "transition", "to": "Agreed", "fields": {"Phase": "P1"}, "madeBy": "Adam"})
        self.assertIsNone(r["failed"]); self.assertEqual(self.read("REQ-0003")["status"], "Agreed")

    def test_link_appends_to_each(self):
        self.h.bulk({"ids": ["REQ-0001", "REQ-0002"], "op": "link", "links": ["worked by OI-0009"], "madeBy": "Adam"})
        self.assertIn("worked by OI-0009", self.read("REQ-0001")["links"])

    def test_withdraw_uses_the_type_table(self):
        r = self.h.bulk({"ids": ["REQ-0001"], "op": "withdraw", "madeBy": "Adam"})
        self.assertIsNone(r["failed"]); self.assertEqual(self.read("REQ-0001")["status"], "Withdrawn")

    def test_refuses_in_change_sets_mode(self):
        open(os.path.join(self.d, "engagement.md"), "w").write("# Engagement: x\n\n- Writes: change-sets\n")
        with self.assertRaises(ValueError): self.h.bulk({"ids": ["REQ-0001"], "op": "set", "fields": {"Owner": "x"}, "madeBy": "Adam"})

    def test_unknown_op_is_refused(self):
        with self.assertRaises(ValueError): self.h.bulk({"ids": ["REQ-0001"], "op": "explode", "madeBy": "Adam"})
```

- [ ] **Step 2: Run to verify it fails**

Run: `docker run --rm -v "$PWD/console:/app" -w /app python:3.12-slim python -m unittest tests.test_bulk -v`
Expected: FAIL on `bulk` not callable.

- [ ] **Step 3: Implement**

In `H`, after `delete`:

```python
    def bulk(self, req):
        """One operation over many ids, each through the single-item handler, stopping at the first refusal.
        Direct mode only: a change set records one block per item and the ingester has no notion of a batch."""
        if not writes_direct():
            raise ValueError("Bulk edits are direct writes; this engagement writes change sets. Move items one at a time.")
        self.evidence(req)
        op, ids = req.get("op"), req.get("ids", [])
        if op not in ("set", "transition", "link", "withdraw"):
            raise ValueError(f"Unknown bulk operation {op!r}.")
        if not ids:
            raise ValueError("Nothing selected.")
        written = []
        for id in ids:
            single = {"id": id, "madeBy": req["madeBy"], "evidence": req.get("evidence", ""), "gist": req.get("gist", ""),
                      "fields": req.get("fields", {}), "links": req.get("links", [])}
            try:
                if op == "set":
                    self.edit(single)
                elif op == "link":
                    self.edit({**single, "fields": {}})
                elif op == "transition":
                    self.transition({**single, "to": req["to"]})
                elif op == "withdraw":
                    kind = id.split("-")[0]
                    self.transition({**single, "to": M.WITHDRAWS[kind]})
            except ValueError as e:
                return {"written": written, "failed": {"id": id, "error": str(e)}}
            written.append(id)
        return {"written": written, "failed": None}
```

Route in `do_POST` after `/api/needs`:

```python
                if p == "/api/bulk":
                    return self.send_json(self.bulk(req))
```

Note: `edit()` raises "Nothing changed." on empty fields and links; the `link` op passes links so it will not. `transition()` requires the target state be reachable, so `withdraw` on an item already terminal refuses and the run stops there, which is the intended behaviour.

- [ ] **Step 4: Run all tests**

Run: `make test`
Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add console/server.py console/tests/test_bulk.py
git commit -m "API: /api/bulk runs set, transition, link and withdraw over a selection

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 5: Saved views and the email summary

**Files:**
- Create: `console/views.py`
- Modify: `console/server.py` (`do_GET`, `do_POST`, `VIEWS_PATH`)
- Test: `console/tests/test_views.py`

**Interfaces:**
- Produces: `views.load(path) -> list`, `views.save(path, list)`, `views.default_views() -> list`, `views.summary(view, items, provenance, integrity, today) -> str`.
- A view is `{"name": str, "filter": {"types": [], "statuses": [], "scopes": [], "owners": [], "rule": "", "since": "", "q": ""}, "columns": [keys], "groupBy": "", "sections": ["moved", "raised", "outstanding", "gaps"]}`.
- `GET /api/views` returns `{"views": [...]}`; when the file is missing, the defaults. `POST /api/views {views: [...]}` writes the file and returns the same. `POST /api/report/summary {view}` returns `{"text": str}`.

- [ ] **Step 1: Write the failing tests**

Create `console/tests/test_views.py`:

```python
import unittest, tempfile, os, shutil, json
import views as V


class Views(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); self.p = os.path.join(self.d, "views.json")

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_missing_file_gives_defaults_and_save_round_trips(self):
        vs = V.load(self.p)
        self.assertEqual([v["name"] for v in vs], ["SLT weekly", "Vendor owes", "By scope"])
        vs[0]["filter"]["since"] = "8 September 2026"
        V.save(self.p, vs)
        self.assertEqual(V.load(self.p)[0]["filter"]["since"], "8 September 2026")

    def test_unparseable_file_gives_defaults(self):
        open(self.p, "w").write("{not json")
        self.assertEqual(len(V.load(self.p)), 3)

    def test_summary_names_moves_outstanding_and_gaps(self):
        items = [
            {"id": "CR-0009", "kind": "CR", "title": "Add site hierarchy", "status": "For approval", "owner": "P", "raised-on": "9 September 2026",
             "updated": "12 September 2026", "history": ["12 September 2026 | Adam | Proposed → For approval | estimate agreed | console session"], "links": [], "due": "22 September 2026"},
            {"id": "OI-0006", "kind": "OI", "title": "Certificate owner", "status": "Blocked", "owner": "A", "raised-on": "1 September 2026",
             "updated": "1 September 2026", "history": [], "links": [], "due": "12 September 2026"},
            {"id": "REQ-0050", "kind": "REQ", "title": "New need", "status": "Draft", "owner": "", "raised-on": "14 September 2026",
             "updated": "14 September 2026", "history": [], "links": []},
        ]
        integ = {"failures": [{"rule": "I3", "id": "REQ-0050", "text": "owner"}], "warnings": []}
        view = V.default_views()[0]; view["filter"]["since"] = "8 September 2026"
        text = V.summary(view, items, integ, "15 September 2026")
        self.assertIn("week to 15 September 2026", text)
        self.assertIn("CR-0009", text); self.assertIn("Proposed to For approval", text)
        self.assertIn("REQ-0050", text)          # raised this week
        self.assertIn("OI-0006", text); self.assertIn("overdue", text)
        self.assertIn("1 gap", text)
```

- [ ] **Step 2: Run to verify it fails**

Run: `docker run --rm -v "$PWD/console:/app" -w /app python:3.12-slim python -m unittest tests.test_views -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'views'`.

- [ ] **Step 3: Implement `console/views.py`**

```python
"""Saved views: a name, a filter, columns, group-by and report sections, kept in <engagement>/views.json.
The summary() text is the email draft the SLT report offers; pure so it can be tested."""
import json, os, re, datetime
import model as M

MONTHS = "January February March April May June July August September October November December".split()
MOVE = re.compile(r"(\S.*?) → (\S.*?)(?: \||$)")


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


def sections(view, items, integrity, today):
    """The four SLT sections as lists of rows. `moved`: items with a History move line on or after `since`.
    `raised`: raised-on on or after since. `outstanding`: DEC Proposed, CR For approval, OI Blocked, anything overdue.
    `gaps`: the integrity failures."""
    since = parse_date(view["filter"].get("since")) or (parse_date(today) - datetime.timedelta(days=7))
    now = parse_date(today)
    moved, raised, outstanding = [], [], []
    for it in items:
        for h in it.get("history", []):
            d = parse_date(h)
            m = MOVE.search(h)
            if d and d >= since and m:
                moved.append({"id": it["id"], "title": it["title"], "from": m.group(1), "to": m.group(2), "owner": it.get("owner", "")})
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
```

In `console/server.py`: add `import views as V` and `VIEWS_PATH = os.path.join(ENG, "views.json")` beside `DUP_PATH`. Add to the `use()` helper pattern nothing (tests of views.py are pure). Routes:

In `do_GET` before `/api/model`:

```python
        if p == "/api/views":
            return self.send_json({"views": V.load(VIEWS_PATH)})
```

In `do_POST` after `/api/bulk`:

```python
                if p == "/api/views":
                    if not writes_direct():
                        raise ValueError("Saved views are a direct-mode file.")
                    V.save(VIEWS_PATH, req["views"])
                    return self.send_json({"views": V.load(VIEWS_PATH)})
                if p == "/api/report/summary":
                    items = list(overlay(load_registers(), load_change_sets()).values())
                    return self.send_json({"text": V.summary(req["view"], items, integrity_of({i["id"]: i for i in items}), today())})
                if p == "/api/report/sections":
                    items = list(overlay(load_registers(), load_change_sets()).values())
                    return self.send_json(V.sections(req["view"], items, integrity_of({i["id"]: i for i in items}), today()))
```

Add `VIEWS_PATH` to the tuple that `use()` resets in tests that touch it (none yet).

- [ ] **Step 4: Run all tests**

Run: `make test`
Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add console/views.py console/server.py console/tests/test_views.py
git commit -m "Saved views in views.json, report sections and the email summary draft

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 6: Renumber

**Files:**
- Create: `console/renumber.py`
- Modify: `console/server.py` (`do_POST`, method `renumber`)
- Modify: `solution-register-model.md` (version 2.29, section 7 sentence)
- Test: `console/tests/test_renumber.py`

**Interfaces:**
- Produces: `renumber.plan(items, kind) -> {"map": {old: new}, "order": [old ids in raised-on then id order]}`. `renumber.dirty(eng) -> bool` (git status of the engagement folder; True when uncommitted changes or not a repo).
- `POST /api/renumber {type, madeBy}` returns `{"map": {...}, "touched": [ids whose links changed]}` and writes `<engagement>/renumbered.md`.

- [ ] **Step 1: Write the failing tests**

Create `console/tests/test_renumber.py` with `use` and `write_item` copied from `test_needs.py`, plus:

```python
import subprocess
import renumber as R


class Stub:
    for _n in ("evidence", "commit", "rewrite_links", "renumber"):
        locals()[_n] = getattr(S.H, _n, None)


class Plan(unittest.TestCase):
    def test_compacts_in_raised_order_and_keeps_already_right_ids(self):
        items = {"REQ-0002": {"id": "REQ-0002", "kind": "REQ", "raised-on": "2 September 2026"},
                 "REQ-0005": {"id": "REQ-0005", "kind": "REQ", "raised-on": "1 September 2026"},
                 "REQ-0009": {"id": "REQ-0009", "kind": "REQ", "raised-on": "3 September 2026"},
                 "LIM-0004": {"id": "LIM-0004", "kind": "LIM", "raised-on": "1 September 2026"}}
        p = R.plan(items, "REQ")
        self.assertEqual(p["order"], ["REQ-0005", "REQ-0002", "REQ-0009"])
        self.assertEqual(p["map"], {"REQ-0005": "REQ-0001", "REQ-0009": "REQ-0003"})   # REQ-0002 already right


class Renumber(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); self.saved = (S.ENG, S.CS_DIR, S.DISMISSED_PATH); use(self.d); self.h = Stub()
        write_item(self.d, "REQ-0002", "Two", "Draft", **{"raised-on": "2 September 2026"})
        write_item(self.d, "REQ-0005", "Five", "Draft", **{"raised-on": "1 September 2026"})
        write_item(self.d, "LIM-0001", "Lim", "Identified", links=["constrains REQ-0005"])
        write_item(self.d, "CR-0001", "Cr", "Proposed", links=["triggered by LIM-0001", "delivers REQ-0002"])
        subprocess.run(["git", "init", "-q", self.d]); subprocess.run(["git", "-C", self.d, "add", "-A"])
        subprocess.run(["git", "-C", self.d, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "seed"])

    def tearDown(self):
        S.ENG, S.CS_DIR, S.DISMISSED_PATH = self.saved; shutil.rmtree(self.d)

    def read(self, id):
        return IT.parse_item(IT.item_path(self.d, id))

    def test_refuses_on_a_dirty_tree(self):
        open(os.path.join(self.d, "scratch.txt"), "w").write("x")
        with self.assertRaises(ValueError): self.h.renumber({"type": "REQ", "madeBy": "Adam"})

    def test_renames_files_rewrites_links_and_writes_the_map(self):
        r = self.h.renumber({"type": "REQ", "madeBy": "Adam"})
        self.assertEqual(r["map"], {"REQ-0005": "REQ-0001"})
        self.assertTrue(os.path.exists(IT.item_path(self.d, "REQ-0001")))
        self.assertFalse(os.path.exists(IT.item_path(self.d, "REQ-0005")))
        self.assertEqual(self.read("REQ-0001")["title"], "Five")
        self.assertTrue(any("renumbered from REQ-0005" in h for h in self.read("REQ-0001")["history"]))
        self.assertEqual(self.read("LIM-0001")["links"], ["constrains REQ-0001"])
        self.assertEqual(self.read("CR-0001")["links"], ["triggered by LIM-0001", "delivers REQ-0002"])
        self.assertIn("LIM-0001", r["touched"])
        self.assertIn("REQ-0005 → REQ-0001", open(os.path.join(self.d, "renumbered.md")).read())

    def test_refuses_in_change_sets_mode(self):
        open(os.path.join(self.d, "engagement.md"), "w").write("# Engagement: x\n\n- Writes: change-sets\n")
        subprocess.run(["git", "-C", self.d, "add", "-A"]); subprocess.run(["git", "-C", self.d, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "m"])
        with self.assertRaises(ValueError): self.h.renumber({"type": "REQ", "madeBy": "Adam"})
```

The python image has no git. Change the `test` target in the Makefile to install it first:

```make
test:
	docker run --rm -v "$(CURDIR)/console:/app" -w /app python:3.12-slim sh -c "apt-get update -qq >/dev/null && apt-get install -y -qq git >/dev/null && python -m unittest discover -s tests -v"
```

- [ ] **Step 2: Run to verify it fails**

Run: `make test`
Expected: the renumber tests FAIL on `ModuleNotFoundError: No module named 'renumber'`; everything else passes.

- [ ] **Step 3: Implement `console/renumber.py`**

```python
"""Renumber one register: compact ids in raised-on order. Pure planning here; the server does the writes."""
import subprocess
import model as M


def plan(items, kind):
    """Order the register's items by raised-on then id and assign 1..n. Items already at their new id are left out of the map."""
    from integrity import parse_date
    ours = [i for i in items.values() if i["kind"] == kind]
    ours.sort(key=lambda i: (parse_date(i.get("raised-on", "")) or __import__("datetime").date.max, i["id"]))
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
```

`integrity.parse_date` returns a date or None; check its signature with `sed -n '13,18p' console/integrity.py` and adjust the import if it is named differently.

In `console/server.py`, add `import renumber as R` and the handler after `bulk`:

```python
    def renumber(self, req):
        """Compact one register's ids. Two-phase so no new id collides with an old one still on disk: every
        affected file moves to a temporary id first, then to its final id, with links rewritten at each step.
        Direct mode only, and only on a clean working tree so there is always a rollback point."""
        if not writes_direct():
            raise ValueError("Renumber is a direct write; this engagement writes change sets.")
        self.evidence(req)
        kind = req.get("type")
        if kind not in M.DIRS:
            raise ValueError("Say which register to renumber.")
        if R.dirty(ENG):
            raise ValueError("Commit the engagement folder first; renumber needs a clean working tree to roll back to.")
        items = load_registers()
        p = R.plan(items, kind)
        if not p["map"]:
            return {"map": {}, "touched": []}
        touched = set()
        # Phase one: old -> temporary (kind-9nnn is never a real id in a register under 9000 items).
        tmp = {old: f"{kind}-9{new[-3:]}" for old, new in p["map"].items()}
        for old, t in tmp.items():
            touched |= set(self.move_id(old, t, req, f"renumbered from {old}"))
        for old, new in p["map"].items():
            touched |= set(self.move_id(tmp[old], new, req, f"renumbered from {old}"))
        lines = ["# Renumbered", "", f"{today()} · {M.NAMES[kind]} register · by {req['madeBy'].strip()}", ""] + \
                [f"- {old} → {new}" for old, new in p["map"].items()] + [""]
        path = os.path.join(ENG, "renumbered.md")
        prior = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
        open(path, "w", encoding="utf-8").write("\n".join(lines) + ("\n" + prior if prior else ""))
        return {"map": p["map"], "touched": sorted(touched - set(p["map"]) - set(p["map"].values()))}

    def move_id(self, old, new, req, gist):
        """Rename one item file to `new`, rewrite every link that named `old`, and record the move in the
        item's History. Returns the ids whose links changed."""
        items = load_registers()
        it = parse_item(item_path(ENG, old))
        it["id"] = new
        it["updated"] = today()
        it["history"].append(" | ".join([today(), req["madeBy"].strip(), gist, self.evidence(req)[0].split(" | ", 2)[2]]))
        newp = item_path(ENG, new); os.makedirs(os.path.dirname(newp), exist_ok=True)
        open(newp, "w", encoding="utf-8").write(render_item(it))
        os.remove(item_path(ENG, old))
        return self.rewrite_links(items, old, new, gist.replace("renumbered from", "link renumbered from"), req)
```

`move_id` writes the file itself rather than through `commit()` because `commit()` keys the file on the item's id and cannot rename. It is the one exception and the docstring says so; the History line format is the same one `commit()` writes. Note the temporary-id History line: `move_id` is called twice per item, so the History gets one "renumbered from OLD" line per phase. Make the second call pass `gist=""` and skip the append when gist is empty:

```python
        if gist:
            it["history"].append(...)
```

and call phase one with the gist and phase two with `""` for the item, while the link rewrite in phase two still needs its gist. Restructure `move_id` to take `item_gist` and `link_gist` separately:

```python
    def move_id(self, old, new, req, item_gist, link_gist):
```

with `if item_gist:` guarding the History append, and the callers:

```python
        for old, t in tmp.items():
            touched |= set(self.move_id(old, t, req, f"renumbered from {old}", f"link renumbered from {old}"))
        for old, new in p["map"].items():
            touched |= set(self.move_id(tmp[old], new, req, "", f"link renumbered from {old}"))
```

Route in `do_POST` after `/api/bulk`:

```python
                if p == "/api/renumber":
                    return self.send_json(self.renumber(req))
```

Model document: change line 3 to `Version 2.29, <today>. Owner: Adam Moyes.` and insert a new paragraph above the 2.28 paragraph: `Version 2.29 adds to section 7 what a tool that renumbers a register leaves behind: every link that named a renamed id rewritten, a History line on each renamed item, and the map of old to new ids kept beside the registers. Nothing in sections 4, 5 or 9 changes.` In section 7, after the merge and delete sentence, add: `When a tool renumbers a register it rewrites every link that named a renamed id, writes a History line on each renamed item, and keeps the map of old to new ids beside the registers.` Update `console/model.py`'s docstring version to 2.29 and the `solution-register-model.md` reference in CLAUDE.md from 2.28 to 2.29.

- [ ] **Step 4: Run all tests**

Run: `make test`
Expected: pass. The LIM link test checks the two-phase rewrite produced exactly `constrains REQ-0001` and not a temporary id.

- [ ] **Step 5: Commit**

```bash
git add console/renumber.py console/server.py console/tests/test_renumber.py Makefile solution-register-model.md console/model.py CLAUDE.md
git commit -m "Renumber a register: compact ids, rewrite links, record the map; model 2.29

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 7: Front-end shell: index, store, rail, read-only table

**Files:**
- Move: `console/static/index.html`, `console/static/app.js` to `console/static/old/`
- Create: `console/static/index.html`, `console/static/app.js`, `console/static/store.js`, `console/static/rail.js`, `console/static/table.js`
- Modify: `console/static/style.css` (append)
- Modify: `console/server.py` (`do_GET` serves `/old/` as before; `/` serves the new index)

**Interfaces:**
- Produces: `store.js` exports on `window.Store`: `state` (the last `/api/state`), `model` (`/api/model`), `views`, `ui` (`{view, filter, selection: Set, focus: id|null, open: id|null, groupBy, columns}`), `load()`, `post(url, body)`, `rows()` (filtered, sorted items), `set(patch)` (merges into `ui` and re-renders), `subscribe(fn)`.
- `rail.js` exports `window.Rail` a Preact component. `table.js` exports `window.Table`.
- Every module is a classic script that reads `preact`, `preactHooks` and `htm` globals and defines `const html = htm.bind(preact.h)`.

- [ ] **Step 1: Move the old front end**

```bash
mkdir -p console/static/old
git mv console/static/index.html console/static/old/index.html
git mv console/static/app.js console/static/old/app.js
sed -i '' 's|href="style.css"|href="../style.css"|; s|src="app.js"|src="app.js"|' console/static/old/index.html
grep -n '"/api\|fetch(' console/static/old/app.js | head -3
```

The old app fetches absolute `/api/...` paths, so it keeps working from `/old/`. `guide.html` stays where it is. Confirm `style.css` is referenced as `../style.css` in `old/index.html`.

- [ ] **Step 2: Write the new `console/static/index.html`**

```html
<!doctype html>
<html lang="en-AU">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Register console</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<link rel="stylesheet" href="style.css">
<script>try{const t=localStorage.getItem("theme");if(t==="light"||t==="dark")document.documentElement.dataset.theme=t;}catch{}</script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/preact/10.19.3/preact.umd.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/preact/10.19.3/hooks.umd.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/htm/3.1.1/htm.umd.js"></script>
</head>
<body>
<div id="root"></div>
<script src="store.js"></script>
<script src="rail.js"></script>
<script src="table.js"></script>
<script src="app.js"></script>
</body>
</html>
```

- [ ] **Step 3: Write `console/static/store.js`**

```js
// Client state for the console. One object, one subscribe, every write goes to the API and reloads state.
(function () {
  const listeners = new Set();
  const Store = {
    state: null, model: null, views: [],
    ui: { view: "all", filter: { types: [], statuses: [], scopes: [], owners: [], rule: "", since: "", q: "" },
          selection: new Set(), focus: null, open: null, groupBy: "", columns: null, madeBy: "" },
    subscribe(fn) { listeners.add(fn); return () => listeners.delete(fn); },
    emit() { listeners.forEach(fn => fn()); },
    set(patch) { Object.assign(Store.ui, patch); Store.emit(); },
    async load() {
      const [s, m, v] = await Promise.all([fetch("/api/state").then(r => r.json()), fetch("/api/model").then(r => r.json()), fetch("/api/views").then(r => r.json())]);
      Store.state = s; Store.model = m; Store.views = v.views;
      Store.byId = Object.fromEntries(s.items.map(i => [i.id, i]));
      Store.failuresById = {};
      for (const f of s.integrity.failures) (Store.failuresById[f.id] ||= []).push(f);
      Store.suggestionsById = {};
      for (const g of s.integrity.suggestions) (Store.suggestionsById[g.id] ||= []).push(g);
      try { Store.ui.madeBy = localStorage.getItem("madeBy") || Store.ui.madeBy; } catch {}
      Store.emit();
    },
    async post(url, body) {
      const r = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ madeBy: Store.ui.madeBy, ...body }) });
      const j = await r.json();
      if (!r.ok || j.error) throw new Error(j.error || r.statusText);
      return j;
    },
    // The rows the current view shows: the view's fixed filter, then the user's chips, then free text.
    rows() {
      const { filter, view } = Store.ui; const S = Store.state; if (!S) return [];
      let xs = S.items.slice();
      const fixed = Store.viewFilter(view);
      xs = xs.filter(i => fixed(i));
      if (filter.types.length) xs = xs.filter(i => filter.types.includes(i.kind));
      if (filter.statuses.length) xs = xs.filter(i => filter.statuses.includes(i.status));
      if (filter.scopes.length) xs = xs.filter(i => filter.scopes.includes(i.scope || ""));
      if (filter.owners.length) xs = xs.filter(i => filter.owners.includes(i.owner || ""));
      if (filter.rule) xs = xs.filter(i => (Store.failuresById[i.id] || []).some(f => f.rule === filter.rule));
      if (filter.since) { const d = Store.parseDate(filter.since); if (d) xs = xs.filter(i => (Store.parseDate(i.updated) || 0) >= d); }
      if (filter.q) { const q = filter.q.toLowerCase(); xs = xs.filter(i => (i.id + " " + i.title + " " + (i.notes || "")).toLowerCase().includes(q)); }
      return xs.sort((a, b) => a.id < b.id ? -1 : 1);
    },
    viewFilter(view) {
      const term = i => (Store.model.terminal[i.kind] || []).includes(i.status);
      if (view === "all") return () => true;
      if (view === "outstanding") return i => !term(i);
      if (view === "integrity") return i => (Store.failuresById[i.id] || []).length > 0;
      if (view === "supports") return i => (Store.suggestionsById[i.id] || []).length > 0;
      if (view === "duplicates") { const ids = new Set(Store.state.dupes.flatMap(g => g.ids || g)); return i => ids.has(i.id); }
      if (view === "unreviewed") { const ids = new Set(Store.state.unreviewed); return i => ids.has(i.id); }
      if (Store.model.states[view]) return i => i.kind === view;
      return () => true;
    },
    parseDate(s) {
      const m = /^(\d{1,2}) (\w+) (\d{4})/.exec(s || ""); if (!m) return null;
      const mi = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"].indexOf(m[2]);
      return mi < 0 ? null : new Date(+m[3], mi, +m[1]);
    },
    counts() {
      const S = Store.state; if (!S) return {};
      const c = { all: S.items.length, outstanding: 0, integrity: 0, supports: 0, duplicates: 0, unreviewed: S.unreviewed.length, byType: {}, byRule: {} };
      const term = i => (Store.model.terminal[i.kind] || []).includes(i.status);
      for (const i of S.items) { c.byType[i.kind] = (c.byType[i.kind] || 0) + 1; if (!term(i)) c.outstanding++; }
      c.integrity = Object.keys(Store.failuresById).length; c.supports = Object.keys(Store.suggestionsById).length;
      c.duplicates = S.dupes.length;
      for (const f of S.integrity.failures) c.byRule[f.rule] = (c.byRule[f.rule] || 0) + 1;
      return c;
    },
  };
  window.Store = Store;
})();
```

Check the shape of `state.dupes` with `curl -s localhost:8085/api/state | python3 -c "import json,sys; print(json.load(sys.stdin)['dupes'][:1])"` and fix the `flatMap` line to match (each group is either a list of ids or a dict with `ids`).

- [ ] **Step 4: Write `console/static/rail.js`**

```js
(function () {
  const html = htm.bind(preact.h);
  const ORDER = ["REQ", "CR", "DEC", "LIM", "OI", "RSK"];
  function Item({ id, label, n, on, onClick, pill }) {
    return html`<div class=${"rl-it" + (on ? " on" : "")} onClick=${onClick}>
      <span>${pill ? html`<span class=${"pill " + pill}>${pill}</span> ` : null}${label}</span>
      ${n !== undefined ? html`<span class="n">${n}</span>` : null}</div>`;
  }
  function Rail() {
    const S = Store, c = S.counts(), ui = S.ui;
    const go = (view, extra = {}) => () => S.set({ view, selection: new Set(), open: null, filter: { ...S.ui.filter, rule: "", ...extra } });
    const rules = Object.entries(c.byRule || {}).sort((a, b) => b[1] - a[1]);
    return html`<nav class="rail">
      <div class="grp"><span class="lbl">Engagement</span><div class="rl-eng">${S.state.engagement.name}</div></div>
      <div class="grp"><span class="lbl">Work</span>
        <${Item} label="Outstanding" n=${c.outstanding} on=${ui.view === "outstanding"} onClick=${go("outstanding")} />
        <${Item} label="Integrity" n=${S.state.integrity.failures.length} on=${ui.view === "integrity" && !ui.filter.rule} onClick=${go("integrity")} />
        ${ui.view === "integrity" ? rules.map(([r, n]) => html`<${Item} label=${r + " " + (S.model.rules[r] || "").split(" ").slice(0, 4).join(" ")} n=${n} on=${ui.filter.rule === r} onClick=${go("integrity", { rule: r })} />`) : null}
        <${Item} label="Suggested supports" n=${c.supports} on=${ui.view === "supports"} onClick=${go("supports")} />
        <${Item} label="Duplicates" n=${c.duplicates} on=${ui.view === "duplicates"} onClick=${go("duplicates")} />
        <${Item} label="Unreviewed" n=${c.unreviewed} on=${ui.view === "unreviewed"} onClick=${go("unreviewed")} />
      </div>
      <div class="grp"><span class="lbl">Registers</span>
        <${Item} label="All items" n=${c.all} on=${ui.view === "all"} onClick=${go("all")} />
        ${ORDER.map(k => html`<${Item} pill=${k} label=${S.model.names[k] + "s"} n=${c.byType[k] || 0} on=${ui.view === k} onClick=${go(k)} />`)}
      </div>
      <div class="grp"><span class="lbl">Reports</span>
        ${S.views.map((v, i) => html`<${Item} label=${v.name} on=${ui.view === "report:" + i} onClick=${go("report:" + i)} />`)}
      </div>
    </nav>`;
  }
  window.Rail = Rail;
})();
```

Note the plural of "Open item" reads "Open items" and "Change request" reads "Change requests"; "Risk" reads "Risks". All six names pluralise with an "s".

- [ ] **Step 5: Write `console/static/table.js` (read only for now)**

```js
(function () {
  const html = htm.bind(preact.h);
  const DEFAULT_COLS = ["id", "title", "status", "scope", "owner", "links", "issues"];
  function label(k) { return { id: "Id", title: "Title", links: "Links", issues: "Issues" }[k] || Store.model.labels[k] || k; }
  function cell(i, k) {
    if (k === "id") return html`<span class=${"pill " + i.kind}>${i.id}</span>`;
    if (k === "status") return html`<span class="st">${i.status}</span>`;
    if (k === "links") return html`<span class="mono muted">${i.links.length || "—"}</span>`;
    if (k === "issues") { const n = (Store.failuresById[i.id] || []).length; return n ? html`<span class="warn"></span> ${n}` : html`<span class="muted">—</span>`; }
    const v = i[k]; return v ? v : html`<span class="muted">—</span>`;
  }
  function Chip({ label, value, onClear }) {
    return html`<span class="chip">${label} ${value ? html`<b>${value}</b>` : null}${onClear ? html`<span class="x" onClick=${onClear}>×</span>` : null}</span>`;
  }
  function Table() {
    const S = Store, ui = S.ui, rows = S.rows();
    const cols = ui.columns || DEFAULT_COLS;
    const f = ui.filter;
    const setF = patch => S.set({ filter: { ...f, ...patch } });
    const title = ui.view === "all" ? "All items" : S.model.names[ui.view] ? S.model.names[ui.view] + "s" : ui.view[0].toUpperCase() + ui.view.slice(1);
    return html`<div class="main-col">
      <div class="bar top"><span class="h2">${title}</span><span class="muted">${rows.length}</span><div class="sp"></div>
        <input class="inp search" placeholder="Search title, id, notes" value=${f.q} onInput=${e => setF({ q: e.target.value })} /></div>
      <div class="bar chips">
        ${f.types.length ? html`<${Chip} label="Type" value=${f.types.join(", ")} onClear=${() => setF({ types: [] })} />` : null}
        ${f.statuses.length ? html`<${Chip} label="Status" value=${f.statuses.join(", ")} onClear=${() => setF({ statuses: [] })} />` : null}
        ${f.scopes.length ? html`<${Chip} label="Scope" value=${f.scopes.join(", ")} onClear=${() => setF({ scopes: [] })} />` : null}
        ${f.owners.length ? html`<${Chip} label="Owner" value=${f.owners.join(", ")} onClear=${() => setF({ owners: [] })} />` : null}
        ${f.rule ? html`<${Chip} label="Failing" value=${f.rule} onClear=${() => setF({ rule: "" })} />` : null}
        <${FilterAdd} setF=${setF} f=${f} />
      </div>
      <div class="tbl-wrap"><table>
        <thead><tr>${cols.map(k => html`<th class=${"c-" + k}>${label(k)}</th>`)}</tr></thead>
        <tbody>${rows.map(i => html`<tr key=${i.id} class=${ui.focus === i.id ? "focus" : ""} onClick=${() => S.set({ focus: i.id })}>
          ${cols.map(k => html`<td class=${"c-" + k}>${cell(i, k)}</td>`)}</tr>`)}</tbody>
      </table></div>
      <div class="bar foot muted">${rows.length} of ${S.state.items.length} · j/k move · Enter opens · / search</div>
    </div>`;
  }
  // One "+ Filter" control: pick a facet, then a value from what the data holds.
  function FilterAdd({ setF, f }) {
    const [facet, setFacet] = preactHooks.useState("");
    const S = Store;
    const values = { types: Object.keys(S.model.names), statuses: [...new Set(S.state.items.map(i => i.status))].sort(),
                     scopes: S.model.scopes, owners: S.model.owners, rule: Object.keys(S.counts().byRule).sort() };
    if (!facet) return html`<select class="chip add" value="" onChange=${e => setFacet(e.target.value)}>
      <option value="">+ Filter</option><option value="types">Type</option><option value="statuses">Status</option>
      <option value="scopes">Scope</option><option value="owners">Owner</option><option value="rule">Failing rule</option></select>`;
    return html`<select class="chip add" value="" onChange=${e => { const v = e.target.value; setFacet(""); if (!v) return;
        facet === "rule" ? setF({ rule: v }) : setF({ [facet]: [...new Set([...f[facet], v])] }); }}>
      <option value="">${label(facet)}…</option>${values[facet].map(v => html`<option value=${v}>${v}</option>`)}</select>`;
  }
  window.Table = Table;
})();
```

- [ ] **Step 6: Write `console/static/app.js`**

```js
(function () {
  const html = htm.bind(preact.h);
  function App() {
    const [, tick] = preactHooks.useState(0);
    preactHooks.useEffect(() => Store.subscribe(() => tick(n => n + 1)), []);
    if (!Store.state) return html`<div class="loading">Loading the registers…</div>`;
    return html`<div class="layout2">
      <${Rail} />
      <${Table} />
    </div>`;
  }
  async function boot(retries = 20) {
    try { await Store.load(); }
    catch (e) { if (retries > 0) return setTimeout(() => boot(retries - 1), 500); document.getElementById("root").textContent = "The console could not load: " + e.message; return; }
    preact.render(html`<${App} />`, document.getElementById("root"));
  }
  document.addEventListener("keydown", e => {
    if (["INPUT", "TEXTAREA", "SELECT"].includes(e.target.tagName)) return;
    const rows = Store.rows(); const at = rows.findIndex(r => r.id === Store.ui.focus);
    if (e.key === "j") Store.set({ focus: rows[Math.min(at + 1, rows.length - 1)]?.id || null });
    if (e.key === "k") Store.set({ focus: rows[Math.max(at - 1, 0)]?.id || null });
    if (e.key === "/") { e.preventDefault(); document.querySelector(".search")?.focus(); }
    if (e.key === "Escape") Store.set({ open: null, selection: new Set() });
  });
  boot();
})();
```

- [ ] **Step 7: Append to `console/static/style.css`**

```css
/* Rethink shell */
.layout2{display:flex;min-height:100vh}
.rail{width:220px;flex:none;background:var(--bg);border-right:1px solid var(--line);padding:16px 10px;box-sizing:border-box;display:flex;flex-direction:column;gap:18px;position:sticky;top:0;height:100vh;overflow:auto}
.rail .lbl{font-family:var(--mono);font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--ink-3);padding:0 10px 6px;display:block}
.rail .rl-eng{padding:2px 10px;font-weight:600}
.rl-it{display:flex;justify-content:space-between;align-items:center;padding:6px 10px;border-radius:6px;color:var(--ink-2);cursor:pointer}
.rl-it:hover{background:var(--surface)}
.rl-it.on{background:var(--surface);color:var(--ink);font-weight:500;box-shadow:0 0 0 1px var(--line)}
.rl-it .n{font-family:var(--mono);font-size:11px;color:var(--ink-3)}
.main-col{flex:1;min-width:0;display:flex;flex-direction:column;background:var(--surface)}
.bar{display:flex;align-items:center;gap:8px;padding:10px 20px;border-bottom:1px solid var(--line)}
.bar.top{padding:12px 20px}.bar.foot{border-bottom:0;border-top:1px solid var(--line);font-size:12px;margin-top:auto}
.bar .sp{flex:1}
.h2{font-size:15px;font-weight:600;letter-spacing:-.01em}
.inp{border:1px solid var(--line);border-radius:6px;padding:7px 10px;background:var(--surface);font:inherit;color:var(--ink)}
.inp.search{width:260px}
.chip{display:inline-flex;align-items:center;gap:6px;padding:4px 10px;border-radius:6px;border:1px solid var(--line);background:var(--surface);font-size:12px;color:var(--ink-2)}
.chip b{font-weight:500;color:var(--ink)}.chip .x{cursor:pointer;color:var(--ink-3)}
select.chip.add{border-style:dashed;color:var(--ink-3);font:inherit;font-size:12px}
.pill{display:inline-block;font-family:var(--mono);font-size:11px;padding:1px 6px;border-radius:4px;white-space:nowrap}
.pill.REQ{color:var(--req);background:var(--req-bg)}.pill.LIM{color:var(--lim);background:var(--lim-bg)}.pill.DEC{color:var(--dec);background:var(--dec-bg)}
.pill.RSK{color:var(--rsk);background:var(--rsk-bg)}.pill.OI{color:var(--oi);background:var(--oi-bg)}.pill.CR{color:var(--cr);background:var(--cr-bg)}
.st{display:inline-block;font-size:12px;padding:1px 8px;border-radius:10px;border:1px solid var(--line);color:var(--ink-2);background:var(--surface);white-space:nowrap}
.tbl-wrap{flex:1;overflow:auto}
.tbl-wrap table{border-collapse:collapse;width:100%;font-size:13px}
.tbl-wrap th{text-align:left;font-weight:500;color:var(--ink-3);font-size:12px;padding:8px 10px;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--surface)}
.tbl-wrap td{padding:8px 10px;border-bottom:1px solid var(--line-2);vertical-align:middle}
.tbl-wrap tr.focus td{box-shadow:inset 3px 0 0 var(--req)}
.tbl-wrap tr.sel td{background:var(--req-bg)}
.c-id{width:90px}.c-status{width:120px}.c-scope{width:150px}.c-owner{width:130px}.c-links,.c-issues{width:70px}
.warn{display:inline-block;width:6px;height:6px;border-radius:3px;background:var(--bad)}
.muted{color:var(--ink-3)}.mono{font-family:var(--mono)}
.loading{padding:40px;color:var(--ink-3)}
```

Check that `--line-2` and `--ink-2` exist in `:root` (they do in the dark blocks; confirm the light block has them with `sed -n '1,8p' console/static/style.css` and add `--ink-2:#3a4354;--ink-3:#7f889a;--line-2:#e9ecf1` to the light `:root` if missing).

- [ ] **Step 8: Serve `/old/`**

`SimpleHTTPRequestHandler` already serves any file under `static/`, so `/old/index.html` works as is. Make `/old/` (trailing slash) resolve: in `do_GET`, after the `if p == "/":` line, add:

```python
        if p == "/old/":
            self.path = "/old/index.html"
```

- [ ] **Step 9: Check in the browser**

```bash
make reload; sleep 2; curl -s -o /dev/null -w "%{http_code}\n" localhost:8085/ ; curl -s localhost:8085/store.js | head -2
```

Open `http://localtest.me:8085/` in Chrome. Expected: the rail with counts matching `/api/state`, the All items table, clicking a rail entry filters, `+ Filter` adds a chip, `j`/`k` move the focus stripe, `/` focuses search. Open `http://localtest.me:8085/old/` and confirm the previous console still renders. Read the console log for errors with the Chrome tools.

- [ ] **Step 10: Commit**

```bash
git add console/static console/server.py
git commit -m "Console shell: Preact table with rail and filters; previous front end kept at /old/

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 8: Side panel, read only

**Files:**
- Create: `console/static/panel.js`
- Modify: `console/static/index.html` (script tag), `console/static/app.js` (mount, Enter key), `console/static/style.css`

**Interfaces:**
- Produces: `window.Panel` component reading `Store.ui.open`. `Store.set({open: id})` opens it. Up and down arrows step through `Store.rows()`.

- [ ] **Step 1: Write `console/static/panel.js`**

```js
(function () {
  const html = htm.bind(preact.h);
  function Hop({ h, word }) {
    return html`<div class="hop"><span class=${"pill " + h.kind}>${h.id}</span><span class="t" onClick=${() => Store.set({ open: h.id, focus: h.id })}>${h.title}</span><span class="st">${h.status}</span></div>`;
  }
  function Panel() {
    const S = Store, id = S.ui.open, i = S.byId[id];
    if (!i) return null;
    const rows = S.rows(); const at = rows.findIndex(r => r.id === id);
    const prov = S.state.provenance[id] || { back: [], forward: [], dangling: [] };
    const fails = S.failuresById[id] || [], sugg = S.suggestionsById[id] || [];
    const moves = S.model.transitions[i.kind]?.[i.status] || [];
    const needs = to => S.model.required[i.kind]?.[to] || [];
    const need = to => needs(to).map(f => f.startsWith("link:") ? "link " + f.slice(5) : S.model.labels[f] || f).join(", ");
    const short = S.model.short[i.kind].filter(k => k !== "scope"), long = S.model.long[i.kind];
    // Words a later state will need, drawn as dashed slots in the forward column.
    const later = Object.entries(S.model.required[i.kind] || {}).flatMap(([st, fs]) => fs.filter(f => f.startsWith("link:")).map(f => ({ st, word: f.slice(5).split(":")[0] })))
      .filter(x => S.model.forward[i.kind].includes(x.word) && !i.links.some(l => l.toLowerCase().startsWith(x.word)));
    return html`<aside class="panel">
      <div class="bar top"><span class=${"pill " + i.kind}>${i.id}</span><span class="muted small">${at + 1} of ${rows.length} · ↑↓ to step</span><div class="sp"></div>
        <button class="btn ghost" onClick=${() => S.set({ open: null })}>Esc ✕</button></div>
      <div class="panel-body">
        <div class="panel-main">
          <div class="ttl">${i.title}</div>
          <div class="chips"><span class="st on">${i.status}</span>
            ${i.scope ? html`<span class="chip">Scope <b>${i.scope}</b></span>` : null}
            ${short.map(k => i[k] ? html`<span class="chip">${S.model.labels[k] || k} <b>${i[k]}</b></span>` : null)}</div>
          <div class="card"><div class="h3">Next moves</div><div class="moves">
            ${moves.map(to => html`<span class="btn">${to}${need(to) ? html` <span class="muted">needs ${need(to)}</span>` : null}</span>`)}
            ${!moves.length ? html`<span class="muted">${i.status} is terminal.</span>` : null}</div></div>
          ${long.map(k => i[k] ? html`<div class="sec"><div class="h3">${S.model.labels[k] || k}</div><p>${i[k]}</p></div>` : null)}
          ${i.links.length ? html`<div class="sec"><div class="h3">Links</div>${i.links.map(l => html`<div class="mono small">${l}</div>`)}</div>` : null}
          ${i.history?.length ? html`<div class="sec"><div class="h3">History</div>${i.history.slice().reverse().map(h => html`<div class="mono small muted">${h}</div>`)}</div>` : null}
        </div>
        <div class="panel-side">
          <div class="h3">Where it came from</div>
          ${prov.back.length ? prov.back.map(h => html`<${Hop} h=${h} />`) : html`<div class="muted small">Nothing links back.</div>`}
          <div class="hop cur"><span class=${"pill " + i.kind}>${i.id}</span><span class="t">This item</span></div>
          <div class="h3">What it produces</div>
          ${prov.forward.map(h => html`<div class="word">${h.word}</div><${Hop} h=${h} />`)}
          ${later.map(x => html`<div class="hop slot"><span class="muted small">${x.word} · none yet, needed for ${x.st}</span></div>`)}
          ${prov.dangling.map(l => html`<div class="hop slot bad"><span class="small">${l} · target not found</span></div>`)}
          <div class="h3">Gaps</div>
          ${fails.map(f => html`<div class="gap"><span class="warn"></span><span class="small">${f.rule} · ${f.text}</span></div>`)}
          ${sugg.map(s => html`<div class="gap"><span class="warn amber"></span><span class="small">${s.rule} · ${s.text || s.prompt || "support suggested"}</span></div>`)}
          ${!fails.length && !sugg.length ? html`<div class="muted small">None.</div>` : null}
        </div>
      </div>
    </aside>`;
  }
  window.Panel = Panel;
})();
```

Check the suggestion dict's text field name with `curl -s localhost:8085/api/state | python3 -c "import json,sys; print(json.load(sys.stdin)['integrity']['suggestions'][:1])"` and use that key in the `sugg.map` line.

- [ ] **Step 2: Mount and wire keys in `app.js`**

In `App`, change the layout to `html\`<div class="layout2"><${Rail} /><${Table} />${Store.ui.open ? html\`<${Panel} />\` : null}</div>\``. In the keydown handler add:

```js
    if (e.key === "Enter" && Store.ui.focus) Store.set({ open: Store.ui.focus });
    if (Store.ui.open && (e.key === "ArrowDown" || e.key === "ArrowUp")) {
      e.preventDefault(); const n = rows[e.key === "ArrowDown" ? Math.min(at + 1, rows.length - 1) : Math.max(at - 1, 0)];
      if (n) Store.set({ open: n.id, focus: n.id });
    }
```

where `at` is computed against `Store.ui.open` when the panel is open: change the `at` line to `const cur = Store.ui.open || Store.ui.focus; const at = rows.findIndex(r => r.id === cur);`.

In `table.js`, make the id cell open the panel: `if (k === "id") return html\`<span class=${"pill " + i.kind + " lnk"} onClick=${e => { e.stopPropagation(); Store.set({ open: i.id, focus: i.id }); }}>${i.id}</span>\`;`

Add `<script src="panel.js"></script>` before `app.js` in `index.html`.

- [ ] **Step 3: Style**

Append to `style.css`:

```css
.panel{position:fixed;top:0;right:0;bottom:0;width:760px;max-width:80vw;background:var(--surface);border-left:1px solid var(--line);box-shadow:-16px 0 40px rgba(28,34,48,.10);display:flex;flex-direction:column;z-index:5}
.panel-body{flex:1;display:grid;grid-template-columns:minmax(0,1fr) 300px;min-height:0}
.panel-main{padding:20px 22px;overflow:auto;display:flex;flex-direction:column;gap:18px}
.panel-side{border-left:1px solid var(--line);padding:20px 16px;overflow:auto;display:flex;flex-direction:column;gap:8px}
.ttl{font-size:18px;font-weight:600;letter-spacing:-.015em;line-height:1.25}
.chips{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.card{border:1px solid var(--line);border-radius:8px;padding:12px 14px;display:flex;flex-direction:column;gap:8px}
.h3{font-size:13px;font-weight:600}.h3+.h3{margin-top:10px}
.moves{display:flex;gap:8px;flex-wrap:wrap}
.btn{display:inline-flex;align-items:center;gap:6px;padding:6px 12px;border-radius:6px;border:1px solid var(--line);background:var(--surface);color:var(--ink);font:inherit;font-weight:500;cursor:pointer}
.btn.pri{background:var(--ink);color:var(--surface);border-color:var(--ink)}.btn.ghost{border-color:transparent;background:transparent;color:var(--ink-2)}
.btn.danger{color:var(--bad)}
.sec p{margin:4px 0 0;max-width:640px;white-space:pre-line}
.small{font-size:12px}
.hop{display:flex;gap:8px;align-items:center;border:1px solid var(--line);border-radius:8px;padding:8px 10px}
.hop .t{flex:1;font-size:12px;cursor:pointer}.hop.cur{border-color:var(--ink);font-weight:500}
.hop.slot{border-style:dashed}.hop.slot.bad{border-color:var(--bad)}
.word{font-size:11px;color:var(--ink-3);padding-left:14px}
.gap{display:flex;gap:8px;align-items:flex-start}.gap .warn{margin-top:6px;flex:none}.warn.amber{background:var(--oi)}
.st.on{border-color:var(--ink)}
.lnk{cursor:pointer}
```

- [ ] **Step 4: Check in the browser**

`make reload; sleep 2`, open `http://localtest.me:8085/`, click an id. Expected: the panel with title, chips, next moves and their needs, long fields, links, History, the provenance columns with real neighbours from the test engagement (CR-0001 in `engagements/test` has a triggered by link; use that), gaps. Up and down step. Esc closes. A dangling link shows as a red dashed slot.

- [ ] **Step 5: Commit**

```bash
git add console/static
git commit -m "Side panel: fields, next moves, provenance chain and gaps, read only

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 9: Inline cells and the single-item move form

**Files:**
- Create: `console/static/cells.js`, `console/static/move-form.js`
- Modify: `console/static/table.js`, `console/static/panel.js`, `console/static/app.js`, `console/static/index.html`, `console/static/style.css`

**Interfaces:**
- Produces: `window.Cells.Editor({item, field, onDone})` renders the right editor for a field and writes through `Store.post("/api/edit", ...)`. `window.Cells.StatusCell({item})` renders the status pill and its dropdown. `window.MoveForm.open({ids, to})` sets `Store.ui.move = {ids, to}`; `window.MoveForm.Form` renders it; `Store.ui.move = null` closes it. `Store.ui.madeBy` must be set before any write; the form asks for it inline when empty.

- [ ] **Step 1: Write `console/static/cells.js`**

```js
(function () {
  const html = htm.bind(preact.h);
  const { useState, useEffect, useRef } = preactHooks;
  const CHOICE_FIELDS = k => Store.model.choices[k] || (k === "scope" ? Store.model.scopes : k === "phase" ? Store.model.phases : k === "owner" ? Store.model.owners : null);
  async function write(item, field, value) {
    try { await Store.post("/api/edit", { id: item.id, fields: { [Store.model.labels[field] || field]: value }, gist: `${Store.model.labels[field] || field} set` }); await Store.load(); }
    catch (e) { Store.toast(e.message); }
  }
  // Text, date and choice editors. Saves on blur or Enter; Esc abandons.
  function Editor({ item, field, onDone, long }) {
    const [v, setV] = useState(item[field] || ""); const ref = useRef();
    useEffect(() => { ref.current?.focus(); ref.current?.select?.(); }, []);
    const done = async save => { if (save && v !== (item[field] || "")) await write(item, field, v); onDone(); };
    const opts = CHOICE_FIELDS(field);
    if (opts && opts.length && !long) return html`<select ref=${ref} class="inp cell" value=${v} onChange=${e => { setV(e.target.value); write(item, field, e.target.value).then(onDone); }} onBlur=${() => onDone()}>
      <option value="">—</option>${opts.map(o => html`<option value=${o}>${o}</option>`)}${v && !opts.includes(v) ? html`<option value=${v}>${v}</option>` : null}</select>`;
    if (long) return html`<textarea ref=${ref} class="inp cell long" value=${v} onInput=${e => setV(e.target.value)} onBlur=${() => done(true)}
      onKeyDown=${e => { if (e.key === "Escape") done(false); if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) done(true); }} />`;
    return html`<input ref=${ref} class="inp cell" value=${v} onInput=${e => setV(e.target.value)} onBlur=${() => done(true)}
      onKeyDown=${e => { if (e.key === "Escape") done(false); if (e.key === "Enter") done(true); }} />`;
  }
  // The status pill. Click lists every state for the type: reachable ones say what they need, others are greyed.
  function StatusCell({ item }) {
    const [open, setOpen] = useState(false);
    const S = Store, m = S.model, can = m.transitions[item.kind]?.[item.status] || [];
    const need = to => (m.required[item.kind]?.[to] || []).map(f => f.startsWith("link:") ? "link " + f.slice(5) : m.labels[f] || f);
    const pick = to => { setOpen(false); MoveForm.open({ ids: [item.id], to }); };
    return html`<span class="stwrap"><span class=${"st lnk" + (open ? " on" : "")} onClick=${e => { e.stopPropagation(); setOpen(!open); }}>${item.status} ▾</span>
      ${open ? html`<div class="menu" onClick=${e => e.stopPropagation()}>
        ${m.states[item.kind].filter(s => s !== item.status).map(s => can.includes(s)
          ? html`<div class="mi" onClick=${() => pick(s)}><span>${s}</span><span class="muted">${need(s).length ? "needs " + need(s).join(", ") : "ready"}</span></div>`
          : html`<div class="mi off"><span>${s}</span><span>not from ${item.status}</span></div>`)}
      </div>` : null}</span>`;
  }
  window.Cells = { Editor, StatusCell, write };
  Store.toast = msg => { const t = document.getElementById("toast") || Object.assign(document.body.appendChild(document.createElement("div")), { id: "toast", className: "toast" }); t.textContent = msg; t.hidden = false; clearTimeout(t._h); t._h = setTimeout(() => t.hidden = true, 4000); };
})();
```

- [ ] **Step 2: Write `console/static/move-form.js`**

```js
(function () {
  const html = htm.bind(preact.h);
  const { useState, useEffect } = preactHooks;
  const MoveForm = {
    open({ ids, to }) { Store.set({ move: { ids, to } }); },
    close() { Store.set({ move: null }); },
  };
  // Field keys behind a needs label, so a shared input can be drawn for each missing thing.
  function keyFor(kind, to, label) {
    const m = Store.model;
    for (const f of m.required[kind]?.[to] || []) {
      if (f.startsWith("link:")) { if (label.startsWith("Links: " + f.slice(5))) return { link: f.slice(5).split(":")[0] }; continue; }
      if ((m.labels[f] || f) === label || (f === "options" && label.startsWith("Options"))) return { field: f };
    }
    for (const sp of m.specials) if (sp.kind === kind && sp.state === to && sp.text === label) return { field: sp.field, prefix: sp.value };
    return { field: label.toLowerCase() };
  }
  function Form() {
    const S = Store, mv = S.ui.move; if (!mv) return null;
    const items = mv.ids.map(id => S.byId[id]).filter(Boolean);
    const [needs, setNeeds] = useState(null), [fields, setFields] = useState({}), [per, setPer] = useState({}), [note, setNote] = useState(""), [busy, setBusy] = useState(false), [err, setErr] = useState("");
    const kinds = [...new Set(items.map(i => i.kind))];
    useEffect(() => { S.post("/api/needs", { ids: mv.ids, to: mv.to, fields: {} }).then(r => setNeeds(r.needs)).catch(e => setErr(e.message)); }, [mv.ids.join(","), mv.to]);
    if (!needs) return html`<div class="modal"><div class="dlg"><div class="muted">Checking what ${mv.to} needs…</div></div></div>`;
    // Shared: a label missing on every item of the same kind. Per item: the rest.
    const missing = id => (needs[id]?.missing || []).filter(x => !x.includes("not an allowed move"));
    const shared = kinds.length === 1 ? missing(items[0].id).filter(l => items.every(i => missing(i.id).includes(l))) : [];
    const blocked = items.filter(i => needs[i.id] && !needs[i.id].ok && (needs[i.id].missing || []).some(x => x.includes("not an allowed move")));
    const labelKind = kinds.length === 1 ? S.model.names[kinds[0]].toLowerCase() + (items.length > 1 ? "s" : "") : "items";
    const value = (id, label) => per[id]?.[label] ?? fields[label] ?? "";
    const ready = !blocked.length && items.every(i => missing(i.id).every(l => String(value(i.id, l)).trim()));
    const apply = async () => {
      setBusy(true); setErr("");
      try {
        if (!S.ui.madeBy.trim()) throw new Error("Say who you are first (Made by).");
        if (items.length === 1) {
          const i = items[0], f = {};
          for (const l of missing(i.id)) { const k = keyFor(i.kind, mv.to, l); if (k.field) f[S.model.labels[k.field] || k.field] = value(i.id, l); }
          const links = missing(i.id).map(l => keyFor(i.kind, mv.to, l)).filter(k => k.link).map(k => k.link + " " + value(items[0].id, "Links: " + k.link + " …"));
          await S.post("/api/transition", { id: i.id, to: mv.to, fields: f, links, gist: note });
        } else {
          const f = {}; for (const l of shared) { const k = keyFor(kinds[0], mv.to, l); if (k.field) f[S.model.labels[k.field] || k.field] = fields[l]; }
          // Per-item gaps first, as single edits, then the shared move in one bulk call.
          for (const i of items) for (const l of missing(i.id)) if (!shared.includes(l) && per[i.id]?.[l]) {
            const k = keyFor(i.kind, mv.to, l); if (k.field) await S.post("/api/edit", { id: i.id, fields: { [S.model.labels[k.field] || k.field]: per[i.id][l] }, gist: "set before " + mv.to });
          }
          const r = await S.post("/api/bulk", { ids: items.map(i => i.id), op: "transition", to: mv.to, fields: f, gist: note });
          if (r.failed) throw new Error(`Wrote ${r.written.length}; stopped at ${r.failed.id}: ${r.failed.error}`);
        }
        await S.load(); MoveForm.close();
      } catch (e) { setErr(e.message); await S.load(); }
      setBusy(false);
    };
    const input = (label, get, set) => {
      const k = keyFor(kinds[0], mv.to, label);
      const opts = k.field && (S.model.choices[k.field] || (k.field === "scope" ? S.model.scopes : k.field === "phase" ? S.model.phases : k.field === "owner" ? S.model.owners : null));
      if (k.link) return html`<${Picker.Inline} word=${k.link} kind=${kinds[0]} value=${get()} onPick=${set} />`;
      if (opts && opts.length) return html`<select class="inp" value=${get()} onChange=${e => set(e.target.value)}><option value="">—</option>${opts.map(o => html`<option value=${o}>${o}</option>`)}</select>`;
      if (k.field && S.model.long[kinds[0]].includes(k.field)) return html`<textarea class="inp" value=${get()} onInput=${e => set(e.target.value)} />`;
      return html`<input class="inp" value=${get()} onInput=${e => set(e.target.value)} placeholder=${k.prefix || ""} />`;
    };
    return html`<div class="modal" onClick=${MoveForm.close}><div class="dlg" onClick=${e => e.stopPropagation()}>
      <div class="dlg-h"><span class="h2">Move ${items.length} ${labelKind} to ${mv.to}</span>
        <span class="muted small">${shared.length ? "Shared: " + shared.join(", ") + "." : "Nothing shared to ask."}</span></div>
      <div class="dlg-b">
        ${!S.ui.madeBy ? html`<div class="field"><label>Made by</label><input class="inp" value=${S.ui.madeBy} onInput=${e => { S.ui.madeBy = e.target.value; try { localStorage.setItem("madeBy", e.target.value); } catch {} }} /></div>` : null}
        ${shared.length ? html`<div class="grid2">${shared.map(l => html`<div class="field"><label>${l} · required for ${mv.to}</label>${input(l, () => fields[l] || "", v => setFields({ ...fields, [l]: v }))}</div>`)}</div>` : null}
        <div class="field"><label>Per item</label><div class="card tight">
          ${items.map(i => html`<div class="prow"><span class=${"pill " + i.kind}>${i.id}</span><span class="small">${needs[i.id]?.from} → ${mv.to}</span>
            ${blocked.includes(i) ? html`<span class="miss small">${needs[i.id].missing[0]}</span>` : null}
            ${missing(i.id).filter(l => !shared.includes(l)).map(l => html`<span class="miss small">${l}</span>${input(l, () => per[i.id]?.[l] || "", v => setPer({ ...per, [i.id]: { ...(per[i.id] || {}), [l]: v } }))}`)}
            ${!blocked.includes(i) && !missing(i.id).filter(l => !shared.includes(l)).length ? html`<span class="muted small">ready</span>` : null}</div>`)}
        </div></div>
        <div class="field"><label>History note · applied to each item</label><input class="inp" value=${note} onInput=${e => setNote(e.target.value)} /></div>
        ${err ? html`<div class="miss">${err}</div>` : null}
      </div>
      <div class="dlg-f"><span class="muted small">Writes ${items.length} file${items.length === 1 ? "" : "s"}, stamps updated, appends History</span><div class="sp"></div>
        <button class="btn" onClick=${MoveForm.close}>Cancel</button><button class="btn pri" disabled=${!ready || busy} onClick=${apply}>Apply to ${items.length}</button></div>
    </div></div>`;
  }
  MoveForm.Form = Form;
  window.MoveForm = MoveForm;
})();
```

`Picker.Inline` is written in Task 10. Until then a link need shows a plain input: add at the top of `move-form.js` `window.Picker = window.Picker || { Inline: ({ value, onPick }) => html\`<input class="inp" value=${value} onInput=${e => onPick(e.target.value)} placeholder="ID-nnnn" />\` };` and leave it there; Task 10 replaces the object.

- [ ] **Step 3: Wire cells into the table and panel**

In `table.js`, replace `cell()` with an editing-aware version:

```js
  function Cell({ i, k }) {
    const [edit, setEdit] = preactHooks.useState(false);
    if (k === "id") return html`<span class=${"pill " + i.kind + " lnk"} onClick=${e => { e.stopPropagation(); Store.set({ open: i.id, focus: i.id }); }}>${i.id}</span>`;
    if (k === "status") return html`<${Cells.StatusCell} item=${i} />`;
    if (k === "links") return html`<span class="mono muted">${i.links.length || "—"}</span>`;
    if (k === "issues") { const n = (Store.failuresById[i.id] || []).length; return n ? html`<span class="warn"></span> ${n}` : html`<span class="muted">—</span>`; }
    if (edit) return html`<${Cells.Editor} item=${i} field=${k} onDone=${() => setEdit(false)} />`;
    const v = i[k];
    return html`<span class="ed" onClick=${e => { e.stopPropagation(); setEdit(true); }}>${v ? v : html`<span class="muted">—</span>`}</span>`;
  }
```

and in the row render use `html\`<td class=${"c-" + k}><${Cell} i=${i} k=${k} /></td>\``. Add `e` key handling in `app.js`: `if (e.key === "e" && Store.ui.focus) document.querySelector("tr.focus .c-title .ed")?.click();` and `if (e.key === "m" && Store.ui.focus) document.querySelector("tr.focus .st")?.click();`.

In `panel.js`, make the title an editor: replace `<div class="ttl">${i.title}</div>` with a component that toggles `Cells.Editor` for `title` on click, the same shape as `Cell` above with class `ttl ed`. Make each chip in `.chips` toggle an editor for its field on click, and render every `short` field, empty ones as `<span class="chip muted">Label —</span>`, so an empty field can be filled from the panel. Make each long field's `<p>` open `Cells.Editor` with `long` set. Make each Next moves button call `MoveForm.open({ ids: [i.id], to })`.

In `app.js` `App`, render `<${MoveForm.Form} />` after the panel. Add `cells.js` and `move-form.js` script tags before `panel.js` in `index.html`. Add a `Made by` input to the top bar of the table (right of search) bound to `Store.ui.madeBy` and `localStorage`, so the name is set once per browser.

- [ ] **Step 4: Style**

```css
.stwrap{position:relative}
.menu{position:absolute;top:26px;left:0;min-width:240px;background:var(--surface);border:1px solid var(--line);border-radius:8px;box-shadow:0 8px 24px rgba(28,34,48,.14);padding:6px;z-index:6;font-size:12px}
.mi{padding:5px 8px;display:flex;justify-content:space-between;gap:12px;border-radius:5px;cursor:pointer}.mi:hover{background:var(--bg)}.mi.off{color:var(--ink-3);cursor:default}
.ed{cursor:text;display:block;min-height:1em}.ed:hover{box-shadow:inset 0 -1px 0 var(--line)}
.inp.cell{width:100%;box-sizing:border-box;padding:3px 8px;font-size:13px}.inp.cell.long{min-height:80px}
.modal{position:fixed;inset:0;background:rgba(28,34,48,.25);display:flex;align-items:flex-start;justify-content:center;padding-top:60px;z-index:10}
.dlg{width:600px;max-width:92vw;background:var(--surface);border:1px solid var(--line);border-radius:8px;box-shadow:0 12px 40px rgba(28,34,48,.12);max-height:80vh;display:flex;flex-direction:column}
.dlg-h{padding:18px 22px;border-bottom:1px solid var(--line-2);display:flex;flex-direction:column;gap:4px}
.dlg-b{padding:18px 22px;display:flex;flex-direction:column;gap:16px;overflow:auto}
.dlg-f{padding:14px 22px;border-top:1px solid var(--line-2);display:flex;gap:8px;align-items:center}
.grid2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.field{display:flex;flex-direction:column;gap:4px}.field label{font-size:12px;color:var(--ink-3)}
.card.tight{padding:0;gap:0}.prow{display:flex;gap:10px;align-items:center;padding:8px 10px;border-bottom:1px solid var(--line-2);flex-wrap:wrap}.prow:last-child{border-bottom:0}
.prow .inp{padding:3px 8px;font-size:12px;max-width:200px}
.miss{color:var(--bad)}
.toast{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:var(--ink);color:var(--surface);padding:8px 14px;border-radius:6px;z-index:20}
```

- [ ] **Step 5: Check in the browser**

`make reload; sleep 2`. On `engagements/test` (set `ENG` to it in the Makefile if the console is on the sample): set Made by, click a title cell and change it, Enter, confirm the file changed with `git -C engagements/test diff --stat`. Click a status pill: unreachable states are grey, reachable ones name their needs; pick one that needs a field, the form opens with that field, Apply, the row moves. Open the panel and edit a chip. Errors surface in the toast.

- [ ] **Step 6: Commit**

```bash
git add console/static
git commit -m "Inline cells, status dropdown and the generated move form for one item

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 10: Picker, Link to and New item

**Files:**
- Create: `console/static/picker.js`
- Modify: `console/static/move-form.js` (remove the stand-in Picker), `console/static/panel.js` (Link to button), `console/static/table.js` (New item button), `console/static/index.html`

**Interfaces:**
- Produces: `window.Picker.Inline({word, kind, value, onPick})` a search input listing `/api/items` results filtered to the types `Store.model.linkWords[kind][word]` allows (`CLAIM` and `ANY` mean no filter; `A|B` means either), with a Create new row at the bottom that opens the create form prefilled. `window.Picker.LinkTo({item})` a dialog: choose a link word, pick a target, Apply writes through `/api/edit` with `links`. `window.CreateForm.open({kind, prefill, onCreated})` opens the create dialog for a type, drawn from `Store.model.create[kind]`.

- [ ] **Step 1: Write `console/static/picker.js`**

```js
(function () {
  const html = htm.bind(preact.h);
  const { useState, useEffect } = preactHooks;
  function typesFor(kind, word) {
    const t = Store.model.linkWords[kind]?.[word] || "ANY";
    return ["ANY", "CLAIM"].includes(t) ? [] : t.split("|");
  }
  function Inline({ word, kind, value, onPick }) {
    const [q, setQ] = useState(value || ""), [hits, setHits] = useState([]), [open, setOpen] = useState(false);
    const types = typesFor(kind, word);
    useEffect(() => { if (!open) return; const u = `/api/items?q=${encodeURIComponent(q)}&types=${types.join(",")}`; fetch(u).then(r => r.json()).then(j => setHits(j.items)); }, [q, open]);
    return html`<span class="pkwrap"><input class="inp" value=${q} placeholder=${"pick " + (types.join(" or ") || "an item")} onFocus=${() => setOpen(true)} onInput=${e => { setQ(e.target.value); onPick(e.target.value); }} onBlur=${() => setTimeout(() => setOpen(false), 150)} />
      ${open ? html`<div class="menu pk">
        ${hits.map(h => html`<div class="mi" onMouseDown=${() => { onPick(h.id); setQ(h.id); setOpen(false); }}><span><span class=${"pill " + h.kind}>${h.id}</span> ${h.title}</span><span class="muted">${h.status}</span></div>`)}
        ${!hits.length ? html`<div class="mi off">No match</div>` : null}
        ${types.length === 1 ? html`<div class="mi new" onMouseDown=${() => CreateForm.open({ kind: types[0], prefill: { title: q }, onCreated: id => { onPick(id); setQ(id); } })}>+ New ${Store.model.names[types[0]].toLowerCase()}</div>` : null}
      </div>` : null}</span>`;
  }
  function LinkTo({ item, onClose }) {
    const words = Object.keys(Store.model.linkWords[item.kind] || {});
    const [word, setWord] = useState(words[0]), [target, setTarget] = useState(""), [err, setErr] = useState("");
    const apply = async () => { try { await Store.post("/api/edit", { id: item.id, links: [word + " " + target], gist: "linked " + word + " " + target }); await Store.load(); onClose(); } catch (e) { setErr(e.message); } };
    return html`<div class="modal" onClick=${onClose}><div class="dlg" onClick=${e => e.stopPropagation()}>
      <div class="dlg-h"><span class="h2">Link ${item.id}</span></div>
      <div class="dlg-b"><div class="grid2">
        <div class="field"><label>Link word</label><select class="inp" value=${word} onChange=${e => { setWord(e.target.value); setTarget(""); }}>${words.map(w => html`<option value=${w}>${w}</option>`)}</select></div>
        <div class="field"><label>Target</label><${Inline} word=${word} kind=${item.kind} value=${target} onPick=${setTarget} /></div></div>
        ${err ? html`<div class="miss">${err}</div>` : null}</div>
      <div class="dlg-f"><div class="sp"></div><button class="btn" onClick=${onClose}>Cancel</button><button class="btn pri" disabled=${!target.trim()} onClick=${apply}>Add link</button></div>
    </div></div>`;
  }
  // New item: every field in model.create[kind], link needs through the picker.
  const CreateForm = { open(o) { Store.set({ create: o }); }, close() { Store.set({ create: null }); } };
  function Create() {
    const S = Store, c = S.ui.create; if (!c) return null;
    const [kind, setKind] = useState(c.kind || "OI"), [f, setF] = useState(c.prefill || {}), [err, setErr] = useState("");
    const req = S.model.create[kind] || [];
    const key = x => x.startsWith("link:") ? null : x;
    const opts = k => S.model.choices[k] || (k === "scope" ? S.model.scopes : k === "phase" ? S.model.phases : k === "owner" ? S.model.owners : null);
    const apply = async () => {
      try {
        const fields = {}; for (const x of req) if (key(x)) fields[S.model.labels[x] || x] = f[x] || "";
        const links = req.filter(x => x.startsWith("link:")).map(x => x.slice(5) + " " + (f[x] || ""));
        const r = await S.post("/api/create", { kind, fields, links });
        await S.load(); c.onCreated?.(r.item); CreateForm.close(); S.set({ open: r.item, focus: r.item });
      } catch (e) { setErr(e.message); }
    };
    return html`<div class="modal" onClick=${CreateForm.close}><div class="dlg" onClick=${e => e.stopPropagation()}>
      <div class="dlg-h"><span class="h2">New ${S.model.names[kind].toLowerCase()}</span>
        <select class="inp" value=${kind} onChange=${e => { setKind(e.target.value); setF({ title: f.title }); }}>${Object.keys(S.model.names).map(k => html`<option value=${k}>${S.model.names[k]}</option>`)}</select></div>
      <div class="dlg-b">${req.map(x => html`<div class="field"><label>${x.startsWith("link:") ? "Link: " + x.slice(5) : S.model.labels[x] || x}</label>
        ${x.startsWith("link:") ? html`<${Inline} word=${x.slice(5)} kind=${kind} value=${f[x] || ""} onPick=${v => setF({ ...f, [x]: v })} />`
        : opts(x)?.length ? html`<select class="inp" value=${f[x] || ""} onChange=${e => setF({ ...f, [x]: e.target.value })}><option value="">—</option>${opts(x).map(o => html`<option value=${o}>${o}</option>`)}</select>`
        : S.model.long[kind].includes(x) ? html`<textarea class="inp" value=${f[x] || ""} onInput=${e => setF({ ...f, [x]: e.target.value })} />`
        : html`<input class="inp" value=${f[x] || ""} onInput=${e => setF({ ...f, [x]: e.target.value })} />`}</div>`)}
        ${err ? html`<div class="miss">${err}</div>` : null}</div>
      <div class="dlg-f"><div class="sp"></div><button class="btn" onClick=${CreateForm.close}>Cancel</button><button class="btn pri" onClick=${apply}>Create</button></div>
    </div></div>`;
  }
  CreateForm.Form = Create;
  window.Picker = { Inline, LinkTo, typesFor };
  window.CreateForm = CreateForm;
})();
```

Confirm `/api/create` takes `{kind, fields, links, madeBy}` and returns `{item: id}` by reading `create()` in `server.py:554-586`; adjust the field labels if it wants keys rather than labels.

- [ ] **Step 2: Wire it**

Remove the stand-in `window.Picker` line from `move-form.js`. Add `picker.js` before `move-form.js` in `index.html`. In `panel.js` header add a `Link to…` button that sets local state to show `Picker.LinkTo`. In `table.js` top bar add `<button class="btn pri" onClick=${() => CreateForm.open({ kind: Store.model.states[Store.ui.view] ? Store.ui.view : "OI" })}>+ New item</button>`. In `app.js` render `<${CreateForm.Form} />` beside the move form. In the panel's forward column, make each dashed slot's text a button that opens `Picker.LinkTo` with the word preselected (pass `word` into `LinkTo` as an optional initial value).

- [ ] **Step 3: Style**

```css
.pkwrap{position:relative;display:block}.menu.pk{top:34px;width:360px;max-height:260px;overflow:auto}.mi.new{border-top:1px solid var(--line-2);color:var(--req)}
```

- [ ] **Step 4: Check in the browser**

New item as a CR: the form asks for `triggered by` through the picker filtered to LIM and REQ, with a New limitation row. Link to from the panel writes a link and the provenance column updates. A status move that needs a link (OI to Closed needs resolves into) shows the picker in the move form.

- [ ] **Step 5: Commit**

```bash
git add console/static
git commit -m "Link picker filtered by link word, Link to, and the generated New item form

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 11: Selection and the bulk bar

**Files:**
- Create: `console/static/bulk.js`
- Modify: `console/static/table.js` (checkbox column, `x`, shift-click, header checkbox), `console/static/app.js`, `console/static/index.html`, `console/static/style.css`

**Interfaces:**
- Produces: `window.Bulk` component rendered above the table when `Store.ui.selection.size > 0`. Actions: Set field, Move to, Link to, Merge, Withdraw, Delete.

- [ ] **Step 1: Selection in the table**

In `table.js`: prepend a `sel` column. Header cell: a checkbox whose checked state is "every row selected", toggling all rows in `rows()`. Row cell: a checkbox; click toggles the id in `Store.ui.selection` (copy the Set, then `Store.set`); shift-click selects the range from the last toggled id (`Store.ui.lastSel`) to this one in `rows()` order. Row class gains `sel` when selected. In `app.js` add `if (e.key === "x" && Store.ui.focus) toggle(Store.ui.focus)` where `toggle` is exported from `table.js` as `window.Table.toggle`.

- [ ] **Step 2: Write `console/static/bulk.js`**

```js
(function () {
  const html = htm.bind(preact.h);
  const { useState } = preactHooks;
  function Bulk() {
    const S = Store, ids = [...S.ui.selection], items = ids.map(id => S.byId[id]).filter(Boolean);
    const [mode, setMode] = useState(null), [field, setField] = useState(""), [value, setValue] = useState(""), [word, setWord] = useState(""), [target, setTarget] = useState(""), [survivor, setSurvivor] = useState(""), [reason, setReason] = useState(""), [err, setErr] = useState("");
    if (!items.length) return null;
    const kinds = [...new Set(items.map(i => i.kind))];
    const common = arrs => arrs.reduce((a, b) => a.filter(x => b.includes(x)));
    const fields = common(kinds.map(k => ["title", ...S.model.short[k], ...S.model.long[k]]));
    const states = common(kinds.map(k => [...new Set(Object.values(S.model.transitions[k] || {}).flat())]));
    const words = common(kinds.map(k => Object.keys(S.model.linkWords[k] || {})));
    const done = async () => { setMode(null); setErr(""); await S.load(); S.set({ selection: new Set() }); };
    const run = async fn => { try { await fn(); await done(); } catch (e) { setErr(e.message); await S.load(); } };
    const bulk = body => S.post("/api/bulk", { ids, ...body }).then(r => { if (r.failed) throw new Error(`Wrote ${r.written.length}; stopped at ${r.failed.id}: ${r.failed.error}`); });
    const opts = k => S.model.choices[k] || (k === "scope" ? S.model.scopes : k === "phase" ? S.model.phases : k === "owner" ? S.model.owners : null);
    return html`<div class="bar bulk">
      <span class="b">${items.length} selected</span><span class="muted">·</span>
      ${!mode ? html`
        <button class="btn" onClick=${() => setMode("set")}>Set field</button>
        <button class="btn" onClick=${() => setMode("move")}>Move to…</button>
        <button class="btn" onClick=${() => setMode("link")}>Link to…</button>
        <button class="btn" disabled=${kinds.length !== 1 || items.length < 2} onClick=${() => setMode("merge")}>Merge</button>
        <button class="btn" onClick=${() => run(() => bulk({ op: "withdraw", gist: "withdrawn in bulk" }))}>Withdraw</button>
        <button class="btn ghost danger" onClick=${() => setMode("delete")}>Delete</button>` : null}
      ${mode === "set" ? html`<select class="inp" value=${field} onChange=${e => { setField(e.target.value); setValue(""); }}><option value="">field…</option>${fields.map(f => html`<option value=${f}>${S.model.labels[f] || f}</option>`)}</select>
        ${field && opts(field)?.length ? html`<select class="inp" value=${value} onChange=${e => setValue(e.target.value)}><option value="">—</option>${opts(field).map(o => html`<option value=${o}>${o}</option>`)}</select>` : html`<input class="inp" value=${value} onInput=${e => setValue(e.target.value)} placeholder="value" />`}
        <button class="btn pri" disabled=${!field || !value.trim()} onClick=${() => run(() => bulk({ op: "set", fields: { [S.model.labels[field] || field]: value }, gist: (S.model.labels[field] || field) + " set in bulk" }))}>Apply to ${items.length}</button>` : null}
      ${mode === "move" ? html`<select class="inp" value="" onChange=${e => { if (e.target.value) { MoveForm.open({ ids, to: e.target.value }); setMode(null); } }}><option value="">state…</option>${states.map(s => html`<option value=${s}>${s}</option>`)}</select>` : null}
      ${mode === "link" ? html`<select class="inp" value=${word} onChange=${e => setWord(e.target.value)}><option value="">link word…</option>${words.map(w => html`<option value=${w}>${w}</option>`)}</select>
        ${word ? html`<${Picker.Inline} word=${word} kind=${kinds[0]} value=${target} onPick=${setTarget} />` : null}
        <button class="btn pri" disabled=${!word || !target.trim()} onClick=${() => run(() => bulk({ op: "link", links: [word + " " + target], gist: "linked in bulk" }))}>Apply to ${items.length}</button>` : null}
      ${mode === "merge" ? html`<span class="small">Survivor</span><select class="inp" value=${survivor} onChange=${e => setSurvivor(e.target.value)}><option value="">pick…</option>${items.map(i => html`<option value=${i.id}>${i.id} ${i.title}</option>`)}</select>
        <button class="btn pri" disabled=${!survivor} onClick=${() => run(() => S.post("/api/merge", { survivor, losers: ids.filter(x => x !== survivor) }))}>Merge ${items.length - 1} into ${survivor || "…"}</button>` : null}
      ${mode === "delete" ? html`<input class="inp" value=${reason} onInput=${e => setReason(e.target.value)} placeholder="reason, goes into History" />
        <button class="btn pri danger" disabled=${!reason.trim()} onClick=${() => run(async () => { for (const id of ids) await S.post("/api/delete", { id, reason }); })}>Delete ${items.length}</button>` : null}
      ${mode ? html`<button class="btn ghost" onClick=${() => { setMode(null); setErr(""); }}>Cancel</button>` : null}
      ${err ? html`<span class="miss small">${err}</span>` : null}
      <div class="sp"></div><span class="muted small">Esc to clear</span>
    </div>`;
  }
  window.Bulk = Bulk;
})();
```

Note `Move to…` lists every state any transition in the type reaches, and the move form's needs check reports the items that cannot reach it from where they are. Delete loops over the single endpoint because `delete()` takes a reason and rewrites links per item; a partial failure leaves the earlier ones deleted, and the error names where it stopped.

- [ ] **Step 3: Mount and style**

In `table.js` render `<${Bulk} />` between the chips bar and the table wrap. Add `bulk.js` to `index.html` before `table.js`. Style:

```css
.bar.bulk{background:var(--req-bg);border-bottom:1px solid var(--line);flex-wrap:wrap}.bar.bulk .b{font-weight:500}
.cb{width:14px;height:14px;border:1.5px solid var(--ink-3);border-radius:3px;display:inline-block;box-sizing:border-box;cursor:pointer}.cb.on{background:var(--req);border-color:var(--req)}
.c-sel{width:30px}
```

- [ ] **Step 4: Check in the browser**

Select three REQs in Draft: Set field Owner applies to all three and the files change. Move to Agreed opens the form with Phase shared. Link to worked by an OI writes three links. Merge two into one removes a file. Withdraw moves them to Withdrawn. Delete with a reason removes files. In change-sets mode (the sample engagement with `- Writes: change-sets`), Set field shows the refusal message in the bar.

- [ ] **Step 5: Commit**

```bash
git add console/static
git commit -m "Selection and the bulk bar: set, move, link, merge, withdraw, delete

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 12: Work queues as filters with their editable columns

**Files:**
- Modify: `console/static/store.js` (columns per view), `console/static/table.js` (rule header, group-by, extra columns for supports and duplicates), `console/static/panel.js` (Mark reviewed, Delete, Merge into in the More menu)

**Interfaces:**
- Produces: `Store.columnsFor(view, filter)` returns the column list; `Store.ui.groupBy` groups rows under headers.

- [ ] **Step 1: Columns per view**

In `store.js` add:

```js
    columnsFor() {
      const { view, filter } = Store.ui;
      if (view === "integrity" && filter.rule) {
        const f = Store.state.integrity.failures.find(x => x.rule === filter.rule);
        // The failing field is the first word of the rule text that names a model field, else Owner.
        const text = (f?.text || "").toLowerCase();
        const key = Object.keys(Store.model.labels).find(k => text.includes((Store.model.labels[k] || k).toLowerCase())) || "owner";
        return ["id", "title", "status", "scope", key, "issues"];
      }
      if (view === "supports") return ["id", "title", "status", "support"];
      if (view === "duplicates") return ["id", "title", "status", "scope", "group"];
      if (view === "unreviewed") return ["id", "title", "status", "scope", "owner", "reviewed"];
      if (Store.model.states[view]) return ["id", "title", "status", "scope", "owner", ...Store.model.short[view].filter(k => !["scope", "owner"].includes(k)).slice(0, 2), "links", "issues"];
      return null;
    },
```

and in `table.js` use `Store.ui.columns || Store.columnsFor() || DEFAULT_COLS`. Add three cells in `Cell`:

- `support`: the first suggestion for the row, `${s.rule} · ${s.text}` with an `Open and accept` button that opens the panel; in the panel's Gaps section, each suggestion gains `Accept` (posts `/api/support/accept` with `{id, key, fields: {}}`), `Link existing` (opens `Picker.LinkTo` with the suggestion's word) and `Dismiss` (posts `/api/support/dismiss` with `{id, key, reason}` after a prompt-free inline reason input). Read the three handlers in `server.py:506-553` for exact request keys.
- `group`: the duplicate group's other ids as pills, with `Not duplicates` posting `/api/rationalise/not-duplicates {ids}`.
- `reviewed`: a `Mark reviewed` button posting `/api/rationalise/reviewed {id}`.

- [ ] **Step 2: Rule header and group-by**

When `filter.rule` is set, the top bar shows `${rule} · ${Store.model.rules[rule] || ""}` and the header checkbox selects all. Add a `Group by` select to the chips bar (none, type, status, scope, owner) that sets `Store.ui.groupBy`; when set, `Table` sorts rows by that key and inserts a `<tr class="grp"><td colspan=...>value · n</td></tr>` before each run.

- [ ] **Step 3: Panel More menu**

Add a `⋯` button in the panel header opening a small menu: `Mark reviewed` (only when `Store.state.unreviewed` includes the id), `Merge into…` (opens `Picker.Inline` for the same type, then posts `/api/merge {survivor: picked, losers: [id]}`), `Delete` (inline reason, posts `/api/delete`). After each, reload and close the panel if the item is gone.

- [ ] **Step 4: Check in the browser**

Integrity, I3: the Owner column is editable in place and the rail count drops after each save. Supports: Accept creates the offered item and the row disappears. Duplicates: Not duplicates removes the group. Unreviewed: Mark reviewed removes the row. Group by scope shows headers.

- [ ] **Step 5: Commit**

```bash
git add console/static
git commit -m "Work queues as table filters: integrity by rule, supports, duplicates, unreviewed; group by

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 13: Reports, summary, push and renumber

**Files:**
- Create: `console/static/report.js`
- Modify: `console/static/rail.js` (Save current view, register menu with Renumber), `console/static/app.js`, `console/static/index.html`, `console/static/style.css`
- Modify: `console/server.py` (`/api/push/build` calling `push-pages.py`'s build function)

**Interfaces:**
- Produces: `window.Report` renders `Store.ui.view === "report:<n>"`. `POST /api/push/build {}` runs the existing push build into `<engagement>/push/` and returns its manifest; sends nothing.

- [ ] **Step 1: `/api/push/build`**

Read `console/push-pages.py` to find its entry function (`grep -n "^def " console/push-pages.py`). Add to `server.py`:

```python
                if p == "/api/push/build":
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("push_pages", os.path.join(HERE, "push-pages.py"))
                    pp = importlib.util.module_from_spec(spec); spec.loader.exec_module(pp)
                    return self.send_json(pp.build(ENG))
```

where `build(eng)` is that entry function; if it is named differently or takes the output directory, call it as it is written and return what it returns. If it only has a `main()` that reads argv, add a `build(eng)` that `main()` calls, and keep `main()` for the Makefile.

- [ ] **Step 2: Write `console/static/report.js`**

```js
(function () {
  const html = htm.bind(preact.h);
  const { useState, useEffect } = preactHooks;
  function Report() {
    const S = Store, n = +S.ui.view.split(":")[1], view = S.views[n]; if (!view) return null;
    const [secs, setSecs] = useState(null), [text, setText] = useState(""), [msg, setMsg] = useState("");
    useEffect(() => { S.post("/api/report/sections", { view }).then(setSecs); setText(""); }, [S.ui.view, JSON.stringify(view.filter)]);
    const saveView = patch => { const vs = S.views.slice(); vs[n] = { ...view, ...patch }; S.post("/api/views", { views: vs }).then(r => { S.views = r.views; S.emit(); }); };
    const rows = S.state.items.filter(S.viewFilter("all")).filter(i => (!view.filter.types.length || view.filter.types.includes(i.kind)) && (!view.filter.statuses.length || view.filter.statuses.includes(i.status)));
    const table = (xs, cols) => html`<table><thead><tr>${cols.map(c => html`<th>${S.model.labels[c] || c}</th>`)}</tr></thead>
      <tbody>${xs.map(r => html`<tr>${cols.map(c => html`<td>${c === "id" ? html`<span class=${"pill " + (r.kind || r.id.split("-")[0]) + " lnk"} onClick=${() => S.set({ open: r.id })}>${r.id}</span>` : c === "status" ? html`<span class="st">${r.status}</span>` : (r[c] ?? "")}</td>`)}</tr>`)}</tbody></table>`;
    const summary = async () => { const r = await S.post("/api/report/summary", { view }); setText(r.text); };
    const copy = async () => { await navigator.clipboard.writeText(text); setMsg("Copied."); };
    const push = async () => { try { const r = await S.post("/api/push/build", {}); setMsg("Built " + (r.pages?.length ?? "") + " pages into push/. Run /push-confluence to send."); } catch (e) { setMsg(e.message); } };
    return html`<div class="main-col">
      <div class="bar top"><span class="muted">Reports /</span><span class="h2">${view.name}</span><div class="sp"></div>
        <button class="btn" onClick=${summary}>Draft email summary</button><button class="btn pri" onClick=${push}>Build Confluence push</button></div>
      <div class="bar chips"><span class="chip">Since <input class="inp cell" style="width:150px" value=${view.filter.since || ""} onChange=${e => saveView({ filter: { ...view.filter, since: e.target.value } })} placeholder="8 September 2026" /></span>
        <span class="chip">Sections <b>${view.sections.join(", ")}</b></span><span class="chip">Columns <b>${view.columns.join(", ")}</b></span>
        <div class="sp"></div><span class="muted small">Saved view · edits change the saved filter</span></div>
      <div class="rep">
        <div class="rep-main">
          ${view.sections.includes("moved") && secs ? html`<div class="card"><div class="h3">Moved this week <span class="muted">${secs.moved.length}</span></div>${table(secs.moved.map(m => ({ ...m, status: m.from + " → " + m.to })), ["id", "title", "status", "owner"])}</div>` : null}
          ${view.sections.includes("raised") && secs ? html`<div class="card"><div class="h3">Raised <span class="muted">${secs.raised.length}</span></div>${table(secs.raised, ["id", "title", "status", "owner"])}</div>` : null}
          ${view.sections.includes("outstanding") && secs ? html`<div class="card"><div class="h3">Outstanding for SLT <span class="muted">${secs.outstanding.length}</span></div>${table(secs.outstanding.map(o => ({ ...o, due: o.overdue ? "Overdue " + o.overdue + " d" : o.due })), ["id", "title", "status", "due"])}</div>` : null}
          ${view.sections.includes("gaps") && secs ? html`<div class="card"><div class="h3">Register gaps <span class="muted">${secs.gaps.length}</span></div><div class="small">${Object.entries(secs.gaps.reduce((a, g) => (a[g.rule] = (a[g.rule] || 0) + 1, a), {})).sort((a, b) => b[1] - a[1]).map(([r, c]) => html`<span class="chip">${r} <b class="mono">${c}</b></span> `)}</div></div>` : null}
          ${view.sections.includes("table") ? html`<div class="card"><div class="h3">${view.name} <span class="muted">${rows.length}</span></div>${table(rows, view.columns)}</div>` : null}
        </div>
        <div class="card rep-side"><div class="h3">Email summary</div>
          <textarea class="inp" style="min-height:260px;font-size:12px" value=${text} onInput=${e => setText(e.target.value)} placeholder="Draft email summary fills this from the sections." />
          <button class="btn" disabled=${!text} onClick=${copy}>Copy</button>${msg ? html`<div class="muted small">${msg}</div>` : null}</div>
      </div></div>`;
  }
  window.Report = Report;
})();
```

- [ ] **Step 3: Save current view and Renumber in the rail**

In `rail.js` Reports group add `<div class="rl-it muted" onClick=${saveCurrent}>+ Save current view</div>` where `saveCurrent` prompts for a name with an inline input (no `window.prompt`), builds `{name, filter: Store.ui.filter, columns: Store.ui.columns || Store.columnsFor() || DEFAULT, groupBy: Store.ui.groupBy, sections: ["table"]}`, posts `/api/views` with the list plus the new one and switches to it. Each register entry gains a `⋯` on hover opening a menu with `Renumber…`, which shows an inline confirm (`Renumber all ${names[k]}s. Needs a clean git tree in the engagement folder.` with a Renumber button) and posts `/api/renumber {type}`; on success toast `Renumbered n items` and reload; on refusal toast the message.

In `app.js` `App`, render `<${Report} />` instead of `<${Table} />` when `Store.ui.view.startsWith("report:")`. Add `report.js` to `index.html`.

Style:

```css
.rep{flex:1;overflow:auto;padding:24px;display:grid;grid-template-columns:minmax(0,1fr) 340px;gap:24px;background:var(--bg)}
.rep-main{display:flex;flex-direction:column;gap:20px}.rep .card{background:var(--surface)}.rep-side{align-self:start}
.rep table{width:100%;border-collapse:collapse;font-size:13px}.rep th{text-align:left;font-weight:500;color:var(--ink-3);font-size:12px;padding:6px 10px;border-bottom:1px solid var(--line)}.rep td{padding:6px 10px;border-bottom:1px solid var(--line-2)}
```

- [ ] **Step 4: Check in the browser**

SLT weekly: sections fill from the test engagement, Draft email summary fills the box, Copy copies. Build Confluence push writes `engagements/test/push/` and says so. Save current view from a filtered table adds a report entry. Renumber on a dirty tree refuses with the message; after `git -C engagements/test add -A && git -C engagements/test commit -qm wip` (only if that folder is its own repository; check with `git -C engagements/test rev-parse --show-toplevel`), Renumber REQ compacts and the links in LIM and CR files change.

- [ ] **Step 5: Commit**

```bash
git add console/static console/server.py console/push-pages.py
git commit -m "Reports as saved views with email summary and push build; Renumber from the rail

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 14: Baseline mode and theme in the new shell

**Files:**
- Modify: `console/static/app.js`, `console/static/rail.js`, `console/static/index.html`

The spec keeps Baseline before the freeze on its existing screens. Rather than port them, the new shell hands off: when `Store.state.baseline?.present && !Store.state.items.length` (the `stage()` test in `old/app.js:27`), `App` renders a full-page notice with a link to `/old/` and the words "This engagement is still baselining. The baseline screens open in the previous console until the freeze." Confirm `/api/state` carries `baseline.present` by reading `state()`; if it does not, add `"baseline": {"present": os.path.isdir(B_DIR)}` to it.

- [ ] **Step 1: Implement the handoff and the theme switch**

Add the theme buttons (Light, Auto, Dark) to the rail's foot, copying `setTheme` from `old/app.js:401-414`. Add `guide.html` as a rail link labelled Guide.

- [ ] **Step 2: Check**

`make down; make sample; make up` and open the console: the sample engagement (baselining) shows the notice and `/old/` still runs the baseline. Point `ENG` back at `engagements/test` and confirm the table returns.

- [ ] **Step 3: Commit**

```bash
git add console/static console/server.py
git commit -m "Baselining hands off to the previous console; theme and guide in the rail

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 15: Retire the old front end and update the documents

**Files:**
- Delete: `console/static/old/app.js`, keep `console/static/old/index.html` only if Task 14's handoff still needs it (it does, until the baseline screens are ported; leave both and record that in CLAUDE.md)
- Modify: `console/README.md`, `CLAUDE.md`, `console/static/guide.html`, `handoffs/`

- [ ] **Step 1: Decide what stays**

The baseline screens live only in `old/app.js`, so `old/` stays for now. Change this task to documentation only and note the port of the baseline screens as an open thread.

- [ ] **Step 2: Update `console/README.md`**

Replace the views section with the new shape: rail, table, cells, panel, move form, bulk bar, reports, renumber, and the handoff to `/old/` while baselining. List the new endpoints in the API table. Say `views.json` and `renumbered.md` are direct-mode files beside the registers.

- [ ] **Step 3: Update `CLAUDE.md`**

In the layout table, replace the `console/static/app.js` row with one row per module in one line each, and add `console/views.py` and `console/renumber.py`. Under rules, add: `Renumber refuses on a dirty engagement tree and rewrites ids in two phases through a temporary id so no new id collides with an old file.` Under open threads add: `The baseline screens still run in console/static/old/. Porting them into the table shell removes the last of the old front end.` Update the model version to 2.29 wherever 2.28 appears.

- [ ] **Step 4: Update `guide.html`**

Add a short section after the Live description: the table, the panel and the bulk bar, and that every state change asks only for what the model needs. Keep the theme handling.

- [ ] **Step 5: Handoff**

Run `/handoff` for the objective "console rethink" so the next session on either machine starts from the right place. Then commit:

```bash
git add console/README.md CLAUDE.md console/static/guide.html handoffs
git commit -m "Docs: the console rethink in README, CLAUDE.md and the guide

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

## Self-review notes

- Spec coverage: every spec section maps to a task. The spec's Task 9 "Delete old/" is scaled back in Task 15 because Baseline mode was kept out of scope by the spec itself; that is recorded as an open thread rather than silently dropped.
- The status cell, panel Next moves, bulk Move to and the create form all route through `MoveForm.open` or `CreateForm.open`, which is the spec's one-form rule.
- Names used across tasks: `Store.rows()`, `Store.set()`, `Store.post()`, `Store.load()`, `Store.byId`, `Store.failuresById`, `Store.suggestionsById`, `Store.viewFilter()`, `Store.columnsFor()`, `Store.toast()`, `MoveForm.open()`, `Picker.Inline`, `Picker.LinkTo`, `CreateForm.open()`, `Cells.Editor`, `Cells.StatusCell`, `Table.toggle`. Server: `model_payload`, `needs`, `search_items`, `bulk`, `renumber`, `move_id`, `state_model`, `V.load/save/sections/summary`, `R.plan/dirty`, `I.provenance`.
