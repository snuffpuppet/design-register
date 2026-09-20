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
    """The handler methods only use self for other methods, so an instance without a socket will do."""
    for _n in ("evidence", "commit", "transition", "create", "edit", "support_accept", "support_link", "supports_preview", "offer_fields", "write_offer", "merge", "delete", "rewrite_links"):
        locals()[_n] = getattr(S.H, _n, None)


class Mode(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); self.saved = (S.ENG, S.CS_DIR, S.DISMISSED_PATH); use(self.d)

    def tearDown(self):
        S.ENG, S.CS_DIR, S.DISMISSED_PATH = self.saved; shutil.rmtree(self.d)

    def test_no_line_means_direct(self):
        open(os.path.join(self.d, "engagement.md"), "w").write("# Engagement: x\n\n## Phases\n\n- P1 (current)\n")
        self.assertEqual(S.load_engagement()["writes"], "direct"); self.assertTrue(S.writes_direct())

    def test_no_file_means_direct(self):
        self.assertEqual(S.load_engagement()["writes"], "direct")

    def test_change_sets_line(self):
        open(os.path.join(self.d, "engagement.md"), "w").write("# Engagement: x\n\n- Writes: change-sets\n- Ingester model version: 2.30\n")
        self.assertEqual(S.load_engagement()["writes"], "change-sets"); self.assertFalse(S.writes_direct())

    def test_unknown_value_is_refused(self):
        open(os.path.join(self.d, "engagement.md"), "w").write("# Engagement: x\n\n- Writes: sideways\n")
        with self.assertRaises(ValueError): S.load_engagement()


class DirectWrites(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); self.saved = (S.ENG, S.CS_DIR, S.DISMISSED_PATH); use(self.d)
        write_item(self.d, "LIM-0001", "No bulk port", "Change requested", impact="Ops", options="1. Vendor adds bulk; 2. Manual", **{"chosen-option": "1"})
        write_item(self.d, "OI-0001", "Chase it", "Open", **{"next action": "ring"})
        self.h = Stub()

    def tearDown(self):
        S.ENG, S.CS_DIR, S.DISMISSED_PATH = self.saved; shutil.rmtree(self.d)

    def read(self, id):
        return IT.parse_item(IT.item_path(self.d, id))

    def no_change_sets(self):
        self.assertFalse(os.path.isdir(S.CS_DIR) and os.listdir(S.CS_DIR))

    def test_create_assigns_the_next_id_and_writes_the_file(self):
        r = self.h.create({"kind": "OI", "fields": {"Title": "New thing", "Owner": "Priya Nair", "Next action": "start", "Source": "meeting"}, "madeBy": "Adam"})
        self.assertEqual(r["item"], "OI-0002")
        it = self.read("OI-0002")
        self.assertEqual(it["title"], "New thing"); self.assertEqual(it["status"], "Open"); self.assertEqual(it["raised-on"], S.today())
        self.assertEqual(len(it["history"]), 1); self.assertIn("Adam", it["history"][0])
        self.no_change_sets()

    def test_edit_rewrites_fields_bumps_updated_and_appends_history(self):
        self.h.edit({"id": "OI-0001", "fields": {"Next action": "email instead"}, "links": ["worked by LIM-0001"], "madeBy": "Adam", "evidence": "call"})
        it = self.read("OI-0001")
        self.assertEqual(it["next action"], "email instead"); self.assertEqual(it["updated"], S.today())
        self.assertIn("worked by LIM-0001", it["links"]); self.assertTrue(it["history"][-1].endswith("| fields updated | call"), it["history"])
        self.no_change_sets()

    def test_transition_moves_sets_closed_on_and_records_the_move(self):
        self.h.transition({"id": "OI-0001", "to": "Closed", "fields": {}, "links": ["resolves into none: done"], "madeBy": "Adam"})
        it = self.read("OI-0001")
        self.assertEqual(it["status"], "Closed"); self.assertEqual(it["closed-on"], S.today())
        self.assertIn("Open → Closed", it["history"][-1]); self.assertNotIn("Open to Closed", it["history"][-1])

    def test_accepted_offer_gets_a_real_id_and_links_both_ways(self):
        items = S.overlay(S.load_registers(), S.load_change_sets())
        s = next(x for x in S.integrity_of(items)["suggestions"] if x["rule"] == "S6" and x["id"] == "LIM-0001")
        r = self.h.support_accept({"id": "LIM-0001", "key": s["key"], "fields": {"Owner": "Tom Okafor"}, "madeBy": "Adam"})
        self.assertEqual(r["item"], "CR-0001")
        self.assertIn("dispositioned by CR-0001", self.read("LIM-0001")["links"])
        self.assertIn("triggered by LIM-0001", self.read("CR-0001")["links"])
        self.assertEqual(self.read("CR-0001")["status"], "Proposed")

    def test_move_with_ticked_offer_links_the_real_id(self):
        write_item(self.d, "RSK-0001", "Slip", "Identified", **{"risk-kind": "Risk", "likelihood": "L", "impact": "H", "mitigation": "watch it", "trigger": "t"})
        pv = self.h.supports_preview({"id": "RSK-0001", "to": "Mitigating", "fields": {}, "links": []})["suggestions"]
        s = next(x for x in pv if x["rule"] == "S17")
        self.h.transition({"id": "RSK-0001", "to": "Mitigating", "fields": {}, "links": [], "madeBy": "Adam", "supports": [{"key": s["key"], "fields": {}}]})
        self.assertIn("mitigated by OI-0002", self.read("RSK-0001")["links"])
        self.assertEqual(self.read("OI-0002")["status"], "Open")

    def test_support_link_writes_both_files(self):
        write_item(self.d, "CR-0001", "Vendor adds bulk port", "Proposed", reason="Ops")
        items = S.overlay(S.load_registers(), S.load_change_sets())
        s = next(x for x in S.integrity_of(items)["suggestions"] if x["rule"] == "S6" and x["id"] == "LIM-0001")
        self.h.support_link({"id": "LIM-0001", "key": s["key"], "target": "CR-0001", "madeBy": "Adam"})
        self.assertIn("dispositioned by CR-0001", self.read("LIM-0001")["links"])
        self.assertIn("triggered by LIM-0001", self.read("CR-0001")["links"])

    def test_change_sets_mode_still_appends_blocks(self):
        open(os.path.join(self.d, "engagement.md"), "w").write("# Engagement: x\n\n- Writes: change-sets\n- Ingester model version: 2.30\n")
        r = self.h.edit({"id": "OI-0001", "fields": {"Next action": "email"}, "madeBy": "Adam"})
        self.assertEqual(r["changeSet"], "CS-0001"); self.assertEqual(self.read("OI-0001")["next action"], "ring")


class Scopes(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); self.saved = (S.ENG, S.CS_DIR, S.DISMISSED_PATH); use(self.d)

    def tearDown(self):
        S.ENG, S.CS_DIR, S.DISMISSED_PATH = self.saved; shutil.rmtree(self.d)

    def eng(self, body):
        open(os.path.join(self.d, "engagement.md"), "w", encoding="utf-8").write(body)

    def test_scopes_parse(self):
        self.eng("# Engagement: x\n\n## Phases\n\n- P1 (current)\n\n## Scopes\n\n- Access\n- Delivery\n")
        self.assertEqual(S.load_engagement()["scopes"], ["Access", "Delivery"])

    def test_phases_still_parse_alongside_scopes(self):
        self.eng("# Engagement: x\n\n## Phases\n\n- P1 (current)\n\n## Scopes\n\n- Access\n")
        e = S.load_engagement()
        self.assertEqual(e["phases"], ["P1"]); self.assertEqual(e["current"], "P1")

    def test_no_scopes_section_is_an_empty_list(self):
        self.eng("# Engagement: x\n\n## Phases\n\n- P1 (current)\n")
        self.assertEqual(S.load_engagement()["scopes"], [])

    def test_scope_is_required_on_create_when_declared(self):
        self.eng("# Engagement: x\n\n## Scopes\n\n- Access\n")
        self.assertIn("scope", S.required_on_create("OI"))

    def test_scope_is_not_required_when_none_declared(self):
        self.eng("# Engagement: x\n")
        self.assertNotIn("scope", S.required_on_create("OI"))

    def test_other_required_fields_are_untouched(self):
        self.eng("# Engagement: x\n")
        self.assertEqual(S.required_on_create("OI"), ["title", "owner", "next action", "source"])
