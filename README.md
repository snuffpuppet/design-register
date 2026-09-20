# design-register

Version 1.0, 19 September 2026.

A local console for rationalising generated solution registers, progressing current work, and running meetings. Six Markdown registers follow `solution-register-model.md` (2.31). The transcript ingester stays in the separate `solution-register` repository.

## Working contexts

- **Rationalise:** start a review batch over actual register items. Compare the starting snapshot with current records, confirm or correct them, resolve duplicate conflicts, retype, split or exclude. Corrections need a reason and evidence. Preview before applying. Historical corrections can set the known current status directly, without reconstructing intermediate open items. Missing evidence and integrity findings remain visible.
- **Desktop:** use the shared table, filters, item panel and model-generated forms. Workflow moves retain the normal transition and required-field checks. Bulk operations preflight all selected items before writing.
- **Meetings:** prepare a fixed agenda from open items or a selection, reorder it, record progress and outcomes, create follow-up open items, and export a summary with a stable meeting reference. Changing a register item does not remove it from the agenda.

These contexts are independent of the engagement's write mode. `- Writes: direct` updates item files. `- Writes: change-sets` records proposals for the ingester. Reviews, meetings and saved views work in either mode; applying historical corrections needs direct mode because the current ingester contract cannot express them. Change-set writes require an explicitly supported `- Ingester model version: 2.30` or `2.31`, declared only after porting the sibling ingester.

## Import and review

`/import-confluence <engagement>` remains a Claude command under `.claude/skills/`. It pulls source pages under the existing permission and engagement guards. Open the console and choose **Import and review**. The import creates working registers, assigns IDs, retains source provenance and opens a review batch. There is no separate freeze mode. Existing registers open directly in the table and can be reviewed repeatedly.

The internal `baseline/frozen.md` map is retained for compatibility with the Confluence push builder and old imports. Imported pages remain evidence. `/push-confluence` still builds and reviews output before its separate write gate; implementation work never pushes automatically.

## Run and verify

```sh
make sample
make up ENG=test-data/puppy-gloves
make test
```

Everything runs in Docker, except the existing sample file generator. Browser dependencies are bundled locally; the console needs no CDN. `make up ENG=/absolute/path/to/engagement` supports private data outside the code checkout. Stop the console before regenerating a mounted sample.

Every console mutation is covered by a recovery journal under the engagement's `operations/`. Failed writes roll back; startup recovers interrupted operations. Recent operations offers undo when the engagement has not changed since the operation. The browser sends item revisions to detect stale edits. Coordinate use with the external ingester: it does not participate in the console's process lock.

## Work and personal laptops

Develop against synthetic or reviewed anonymised fixtures here. Keep real registers and the identifying glossary on the work laptop. `console/anonymise.py` performs deterministic substitutions and reference re-keying. `/anonymise-register` lets Claude, including Opus, run the same script. No model-generated rewriting is required.

Read [the anonymisation instructions](docs/anonymisation.md) and [work-laptop acceptance checks](docs/work-laptop-acceptance.md). `/check-register-release` runs those checks using a disposable copy.

## Repository map

| Path | Purpose |
|---|---|
| `CLAUDE.md` | Project conventions and implementation constraints |
| `ARCHITECTURE.md` | Components, write boundaries and recovery behaviour |
| `solution-register-model.md` | Types, lifecycle rules, relationships and correction semantics |
| `console/` | Standard-library Python server, local Preact interface and tests |
| `.claude/skills/` | Existing Confluence/handoff commands plus anonymisation and release checks |
| `docs/` | Design history and work-laptop operating instructions |
| `engagements/test/`, `test-data/` | Anonymised and synthetic development fixtures |

Australian English. Documents carry versions and dates. The sibling ingester is never edited from this repository.
