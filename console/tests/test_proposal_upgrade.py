import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import baseline
import items
import model
import operations as O
import proposal_upgrade as P
import server as S
import views


class ProposalUpgrade(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / 'engagement.md').write_text('# Engagement: Test\n- Writes: direct\n- Ingester model version: 2.30\n')

    def tearDown(self): self.tmp.cleanup()

    def write(self, id, links=None, status='Proposed'):
        kind = id.split('-')[0]
        folder = 'change-requests' if kind == 'CR' else model.DIRS[kind]
        path = self.root / folder / (id + '.md')
        path.parent.mkdir(exist_ok=True)
        # Original vendor reference is intentionally identical to an internal ID.
        path.write_text('---\nid: ' + id + '\ntitle: Vendor CR-0001 capability\nstatus: ' + status +
                        '\nvendor-ref: CR-0001\nlinks:\n' + ''.join('  - ' + l + '\n' for l in (links or [])) +
                        '---\n\n## Source\n\nVendor CR-0001 and Design section 3\n\n## History\n\n- 20 September 2026 | Pat | created CR-0001\n')
        return path

    def save(self, name, value):
        path = self.root / name
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(value))

    def apply(self):
        plan = P.plan(self.root)
        P.apply(self.root, plan['token'], 'Pat')
        return plan

    def test_preview_is_read_only_and_apply_moves_records_and_links_losslessly(self):
        source = self.write('CR-0001', ['triggered by LIM-0001'])
        self.write('LIM-0001', ['dispositioned by CR-0001', 'https://vendor.example/CR-0001', 'Vendor request CR-0001'], status='Change requested')
        before = O.snapshot(self.root)
        plan = P.plan(self.root)
        self.assertEqual(before, O.snapshot(self.root))
        self.assertEqual(plan['mapping'], {'CR-0001': 'CP-0001'})
        self.assertIn('CR-0001 → CP-0001', P.report(plan))
        P.apply(self.root, plan['token'], 'Pat')
        self.assertFalse(source.exists())
        cp = items.parse_item(self.root / 'change-proposals/CP-0001.md')
        self.assertEqual(cp['kind'], 'CP')
        self.assertEqual(cp['vendor-ref'], 'CR-0001')
        self.assertEqual(cp['history'], ['20 September 2026 | Pat | created CR-0001'])
        self.assertEqual(cp['source'], 'Vendor CR-0001 and Design section 3')
        self.assertIn('dispositioned by CP-0001', (self.root / 'limitations/LIM-0001.md').read_text())
        self.assertIn('https://vendor.example/CR-0001', (self.root / 'limitations/LIM-0001.md').read_text())
        self.assertIn('Vendor request CR-0001', (self.root / 'limitations/LIM-0001.md').read_text())
        self.assertEqual(json.loads((self.root / 'aliases.json').read_text())['CR-0001']['targets'], ['CP-0001'])
        op = O.records(self.root)[0]
        self.assertEqual(op['status'], 'applied')
        self.assertEqual(op['by'], 'Pat')
        self.assertEqual(op['mapping'], plan['mapping'])
        self.assertEqual(op['before']['change-requests/CR-0001.md'], before['change-requests/CR-0001.md'])
        with patch.object(S, 'ENG', str(self.root)):
            self.assertIn('CP-0001', S.load_registers())
            self.assertNotIn('CR-0001', S.load_registers())

    def test_every_legacy_status_is_preserved(self):
        for n, status in enumerate(model.STATES['CP'], 1): self.write(f'CR-{n:04}', status=status)
        self.apply()
        for n, status in enumerate(model.STATES['CP'], 1):
            self.assertEqual(items.parse_item(self.root / f'change-proposals/CP-{n:04}.md')['status'], status)

    def test_references_in_views_sessions_bin_and_baseline_migrate(self):
        source = self.write('CR-0001')
        snapshot = items.parse_item(source)
        record = {'id': 'MTG-1', 'ids': ['CR-0001'], 'snapshot': {'CR-0001': snapshot},
                  'entries': {'CR-0001': {'basedOn': 'old-review-revision', 'evidence': 'CR-0001', 'links': ['part of CR-0001']}}, 'revision': 'old'}
        self.save('meetings.json', [record]); self.save('reviews.json', [record])
        self.save('views.json', [{'name': 'CR-0001 costs', 'filter': {'types': ['CR'], 'phases': ['P1']}}])
        deleted = {**snapshot, 'id': 'CR-0002', 'links': ['part of CR-0001']}
        self.save('rubbish-bin.json', [{'key': '1', 'item': deleted, 'incoming': {'CR-0001': ['part of CR-0002']}, 'restored': False, 'pendingSources': ['CR-0001']}])
        (self.root / 'baseline').mkdir()
        frozen = '| Source id | Item id |\n| CR-0001 | CR-0001 |\n'
        (self.root / 'baseline/frozen.md').write_text(frozen)
        self.apply()
        for name in ('meetings.json', 'reviews.json'):
            migrated = json.loads((self.root / name).read_text())[0]
            self.assertEqual(migrated['ids'], ['CP-0001'])
            self.assertEqual(migrated['snapshot']['CP-0001']['kind'], 'CP')
            self.assertEqual(migrated['snapshot']['CP-0001']['vendor-ref'], 'CR-0001')
            self.assertEqual(migrated['entries']['CP-0001']['basedOn'], 'old-review-revision')
            self.assertEqual(migrated['entries']['CP-0001']['evidence'], 'CR-0001')
            self.assertNotEqual(migrated['revision'], 'old')
        view = json.loads((self.root / 'views.json').read_text())[0]
        self.assertEqual(view['filter']['types'], ['CP']); self.assertEqual(view['name'], 'CR-0001 costs')
        entry = json.loads((self.root / 'rubbish-bin.json').read_text())[0]
        self.assertEqual(entry['item']['id'], 'CP-0002')
        self.assertEqual(entry['item']['links'], ['part of CP-0001'])
        self.assertEqual(entry['incoming'], {'CP-0001': ['part of CP-0002']})
        self.assertEqual(entry['pendingSources'], ['CP-0001'])
        aliases = json.loads((self.root / 'aliases.json').read_text())
        self.assertIn('CP-0002', aliases)  # Reserve binned IDs so newly created CPs cannot reuse them.
        self.assertEqual(aliases['CP-0002']['targets'], [])
        self.assertIn('| CR-0001 | CP-0001 |', (self.root / 'baseline/frozen.md').read_text())
        self.assertEqual(P.plan(self.root)['mapping'], {})

    def test_ui_undo_cannot_restore_old_model_records(self):
        self.write('CR-0001'); self.apply()
        with self.assertRaisesRegex(ValueError, 'offline'): O.undo(self.root, O.records(self.root)[0]['id'])

    def test_alias_chains_and_idempotence(self):
        self.write('CR-0001')
        self.save('aliases.json', {'CR-0002': {'targets': ['CR-0001'], 'reason': 'merged'}})
        self.apply()
        aliases = json.loads((self.root / 'aliases.json').read_text())
        self.assertEqual(aliases['CR-0002']['targets'], ['CP-0002'])
        self.assertEqual(aliases['CP-0002']['targets'], ['CP-0001'])
        before = O.snapshot(self.root)
        repeat = self.apply()
        self.assertEqual(repeat['mapping'], {})
        self.assertEqual(repeat['writes'], {})
        self.assertEqual(before, O.snapshot(self.root))
        self.assertEqual(len(O.records(self.root)), 1)

    def test_collisions_and_pending_change_sets_refuse_without_writes(self):
        self.write('CR-0001'); self.write('CP-0001')
        before = O.snapshot(self.root)
        with self.assertRaisesRegex(ValueError, 'collision'): P.plan(self.root)
        self.assertEqual(before, O.snapshot(self.root))
        (self.root / 'change-proposals/CP-0001.md').unlink()
        (self.root / 'change-sets').mkdir()
        (self.root / 'change-sets/CS-0001.md').write_text('# Session\n- Applied on: \n')
        with self.assertRaisesRegex(ValueError, 'unapplied'): P.plan(self.root)

    def test_stale_preview_and_missing_operator_refuse(self):
        self.write('CR-0001')
        plan = P.plan(self.root)
        with self.assertRaisesRegex(ValueError, 'Made by'): P.apply(self.root, plan['token'], '')
        (self.root / 'engagement.md').write_text('# Engagement: changed')
        with self.assertRaisesRegex(ValueError, 'stale'): P.apply(self.root, plan['token'], 'Pat')
        self.assertTrue((self.root / 'change-requests/CR-0001.md').exists())
        self.assertEqual(O.records(self.root), [])

    def test_failure_rolls_back_every_file(self):
        self.write('CR-0001'); self.write('LIM-0001', ['dispositioned by CR-0001'], 'Change requested')
        before = O.snapshot(self.root); plan = P.plan(self.root)
        real = O.atomic; failed = False
        def fail_once(path, text):
            nonlocal failed
            if str(path).endswith('aliases.json') and not failed:
                failed = True
                raise OSError('injected failure')
            return real(path, text)
        with patch.object(O, 'atomic', side_effect=fail_once):
            with self.assertRaisesRegex(OSError, 'injected'): P.apply(self.root, plan['token'], 'Pat')
        self.assertEqual(O.snapshot(self.root), before)
        self.assertEqual(O.records(self.root)[0]['status'], 'rolled-back')

    def test_prepared_operation_requires_recovery_and_can_restore(self):
        self.write('CR-0001'); before = O.snapshot(self.root)
        plan = P.plan(self.root)
        self.save('operations/interrupted.json', {'id': 'interrupted', 'status': 'prepared', 'before': before})
        for name, text in plan['writes'].items(): O.atomic(self.root / name, text)
        with self.assertRaisesRegex(ValueError, 'recovery'): P.plan(self.root)
        O.recover(self.root)
        self.assertEqual(O.snapshot(self.root), before)
        self.apply()

    def test_writer_lock_excludes_migration(self):
        self.write('CR-0001'); plan = P.plan(self.root)
        with O.writer_lock(self.root):
            with self.assertRaisesRegex(ValueError, 'Another console'): P.apply(self.root, plan['token'], 'Pat')

    def test_server_does_not_silently_hide_legacy_records_and_old_ingester_is_blocked(self):
        self.write('CR-0001')
        with patch.object(S, 'ENG', str(self.root)):
            with self.assertRaisesRegex(ValueError, 'migration'): S.load_registers()
            self.assertFalse(S.compatibility()['compatible'])
        self.apply()
        self.assertIn('Ingester model version: 2.30', (self.root / 'engagement.md').read_text())

    def test_legacy_and_new_import_ids_and_headers_map_to_cp(self):
        for term in ('Change request', 'Change proposal'):
            self.assertEqual(baseline.guess_kind(term), 'CP')
            self.assertIn('title', baseline.map_header(['Ref', term, 'Status']))
        for id in ('CR-0001', 'CP-0001'): self.assertEqual(baseline.ref_kind(id), 'CP')

    def test_phase_and_scope_saved_filter(self):
        rows = [dict(id='CP-0001', kind='CP', scope='EE', phase='P1'), dict(id='CP-0002', kind='CP', scope='EE', phase='P2')]
        self.assertEqual([i['id'] for i in views.apply_filter(rows, {'types': ['CP'], 'scopes': ['EE'], 'phases': ['P1']})], ['CP-0001'])
