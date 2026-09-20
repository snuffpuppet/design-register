import unittest, tempfile, os, json, shutil
import server as S
import items as IT
import baseline as B
from tests.test_server_direct import write_item, Stub


def use(eng):
    S.ENG = eng; S.CS_DIR = os.path.join(eng, "change-sets"); S.B_DIR = os.path.join(eng, "baseline")
    S.DISMISSED_PATH = os.path.join(eng, "supports-dismissed.json"); S.DUP_PATH = os.path.join(eng, "duplicates-dismissed.json")


class Base(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); self.saved = (S.ENG, S.CS_DIR, S.B_DIR, S.DISMISSED_PATH, S.DUP_PATH); use(self.d)
        self.h = Stub()

    def tearDown(self):
        S.ENG, S.CS_DIR, S.B_DIR, S.DISMISSED_PATH, S.DUP_PATH = self.saved; shutil.rmtree(self.d)

    def read(self, id):
        return IT.parse_item(IT.item_path(self.d, id))

    def req(self, **k):
        return {"madeBy": "Adam", "evidence": "", **k}


class Dupes(Base):
    def test_clusters_over_items_find_overlapping_titles(self):
        write_item(self.d, "REQ-0001", "Bulk number porting for operations", "Draft")
        write_item(self.d, "REQ-0002", "Operations bulk porting of numbers", "Draft")
        write_item(self.d, "REQ-0003", "Email alerts", "Draft")
        groups = S.state()["dupes"]
        self.assertEqual(groups, [["REQ-0001", "REQ-0002"]])

    def test_dismissed_group_stays_out(self):
        write_item(self.d, "REQ-0001", "Bulk number porting for operations", "Draft")
        write_item(self.d, "REQ-0002", "Operations bulk porting of numbers", "Draft")
        S.dismiss_dup(["REQ-0002", "REQ-0001"])
        self.assertEqual(S.state()["dupes"], [])
        self.assertTrue(os.path.exists(S.DUP_PATH))
        S.dismiss_dup(["REQ-0001", "REQ-0002"], undo=True)
        self.assertEqual(len(S.state()["dupes"]), 1)


class Merge(Base):
    def setUp(self):
        super().setUp()
        write_item(self.d, "REQ-0001", "Bulk porting", "Draft", source="page A", notes="", moscow="", links=["constrained by LIM-0001"])
        write_item(self.d, "REQ-0002", "Bulk number porting", "Agreed", source="page B", notes="from the vendor", moscow="Must", links=["constrained by LIM-0001"])
        write_item(self.d, "LIM-0001", "No bulk port", "Identified", links=["constrains REQ-0002", "constrains REQ-0001"])
        write_item(self.d, "DEC-0001", "Manual port", "Proposed", links=["dispositions LIM-0001", "affects REQ-0002"])

    def test_merge_folds_rewrites_and_removes(self):
        r = self.h.merge(self.req(survivor="REQ-0001", losers=["REQ-0002"], resolutions={"title":"Bulk porting","status":"Draft"}))
        self.assertEqual(r["removed"], ["REQ-0002"])
        self.assertFalse(os.path.exists(IT.item_path(self.d, "REQ-0002")))
        s = self.read("REQ-0001")
        self.assertEqual(s["status"], "Draft")            # never taken from the loser
        self.assertEqual(s["moscow"], "Must")             # blank on the survivor, filled from the loser
        self.assertIn("page B", s["source"]); self.assertIn("page A", s["source"])
        self.assertIn("Merged in from REQ-0002: from the vendor", s["notes"])
        self.assertEqual(s["links"], ["constrained by LIM-0001"])
        self.assertTrue(any("merged REQ-0002 into this item" in h for h in s["history"]))
        lim = self.read("LIM-0001")
        self.assertEqual(lim["links"], ["constrains REQ-0001"])
        self.assertTrue(any("merged REQ-0002 into REQ-0001" in h for h in lim["history"]))
        dec = self.read("DEC-0001")
        self.assertIn("affects REQ-0001", dec["links"]); self.assertNotIn("affects REQ-0002", dec["links"])
        self.assertIn("DEC-0001", r["touched"]); self.assertIn("LIM-0001", r["touched"])

    def test_merge_drops_survivors_own_link_to_loser(self):
        write_item(self.d, "DEC-0001", "Manual port", "Proposed", links=["supersedes DEC-0002"])
        write_item(self.d, "DEC-0002", "Old manual port note", "Proposed", links=["superseded by DEC-0001"])
        r = self.h.merge(self.req(survivor="DEC-0001", losers=["DEC-0002"], resolutions={"title":"Manual port"}))
        self.assertFalse(os.path.exists(IT.item_path(self.d, "DEC-0002")))
        dec = self.read("DEC-0001")
        self.assertFalse(any("DEC-0002" in l for l in dec["links"]))

    def test_merge_refuses_across_types_and_writes_nothing(self):
        with self.assertRaises(ValueError):
            self.h.merge(self.req(survivor="REQ-0001", losers=["LIM-0001"]))
        self.assertTrue(os.path.exists(IT.item_path(self.d, "LIM-0001")))
        self.assertEqual(self.read("REQ-0001")["history"], [])

    def test_merge_refuses_in_change_sets_mode(self):
        open(os.path.join(self.d, "engagement.md"), "w").write("# Engagement: x\n\n- Writes: change-sets\n")
        with self.assertRaises(ValueError) as e:
            self.h.merge(self.req(survivor="REQ-0001", losers=["REQ-0002"], resolutions={"title":"Bulk porting","status":"Draft"}))
        self.assertIn("change set", str(e.exception).lower())
        self.assertTrue(os.path.exists(IT.item_path(self.d, "REQ-0002")))


class Delete(Base):
    def setUp(self):
        super().setUp()
        write_item(self.d, "REQ-0002", "Bulk number porting", "Agreed")
        write_item(self.d, "LIM-0001", "No bulk port", "Identified", links=["constrains REQ-0002"])

    def test_delete_drops_links_and_removes_file(self):
        r = self.h.delete(self.req(id="REQ-0002", reason="not a requirement"))
        self.assertFalse(os.path.exists(IT.item_path(self.d, "REQ-0002")))
        lim = self.read("LIM-0001")
        self.assertEqual(lim["links"], [])
        self.assertTrue(any("dropped link to REQ-0002, deleted: not a requirement" in h for h in lim["history"]))
        self.assertEqual(r["touched"], ["LIM-0001"])

    def test_delete_needs_a_reason(self):
        with self.assertRaises(ValueError):
            self.h.delete(self.req(id="REQ-0002", reason=""))
        self.assertTrue(os.path.exists(IT.item_path(self.d, "REQ-0002")))

    def test_delete_refuses_in_change_sets_mode(self):
        open(os.path.join(self.d, "engagement.md"), "w").write("# Engagement: x\n\n- Writes: change-sets\n")
        with self.assertRaises(ValueError):
            self.h.delete(self.req(id="REQ-0002", reason="x"))


class Unreviewed(Base):
    def setUp(self):
        super().setUp()
        os.makedirs(S.B_DIR)
        json.dump({"c1": {"frozenAs": "REQ-0001"}, "c2": {"frozenAs": "REQ-0002", "verdict": "Accept"},
                   "c3": {"frozenAs": "REQ-0002", "verdict": "Merge", "mergedInto": "c2"}},
                  open(os.path.join(S.B_DIR, "verdicts.json"), "w"))
        write_item(self.d, "REQ-0001", "One", "Draft"); write_item(self.d, "REQ-0002", "Two", "Draft"); write_item(self.d, "REQ-0003", "Raised here", "Draft")

    def test_unreviewed_is_the_frozen_from_candidate_with_no_verdict(self):
        self.assertEqual(S.state()["unreviewed"], ["REQ-0001"])

    def test_mark_reviewed_sets_accept(self):
        self.assertTrue(B.mark_reviewed(S.B_DIR, "REQ-0001"))
        self.assertEqual(S.state()["unreviewed"], [])
        self.assertEqual(B.load_verdicts(S.B_DIR)["c1"]["verdict"], "Accept")

    def test_mark_reviewed_on_a_console_item_is_a_no_op(self):
        self.assertFalse(B.mark_reviewed(S.B_DIR, "REQ-0003"))

    def test_no_baseline_folder_means_nothing_unreviewed(self):
        shutil.rmtree(S.B_DIR)
        self.assertEqual(S.state()["unreviewed"], [])
