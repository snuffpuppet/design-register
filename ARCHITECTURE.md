# Architecture

Version 1.7, 20 September 2026. Owner: Adam Moyes.

## Boundaries

This repository owns the register model, local console, rationalisation tools and Confluence import/push commands. The separate transcript ingester is never edited here. Real engagement data and the identifying anonymisation glossary stay on the work laptop. Synthetic and reviewed anonymised fixtures support development on the personal laptop.

The console is a standard-library Python server and local Preact/htm assets, running in Docker. Markdown item files remain the shared register format. No external AI service or CDN is required to use it. Optional Claude commands are under `.claude/skills/`; deterministic scripts do the repeatable processing.

## Working contexts and storage

Rationalise and Desktop share the table and item panel. Rationalise sends immediate single/bulk corrections to `/api/rationalise/edit`, without lifecycle entry checks or review forms. The endpoint preflights every row and commits inside one recoverable transaction. Desktop follows lifecycle transitions; scope shortcuts open filtered Desktop work. Optional saved reviews and meeting records retain existing data and structured operations. These contexts are independent of direct versus change-set persistence.

| Component | Responsibility |
|---|---|
| `model.py`, model document | Types, fields, states, transition and integrity rules |
| `items.py` | Parse and render item files |
| `integrity.py` | Pure integrity/provenance analysis; review does not suppress its findings |
| `baseline.py` | Tolerant source conversion and initial ID/provenance map |
| `workspaces.py` | Review snapshots/proposals/revisions and meeting agendas/outcomes |
| `server.py` | API coordination, validation and the shared register commit boundary |
| `operations.py` | Operation journal, exception rollback, startup recovery and guarded undo |
| `views.py` | Consistent report filtering and summaries, separating corrections/proposals |
| `anonymise.py` | Deterministic fixture generation using a private replacement glossary |
| `push-pages.py` and Claude skills | Build-before-send Confluence output under existing guards |

Engagement metadata files are `reviews.json`, `meetings.json`, `views.json`, `aliases.json` and dismissal ledgers. `operations/*.json` holds private before/after snapshots and operation metadata. These journals never enter anonymised exports.

## Import and rationalisation

Confluence pull retains source pages and raw audit copies under `baseline/`. Import and review converts rows to working items and immediately creates a review batch. It refuses to overwrite existing registers. There is no separate freeze workspace. The historical `baseline/frozen.md` filename and `freeze()` converter remain internal compatibility details used by push and existing fixtures.

Reviews can be repeated over any current register items. The review's starting snapshot is immutable; each proposal retains the version it was reviewed against. Apply refuses changed records. Corrections specify reason, evidence and optional effective date, and can set any valid status for the resulting type without replaying transitions. Missing fields/supports remain integrity findings. They are never fabricated to reach a zero count.

Merge requires explicit resolution of conflicting values and records an alias. Retype creates a new correctly prefixed item, rewrites incoming links and reserves the old ID through an alias. Split creates records with source provenance and retains the original as an index, preserving external references. Exclusion reserves the deleted ID and retains its reason in the alias/journal. IDs are not compacted in normal use.

## Write and recovery boundary

Every HTTP mutation requires a maker and runs under the server lock inside an operation transaction. Register operations call `commit()`; related link rewrites and legacy renumber writes are coordinated by the same transaction. Metadata uses atomic replacement. Item writes atomically replace files. Baseline conversion remains a legacy multi-file writer, protected by the surrounding operation.

A prepared journal is persisted before mutation. A successful operation records its resulting snapshot; an exception restores the starting snapshot. Startup restores prepared operations left by interruption. Undo requires current engagement content to match the operation result before restoring its start. Reads through the console share the lock and do not observe intermediate states. Browser item revisions catch stale edits, including multiple changes on the same day.

This is local recovery, not a distributed transaction with the ingester or an external editor. Run those writers at separate times. An external process changing files during an operation is not coordinated by this lock. Completed journals retain only changed file contents plus an engagement fingerprint; prepared journals retain the full recovery snapshot. Archive private completed engagement history deliberately.

## Integration contracts

Normal workflow uses existing model transition and required-field checks. Generic edit cannot change status or unknown fields. Direct mode permits explicit field clearing. Change-set mode refuses unsupported clearing, bulk, merge and correction application; sessions and views remain available.

Before writing a change set, the engagement must explicitly declare a supported ingester model version (2.30 or 2.31). The repository does not claim the current sibling implementation has been ported. Meeting exports include a stable MTG reference for correlation, but transcript reconciliation remains the sibling repository's responsibility.

Confluence reads and writes retain the existing source/engagement guards and permission records. Push builds the full registers into files for review; it does not silently publish a saved report's subset. An anonymised fixture is never a production source.

## Validation

Container tests cover the model, conversion, integrity, writes, stale revisions, corrections, aliases, reports, agendas, recovery and deterministic export. Browser smoke checks use disposable data in a separate container. Work-laptop acceptance instructions provide expected outcomes and a sanitised feedback path. The private glossary and raw failures containing company data remain on that laptop.
