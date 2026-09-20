import json
import tempfile
from pathlib import Path
import unittest
import server as S
import operations as O
import workspaces as W
import views as V
from tests.test_server_direct import write_item


class Workspaces(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.eng = self.tmp.name
        self.names = ['ENG', 'CS_DIR', 'B_DIR', 'DISMISSED_PATH', 'DUP_PATH', 'VIEWS_PATH']
        self.saved = {k:getattr(S,k) for k in self.names}
        S.ENG=self.eng
        for key,path in [('CS_DIR','change-sets'),('B_DIR','baseline'),('DISMISSED_PATH','supports-dismissed.json'),('DUP_PATH','duplicates-dismissed.json'),('VIEWS_PATH','views.json')]: setattr(S,key,str(Path(self.eng)/path))
        write_item(self.eng,'LIM-0001','Historical shortfall','Identified')
        write_item(self.eng,'REQ-0001','Historical requirement','Draft',moscow='Must')
        self.h=S.H.__new__(S.H)

    def tearDown(self):
        for k,v in self.saved.items():setattr(S,k,v)
        self.tmp.cleanup()

    def request(self,path,**req):
        req={'madeBy':'Reviewer',**req}
        with O.transaction(self.eng,path,req):return self.h.dispatch(path,req)

    def batch(self,category='reviews'):
        return self.request('/api/'+category+'/create',name='Current position',ids=['LIM-0001','REQ-0001'])

    def correction(self,b,**extra):
        entry={'outcome':'corrected','fields':{'status':'Accepted'},'reason':'Already accepted last month','evidence':'Minutes 7 August','effectiveOn':'7 August 2026',**extra}
        return self.request('/api/reviews/update',batch=b['id'],revision=b['revision'],id='LIM-0001',entry=entry)

    def test_correction_skips_historical_workflow_and_preserves_evidence(self):
        b=self.correction(self.batch())
        preview=self.h.dispatch('/api/reviews/preview',{'batch':b['id'],'revision':b['revision']})
        self.assertTrue(preview['changes'][0]['gaps'])
        self.request('/api/reviews/apply',batch=b['id'],revision=b['revision'])
        items=S.load_registers(); self.assertEqual(items['LIM-0001']['status'],'Accepted')
        self.assertFalse(any(i['kind']=='OI' for i in items.values()))
        self.assertIn('effective 7 August 2026',items['LIM-0001']['history'][-1])
        self.assertIn('Minutes 7 August',items['LIM-0001']['history'][-1])
        self.assertTrue(S.integrity_of(items)['failures'])
        events=O.events(self.eng);self.assertEqual(events[-1]['context'],'rationalise')

    def test_stale_item_is_rejected_without_writing(self):
        b=self.correction(self.batch())
        self.h.edit({'id':'LIM-0001','fields':{'Owner':'Someone else'},'madeBy':'Other'})
        with self.assertRaises(ValueError):self.request('/api/reviews/apply',batch=b['id'],revision=b['revision'])
        self.assertEqual(S.load_registers()['LIM-0001']['status'],'Identified')

    def test_generic_edit_cannot_bypass_workflow_and_can_clear(self):
        with self.assertRaises(ValueError):self.h.edit({'id':'LIM-0001','fields':{'Status':'Accepted'},'madeBy':'A'})
        self.h.edit({'id':'LIM-0001','fields':{'Owner':''},'madeBy':'A'})
        self.assertEqual(S.load_registers()['LIM-0001']['owner'],'')

    def test_revision_detects_same_day_edit(self):
        item=S.load_registers()['LIM-0001']; rev=O.revision(item)
        self.h.edit({'id':item['id'],'fields':{'Owner':'Other'},'madeBy':'A'})
        with self.assertRaises(ValueError):S.check_revisions({'revisions':{item['id']:rev}})

    def test_sessions_work_in_change_sets_mode_without_compatible_ingester(self):
        Path(self.eng,'engagement.md').write_text('- Writes: change-sets\n- Ingester model version: 2.20\n')
        b=self.correction(self.batch()); m=self.batch('meetings')
        self.assertEqual(m['status'],'open')
        self.request('/api/views',views=V.default_views())
        with self.assertRaises(ValueError):self.request('/api/reviews/apply',batch=b['id'],revision=b['revision'])
        with self.assertRaises(ValueError):self.h.edit({'id':'LIM-0001','fields':{'Owner':'A'},'madeBy':'A'})

    def test_meeting_agenda_survives_status_changes_and_reorders(self):
        m=self.batch('meetings')
        self.h.edit({'id':'REQ-0001','fields':{'Title':'New title'},'madeBy':'A'})
        m=self.request('/api/meetings/update',batch=m['id'],revision=m['revision'],order=list(reversed(m['ids'])))
        self.assertEqual(m['snapshot']['REQ-0001']['title'],'Historical requirement')
        m=self.request('/api/meetings/update',batch=m['id'],revision=m['revision'],id='REQ-0001',entry={'status':'discussed','outcome':'Agreed next steps','action':'Confirm scope','owner':'A'})
        self.assertIn('Agreed next steps',W.summary(m,'meetings'))
        self.assertEqual(len(m['ids']),2)

    def test_follow_up_is_atomic_and_cannot_be_duplicated(self):
        m=self.batch('meetings');req=dict(batch=m['id'],revision=m['revision'],id='REQ-0001',entry={'status':'discussed','outcome':'Needs work','action':'Confirm','owner':'A'})
        result=self.request('/api/meetings/action',**req)
        self.assertTrue(result['entries']['REQ-0001']['actionItem'].startswith('OI-'))
        with self.assertRaises(ValueError):self.request('/api/meetings/action',**req)
        self.assertEqual(len([i for i in S.load_registers() if i.startswith('OI-')]),1)

    def test_retype_preserves_alias_and_rewrites_incoming_links(self):
        write_item(self.eng,'OI-0001','Assess','Open',links=['resolves into LIM-0001'])
        b=self.correction(self.batch(),outcome='retyped',kind='DEC',fields={'title':'Historical choice','status':'Accepted'})
        self.request('/api/reviews/apply',batch=b['id'],revision=b['revision'])
        items=S.load_registers();self.assertNotIn('LIM-0001',items)
        target=S.aliases()['LIM-0001']['targets'][0];self.assertIn(target,items)
        self.assertIn('resolves into '+target,items['OI-0001']['links'])

    def test_split_keeps_original_and_provenance(self):
        b=self.correction(self.batch(),outcome='split',fields={},children=[{'kind':'REQ','fields':{'title':'Part A'}},{'kind':'REQ','fields':{'title':'Part B'}}])
        self.request('/api/reviews/apply',batch=b['id'],revision=b['revision'])
        items=S.load_registers();self.assertIn('Split into:',items['LIM-0001']['notes'])
        self.assertIn('Derived from LIM-0001',items['REQ-0002']['source'])

    def test_unresolved_review_cannot_close(self):
        b=self.batch()
        with self.assertRaises(ValueError):self.request('/api/reviews/update',batch=b['id'],revision=b['revision'],close=True)

    def test_journal_rolls_back_exception_and_undo_refuses_external_changes(self):
        before=O.snapshot(self.eng)
        with self.assertRaises(RuntimeError):
            with O.transaction(self.eng,'test',{'madeBy':'A'}):
                self.h.edit({'id':'LIM-0001','fields':{'Owner':'B'},'madeBy':'A'})
                raise RuntimeError('disk failure')
        self.assertEqual(O.snapshot(self.eng),before)
        self.request('/api/edit',id='LIM-0001',fields={'Owner':'B'})
        op=O.records(self.eng)[-1]
        O.undo(self.eng,op['id']);self.assertEqual(O.snapshot(self.eng),before)
        Path(self.eng,'engagement.md').write_text('External change')
        with self.assertRaises(ValueError):O.undo(self.eng,op['id'])

    def test_prepared_journal_is_recovered_on_start(self):
        before=O.snapshot(self.eng)
        O.atomic(Path(self.eng,'operations','interrupted.json'),json.dumps({'id':'interrupted','status':'prepared','before':before}))
        self.h.edit({'id':'LIM-0001','fields':{'Owner':'B'},'madeBy':'A'})
        O.recover(self.eng);self.assertEqual(O.snapshot(self.eng),before)

    def test_report_search_rule_and_gaps_share_scope(self):
        items=list(S.load_registers().values());integ={'failures':[{'id':'LIM-0001','rule':'I3'},{'id':'REQ-0001','rule':'I2'}]}
        view=V.default_views()[0];view['filter'].update(q='shortfall',rule='I3')
        r=V.sections(view,items,integ,S.today())
        self.assertEqual([i['id'] for i in r['table']],['LIM-0001']);self.assertEqual(r['gaps'],[{'id':'LIM-0001','rule':'I3'}])

    def test_import_creates_registers_and_review_without_freeze_workspace(self):
        import shutil
        for folder in S.M.DIRS.values():
            path=Path(self.eng,folder)
            if path.exists():shutil.rmtree(path)
        Path(S.B_DIR).mkdir()
        Path(S.B_DIR,'Requirements.md').write_text('# Requirements\n\n| ID | Title | Status |\n|---|---|---|\n| REQ-8 | A generated requirement | Agreed |\n')
        result=self.request('/api/import')
        self.assertEqual(result['written'],1)
        self.assertEqual(len(W.load(self.eng,'reviews')),1)
        self.assertEqual(S.load_registers()['REQ-0001']['status'],'Agreed')
        with self.assertRaises(ValueError):self.request('/api/import')

    def test_closed_confirmation_refuses_changed_item(self):
        b=self.batch()
        for id in b['ids']:
            b=self.request('/api/reviews/update',batch=b['id'],revision=b['revision'],id=id,entry={'outcome':'confirmed','reason':'Checked source'})
        self.h.edit({'id':'REQ-0001','fields':{'Owner':'Changed'},'madeBy':'A'})
        with self.assertRaises(ValueError):self.request('/api/reviews/update',batch=b['id'],revision=b['revision'],close=True)

    def test_merge_preview_requires_resolutions_and_alias_ids_are_reserved(self):
        write_item(self.eng,'REQ-0002','Conflicting title','Agreed',moscow='Should')
        preview=S.merge_preview({'survivor':'REQ-0001','losers':['REQ-0002']})
        self.assertIn('title',preview['conflicts'])
        with self.assertRaises(ValueError):self.h.merge({'survivor':'REQ-0001','losers':['REQ-0002'],'madeBy':'A'})
        resolutions={k:vs[0] for k,vs in preview['conflicts'].items()}
        self.request('/api/merge',survivor='REQ-0001',losers=['REQ-0002'],resolutions=resolutions)
        self.assertEqual(S.aliases()['REQ-0002']['targets'],['REQ-0001'])
        created=self.h.create({'kind':'REQ','fields':{'Title':'New','Owner':'A','MoSCoW':'Must','Implemented by':'Internal','Source':'test'},'madeBy':'A'})
        self.assertEqual(created['item'],'REQ-0003')

    def test_completed_journal_only_retains_changed_files(self):
        self.request('/api/edit',id='LIM-0001',fields={'Owner':'B'})
        op=O.records(self.eng)[-1]
        self.assertEqual(op['paths'],['limitations/LIM-0001.md'])
        self.assertEqual(len(op['before']),1)
        O.undo(self.eng,op['id']);self.assertEqual(S.load_registers()['LIM-0001']['owner'],'Priya Nair')

    def test_unreviewed_count_tracks_actual_review_batches(self):
        b=self.batch();self.assertEqual(len(S.state()['unreviewed']),2)
        self.request('/api/reviews/update',batch=b['id'],revision=b['revision'],id='REQ-0001',entry={'outcome':'confirmed','reason':'Checked'})
        self.assertEqual(S.state()['unreviewed'],['LIM-0001'])
        self.h.edit({'id':'REQ-0001','fields':{'Owner':'Changed'},'madeBy':'A'})
        self.assertEqual(len(S.state()['unreviewed']),2)
