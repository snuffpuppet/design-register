import unittest
import model as M


class ModelTables(unittest.TestCase):
    def test_every_transition_target_is_a_state(self):
        for kind, moves in M.TRANSITIONS.items():
            for frm, tos in moves.items():
                self.assertIn(frm, M.STATES[kind])
                for to in tos:
                    self.assertIn(to, M.STATES[kind], f"{kind} {frm} -> {to}")

    def test_first_state_is_first_listed(self):
        for kind, st in M.FIRST_STATE.items():
            self.assertEqual(st, M.STATES[kind][0])

    def test_supports_rows_are_well_formed(self):
        seen = set()
        for r in M.SUPPORTS:
            self.assertNotIn(r["rule"], seen); seen.add(r["rule"])
            kind, states = r["when"]
            self.assertIn(kind, M.STATES)
            # None means every state (S8): nothing to check per-state.
            for st in (states or []):
                self.assertIn(st, M.STATES[kind], r["rule"])
            self.assertIn(r["level"], ("fail", "warn"))
            if r["offer"]:
                okind, ostate = r["offer"]
                self.assertIn(ostate, M.STATES[okind], r["rule"])
                self.assertEqual(ostate, M.FIRST_STATE[okind], f"{r['rule']} must offer the first state")
                word, oword = r["link"]
                self.assertIn(word, M.LINK_WORDS[kind], f"{r['rule']} link word {word} not registered for {kind}")
                if oword:
                    self.assertIn(oword, M.LINK_WORDS[okind], f"{r['rule']} reverse word {oword} not registered for {okind}")
            else:
                self.assertTrue(r.get("prompt"), r["rule"])

    def test_new_link_words(self):
        self.assertEqual(M.LINK_WORDS["RSK"]["mitigated by"], "OI")
        self.assertEqual(M.LINK_WORDS["LIM"]["needs"], "REQ")

    def test_rules_named(self):
        for n in ("I21", "I22", "I23"):
            self.assertIn(n, M.RULES)


if __name__ == "__main__":
    unittest.main()
