# Rationalisation and meetings

Version 1.0, 20 September 2026. Implementation branch: feature/rationalisation-meetings.

## Intended behaviour

Rationalisation establishes the current position without replaying historical workflow. Desktop edits retain the model's transition rules. Meetings retain a fixed agenda and outcomes while using those same desktop operations. Direct versus change sets remains an independent persistence choice.

Review batches snapshot selected items and keep proposals, review outcomes, evidence and revisions. Applying corrections is a direct-mode operation, with unresolved integrity findings retained. Review and meeting metadata can be saved in either write mode. Multi-file writes have a recovery journal and revision-checked undo. Stable published identifiers survive through aliases when records merge or change type.

## Build and validation

- [x] Validated field edits, explicit clearing, consistent report filters and compatible change-set writes.
- [x] Recovery journal, revisions and bulk preflight.
- [x] Review batches, historical corrections, comparison, retype/split and aliases.
- [x] Persistent meeting agendas, outcomes and export.
- [x] Shared frontend, baseline entry, local browser dependencies.
- [x] Deterministic anonymisation, private glossary, Claude commands and work-laptop acceptance runbook.
- [x] Container unit tests and browser smoke checks.

The sibling ingester is outside this change. Real engagement data and identifying glossary remain on the work laptop. No production register edits or Confluence writes are part of implementation.

## Validation evidence

`make test IMAGE=register-console-feature` builds the application and runs container unit tests. The final suite passes 208 tests and includes import without a freeze workspace, repeated review counts, historical correction without intermediate open items, conflicting merge resolution, aliases, reserved IDs, retyping, splitting, stale edits, partial-failure rollback, startup recovery, guarded undo, report filtering, persistent agendas, atomic follow-up creation and deterministic anonymisation. Push-builder tests cover source IDs after aliases and empty imported register tables.

The native Chromium Docker smoke test checks local-only browser requests, correction preview/apply/reload, a meeting follow-up and summary, and report correction separation. Screenshots are generated from disposable data. Claude skill YAML, standard fields and the project's usage extension were validated; SessionStart lists all six commands.

No real Confluence connector or work-laptop private data was used. The sibling ingester remains unchanged. The work laptop still needs its private glossary and an explicit ingester compatibility declaration only after that separate port is complete.
