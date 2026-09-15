import re
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

    def test_every_raised_rule_is_named(self):
        raised = set(re.findall(r'(?:fail|warn)\("(I\d+)"', open("integrity.py").read()))
        self.assertTrue(raised, "expected integrity.py to raise at least one rule")
        for rule in raised:
            self.assertIn(rule, M.RULES, f"{rule} has no entry in M.RULES")


class Scope(unittest.TestCase):
    def test_scope_is_first_short_field_on_every_type(self):
        for kind in M.DIRS:
            self.assertEqual(M.SHORT[kind][0], "scope", f"{kind} does not lead with scope")

    def test_scope_has_a_label(self):
        self.assertEqual(M.LABELS["scope"], "Scope")

    def test_scope_is_required_on_create_for_every_type(self):
        for kind in M.DIRS:
            self.assertIn("scope", M.REQUIRED_ON_CREATE[kind], f"{kind} does not require scope")

    def test_i24_is_stated(self):
        self.assertIn("I24", M.RULES)
        self.assertIn("Scope", M.RULES["I24"])


class Specials(unittest.TestCase):
    def test_blocked_needs_the_prefix(self):
        it = {"kind": "OI", "status": "Open", "next action": "wait", "owner": "x", "links": []}
        self.assertIn('Next action starting "Blocked: "', M.missing_for("OI", "Blocked", it))
        it["next action"] = "Blocked: waiting"
        self.assertEqual(M.missing_for("OI", "Blocked", it), [])

    def test_vendor_cr_needs_vendor_ref_for_submitted(self):
        it = {"kind": "CR", "status": "Approved", "approved-by": "x", "phase": "P1", "implemented-by": "Vendor", "links": []}
        self.assertIn("Vendor ref", M.missing_for("CR", "Submitted", it))
        it["implemented-by"] = "Internal"
        self.assertEqual(M.missing_for("CR", "Submitted", it), [])

    def test_withdraws_names_a_terminal_state_per_type(self):
        for k, st in M.WITHDRAWS.items():
            self.assertIn(st, M.TERMINAL[k], k)
        self.assertEqual(M.WITHDRAWS["DEC"], "Rejected")

    def test_provenance_words_are_link_words(self):
        for k, words in list(M.BACKWARD.items()) + list(M.FORWARD.items()):
            for w in words:
                self.assertIn(w, M.LINK_WORDS[k], f"{k} {w}")


if __name__ == "__main__":
    unittest.main()
