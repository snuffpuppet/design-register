# Scope Field Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give every register item an optional Scope field whose vocabulary each engagement declares, so the abb-nokia registers can be filtered by service instead of losing the source's Scope column into Notes.

**Architecture:** Scope is a header field held in `M.SHORT` first for every type, which gives the item file position and the pushed table column for free, because `items.render_item` and `push_pages.columns` both build from that table. The whole feature is gated on the engagement declaring a `## Scopes` section in `engagement.md`: no declaration means no Scope on items, no requirement to fill one, and no rule checking one, so every existing engagement behaves exactly as it does under model 2.26.

**Tech Stack:** Python 3.12 standard library only (no third-party imports anywhere under `console/`), vanilla JavaScript in one file, `unittest` run inside Docker via `make test`.

**Spec:** `docs/superpowers/specs/2026-09-14-scope-field-design.md`

## Global Constraints

- Australian English throughout code comments, documents and user-facing strings.
- No em dashes. No "not x but y" framing. No rhyming patterns of three.
- `console/` is standard library only. Do not add an import that is not already used in the file you are editing.
- Documents carry a version and date near the top and are bumped on change. The model document goes to **Version 2.27, 14 September 2026**.
- `scope` goes **first** in every `M.SHORT` list. This placement is load-bearing: it is what puts Scope directly after Status in both the item file and the pushed table.
- An engagement with no `## Scopes` section must behave exactly as it does today. Every task has a test proving its change is inert in that case.
- Run the suite with `make test`, which runs `python -m unittest discover -s tests -v` in the `python:3.12-slim` image. Do not run python on the host.
- End every commit message with:
  `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`

---

### Task 1: The model knows Scope

**Files:**
- Modify: `console/model.py:60-66` (`SHORT`), `:76-83` (`LABELS`), `:111-118` (`REQUIRED_ON_CREATE`), `:196-200` (`RULES`)
- Modify: `console/push-pages.py:107` (`columns`), and `build()` at `:206`
- Modify: `solution-register-model.md` (header notes, section 4.1, section 6, section 7, section 9)
- Test: `console/tests/test_model.py`, `console/tests/test_items.py`, `console/tests/test_push_pages.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `M.SHORT[kind][0] == "scope"` for all six kinds; `M.LABELS["scope"] == "Scope"`; `"scope" in M.REQUIRED_ON_CREATE[kind]` for all six kinds; `M.RULES["I24"]` as a string; `push_pages.columns(kind, scopes)` taking the engagement's scopes as its second argument and omitting the Scope column when that list is empty; `push_pages.engagement_scopes(eng)` returning the declared list.

- [ ] **Step 1: Write the failing tests**

Add to `console/tests/test_model.py`:

```python
class Scope(unittest.TestCase):
    def test_scope_is_first_short_field_on_every_type(self):
        for kind in M.DIRS:
            self.assertEqual(M.SHORT[kind][0], "scope", f"{kind} does not lead with scope")

    def test_scope_has_a_label(self):
        self.assertEqual(M.LABELS["scope"], "Scope")

    def test_scope_is_required_on_create_for_every_type(self):
        for kind in M.DIRS:
            self.assertIn("scope", M.REQUIRED_ON_CREATE[kind], f"{kind} does not require scope")

    def test_i24_is_stated(self):
        self.assertIn("I24", M.RULES)
        self.assertIn("Scope", M.RULES["I24"])
```

Add to `console/tests/test_items.py`:

```python
class ScopeRoundTrip(unittest.TestCase):
    def test_scope_sits_directly_after_status(self):
        it = {"id": "REQ-0001", "kind": "REQ", "title": "A need", "status": "Draft", "scope": "CarrierEthernet",
              "moscow": "Must", "phase": "", "owner": "Priya Nair", "implemented-by": "Vendor",
              "raised-on": "1 September 2026", "closed-on": "", "updated": "1 September 2026", "links": []}
        lines = IT.render_item(it).splitlines()
        self.assertEqual(lines[4], "status: Draft")
        self.assertEqual(lines[5], "scope: CarrierEthernet")

    def test_scope_round_trips(self):
        d = tempfile.mkdtemp()
        try:
            it = {"id": "RSK-0002", "kind": "RSK", "title": "A risk", "status": "Identified", "scope": "NbnTC4Access",
                  "risk-kind": "Risk", "owner": "Priya Nair", "likelihood": "M", "impact": "H", "due": "",
                  "raised-on": "1 September 2026", "closed-on": "", "updated": "1 September 2026", "links": []}
            p = os.path.join(d, "RSK-0002.md")
            open(p, "w", encoding="utf-8").write(IT.render_item(it))
            self.assertEqual(IT.parse_item(p)["scope"], "NbnTC4Access")
        finally:
            shutil.rmtree(d)

    def test_blank_scope_round_trips_as_blank(self):
        d = tempfile.mkdtemp()
        try:
            it = {"id": "OI-0003", "kind": "OI", "title": "Do a thing", "status": "Open", "scope": "",
                  "owner": "Priya Nair", "due": "", "next action": "Ring the vendor",
                  "raised-on": "1 September 2026", "closed-on": "", "updated": "1 September 2026", "links": []}
            p = os.path.join(d, "OI-0003.md")
            open(p, "w", encoding="utf-8").write(IT.render_item(it))
            self.assertEqual(IT.parse_item(p)["scope"], "")
        finally:
            shutil.rmtree(d)
```

Check the top of `test_items.py` already imports `tempfile`, `os` and `shutil`; add whichever are missing to its import line.

Add to `console/tests/test_push_pages.py`, matching however that file already imports the push module:

```python
class ScopeColumn(unittest.TestCase):
    def test_scope_is_the_fourth_column_when_scopes_are_declared(self):
        for kind in M.DIRS:
            cols = P.columns(kind, ["Access"])
            self.assertEqual(cols[3], ("Scope", "scope"), f"{kind} column 4 is {cols[3]}")

    def test_no_scope_column_when_none_are_declared(self):
        for kind in M.DIRS:
            self.assertNotIn("scope", [key for _, key in P.columns(kind, [])],
                             f"{kind} pushes a Scope column for an engagement with no scopes")
```

The second test is the one that matters. `columns()` builds from `M.SHORT`, so without a change it would push an empty Scope column to the Confluence pages of every engagement that opted out, which breaks the global constraint that such an engagement behaves exactly as it does under 2.26.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `make test`
Expected: FAIL. `test_scope_is_first_short_field_on_every_type` with `KeyError` or an assertion naming `moscow`, and `test_scope_has_a_label` with `KeyError: 'scope'`.

- [ ] **Step 3: Add scope to the four model tables**

In `console/model.py`, replace `SHORT`:

```python
SHORT = {
    "REQ": ["scope", "moscow", "phase", "owner", "implemented-by"],
    "DEC": ["scope", "owner", "consulted", "approved-by", "implemented-by"],
    "LIM": ["scope", "owner", "chosen-option", "implemented-by"],
    "RSK": ["scope", "risk-kind", "owner", "likelihood", "impact", "due"],
    "OI":  ["scope", "owner", "due"],
    "CR":  ["scope", "owner", "chosen-option", "estimate", "approved-by", "phase", "implemented-by", "vendor-ref"],
}
```

In `LABELS`, add `"scope": "Scope",` beside `"phase": "Phase"`.

Replace `REQUIRED_ON_CREATE`, adding `"scope"` after `"title"` on each line:

```python
REQUIRED_ON_CREATE = {
    "REQ": ["title", "scope", "moscow", "owner", "implemented-by", "source"],
    "DEC": ["title", "scope", "owner", "rationale", "implemented-by", "source"],
    "LIM": ["title", "scope", "owner", "implemented-by", "source"],
    "RSK": ["title", "scope", "risk-kind", "owner", "likelihood", "impact", "source"],
    "OI":  ["title", "scope", "owner", "next action", "source"],
    "CR":  ["title", "scope", "owner", "reason", "implemented-by", "source", "link:triggered by"],
}
```

In `RULES`, add:

```python
    "I24": "Every item's Scope is one of the engagement's Scopes, and no item is without one, where the engagement declares any.",
```

Update the module docstring's first line to say `Register model 2.27 as data:`.

- [ ] **Step 4: Teach the push to drop Scope when the engagement declares none**

In `console/push-pages.py`, change `columns` at line 107 to take the engagement's scopes:

```python
def columns(kind, scopes=None):
    cols = [("ID", "id"), ("Title", "title"), ("Status", "status")]
    cols += [(M.LABELS.get(k, k), k) for k in M.SHORT[kind] if k != "scope" or scopes]
    cols += [("Raised on", "raised-on"), ("Closed on", "closed-on"), ("Links", "links"), ("Source", "source"), ("Source id", "source-id")]
    return cols
```

Add a reader beside it, because this script runs standalone and does not import `server`:

```python
def engagement_scopes(eng):
    """The engagement's declared scopes. This script has its own reader rather than importing the
    server, as it does for the rest of engagement.md."""
    p = os.path.join(eng, "engagement.md")
    if not os.path.exists(p):
        return []
    out, on = [], False
    for ln in open(p, encoding="utf-8"):
        if ln.startswith("## Scopes"):
            on = True; continue
        if ln.startswith("## "):
            on = False
        if on and ln.startswith("- "):
            out.append(ln[2:].strip())
    return out
```

In `build()`, read them once after `items = load_items(eng)` and pass them to every `columns(kind)` call in the function:

```python
    scopes = engagement_scopes(eng)
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `make test`
Expected: PASS for the new tests. Other suites may now fail on required fields; that is expected and Task 3 fixes it. If any pre-existing test fails, note which and carry on to step 5 rather than patching it here.

- [ ] **Step 6: Update the model document to 2.27**

In `solution-register-model.md`:

Change line 3 to `Version 2.27, 14 September 2026. Owner: Adam Moyes.` and insert a note directly above the 2.26 paragraph:

```markdown
Version 2.27 gives the item a Scope. Section 6 has said since 2.17 that a way of filtering by service or domain could be added when an engagement has several services to name, and an engagement with four technical services now does. Scope is declared per engagement rather than by this document: an engagement that names no scopes carries none and is checked by no scope rule, so nothing changes for a single-service engagement. Section 9 adds I24.
```

In section 4.1, add a row after the Implemented by row:

```markdown
| Scope | The service or area the item belongs to, from the engagement's Scopes list (6). One value, at the lowest level that applies. Required while the engagement declares scopes. Absent where it declares none. |
```

Replace the whole of section 6 with:

```markdown
## 6. Scope

Scope names the service or area an item belongs to. The engagement declares its own values, because the useful split differs by engagement: one delivering four technical services splits by service, one delivering a single platform splits by nothing at all.

Each item carries one Scope, at the lowest level that applies. An integration issue between two technical services is tagged at the customer-service level above them. There is no programme level, because the registers sit inside the programme and the programme is implied.

An engagement with one service declares no scopes. Its items carry no Scope, nothing asks for one, and I24 never fires. Scope was removed in 2.17 for exactly that case and returns in 2.27 for the other one.
```

In section 7, add `scope` after `status` in all six rows of the frontmatter table, so the REQ row reads `id, title, status, scope, moscow, phase, owner, implemented-by, links, raised-on, closed-on, updated` and the others follow the same pattern.

In section 9, add after the I23 line:

```markdown
- **I24.** Every item's Scope is one of the engagement's Scopes, and no item is without one, where the engagement declares any. Where the engagement declares none, the rule does not apply.
```

- [ ] **Step 7: Commit**

```bash
git add console/model.py console/push-pages.py solution-register-model.md console/tests/test_model.py console/tests/test_items.py console/tests/test_push_pages.py
git commit -m "Model 2.27: Scope as a per-engagement field on every item

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: I24 and inherited Scope on offers

**Files:**
- Modify: `console/integrity.py:165` (`check`), `:174` (`rules`), `:218` (beside I5), and the `offer()` function
- Test: `console/tests/test_integrity.py`

**Interfaces:**
- Consumes: `M.RULES["I24"]` from Task 1.
- Produces: `I.check(items, scopes=[...])` accepting a `scopes` keyword that defaults to `None`; `I.rules(items, by_id, phases, stakeholders, today, scopes)` with `scopes` as the last positional parameter; `offer()` copying the trigger's `scope` into the offered fields.

- [ ] **Step 1: Write the failing tests**

Add to `console/tests/test_integrity.py`:

```python
class ScopeRule(unittest.TestCase):
    def fails(self, res, id):
        return [f["rule"] for f in res["failures"] if f["id"] == id]

    def test_off_list_scope_fails(self):
        r = I.check([item("REQ-0001", "Draft", moscow="Must", scope="Nonsense")], scopes=["Access", "Delivery"])
        self.assertIn("I24", self.fails(r, "REQ-0001"))

    def test_blank_scope_fails_when_scopes_declared(self):
        r = I.check([item("REQ-0001", "Draft", moscow="Must", scope="")], scopes=["Access", "Delivery"])
        self.assertIn("I24", self.fails(r, "REQ-0001"))

    def test_listed_scope_passes(self):
        r = I.check([item("REQ-0001", "Draft", moscow="Must", scope="Access")], scopes=["Access", "Delivery"])
        self.assertNotIn("I24", self.fails(r, "REQ-0001"))

    def test_rule_is_inert_when_no_scopes_declared(self):
        r = I.check([item("REQ-0001", "Draft", moscow="Must", scope="")])
        self.assertNotIn("I24", self.fails(r, "REQ-0001"))

    def test_off_list_scope_is_inert_when_no_scopes_declared(self):
        r = I.check([item("REQ-0001", "Draft", moscow="Must", scope="Nonsense")])
        self.assertNotIn("I24", self.fails(r, "REQ-0001"))


class ScopeInheritance(unittest.TestCase):
    def test_offer_takes_the_triggers_scope(self):
        r = I.check([item("REQ-0001", "Draft", moscow="Must", scope="CarrierEthernet")])
        s = sug(r, "S1", "REQ-0001")
        self.assertEqual(s[0]["fields"]["scope"], "CarrierEthernet")

    def test_offer_with_no_trigger_scope_leaves_an_empty_box(self):
        r = I.check([item("REQ-0001", "Draft", moscow="Must")])
        s = sug(r, "S1", "REQ-0001")
        self.assertEqual(s[0]["fields"]["scope"], "")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `make test`
Expected: FAIL. The `ScopeRule` tests with `TypeError: check() got an unexpected keyword argument 'scopes'`, and `test_offer_takes_the_triggers_scope` asserting `'' != 'CarrierEthernet'`.

- [ ] **Step 3: Thread scopes through and add I24**

In `console/integrity.py`, change the two signatures:

```python
def check(items, phases=None, stakeholders=None, today=None, scopes=None):
```

```python
    failures, warnings = rules(items, by_id, phases, stakeholders, today, scopes)
```

```python
def rules(items, by_id, phases=None, stakeholders=None, today=None, scopes=None):
```

Directly after the I5 block at line 218, add:

```python
        # I24
        if scopes:
            sc = str(it.get("scope", "")).strip()
            if not sc:
                fail("I24", it, "no Scope")
            elif sc not in scopes:
                fail("I24", it, f"scope {sc!r} is not in the engagement's Scopes")
```

The guard is `if scopes:` rather than `if scopes is not None:` so that an engagement declaring an empty list behaves the same as one declaring nothing.

In `offer()`, insert directly above the `for key in M.REQUIRED_ON_CREATE.get(okind, []):` loop:

```python
    # Scope is inherited, never asked for: an offered record belongs to the same service as its trigger.
    if str(trigger.get("scope", "") or "").strip():
        out.setdefault("scope", trigger["scope"])
```

It must sit above that loop, because the loop's `out.setdefault(key, "")` would otherwise be reached first only when the template did not set it, and placing the inheritance after would still work but reads as an afterthought. Above the loop, the setdefault in the loop finds `scope` already present and leaves it.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `make test`
Expected: PASS for both new classes.

- [ ] **Step 5: Commit**

```bash
git add console/integrity.py console/tests/test_integrity.py
git commit -m "I24: Scope is one of the engagement's, and offers inherit the trigger's

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: The engagement declares its scopes

**Files:**
- Modify: `console/server.py:63-85` (`load_engagement`), `:210-218` (`state`), `:236` (`integrity_of` call site), `:488-503` (`create`)
- Test: `console/tests/test_server_direct.py`

**Interfaces:**
- Consumes: `I.check(..., scopes=...)` from Task 2.
- Produces: `load_engagement()` returning a `scopes` list; `required_on_create(kind)` returning `M.REQUIRED_ON_CREATE[kind]` with `scope` dropped when the engagement declares none.

- [ ] **Step 1: Write the failing tests**

Add to `console/tests/test_server_direct.py`:

```python
class Scopes(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); self.saved = (S.ENG, S.CS_DIR, S.DISMISSED_PATH); use(self.d)

    def tearDown(self):
        S.ENG, S.CS_DIR, S.DISMISSED_PATH = self.saved; shutil.rmtree(self.d)

    def eng(self, body):
        open(os.path.join(self.d, "engagement.md"), "w", encoding="utf-8").write(body)

    def test_scopes_parse(self):
        self.eng("# Engagement: x\n\n## Phases\n\n- P1 (current)\n\n## Scopes\n\n- Access\n- Delivery\n")
        self.assertEqual(S.load_engagement()["scopes"], ["Access", "Delivery"])

    def test_phases_still_parse_alongside_scopes(self):
        self.eng("# Engagement: x\n\n## Phases\n\n- P1 (current)\n\n## Scopes\n\n- Access\n")
        e = S.load_engagement()
        self.assertEqual(e["phases"], ["P1"]); self.assertEqual(e["current"], "P1")

    def test_no_scopes_section_is_an_empty_list(self):
        self.eng("# Engagement: x\n\n## Phases\n\n- P1 (current)\n")
        self.assertEqual(S.load_engagement()["scopes"], [])

    def test_scope_is_required_on_create_when_declared(self):
        self.eng("# Engagement: x\n\n## Scopes\n\n- Access\n")
        self.assertIn("scope", S.required_on_create("OI"))

    def test_scope_is_not_required_when_none_declared(self):
        self.eng("# Engagement: x\n")
        self.assertNotIn("scope", S.required_on_create("OI"))

    def test_other_required_fields_are_untouched(self):
        self.eng("# Engagement: x\n")
        self.assertEqual(S.required_on_create("OI"), ["title", "owner", "next action", "source"])
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `make test`
Expected: FAIL. `test_scopes_parse` with `KeyError: 'scopes'`, and the `required_on_create` tests with `AttributeError: module 'server' has no attribute 'required_on_create'`.

- [ ] **Step 3: Parse the section and gate the requirement**

In `console/server.py`, change the opening of `load_engagement`:

```python
def load_engagement():
    eng = {"name": os.path.basename(ENG), "phases": [], "current": "", "writes": "direct", "scopes": []}
```

Replace the `## Phases` block inside the loop with a two-section version. The existing code uses a single `on` flag; replace it with a section name so both lists are read in one pass:

```python
            if ln.startswith("## Phases"):
                sect = "phases"; continue
            if ln.startswith("## Scopes"):
                sect = "scopes"; continue
            if ln.startswith("## "):
                sect = None
            if sect and ln.startswith("- "):
                name = ln[2:].strip()
                if sect == "phases":
                    if name.endswith("(current)"):
                        name = name[:-9].strip(); eng["current"] = name
                    eng["phases"].append(name)
                else:
                    eng["scopes"].append(name)
```

Rename the `on = False` initialiser above the loop to `sect = None`.

Add a helper beside `writes_direct()`:

```python
def required_on_create(kind):
    """The model's required fields, less Scope where the engagement names no scopes. Scope is the one
    field the model makes conditional on the engagement rather than on the type."""
    req = list(M.REQUIRED_ON_CREATE[kind])
    if not load_engagement()["scopes"]:
        req = [r for r in req if r != "scope"]
    return req
```

In `create()`, change the loop to use it:

```python
        for r in required_on_create(kind):
```

In `state()`, change the `create` key so the page is told the same truth:

```python
                      "choices": M.CHOICES, "required": M.REQUIRED_ON_ENTRY, "create": {k: required_on_create(k) for k in M.DIRS},
```

At the `integrity_of` call site on line 236, pass the scopes:

```python
    res = I.check(list(items.values()), phases=eng["phases"] or None, stakeholders=load_stakeholders() or None, today=today(), scopes=eng["scopes"] or None)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `make test`
Expected: PASS, including the suites that Task 1 may have broken, because `required_on_create` now drops `scope` for the scope-less engagements those tests build.

- [ ] **Step 5: Commit**

```bash
git add console/server.py console/tests/test_server_direct.py
git commit -m "Engagement declares its Scopes; Scope required on create only where it does

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: The baseline reads, edits and freezes Scope

**Files:**
- Modify: `console/baseline.py` (`COLS`, `EDITABLE`, the implied candidate dict near line 530, `freeze` near line 659)
- Test: `console/tests/test_baseline_supports.py`

**Interfaces:**
- Consumes: `M.SHORT` from Task 1, inherited scope on suggestions from Task 2.
- Produces: `map_header(["Domain"]) == ["scope"]`; `freeze()` raising `ValueError` when the engagement declares scopes and an accepted candidate has a blank or off-list Scope.

- [ ] **Step 1: Write the failing tests**

Add to `console/tests/test_baseline_supports.py`:

```python
class ScopeColumns(unittest.TestCase):
    def test_scope_header_maps(self):
        self.assertEqual(B.map_header(["Scope"]), ["scope"])

    def test_domain_header_maps_to_scope(self):
        self.assertEqual(B.map_header(["Domain"]), ["scope"])

    def test_service_and_area_map_to_scope(self):
        self.assertEqual(B.map_header(["Service", "Area"]), ["scope", "scope"])

    def test_scope_is_editable(self):
        self.assertIn("scope", B.EDITABLE)

    def test_owner_still_maps(self):
        self.assertEqual(B.map_header(["Owner"]), ["owner"])
```

Add the freeze cases. The fixture mirrors `BaselineSupports.setUp` at the top of the same file, with the failure-level offers dismissed so the freeze reaches the Scope guard rather than stopping at the supports guard:

```python
class ScopeFreeze(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); self.b = os.path.join(self.d, "baseline"); os.makedirs(self.b)
        open(os.path.join(self.b, "Limitations.md"), "w").write(PAGE)
        open(os.path.join(self.b, "Requirements.md"), "w").write(REQS)
        self.ids = [c["id"] for c in B.load_candidates(self.b)]
        B.apply_verdict(self.b, self.ids, "Accept")
        for x in B.suggestions(B.load_candidates(self.b), B.load_verdicts(self.b))["suggestions"]:
            if x["level"] == "fail":
                B.support_verdict(self.b, x["key"], "Dismiss", reason="test")

    def tearDown(self):
        shutil.rmtree(self.d)

    def run_freeze(self, scope, scopes):
        B.apply_verdict(self.b, self.ids, "Accept", fields={"scope": scope})
        eng = os.path.join(self.d, "eng"); os.makedirs(eng, exist_ok=True)
        return B.freeze(eng, self.b, B.load_candidates(self.b), B.load_verdicts(self.b),
                        "13 September 2026", "Adam", scopes=scopes or None)

    def test_freeze_refuses_a_blank_scope_when_scopes_declared(self):
        with self.assertRaises(ValueError) as e:
            self.run_freeze("", ["Access"])
        self.assertIn("Scope", str(e.exception))
        self.assertIn("(blank)", str(e.exception))

    def test_freeze_refuses_an_off_list_scope(self):
        with self.assertRaises(ValueError) as e:
            self.run_freeze("Nonsense", ["Access"])
        self.assertIn("Nonsense", str(e.exception))

    def test_freeze_accepts_a_listed_scope(self):
        self.assertTrue(self.run_freeze("Access", ["Access"])["ok"])

    def test_freeze_ignores_scope_when_none_declared(self):
        self.assertTrue(self.run_freeze("", [])["ok"])
```

`apply_verdict` takes `fields` as a dict of candidate keys, which is why `scope` must be in `EDITABLE` before this passes. `freeze` returns a dict with an `ok` key, as the existing freeze tests in this file show.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `make test`
Expected: FAIL. `test_domain_header_maps_to_scope` returning `['Domain']`, and the freeze tests with `TypeError` on the unexpected `scopes` argument.

- [ ] **Step 3: Map the column, allow the edit, inherit and guard the freeze**

In `console/baseline.py`, add to `COLS` directly above the `"title"` entry, so a narrow header is claimed before the broad ones:

```python
    "scope": ["scope", "domain", "service", "area"],
```

Add `"scope"` to the `EDITABLE` set.

In the implied candidate dict near line 530, add `scope` beside the other inherited fields:

```python
                "scope": f.get("scope", ""),
```

Change the `freeze` signature to take the engagement's scopes:

```python
def freeze(eng, bdir, cands, v, today, who, scopes=None):
```

Add a guard directly after the `if not records: raise ValueError("Nothing accepted yet.")` line:

```python
    if scopes:
        bad = [r for r in records if str(r.get("scope", "")).strip() not in scopes]
        if bad:
            vals = sorted({str(r.get("scope", "")).strip() or "(blank)" for r in bad})
            raise ValueError(f"{len(bad)} accepted item(s) have a Scope that is not one of the engagement's: "
                             + ", ".join(vals) + ". Fix them on the Candidates tab before the freeze.")
```

Find the caller of `freeze` in `console/server.py` and pass `scopes=load_engagement()["scopes"] or None`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `make test`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add console/baseline.py console/server.py console/tests/test_baseline_supports.py
git commit -m "Baseline maps Scope and Domain, edits Scope, and the freeze refuses an unlisted one

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: The console shows and sets Scope

**Files:**
- Modify: `console/static/app.js:259` (field editor), `:623` and `:746` (baseline bulk bar), `:631` (candidates table), `:653` (candidate editor), plus the register view filters

**Interfaces:**
- Consumes: `S.engagement.scopes` from Task 3's state API, `S.model.short` which now leads with `scope`.
- Produces: no interface for later tasks. This is the last code task.

There is no JavaScript test harness in this repository, so this task is verified in Chrome rather than by `make test`. Follow the steps in order and do not skip the browser check.

- [ ] **Step 1: Render Scope as a select in the field editor**

At `app.js:259`, beside the existing `phase` special case, add:

```javascript
  if (key === "scope") return `<div class="field">${lab}<select data-f="scope"><option value="">—</option>${(S.engagement.scopes || []).map(s => `<option ${s === val ? "selected" : ""}>${esc(s)}</option>`).join("")}</select></div>`;
```

Place it above the `phase` line so the two read together.

- [ ] **Step 2: Add Scope to the baseline bulk bar**

At `app.js:623`, beside the `bf-moscow` select, add:

```javascript
      ${(S.engagement.scopes || []).length ? `<select id="bf-scope"><option value="">set Scope…</option>${S.engagement.scopes.map(s => `<option>${esc(s)}</option>`).join("")}</select>` : ""}
```

At `app.js:746`, in the `fields` branch, add the read beside the others:

```javascript
const sc = ($("#bf-scope", m) || {}).value || ""; if (sc) fields.scope = sc;
```

- [ ] **Step 3: Show Scope in the candidates table and the candidate editor**

At `app.js:631`, add a cell beside the owner cell:

```javascript
      <td>${esc(c.scope)}</td>
```

Add a matching `<th>Scope</th>` to that table's header row.

At `app.js:653`, add Scope to the editor's field list, directly after Description:

```javascript
${f("Scope", c.scope)}
```

- [ ] **Step 4: Add a scope filter to the register views, and hide the column when there are none**

`register()` at `app.js:101` builds its columns as `["status", ...S.model.short[k]...]`, so the Scope column already appears once Task 1 is in. Two changes are needed there: drop it again when the engagement declares no scopes, and add the filter.

Add a module-level variable beside `let riskKind = "";` at line 100:

```javascript
let scopeFilter = "";
```

Replace `register()` with:

```javascript
function register(k) {
  let items = S.items.filter(i => i.kind === k);
  const scopes = S.engagement.scopes || [];
  let chips = "";
  if (k === "RSK") {
    if (riskKind) items = items.filter(i => i["risk-kind"] === riskKind);
    chips = `<div class="moves" style="--c:var(--rsk)">${["", "Risk", "Assumption", "Dependency"].map(v => `<button data-rk="${v}" class="${riskKind === v ? "on" : ""}">${v || "All"}</button>`).join("")}</div>`;
  }
  if (scopes.length) {
    if (scopeFilter) items = items.filter(i => i.scope === scopeFilter);
    chips += `<select id="flt-scope"><option value="">All scopes</option>${scopes.map(s => `<option ${s === scopeFilter ? "selected" : ""}>${esc(s)}</option>`).join("")}</select>`;
  }
  const cols = ["status", ...S.model.short[k].filter(f => f !== "owner" && (f !== "scope" || scopes.length)), "owner", "raised-on", "closed-on"];
  return head(`${S.model.names[k]}s`, `${items.length} item${items.length === 1 ? "" : "s"}. Click a row to open it.`, `${chips}<button class="primary" data-new="${k}">New ${S.model.names[k].toLowerCase()}</button>`) + table(items, cols);
}
```

Wire the select in the same delegated handler that already handles `data-rk`. Find that handler and add a sibling branch:

```javascript
  const fs = e.target.closest("#flt-scope");
  if (fs) { scopeFilter = fs.value; render(); return; }
```

Use a `change` listener rather than `click` for the select. If the existing handler is click-only, add a `change` listener beside it rather than converting the one that serves the risk chips.

- [ ] **Step 5: Verify in Chrome against the sample, which declares no scopes**

```bash
make down && make sample && make up
```

Wait two seconds, then open `http://localtest.me:8085/`. Confirm: no Scope column, no Scope filter, no "set Scope…" control anywhere, and creating an item does not ask for a Scope. The page must look exactly as it did before this task.

- [ ] **Step 6: Verify in Chrome against an engagement that declares scopes**

```bash
make down && make up ENG=engagements/abb-nokia
```

Wait two seconds, then open `http://localtest.me:8085/`. Confirm: the candidates table has a Scope column with values, the bulk bar offers "set Scope…" with the engagement's values, and the candidate editor shows Scope as a select. If the page renders blank, run `loadOnce()` in the page console to see the exception rather than reloading.

This step depends on Task 6 having seeded `## Scopes`. Do Task 6 first if the controls do not appear.

- [ ] **Step 7: Commit**

```bash
git add console/static/app.js
git commit -m "Console shows Scope, sets it in bulk, and filters the registers by it

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Seed abb-nokia and update the docs

**Files:**
- Modify: `engagements/abb-nokia/engagement.md` (untracked, gitignored, so it is not committed)
- Modify: `CLAUDE.md`, `console/README.md`

**Interfaces:**
- Consumes: everything above.
- Produces: nothing.

- [ ] **Step 1: Declare abb-nokia's scopes**

Append to `engagements/abb-nokia/engagement.md`, and change its `- Model version:` line to `2.27`:

```markdown
## Scopes

- NbnTC4Access
- SubscriberInternet
- CarrierEthernet
- CustomerENNI
- TC4 Internet
- TC4 CarrierEthernet Handoff
- Cross-service design
- Service model
- Order handling
- Fallout and intervention
- Northbound BSS integration
- Inventory and resources
- UIV service and resource model
- Identifier and VLAN management
- Port allocation
- Solution scope and criteria
```

These sixteen values are the taxonomy from `baseline/TSA SD-009 Scope Taxonomy.md`, which stays in `skip-pages.txt`.

- [ ] **Step 2: Check what the real baseline now says**

```bash
make down && make up ENG=engagements/abb-nokia
curl -s http://localhost:8085/api/baseline
```

Expected: every one of the 320 candidates carries a `scope`, including the nineteen from `CRs Register` which take theirs from the `Domain` column. Three values will be off the list and need a person: `NBN TC4 Access` on one row, `Pool Management` on one, `Location Management` on one. Report those to Adam rather than deciding them.

- [ ] **Step 3: Update CLAUDE.md**

In the "Rules that are not obvious from the code" section, add a bullet after the model bullet:

```markdown
- **Scope is declared per engagement, not by the model.** A `## Scopes` section in `engagement.md` names the values; an engagement without one carries no Scope, is never asked for one, and I24 never fires. `required_on_create()` in `server.py` is the only place that conditionality lives.
```

Update the "Open threads" date line and drop the Scope question if it appears there.

- [ ] **Step 4: Update console/README.md**

Read the file first and find where it describes what an engagement folder holds. Add one paragraph there, in the README's own voice:

```markdown
An engagement may declare its scopes in a `## Scopes` section of `engagement.md`, one value per line, the same shape as `## Phases`. Where it does, every item carries a Scope from that list, a new item cannot be created without one, the register views gain a scope filter and the pushed tables gain a Scope column. Where it does not, Scope does not exist for that engagement: nothing asks for it, no rule checks it, and the pushed tables are as they were.
```

Do not add a new top-level section if the README already has a place describing `engagement.md`.

- [ ] **Step 5: Run the full suite one last time**

Run: `make test`
Expected: PASS, all suites.

- [ ] **Step 6: Commit**

```bash
git add CLAUDE.md console/README.md
git commit -m "Docs: Scope is declared per engagement

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

## Notes for the implementer

**A pre-existing divergence you will notice and must not fix here.** Section 7 of the model document lists frontmatter as `... implemented-by, links, raised-on, closed-on, updated`, while `items.render_item` writes `... implemented-by, raised-on, closed-on, updated, links`. Links sits in a different place in the document from the code. This predates Scope and is out of scope for this plan. Leave both as they are and mention it to Adam.

**Why Scope is not in `REQUIRED_ON_ENTRY`.** Required on create is enough. A field required on entry to a later state would make an existing item unmovable until someone backfilled it, and the freeze already guarantees every frozen item has a Scope.

**Why the freeze guard reads `records` rather than the candidates.** `assemble()` has already folded merged duplicates into their leader by that point, so checking `records` checks what will actually be written, once per item rather than once per source row.
