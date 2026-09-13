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
