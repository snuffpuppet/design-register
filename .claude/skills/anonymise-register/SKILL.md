---
name: anonymise-register
description: Create a deterministic anonymised engagement for development on a personal laptop, using the private glossary on the work laptop.
usage: "/anonymise-register <source-folder> <new-output-folder> <private-glossary.json>: build a shareable fixture"
---

# Anonymise a register

Version 1.0, 19 September 2026.

Run on the work laptop. The Python tool performs the substitutions; no model-generated rewriting is needed. It works the same when operated by Opus or by a person.

1. If the old private `translate.py` holds the glossary, migrate its source/replacement pairs locally to the documented JSON shape without inventing replacements. Keep that identifying mapping on the work laptop. Read `docs/anonymisation.md` for the glossary format and the review boundary. Resolve the three arguments. If a required path is missing, ask for that path.
2. Run `make anonymise SRCENG="<source>" DEST="<new-output>" GLOSSARY="<private-glossary>"`. Docker is required. The source and glossary mount read only. An existing destination is refused and must not be deleted automatically.
3. If validation fails, inspect and correct the glossary locally on the work laptop. Do not copy original terms, raw examples or the glossary into a handoff intended for the personal laptop. Never bypass a remaining-term failure.
4. Inspect the resulting text on the work laptop for names and technical details absent from the glossary. The tool removes mapped terms and replaces URLs/emails; it cannot recognise every unlisted confidential phrase. Keep register IDs, types, states, dates and link structure intact when extending mappings.
5. Run the same export into a second new temporary folder and compare file hashes against `anonymised-manifest.json` if reproducibility needs checking. The automated tests already cover this property.
6. Report output location, file count, validation result and whether content review is complete. Sharing or committing the output is a separate user action. The private glossary and operation journal never belong in a shareable export.

Do not invoke Confluence or the transcript ingester. This command reads local source material and creates a separate fixture.
