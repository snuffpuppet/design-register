"""Review batches and meeting sessions, independent of register lifecycle and write mode."""
import copy
import json
from pathlib import Path
import re
import uuid
import model as M
import operations as O

OUTCOMES = M.REVIEW_OUTCOMES


def load(eng, category):
    path = Path(eng) / (category + '.json')
    return json.loads(path.read_text()) if path.exists() else []


def save(eng, category, records):
    O.atomic(Path(eng) / (category + '.json'), json.dumps(records, indent=2, ensure_ascii=False))


def find(records, id):
    row = next((r for r in records if r['id'] == id), None)
    if row is None:
        raise ValueError('No such session or review batch.')
    return row


def maker(req):
    if not str(req.get('madeBy', '')).strip():
        raise ValueError('Set Made by first.')
    return req['madeBy'].strip()


def create(eng, category, req, items, today):
    who = maker(req)
    ids = list(dict.fromkeys(req.get('ids', [])))
    if not ids or any(id not in items for id in ids):
        raise ValueError('Select existing items for the agenda or review.')
    if not req.get('name', '').strip():
        raise ValueError('Give this session a name.')
    prefix = 'REV' if category == 'reviews' else 'MTG'
    record = {'id': prefix + '-' + uuid.uuid4().hex[:12], 'name': req['name'].strip(),
              'created': today, 'by': who, 'status': 'open', 'ids': ids,
              'snapshot': {id: copy.deepcopy(items[id]) for id in ids}, 'entries': {}}
    record['revision'] = O.revision(record)
    records = load(eng, category)
    records.append(record)
    save(eng, category, records)
    return record


def update(eng, category, req, items, today):
    who = maker(req)
    records = load(eng, category)
    record = find(records, req['batch'])
    if record['status'] != 'open':
        raise ValueError('This session is closed.')
    if req.get('revision') != record['revision']:
        raise ValueError('The session changed. Reload before saving.')
    if req.get('order') is not None:
        order = req['order']
        if len(order) != len(record['ids']) or set(order) != set(record['ids']):
            raise ValueError('Agenda order must contain every agenda item exactly once.')
        record['ids'] = order
    elif req.get('close'):
        if category == 'reviews' and any(id not in record['entries'] or
                record['entries'][id].get('outcome') == 'needs clarification' or
                (record['entries'][id].get('outcome') in ('corrected', 'merged', 'excluded', 'retyped', 'split')
                 and not record['entries'][id].get('applied')) for id in record['ids']):
            raise ValueError('Resolve outstanding entries and apply proposals before completing this review.')
        if category == 'reviews':
            for id, e in record['entries'].items():
                if e.get('outcome') == 'confirmed' and (id not in items or e.get('basedOn') != O.revision(items[id])):
                    raise ValueError(f'{id} changed after confirmation. Review it again before completing.')
        record.update(status='closed', closed=today)
    else:
        id = req.get('id')
        if id not in record['ids']:
            raise ValueError('Item is not in this session.')
        entry = copy.deepcopy(req.get('entry', {}))
        if category == 'reviews':
            if entry.get('outcome') not in OUTCOMES:
                raise ValueError('Choose a review outcome.')
            if not entry.get('reason', '').strip():
                raise ValueError('Record why this is the correct position.')
            if entry['outcome'] in ('corrected', 'retyped', 'split', 'merged') and not entry.get('evidence', '').strip():
                raise ValueError('Historical corrections need evidence, or use Needs clarification.')
            if id not in items:
                raise ValueError('The item no longer exists. Reload the session.')
            entry['basedOn'] = O.revision(items[id])
            entry['before'] = copy.deepcopy(items[id])
            entry['applied'] = False
            if entry['outcome'] == 'merged' and entry.get('survivor') in items:
                entry['survivorRevision'] = O.revision(items[entry['survivor']])
        else:
            if entry.get('status') not in ('discussed', 'deferred', 'not discussed'):
                raise ValueError('Choose discussion progress.')
            if entry.get('status') == 'discussed' and not entry.get('outcome', '').strip():
                raise ValueError('Record the discussion outcome.')
        entry.update(by=who, on=today)
        record['entries'][id] = entry
    record['revision'] = O.revision(record)
    save(eng, category, records)
    return record


def check_entry(id, entry, items, validate):
    if id not in items or entry.get('basedOn') != O.revision(items[id]):
        raise ValueError(f'{id} changed after review. Review it again before applying.')
    kind = entry.get('kind') or items[id]['kind']
    if kind not in M.DIRS:
        raise ValueError('Unknown item type.')
    fields = validate(kind, entry.get('fields', {}), correction=True)
    if 'status' in fields and fields['status'] not in M.STATES[kind]:
        raise ValueError('Choose a valid status for this type.')
    links = entry.get('links', items[id]['links'])
    if not isinstance(links, list) or any(not isinstance(l, str) for l in links):
        raise ValueError('Links must be a list of text entries.')
    if entry['outcome'] == 'retyped' and kind == items[id]['kind']:
        raise ValueError('Choose a different type.')
    if entry['outcome'] == 'merged':
        target = items.get(entry.get('survivor'))
        if not target or target['kind'] != items[id]['kind'] or target['id'] == id:
            raise ValueError('Choose an existing survivor of the same type.')
        if entry.get('survivorRevision') != O.revision(target):
            raise ValueError('The merge survivor changed. Compare and save the review again.')
    if entry['outcome'] == 'split':
        children = entry.get('children', [])
        if len(children) < 2:
            raise ValueError('A split needs at least two new records.')
        for child in children:
            ck = child.get('kind', kind)
            if ck not in M.DIRS:
                raise ValueError('Unknown child type.')
            cf = validate(ck, child.get('fields', {}), correction=True)
            if not cf.get('title', '').strip() or cf.get('status', M.FIRST_STATE[ck]) not in M.STATES[ck]:
                raise ValueError('Every split record needs a title and valid status.')
    if entry['outcome'] == 'merged':
        resolutions = validate(kind, entry.get('resolutions', {}), correction=True)
        keys = ['title', 'status', 'description'] + M.SHORT[kind] + [k for k in M.LONG[kind] if k not in ('source', 'notes')]
        conflicts = [k for k in keys if items[id].get(k) and target.get(k) and items[id][k] != target[k]]
        if any(k not in resolutions for k in conflicts):
            raise ValueError('Resolve all merge conflicts: ' + ', '.join(conflicts))
    return kind, fields, links


def preview(eng, req, items, validate):
    record = find(load(eng, 'reviews'), req['batch'])
    if record['status'] != 'open' or req.get('revision') != record['revision']:
        raise ValueError('Review changed or completed. Reload before applying.')
    changes, errors = [], []
    for id in record['ids']:
        entry = record['entries'].get(id, {})
        if entry.get('outcome') not in ('corrected', 'merged', 'excluded', 'retyped', 'split') or entry.get('applied'):
            continue
        try:
            kind, fields, links = check_entry(id, entry, items, validate)
            current = items[id]
            after = {**current, **fields, 'kind': kind, 'links': links}
            if kind != current['kind'] and 'status' not in fields:
                after['status'] = M.FIRST_STATE[kind]
            changes.append({'id': id, 'outcome': entry['outcome'], 'before': current, 'after': after,
                            'survivor': entry.get('survivor'), 'resolutions': entry.get('resolutions'), 'children': entry.get('children'),
                            'gaps': M.missing_for(kind, after['status'], after)})
        except ValueError as e:
            errors.append({'id': id, 'error': str(e)})
    # Structural operations cannot consume a survivor elsewhere in the same batch.
    consumed = {c['id'] for c in changes if c['outcome'] in ('merged', 'excluded', 'retyped', 'split')}
    for c in changes:
        if c['outcome'] == 'merged' and record['entries'][c['id']].get('survivor') in consumed:
            errors.append({'id': c['id'], 'error': 'The survivor is also being removed or retyped. Apply that merge separately.'})
    return {'changes': changes, 'errors': errors, 'revision': record['revision']}


def summary(record, category):
    lines = [f"# {record['name']}", '', f"Reference: {record['id']}", f"Created: {record['created']} by {record['by']}", '']
    for id in record['ids']:
        it = record['snapshot'][id]
        e = record['entries'].get(id, {})
        lines += [f"## {id}: {it['title']}", '', f"Progress: {e.get('status', e.get('outcome', 'unreviewed'))}",
                  e.get('outcome', ''), e.get('reason', ''), f"Evidence: {e.get('evidence', '')}"]
        if category == 'meetings':
            lines += [f"Follow-up: {e.get('action', '')}", f"Owner: {e.get('owner', '')}", f"Due: {e.get('due', '')}",
                      f"Register references: {e.get('references', '')}"]
        lines.append('')
    return '\n'.join(lines)
