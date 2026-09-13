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


if __name__ == "__main__":
    unittest.main()
