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


def rules_for(res, id):
    return [p["rule"] for p in res["prompts"] if p["id"] == id]


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

    def test_s3_under_assessment_limitation_offers_open_item(self):
        r = I.check([item("LIM-0006", "Under assessment", impact="x", links=["constrains REQ-0001"]), item("REQ-0001", "Agreed", moscow="Must")])
        s = sug(r, "S3", "LIM-0006")
        self.assertEqual(len(s), 1)
        self.assertEqual(s[0]["kind"], "OI"); self.assertEqual(s[0]["status"], "Open")
        self.assertEqual(s[0]["fields"]["title"], "Assess LIM: LIM-0006 title")
        self.assertEqual(s[0]["link"], "assessed by ")

    def test_s3_silent_when_assessed_by_present(self):
        r = I.check([item("LIM-0006", "Under assessment", impact="x", links=["constrains REQ-0001", "assessed by OI-0001"]),
                     item("REQ-0001", "Agreed", moscow="Must"), item("OI-0001", "Open", **{"next action": "x"})])
        self.assertEqual(sug(r, "S3", "LIM-0006"), [])

    def test_s9_realised_risk_offers_open_item(self):
        r = I.check([item("RSK-0004", "Realised", **{"risk-kind": "Risk"}, trigger="t", mitigation="Fail over to the manual path", due="1 October 2026")])
        s = sug(r, "S9", "RSK-0004")
        self.assertEqual(len(s), 1)
        self.assertEqual(s[0]["kind"], "OI"); self.assertEqual(s[0]["status"], "Open")
        self.assertEqual(s[0]["fields"]["title"], "Respond: RSK-0004 title")
        self.assertEqual(s[0]["fields"]["next action"], "Fail over to the manual path")
        self.assertEqual(s[0]["link"], "realised as ")

    def test_s9_silent_when_realised_as_present(self):
        r = I.check([item("RSK-0004", "Realised", **{"risk-kind": "Risk"}, trigger="t", mitigation="m", links=["realised as OI-0001"]),
                     item("OI-0001", "Open", **{"next action": "x"})])
        self.assertEqual(sug(r, "S9", "RSK-0004"), [])

    def test_s9_empty_mitigation_still_offers_a_next_action_box(self):
        r = I.check([item("RSK-0004", "Realised", **{"risk-kind": "Risk"}, trigger="t", mitigation="")])
        s = sug(r, "S9", "RSK-0004")
        self.assertEqual(len(s), 1)
        self.assertIn("next action", s[0]["fields"])
        self.assertEqual(s[0]["fields"]["next action"], "")
        self.assertFalse(s[0]["needsOwner"])

    def test_s8_implemented_by_is_carried_but_not_demanded(self):
        # Optional on a limitation until it is dispositioned (2.30), so an empty value offers no box.
        r = I.check([item("CR-0002", "Proposed", reason="Vendor CR 78", **{"implemented-by": ""})])
        s = sug(r, "S8", "CR-0002")
        self.assertEqual(len(s), 1)
        self.assertNotIn("implemented-by", s[0]["fields"])
        r = I.check([item("CR-0003", "Proposed", reason="Vendor CR 79", **{"implemented-by": "Both"})])
        self.assertEqual(sug(r, "S8", "CR-0003")[0]["fields"]["implemented-by"], "Both")

    def test_s10_closed_open_item_prompts_for_a_resolution(self):
        r = I.check([item("OI-0005", "Closed", **{"next action": "x", "closed-on": "1 September 2026"})])
        self.assertIn("S10", rules_for(r, "OI-0005"))

    def test_s10_silent_when_resolves_into_present(self):
        r = I.check([item("OI-0005", "Closed", **{"next action": "x", "closed-on": "1 September 2026"}, links=["resolves into REQ-0001"]),
                     item("REQ-0001", "Agreed", moscow="Must")])
        self.assertNotIn("S10", rules_for(r, "OI-0005"))

    def test_s11_superseded_decision_offers_its_replacement(self):
        r = I.check([item("DEC-0004", "Superseded", rationale="Chose X over Y", consulted="Vendor",
                          **{"approved-by": "SLT", "closed-on": "1 September 2026"})])
        s = sug(r, "S11", "DEC-0004")
        self.assertEqual(len(s), 1)
        self.assertEqual(s[0]["kind"], "DEC"); self.assertEqual(s[0]["status"], "Proposed")
        self.assertEqual(s[0]["fields"]["rationale"], "Chose X over Y")
        self.assertEqual(s[0]["reverse"], "supersedes DEC-0004")

    def test_s11_silent_when_superseded_by_present(self):
        r = I.check([item("DEC-0004", "Superseded", rationale="x", links=["superseded by DEC-0005"], **{"approved-by": "SLT", "closed-on": "1 September 2026"}),
                     item("DEC-0005", "Proposed", rationale="y")])
        self.assertEqual(sug(r, "S11", "DEC-0004"), [])

    def test_s15_accepted_limitation_without_a_chosen_option_prompts(self):
        r = I.check([item("LIM-0007", "Accepted", impact="x", **{"chosen-option": ""}, links=["constrains REQ-0001", "dispositioned by DEC-0001"]),
                     item("REQ-0001", "Agreed", moscow="Must"), item("DEC-0001", "Accepted", rationale="x", consulted="V", **{"approved-by": "SLT", "closed-on": "1 September 2026"})])
        self.assertIn("S15", rules_for(r, "LIM-0007"))

    def test_s15_silent_when_chosen_option_filled(self):
        r = I.check([item("LIM-0007", "Accepted", impact="x", options="1. Live with it; impact: none; phase: P1\n2. Fix; impact: $; phase: P1",
                          **{"chosen-option": "1"}, links=["constrains REQ-0001", "dispositioned by DEC-0001"]),
                     item("REQ-0001", "Agreed", moscow="Must"), item("DEC-0001", "Accepted", rationale="x", consulted="V", **{"approved-by": "SLT", "closed-on": "1 September 2026"})])
        self.assertNotIn("S15", rules_for(r, "LIM-0007"))

    def test_s16_designed_requirement_without_a_source_prompts(self):
        r = I.check([item("REQ-0008", "Designed", moscow="Must", phase="P1", source="", links=["worked by OI-0001"]),
                     item("OI-0001", "Open", **{"next action": "x"})])
        self.assertIn("S16", rules_for(r, "REQ-0008"))
        self.assertEqual([p["level"] for p in r["prompts"] if p["id"] == "REQ-0008" and p["rule"] == "S16"], ["warn"])

    def test_s16_silent_when_source_names_the_design(self):
        r = I.check([item("REQ-0008", "Designed", moscow="Must", phase="P1", source="Design doc §3.1", links=["worked by OI-0001"]),
                     item("OI-0001", "Open", **{"next action": "x"})])
        self.assertNotIn("S16", rules_for(r, "REQ-0008"))

    def test_s19_delivered_cr_without_a_delivers_link_prompts(self):
        r = I.check([item("CR-0003", "Delivered", reason="x", phase="P1", links=["triggered by LIM-0001"],
                          **{"approved-by": "SLT", "closed-on": "1 September 2026"})])
        self.assertIn("S19", rules_for(r, "CR-0003"))

    def test_s19_silent_when_delivers_present(self):
        r = I.check([item("CR-0003", "Delivered", reason="x", phase="P1", links=["triggered by LIM-0001", "delivers REQ-0001"],
                          **{"approved-by": "SLT", "closed-on": "1 September 2026"}), item("REQ-0001", "Delivered", moscow="Must", phase="P1")])
        self.assertNotIn("S19", rules_for(r, "CR-0003"))

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

    def test_i12_limitation_only_once_dispositioned(self):
        r = I.check([item("LIM-0001", "Identified", impact="x", **{"implemented-by": ""}),
                     item("LIM-0002", "Under assessment", impact="x", **{"implemented-by": ""})])
        self.assertEqual(fails(r, "I12"), [])
        r = I.check([item("LIM-0003", "Accepted", impact="x", **{"implemented-by": ""})])
        self.assertEqual(fails(r, "I12"), ["LIM-0003"])

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


if __name__ == "__main__":
    unittest.main()


class LinkExisting(unittest.TestCase):
    """An offer lists existing records of its type the trigger could link instead of creating one."""
    def test_matches_rank_by_shared_title_tokens_and_skip_other_kinds(self):
        lim = item("LIM-0001", "Accepted", title="One channel per customer", impact="x", options="1. Live; 2. SMS", **{"chosen-option": "1"})
        close = item("DEC-0001", "Proposed", title="Accept one channel per customer", rationale="r")
        far = item("DEC-0002", "Proposed", title="Retire the legacy portal", rationale="r")
        mid = item("DEC-0003", "Proposed", title="Customer channel policy", rationale="r")
        cr = item("CR-0001", "Proposed", title="One channel per customer", reason="r")
        r = I.check([lim, far, close, mid, cr])
        s = sug(r, "S5", "LIM-0001")[0]
        self.assertEqual([m["id"] for m in s["matches"]], ["DEC-0001", "DEC-0003"])
        self.assertEqual(s["matches"][0]["title"], "Accept one channel per customer")
        self.assertEqual(s["matches"][0]["status"], "Proposed")

    def test_matches_never_include_the_trigger_and_are_empty_without_shared_words(self):
        dec = item("DEC-0001", "Superseded", title="Retire the portal", rationale="r")
        other = item("DEC-0002", "Proposed", title="Buy the widget", rationale="r")
        r = I.check([dec, other])
        self.assertEqual(sug(r, "S11", "DEC-0001")[0]["matches"], [])

    def test_matches_capped_at_five(self):
        lim = item("LIM-0001", "Accepted", title="One channel per customer", impact="x", options="1. Live; 2. SMS", **{"chosen-option": "1"})
        decs = [item(f"DEC-{n:04d}", "Proposed", title=f"Channel decision {n}", rationale="r") for n in range(1, 8)]
        r = I.check([lim] + decs)
        self.assertEqual(len(sug(r, "S5", "LIM-0001")[0]["matches"]), 5)
