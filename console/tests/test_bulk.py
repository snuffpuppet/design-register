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
    for _n in ("evidence", "commit", "transition", "edit", "bulk", "supports_preview", "offer_fields", "write_offer"):
        locals()[_n] = getattr(S.H, _n, None)


class Bulk(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); self.saved = (S.ENG, S.CS_DIR, S.DISMISSED_PATH); use(self.d); self.h = Stub()
        write_item(self.d, "REQ-0001", "One", "Draft", moscow="Must", phase="P1")
        write_item(self.d, "REQ-0002", "Two", "Draft", moscow="Must", phase="P1")
        write_item(self.d, "REQ-0003", "Three", "Draft", moscow="Must")   # no phase: Agreed will refuse

    def tearDown(self):
        S.ENG, S.CS_DIR, S.DISMISSED_PATH = self.saved; shutil.rmtree(self.d)

    def read(self, id):
        return IT.parse_item(IT.item_path(self.d, id))

    def test_set_writes_a_field_on_each(self):
        r = self.h.bulk({"ids": ["REQ-0001", "REQ-0002"], "op": "set", "fields": {"Owner": "Tom Okafor"}, "madeBy": "Adam"})
        self.assertEqual(r, {"written": ["REQ-0001", "REQ-0002"], "failed": None})
        self.assertEqual(self.read("REQ-0002")["owner"], "Tom Okafor")
        self.assertTrue(any("Adam" in h for h in self.read("REQ-0002")["history"]))

    def test_preflight_refuses_whole_batch_without_partial_writes(self):
        r = self.h.bulk({"ids": ["REQ-0001", "REQ-0003", "REQ-0002"], "op": "transition", "to": "Agreed", "madeBy": "Adam"})
        self.assertEqual(r["written"], [])
        self.assertEqual(self.read("REQ-0001")["status"], "Draft")
        self.assertEqual(r["failed"]["id"], "REQ-0003"); self.assertIn("Phase", r["failed"]["error"])
        self.assertEqual(self.read("REQ-0002")["status"], "Draft")

    def test_transition_with_shared_fields_fills_the_gap(self):
        r = self.h.bulk({"ids": ["REQ-0003"], "op": "transition", "to": "Agreed", "fields": {"Phase": "P1"}, "madeBy": "Adam"})
        self.assertIsNone(r["failed"]); self.assertEqual(self.read("REQ-0003")["status"], "Agreed")

    def test_link_appends_to_each(self):
        self.h.bulk({"ids": ["REQ-0001", "REQ-0002"], "op": "link", "links": ["worked by OI-0009"], "madeBy": "Adam"})
        self.assertIn("worked by OI-0009", self.read("REQ-0001")["links"])

    def test_withdraw_uses_the_type_table(self):
        r = self.h.bulk({"ids": ["REQ-0001"], "op": "withdraw", "madeBy": "Adam"})
        self.assertIsNone(r["failed"]); self.assertEqual(self.read("REQ-0001")["status"], "Withdrawn")

    def test_refuses_in_change_sets_mode(self):
        open(os.path.join(self.d, "engagement.md"), "w").write("# Engagement: x\n\n- Writes: change-sets\n")
        with self.assertRaises(ValueError): self.h.bulk({"ids": ["REQ-0001"], "op": "set", "fields": {"Owner": "x"}, "madeBy": "Adam"})

    def test_unknown_op_is_refused(self):
        with self.assertRaises(ValueError): self.h.bulk({"ids": ["REQ-0001"], "op": "explode", "madeBy": "Adam"})
