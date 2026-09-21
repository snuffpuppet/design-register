import unittest
import integrity as I


def it(id, status, links=(), title=""):
    return {"id": id, "kind": id.split("-")[0], "status": status, "title": title or id, "links": list(links)}


class Provenance(unittest.TestCase):
    def setUp(self):
        self.items = [
            it("DEC-0003", "Accepted", ["introduces LIM-0004"]),
            it("LIM-0004", "Change requested", ["introduced by DEC-0003", "constrains REQ-0042", "dispositioned by CP-0009"]),
            it("REQ-0042", "Agreed"),
            it("CP-0009", "For approval", ["triggered by LIM-0004", "worked by OI-0011", "delivers REQ-0099"]),
            it("OI-0011", "Open"),
        ]
        self.by = {x["id"]: x for x in self.items}
        self.p = I.provenance(self.items, self.by)

    def test_backward_hop_carries_word_and_neighbour(self):
        back = self.p["CP-0009"]["back"]
        self.assertEqual([(b["word"], b["id"], b["status"]) for b in back], [("triggered by", "LIM-0004", "Change requested")])

    def test_forward_hop(self):
        fwd = self.p["CP-0009"]["forward"]
        self.assertEqual([(f["word"], f["id"]) for f in fwd], [("worked by", "OI-0011")])

    def test_dangling_link_is_reported_not_walked(self):
        self.assertEqual(self.p["CP-0009"]["dangling"], ["delivers REQ-0099"])

    def test_reverse_of_a_backward_word_appears_forward_on_the_target(self):
        # LIM-0004 introduced by DEC-0003; DEC-0003 also writes introduces. One entry, not two.
        fwd = self.p["DEC-0003"]["forward"]
        self.assertEqual([(f["word"], f["id"]) for f in fwd], [("introduces", "LIM-0004")])

    def test_item_with_no_links_has_empty_chains(self):
        self.assertEqual(self.p["OI-0011"], {"back": [], "forward": [], "dangling": []})

    def test_link_with_word_but_no_id_token_is_dangling(self):
        # "triggered by nothing here" has the word but no id, should go to dangling
        items = [it("CP-0001", "Open", ["triggered by nothing here"])]
        by = {x["id"]: x for x in items}
        p = I.provenance(items, by)
        self.assertEqual(p["CP-0001"]["dangling"], ["triggered by nothing here"])
