---
objective: refine-register-dashboard
title: Continue refining the register dashboard
written: 21 September 2026
commit: 9ed53db
branch: feature/rationalisation-meetings
status: active
model-version: 2.34
---

# Dashboard refinement handoff

Version 1.3, 21 September 2026.

## Objective

Continue refining the dashboard through practical use of generated registers, making individual and bulk cleanup straightforward. Preserve the clear separation between correcting an inaccurate record in Rationalise and progressing work through the model in Desktop.

Read [README.md](README.md) for current operator instructions, then [CLAUDE.md](CLAUDE.md) for implementation constraints. This root file is the requested starting point for the next development session.

## Where things stand

- Latest validation for model 2.34: **224 Python tests passed**. Chromium passed proposal labels, unfinished/deferred inclusion, combined scope/phase filtering, blank estimates, saved report filtering, No phase and design guidance. `make proposal-check` passed against a disposable engagement. The browser save check requires Made by, as do other journalled operations. Work-laptop data and Confluence remain untouched.

- Latest refinement: Rationalise now has visible Type and Scope dropdowns above the table, with All types, All scopes and No scope options. They share the existing filters, retain Rationalise mode and clear row selection when changed. Scope choices include declared and recorded values. README describes the controls. Included in this refinement update.
- Filter validation: Chromium passed combined type/scope filtering, clearing to all items, blank scope, switching type from a register view, existing multi-filter state and search, with no browser errors. Used a disposable copy under `/tmp/register-filter-check` on port 18088. No backend changes or model changes; Python tests were not rerun. The active `register-console` mounts this checkout's `console` directory, so refresh the browser for the new controls.
- Branch: `feature/rationalisation-meetings`. The baseline before this refinement was `9ed53db` (`improve UI`). Inspect git for the current refinement commit. The update includes Rationalise filters, model 2.34 Change proposals and the work-laptop upgrade procedure.
- The four latest requests are implemented: single/bulk type changes, dismissible status menus, a persistent rubbish bin with restoration, and lead-first merging with before/after previews and Accept/Cancel.
- Ordinary Rationalise edits save directly. Type changes and merges use a preview because they restructure records and references. They do not require a review batch.
- Last implementation validation: **219 Python tests passed**. Chromium checks passed for status Escape/outside dismissal, merge/type preview cancellation and acceptance, reference rewrites, and bin persistence/restoration. Earlier browser checks covered single status corrections, bulk date set/clear, bulk scope edits and scope shortcuts restoring Desktop workflow checks. These were disposable fixtures, not company registers. Tests were not rerun for this documentation-only handoff.
- The local console was restarted successfully after the implementation. Current Docker/container state has not been rechecked for this handoff; inspect before restarting or repointing anything.
- The subsequent type/scope filters and Change proposal refinement are implemented as described here. The next session should continue from the user's next observed friction rather than invent another workflow.
- The older [work-laptop handoff](handoffs/work-laptop-rationalisation-meetings.md) describes deployment. Its claims that the latest structural changes are uncommitted are now stale: `9ed53db` includes them. Other handoffs are historical context; do not revive their freeze or mandatory-review instructions.

## Product decisions to preserve

The user's direction is: **“Simple beats complicated every time.”**

- **Rationalise:** the existing table and item panel, with individual and bulk field/status corrections that bypass lifecycle entry requirements. No required review outcome, evidence form or staged batch application for ordinary cleanup. Retain valid field structure, typed statuses, stale-edit checks, history and recovery.
- **Desktop:** the same controls with normal model transitions and required supporting records.
- **Desktop by scope:** a predefined Desktop filter, retaining workflow rules. It is not another editing engine. Saved reviews and meeting records remain optional tools.
- **Type changes:** choose the destination type and optionally its status, review before/after, accept or cancel. New typed IDs replace old ones; aliases and rewritten links preserve references. History and old-type fields are retained. No reconstructed intermediate workflow.
- **Merging:** choose the lead, see the result, accept or cancel. The lead retains populated fields, blanks can be filled, and conflicting values/history remain in Notes. Sources and external links are combined. Same-type records only; change a type first if necessary.
- **Deletion:** move records into the engagement's rubbish bin. Restore their original IDs/history and removed incoming links while preserving later field edits. Bin restoration is separate from guarded whole-operation undo. Earlier deletions are not retroactively added to the bin.
- **Status menus:** Escape, an outside click or clicking the status again dismisses without changing its value.

## Agreed terminology and next work-laptop migration

Implemented in model 2.34: **Change proposal** replaces the internal Change request display name. Existing CR records load unchanged; no data rewrite is necessary. See [the work-laptop upgrade procedure](docs/change-proposal-upgrade.md).

- A change proposal tracks outstanding work identified as requirements and solution design develop iteratively. It need not represent a departure from a previously complete or approved baseline. It can be essential to delivery.
- Requirements and limitations retain lightweight options. A Decision records the selected option where the decision rules require one. The proposal has a separate purpose: visibility of the resulting work, scope, sizing, cost, approval and delivery. Reference the originating requirements/limitations, any relevant Decision and the solution design rather than duplicating their contents.
- A proposal must link to the solution design. It may exist before sizing, approval or creation of a vendor change request. Selecting an approach and authorising its cost and delivery are separate decisions; the name remains Change proposal after approval, with status showing its position.
- Vendor change requests are managed by the vendor. Store their references/links on the proposal where vendor work requires them; do not introduce another internally managed vendor-request record. Internal, Vendor and Both delivery remain supported.
- SLT needs to see outstanding proposals by phase and scope, such as Phase 1 or Enterprise Ethernet, with delivery/approval position and cost visibility. Distinguish unknown sizing from zero cost, and indicative estimates from confirmed costs.
- **On the work laptop after the next repo pull:** follow docs/change-proposal-upgrade.md. Stop writers, back up, pull, run `make proposal-check ENG=<actual engagement>`, and restart against that engagement. The check is read-only; CR IDs, folders, links, history and statuses remain unchanged. Review Source for the solution design and review phase, scope and sizing manually; do not invent missing facts.
- Implementation: new/legacy import headings accepted, requirement Options supported, optional `based on DEC-…` link supported. Outstanding proposals opens the shared table with unfinished/deferred CRs, phase/scope filters and estimate/vendor/design visibility. Saved reports preserve phase filters and blank estimates read Not sized. Existing statuses (including Submitted and LIM Change requested) deliberately retained for compatibility. No ingester compatibility declaration or real-data migration was performed.

## Next steps

1. **Re-establish the actual state.** Read this file, README and CLAUDE; inspect `git status`, current branch and changes since `9ed53db`. Check which engagement any running container mounts. Done when current code and data boundaries are understood without disturbing the user's registers.
2. **Reproduce the next reported friction on disposable data.** Use a synthetic or reviewed anonymised example matching the user's issue. If no further issue is supplied, ask which interaction they want to refine next. Done when there is a concrete expected/actual behaviour, not a speculative redesign.
3. **Refine the existing shared controls.** Keep Rationalise permissive about workflow and Desktop bound to it. For structural changes, ensure the displayed result is what acceptance writes and that cancellation writes nothing. Done when the shortest intended user flow works and references/history remain intact.
4. **Verify the affected boundary.** Run `make test` for backend changes and the relevant browser scenario for UI behaviour. The structural browser script mutates its fixture and requires a fresh setup. Done when relevant checks pass and any untested external behaviour is stated plainly.
5. **Keep the handoff and operator guide current.** Update README for changed controls and this file for the next session. Bump the model only if semantics change. Transfer code separately from real engagement data through the user's normal route.

## Validation and debugging pointers

- [Work-laptop acceptance](docs/work-laptop-acceptance.md) describes fixture requirements and manual checks.
- `console/tests/browser-rationalise.cjs`: correction editing and Desktop scope boundaries.
- `console/tests/browser-structure.cjs`: menu dismissal, merge/retype cancel and accept, bin persistence and restoration. Its four-record fixture is documented in the acceptance guide.
- `console/tests/browser-smoke.cjs`: optional structured reviews and meeting records.
- `console/Dockerfile.browser-test` provides native Chromium and Puppeteer. Build it as needed and mount the desired browser script; its default command runs the older smoke script.
- Last disposable previews used ports 18086 and 18087. Screenshots were written under `/tmp/register-simple-check` and `/tmp/register-structure-check`. These are optional local artefacts, not dependencies or transferable test evidence.
- Two browser regressions fixed in the last session deserve attention if these controls change: status dismissal listeners must be installed before the next key event; structural dialogs must tolerate source records disappearing during state reload after a merge or type change.

## Watch out for

- Everything runs in Docker. Use a separately named container and spare port for mutation tests; leave the active real-data console alone. Python changes require process reload; static changes require browser refresh. `make up` remembers its engagement, so pass `ENG=` deliberately.
- Correction and structural operations require direct writes and no unapplied change sets. Resolve proposals through their established workflow. Do not falsely declare ingester compatibility to bypass a guard.
- All HTTP mutations stay within the journalled transaction boundary. Preflight the full selection, reject stale previews, preserve aliases and test rollback where relevant. Do not replace undo or restore with overwriting an entire old engagement snapshot after intervening edits.
- The rubbish bin and operation journals contain private snapshots and stay out of anonymised exports. Real registers and the identifying glossary live on the work laptop; personal-laptop examples must be synthetic or reviewed anonymised data.
- The separate `../solution-register` repository owns transcript ingestion and is not edited here. The external ingester does not share the console's write lock. Opus on the work laptop can run deterministic anonymisation through the existing `.claude` commands.
- No live Confluence publication or work-laptop acceptance was performed here. Remote availability of the branch is unchecked. `/resume` is optional session context for Claude, not a requirement for starting the dashboard.

## Anchors

- files:
  - console/server.py: immediate corrections, structure previews/apply, deletion/restoration, commit boundary
  - console/structure.py: deterministic retype/merge plans and bin persistence
  - console/operations.py: recovery, guarded undo and change events
  - console/static/structure.js: preview dialogs and rubbish-bin screen
  - console/static/cells.js: field editing and status menus
  - console/static/bulk.js, console/static/panel.js: action entry points
  - console/static/store.js, console/static/rail.js, console/static/table.js: shared mode/filter state and table
  - console/tests/test_workspaces.py, console/tests/test_anonymise.py: structural/recovery/privacy regression coverage
- docs:
  - README.md, CLAUDE.md, ARCHITECTURE.md
  - solution-register-model.md: model 2.33, especially section 12
  - docs/work-laptop-acceptance.md, docs/anonymisation.md
- config:
  - engagement.md: Writes, Scopes, Ingester model version
  - docker-compose.override.yaml: locally remembered engagement and port
- external:
  - Work-laptop real registers, glossary and installed ingester version: unchecked
  - Running Docker containers and temporary fixtures: recheck locally
  - Confluence connector, live pages and remote branch availability: unchecked
