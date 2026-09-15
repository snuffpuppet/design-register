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
