"""Preview and migrate internal CR records to CP, without changing vendor references.

Run with the console and ingester stopped. Default is read-only; --apply requires
an unchanged preview token and a named operator. Writes use the recovery journal.
"""
import argparse
import copy
import json
import os
import re
from pathlib import Path

import items
import model as M
import operations as O

LEGACY = re.compile(r'CR-\d+')
TOKEN = re.compile(r'\bCR-\d+\b')
LINK_TARGET = re.compile(r'^(\s*(?:' + '|'.join(re.escape(w) for w in sorted(
    {word for words in M.LINK_WORDS.values() for word in words}, key=len, reverse=True)) + r')\s+)(CR-\d+)(?=\s|$)')
METADATA = ('views.json', 'reviews.json', 'meetings.json', 'rubbish-bin.json',
            'supports-dismissed.json', 'duplicates-dismissed.json', 'baseline/verdicts.json')
# Narrative is evidence, not an ID namespace. Never rewrite a vendor number in it.
EVIDENCE = {'vendor-ref', 'vendor ref', 'source', 'ref', 'history', 'notes', 'reason',
            'rationale', 'evidence', 'title', 'description', 'name', 'text', 'outcome',
            'next action', 'estimate', 'source_status', 'source_ref'}


def json_file(root, name, default):
    path = root / name
    return json.loads(path.read_text()) if path.exists() else default


def require_migrated(engagement, include_bin=True):
    root = Path(engagement)
    if any((root / 'change-requests').glob('*.md')) or (include_bin and any(
            entry.get('item', {}).get('kind') == 'CR' for entry in json_file(root, 'rubbish-bin.json', []))):
        raise ValueError('Legacy internal CR records need migration. Stop the console and run make proposal-check, then make proposal-migrate; see docs/change-proposal-upgrade.md.')


def rewrite_link(value, mapping):
    # Only the internal relationship target is ours. URLs and vendor/narrative text stay intact.
    if value.strip() in mapping:
        return value.replace(value.strip(), mapping[value.strip()], 1)
    return LINK_TARGET.sub(lambda m: m[1] + mapping.get(m[2], m[2]), value, count=1)


def rewrite(value, mapping, field=''):
    """Rewrite structured identities and typed links, preserving narrative verbatim."""
    if field.lower() in EVIDENCE:
        return copy.deepcopy(value)
    if isinstance(value, dict):
        out = {}
        for key, val in value.items():
            new_key = mapping.get(key, 'CP' if key == 'CR' and field == 'counts' else key)
            if new_key in out:
                raise ValueError('Metadata key collision: ' + new_key)
            out[new_key] = rewrite(val, mapping, 'links' if field == 'incoming' else key)
        return out
    if isinstance(value, list):
        return [rewrite(v, mapping, field) for v in value]
    if isinstance(value, str):
        if field in ('kind', 'types') and value == 'CR': return 'CP'
        if field.lower() == 'links': return rewrite_link(value, mapping)
        return mapping.get(value, value)
    return value


def owned_ids(value, field=''):
    if field.lower() in EVIDENCE: return set()
    if isinstance(value, dict):
        return {k for k in value if LEGACY.fullmatch(k)} | set().union(*(owned_ids(v, k) for k, v in value.items()), set())
    if isinstance(value, list): return set().union(*(owned_ids(v, field) for v in value), set())
    if isinstance(value, str) and field in ('id', 'ids', 'item', 'targets', 'survivor', 'pendingSources') and LEGACY.fullmatch(value):
        return {value}
    return set()


def rewrite_item(text, mapping):
    """Change only the frontmatter identity and structured Links; retain all other bytes."""
    lines = text.splitlines(keepends=True)
    front, links = False, False
    for n, line in enumerate(lines):
        if line.rstrip('\r\n') == '---':
            if front: break
            if n == 0: front = True
            continue
        if not front: continue
        if line.startswith('id: '):
            lines[n] = TOKEN.sub(lambda m: mapping.get(m[0], m[0]), line)
        elif line.startswith('links:'):
            links = True
            lines[n] = 'links:' + rewrite_link(line[6:], mapping)
        elif links and line.startswith('  - '):
            lines[n] = '  - ' + rewrite_link(line[4:], mapping)
        elif line.strip():
            links = False
    return ''.join(lines)


def rewrite_frozen(text, mapping):
    lines = []
    implied = False
    for line in text.splitlines(keepends=True):
        if line.startswith('## '): implied = line.startswith('## Implied at baseline')
        if line.startswith('- Items by type:'): line = line.replace('CR=', 'CP=')
        if line.startswith('|'):
            cells = line.split('|')
            # Source-id column is evidence. Only the destination is ours.
            columns = (1, 3) if implied else (2,)
            for col in columns:
                if col < len(cells): cells[col] = TOKEN.sub(lambda m: mapping.get(m[0], m[0]), cells[col])
            line = '|'.join(cells)
        lines.append(line)
    return ''.join(lines)


def plan(engagement):
    root = Path(engagement)
    if not (root / 'engagement.md').is_file(): raise ValueError('Expected an engagement folder containing engagement.md')
    if any(p.is_symlink() for p in root.rglob('*') if '.git' not in p.relative_to(root).parts):
        raise ValueError('Resolve engagement symlinks before migrating; migration must stay inside the engagement.')
    for path in (root / 'change-sets').glob('CS-*.md'):
        if not re.search(r'^- Applied on:\s*\S', path.read_text(), re.M):
            raise ValueError('Resolve unapplied change sets with the existing ingester before migrating: ' + path.name)
    if any(op['status'] == 'prepared' for op in O.records(root)):
        raise ValueError('An interrupted operation needs recovery. Run --recover with writers stopped, then preview again.')
    before = O.snapshot(root)
    records, paths = {}, {}
    dirs = {**M.DIRS, 'CR': 'change-requests'}
    for kind, folder in dirs.items():
        for path in sorted((root / folder).glob('*.md')):
            item = items.parse_item(path)
            if item['kind'] != kind or path.stem != item['id'] or item['id'] in records:
                raise ValueError('Invalid, duplicate or mismatched ID: ' + str(path.relative_to(root)))
            expected = 'CP' if kind == 'CR' else kind
            if item['status'] not in M.STATES[expected]: raise ValueError('Unrecognised status on ' + item['id'])
            records[item['id']] = item
            paths[item['id']] = str(path.relative_to(root))
    meta = {name: json_file(root, name, None) for name in METADATA if (root / name).exists()}
    aliases = json_file(root, 'aliases.json', {})
    legacy = {id for id in records if LEGACY.fullmatch(id)} | {id for id, value in aliases.items() if LEGACY.fullmatch(id) and value.get('reason') != 'Internal Change request migrated to Change proposal'}
    for value in meta.values(): legacy |= owned_ids(value)
    mapping = {id: 'CP-' + id[3:] for id in sorted(legacy)}
    # Existing canonical records, bin IDs and alias reservations must never be overwritten.
    canonical = set(records) | set(aliases)
    for entry in meta.get('rubbish-bin.json', []): canonical.add(entry['item']['id'])
    for old, new in mapping.items():
        if new in canonical or (root / 'change-proposals' / (new + '.md')).exists():
            raise ValueError(f'ID collision: {old} would become existing/reserved {new}. Resolve explicitly before migrating.')
        if old in records and aliases.get(old, {}).get('targets'):
            raise ValueError('Active item also redirects: ' + old)
    writes, deletes = {}, []
    for id, path in paths.items():
        text = rewrite_item(before[path], mapping)
        dest = 'change-proposals/' + mapping[id] + '.md' if id in mapping else path
        if dest != path: deletes.append(path)
        if dest != path or text != before[path]: writes[dest] = text
    for name, value in meta.items():
        migrated = rewrite(value, mapping)
        if name in ('reviews.json', 'meetings.json') and migrated != value:
            for record in migrated:
                # Keep basedOn/survivorRevision stale: old review approval must not be silently renewed.
                record['revision'] = O.revision(record)
        if migrated != value: writes[name] = json.dumps(migrated, indent=2, ensure_ascii=False) + '\n'
    migrated_aliases = {}
    for old, value in aliases.items():
        migrated_aliases[mapping.get(old, old)] = rewrite(value, mapping)
    for old, new in mapping.items():
        if old not in records and old not in aliases:
            migrated_aliases[new] = {'targets': [], 'reason': 'Reserved historical proposal ID'}
        migrated_aliases[old] = {'targets': [new], 'reason': 'Internal Change request migrated to Change proposal'}
    if migrated_aliases != aliases: writes['aliases.json'] = json.dumps(migrated_aliases, indent=2, ensure_ascii=False) + '\n'
    if 'baseline/frozen.md' in before:
        text = rewrite_frozen(before['baseline/frozen.md'], mapping)
        if text != before['baseline/frozen.md']: writes['baseline/frozen.md'] = text
    return {'mapping': mapping, 'writes': writes, 'deletes': deletes,
            'token': O.digest({'version': M.MODEL_VERSION, 'before': before, 'mapping': mapping, 'writes': writes, 'deletes': deletes}),
            'records': len(records), 'legacyRecords': sum(id.startswith('CR-') for id in records)}


def apply(engagement, expected, made_by):
    if not made_by.strip(): raise ValueError('Set Made by for the migration history.')
    with O.writer_lock(engagement):
        result = plan(engagement)
        if not expected or result['token'] != expected: raise ValueError('The preview is stale. Run proposal-check again and use its token.')
        if not result['writes'] and not result['deletes']: return result
        with O.transaction(engagement, 'migration/CR-to-CP', {'madeBy': made_by, 'context': 'rationalise'}) as operation:
            for name, text in result['writes'].items(): O.atomic(Path(engagement) / name, text)
            for name in result['deletes']: (Path(engagement) / name).unlink()
            operation['mapping'] = result['mapping']
        return result


def report(result, applied=False):
    lines = ['Internal Change request → Change proposal migration (model ' + M.MODEL_VERSION + ')',
             'Vendor refs, narrative, source evidence and original history are preserved.',
             f"{result['legacyRecords']} active CR records; {len(result['mapping'])} internal IDs to migrate."]
    lines += [old + ' → ' + new for old, new in result['mapping'].items()]
    lines += [('Wrote: ' if applied else 'Write: ') + name for name in sorted(result['writes'])]
    lines += [('Removed old path: ' if applied else 'Remove old path: ') + name for name in result['deletes']]
    if not applied:
        lines += ['Preview token: ' + result['token'],
                  'Apply with proposal-migrate using this EXPECT token and MADE_BY. Stop console and ingester first.']
    else:
        lines += ['Migration complete. Run proposal-check again; it should show no changes.']
    lines += ['Existing review approvals become stale where identities change; reconfirm before applying reviews.',
              'Old internal CR URLs resolve through aliases. Vendor request references are not renamed.']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('engagement')
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--expect', default=os.environ.get('EXPECT', ''))
    parser.add_argument('--made-by', default=os.environ.get('MADE_BY', ''))
    parser.add_argument('--recover', action='store_true')
    args = parser.parse_args()
    try:
        if args.recover:
            if args.apply: raise ValueError('Recover first, then preview and apply separately.')
            with O.writer_lock(args.engagement): O.recover(args.engagement)
        result = apply(args.engagement, args.expect, args.made_by) if args.apply else plan(args.engagement)
        print(('Applied.\n' if args.apply else 'PREVIEW ONLY: no records migrated.\n') + report(result, applied=args.apply))
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(1, 'Migration refused: ' + str(exc) + '\n')


if __name__ == '__main__': main()
