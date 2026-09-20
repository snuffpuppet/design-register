---
objective: work-laptop-rationalisation-meetings
title: Use Rationalise and Desktop on the work laptop
written: 20 September 2026
commit: 87e46b3
branch: feature/rationalisation-meetings
status: active
model-version: 2.33
---

## Objective

Use the shared register table to correct generated records in Rationalise and progress work under the model in Desktop. Keep real registers and the identifying glossary on the work laptop, returning only reviewed anonymised fixtures for development.

## Where things stand

- The simplified table modes are committed at `87e46b3` on `feature/rationalisation-meetings`. New type-change previews, dismissible status menus, restorable deletion and lead-first merge previews are working-tree changes, along with model 2.33 and README 1.4. These latest changes remain **uncommitted**; pulling `87e46b3` alone will not include them. No push was performed by this session.
- Rationalise uses immediate single and bulk field/status edits. Desktop uses the same table with workflow checks. Desktop by scope is a predefined Desktop filter. Saved reviews and meeting records remain optional tools; ordinary cleanup requires no review batch.
- All 219 Python tests passed. New disposable browser checks passed for Escape/outside menu dismissal, merge/type preview cancellation and acceptance, rewritten references, and rubbish-bin persistence/restoration. Disposable browser checks passed for immediate status correction, bulk date setting/clearing, bulk scope changes and scope shortcuts restoring Desktop workflow rules. The local development console was restarted and responded successfully. No real work-laptop registers were tested.
- The root README is the operator guide. This handoff replaces its earlier review-batch rollout instructions; the other two active handoffs remain historical context and were not changed in this update.
- The sibling ingester, live Confluence connector and work-laptop configuration remain unchecked. Item and change-set wire formats are unchanged.

## Next steps

1. **Transfer the current code and documentation.** Commit and transfer the reviewed code/docs through the normal code-transfer route, or copy the complete intended changes. Preserve the work laptop's actual engagement and local changes. Do not include local test engagement journals or review data merely because they are untracked. Done when the work checkout has model 2.33, README 1.4 and `/api/rationalise/edit` in `console/server.py`.
2. **Start the dashboard directly.** From that checkout run `make up ENG=/absolute/path/to/real-engagement` and open `http://localhost:8085` (or the configured port). If an existing container retained its server process, run `make reload`, then refresh the browser. No `/resume`, import, freeze or data conversion is required for existing registers. Done when the intended engagement loads with Rationalise, Desktop and its declared scope shortcuts.
3. **Check the work-laptop installation.** Follow `docs/work-laptop-acceptance.md` on a disposable copy, manually or with `/check-register-release`. Before correcting real records, confirm direct write mode and resolve any unapplied change sets through their normal process. Keep external ingester writes separate. Done when single/bulk corrections persist and Desktop still enforces transitions.
4. **Use the registers.** Follow README's Rationalise, Desktop and Working by scope sections. Use optional meeting records only when a saved agenda or discussion record is useful. Done when the intended corrections and subsequent workflow changes appear correctly in the register history.
5. **Prepare anonymised feedback when needed.** Follow `docs/anonymisation.md` and `/anonymise-register` using the private work-laptop glossary. Done when deterministic exports have been locally reviewed before transfer.

`/resume work laptop rationalisation meetings` is optional. Use it in Claude when asking Opus to continue setup, investigate a problem or develop this project with session context. It reads and checks this handoff; it is not a dashboard startup or migration command.

## Decisions taken on purpose

- Single and bulk correction use the existing table. Mandatory review batches, evidence forms and preview/apply steps were removed from ordinary cleanup at the user's request.
- Rationalise bypasses lifecycle entry requirements while preserving field structure, valid statuses, revisions, correction history and recoverable transactions. Missing evidence remains visible; the tool does not manufacture approvals or intermediate open items.
- Desktop by scope applies a filter and restores Desktop workflow rules. It is not a third editing engine. Existing structured review/meeting records are retained as optional tools.
- Historical corrections require direct writes because the separate ingester contract cannot express them. No compatibility declaration should be added until the ingester actually supports it.
- Anonymisation remains deterministic and glossary-driven; Opus can run the existing Claude commands on the work laptop. Private content stays there.

## Open questions for the user

No product decision blocks startup. The work laptop's engagement path, write mode, pending changes, ingester compatibility and availability of the latest code must be checked locally.

## Watch out for

- The handoff's commit is the last committed base, not a release containing the latest structural-editing changes. Check the working tree as well as commit history when resuming.
- Pass `ENG=` deliberately: `make up` remembers the previously mounted engagement. Refresh the browser after loading updated code. Reloading the browser starts in Desktop mode.
- Rationalise edits save immediately; date fields must be corrected explicitly. README describes text, dropdown and bulk save behaviour. Recent operations offers undo only while the engagement still matches the recorded result.
- Preserve real work-laptop files; do not replace them with personal-laptop fixtures or regenerate a mounted sample. The external ingester does not share the console's process lock.
- The rubbish bin captures deletions from this version onwards. Older deletions require their existing operation journals or engagement version history.
- Operation journals, rubbish-bin snapshots and the identifying glossary contain private material. Unknown confidential phrases still need local review before sharing an anonymised export.
- Confluence publication remains a separate reviewed operation. This handoff does not authorise a push.

## Anchors

- files:
  - console/server.py
  - console/model.py
  - console/static/store.js
  - console/static/rail.js
  - console/static/table.js
  - console/static/cells.js
  - console/static/bulk.js
  - console/static/panel.js
  - console/operations.py
  - console/anonymise.py
  - console/structure.py
  - console/static/structure.js
  - console/tests/browser-structure.cjs
  - console/tests/browser-rationalise.cjs
- docs:
  - README.md
  - CLAUDE.md
  - solution-register-model.md
  - docs/work-laptop-acceptance.md
  - docs/anonymisation.md
- config:
  - engagement.md: Writes, Ingester model version, Scopes
  - docker-compose.override.yaml: locally remembered engagement and port
  - confluence.json: parent_page_url, push.engagement, permissions
- external:
  - Work-laptop real engagement, pending changes and private glossary
  - Separate solution-register ingester and installed contract
  - Confluence connector and live page versions
  - Transfer of the currently uncommitted implementation and documentation
