# Deterministic anonymisation

Version 1.1, 20 September 2026.

The generic tool is `console/anonymise.py`. Its private glossary is stored on the work laptop, outside the tracked code. Opus can run `/anonymise-register`; the output does not depend on its wording or reasoning.

```json
{
  "replacements": {
    "Example Company": "Puppy Gloves",
    "Example Person": "Priya Sample",
    "Example Product": "Wool Loom"
  },
  "forbidden": ["an additional phrase that must not appear"]
}
```

This example contains invented names. A real glossary must never be copied to the personal laptop. Mapping keys are case-insensitive literal strings. Longest matches win and substitution occurs once, so replacements never cascade. Preserve item identifiers, lifecycle states, dates, field labels and link words. Map names and confidential technical vocabulary consistently across prose, fields, paths and JSON keys.

```sh
make anonymise SRCENG=/path/to/private/engagement \
  DEST=/tmp/register-fixture-new \
  GLOSSARY=/path/to/private/glossary.json
```

The destination parent must exist. The destination itself must not exist. Input and glossary are read only; an export is staged and published only after validation. The same input and glossary produce byte-identical outputs and manifests. URLs and email addresses become deterministic example.invalid references. Register IDs and relationships stay intact. Baseline candidate hashes and their verdict references are recomputed, as are review revisions. Raw Confluence responses, operation journals, push files and anonymisation resources are excluded. Only declared engagement files and register/baseline/change-set folders are copied.

Validation rejects remaining glossary terms, forbidden terms, colliding filenames or JSON keys, symbolic links and overlapping source/output folders. It cannot detect every unknown name or confidential description. Review the exported content on the work laptop before sharing. Add missed terms to the private glossary, then regenerate into a new folder. The manifest contains only output paths and output hashes, with no timestamp or private glossary.

For a bug report, prefer a small synthetic case first. Otherwise export the relevant engagement, complete the work-laptop review, and transfer the reviewed fixture. Transfer application code back to the work laptop; never overwrite production registers with fixture data.

## Existing work-laptop glossary

If the old engagement-local `translate.py` contains the mapping as a Python dictionary, ask Opus on the work laptop to transcribe that mapping into the `replacements` object above. Keep the same source/replacement pairs and preserve the private original. This is a one-time glossary migration; Opus must not rewrite the register content itself. Run the deterministic export and content checks afterwards. Neither the old script's identifying dictionary nor the new JSON belongs in a cross-laptop handoff.

Deleted-record snapshots in `rubbish-bin.json` stay on the source laptop. The export allowlist excludes the bin as well as operation journals.
