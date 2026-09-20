"""Deterministic previews for register restructuring and persistent deleted-item storage."""
import json
from pathlib import Path
import re
import model as M
import operations as O


def fields(kind):
    return list(dict.fromkeys(['title', 'status', 'description', 'raised-on', 'closed-on'] + M.SHORT[kind] + M.LONG[kind]))


def bin_load(eng):
    path = Path(eng) / 'rubbish-bin.json'
    return json.loads(path.read_text()) if path.exists() else []


def bin_save(eng, entries):
    O.atomic(Path(eng) / 'rubbish-bin.json', json.dumps(entries, indent=2))


def archive(eng, item, items, req, date):
    entries = bin_load(eng)
    pat = re.compile(r'\b' + re.escape(item['id']) + r'\b')
    incoming = {id: [l for l in it['links'] if pat.search(l)] for id, it in items.items() if id != item['id']}
    entry = {'key': str(len(entries) + 1), 'item': item, 'deletedOn': date, 'by': req['madeBy'],
             'reason': req['reason'], 'incoming': {id: links for id, links in incoming.items() if links}, 'restored': False}
    entries.append(entry)
    bin_save(eng, entries)


def retype(items, aliases, ids, kind, status=None):
    if kind not in M.DIRS: raise ValueError('Choose an item type.')
    if not ids or len(ids) != len(set(ids)) or any(id not in items for id in ids):
        raise ValueError('Choose distinct existing records.')
    if any(items[id]['kind'] == kind for id in ids): raise ValueError('Choose a different type for every selected record.')
    if status is not None and status not in M.STATES[kind]: raise ValueError('Choose a valid status for the new type.')
    taken = [int(id.split('-')[1]) for id in set(items) | set(aliases) if re.fullmatch(kind + r'-\d+', id)]
    next_id = max(taken + [0]) + 1
    changes = []
    for n, id in enumerate(ids):
        old = items[id]
        new = {k: old.get(k, '') for k in fields(kind)}
        new.update(id=f'{kind}-{next_id+n:04d}', kind=kind, links=list(old['links']), history=list(old.get('history', [])))
        new['status'] = status or (old['status'] if old['status'] in M.STATES[kind] else M.FIRST_STATE[kind])
        preserved = []
        for key in fields(old['kind']):
            value = old.get(key, '')
            invalid_choice = key in M.CHOICES and value and value not in M.CHOICES[key] and not (key == 'impact' and kind != 'RSK')
            if key not in fields(kind) or invalid_choice:
                if value: preserved.append(f'{M.LABELS.get(key, key)}: {value}')
                if invalid_choice: new[key] = ''
        if old['status'] != new['status']: preserved.append('Previous status: ' + old['status'])
        new['notes'] = '\n'.join(filter(None, [new.get('notes'), 'Retyped from ' + id, *preserved]))
        changes.append({'before': old, 'after': new})
    mapping = {c['before']['id']: c['after']['id'] for c in changes}
    for change in changes:
        change['after']['links'] = [re.sub(r'\b[A-Z]+-\d+\b', lambda m: mapping.get(m[0], m[0]), l) for l in change['after']['links']]
    return changes


def merge(items, lead, ids):
    if len(ids) < 2 or len(ids) != len(set(ids)) or lead not in ids or any(id not in items for id in ids):
        raise ValueError('Select at least two records and choose their lead.')
    rows = [items[lead]] + [items[id] for id in ids if id != lead]
    if any(row['kind'] != rows[0]['kind'] for row in rows): raise ValueError('Merge records of one type; change types first if needed.')
    after = {**rows[0], 'links': list(rows[0]['links'])}
    keys = fields(after['kind'])
    notes = [after.get('notes', '')]
    sources = [after.get('source', '')]
    for row in rows[1:]:
        preserved = []
        for key in keys:
            if key in ('notes', 'source'): continue
            value = row.get(key, '')
            if not str(after.get(key, '')).strip(): after[key] = value
            elif value and value != after.get(key): preserved.append(f'{M.LABELS.get(key, key)}: {value}')
        notes.append('\n'.join(filter(None, ['Merged from ' + row['id'], *preserved, row.get('notes'),
                                            'Previous history:\n' + '\n'.join(row['history']) if row.get('history') else ''])))
        sources.append(row.get('source', ''))
        after['links'].extend(row['links'])
    after['source'] = '\n'.join(dict.fromkeys(s for src in sources for s in src.splitlines() if s.strip()))
    after['notes'] = '\n\n'.join(n for n in notes if n)
    internal = re.compile(r'\b(?:' + '|'.join(map(re.escape, ids)) + r')\b')
    after['links'] = list(dict.fromkeys(l for l in after['links'] if not internal.search(l)))
    return {'before': rows, 'after': after}
