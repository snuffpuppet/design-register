import unittest, tempfile, os, shutil
import server as S


def write_item(eng, kind, id, title, status, **f):
    d = {"REQ": "requirements", "DEC": "decisions", "LIM": "limitations", "CP": "change-proposals", "OI": "open-items", "RSK": "risks"}[kind]
    os.makedirs(os.path.join(eng, d), exist_ok=True)
    lines = [f"id: {id}", f"title: {title}", f"status: {status}", "owner: Priya Nair", "raised-on: 1 September 2026", "implemented-by: Vendor", "source: workshop", "updated: 1 September 2026"]
    lines += [f"{k}: {v}" for k, v in f.items()]
    open(os.path.join(eng, d, id + ".md"), "w", encoding="utf-8").write("---\n" + "\n".join(lines) + "\n---\n\n## Rationale\n\nr\n")


class Stub:
    """The handler methods only use self for other methods, so an instance without a socket will do."""
    evidence = S.H.evidence; support_link = S.H.support_link; commit = S.H.commit


class LiveLink(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); self.eng = os.path.join(self.d, "eng"); os.makedirs(self.eng)
        self.saved = (S.ENG, S.CS_DIR, S.DISMISSED_PATH)
        S.ENG = self.eng; S.CS_DIR = os.path.join(self.eng, "change-sets"); S.DISMISSED_PATH = os.path.join(self.eng, "supports-dismissed.json")
        open(os.path.join(self.eng, "engagement.md"), "w").write("# Engagement: x\n\n- Writes: change-sets\n- Ingester model version: 2.35\n")
        write_item(self.eng, "LIM", "LIM-0001", "No bulk port", "Change requested", impact="Ops", options="1. Vendor adds bulk; 2. Manual", **{"chosen-option": "1"})
        write_item(self.eng, "CP", "CP-0001", "Vendor adds bulk port", "Proposed", reason="Ops")
        write_item(self.eng, "DEC", "DEC-0001", "Bulk port stance", "Proposed")

    def tearDown(self):
        S.ENG, S.CS_DIR, S.DISMISSED_PATH = self.saved
        shutil.rmtree(self.d)

    def items(self):
        return S.overlay(S.load_registers(), S.load_change_sets())

    def s6(self):
        return next(s for s in S.integrity_of(self.items())["suggestions"] if s["rule"] == "S6")

    def test_offer_carries_matches_from_the_registers(self):
        self.assertEqual([m["id"] for m in self.s6()["matches"]], ["CP-0001"])

    def test_link_writes_an_edit_block_each_way_and_the_offer_goes(self):
        s = self.s6()
        r = Stub().support_link({"id": "LIM-0001", "key": s["key"], "target": "CP-0001", "madeBy": "Adam"})
        self.assertTrue(r["ok"])
        cs = S.load_change_sets()[0]
        self.assertEqual(len(cs["blocks"]), 2)
        self.assertEqual(cs["blocks"][0]["fields"]["Target"], "LIM-0001"); self.assertIn("dispositioned by CP-0001", cs["blocks"][0]["links"])
        self.assertEqual(cs["blocks"][1]["fields"]["Target"], "CP-0001"); self.assertIn("triggered by LIM-0001", cs["blocks"][1]["links"])
        self.assertFalse(any(x["rule"] == "S6" for x in S.integrity_of(self.items())["suggestions"]))

    def test_link_refuses_the_wrong_kind_and_an_unknown_target(self):
        s = self.s6()
        with self.assertRaises(ValueError): Stub().support_link({"id": "LIM-0001", "key": s["key"], "target": "DEC-0001", "madeBy": "Adam"})
        with self.assertRaises(ValueError): Stub().support_link({"id": "LIM-0001", "key": s["key"], "target": "CP-0099", "madeBy": "Adam"})
        self.assertEqual(S.load_change_sets()[0]["blocks"] if S.load_change_sets() else [], [])
