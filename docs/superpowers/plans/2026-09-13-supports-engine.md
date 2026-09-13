# Supports Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The console reads the register model's implications as data, finds every item whose supporting items are missing, and offers each missing support as a prefilled item the reviewer accepts, edits or dismisses, in Baseline mode before the freeze and in Live mode as change set blocks.

**Architecture:** A `SUPPORTS` table in `console/model.py` beside `TRANSITIONS` declares each implication. A new pure module `console/integrity.py` evaluates section 9 rules and the `SUPPORTS` table over a list of item dicts and returns failures, warnings, prompts and suggestions with prefilled offers. `baseline.py` adapts candidates to that item shape and stores accepted offers as implied candidates in `verdicts.json`; `server.py` exposes the results and writes accepted offers as change set blocks through the existing `append_block`; `app.js` renders a Missing supports tab, a Supports panel and supports in the move dialog.

**Tech Stack:** Python 3.12 standard library only (no pip). Vanilla JS. Tests are `unittest` run inside the console Docker image. Nothing runs on the host but `make`, `docker`, `git` and `python3` for `make sample`.

**Spec:** `docs/superpowers/specs/2026-09-13-supports-engine-design.md`

## Global Constraints

- No new write path touches `requirements/`, `decisions/`, `limitations/`, `risks/`, `open-items/` or `change-requests/`. Only `baseline.freeze` writes item files. Live writes are change set blocks via `append_block`.
- The engine never creates a DEC in Accepted or Rejected, never creates a CR past Proposed, never fills Approved by, never guesses an owner for a REQ.
- `console/model.py` is the only place the console learns the model. Any new state, field, link word or rule goes there.
- Everything runs in Docker. Tests run as `make test`, which is `docker run --rm -v "$PWD/console:/app" -w /app python:3.12-slim python -m unittest discover -s tests -v`. Never run `python3 -m unittest` on the host.
- Australian English in every string a person reads. No em dashes. Documents carry a version and date near the top and are bumped on change.
- Model document bumps to 2.25 with a dated line at the top. `model.py`'s docstring names 2.25.
- Commits end with the attribution lines the session provides.
- The console container mounts `console/` over `/app`, so python changes need `make reload` and static changes need a browser reload. Chrome uses `http://localtest.me:8085/`, never localhost. Wait two seconds after `make up` or `make reload` before loading.

---

## File map

| Path | Responsibility |
|---|---|
| `Makefile` | new `test` target |
| `console/tests/__init__.py`, `console/tests/test_model.py`, `console/tests/test_integrity.py`, `console/tests/test_baseline_supports.py` | unit tests |
| `console/model.py` | `SUPPORTS` table, two link words, `RULES` descriptions for I21 to I23, docstring 2.25 |
| `console/integrity.py` | new: `check(items, phases=None, stakeholders=None)`, `offer(row, trigger)`, `suggestion_key(rule, trigger_id)` |
| `console/baseline.py` | `as_items`, `source_links`, implied candidates, support verdicts, freeze guard and cid remap |
| `console/server.py` | `integrity` in `/api/state`, `suggestions` in `/api/baseline`, `/api/baseline/support`, `/api/supports`, `/api/support/accept`, `/api/support/dismiss`, transition with supports |
| `console/static/app.js` | Missing supports tab, Supports panel, move dialog supports, Outstanding counts, SLT line |
| `console/static/guide.html`, `console/README.md`, `console/confluence-runbook.md`, `CLAUDE.md` | docs |
| `solution-register-model.md` | 2.25 |
| `console/sample-baseline/*.md`, `console/make-sample.py` | sample rows that trip the rules |

Item dict shape used throughout (what `server.parse_item` and `overlay` produce): keys `id`, `kind` (REQ, DEC, LIM, RSK, OI, CR), `status`, `title`, `links` (list of strings such as `"constrains REQ-0004"`), every frontmatter key in kebab-case (`owner`, `moscow`, `phase`, `implemented-by`, `chosen-option`, `vendor-ref`, `approved-by`, `consulted`, `risk-kind`, `due`, `raised-on`, `closed-on`), and every long field lower-cased (`source`, `notes`, `rationale`, `impact`, `options`, `reason`, `trigger`, `mitigation`, `next action`).

---

### Task 1: Test harness

**Files:**
- Modify: `Makefile` (after the `sample:` target)
- Create: `console/tests/__init__.py` (empty)
- Create: `console/tests/test_model.py`

**Interfaces:**
- Produces: `make test` running every `console/tests/test_*.py` in the `python:3.12-slim` image with `/app` as the working directory, so tests do `import model`, `import integrity`, `import baseline` directly.

- [ ] **Step 1: Add the make target**

Append to `Makefile` after the `sample:` block, and add `test` to the `.PHONY` line:

```make
# Unit tests for the console, run in the official python image. No host python.
test:
	docker run --rm -v "$(CURDIR)/console:/app" -w /app python:3.12-slim python -m unittest discover -s tests -v
```

Also add a line to the comment block at the top: `#   make test          run the console's unit tests inside the python image`.

- [ ] **Step 2: Write a first test**

`console/tests/__init__.py` is empty. `console/tests/test_model.py`:

```python
import unittest
import model as M


class ModelTables(unittest.TestCase):
    def test_every_transition_target_is_a_state(self):
        for kind, moves in M.TRANSITIONS.items():
            for frm, tos in moves.items():
                self.assertIn(frm, M.STATES[kind])
                for to in tos:
                    self.assertIn(to, M.STATES[kind], f"{kind} {frm} -> {to}")

    def test_first_state_is_first_listed(self):
        for kind, st in M.FIRST_STATE.items():
            self.assertEqual(st, M.STATES[kind][0])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run it**

Run: `make test`
Expected: `Ran 2 tests ... OK`

- [ ] **Step 4: Commit**

```bash
git add Makefile console/tests/__init__.py console/tests/test_model.py
git commit -m "Console unit tests run in the python image with make test"
```

---

### Task 2: The SUPPORTS table in model.py

**Files:**
- Modify: `console/model.py` (docstring line 1; `LINK_WORDS` at line 122; append `SUPPORTS` and `RULES` at the end, before `missing_for`)
- Test: `console/tests/test_model.py`

**Interfaces:**
- Produces: `M.SUPPORTS`, a list of dicts with keys `rule`, `check`, `level` (`"fail"` or `"warn"`), `when` (kind, list of states), `unless` (predicate string or `None`), `only_if` (predicate string or `None`), `offer` (`(kind, state)` or `None`), `link` (`(word on trigger, word on offer or None)`), `fields` (dict of target field key to template string), `prompt` (string for rows with no offer).
- Produces: `M.RULES`, dict of rule id to one-line description, for I21 to I23.
- Predicate strings, evaluated in Task 3: `"link:<word>"` (trigger has a link starting with that word), `"link:<word>:<KIND>"` (that link and its target id starts with KIND), `"linked:<word>:<KIND>:<state1>|<state2>"` (link exists and the target item is that kind in one of those states), `"field:<key>"` (field non-empty), `"tooling"` (chosen option text names something to build), `"unmet"` (chosen option text says the need is deferred or dropped).
- Template strings use `{key}` for any trigger field, plus `{id}`, `{title}`, `{chosen}` (the text of the chosen option line), `{beaten}` (the other option lines joined by "; ").

- [ ] **Step 1: Write the failing test**

Append to `console/tests/test_model.py` inside the class:

```python
    def test_supports_rows_are_well_formed(self):
        seen = set()
        for r in M.SUPPORTS:
            self.assertNotIn(r["rule"], seen); seen.add(r["rule"])
            kind, states = r["when"]
            self.assertIn(kind, M.STATES)
            for st in states:
                self.assertIn(st, M.STATES[kind], r["rule"])
            self.assertIn(r["level"], ("fail", "warn"))
            if r["offer"]:
                okind, ostate = r["offer"]
                self.assertIn(ostate, M.STATES[okind], r["rule"])
                self.assertEqual(ostate, M.FIRST_STATE[okind], f"{r['rule']} must offer the first state")
                word, oword = r["link"]
                self.assertIn(word, M.LINK_WORDS[kind], f"{r['rule']} link word {word} not registered for {kind}")
                if oword:
                    self.assertIn(oword, M.LINK_WORDS[okind], f"{r['rule']} reverse word {oword} not registered for {okind}")
            else:
                self.assertTrue(r.get("prompt"), r["rule"])

    def test_new_link_words(self):
        self.assertEqual(M.LINK_WORDS["RSK"]["mitigated by"], "OI")
        self.assertEqual(M.LINK_WORDS["LIM"]["needs"], "REQ")

    def test_rules_named(self):
        for n in ("I21", "I22", "I23"):
            self.assertIn(n, M.RULES)
```

- [ ] **Step 2: Run to see it fail**

Run: `make test`
Expected: FAIL, `AttributeError: module 'model' has no attribute 'SUPPORTS'`

- [ ] **Step 3: Add the table**

Change line 1 of `console/model.py` to `"""Register model 2.25 as data: types, states, transitions, the fields each move demands, and the supports each state implies.` and add `and SUPPORTS (4.4 and 5 as implications)` to the docstring's list of mirrored sections.

In `LINK_WORDS`, add `"mitigated by": "OI"` to the `RSK` entry and `"needs": "REQ"` to the `LIM` entry.

Append before `def missing_for`:

```python
# 4.4 and 5 read as implications: an item in `when` states must have `unless`; if it does not, offer
# the item in `offer`, linked by `link` (word written on the trigger, word written on the offer or None
# because section 5 derives the reverse). Rows with no offer are prompts: a field or a linked item's
# state that the reviewer must fix by hand. `check` names the section 9 rule the row serves.
# Templates may use any trigger field key plus {id}, {title}, {chosen} and {beaten}.
SUPPORTS = [
    dict(rule="S1", check="I3", level="fail", when=("REQ", ["Draft"]), unless="link:worked by", only_if=None,
         offer=("OI", "Open"), link=("worked by", None),
         fields={"title": "Agree REQ: {title}", "owner": "{owner}", "next action": "Confirm the need with {owner} and set Phase"}),
    dict(rule="S2", check="I3", level="fail", when=("DEC", ["Proposed"]), unless="link:proposed by", only_if=None,
         offer=("OI", "Open"), link=("proposed by", None),
         fields={"title": "Decide: {title}", "owner": "{owner}", "next action": "Take {id} to the approver"}),
    dict(rule="S3", check="I3", level="fail", when=("LIM", ["Under assessment"]), unless="link:assessed by", only_if=None,
         offer=("OI", "Open"), link=("assessed by", None),
         fields={"title": "Assess LIM: {title}", "owner": "{owner}", "next action": "Find the requirement this constrains; write constrains REQ-nnnn"}),
    dict(rule="S4", check="I7", level="fail", when=("LIM", ["Under assessment", "Accepted", "Change requested"]), unless="link:constrains", only_if=None,
         offer=("REQ", "Draft"), link=("constrains", None),
         fields={"title": "Need behind: {title}", "owner": "", "moscow": "Must", "implemented-by": "{implemented-by}"}),
    dict(rule="S5", check="I7", level="fail", when=("LIM", ["Accepted"]), unless="link:dispositioned by:DEC", only_if=None,
         offer=("DEC", "Proposed"), link=("dispositioned by", None),
         fields={"title": "Accept: {title}", "owner": "{owner}", "consulted": "Vendor", "implemented-by": "{implemented-by}",
                 "rationale": "Accepts {id} with option {chosen-option}: {chosen}. Beat: {beaten}"}),
    dict(rule="S6", check="I7", level="fail", when=("LIM", ["Change requested"]), unless="link:dispositioned by:CR", only_if=None,
         offer=("CR", "Proposed"), link=("dispositioned by", "triggered by"),
         fields={"title": "{chosen}", "owner": "{owner}", "reason": "{impact}", "chosen-option": "{chosen}", "implemented-by": "{implemented-by}"}),
    dict(rule="S7", check="I3", level="fail", when=("CR", ["Proposed", "For approval", "Submitted"]), unless="link:worked by", only_if=None,
         offer=("OI", "Open"), link=("worked by", None),
         fields={"title": "Progress CR: {title}", "owner": "{owner}", "next action": "Shape, estimate and take {id} to approval"}),
    dict(rule="S8", check="I10", level="fail", when=("CR", None), unless="link:triggered by", only_if=None,
         offer=("LIM", "Identified"), link=("triggered by", None),
         fields={"title": "Behind {id}: {title}", "owner": "{owner}", "impact": "{reason}", "implemented-by": "{implemented-by}",
                 "source": "Implied by {id}; vendor ref {vendor-ref}"}),
    dict(rule="S9", check="I13", level="fail", when=("RSK", ["Realised"]), unless="link:realised as", only_if=None,
         offer=("OI", "Open"), link=("realised as", None),
         fields={"title": "Respond: {title}", "owner": "{owner}", "next action": "{mitigation}"}),
    dict(rule="S10", check="I9", level="fail", when=("OI", ["Closed"]), unless="link:resolves into", only_if=None,
         offer=None, link=(None, None), fields={}, prompt="Add a resolves into link, or 'resolves into none: <reason>'."),
    dict(rule="S11", check="I8", level="fail", when=("DEC", ["Superseded"]), unless="link:superseded by", only_if=None,
         offer=("DEC", "Proposed"), link=("superseded by", "supersedes"),
         fields={"title": "{title}", "owner": "{owner}", "rationale": "{rationale}", "consulted": "{consulted}", "implemented-by": "{implemented-by}"}),
    dict(rule="S12", check="I7", level="fail", when=("LIM", ["Accepted"]), unless="linked:dispositioned by:DEC:Accepted", only_if="link:dispositioned by:DEC",
         offer=None, link=(None, None), fields={}, prompt="The accepting decision is not yet Accepted."),
    dict(rule="S13", check="I7", level="fail", when=("LIM", ["Change requested"]), unless="linked:dispositioned by:CR:Proposed|For approval|Approved|Submitted|Deferred|Delivered", only_if="link:dispositioned by:CR",
         offer=None, link=(None, None), fields={}, prompt="The change request was withdrawn or rejected: move this limitation back to Under assessment."),
    dict(rule="S14", check="I10", level="fail", when=("CR", ["Approved", "Submitted", "Delivered", "Deferred", "Withdrawn", "Rejected"]), unless="field:approved-by", only_if=None,
         offer=None, link=(None, None), fields={}, prompt="Approved by is empty."),
    dict(rule="S15", check="I2", level="fail", when=("LIM", ["Accepted", "Change requested"]), unless="field:chosen-option", only_if=None,
         offer=None, link=(None, None), fields={}, prompt="Impact, at least two Options and a Chosen option are needed."),
    dict(rule="S16", check="4.4", level="warn", when=("REQ", ["Designed", "Delivered", "Verified"]), unless="field:source", only_if=None,
         offer=None, link=(None, None), fields={}, prompt="Source or Links should name the design section."),
    dict(rule="S17", check="I21", level="fail", when=("RSK", ["Mitigating"]), unless="link:mitigated by", only_if="field:mitigation",
         offer=("OI", "Open"), link=("mitigated by", None),
         fields={"title": "Mitigate: {title}", "owner": "{owner}", "next action": "{mitigation}", "due": "{due}"}),
    dict(rule="S18", check="I22", level="warn", when=("LIM", ["Accepted"]), unless="link:needs", only_if="tooling",
         offer=("REQ", "Draft"), link=("needs", None),
         fields={"title": "{chosen}", "owner": "{owner}", "moscow": "Must", "implemented-by": "Internal"}),
    dict(rule="S19", check="I23", level="fail", when=("CR", ["Delivered"]), unless="link:delivers", only_if=None,
         offer=None, link=(None, None), fields={}, prompt="Add a delivers link to the requirement, then move that requirement."),
    dict(rule="S21", check="I7", level="warn", when=("LIM", ["Accepted"]), unless="linked:constrains:REQ:Withdrawn", only_if="unmet",
         offer=None, link=(None, None), fields={}, prompt="The chosen option leaves the need unmet: set the requirement to Won't or a later Phase, with a Deferred CR."),
]

# Section 9 rules added in 2.25. The numbered rules up to I20 are read from the model document; these
# are here so the console can print them beside a suggestion.
RULES = {
    "I21": "Every RSK in Mitigating whose Mitigation names an action has a mitigated by link to an open item.",
    "I22": "Every LIM in Accepted whose chosen option needs something built has a needs link to an internal REQ (warning).",
    "I23": "Every CR in Delivered has a delivers link to the requirement it delivered.",
}
```

Note the `when` state list `None` on S8 means every state.

- [ ] **Step 4: Run tests**

Run: `make test`
Expected: `Ran 5 tests ... OK`

- [ ] **Step 5: Commit**

```bash
git add console/model.py console/tests/test_model.py
git commit -m "Model 2.25 as data: SUPPORTS table, mitigated by and needs link words, rules I21 to I23"
```

---

### Task 3: integrity.py: predicates and suggestions

**Files:**
- Create: `console/integrity.py`
- Test: `console/tests/test_integrity.py`

**Interfaces:**
- Produces: `integrity.check(items, phases=None, stakeholders=None) -> dict` with keys `failures`, `warnings` (lists of `{"rule", "id", "text"}`), `prompts` (list of `{"rule", "check", "level", "id", "text"}`) and `suggestions` (list of `{"key", "rule", "check", "level", "id", "kind", "status", "fields", "link", "reverse", "needsOwner"}`), where `fields` is the prefilled offer (keys as item keys), `link` is the string to add to the trigger's links once the offer has an id, written as `"<word> "` with the id appended by the caller, and `reverse` is the string to add to the offer's links, already complete (`"triggered by LIM-0004"`) or `None`.
- Produces: `integrity.suggestion_key(rule, trigger_id) -> str` (stable, `"s"` plus ten hex chars).
- Produces: `integrity.offer(row, trigger) -> dict` (the `fields` for one row and one trigger).
- Consumes: `M.SUPPORTS`, `M.LINK_WORDS`, `M.STATES`.
- `items` is a list of item dicts (shape in the file map). Ids may be provisional (`LIM-0002.3`) or candidate keys (`c1a2b3c4d5`, `i1a2b3c4d5`); the module never parses ids beyond a prefix check.

- [ ] **Step 1: Write the failing tests for the predicates and suggestions**

`console/tests/test_integrity.py`:

```python
import unittest
import integrity as I


def item(id, status, **f):
    kind = id.split("-")[0]
    base = {"id": id, "kind": kind, "status": status, "title": f.pop("title", id + " title"), "links": f.pop("links", []),
            "owner": f.pop("owner", "Priya Nair"), "implemented-by": f.pop("implemented-by", "Vendor"), "source": f.pop("source", "workshop")}
    base.update(f)
    return base


def sug(res, rule, id):
    return [s for s in res["suggestions"] if s["rule"] == rule and s["id"] == id]


class Suggestions(unittest.TestCase):
    def test_key_is_stable(self):
        self.assertEqual(I.suggestion_key("S5", "LIM-0001"), I.suggestion_key("S5", "LIM-0001"))
        self.assertNotEqual(I.suggestion_key("S5", "LIM-0001"), I.suggestion_key("S4", "LIM-0001"))
        self.assertRegex(I.suggestion_key("S5", "LIM-0001"), r"^s[0-9a-f]{10}$")

    def test_s1_draft_requirement_offers_open_item(self):
        r = I.check([item("REQ-0001", "Draft", moscow="Must")])
        s = sug(r, "S1", "REQ-0001")
        self.assertEqual(len(s), 1)
        self.assertEqual(s[0]["kind"], "OI"); self.assertEqual(s[0]["status"], "Open")
        self.assertEqual(s[0]["fields"]["title"], "Agree REQ: REQ-0001 title")
        self.assertEqual(s[0]["fields"]["owner"], "Priya Nair")
        self.assertEqual(s[0]["link"], "worked by "); self.assertIsNone(s[0]["reverse"])
        self.assertFalse(s[0]["needsOwner"])

    def test_s1_silent_when_link_present(self):
        r = I.check([item("REQ-0001", "Draft", moscow="Must", links=["worked by OI-0003"]), item("OI-0003", "Open")])
        self.assertEqual(sug(r, "S1", "REQ-0001"), [])

    def test_s4_requirement_offer_needs_owner(self):
        r = I.check([item("LIM-0001", "Under assessment", impact="x", links=["assessed by OI-0001"]), item("OI-0001", "Open")])
        s = sug(r, "S4", "LIM-0001")
        self.assertEqual(len(s), 1)
        self.assertTrue(s[0]["needsOwner"]); self.assertEqual(s[0]["fields"]["owner"], "")

    def test_s5_accepted_limitation_offers_proposed_decision_with_rationale(self):
        lim = item("LIM-0002", "Accepted", impact="Two invoice lines", options="1. Live with it; impact: none; phase: P1\n2. Ask vendor; impact: $40k; phase: P2",
                   **{"chosen-option": "1"}, links=["constrains REQ-0001"])
        r = I.check([lim, item("REQ-0001", "Agreed", moscow="Must")])
        s = sug(r, "S5", "LIM-0002")
        self.assertEqual(len(s), 1)
        self.assertEqual(s[0]["kind"], "DEC"); self.assertEqual(s[0]["status"], "Proposed")
        self.assertIn("Live with it", s[0]["fields"]["rationale"]); self.assertIn("Ask vendor", s[0]["fields"]["rationale"])
        self.assertEqual(s[0]["fields"]["consulted"], "Vendor")
        self.assertNotIn("approved-by", s[0]["fields"])

    def test_s5_unless_honours_target_kind(self):
        lim = item("LIM-0002", "Accepted", **{"chosen-option": "1"}, links=["constrains REQ-0001", "dispositioned by CR-0001"])
        r = I.check([lim, item("REQ-0001", "Agreed", moscow="Must"), item("CR-0001", "Proposed", reason="r", links=["triggered by LIM-0002"])])
        self.assertEqual(len(sug(r, "S5", "LIM-0002")), 1)

    def test_s6_change_requested_offers_cr_with_reverse_link(self):
        lim = item("LIM-0003", "Change requested", impact="No SMS", options="1. Add SMS; impact: $20k; phase: P1\n2. Accept; impact: none; phase: P1",
                   **{"chosen-option": "1"}, links=["constrains REQ-0001"])
        r = I.check([lim, item("REQ-0001", "Agreed", moscow="Must")])
        s = sug(r, "S6", "LIM-0003")[0]
        self.assertEqual(s["kind"], "CR"); self.assertEqual(s["fields"]["title"], "Add SMS")
        self.assertEqual(s["fields"]["reason"], "No SMS"); self.assertEqual(s["reverse"], "triggered by LIM-0003")
        self.assertEqual(s["link"], "dispositioned by ")

    def test_s8_any_cr_without_trigger_offers_limitation(self):
        r = I.check([item("CR-0001", "Submitted", reason="Vendor CR 77", **{"vendor-ref": "VCR-77", "approved-by": "SLT"})])
        s = sug(r, "S8", "CR-0001")
        self.assertEqual(len(s), 1); self.assertEqual(s[0]["kind"], "LIM"); self.assertEqual(s[0]["status"], "Identified")
        self.assertIn("VCR-77", s[0]["fields"]["source"])

    def test_s12_prompt_when_decision_not_accepted(self):
        lim = item("LIM-0002", "Accepted", **{"chosen-option": "1"}, links=["constrains REQ-0001", "dispositioned by DEC-0001"])
        r = I.check([lim, item("REQ-0001", "Agreed", moscow="Must"), item("DEC-0001", "Proposed", rationale="x")])
        self.assertEqual(sug(r, "S5", "LIM-0002"), [])
        self.assertEqual([p["rule"] for p in r["prompts"] if p["id"] == "LIM-0002"], ["S12"])

    def test_s13_prompt_when_cr_withdrawn(self):
        lim = item("LIM-0003", "Change requested", **{"chosen-option": "1"}, links=["constrains REQ-0001", "dispositioned by CR-0001"])
        r = I.check([lim, item("REQ-0001", "Agreed", moscow="Must"), item("CR-0001", "Withdrawn", reason="x", links=["triggered by LIM-0003"], **{"approved-by": "SLT"})])
        self.assertIn("S13", [p["rule"] for p in r["prompts"] if p["id"] == "LIM-0003"])

    def test_s17_only_when_mitigation_text(self):
        with_text = item("RSK-0001", "Mitigating", **{"risk-kind": "Risk"}, trigger="t", mitigation="Weekly report", due="1 October 2026")
        without = item("RSK-0002", "Mitigating", **{"risk-kind": "Risk"}, trigger="t", mitigation="")
        r = I.check([with_text, without])
        self.assertEqual(len(sug(r, "S17", "RSK-0001")), 1)
        self.assertEqual(sug(r, "S17", "RSK-0001")[0]["fields"]["next action"], "Weekly report")
        self.assertEqual(sug(r, "S17", "RSK-0002"), [])

    def test_s18_tooling_warning(self):
        lim = item("LIM-0004", "Accepted", options="1. Build a report to find affected cases; impact: 2 days; phase: P1\n2. Ignore; impact: none; phase: P1",
                   **{"chosen-option": "1"}, links=["constrains REQ-0001", "dispositioned by DEC-0001"])
        r = I.check([lim, item("REQ-0001", "Agreed", moscow="Must"), item("DEC-0001", "Accepted", rationale="x", consulted="Vendor", **{"approved-by": "SLT", "closed-on": "1 September 2026"})])
        s = sug(r, "S18", "LIM-0004")
        self.assertEqual(len(s), 1); self.assertEqual(s[0]["level"], "warn")
        self.assertEqual(s[0]["fields"]["implemented-by"], "Internal")
        self.assertEqual(s[0]["fields"]["title"], "Build a report to find affected cases")

    def test_s21_unmet_warning(self):
        lim = item("LIM-0005", "Accepted", options="1. Defer to a later phase; impact: none now; phase: P2\n2. Fix; impact: $; phase: P1",
                   **{"chosen-option": "1"}, links=["constrains REQ-0001", "dispositioned by DEC-0001"])
        r = I.check([lim, item("REQ-0001", "Agreed", moscow="Must", phase="P1"), item("DEC-0001", "Accepted", rationale="x", consulted="V", **{"approved-by": "SLT", "closed-on": "1 September 2026"})])
        self.assertIn("S21", [p["rule"] for p in r["prompts"] if p["id"] == "LIM-0005"])

    def test_offer_never_carries_approved_by(self):
        for row in [r for r in I.M.SUPPORTS if r["offer"]]:
            self.assertNotIn("approved-by", row["fields"], row["rule"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run to see it fail**

Run: `make test`
Expected: FAIL, `ModuleNotFoundError: No module named 'integrity'`

- [ ] **Step 3: Write integrity.py (suggestions half)**

```python
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
    return [l.strip() for l in str(item.get("options", "") or "").splitlines() if l.strip()]


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
        if val:
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
```

- [ ] **Step 4: Run tests**

Run: `make test`
Expected: all Suggestions tests pass. If `test_s5_unless_honours_target_kind` fails, check that `link:dispositioned by:DEC` rejects a CR target: the target id `CR-0001` starts with `CR-`, so `_predicate` must return False for it, and S5 fires.

- [ ] **Step 5: Commit**

```bash
git add console/integrity.py console/tests/test_integrity.py
git commit -m "integrity.py: SUPPORTS evaluated over items into suggestions and prompts"
```

---

### Task 4: integrity.py: section 9 rules

**Files:**
- Modify: `console/integrity.py` (replace the stub `rules`)
- Test: `console/tests/test_integrity.py`

**Interfaces:**
- Produces: `rules(items, by_id, phases, stakeholders) -> (failures, warnings)` implementing I1, I2, I3, I4, I5, I6, I7, I8, I9, I10, I11, I12, I13, I14, I15, I16, I17, I19. I18 (current-state claims) and I20 (a transition check, done in `server.transition`) are skipped. I5 and I19 run only when `phases` or `stakeholders` are given. Each entry is `{"rule", "id", "text"}`.

- [ ] **Step 1: Write the failing tests**

Append to `console/tests/test_integrity.py`:

```python
def fails(res, rule):
    return sorted(f["id"] for f in res["failures"] if f["rule"] == rule)


def warns(res, rule):
    return sorted(f["id"] for f in res["warnings"] if f["rule"] == rule)


class Rules(unittest.TestCase):
    def test_i1_duplicate_id(self):
        r = I.check([item("REQ-0001", "Agreed", moscow="Must"), item("REQ-0001", "Agreed", moscow="Must")])
        self.assertEqual(fails(r, "I1"), ["REQ-0001"])

    def test_i2_status_and_required(self):
        r = I.check([item("REQ-0001", "Nonsense", moscow="Must"), item("REQ-0002", "Draft", moscow="", links=["worked by OI-0001"]), item("OI-0001", "Open", **{"next action": "x"})])
        self.assertEqual(fails(r, "I2"), ["REQ-0001", "REQ-0002"])

    def test_i2_closed_on_in_terminal(self):
        r = I.check([item("DEC-0001", "Accepted", rationale="x", consulted="V", **{"approved-by": "SLT"})])
        self.assertIn("DEC-0001", fails(r, "I2"))

    def test_i3_owner(self):
        r = I.check([item("REQ-0001", "Agreed", moscow="Must", owner="")])
        self.assertEqual(fails(r, "I3"), ["REQ-0001"])

    def test_i4_next_action(self):
        r = I.check([item("OI-0001", "Open", **{"next action": ""})])
        self.assertEqual(fails(r, "I4"), ["OI-0001"])

    def test_i5_phase_when_given(self):
        r = I.check([item("REQ-0001", "Agreed", moscow="Must", phase="P9")], phases=["P1", "P2"])
        self.assertEqual(fails(r, "I5"), ["REQ-0001"])
        self.assertEqual(fails(I.check([item("REQ-0001", "Agreed", moscow="Must", phase="P9")]), "I5"), [])

    def test_i6_link_target_exists(self):
        r = I.check([item("REQ-0001", "Agreed", moscow="Must", links=["worked by OI-0099"])])
        self.assertEqual(fails(r, "I6"), ["REQ-0001"])

    def test_i7_dispositions(self):
        r = I.check([item("LIM-0001", "Identified", links=["dispositioned by DEC-0001"]), item("DEC-0001", "Accepted", rationale="x", consulted="V", **{"approved-by": "S", "closed-on": "1 September 2026"})])
        self.assertEqual(fails(r, "I7"), ["LIM-0001"])

    def test_i9_closed_open_item(self):
        r = I.check([item("OI-0001", "Closed", **{"next action": "x", "closed-on": "1 September 2026"})])
        self.assertEqual(fails(r, "I9"), ["OI-0001"])

    def test_i11_decision_approval(self):
        r = I.check([item("DEC-0001", "Accepted", rationale="x", consulted="", **{"approved-by": "S", "closed-on": "1 September 2026"})])
        self.assertEqual(fails(r, "I11"), ["DEC-0001"])

    def test_i12_implemented_by(self):
        r = I.check([item("REQ-0001", "Agreed", moscow="Must", **{"implemented-by": ""})])
        self.assertEqual(fails(r, "I12"), ["REQ-0001"])

    def test_i14_source(self):
        r = I.check([item("REQ-0001", "Agreed", moscow="Must", source="")])
        self.assertEqual(fails(r, "I14"), ["REQ-0001"])

    def test_i15_i16_warnings(self):
        r = I.check([item("DEC-0001", "Proposed", rationale="Chose X over Y", **{"raised-on": "1 January 2026"}, links=["proposed by OI-0001"]), item("OI-0001", "Open", **{"next action": "x"})], today="13 September 2026")
        self.assertEqual(warns(r, "I15"), ["DEC-0001"])
        self.assertEqual(warns(r, "I16"), ["DEC-0001"])

    def test_i17_deferred_cr(self):
        r = I.check([item("CR-0001", "Deferred", reason="x", phase="", links=["triggered by LIM-0001", "worked by OI-0001"], **{"approved-by": "S", "closed-on": "1 September 2026"}),
                     item("LIM-0001", "Change requested", **{"chosen-option": "1"}, links=["constrains REQ-0001", "dispositioned by CR-0001"]), item("REQ-0001", "Agreed", moscow="Must"), item("OI-0001", "Open", **{"next action": "x"})])
        self.assertEqual(fails(r, "I17"), ["CR-0001"])

    def test_i19_stakeholders_when_given(self):
        r = I.check([item("REQ-0001", "Agreed", moscow="Must", owner="Nobody Known")], stakeholders=[{"name": "Priya Nair", "role": "Owner"}])
        self.assertEqual(fails(r, "I19"), ["REQ-0001"])
        r = I.check([item("REQ-0001", "Agreed", moscow="Must", owner="Vendor: Nokia")], stakeholders=[{"name": "Priya Nair", "role": "Owner"}])
        self.assertEqual(fails(r, "I19"), [])
```

Note `check` gains an optional `today` argument (a date string in the register's `D Month YYYY` form) for I15; default is the real date.

- [ ] **Step 2: Run to see them fail**

Run: `make test`
Expected: the Rules tests fail with empty lists.

- [ ] **Step 3: Implement the rules**

Replace the `check` and `rules` stubs in `console/integrity.py`:

```python
import datetime

MONTHS = "January February March April May June July August September October November December".split()


def parse_date(s):
    m = re.match(r"^(\d{1,2}) (\w+) (\d{4})", str(s or ""))
    if not m or m.group(2) not in MONTHS:
        return None
    return datetime.date(int(m.group(3)), MONTHS.index(m.group(2)) + 1, int(m.group(1)))


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
                ok = not v or v in names or v.startswith("Vendor:") or v == "Joint"
                if not ok:
                    fail("I19", it, f"{M.LABELS.get(key, key)} {v!r} is not a known stakeholder")
                if key == "owner" and v in mentioned:
                    fail("I19", it, f"Owner {v!r} has role Mentioned")
    return F, W
```

- [ ] **Step 4: Run tests**

Run: `make test`
Expected: all pass. If `test_i2_status_and_required` reports REQ-0001 twice under I2, that is fine: the assertion sorts ids and compares to `["REQ-0001", "REQ-0002"]`, so dedupe by using `sorted(set(...))` in the `fails` helper.

- [ ] **Step 5: Commit**

```bash
git add console/integrity.py console/tests/test_integrity.py
git commit -m "integrity.py: section 9 rules I1 to I19 over item dicts"
```

---

### Task 5: Baseline adapter and implied candidates

**Files:**
- Modify: `console/baseline.py`
- Test: `console/tests/test_baseline_supports.py`

**Interfaces:**
- Produces: `B.LINK_NOTE_WORDS` (module-level dict hoisted from `freeze`'s local `words`).
- Produces: `B.source_links(c, refmap) -> list[str]`: links a candidate's Notes carry, with source ids remapped to candidate ids where `refmap` (source ref or `"<page> · <ref>"` to cid) resolves; unresolved ones are dropped.
- Produces: `B.status_of(c) -> str`: the status the candidate would be frozen with (the rule in `assemble`).
- Produces: `B.as_items(cands, v) -> list[dict]`: the accepted candidates (verdict Accept, merged rows folded) plus implied candidates, as item dicts with `id` = cid, `links` = verdict links + source links + implied links, `status` = `status_of`.
- Produces: `B.load_implied(bdir)`, `B.SUPPORTS_KEY = "_supports"`, `B.IMPLIED_KEY = "_implied"`.
- Produces: `B.support_verdict(bdir, key, verdict, reason="", fields=None, sugg=None) -> dict`: verdict is `"Accept"`, `"Dismiss"` or `"Reassess"`. Accept creates an implied candidate (id `"i" + key[1:]`), stores it under `_implied` with verdict Accept, adds the trigger's link (`sugg["link"] + implied id`) to the trigger's verdict `links`, and the reverse link to the implied candidate. Reassess sets the trigger's `fields.status` to `"Under assessment"`. Dismiss records `{verdict, reason}` under `_supports[key]`. Raises `ValueError` when Accept has `needsOwner` and no owner in `fields`.
- Produces: `B.suggestions(cands, v) -> dict`: `integrity.check(as_items(cands, v))` with dismissed keys removed and each suggestion annotated with `recommend` (`"Reconstruct"` or `"Reassess"`, only on rows whose trigger is a LIM claiming Accepted or Change requested) and `triggerTitle`.
- Modify `load_candidates` to append `load_implied(bdir)`.
- Modify `apply_verdict` to accept `links` (a list, replaces) alongside `fields`.
- Modify `effective` to expose `links` (verdict links, default `[]`) and `implied` (bool).
- Modify `assemble` so records carry `links` from the effective candidate.
- Modify `freeze`: refuse when any `level == "fail"` suggestion is undecided; remap candidate ids in links to new ids; write links from records; list implied items in `frozen.md`.

- [ ] **Step 1: Write the failing tests**

`console/tests/test_baseline_supports.py`:

```python
import unittest, tempfile, os, json, shutil
import baseline as B
import model as M

PAGE = """---
page-id: 1
page-title: Limitations
---

# Limitations

| Ref | Limitation | Status | Impact | Options | Chosen option | Owner | Rationale | Links |
|---|---|---|---|---|---|---|---|---|
| LIM-001 | One channel per customer | Accepted | Email only on day one | 1. Live with it; impact: none; phase: P1 2. Add SMS; impact: $40k; phase: P2 | 1 | Priya Nair | Volume is low | constrains REQ-001 |
| LIM-002 | No bulk port | Change requested | Ops cannot port in bulk | 1. Vendor adds bulk; impact: $20k; phase: P1 2. Manual; impact: 2 FTE; phase: P1 | 1 | Tom Okafor | | |
"""
REQS = """---
page-id: 2
page-title: Requirements
---

# Requirements

| Ref | Requirement | MoSCoW | Owner | Status |
|---|---|---|---|---|
| REQ-001 | Email and SMS notifications | Must | Priya Nair | Agreed |
"""


class BaselineSupports(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); self.b = os.path.join(self.d, "baseline"); os.makedirs(self.b)
        open(os.path.join(self.b, "Limitations.md"), "w").write(PAGE)
        open(os.path.join(self.b, "Requirements.md"), "w").write(REQS)
        self.cands = B.load_candidates(self.b)
        B.apply_verdict(self.b, [c["id"] for c in self.cands], "Accept")

    def tearDown(self):
        shutil.rmtree(self.d)

    def cid(self, ref):
        return next(c["id"] for c in B.load_candidates(self.b) if c["ref"] == ref)

    def test_as_items_maps_source_links_to_candidate_ids(self):
        items = B.as_items(B.load_candidates(self.b), B.load_verdicts(self.b))
        lim = next(i for i in items if i["id"] == self.cid("LIM-001"))
        self.assertEqual(lim["status"], "Accepted")
        self.assertEqual(lim["links"], ["constrains " + self.cid("REQ-001")])

    def test_suggestions_offer_dec_and_cr_with_recommendation(self):
        s = B.suggestions(B.load_candidates(self.b), B.load_verdicts(self.b))["suggestions"]
        by = {(x["rule"], x["id"]): x for x in s}
        self.assertEqual(by[("S5", self.cid("LIM-001"))]["recommend"], "Reconstruct")
        self.assertEqual(by[("S6", self.cid("LIM-002"))]["recommend"], "Reconstruct")
        self.assertIn(("S4", self.cid("LIM-002")), by)
        self.assertNotIn(("S4", self.cid("LIM-001")), by)

    def test_accept_creates_implied_candidate_linked_both_ways(self):
        s = B.suggestions(B.load_candidates(self.b), B.load_verdicts(self.b))["suggestions"]
        x = next(x for x in s if x["rule"] == "S6")
        B.support_verdict(self.b, x["key"], "Accept", sugg=x)
        v = B.load_verdicts(self.b)
        imp = v[B.IMPLIED_KEY][0]
        self.assertEqual(imp["id"], "i" + x["key"][1:]); self.assertEqual(imp["kind"], "CR")
        self.assertTrue(imp["implied"]); self.assertEqual(v[imp["id"]]["verdict"], "Accept")
        self.assertIn("triggered by " + x["id"], imp["links"])
        self.assertIn("dispositioned by " + imp["id"], v[x["id"]]["links"])
        again = B.suggestions(B.load_candidates(self.b), v)["suggestions"]
        self.assertFalse(any(y["rule"] == "S6" for y in again))
        self.assertTrue(any(y["rule"] == "S7" and y["id"] == imp["id"] for y in again))

    def test_accept_requires_owner_where_offer_has_none(self):
        s = B.suggestions(B.load_candidates(self.b), B.load_verdicts(self.b))["suggestions"]
        x = next(x for x in s if x["rule"] == "S4")
        with self.assertRaises(ValueError):
            B.support_verdict(self.b, x["key"], "Accept", sugg=x)
        B.support_verdict(self.b, x["key"], "Accept", sugg=x, fields={"owner": "Tom Okafor"})
        self.assertEqual(B.load_verdicts(self.b)[B.IMPLIED_KEY][0]["owner"], "Tom Okafor")

    def test_dismiss_hides_until_trigger_changes(self):
        s = B.suggestions(B.load_candidates(self.b), B.load_verdicts(self.b))["suggestions"]
        x = next(x for x in s if x["rule"] == "S5")
        B.support_verdict(self.b, x["key"], "Dismiss", reason="decision is on the vendor page")
        again = B.suggestions(B.load_candidates(self.b), B.load_verdicts(self.b))
        self.assertFalse(any(y["key"] == x["key"] for y in again["suggestions"]))
        self.assertEqual(again["dismissed"], 1)

    def test_reassess_drops_limitation_to_under_assessment(self):
        s = B.suggestions(B.load_candidates(self.b), B.load_verdicts(self.b))["suggestions"]
        x = next(x for x in s if x["rule"] == "S5")
        B.support_verdict(self.b, x["key"], "Reassess", sugg=x)
        again = B.suggestions(B.load_candidates(self.b), B.load_verdicts(self.b))["suggestions"]
        self.assertTrue(any(y["rule"] == "S3" and y["id"] == x["id"] for y in again))
        self.assertFalse(any(y["rule"] == "S5" for y in again))

    def test_freeze_refuses_with_undecided_failures_and_remaps_links(self):
        eng = os.path.join(self.d, "eng"); os.makedirs(eng)
        with self.assertRaises(ValueError) as e:
            B.freeze(eng, self.b, B.load_candidates(self.b), B.load_verdicts(self.b), "13 September 2026", "Adam")
        self.assertIn("support", str(e.exception).lower())
        for x in B.suggestions(B.load_candidates(self.b), B.load_verdicts(self.b))["suggestions"]:
            if x["level"] == "fail":
                B.support_verdict(self.b, x["key"], "Dismiss", reason="test")
        r = B.freeze(eng, self.b, B.load_candidates(self.b), B.load_verdicts(self.b), "13 September 2026", "Adam")
        self.assertTrue(r["ok"])
        lim = open(os.path.join(eng, "limitations", "LIM-0001.md")).read()
        self.assertIn("constrains REQ-0001", lim)
        self.assertNotIn("constrains c", lim)

    def test_freeze_lists_implied(self):
        eng = os.path.join(self.d, "eng"); os.makedirs(eng)
        for x in B.suggestions(B.load_candidates(self.b), B.load_verdicts(self.b))["suggestions"]:
            if x["level"] == "fail":
                B.support_verdict(self.b, x["key"], "Accept", sugg=x, fields={"owner": "Tom Okafor"})
        while True:
            left = [x for x in B.suggestions(B.load_candidates(self.b), B.load_verdicts(self.b))["suggestions"] if x["level"] == "fail"]
            if not left: break
            for x in left: B.support_verdict(self.b, x["key"], "Accept", sugg=x, fields={"owner": "Tom Okafor"})
        B.freeze(eng, self.b, B.load_candidates(self.b), B.load_verdicts(self.b), "13 September 2026", "Adam")
        frozen = open(os.path.join(self.b, "frozen.md")).read()
        self.assertIn("## Implied at baseline", frozen)
        self.assertIn("S6", frozen)
```

- [ ] **Step 2: Run to see them fail**

Run: `make test`
Expected: FAIL on `B.as_items` missing.

- [ ] **Step 3: Implement in baseline.py**

Add `import integrity as I` at the top. Hoist the `words` dict out of `freeze` to module level as `LINK_NOTE_WORDS` and make `freeze` use it. Then add after `effective`:

```python
IMPLIED_KEY = "_implied"
SUPPORTS_KEY = "_supports"


def load_implied(bdir):
    return list(load_verdicts(bdir).get(IMPLIED_KEY, []))


def status_of(c):
    k = c["kind"]
    return c.get("status") or next((st for st in M.STATES[k] if st.lower() == (c.get("source_status") or "").lower()), M.FIRST_STATE[k])


def refmap_of(cands):
    """Source ref -> candidate id, the way the freeze maps refs to new ids: a full model-form id is unique
    across the source, a bare number only within its page."""
    m = {}
    for c in cands:
        if c["ref"]:
            m[c["ref"] if LINK_RE.fullmatch(c["ref"]) else f"{c['page']} · {c['ref']}"] = c["id"]
    return m


def source_links(c, refmap):
    out = []
    for n in (c.get("notes") or "").split("\n"):
        m = re.match(r"(" + "|".join(LINK_NOTE_WORDS) + r"): (.+)", n)
        if not (m and LINK_RE.search(m.group(2))):
            continue
        word = LINK_NOTE_WORDS[m.group(1)]
        for part in re.split(r"[;,]\s*", m.group(2)):
            part = part.strip()
            idm = LINK_RE.search(part)
            if not idm:
                continue
            ref = f"{idm.group(1)}-{idm.group(2)}"
            cid = refmap.get(ref) or refmap.get(f"{idm.group(1)}{idm.group(2)}") or refmap.get(f"{c['page']} · {ref}")
            if not cid:
                continue
            lead = part[:idm.start()].strip().lower()
            out.append(((lead or word) + " " + cid).strip() if (lead or word) else cid)
    return out


def as_items(cands, v):
    """Accepted candidates and implied ones as item dicts for integrity.check. Ids are candidate ids."""
    refmap = refmap_of(cands)
    eff = {c["id"]: effective(c, v) for c in cands}
    merged_into = {}
    for c in eff.values():
        if c["verdict"] == "Merge" and c["mergedInto"] in eff:
            merged_into.setdefault(c["mergedInto"], []).append(c)
    items = []
    for c in eff.values():
        if c["verdict"] != "Accept":
            continue
        k = c["kind"]
        c, _ = fold_merged(c, merged_into.get(c["id"], []), k)
        it = {key: (val if isinstance(val, str) else val) for key, val in c.items()}
        it["status"] = status_of(c)
        it["links"] = list(dict.fromkeys(list(c.get("links") or []) + source_links(c, refmap) + sum((source_links(m, refmap) for m in merged_into.get(c["id"], [])), [])))
        if k == "CR" and not it.get("reason"):
            it["reason"] = c.get("rationale", "")
        items.append(it)
    return items


def suggestions(cands, v):
    res = I.check(as_items(cands, v))
    done = v.get(SUPPORTS_KEY, {})
    byc = {c["id"]: c for c in cands}
    kept = []
    for s in res["suggestions"]:
        if done.get(s["key"], {}).get("verdict") == "Dismiss":
            continue
        trig = byc.get(s["id"], {})
        s["triggerTitle"] = trig.get("title", "")
        s["triggerPage"] = trig.get("page", "")
        if s["rule"] in ("S5", "S6"):
            s["recommend"] = "Reconstruct" if (effective(trig, v).get("rationale") or effective(trig, v).get("chosen-option")) else "Reassess"
        kept.append(s)
    res["suggestions"] = kept
    res["dismissed"] = sum(1 for e in done.values() if e.get("verdict") == "Dismiss")
    return res


def support_verdict(bdir, key, verdict, reason="", fields=None, sugg=None):
    v = load_verdicts(bdir)
    fields = fields or {}
    if verdict == "Dismiss":
        v.setdefault(SUPPORTS_KEY, {})[key] = {"verdict": "Dismiss", "reason": reason}
    elif verdict == "Reassess":
        if not sugg:
            raise ValueError("Reassess needs the suggestion.")
        e = v.setdefault(sugg["id"], {}); e.setdefault("fields", {})["status"] = "Under assessment"
        e["links"] = [l for l in e.get("links", []) if not l.lower().startswith("dispositioned by")]
        v.setdefault(SUPPORTS_KEY, {})[key] = {"verdict": "Reassess"}
    elif verdict == "Accept":
        if not sugg:
            raise ValueError("Accept needs the suggestion.")
        f = dict(sugg["fields"]); f.update({k: x for k, x in fields.items() if x is not None})
        if sugg["needsOwner"] and not str(f.get("owner", "")).strip():
            raise ValueError("Set the owner before accepting this one; the engine does not guess stakeholders.")
        iid = "i" + key[1:]
        cand = {"id": iid, "page": "Implied at baseline", "table": "", "kind": sugg["kind"], "title": f.get("title", ""), "ref": "",
                "source_status": sugg["status"], "owner": f.get("owner", ""), "approved-by": "", "moscow": f.get("moscow", ""), "phase": f.get("phase", ""),
                "implemented-by": f.get("implemented-by", ""), "vendor-ref": "", "raised-on": "", "consulted": f.get("consulted", ""),
                "rationale": f.get("rationale", "") if sugg["kind"] != "CR" else f.get("reason", ""), "impact": f.get("impact", ""), "description": "",
                "source": f.get("source", ""), "confidence": "", "inferred": False, "trigger": "", "mitigation": "", "likelihood": "", "risk-kind": "Risk" if sugg["kind"] == "RSK" else "",
                "options": "", "next action": f.get("next action", ""), "due": f.get("due", ""), "notes": f"Implied at baseline by {sugg['id']} under {sugg['rule']}",
                "links": [sugg["reverse"]] if sugg["reverse"] else [], "implied": True, "chosen-option": f.get("chosen-option", "")}
        imp = [c for c in v.get(IMPLIED_KEY, []) if c["id"] != iid] + [cand]
        v[IMPLIED_KEY] = imp
        v.setdefault(iid, {})["verdict"] = "Accept"
        trig = v.setdefault(sugg["id"], {})
        trig["links"] = list(dict.fromkeys(trig.get("links", []) + [sugg["link"] + iid]))
        v.setdefault(SUPPORTS_KEY, {})[key] = {"verdict": "Accept", "created": iid}
    else:
        raise ValueError("Unknown support verdict.")
    save_verdicts(bdir, v)
    return v
```

Modify `load_candidates` so its last line is `return cands + load_implied(bdir)`.

Modify `apply_verdict` to take `links=None` and, when given, set `e["links"] = list(links)`.

Modify `effective` to add `out["links"] = list(e.get("links", [])) + (list(c.get("links", [])) if c.get("implied") else [])` and `out["implied"] = bool(c.get("implied"))`. Note: an implied candidate's own links live on the candidate; a trigger's links live on its verdict.

In `assemble`, after computing `fields`, add `"links": list(dict.fromkeys(c.get("links") or []))` to the record dict, and use `raised-on` fallback to the trigger's: implied candidates have empty `raised-on`, so `fields["Raised on"] = c.get("raised-on") or today` already covers them.

In `freeze`, after the register-empty check and before `assemble`:

```python
    pending = [s for s in suggestions(cands, v)["suggestions"] if s["level"] == "fail"]
    if pending:
        raise ValueError(f"{len(pending)} missing support(s) still undecided on the Missing supports tab; accept or dismiss them before the freeze.")
```

In the id loop, also map candidate ids: after `r["id"] = nid`, add `idmap[r["cid"]] = nid` and for each `mc in r["merged_cids"]`: `idmap[mc] = nid`. Extend `remap` to also replace candidate ids: `re.sub(r"\b[ci][0-9a-f]{8,10}\b", lambda m: idmap.get(m.group(0), m.group(0)), LINK_RE.sub(...))`. In the write loop, start `links` from `[remap(l) for l in r.get("links", [])]` instead of `[]`, and drop any link whose target is still a candidate id (its target was not accepted). Also make `LINK_NOTE_WORDS` the dict used there.

In the `frozen.md` write, after the id map table, append:

```python
                + "\n\n## Implied at baseline\n\n| Item | Rule | Implied by |\n|---|---|---|\n"
                + "\n".join(f"| {r['id']} | {re.search(r'under (S\d+)', r['fields'].get('Notes', '') + ' ' + r['fields'].get('Source', '')).group(1) if re.search(r'under (S\d+)', r['fields'].get('Notes', '') + ' ' + r['fields'].get('Source', '')) else ''} | {remap(re.search(r'by (\S+) under', r['fields'].get('Notes', '')).group(1)) if re.search(r'by (\S+) under', r['fields'].get('Notes', '')) else ''} |" for r in out if r.get('implied'))
```

and mark records implied in `assemble` with `"implied": bool(c.get("implied"))`.

- [ ] **Step 4: Run tests**

Run: `make test`
Expected: all pass. Likely snags: `LINK_RE` groups (check its definition near the top of `baseline.py` before writing `source_links`; it captures prefix and number as groups 1 and 2), and the Options column in the test page being one cell with both options on one line. If `chosen_text` returns empty for the test page, split options on `(?=\d+\.\s)` in `option_lines` in `integrity.py`:

```python
def option_lines(item):
    txt = str(item.get("options", "") or "")
    parts = re.split(r"(?:\n|\s)(?=\d+[.)]\s)", txt)
    return [p.strip() for p in parts if p.strip()]
```

- [ ] **Step 5: Commit**

```bash
git add console/baseline.py console/integrity.py console/tests/test_baseline_supports.py
git commit -m "Baseline: candidates as items, missing supports as implied candidates, freeze guard and link remap"
```

---

### Task 6: Server endpoints

**Files:**
- Modify: `console/server.py` (`state()` at line 240, `do_GET` at 269, `do_POST` at 285, `transition` at 327, `baseline_state` at 399)

**Interfaces:**
- `/api/state` gains `integrity`: `I.check(items, phases, stakeholders, today)` with each suggestion whose key is in `<engagement>/supports-dismissed.json` removed and a `dismissed` count.
- `/api/baseline` gains `suggestions` (`B.suggestions(...)`).
- POST `/api/baseline/support` `{key, verdict, reason?, fields?}`: looks up the suggestion by key from `B.suggestions`, calls `B.support_verdict`.
- POST `/api/supports` `{id, to, fields, links}`: the suggestions the item would raise in state `to` with those fields merged; returns `{"suggestions": [...]}`.
- POST `/api/transition` accepts optional `supports: [{key, fields}]`. For each, a create block is written first (links: the reverse link plus any in the offer), then the transition block carries the trigger's link as `"<word> item <n>"`.
- POST `/api/support/accept` `{id, key, fields?, madeBy, evidence?}`: create block for the offer and an edit block on the trigger adding `"<word> item <n>"`.
- POST `/api/support/dismiss` `{id, key, reason, madeBy}`: writes to `supports-dismissed.json` `{key: {rule, id, reason, by, on}}`.

- [ ] **Step 1: Add the helpers and endpoints**

At the top: `import integrity as I` and `DISMISSED_PATH = os.path.join(ENG, "supports-dismissed.json")`.

Add after `state()`:

```python
def load_dismissed():
    return json.load(open(DISMISSED_PATH, encoding="utf-8")) if os.path.exists(DISMISSED_PATH) else {}


def integrity_of(items):
    eng = load_engagement()
    res = I.check(list(items.values()), phases=eng["phases"] or None, stakeholders=load_stakeholders() or None, today=today())
    gone = load_dismissed()
    res["suggestions"] = [s for s in res["suggestions"] if s["key"] not in gone]
    res["dismissed"] = len(gone)
    return res
```

In `state()`, compute `items` once and add `"integrity": integrity_of(items)` to the returned dict.

In `baseline_state()`, add `"suggestions": B.suggestions(cands, v)` to the present branch and `"suggestions": {"suggestions": [], "prompts": [], "failures": [], "warnings": [], "dismissed": 0}` to the absent one.

In `do_POST`, add routes:

```python
                if p == "/api/baseline/support":
                    sugg = next((s for s in B.suggestions(B.load_candidates(B_DIR), B.load_verdicts(B_DIR))["suggestions"] if s["key"] == req["key"]), None)
                    if req["verdict"] != "Dismiss" and not sugg:
                        raise ValueError("That suggestion is no longer current; reload.")
                    B.support_verdict(B_DIR, req["key"], req["verdict"], req.get("reason", ""), req.get("fields"), sugg)
                    return self.send_json({"ok": True})
                if p == "/api/supports":
                    return self.send_json(self.supports_preview(req))
                if p == "/api/support/accept":
                    return self.send_json(self.support_accept(req))
                if p == "/api/support/dismiss":
                    return self.send_json(self.support_dismiss(req))
```

Add methods:

```python
    def supports_preview(self, req):
        items = overlay(load_registers(), load_change_sets())
        it = items.get(req["id"])
        if not it:
            raise ValueError("No such item.")
        merged = dict(it); merged.update({field_key(k): v for k, v in req.get("fields", {}).items()})
        merged["links"] = it["links"] + req.get("links", [])
        merged["status"] = req.get("to") or it["status"]
        items[it["id"]] = merged
        res = integrity_of(items)
        return {"suggestions": [s for s in res["suggestions"] if s["id"] == it["id"]]}

    def write_offer(self, cs, req, sugg, overrides):
        """One create block for an offer. Returns its block number."""
        f = dict(sugg["fields"]); f.update({field_key(k): v for k, v in (overrides or {}).items() if v is not None})
        if sugg["needsOwner"] and not str(f.get("owner", "")).strip():
            raise ValueError("Set the owner before accepting this one; the engine does not guess stakeholders.")
        kind = sugg["kind"]
        fields = {"Title": f.get("title", ""), "Status": sugg["status"], "Raised on": today()}
        for k in M.SHORT[kind] + M.LONG[kind]:
            if f.get(k):
                fields[label_of(k)] = f[k]
        if kind == "RSK":
            fields["Kind"] = f.get("risk-kind", "Risk")
        links = [sugg["reverse"]] if sugg["reverse"] else []
        return append_block(cs, kind, "new", fields, links, self.evidence(req), f"{sugg['rule']}: implied by {sugg['id']}")

    def transition(self, req):
        items = overlay(load_registers(), load_change_sets())
        it = items.get(req["id"])
        if not it:
            raise ValueError("No such item.")
        kind, frm, to = it["kind"], it["status"], req["to"]
        if to not in M.TRANSITIONS.get(kind, {}).get(frm, []):
            raise ValueError(f"{frm} → {to} is not an allowed move for a {M.NAMES[kind]} (I20).")
        cs = current_change_set(req["madeBy"])
        support_links = []
        wanted = req.get("supports") or []
        if wanted:
            preview = {s["key"]: s for s in self.supports_preview({**req, "to": to})["suggestions"]}
            for w in wanted:
                s = preview.get(w["key"])
                if not s:
                    raise ValueError("A chosen support is no longer current; reload and try again.")
                n = self.write_offer(cs, req, s, w.get("fields"))
                support_links.append(f"{s['link']}item {n}")
        merged = dict(it); merged.update({field_key(k): v for k, v in req.get("fields", {}).items()})
        merged["links"] = it["links"] + req.get("links", []) + support_links
        missing = M.missing_for(kind, to, merged)
        if kind == "OI" and to == "Blocked" and not merged.get("next action", "").startswith("Blocked:"):
            missing.append('Next action starting "Blocked: "')
        if kind == "CR" and to == "Submitted" and merged.get("implemented-by") == "Vendor" and not merged.get("vendor-ref"):
            missing.append("Vendor ref")
        if missing:
            raise ValueError("Before " + to + " you need: " + "; ".join(missing))
        fields = {"Status": to}
        for k, v in req.get("fields", {}).items():
            fields[label_of(field_key(k))] = v
        if to in M.CLOSES[kind]:
            fields["Closed on"] = today()
        n = append_block(cs, kind, it["id"], fields, req.get("links", []) + support_links, self.evidence(req), req.get("gist", "") or f"{frm} to {to}", frm=frm, based_on=it.get("updated", ""))
        return {"ok": True, "changeSet": cs["id"], "item": n, "supports": len(support_links)}

    def support_accept(self, req):
        items = overlay(load_registers(), load_change_sets())
        it = items.get(req["id"])
        if not it:
            raise ValueError("No such item.")
        s = next((x for x in integrity_of(items)["suggestions"] if x["key"] == req["key"]), None)
        if not s:
            raise ValueError("That suggestion is no longer current; reload.")
        cs = current_change_set(req["madeBy"])
        n = self.write_offer(cs, req, s, req.get("fields"))
        m = append_block(cs, it["kind"], it["id"], {}, [f"{s['link']}item {n}"], self.evidence(req), f"{s['rule']}: linked to the implied {s['kind']}", frm=None, based_on=it.get("updated", ""))
        return {"ok": True, "changeSet": cs["id"], "item": n, "linkBlock": m}

    def support_dismiss(self, req):
        who = req.get("madeBy", "").strip()
        if not who:
            raise ValueError("Say who you are first (Made by).")
        reason = req.get("reason", "").strip()
        if not reason:
            raise ValueError("Give a reason; it is kept beside the register.")
        gone = load_dismissed()
        gone[req["key"]] = {"id": req["id"], "rule": req.get("rule", ""), "reason": reason, "by": who, "on": today()}
        json.dump(gone, open(DISMISSED_PATH, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        return {"ok": True}
```

Note the ordering inside `transition`: support create blocks are written before validation runs. If validation then fails, the create blocks stay in the change set. Avoid that: compute `missing` first with the supports' links as placeholders (`support_links` derived from the preview before writing), and only call `write_offer` after the `missing` check passes. Restructure so: preview, build `placeholder_links = [s["link"] + "item ?"]`, validate with those, then write offers, then replace placeholders with real numbers, then write the transition block.

- [ ] **Step 2: Reload and check the API**

Run: `make up` then wait two seconds, then:

```bash
curl -s localhost:8085/api/state | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d['integrity']['suggestions']), 'suggestions', len(d['integrity']['failures']), 'failures')"
curl -s localhost:8085/api/baseline | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['suggestions'].keys())"
```

Expected: counts print with no traceback in `make logs`. (`python3` here only parses JSON on the host, which the repository's rules allow for reading.)

- [ ] **Step 3: Commit**

```bash
git add console/server.py
git commit -m "Server: integrity in state, baseline suggestions, support verdicts, supports written with a transition"
```

---

### Task 7: Baseline UI: Missing supports tab

**Files:**
- Modify: `console/static/app.js` (`baselineView` at line 454, `wireBaseline` at 563, the `BF` state object near the top)
- Modify: `console/static/guide.html` (baseline step list)

**Interfaces:**
- Consumes: `S.baseline.suggestions` = `{suggestions, prompts, failures, warnings, dismissed}`; POST `/api/baseline/support`.
- `BF` gains `sedit` (key of the suggestion being edited) and `sfields` (edits).

- [ ] **Step 1: Add the tab button and the count**

In `baselineView`, in the `tabs` div, add after the duplicates button:

```js
<button data-bltab="supports" class="${BF.tab === "supports" ? "on" : ""}">Missing supports <span class="n">${B.suggestions.suggestions.filter(s => s.level === "fail").length}</span></button>
```

and reorder so the buttons read Candidates, Suggested duplicates, Row by row, Missing supports.

Change the how-to list: step 3 stays Row by row; insert a new step 4 before "Fix fields in bulk":

```html
<li><b>Fill the missing supports.</b> Every accepted row whose state implies another record, a decision behind an accepted limitation, a change request behind one marked Change requested, the open item that carries a draft, is offered here prefilled. Accept, edit then accept, or dismiss with a reason. A limitation the source calls Accepted with nothing behind it can instead be sent back to Under assessment. The freeze waits until this list is empty of failures.</li>
```

- [ ] **Step 2: Render the tab**

Add to `baselineView` after the duplicates block:

```js
    ${BF.tab === "supports" && !B.frozen ? blSupports() : ""}
```

and add the function after `blPass`:

```js
/* Missing supports: what the accepted rows' states imply and the set does not yet hold. Each offer is
   prefilled from its trigger; accepting adds an implied candidate, linked both ways, already accepted. */
function blSupports() {
  const B = S.baseline, R = B.suggestions, byId = Object.fromEntries(B.candidates.map(c => [c.id, c]));
  const fails = R.suggestions.filter(s => s.level === "fail"), warnsS = R.suggestions.filter(s => s.level === "warn");
  const one = s => {
    const editing = BF.sedit === s.key, f = editing ? {...s.fields, ...BF.sfields} : s.fields;
    const fld = (k, v) => `<div class="field"><label>${esc(S.model.labels[k] || k)}</label>${editing ? (["rationale", "reason", "impact", "next action", "source"].includes(k) ? `<textarea data-sf="${k}">${esc(v)}</textarea>` : k === "owner" ? `<input data-sf="owner" list="stk" value="${esc(v)}">` : `<input data-sf="${k}" value="${esc(v)}">`) : `<div class="v">${esc(v) || '<span class="muted">—</span>'}</div>`}</div>`;
    const keys = Object.keys(f); if (s.needsOwner && !keys.includes("owner")) keys.splice(1, 0, "owner");
    return `<div class="cs blk-support"><div class="small muted"><b>${esc(s.rule)}</b> (${esc(s.check)}) · ${esc(S.model.names[byId[s.id]?.kind] || "")} <i>${esc(s.triggerTitle)}</i> on ${esc(s.triggerPage)} is ${esc(byId[s.id] ? (byId[s.id].status || byId[s.id].source_status || S.model.first[byId[s.id].kind]) : "")} and needs a <span class="id" style="${COLOR(s.kind)}">${s.kind}</span>${s.needsOwner ? ' <span class="tag">owner needed</span>' : ""}</div>
      ${keys.map(k => fld(k, f[k] ?? "")).join("")}
      <div class="small muted">Links: trigger gets <code>${esc(s.link)}&lt;new id&gt;</code>${s.reverse ? `; new item gets <code>${esc(s.reverse)}</code>` : ""}</div>
      <div class="moves" style="--c:var(--cs)">
        ${s.recommend === "Reassess" ? `<button class="primary" data-sv="Reassess" data-key="${s.key}" title="Send the limitation back to Under assessment; its open item is offered next">Reassess (recommended)</button> <button data-sv="Accept" data-key="${s.key}">Reconstruct</button>` : `<button class="primary" data-sv="Accept" data-key="${s.key}">${s.recommend === "Reconstruct" ? "Reconstruct (recommended)" : "Accept"}</button>${s.recommend ? ` <button data-sv="Reassess" data-key="${s.key}">Reassess</button>` : ""}`}
        <button data-sv="edit" data-key="${s.key}">${editing ? "Stop editing" : "Edit"}</button>
        <input data-sreason="${s.key}" placeholder="reason to dismiss" style="width:220px"><button class="ghost" data-sv="Dismiss" data-key="${s.key}">Dismiss</button>
      </div></div>`;
  };
  const prompts = R.prompts.filter(p => byId[p.id]);
  return `<div class="section"><p class="small muted">${fails.length} needed before the freeze · ${warnsS.length} suggested · ${prompts.length} field prompt(s) · ${R.dismissed} dismissed. Offers are drafted in their first state; nothing here fills Approved by.</p>
    ${fails.map(one).join("") || '<p class="muted">Nothing missing among the accepted rows.</p>'}
    ${warnsS.length ? `<h3>Suggested, not required</h3>${warnsS.map(one).join("")}` : ""}
    ${prompts.length ? `<h3>Fix by hand in the editor</h3>${prompts.map(p => `<div class="blk"><span class="id" style="${COLOR(byId[p.id].kind)}">${byId[p.id].kind}</span> <a href="#" data-edit="${p.id}">${esc(byId[p.id].title)}</a> <span class="small muted">${esc(p.rule)}: ${esc(p.text)}</span></div>`).join("")}` : ""}</div>`;
}
```

- [ ] **Step 3: Wire it**

In `wireBaseline`, add:

```js
  m.querySelectorAll("[data-sf]").forEach(el => el.oninput = () => { BF.sfields[el.dataset.sf] = el.value; });
  m.querySelectorAll("[data-sv]").forEach(el => el.onclick = async () => {
    const key = el.dataset.key, what = el.dataset.sv;
    if (what === "edit") { if (BF.sedit === key) { BF.sedit = null; BF.sfields = {}; } else { BF.sedit = key; BF.sfields = {}; } render(); return; }
    const body = {key, verdict: what};
    if (what === "Dismiss") { body.reason = m.querySelector(`[data-sreason="${key}"]`)?.value.trim() || ""; if (!body.reason) return toast("Give a reason to dismiss"); }
    if (what === "Accept" && BF.sedit === key) body.fields = BF.sfields;
    try { const y = window.scrollY; await post("/api/baseline/support", body); BF.sedit = null; BF.sfields = {}; await load(); window.scrollTo(0, y); toast(what === "Accept" ? "Added as an accepted candidate" : what === "Reassess" ? "Sent back to Under assessment" : "Dismissed"); } catch (e) { toast(e.message); }
  });
```

Initialise `BF.sedit = null; BF.sfields = {};` where `BF` is declared. Add `.blk-support .field{margin:4px 0}` to the stylesheet if fields render cramped.

The freeze error from the server already names the tab, so no client guard is needed beyond showing the toast.

- [ ] **Step 4: Check in Chrome**

`make up ENG=test-data/puppy-gloves` (after Task 10 gives the sample rows; before that, use `engagements/test` if present). Wait two seconds. Open `http://localtest.me:8085/`, accept a few rows on Row by row, open Missing supports, accept one, confirm the Candidates tab shows the implied row with page "Implied at baseline" and verdict Accept, and the trigger's editor shows nothing broken. Try Freeze with a failure left: expect the toast naming the tab.

- [ ] **Step 5: Commit**

```bash
git add console/static/app.js console/static/guide.html
git commit -m "Baseline: Missing supports tab with accept, edit, reassess and dismiss"
```

---

### Task 8: Live UI: Supports panel, move dialog, Outstanding counts, SLT line

**Files:**
- Modify: `console/static/app.js` (`itemPanel` line 155, `wire` 174, `moveForm` 202, `submit` 225, `outstanding` 105, `sltData` 375, `slt` 404, `sltMarkdown` 430)

**Interfaces:**
- Consumes: `S.integrity` from `/api/state`; POST `/api/supports`, `/api/support/accept`, `/api/support/dismiss`; `supports` on `/api/transition`.
- `form` gains `supports` (array of `{key, fields, on}`) in move mode.

- [ ] **Step 1: Supports panel on the item**

In `itemPanel`, after the pending list and before the "Move to" heading:

```js
    ${supportsPanel(i)}
```

Add:

```js
function supportsPanel(i) {
  const R = S.integrity || {suggestions: [], prompts: [], failures: []};
  const mine = R.suggestions.filter(s => s.id === i.id), prompts = R.prompts.filter(p => p.id === i.id);
  if (!mine.length && !prompts.length) return "";
  return `<div class="supports"><h3>Supports needed</h3>
    ${mine.map(s => `<div class="blk"><span class="id" style="${COLOR(s.kind)}">${s.kind}</span> ${esc(s.fields.title || "")} <span class="small muted">${esc(s.rule)} · ${s.level === "fail" ? "needed" : "suggested"}${s.needsOwner ? " · owner needed" : ""}</span>
      <div class="moves"><button data-sacc="${s.key}">Accept</button> <button class="ghost" data-sdis="${s.key}" data-rule="${s.rule}">Dismiss</button></div>
      ${form?.mode === "support" && form.key === s.key ? supportForm(s) : ""}</div>`).join("")}
    ${prompts.map(p => `<div class="blk small muted">${esc(p.rule)}: ${esc(p.text)}</div>`).join("")}</div>`;
}
function supportForm(s) {
  const keys = Object.keys(s.fields); if (s.needsOwner && !keys.includes("owner")) keys.splice(1, 0, "owner");
  return `<div class="form">${keys.map(k => input(k, form.fields[k] ?? s.fields[k] ?? "", k === "owner" && s.needsOwner, s.kind)).join("")}
    ${form.dismiss ? `<div class="field"><label>Reason to dismiss</label><input data-f="__reason" value="${esc(form.fields.__reason || "")}"></div>` : ""}${tail()}</div>`;
}
```

In `wire`:

```js
  d.querySelectorAll("[data-sacc]").forEach(el => el.onclick = () => { form = {mode: "support", key: el.dataset.sacc, fields: {}, links: []}; renderDetail(); });
  d.querySelectorAll("[data-sdis]").forEach(el => el.onclick = () => { form = {mode: "support", key: el.dataset.sdis, rule: el.dataset.rule, dismiss: true, fields: {}, links: []}; renderDetail(); });
```

In `submit`, before the `else` chain:

```js
    if (form.mode === "support") {
      if (form.dismiss) { if (!form.fields.__reason) throw new Error("Give a reason to dismiss."); r = await post("/api/support/dismiss", {id: open, key: form.key, rule: form.rule, reason: form.fields.__reason}); toast("Dismissed; kept in supports-dismissed.json"); }
      else { r = await post("/api/support/accept", {id: open, key: form.key, fields: form.fields, evidence: form.evidence || ""}); toast(`${r.changeSet} item ${r.item} appended and linked`); }
      form = null; await load(); return;
    }
```

Note `submit` reads `form.fields` for `__reason`; the `input` helper's `data-f` handler writes there. Change the button label in `tail()` when `form.mode === "support" && form.dismiss` to "Dismiss".

- [ ] **Step 2: Supports in the move dialog**

`moveForm` becomes async-aware: when the user picks a move, fetch the preview. In `wire`'s `[data-move]` handler:

```js
  d.querySelectorAll("[data-move]").forEach(el => el.onclick = async () => {
    form = {mode: "move", to: el.dataset.move, fields: {}, links: [], supports: null};
    renderDetail();
    try { const r = await post("/api/supports", {id: open, to: form.to, fields: {}, links: []}); if (form?.mode === "move") { form.supports = r.suggestions.map(s => ({...s, on: s.level === "fail" && !s.needsOwner, edits: {}})); renderDetail(); } } catch (e) { toast(e.message); }
  });
```

In `moveForm`, before `${linkAdder(k)}`:

```js
    ${form.supports === null ? '<p class="small muted">Checking what this move implies…</p>' : form.supports.length ? `<div class="supports"><h3>This move implies</h3>${form.supports.map((s, n) => `<label class="dup"><input type="checkbox" data-son="${n}" ${s.on ? "checked" : ""}> <span class="id" style="${COLOR(s.kind)}">${s.kind}</span> ${esc(s.fields.title || "")} <span class="small muted">${esc(s.rule)}${s.needsOwner ? " · set an owner to include" : ""}</span></label>${s.needsOwner ? `<input data-sowner="${n}" list="stk" placeholder="owner" value="${esc(s.edits.owner || "")}">` : ""}`).join("")}<p class="small muted">Ticked items are written to the change set before the move and linked to it.</p></div>` : ""}
```

Wire: `d.querySelectorAll("[data-son]").forEach(el => el.onchange = () => form.supports[+el.dataset.son].on = el.checked);` and `d.querySelectorAll("[data-sowner]").forEach(el => el.oninput = () => { const s = form.supports[+el.dataset.sowner]; s.edits.owner = el.value; s.on = !!el.value.trim(); });`.

In `submit`, the move branch sends `supports: (form.supports || []).filter(s => s.on).map(s => ({key: s.key, fields: s.edits}))`.

Because a support's link satisfies `link:` requirements, the "This move needs a link" note in `moveForm` should read "Already present, or provided by a ticked support below, or add another." when any support is on.

- [ ] **Step 3: Counts on Outstanding and the SLT line**

In `outstanding()`, at the top of the returned HTML:

```js
    ${(S.integrity?.suggestions.filter(s => s.level === "fail").length || S.integrity?.failures.length) ? `<div class="note">Register gaps: ${S.integrity.suggestions.filter(s => s.level === "fail").length} missing support(s), ${S.integrity.failures.length} integrity failure(s). ${[...new Set(S.integrity.suggestions.filter(s => s.level === "fail").map(s => s.id))].slice(0, 12).map(id => `<a href="#" data-open="${id}">${id}</a>`).join(" ")}</div>` : ""}
```

In `sltData`, add `gaps: (() => { const o = {}; (S.integrity?.suggestions || []).filter(s => s.level === "fail").forEach(s => o[s.rule] = (o[s.rule] || 0) + 1); (S.integrity?.failures || []).forEach(f => o[f.rule] = (o[f.rule] || 0) + 1); return o; })()`.

In `slt()` and `sltMarkdown()`, after the last section, add "Register gaps" with one line per rule with a non-zero count: `${Object.entries(r.gaps).map(([k, n]) => `${k}: ${n}`).join(" · ")}`, omitted when empty.

- [ ] **Step 4: Check in Chrome**

`make reload`, wait two seconds, load `http://localtest.me:8085/`. Open a LIM in Under assessment from the sample, choose Change requested, confirm the dialog lists a CR offer ticked, submit, then open the change set view and confirm the CR block precedes the transition block and the transition's links include `dispositioned by item n`. Open the new provisional CR from the register and confirm its Supports panel offers the S7 open item.

- [ ] **Step 5: Commit**

```bash
git add console/static/app.js
git commit -m "Live: supports panel on items, implied items written with a move, gaps on Outstanding and the SLT report"
```

---

### Task 9: Sample data that trips the rules

**Files:**
- Modify: `console/sample-baseline/Risks and Limitations.md`, `console/sample-baseline/Decisions and Actions.md`, `console/make-sample.py`

- [ ] **Step 1: Baseline pages**

In `Risks and Limitations.md`, add a Limitations table (or extend the existing one) with these rows, using the columns `Ref | Limitation | Status | Impact | Options | Chosen option | Owner | Rationale | Links`:

```
| LM-1 | One notification channel per customer | Accepted | Email only on day one | 1. Live with it; impact: none; phase: Day one 2. Ask the vendor for SMS; impact: $40k; phase: Later | 1 | Priya Nair | Volume is low and SMS is rarely used | constrains RQ-3 |
| LM-2 | No bulk port assignment | Change requested | Operations cannot port in bulk | 1. Vendor adds bulk port; impact: $20k, 3 weeks; phase: Day one 2. Manual with a report; impact: 2 FTE; phase: Day one | 1 | Tom Okafor | | |
| LM-3 | Invoice shows two lines per bundle | Accepted | Customers see two lines | 1. Build a report to find affected customers and warn them; impact: 2 days; phase: Day one 2. Accept; impact: complaints; phase: Day one | 1 | Priya Nair | | constrains RQ-4 |
```

Set the Risks table's RK-3 row to status Mitigating (add a Status column if the table lacks one) so S17 fires.

In `Decisions and Actions.md`, add a Change requests table with columns `Ref | Change request | Status | Reason | Vendor ref | Owner`:

```
| CR-1 | Vendor to add bulk port assignment | Submitted | Operations need bulk port on day one | NK-CR-118 | Tom Okafor |
```

Make sure a Requirements row `RQ-3` and `RQ-4` exist in `Requirements.md` (add `RQ-4 | Bundle shown as one invoice line | Should | Priya Nair | Agreed` if not).

- [ ] **Step 2: Live sample items**

In `make-sample.py`, add two items so Live has gaps: a LIM in Accepted with `constrains REQ-0002` and no DEC (Impact, two Options, Chosen option 1), and a RSK in Mitigating with Mitigation text and no `mitigated by` link. Use the existing `item()` helper. Keep ids after the last used in each register.

- [ ] **Step 3: Regenerate and look**

Run: `make sample && make up`, wait two seconds, then `curl -s localhost:8085/api/state | python3 -c "import json,sys; d=json.load(sys.stdin); print([ (s['rule'], s['id']) for s in d['integrity']['suggestions']])"`.
Expected: at least S5 and S17 listed. Switch the console to the sample's baseline folder (`make up ENG=test-data/puppy-gloves` already serves it; the baseline tab shows the pages) and confirm S5, S6, S8, S17 and S18 appear once the rows are accepted.

- [ ] **Step 4: Commit**

```bash
git add console/sample-baseline console/make-sample.py
git commit -m "Sample data: rows that need supports, in the baseline pages and the live registers"
```

---

### Task 10: Model 2.25 and documentation

**Files:**
- Modify: `solution-register-model.md` (header lines 1 to 5, section 5 table, section 9 table, section 10)
- Modify: `console/README.md`, `console/confluence-runbook.md`, `CLAUDE.md`, `docs/superpowers/specs/2026-09-13-supports-engine-design.md`

- [ ] **Step 1: Model document**

Change line 3 to `Version 2.25, 13 September 2026. Owner: Adam Moyes.` and insert after it:

```
Version 2.25 adds the supports rules. Sections 4.4 and 5 already say what must exist beside an item in a given state; a tool may read them as implications and offer the missing record prefilled, in its first state, with Approved by empty. Two link words are added for cases the sections implied without naming: a risk's mitigation actions are open items linked "mitigated by", and an accepted workaround that needs something built raises a requirement linked "needs". Rules I21 to I23 check them. Nothing changes for an item that already meets 4.4.
```

Section 5 table: add rows `| RSK | mitigated by | OI (one per mitigation action) |` and `| LIM | needs | REQ with Implemented by Internal (the tooling an accepted workaround requires) |`.

Section 9 table: add

```
| I21 Mitigation actions | Every RSK in Mitigating whose Mitigation names an action has a "mitigated by OI-nnnn" link to an open item not Closed. |
| I22 Workaround tooling | A LIM in Accepted whose chosen option needs something built has a "needs REQ-nnnn" link to a requirement with Implemented by Internal. Warning. |
| I23 Delivered change | Every CR in Delivered has a "delivers REQ-nnnn" link. |
```

and change the closing sentence to `I1 to I14, I17 to I21 and I23 are failures. I15, I16 and I22 are warnings.`

Section 10: add one sentence: `A tool that runs these rules should offer the missing record for each failing item, prefilled from the item that implies it, and leave approval to a person.`

- [ ] **Step 2: Console docs**

`console/README.md`: under Baseline mode add the Missing supports tab and the order Duplicates, Row by row, Missing supports, Freeze; under Live add the Supports panel, the move dialog's implied items, and `supports-dismissed.json`. `console/confluence-runbook.md`: in the baseline step, add "work Missing supports to zero failures before the freeze". `CLAUDE.md`: add a row to the layout table: `| console/integrity.py | Section 9 and the SUPPORTS table over item dicts. Pure; used by baseline and live. Rules read from model.py only. |` and mention `make test`. Update the spec's Live dismissals paragraph, baseline order and S20 to match what was built.

- [ ] **Step 3: Commit**

```bash
git add solution-register-model.md console/README.md console/confluence-runbook.md CLAUDE.md docs/superpowers/specs/2026-09-13-supports-engine-design.md
git commit -m "Model 2.25: supports rules I21 to I23, mitigated by and needs; console and runbook docs"
```

---

### Task 11: End-to-end check on the sample

**Files:** none changed unless a defect is found.

- [ ] **Step 1: Full test run**

Run: `make test`
Expected: all tests pass.

- [ ] **Step 2: Baseline to freeze in Chrome**

`make sample && make up`, wait two seconds, open `http://localtest.me:8085/`. Because the sample also writes live items, the console opens Live; to test the baseline, run `make up ENG=engagements/test` if that folder exists, otherwise temporarily move `test-data/puppy-gloves`'s register folders aside (`mv` them under the scratchpad) so `stage()` returns baseline. Then: work Duplicates, accept everything on Row by row, open Missing supports, Reconstruct the S5 offer, Accept the S6 offer, set an owner on the S4 offer and accept, dismiss S8 with a reason, accept S17. Freeze. Confirm `baseline/frozen.md` has the Implied at baseline table and that `curl localhost:8085/api/state` shows no I7 failure for the accepted limitation once the DEC is moved to Accepted in the editor before freezing (or shows the S12 prompt if left Proposed).

- [ ] **Step 3: Live move in Chrome**

Restore the register folders, `make up`. Move the sample's LIM in Under assessment to Change requested with the CR ticked. Open the change set view and confirm the block order. Confirm the Outstanding view shows the Register gaps note and the SLT report has the gaps line.

- [ ] **Step 4: Commit any fixes and record**

If defects were fixed, commit them with a message naming the defect. Then write the handoff refresh: run `/handoff` so `handoffs/baseline-abb-nokia.md` gains the new step "work Missing supports before the freeze" and notes model 2.25.

---

## Self-review

**Spec coverage.** Table rows S1 to S19 and S21: Task 2. S20: folded into S8, spec updated in Task 10. Baseline tab, verdicts, reconstruction default, freeze guard, frozen.md list: Tasks 5 and 7. Live panel, Outstanding count, move dialog, dismissals, SLT line: Tasks 6 and 8. "Never does" list: `write_offer` and `support_verdict` refuse a missing owner; no row offers past the first state (asserted in `test_supports_rows_are_well_formed`); no row's fields include `approved-by` (asserted). Model bump and docs: Task 10. Sample rows: Task 9. Tests per row: Task 3 covers S1, S4, S5, S6, S8, S12, S13, S17, S18, S21 directly and the table test covers the shape of the rest; add a one-line test per remaining row (S2, S3, S7, S9, S10, S11, S14, S15, S16, S19) in Task 3 following the S1 pattern if time allows, each asserting the rule fires for a minimal item and is silent when the `unless` holds.

**Placeholders.** None. Every code step carries the code.

**Type consistency.** `suggestion` dict keys (`key, rule, check, level, id, kind, status, fields, link, reverse, needsOwner`) are the same in `integrity.py`, `baseline.support_verdict`, `server.write_offer` and `app.js`. `B.suggestions` returns the `check` dict plus `dismissed`, and annotates `recommend`, `triggerTitle`, `triggerPage`. `/api/transition`'s `supports` entries are `{key, fields}`.
