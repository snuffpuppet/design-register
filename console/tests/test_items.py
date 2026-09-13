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
              "reason": "Ops cannot port in bulk", "description": "The vendor builds bulk port", "source": "workshop", "notes": "Baseline import from CRs",
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
        text = IT.render_item(it)
        self.assertNotIn("## History", text)
        p = os.path.join(self.d, "OI-0001.md"); open(p, "w", encoding="utf-8").write(text)
        self.assertEqual(IT.parse_item(p)["history"], [])

    def test_item_path(self):
        self.assertEqual(IT.item_path("/e", "LIM-0003"), "/e/limitations/LIM-0003.md")
