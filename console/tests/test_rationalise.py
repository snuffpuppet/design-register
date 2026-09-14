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
