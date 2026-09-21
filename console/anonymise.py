#!/usr/bin/env python3
"""Deterministic shareable fixtures. Run in Docker on the work laptop with a private glossary."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
import baseline as B
import model as M
import operations as O

ROOT_FILES = {'engagement.md', 'views.json', 'reviews.json', 'meetings.json', 'aliases.json',
              'supports-dismissed.json', 'duplicates-dismissed.json', 'renumbered.md'}
DIRECTORIES = set(M.DIRS.values()) | {'stakeholders', 'baseline', 'change-sets'}
EXCLUDED = {'.raw', 'push', 'operations', 'anonymise', '.git', '__pycache__'}


def transformer(mapping):
    if not isinstance(mapping, dict) or not mapping:
        raise ValueError('Glossary must contain a non-empty replacements object.')
    if any(not isinstance(k, str) or not k or not isinstance(v, str) or not v for k, v in mapping.items()):
        raise ValueError('Every replacement must have non-empty source and replacement text.')
    folded = {k.casefold(): v for k, v in mapping.items()}
    if len(folded) != len(mapping):
        raise ValueError('Glossary has case-insensitive duplicate source terms.')
    pattern = re.compile('|'.join(re.escape(k) for k in sorted(mapping, key=lambda k: (-len(k), k))), re.I)
    def replace(text):
        text = pattern.sub(lambda m: folded[m.group().casefold()], text)
        text = re.sub(r'https?://[^\s<>"\]|)]+', lambda m: 'https://example.invalid/ref/' + hashlib.sha256(m.group().encode()).hexdigest()[:12], text)
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
                      lambda m: 'person-' + hashlib.sha256(m.group().encode()).hexdigest()[:10] + '@example.invalid', text)
        return text
    return replace


def translate_json(value, replace):
    if isinstance(value, str): return replace(value)
    if isinstance(value, list): return [translate_json(v, replace) for v in value]
    if isinstance(value, dict):
        pairs = [(replace(k), translate_json(v, replace)) for k, v in value.items()]
        if len({k for k, _ in pairs}) != len(pairs): raise ValueError('Translation would collapse JSON keys.')
        result = dict(pairs)
        if 'before' in result and isinstance(result['before'], dict) and 'basedOn' in result:
            result['basedOn'] = O.revision(result['before'])
        if 'revision' in result: result['revision'] = O.revision(result)
        return result
    return value


def export(source, destination, glossary):
    from proposal_upgrade import require_migrated
    require_migrated(source, include_bin=False)
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if not source.is_dir(): raise ValueError('Source engagement does not exist.')
    if destination == source or source in destination.parents or destination in source.parents:
        raise ValueError('Source and destination must be separate, non-nested folders.')
    if destination.exists(): raise ValueError('Destination already exists. Choose a new output folder and review before replacing a fixture.')
    config = json.loads(Path(glossary).read_text(encoding='utf-8'))
    mapping = config.get('replacements', {})
    replace = transformer(mapping)
    # No timestamps, machine paths, source filenames or glossary content in the manifest.
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.anonymise-', dir=destination.parent))
    try:
        source_candidates = B.load_candidates(source / 'baseline') if (source / 'baseline').exists() else []
        for path in sorted(source.rglob('*')):
            rel = path.relative_to(source)
            if path.is_symlink(): raise ValueError('Source contains a symbolic link; export only ordinary files.')
            if not path.is_file() or any(p in EXCLUDED for p in rel.parts): continue
            if not (str(rel) in ROOT_FILES or (rel.parts[0] in DIRECTORIES and len(rel.parts) == 2)): continue
            if path.suffix not in ('.md', '.json', '.txt'): continue
            target = staging / replace(str(rel))
            if not target.resolve().is_relative_to(staging.resolve()): raise ValueError('Translated path escaped the output folder.')
            if target.exists(): raise ValueError('Translation would collapse filenames.')
            text = path.read_text(encoding='utf-8')
            if path.suffix == '.json': text = json.dumps(translate_json(json.loads(text), replace), indent=2, ensure_ascii=False) + '\n'
            else: text = replace(text)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding='utf-8')
        # Candidate keys derive from source text. Re-key verdicts and all references deterministically.
        idmap = {}
        for c in source_candidates:
            if not c['id'].startswith('c'): continue
            key = replace(c['page']) + replace(c['table']) + replace(c['title']) + replace(c.get('ref', ''))
            idmap[c['id']] = 'c' + hashlib.sha1(key.encode()).hexdigest()[:8]
        if idmap:
            pattern = re.compile(r'\b(?:' + '|'.join(re.escape(k) for k in idmap) + r')\b')
            for p in sorted(staging.rglob('*')):
                if p.is_file():
                    text = pattern.sub(lambda m: idmap[m.group()], p.read_text())
                    if p.suffix == '.json': text = json.dumps(translate_json(json.loads(text), lambda v: v), indent=2, ensure_ascii=False) + '\n'
                    p.write_text(text, encoding='utf-8')
        engagement = staging / 'engagement.md'
        if engagement.exists():
            text = engagement.read_text()
            text = re.sub(r'^- Writes:.*$', '- Writes: direct', text, flags=re.M)
            text += '\n- Data classification: anonymised fixture\n'
            engagement.write_text(text)
        files = sorted(p for p in staging.rglob('*') if p.is_file())
        # A glossary mistake (for example a replacement still containing an original term) fails closed.
        forbidden = list(mapping) + config.get('forbidden', [])
        for p in files:
            text = str(p.relative_to(staging)) + '\n' + p.read_text()
            if any(term.casefold() in text.casefold() for term in forbidden if term):
                raise ValueError('An original or forbidden term remains in the output. Review the private glossary on the work laptop.')
        manifest = {'format': 1, 'classification': 'anonymised fixture',
                    'reviewRequired': 'Review unlisted names and technical details on the work laptop before sharing.',
                    'files': {str(p.relative_to(staging)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
        (staging / 'anonymised-manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
        staging.rename(destination)
        return {'files': len(files), 'classification': 'anonymised fixture'}
    except Exception:
        shutil.rmtree(staging)
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source'); parser.add_argument('destination'); parser.add_argument('--glossary', required=True)
    args = parser.parse_args()
    try: print(json.dumps(export(args.source, args.destination, args.glossary)))
    except (ValueError, OSError) as e: parser.exit(1, str(e) + '\n')
