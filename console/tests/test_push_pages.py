import unittest, tempfile, os, shutil, json, importlib.util
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("push_pages", os.path.join(HERE, "push-pages.py")); PP = importlib.util.module_from_spec(spec); spec.loader.exec_module(PP)
import items as IT
import model as M

PAGE = "---\npage-id: 401\npage-title: Requirements\npage-version: 3\npage-url: https://x/wiki/pages/401\nparent-page-id: 400\n---\n\n# Requirements\n\n| Ref | Requirement |\n|---|---|\n| R1 | old |\n"


class BuildWithoutFreeze(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); self.eng = os.path.join(self.d, "abb-nokia"); b = os.path.join(self.eng, "baseline"); os.makedirs(b)
        open(os.path.join(b, "Requirements.md"), "w").write(PAGE)
        it = {"id": "REQ-0001", "kind": "REQ", "title": "Email", "status": "Agreed", "moscow": "Must", "phase": "", "owner": "P", "implemented-by": "Vendor",
              "links": [], "raised-on": "1 September 2026", "closed-on": "", "updated": "14 September 2026", "source": "", "notes": "Baseline import from Requirements",
              "history": ["14 September 2026 | Adam | Draft → Agreed | ok | forum"]}
        p = IT.item_path(self.eng, "REQ-0001"); os.makedirs(os.path.dirname(p)); open(p, "w").write(IT.render_item(it))
        self.cfg = {"parent_page_url": "https://x/wiki/pages/400", "push": {"engagement": "abb-nokia", "mode": "replace-tables"}, "log": [{"action": "pull", "engagement": "abb-nokia"}]}

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_builds_with_as_of_and_no_source_ids(self):
        out = os.path.join(self.eng, "push"); PP.build(self.eng, self.cfg, out)
        m = json.load(open(os.path.join(out, "manifest.json")))
        self.assertEqual(m["as_of"], PP.today()); self.assertNotIn("frozen", m); self.assertEqual(m["pages"][0]["items"], 1)
        body = json.load(open(os.path.join(out, "401.json")))["body"]
        self.assertIn("REQ-0001", body); self.assertIn("Register as at", body); self.assertNotIn("Baselined", body)

    def test_frozen_map_still_fills_source_ids_when_present(self):
        open(os.path.join(self.eng, "baseline", "frozen.md"), "w").write("# Baseline frozen\n\n- Frozen on: 12 September 2026\n\n## Id map\n\n| Source id | Item |\n|---|---|\n| R1 | REQ-0001 |\n")
        out = os.path.join(self.eng, "push"); PP.build(self.eng, self.cfg, out)
        m = json.load(open(os.path.join(out, "manifest.json")))
        self.assertEqual(m["frozen"], "12 September 2026")
        self.assertIn("R1", json.load(open(os.path.join(out, "401.json")))["body"])


class ScopeColumn(unittest.TestCase):
    def test_scope_is_the_fourth_column_when_scopes_are_declared(self):
        for kind in M.DIRS:
            cols = PP.columns(kind, ["Access"])
            self.assertEqual(cols[3], ("Scope", "scope"), f"{kind} column 4 is {cols[3]}")

    def test_no_scope_column_when_none_are_declared(self):
        for kind in M.DIRS:
            self.assertNotIn("scope", [key for _, key in PP.columns(kind, [])],
                             f"{kind} pushes a Scope column for an engagement with no scopes")
