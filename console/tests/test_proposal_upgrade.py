import tempfile
import unittest
from pathlib import Path

import baseline
import items
import model
import proposal_upgrade
import views


class ProposalUpgrade(unittest.TestCase):
    def test_legacy_records_load_without_any_file_changes(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "engagement.md").write_text("# Engagement: Test\n")
            folder = root / "change-requests"
            folder.mkdir()
            for n, status in enumerate(model.STATES["CR"], 1):
                item = dict(id=f"CR-{n:04}", kind="CR", title="Existing change", status=status,
                            source="Design page section 3", links=["triggered by LIM-0001"],
                            history=["20 September 2026 | Pat | created | legacy"],
                            **{"vendor-ref": "VCR-42", "estimate": "Indicative: $10k; 2 weeks; vendor 20 September 2026"})
                (folder / f"{item['id']}.md").write_text(items.render_item(item))
            before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
            proposals, errors = proposal_upgrade.inspect(root)
            self.assertEqual(errors, [])
            self.assertEqual(len(proposals), len(model.STATES["CR"]))
            self.assertEqual(model.NAMES["CR"], "Change proposal")
            self.assertEqual(proposals[0]["vendor-ref"], "VCR-42")
            self.assertEqual(proposals[0]["links"], ["triggered by LIM-0001"])
            self.assertIn("legacy", proposals[0]["history"][0])
            self.assertIn("solution design", proposal_upgrade.report(proposals, errors))
            self.assertEqual(before, {p: p.read_bytes() for p in root.rglob("*") if p.is_file()})

    def test_invalid_legacy_record_is_reported_without_repair(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "engagement.md").write_text("# Test")
            (root / "change-requests").mkdir()
            (root / "change-requests/CR-0001.md").write_text("---\nid: CR-0001\nstatus: Invented\n---\n")
            proposals, errors = proposal_upgrade.inspect(root)
            self.assertEqual(proposals, [])
            self.assertIn("unrecognised status", errors[0])

    def test_old_and_new_import_headers(self):
        for term in ("Change request", "Change proposal"):
            self.assertEqual(baseline.guess_kind(term), "CR")
            self.assertIn("title", baseline.map_header(["Ref", term, "Status"]))

    def test_options_and_decision_reference_round_trip(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "item.md"
            req = dict(id="REQ-0001", kind="REQ", title="Need", status="Draft", options="1. Internal\n2. Vendor", links=[])
            p.write_text(items.render_item(req))
            self.assertEqual(items.parse_item(p)["options"], req["options"])
            cr = dict(id="CR-0001", kind="CR", title="Work", status="Proposed", links=["based on DEC-0001", "triggered by REQ-0001"])
            p.write_text(items.render_item(cr))
            self.assertEqual(items.parse_item(p)["links"], cr["links"])
            self.assertEqual(model.LINK_WORDS["CR"]["based on"], "DEC")

    def test_phase_and_scope_filter_saved_round_trip_and_legacy(self):
        records = [dict(id="CR-0001", kind="CR", scope="EE", phase="P1"),
                   dict(id="CR-0002", kind="CR", scope="EE", phase="P2"),
                   dict(id="CR-0003", kind="CR", scope="Other", phase="P1")]
        legacy = {**views.blank_filter(), "types": ["CR"], "scopes": ["EE"]}
        self.assertEqual(len(views.apply_filter(records, legacy)), 2)
        with tempfile.TemporaryDirectory() as d:
            p = str(Path(d) / "views.json")
            views.save(p, [{"name": "Phase 1 EE", "filter": {**legacy, "phases": ["P1"]}}])
            self.assertEqual([i["id"] for i in views.apply_filter(records, views.load(p)[0]["filter"])], ["CR-0001"])
