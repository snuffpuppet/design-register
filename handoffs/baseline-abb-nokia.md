---
objective: baseline-abb-nokia
title: Baseline the abb-nokia registers from Confluence and start running them
written: 15 September 2026
commit: f910549
branch: main
status: active
model-version: 2.28
---

## Objective

Turn the registers held in the oss-kb Confluence Design Register into the abb-nokia engagement's working registers and run the engagement from them. The freeze has now happened, so the remaining work is rationalising in place while new items are raised, pushing the tables back to Confluence, and writing every meeting's changes straight into the item files.

**Read this first: abb-nokia is frozen.** The registers hold 179 items and the console is Live. Steps 1 and 2 of the previous handoff are done. Do not look for a baseline to work; look at the Rationalise view over the item files.

## Where things stand

- **The freeze ran on 15 September 2026** and wrote 179 items: REQ 74, CR 42, DEC 26, LIM 17, OI 16, RSK 4. Zero rejected, zero unreviewed. `baseline/frozen.md` holds the id map and the counts. The freeze also stamps `frozenAs` into each accepted candidate in `baseline/verdicts.json`, so the ledger now records which item each row became.
- **The review was already complete before the freeze.** All 320 candidates carried a verdict: 179 Accept, 134 Discard, 7 Merge. The previous handoff's figures (214 verdicts, 211 attaching to nothing, roughly 185 supports, three off-list scopes) were stale by the time it was read. The ledger's 531 entries include 211 orphans from earlier candidate id churn; they are harmless.
- **Both off-vocabulary scopes are settled and I24 is zero.** DEC-0026 moved from `NBN TC4 Access` to the declared `NbnTC4Access`. CR-0009 moved from `Location Management` to a new seventeenth value, `Location and site management`, now in `## Scopes`. Both writes went through the console and carry History lines.
- **`engagement.md` is at version 0.2** and its `Model version` line was corrected from 2.27 to 2.28.
- **Nothing is committed.** `engagements/abb-nokia` sits at `c7c90bc` with the six register folders, `baseline/frozen.md` and `baseline/rejections.md` untracked, and `engagement.md` and `baseline/verdicts.json` modified. The main repository is clean at `f910549` and is not pushed to any remote.
- **Rationalise has 10 duplicate groups and 108 support suggestions** (S8 41, S1 33, S7 20, S2 10, S17 4). Integrity shows 554 failures, which is the ordinary shape of an import rather than a defect: I3 184, I2 142 and I5 105 are missing owners, dates and approvers on rows that never carried them.
- **`baseline/rejections.md` is an empty table**, because nothing was rejected. The first push has no rejections to publish.
- **The push to Confluence is unchanged** and still has never run against a live connector.

## Next steps

1. **Commit the engagement repository.** `git -C engagements/abb-nokia add -A && git -C engagements/abb-nokia commit`. Done when the freeze has a rollback point and `git status` there is clean. This is the first thing, because every step below writes item files.
2. **Work the Rationalise Duplicates tab**, ten groups. Done when the tab is empty or each remaining group is set aside in `duplicates-dismissed.json`.
3. **Work Missing supports**, 108 suggestions. Done when the count is zero or every remaining offer is dismissed with a reason.
4. **Add `Location and site management` to the client's Scope Taxonomy page in Confluence by hand.** That page is named in `baseline/skip-pages.txt`, so the push will not carry the new value. Done when the client's page and `## Scopes` agree.
5. **`make push-pages ENG=engagements/abb-nokia`, read the manifest, then `/push-confluence abb-nokia`.** Done when `confluence.json`'s log has a push entry and each pulled page's `page-version` holds the sent version.
6. **Run the engagement**: meetings from Outstanding and Work through, weekly SLT report. Done when the first meeting's moves show in the item files' History sections.

New items can be raised at any point from here; nothing above blocks them.

## Decisions taken on purpose

- **CR-0009 got a new scope value rather than an existing one.** Rejected: `Inventory and resources`, which is declared and holds no items, and `UIV service and resource model`. Adam's call, on the grounds that location and site management is a distinct carve of the solution. The cost is that the client's taxonomy page changes.
- **DEC-0026's `NBN TC4 Access` was mapped, not added.** It was a spelling of the declared `NbnTC4Access`, not a new concept.
- **The freeze was driven through `POST /api/baseline/freeze` with curl, not the browser.** Faster and the result is the same write path. The consequence is under "Watch out for".
- Decisions from the previous handoff stand: the freeze writes undecided candidates and the review continues over items; unreviewed is the ledger's fact rather than an item field; merge and delete remove the file and are direct-mode only; scope is opt-in per engagement; work on a branch in the main checkout rather than a worktree, because `engagements/` is gitignored and `make up` binds the current directory.

## Open questions for the user

- **Whether the engagement folder is committed after every meeting or once a week.** Live now, with 179 files uncommitted.
- **Whether the Rationalise Missing supports tab should carry the four inline actions** (Accept, Edit then accept, Link existing, Dismiss) the spec described, or stay as the "Open and accept" jump to the drawer that was built.
- **Whether a Live engagement with no baseline folder should get Rationalise anyway**, for duplicates and off-list scopes among items raised by hand. Today the nav slot needs the baseline folder present.
- Whether pushed tables carry Notes or History as columns, and whether register gaps belong on the weekly SLT report.
- Whether the "Baseline rejections" child page is created on the first push at all, given the table is empty.

## Watch out for

- **The Rationalise view has still never been rendered against abb-nokia.** The freeze and both scope edits went through the API, so the first person to open the Rationalise tabs on the real engagement is doing its second render ever, after a fix that has only a syntax check behind it. `console/static/app.js` has no automated coverage.
- **A running container serves stale python after a pull.** `console/` is mounted over `/app`, so a container left up for a day keeps its old `server.py` process. `make reload` after pulling, or the freeze runs on old code.
- **Do not pipe curl output through `echo "$var"` in zsh**; it expands the literal `\n` inside JSON strings and corrupts it. `curl -o file` instead. The API output itself is clean.
- **A mixed-type duplicate group fails at the server** if "This one leads" is pressed with an item of another type ticked. Untick it. The coloured id prefix shows the type.
- **The Rationalise Duplicates tab shows the first 25 groups** and says so past 25.
- **`make sample` while the console is up** leaves the container mounted on a deleted folder; `make down` first.
- **The first `/api/state` after `make up` can be empty.** Wait a moment and retry.
- **Row by row keys are inert while a text field has focus**; click the page background first. Keys: `a` reviewed, `e` edit, `m` merge, `d` delete, `j`/`k`.
- The freeze stamped items with the source's raised dates, so the first SLT report reads high on "raised this week".

## Anchors

- files: console/baseline.py, console/server.py, console/static/app.js, console/items.py, console/model.py, console/tests/test_rationalise.py, console/tests/test_baseline_supports.py, console/push-pages.py
- docs: CLAUDE.md, console/README.md, console/confluence-runbook.md, console/static/guide.html, solution-register-model.md, docs/superpowers/specs/2026-09-15-rationalise-in-place-design.md, docs/superpowers/plans/2026-09-15-rationalise-in-place.md
- config: confluence.json push.engagement, confluence.json permissions.write, confluence.json parent_page_url, engagements/abb-nokia/engagement.md `## Scopes` and version line, engagements/abb-nokia/baseline/skip-pages.txt
- external: `engagements/abb-nokia/` on the work laptop only, its own git repository at `c7c90bc` with the freeze uncommitted; the client's Confluence Scope Taxonomy page, which does not yet carry `Location and site management`; the Confluence connector, still not configured; the sibling repository `solution-register` at model 2.20; `main` at `f910549` not pushed to any remote
