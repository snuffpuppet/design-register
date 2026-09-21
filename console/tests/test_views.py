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
            {"id": "CP-0009", "kind": "CP", "title": "Add site hierarchy", "status": "For approval", "owner": "P", "raised-on": "9 September 2026",
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
        self.assertIn("CP-0009", text); self.assertIn("Proposed to For approval", text)
        self.assertIn("REQ-0050", text)          # raised this week
        self.assertIn("OI-0006", text); self.assertIn("overdue", text)
        self.assertIn("1 gap", text)

    def test_sections_honours_the_saved_filter_s_types(self):
        items = [
            {"id": "CP-0009", "kind": "CP", "title": "Add site hierarchy", "status": "For approval", "owner": "P", "raised-on": "9 September 2026",
             "updated": "12 September 2026", "history": ["12 September 2026 | Adam | Proposed → For approval | estimate agreed | console session"], "links": []},
            {"id": "REQ-0050", "kind": "REQ", "title": "New need", "status": "Draft", "owner": "", "raised-on": "14 September 2026",
             "updated": "14 September 2026", "history": [], "links": []},
            {"id": "OI-0006", "kind": "OI", "title": "Certificate owner", "status": "Blocked", "owner": "A", "raised-on": "1 September 2026",
             "updated": "1 September 2026", "history": [], "links": [], "due": "12 September 2026"},
        ]
        integ = {"failures": [], "warnings": []}
        view = V.default_views()[0]; view["filter"]["since"] = "8 September 2026"; view["filter"]["types"] = ["CP"]
        s = V.sections(view, items, integ, "15 September 2026")
        self.assertEqual([m["id"] for m in s["moved"]], ["CP-0009"])
        self.assertEqual([r["id"] for r in s["raised"]], ["CP-0009"])   # CP-0009 was also raised this week; REQ-0050 is filtered out
        self.assertEqual([o["id"] for o in s["outstanding"]], ["CP-0009"])   # CP For approval is outstanding; OI-0006 Blocked is filtered out

    def test_sections_splits_move_line_on_the_arrow(self):
        items = [
            {"id": "CP-0009", "kind": "CP", "title": "Add site hierarchy", "status": "For approval", "owner": "P", "raised-on": "9 September 2026",
             "updated": "12 September 2026", "history": ["12 September 2026 | Adam | Proposed → For approval | estimate agreed | console session"], "links": []},
            {"id": "CP-0010", "kind": "CP", "title": "No arrow here", "status": "For approval", "owner": "P", "raised-on": "9 September 2026",
             "updated": "12 September 2026", "history": ["12 September 2026 | Adam | fields updated | console session"], "links": []},
        ]
        integ = {"failures": [], "warnings": []}
        view = V.default_views()[0]; view["filter"]["since"] = "8 September 2026"
        s = V.sections(view, items, integ, "15 September 2026")
        moved = [m for m in s["moved"] if m["id"] == "CP-0009"]
        self.assertEqual(len(moved), 1)
        self.assertEqual(moved[0]["from"], "Proposed")
        self.assertEqual(moved[0]["to"], "For approval")
        self.assertFalse([m for m in s["moved"] if m["id"] == "CP-0010"])
