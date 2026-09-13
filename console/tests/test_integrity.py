import unittest
import integrity as I


def item(id, status, **f):
    kind = id.split("-")[0]
    base = {"id": id, "kind": kind, "status": status, "title": f.pop("title", id + " title"), "links": f.pop("links", []),
            "owner": f.pop("owner", "Priya Nair"), "implemented-by": f.pop("implemented-by", "Vendor"), "source": f.pop("source", "workshop"),
            "raised-on": f.pop("raised-on", "1 September 2026")}
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


def fails(res, rule):
    return sorted(set(f["id"] for f in res["failures"] if f["rule"] == rule))


def warns(res, rule):
    return sorted(set(f["id"] for f in res["warnings"] if f["rule"] == rule))


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

    def test_i19_consulted(self):
        r = I.check([item("DEC-0001", "Proposed", rationale="x", consulted="Nobody Known")], stakeholders=[{"name": "Priya Nair", "role": "Owner"}])
        self.assertEqual(fails(r, "I19"), ["DEC-0001"])
        r = I.check([item("DEC-0001", "Proposed", rationale="x", consulted="Vendor: Nokia; Priya Nair")], stakeholders=[{"name": "Priya Nair", "role": "Owner"}])
        self.assertEqual(fails(r, "I19"), [])

    def test_i4_due_warning_open_item(self):
        r = I.check([item("OI-0001", "Open", **{"next action": "x", "due": ""})])
        self.assertEqual(warns(r, "I4"), ["OI-0001"])
        r = I.check([item("OI-0001", "Open", **{"next action": "x", "due": "1 October 2026"})])
        self.assertEqual(warns(r, "I4"), [])

    def test_i4_due_warning_risk(self):
        r = I.check([item("RSK-0001", "Mitigating", **{"risk-kind": "Risk"}, trigger="t", mitigation="m", due="")])
        self.assertEqual(warns(r, "I4"), ["RSK-0001"])
        r = I.check([item("RSK-0001", "Mitigating", **{"risk-kind": "Risk"}, trigger="t", mitigation="m", due="1 October 2026")])
        self.assertEqual(warns(r, "I4"), [])

    def test_i2_raised_on_required(self):
        r = I.check([item("REQ-0001", "Agreed", moscow="Must", **{"raised-on": ""})])
        self.assertIn("REQ-0001", fails(r, "I2"))


if __name__ == "__main__":
    unittest.main()
