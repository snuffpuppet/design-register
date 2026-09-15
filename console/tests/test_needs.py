import unittest, tempfile, os, shutil
import server as S
import items as IT


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
    for _n in ("needs", "search_items", "model_payload"):
        locals()[_n] = getattr(S.H, _n, None)


class Needs(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); self.saved = (S.ENG, S.CS_DIR, S.DISMISSED_PATH); use(self.d); self.h = Stub()
        write_item(self.d, "REQ-0001", "One", "Draft", moscow="Must")
        write_item(self.d, "REQ-0002", "Two", "Draft", moscow="Must", phase="P1")
        write_item(self.d, "REQ-0003", "Three", "Verified", moscow="Must", phase="P1")
        write_item(self.d, "CR-0001", "Vendor CR", "Approved", **{"approved-by": "Board", "phase": "P1", "reason": "r"})
        write_item(self.d, "OI-0001", "Wait", "Open", **{"next action": "wait"})

    def tearDown(self):
        S.ENG, S.CS_DIR, S.DISMISSED_PATH = self.saved; shutil.rmtree(self.d)

    def test_needs_lists_missing_per_item(self):
        r = self.h.needs({"ids": ["REQ-0001", "REQ-0002"], "to": "Agreed"})["needs"]
        self.assertEqual(r["REQ-0001"], {"ok": False, "missing": ["Phase"], "from": "Draft"})
        self.assertEqual(r["REQ-0002"], {"ok": True, "missing": [], "from": "Draft"})

    def test_needs_refuses_a_move_the_model_forbids(self):
        r = self.h.needs({"ids": ["REQ-0003"], "to": "Agreed"})["needs"]["REQ-0003"]
        self.assertFalse(r["ok"]); self.assertIn("not an allowed move", r["missing"][0])

    def test_needs_includes_specials(self):
        self.assertEqual(self.h.needs({"ids": ["CR-0001"], "to": "Submitted"})["needs"]["CR-0001"]["missing"], ["Vendor ref"])
        self.assertEqual(self.h.needs({"ids": ["OI-0001"], "to": "Blocked"})["needs"]["OI-0001"]["missing"], ['Next action starting "Blocked: "'])

    def test_search_filters_by_type_and_text_and_excludes(self):
        r = self.h.search_items({"q": "o", "types": ["REQ"], "exclude": "REQ-0001"})["items"]
        self.assertEqual([x["id"] for x in r], ["REQ-0002"])   # "Two" contains o; "Three" does not; REQ-0001 excluded
        r = self.h.search_items({"q": "0001", "types": [], "exclude": ""})["items"]
        self.assertEqual([x["id"] for x in r], ["CR-0001", "OI-0001", "REQ-0001"])

    def test_model_payload_carries_the_new_tables(self):
        m = self.h.model_payload()
        self.assertEqual(m["withdraws"]["DEC"], "Rejected")
        self.assertIn("triggered by", m["backward"]["CR"])
        self.assertEqual(m["specials"][0]["kind"], "OI")
        self.assertIn("Priya Nair", m["owners"])
