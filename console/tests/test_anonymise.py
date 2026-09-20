import json
from pathlib import Path
import tempfile
import unittest
import anonymise as A
import baseline as B
import operations as O

class Anonymise(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.src=self.root/'private';self.src.mkdir()
        self.glossary=self.root/'glossary.json'
        self.glossary.write_text(json.dumps({'replacements':{'Example Client':'Puppy Gloves','Alice Example':'Priya Sample','Private Product':'Wool Loom'}}))
        (self.src/'engagement.md').write_text('# Engagement: Example Client\n- Writes: direct\n')
        (self.src/'requirements').mkdir()
        (self.src/'requirements'/'REQ-0001.md').write_text('---\nid: REQ-0001\ntitle: Private Product for Example Client\nowner: Alice Example\nstatus: Draft\n---\n## Source\nhttps://private.example.com/docs\nalice@private.example.com\n')
        (self.src/'operations').mkdir();(self.src/'operations'/'private.json').write_text('{"secret":"Do not export"}')
        (self.src/'baseline').mkdir();(self.src/'baseline'/'Example Client.md').write_text('# Example Client\n\n## Requirements\n\n| ID | Title | Status |\n|---|---|---|\n| REQ-1 | Private Product for Example Client | Draft |\n')

    def tearDown(self):self.tmp.cleanup()

    def test_exports_are_byte_identical_and_do_not_copy_journal(self):
        one,two=self.root/'one',self.root/'two'
        A.export(self.src,one,self.glossary);A.export(self.src,two,self.glossary)
        def tree(p):return {str(f.relative_to(p)):f.read_bytes() for f in p.rglob('*') if f.is_file()}
        self.assertEqual(tree(one),tree(two));self.assertFalse((one/'operations').exists())
        text=(one/'requirements'/'REQ-0001.md').read_text()
        self.assertNotIn('Private Product',text);self.assertIn('Wool Loom',text);self.assertNotIn('private.example.com',text)
        self.assertIn('id: REQ-0001',text)

    def test_rekeys_baseline_verdicts(self):
        c=B.load_candidates(self.src/'baseline')[0]
        (self.src/'baseline'/'verdicts.json').write_text(json.dumps({c['id']:{'verdict':'Accept','frozenAs':'REQ-0001'}}))
        dest=self.root/'out';A.export(self.src,dest,self.glossary)
        new=B.load_candidates(dest/'baseline')[0]
        verdicts=json.loads((dest/'baseline'/'verdicts.json').read_text())
        self.assertNotEqual(c['id'],new['id']);self.assertEqual(verdicts[new['id']]['frozenAs'],'REQ-0001')

    def test_refuses_existing_destination_and_leaves_it_untouched(self):
        dest=self.root/'out';dest.mkdir();(dest/'keep').write_text('keep')
        with self.assertRaises(ValueError):A.export(self.src,dest,self.glossary)
        self.assertEqual((dest/'keep').read_text(),'keep')

    def test_forbidden_term_refuses_and_publishes_nothing(self):
        conf=json.loads(self.glossary.read_text());conf['forbidden']=['Wool Loom'];self.glossary.write_text(json.dumps(conf))
        with self.assertRaises(ValueError):A.export(self.src,self.root/'out',self.glossary)
        self.assertFalse((self.root/'out').exists())

    def test_replacements_do_not_cascade(self):
        replace=A.transformer({'Original':'Middle','Middle':'Final'})
        self.assertEqual(replace('Original and Middle'),'Middle and Final')
