---
objective: baseline-abb-nokia
title: Baseline the abb-nokia registers from Confluence and start running them
written: 15 September 2026
commit: aeb29e1
branch: main
status: active
model-version: 2.28
---

## Objective

Turn the registers held in the oss-kb Confluence Design Register into the abb-nokia engagement's working registers and run the engagement from them: freeze what was pulled, keep rationalising in place (duplicates, merges, deletes, missing supports) while new items are raised, push the tables back to Confluence, and from then on write every meeting's changes straight into the item files.

**Read this first: the freeze no longer waits for the review to finish.** As of model 2.28 and commit aeb29e1 on `main`, the freeze writes every candidate not rejected, merged or discarded, reports what is left, and the console is Live from the first item with a Rationalise view over the item files. The previous handoff's steps 5 and 6 (work the baseline to zero, then freeze) are no longer the order of work. Spec: `docs/superpowers/specs/2026-09-15-rationalise-in-place-design.md`.

## Where things stand

- **`main` holds the scope field and the rationalise-in-place change.** The `scope-field` branch from the previous handoff is merged; the Critical and Important it named are no longer open on `main` (the suite is 145 green and `test_offer_with_no_trigger_scope_leaves_an_empty_box` is gone). Nothing is pushed to a remote.
- **The console's stage is Live when any register holds an item.** Baseline shows only before that. After the freeze the Source nav slot holds Rationalise with the unreviewed count as its badge. See `console/README.md` for the tabs.
- **"Unreviewed" is derived from `baseline/verdicts.json`**: an item frozen from a candidate with no verdict. Mark reviewed sets that candidate's verdict to Accept. Nothing about review is written into item files.
- **Merge and Delete exist and remove files**, direct mode only, through `commit()`. Links elsewhere are rewritten or dropped with a History line. Verified in a browser on `engagements/test`: freeze of 320 rows, new item, merge, mark reviewed, delete.
- **`engagements/abb-nokia/` lives only on the work laptop** (gitignored). Its `baseline/verdicts.json` carries the real review so far, 214 entries of which 211 attach to nothing. Its `engagement.md` declares sixteen scopes. Three candidates carry off-vocabulary scopes; the freeze now reports these rather than refusing.
- **`engagements/test/` on the local laptop is the anonymised copy.** Its verdicts file is keyed against stale candidate ids, so only one verdict attaches and a freeze writes all 320. That is test-data hygiene, not a console defect.
- **The push to Confluence is unchanged** and still has never run against a live connector.

## Next steps

1. **On the work laptop, pull `main` and freeze abb-nokia.** `make up ENG=engagements/abb-nokia`, Made by set, Freeze baseline. Done when the toast reports the counts, the stage reads Live and Rationalise shows its badge. Expect roughly 185 supports needed and three off-list scopes.
2. **Settle the three off-vocabulary scopes on the Rationalise Scopes tab.** `NBN TC4 Access` to `NbnTC4Access`; `Pool Management` to `Identifier and VLAN management`; `Location Management` needs the decision in open questions. Done when the Scopes tab is empty.
3. **Start raising new items straight away**; the freeze no longer blocks this. Done when the first item raised in the console has a `raised in console` History line.
4. **Rationalise in the gaps**: Duplicates tab first (twenty-odd groups), then Row by row with unreviewed only, then Missing supports. Done when the Rationalise badge is zero and the Missing supports count is zero or every remaining offer is dismissed with a reason.
5. **`make push-pages ENG=engagements/abb-nokia`, read the manifest, then `/push-confluence abb-nokia`.** Done when `confluence.json`'s log has a push entry and each pulled page's `page-version` holds the sent version.
6. **Run the engagement**: meetings from Outstanding and Work through, weekly SLT report. Done when the first meeting's moves show in the item files' History sections.

## Decisions taken on purpose

- **The freeze writes undecided candidates and the review continues over items.** Rejected: writing accepted only and keeping the rest as candidates (two workspaces alive at once); keeping the verdict gate (still blocks new items). Spec section "Decisions taken".
- **Unreviewed is the ledger's fact, not an item field.** Rejected: a `review` frontmatter key, which the ingester would have to learn.
- **Merge and Delete remove the file; git holds the history.** Rejected: marking the loser terminal and hiding it, which the push would still send.
- **Merge and Delete are direct-mode only.** The ingester has no block for either and is never edited from here.
- **Scope decisions from the previous handoff stand** (opt-in per engagement, required on create where declared, `scope` first in `M.SHORT`, `Domain` maps to Scope, Scope Taxonomy page skipped, stale verdicts kept).
- **Work on a branch in the main checkout, not a worktree**, because `engagements/` is gitignored and `make up` binds the current directory.

## Open questions for the user

- **What `Location Management` should become.** The taxonomy has no location concept in its sixteen values and TMF674 geographicSite fits none. Add a value (changing the client's page and `## Scopes`) or accept `Inventory and resources`. A statement about how the solution is carved up, not a tooling question.
- **Whether the Rationalise Missing supports tab should carry the four inline actions** (Accept, Edit then accept, Link existing, Dismiss) the spec described, or stay as the "Open and accept" jump to the drawer that was built.
- **Whether a Live engagement with no baseline folder should get Rationalise anyway**, for duplicates and off-list scopes among items raised by hand. Today the nav slot needs the baseline folder present.
- The earlier questions still stand: whether pushed tables carry Notes or History as columns, whether register gaps belong on the weekly SLT report, whether the "Baseline rejections" child page is created on the first push, and whether the engagement folder is committed after every meeting or once a week.

## Watch out for

- **`console/static/app.js` has no automated coverage.** The Rationalise view was rendered in a browser once, before the final fix that removed the row card's unwired controls; that last change has only a syntax check and a read behind it. The first real Rationalise session on abb-nokia is its second render.
- **A mixed-type duplicate group fails at the server** if "This one leads" is pressed with an item of another type ticked. Untick it. The coloured id prefix shows the type.
- **The Rationalise Duplicates tab shows the first 25 groups** and says so past 25.
- **`make sample` while the console is up** leaves the container mounted on a deleted folder; `make down` first.
- **The first `/api/state` after `make up` can be empty.** Wait a moment and retry.
- **Row by row keys are inert while a text field has focus**; click the page background first. Keys: `a` reviewed, `e` edit, `m` merge, `d` delete, `j`/`k`.
- The freeze stamps items with the source's raised dates, so the first SLT report reads high on "raised this week".

## Anchors

- files: console/baseline.py, console/server.py, console/static/app.js, console/items.py, console/model.py, console/tests/test_rationalise.py, console/tests/test_baseline_supports.py, console/push-pages.py
- docs: CLAUDE.md, console/README.md, console/confluence-runbook.md, console/static/guide.html, solution-register-model.md, docs/superpowers/specs/2026-09-15-rationalise-in-place-design.md, docs/superpowers/plans/2026-09-15-rationalise-in-place.md, docs/superpowers/specs/2026-09-14-scope-field-design.md
- config: confluence.json push.engagement, confluence.json permissions.write, confluence.json parent_page_url, engagements/abb-nokia/engagement.md `## Scopes` and `Writes` line
- external: `engagements/abb-nokia/` on the work laptop only, with its `baseline/verdicts.json` review ledger; the Confluence connector, still not configured; the sibling repository `solution-register` at model 2.20; `main` at aeb29e1 not pushed to any remote
