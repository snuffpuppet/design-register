---
objective: baseline-abb-nokia
title: Baseline the abb-nokia registers from Confluence and start running them
written: 14 September 2026
commit: 352fe8d
branch: scope-field
status: active
model-version: 2.27
---

## Objective

Turn the registers already held in the oss-kb Confluence Design Register, part pipeline-generated and part hand-written, into the abb-nokia engagement's starting registers: reconcile and de-duplicate them in the console, correct what is at the wrong altitude, freeze the result as item files, push the frozen tables back to the same Confluence pages, and from then on run the engagement through meetings with every change written straight into the item files and pushed back.

**Read this first: the work is on an unmerged branch with a Critical finding outstanding.** `scope-field` holds ten commits and is not merged into `main`. Nothing is pushed. The baseline cannot be frozen until that branch lands, because the Scope field it adds is now required.

## Where things stand

- **The view pages are named.** `engagements/abb-nokia/baseline/skip-pages.txt` lists the four: Outstanding, Next Phase, Register Conventions, Scope Taxonomy. Seven register pages produce 320 candidates. This was the old next step 2 and is done.
- **The column mapping needed no work.** Contrary to the previous handoff's expectation, Owner, Status, MoSCoW and Phase all fill from the real pages where the source carries them. `Links` staying in Notes and `Vendor ref` being CR-only are both deliberate model behaviour, not misses. The one real gap was Scope, which the model had no field for.
- **Scope is built, on the branch.** Model 2.27 gives every item a Scope whose vocabulary each engagement declares in a `## Scopes` section of `engagement.md`. An engagement that declares none behaves as it did under 2.26. Spec and plan are committed at `docs/superpowers/specs/2026-09-14-scope-field-design.md` and `docs/superpowers/plans/2026-09-14-scope-field.md`. 130 tests pass. Verified in a browser both with scopes declared (abb-nokia) and without (`engagements/test`).
- **abb-nokia declares its sixteen scopes** in `engagements/abb-nokia/engagement.md`, seeded from the Scope Taxonomy page, which stays a skipped view page. That file is untracked and gitignored, so it exists only on this machine.
- **All 320 candidates now carry a scope, none blank.** The `CRs Register` page's `Domain` column folds into the same field, which is why `domain` is a word in the `COLS` entry.
- **Three candidates carry a scope outside the vocabulary** and will block the freeze: `NBN TC4 Access` on DEC-059 (a typo for `NbnTC4Access`), `Pool Management` on CR 14 (TMF685 resourcePoolManagement), and `Location Management` on CR 15 (TMF674 geographicSite).
- **`baseline/verdicts.json` holds 214 entries of which 211 attach to nothing.** All 211 came from pages now on the skip list and 210 were Discards. They are harmless and were left in place deliberately, so that restoring a view page brings its old verdicts back.
- **The final whole-branch review says not yet safe to merge.** One Critical, one Important, five Minor. Its findings are the first next steps below.

## Next steps

1. **Fix the Critical and the Important in `console/integrity.py` and `console/static/app.js`.** `scope` is in `REQUIRED_ON_CREATE` for all six types, so `offer()`'s gap loop runs `out.setdefault("scope", "")` whatever the engagement declares. Two UI surfaces read that key with no gate: the move form's "This move implies" panel (`app.js` `sGaps`), which then refuses to auto-tick a fail-level offer until someone types a scope, and the baseline Missing supports tab (`app.js` `blSupports`), which renders scope as free text so an off-list value can be typed and will block a freeze much later with no obvious cause. Fix at the source: thread `scopes` through `check()` to `suggestions()` to `offer()` and skip `scope` in the gap loop when there are none. `server.integrity_of()` already holds `eng["scopes"]`; `baseline.py`'s call site needs it plumbed from `baseline_state()`. Give the supports tab's field helper a select branch for scope mirroring `blEditor`. Done when a scope-less engagement's move form shows no Scope gap and its offers arrive ticked again.
2. **Drop or rewrite `test_offer_with_no_trigger_scope_leaves_an_empty_box`** in `console/tests/test_integrity.py`. It passes with the production change reverted, because the empty key comes from `REQUIRED_ON_CREATE` rather than from the lines it accompanies, and it enshrines the defect in step 1. Done when it asserts that a scope-less engagement's offer carries no scope key at all.
3. **Merge `scope-field` into `main`.** Done when `main` holds the ten commits plus the fixes and the suite is green there.
4. **Settle the three off-vocabulary scopes in the candidate editor.** `NBN TC4 Access` is a transcription error, retag to `NbnTC4Access`. `Pool Management` maps well to `Identifier and VLAN management`, which the CR's own description all but names. `Location Management` is a genuine gap in the client's taxonomy and needs a decision, see open questions. Done when `/api/baseline` reports every candidate's scope inside the declared sixteen.
5. **Work the baseline to zero undecided**: duplicates tab, then Row by row per register page, then bulk field fixes. Twenty duplicate groups and five suggestions are waiting. Done when Row by row shows nothing undecided.
6. **Work Missing supports to zero failures, then freeze.** Expect S8 for every vendor CR without a trigger and S5 for every limitation the source calls Accepted with no decision behind it. Done when `baseline/frozen.md` exists and the register tabs show items.
7. **`make push-pages ENG=engagements/abb-nokia`, read the manifest, then `/push-confluence abb-nokia`.** The first real send will show whether the connector's update call takes the storage body as built. Done when `confluence.json`'s log has a push entry and each pulled page's `page-version` holds the sent version.
8. **Run the engagement**: Made by set, meetings from Outstanding and Work through, weekly SLT report. Done when the first meeting's moves show in the item files' History sections.

## Decisions taken on purpose

- **Scope is an engagement opt-in, not a model-wide field.** A `## Scopes` section declares the vocabulary; an engagement without one carries no Scope and is checked by no rule. Rejected: always on with free text, which lets the vocabulary drift into the synonyms the taxonomy page exists to prevent; and always on and mandatory, which would break every existing engagement folder for no gain. This is section 6 of the model doing what it said it would since 2.17.
- **Scope is required on create where scopes are declared, and offered records inherit their trigger's.** Rejected: optional with a warning, and optional and silent, both of which let a scope filter under-report without showing it.
- **`scope` goes first in every `M.SHORT` list.** Load-bearing: `items.render_item` and `push_pages.columns` both iterate that table, so first position is what puts Scope directly after Status in the item file and the pushed table.
- **The `CRs Register` page's `Domain` column maps to Scope.** Seventeen of its nineteen rows already use the taxonomy's service names. The two that do not are step 4 above.
- **The Scope Taxonomy page stays on the skip list.** It is the vocabulary, not a register.
- **The 211 stale verdicts stay.** They attach to nothing and cost nothing, and they mean restoring a view page brings its old work back rather than starting over.
- **Work was done on a branch in the main checkout, not a git worktree.** `engagements/abb-nokia/` is untracked and gitignored so it does not exist in a worktree, and `make up` binds the console's Docker mount to the current directory.

## Open questions for the user

- **What `Location Management` should become.** The taxonomy has no location or address concept anywhere in its sixteen values, and TMF674 geographicSite fits none of them cleanly. Either add a value, which means changing the client's own page as well as `## Scopes`, or accept `Inventory and resources` as near enough. This is a statement about how the solution is carved up, not a tooling question.
- **Whether to move the opt-in gating server-side.** The review's structural suggestion: have `/api/state` send `short` already filtered per kind, which would delete five guards in `app.js` and put the behaviour under python coverage. Every opt-in breach found on this branch was in `app.js` and none could fail a test.
- The four questions the previous handoff left open still stand: whether pushed tables should carry Notes or History as columns, whether register gaps belong on the weekly SLT report, whether the "Baseline rejections" child page is created on the first push, and whether the engagement folder is committed after every meeting or once a week.

## Watch out for

- **`console/static/app.js` has no automated coverage at all**, and all four opt-in breaches found on this branch were in it. Two were caught by review before merge, two by the final review after the browser pass had already looked at the page. Treat any change that iterates `S.model.short` as needing a manual check in both configurations.
- Five stale model references to 2.26 remain: `console/README.md` line 5, `console/make-sample.py` line 45 which writes it into every generated sample, and `CLAUDE.md` lines 7 and 52.
- `console/items.py` writes `scope:` into every item file whether or not the engagement declares scopes, following model section 7, while section 4.1 says Scope is absent where none are declared. The model disagrees with itself; softening 4.1 is the smaller change.
- `scopeFilter` in `app.js` is module-level and is not reset when the view changes, so a filter set on Requirements still applies on Decisions. Visible in the select, so the harm is small.
- The first `/api/state` after `make up` can return empty. That is the startup race, not a defect; wait a moment and retry.
- Running `make sample` while the console is up leaves the container mounted on a deleted folder and every write fails. `make down` first.
- The first week's SLT report after a freeze reads high on "raised this week", because the freeze stamps items with the source's raised dates.
- The Row by row keys are inert while a text field has focus; click the page background first.

## Anchors

- files: console/model.py, console/integrity.py, console/baseline.py, console/items.py, console/server.py, console/static/app.js, console/push-pages.py, console/tests/test_integrity.py, .claude/skills/push-confluence/SKILL.md
- docs: CLAUDE.md, ARCHITECTURE.md, console/README.md, console/confluence-runbook.md, solution-register-model.md, docs/superpowers/specs/2026-09-14-scope-field-design.md, docs/superpowers/plans/2026-09-14-scope-field.md
- config: confluence.json push.engagement, confluence.json permissions.write, confluence.json parent_page_url, engagements/abb-nokia/engagement.md `## Scopes` and `Writes` line
- external: branch `scope-field`, ten commits, unmerged and unpushed; `engagements/abb-nokia/` untracked and gitignored so it lives on this machine only; the Confluence connector, still not configured; the sibling repository `solution-register` at model 2.20
