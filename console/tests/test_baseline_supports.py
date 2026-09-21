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
        self.assertEqual(imp["id"], "i" + x["key"][1:]); self.assertEqual(imp["kind"], "CP")
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

    def accept_every_support(self):
        while True:
            left = [x for x in B.suggestions(B.load_candidates(self.b), B.load_verdicts(self.b))["suggestions"] if x["level"] == "fail"]
            if not left:
                return
            for x in left:
                B.support_verdict(self.b, x["key"], "Accept", sugg=x, fields={"owner": "Tom Okafor"})

    def test_freeze_leaves_no_candidate_id_in_any_item_file(self):
        eng = os.path.join(self.d, "eng"); os.makedirs(eng)
        self.accept_every_support()
        B.freeze(eng, self.b, B.load_candidates(self.b), B.load_verdicts(self.b), "13 September 2026", "Adam")
        seen = 0
        for root, _, names in os.walk(eng):
            for name in names:
                seen += 1
                text = open(os.path.join(root, name), encoding="utf-8").read()
                self.assertIsNone(B.CAND_RE.search(text), name + " carries a candidate id")
        self.assertGreater(seen, 5)
        # the ids are there, remapped, rather than simply absent
        self.assertIn("Accepts LIM-0001", open(os.path.join(eng, "decisions", "DEC-0001.md"), encoding="utf-8").read())
        ois = [open(os.path.join(eng, "open-items", n), encoding="utf-8").read() for n in os.listdir(os.path.join(eng, "open-items"))]
        self.assertTrue(any("Take DEC-0001 to the approver" in t for t in ois))

    def test_frozen_files_parse_back_with_no_history(self):
        import items as IT
        eng = os.path.join(self.d, "eng"); os.makedirs(eng)
        self.accept_every_support()
        B.freeze(eng, self.b, B.load_candidates(self.b), B.load_verdicts(self.b), "13 September 2026", "Adam")
        lim = IT.parse_item(IT.item_path(eng, "LIM-0001"))
        self.assertEqual(lim["history"], []); self.assertEqual(lim["updated"], lim["raised-on"])
        self.assertEqual(lim["title"], "One channel per customer"); self.assertEqual(lim["owner"], "Priya Nair")
        self.assertEqual(lim["impact"], "Email only on day one"); self.assertIn("constrains REQ-0001", lim["links"])
        self.assertEqual(lim["chosen-option"], "1")
        rsk_dir = os.path.join(eng, "risks")
        for name in (os.listdir(rsk_dir) if os.path.isdir(rsk_dir) else []):
            self.assertIn("risk-kind", IT.parse_item(os.path.join(rsk_dir, name)))

    def test_frozen_counts_every_item_written_including_implied(self):
        eng = os.path.join(self.d, "eng"); os.makedirs(eng)
        self.accept_every_support()
        r = B.freeze(eng, self.b, B.load_candidates(self.b), B.load_verdicts(self.b), "13 September 2026", "Adam")
        self.assertEqual(B.frozen(self.b)["counts"], r["counts"])
        self.assertEqual(sum(r["counts"].values()), r["written"])

    def test_source_links_reads_a_disposition_record_column(self):
        dec = {"id": "cdeadbeef", "page": "Limitations", "ref": "DEC-001"}
        lim = {"page": "Limitations", "notes": "Baseline import from Limitations\nDisposition record: DEC-001"}
        self.assertEqual(B.source_links(lim, B.refmap_of([dec])), ["dispositioned by cdeadbeef"])


DECS = """---
page-id: 3
page-title: Decisions
---

# Decisions

| Ref | Decision | Status | Owner | Rationale |
|---|---|---|---|---|
| DEC-001 | Accept one channel per customer | Accepted | Priya Nair | Volume is low |
| DEC-002 | Retire the legacy portal | Proposed | Tom Okafor | Old |
"""


class LinkExisting(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); self.b = os.path.join(self.d, "baseline"); os.makedirs(self.b)
        open(os.path.join(self.b, "Limitations.md"), "w").write(PAGE)
        open(os.path.join(self.b, "Requirements.md"), "w").write(REQS)
        open(os.path.join(self.b, "Decisions.md"), "w").write(DECS)
        self.cands = B.load_candidates(self.b)
        B.apply_verdict(self.b, [c["id"] for c in self.cands], "Accept")

    def tearDown(self):
        shutil.rmtree(self.d)

    def cid(self, ref):
        return next(c["id"] for c in B.load_candidates(self.b) if c["ref"] == ref)

    def sugg(self, rule):
        s = B.suggestions(B.load_candidates(self.b), B.load_verdicts(self.b))["suggestions"]
        return next(x for x in s if x["rule"] == rule)

    def test_offer_lists_accepted_candidates_of_its_kind(self):
        x = self.sugg("S5")
        self.assertEqual([m["id"] for m in x["matches"]], [self.cid("DEC-001")])
        self.assertEqual(x["matches"][0]["page"], "Decisions")

    def test_offer_omits_candidates_not_accepted(self):
        B.apply_verdict(self.b, [self.cid("DEC-001")], "Reject", reason="other")
        self.assertEqual(self.sugg("S5")["matches"], [])

    def test_link_writes_the_link_and_the_offer_goes(self):
        x = self.sugg("S5"); dec = self.cid("DEC-001")
        B.support_verdict(self.b, x["key"], "Link", sugg=x, target=dec)
        v = B.load_verdicts(self.b)
        self.assertIn("dispositioned by " + dec, v[x["id"]]["links"])
        self.assertNotIn("links", v.get(dec, {}))
        self.assertEqual(v[B.SUPPORTS_KEY][x["key"]], {"verdict": "Link", "target": dec})
        again = B.suggestions(B.load_candidates(self.b), v)["suggestions"]
        self.assertFalse(any(y["rule"] == "S5" for y in again))
        self.assertFalse(v.get(B.IMPLIED_KEY))

    def test_link_writes_the_reverse_where_the_model_names_one(self):
        # S6 offers a CP with the reverse word triggered by; make an accepted CP candidate to link
        open(os.path.join(self.b, "Changes.md"), "w").write("---\npage-id: 4\npage-title: Change requests\n---\n\n# Change requests\n\n| Ref | Change request | Status | Owner | Reason |\n|---|---|---|---|---|\n| CP-001 | Vendor adds bulk port | Proposed | Tom Okafor | Ops |\n")
        B.apply_verdict(self.b, [self.cid("CP-001")], "Accept")
        x = self.sugg("S6"); cr = self.cid("CP-001")
        self.assertIn(cr, [m["id"] for m in x["matches"]])
        B.support_verdict(self.b, x["key"], "Link", sugg=x, target=cr)
        v = B.load_verdicts(self.b)
        self.assertIn("dispositioned by " + cr, v[x["id"]]["links"])
        self.assertIn("triggered by " + x["id"], v[cr]["links"])

    def test_link_refuses_wrong_kind_unaccepted_and_self(self):
        x = self.sugg("S5")
        with self.assertRaises(ValueError): B.support_verdict(self.b, x["key"], "Link", sugg=x, target=self.cid("REQ-001"))
        with self.assertRaises(ValueError): B.support_verdict(self.b, x["key"], "Link", sugg=x, target=x["id"])
        B.apply_verdict(self.b, [self.cid("DEC-002")], "Discard")
        with self.assertRaises(ValueError): B.support_verdict(self.b, x["key"], "Link", sugg=x, target=self.cid("DEC-002"))
        with self.assertRaises(ValueError): B.support_verdict(self.b, x["key"], "Link", sugg=x, target="")

    def test_freeze_carries_the_link_through_the_id_map(self):
        x = self.sugg("S5"); B.support_verdict(self.b, x["key"], "Link", sugg=x, target=self.cid("DEC-001"))
        for y in B.suggestions(B.load_candidates(self.b), B.load_verdicts(self.b))["suggestions"]:
            if y["level"] == "fail": B.support_verdict(self.b, y["key"], "Dismiss", reason="test")
        eng = os.path.join(self.d, "eng"); os.makedirs(eng)
        B.freeze(eng, self.b, B.load_candidates(self.b), B.load_verdicts(self.b), "14 September 2026", "Adam")
        lim = open(os.path.join(eng, "limitations", "LIM-0001.md"), encoding="utf-8").read()
        self.assertIn("dispositioned by DEC-0001", lim)
        self.assertNotIn("Implied at baseline", open(os.path.join(self.b, "frozen.md"), encoding="utf-8").read())


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

    def test_freeze_reports_a_blank_scope_when_scopes_declared(self):
        r = self.run_freeze("", ["Access"])
        self.assertTrue(r["ok"]); self.assertEqual(r["offScope"], 3)

    def test_freeze_reports_an_off_list_scope(self):
        r = self.run_freeze("Nonsense", ["Access"])
        self.assertTrue(r["ok"]); self.assertEqual(r["offScope"], 3)

    def test_freeze_accepts_a_listed_scope(self):
        r = self.run_freeze("Access", ["Access"])
        self.assertTrue(r["ok"])
        self.assertEqual(r["offScope"], 0)

    def test_freeze_ignores_scope_when_none_declared(self):
        self.assertTrue(self.run_freeze("", [])["ok"])


class ScopeInCandidates(unittest.TestCase):
    """A source Scope or Domain column must reach the candidate's own scope field, not just Notes."""
    def setUp(self):
        self.d = tempfile.mkdtemp(); self.b = os.path.join(self.d, "baseline"); os.makedirs(self.b)

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_scope_column_reaches_the_candidate(self):
        open(os.path.join(self.b, "Limitations.md"), "w").write("""---
page-id: 1
page-title: Limitations
---

# Limitations

| Ref | Limitation | Status | Owner | Scope |
|---|---|---|---|---|
| LIM-001 | One channel per customer | Accepted | Priya Nair | CarrierEthernet |
""")
        c = B.load_candidates(self.b)[0]
        self.assertEqual(c["scope"], "CarrierEthernet")

    def test_domain_column_reaches_the_candidate(self):
        open(os.path.join(self.b, "Changes.md"), "w").write("""---
page-id: 2
page-title: Change requests
---

# Change requests

| Ref | Change request | Status | Owner | Domain |
|---|---|---|---|---|
| CP-001 | Vendor adds bulk port | Proposed | Tom Okafor | CarrierEthernet |
""")
        c = B.load_candidates(self.b)[0]
        self.assertEqual(c["scope"], "CarrierEthernet")

    def test_no_scope_column_leaves_scope_blank_and_notes_unaffected(self):
        open(os.path.join(self.b, "Requirements.md"), "w").write(REQS)
        c = B.load_candidates(self.b)[0]
        self.assertEqual(c["scope"], "")
        self.assertNotIn("Scope", c["notes"])
        self.assertNotIn("Domain", c["notes"])


class AssembleCarriesScope(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); self.b = os.path.join(self.d, "baseline"); os.makedirs(self.b)
        open(os.path.join(self.b, "Limitations.md"), "w").write("""---
page-id: 1
page-title: Limitations
---

# Limitations

| Ref | Limitation | Status | Owner | Scope |
|---|---|---|---|---|
| LIM-001 | One channel per customer | Accepted | Priya Nair | CarrierEthernet |
""")

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_assemble_record_scope_matches_the_candidate(self):
        cands = B.load_candidates(self.b)
        B.apply_verdict(self.b, [c["id"] for c in cands], "Accept")
        records, _ = B.assemble(B.load_candidates(self.b), B.load_verdicts(self.b), "13 September 2026")
        self.assertEqual(records[0]["scope"], "CarrierEthernet")
