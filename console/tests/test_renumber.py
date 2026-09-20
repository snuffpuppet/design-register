import unittest, tempfile, os, shutil
import subprocess
import server as S
import items as IT
import renumber as R


def use(eng):
    S.ENG = eng; S.CS_DIR = os.path.join(eng, "change-sets"); S.DISMISSED_PATH = os.path.join(eng, "supports-dismissed.json")


def write_item(eng, id, title, status, **f):
    kind = id.split("-")[0]
    it = {"id": id, "kind": kind, "title": title, "status": status, "owner": "Priya Nair", "raised-on": "1 September 2026", "closed-on": "",
          "updated": "1 September 2026", "implemented-by": "Vendor", "source": "workshop", "notes": "", "links": [], "history": []}
    it.update(f)
    p = IT.item_path(eng, id); os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(IT.render_item(it))


class Stub:
    for _n in ("evidence", "commit", "rewrite_links", "renumber", "move_id"):
        locals()[_n] = getattr(S.H, _n, None)


class Plan(unittest.TestCase):
    def test_compacts_in_raised_order_and_keeps_already_right_ids(self):
        items = {"REQ-0002": {"id": "REQ-0002", "kind": "REQ", "raised-on": "2 September 2026"},
                 "REQ-0005": {"id": "REQ-0005", "kind": "REQ", "raised-on": "1 September 2026"},
                 "REQ-0009": {"id": "REQ-0009", "kind": "REQ", "raised-on": "3 September 2026"},
                 "LIM-0004": {"id": "LIM-0004", "kind": "LIM", "raised-on": "1 September 2026"}}
        p = R.plan(items, "REQ")
        self.assertEqual(p["order"], ["REQ-0005", "REQ-0002", "REQ-0009"])
        self.assertEqual(p["map"], {"REQ-0005": "REQ-0001", "REQ-0009": "REQ-0003"})   # REQ-0002 already right


class Renumber(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); self.saved = (S.ENG, S.CS_DIR, S.DISMISSED_PATH); use(self.d); self.h = Stub()
        write_item(self.d, "REQ-0002", "Two", "Draft", **{"raised-on": "2 September 2026"})
        write_item(self.d, "REQ-0005", "Five", "Draft", **{"raised-on": "1 September 2026"})
        write_item(self.d, "LIM-0001", "Lim", "Identified", links=["constrains REQ-0005"])
        write_item(self.d, "CR-0001", "Cr", "Proposed", links=["triggered by LIM-0001", "delivers REQ-0002"])
        subprocess.run(["git", "init", "-q", self.d]); subprocess.run(["git", "-C", self.d, "add", "-A"])
        subprocess.run(["git", "-C", self.d, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "seed"])

    def tearDown(self):
        S.ENG, S.CS_DIR, S.DISMISSED_PATH = self.saved; shutil.rmtree(self.d)

    def read(self, id):
        return IT.parse_item(IT.item_path(self.d, id))

    def test_refuses_on_a_dirty_tree(self):
        open(os.path.join(self.d, "scratch.txt"), "w").write("x")
        with self.assertRaises(ValueError): self.h.renumber({"type": "REQ", "madeBy": "Adam", "allowUnpublished": True})

    def test_refuses_when_not_a_git_repository(self):
        d = tempfile.mkdtemp()
        try:
            use(d)
            write_item(d, "REQ-0005", "Five", "Draft", **{"raised-on": "1 September 2026"})
            with self.assertRaises(ValueError) as cm: self.h.renumber({"type": "REQ", "madeBy": "Adam", "allowUnpublished": True})
            self.assertIn("not a git repository", str(cm.exception))
        finally:
            use(self.d); shutil.rmtree(d)

    def test_renames_files_rewrites_links_and_writes_the_map(self):
        r = self.h.renumber({"type": "REQ", "madeBy": "Adam", "allowUnpublished": True})
        self.assertEqual(r["map"], {"REQ-0005": "REQ-0001"})
        self.assertTrue(os.path.exists(IT.item_path(self.d, "REQ-0001")))
        self.assertFalse(os.path.exists(IT.item_path(self.d, "REQ-0005")))
        self.assertEqual(self.read("REQ-0001")["title"], "Five")
        self.assertTrue(any("renumbered from REQ-0005" in h for h in self.read("REQ-0001")["history"]))
        self.assertEqual(self.read("LIM-0001")["links"], ["constrains REQ-0001"])
        self.assertEqual(self.read("CR-0001")["links"], ["triggered by LIM-0001", "delivers REQ-0002"])
        self.assertIn("LIM-0001", r["touched"])
        self.assertIn("REQ-0005 → REQ-0001", open(os.path.join(self.d, "renumbered.md")).read())

    def test_refuses_when_the_staging_range_is_occupied(self):
        write_item(self.d, "REQ-9001", "Nine", "Draft")
        subprocess.run(["git", "-C", self.d, "add", "-A"])
        subprocess.run(["git", "-C", self.d, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "occupy"])
        with self.assertRaises(ValueError): self.h.renumber({"type": "REQ", "madeBy": "Adam", "allowUnpublished": True})
        self.assertTrue(os.path.exists(IT.item_path(self.d, "REQ-0005")))
        self.assertTrue(os.path.exists(IT.item_path(self.d, "REQ-9001")))

    def test_refuses_in_change_sets_mode(self):
        open(os.path.join(self.d, "engagement.md"), "w").write("# Engagement: x\n\n- Writes: change-sets\n")
        subprocess.run(["git", "-C", self.d, "add", "-A"]); subprocess.run(["git", "-C", self.d, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "m"])
        with self.assertRaises(ValueError): self.h.renumber({"type": "REQ", "madeBy": "Adam", "allowUnpublished": True})
