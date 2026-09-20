"""Recoverable local writes. Journals stay with the private engagement, never in exports."""
import contextlib
import datetime
import hashlib
import json
import os
from pathlib import Path
import uuid


def atomic(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    with tmp.open('w', encoding='utf-8') as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def revision(item):
    return digest({k: v for k, v in item.items() if k != 'revision'})


def snapshot(eng):
    root = Path(eng)
    return {str(p.relative_to(root)): p.read_text(encoding='utf-8')
            for p in sorted(root.rglob('*')) if p.is_file()
            and p.suffix in ('.md', '.json', '.txt')
            and not any(x in p.relative_to(root).parts for x in
                        ('.git', 'operations', 'push', '.raw', 'anonymise', '__pycache__'))}


def restore(eng, target):
    current = snapshot(eng)
    for name in current.keys() - target.keys():
        (Path(eng) / name).unlink()
    for name, content in target.items():
        if current.get(name) != content:
            atomic(Path(eng) / name, content)


def records(eng):
    return [json.loads(p.read_text()) for p in sorted((Path(eng) / 'operations').glob('*.json'))]


def recover(eng):
    for op in records(eng):
        if op['status'] == 'prepared':
            restore(eng, op['before'])
            op['status'] = 'recovered'
            atomic(Path(eng) / 'operations' / (op['id'] + '.json'), json.dumps(op, indent=2))


@contextlib.contextmanager
def transaction(eng, action, req):
    before = snapshot(eng)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    op = {'id': now.replace(':', '-') + '-' + uuid.uuid4().hex[:8], 'at': now,
          'action': action, 'by': req.get('madeBy', ''), 'session': req.get('session', ''),
          'context': req.get('context', 'desktop'), 'status': 'prepared', 'before': before}
    path = Path(eng) / 'operations' / (op['id'] + '.json')
    atomic(path, json.dumps(op, indent=2))
    try:
        yield op
        after = snapshot(eng)
        changed = {name for name in before.keys() | after.keys() if before.get(name) != after.get(name)}
        op.update(status='applied' if changed else 'no-change', delta=True,
                  before={name: before[name] for name in changed if name in before},
                  after={name: after[name] for name in changed if name in after},
                  paths=sorted(changed), afterDigest=digest(after))
        atomic(path, json.dumps(op, indent=2))
    except Exception:
        restore(eng, before)
        op['status'] = 'rolled-back'
        atomic(path, json.dumps(op, indent=2))
        raise


def undo(eng, op_id):
    op = next((o for o in records(eng) if o['id'] == op_id), None)
    if not op or op['status'] != 'applied':
        raise ValueError('Choose an applied operation.')
    current = snapshot(eng)
    matches = digest(current) == op['afterDigest'] if op.get('delta') else current == op['after']
    if not matches:
        raise ValueError('The engagement changed since this operation. Undo newer changes first; external edits must be reconciled.')
    if op.get('delta'):
        for name in op['paths']:
            if name not in op['before']:
                path = Path(eng) / name
                if path.exists(): path.unlink()
            else:
                atomic(Path(eng) / name, op['before'][name])
    else:
        restore(eng, op['before'])
    return {'ok': True}


def summaries(eng):
    return [{k: o.get(k) for k in ('id', 'at', 'action', 'by', 'session', 'context', 'status')}
            for o in records(eng)][-50:]


def events(eng):
    """Structured change records derived from durable before/after operation snapshots."""
    out = []
    for op in records(eng):
        if op['status'] != 'applied': continue
        for name, text in op.get('after', {}).items():
            if text == op['before'].get(name) or not name.endswith('.md'): continue
            import re
            id = re.search(r'^id: (.+)$', text, re.M)
            if not id: continue
            previous = op['before'].get(name, '')
            old = re.search(r'^status: (.+)$', previous, re.M)
            new = re.search(r'^status: (.+)$', text, re.M)
            out.append({'operation': op['id'], 'item': id.group(1), 'date': op['at'][:10],
                        'context': 'rationalise' if '/reviews/apply' in op['action'] else op['context'],
                        'session': op['session'], 'history': [l[2:] for l in text.splitlines() if l.startswith('- ') and l not in previous.splitlines()], 'from': old.group(1) if old else '',
                        'to': new.group(1) if new else '', 'by': op['by']})
    return out
