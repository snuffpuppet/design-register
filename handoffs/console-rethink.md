---
objective: console-rethink
title: Rethink the console on a model-driven table
written: 16 September 2026
commit: 0819d8d
branch: main
status: active
model-version: 2.29
---

> 19 September 2026: console behaviour changed on feature/rationalisation-meetings. Read current CLAUDE.md and docs/work-laptop-acceptance.md before following these historical next steps. Freeze is no longer a user-facing stage. Real engagement data was not changed by this feature.

## Objective

Replace the console's one-view-per-screen front end with one table, filtered and grouped, a side panel over it and a bulk bar above it, every state change going through one move form generated from `model.py`. Desk mode drives it: working a queue of changes after meetings and driving an import to zero integrity failures.

## Where things stand

- **All 15 tasks in the plan are done and committed on `console-rethink`, 15 commits ahead of `main`.** The build order in the spec ran task by task: model additions and provenance, the shell, the panel, the move form and status cell, the picker, selection and the bulk bar, the work queues and merge/delete as filters, views and reports and renumber, then this task's baselining hand-off and documentation.
- **The new front end is `console/static/{index.html,app.js,store.js,rail.js,table.js,cells.js,panel.js,move-form.js,picker.js,bulk.js,report.js}`**, Preact and htm from a pinned cdnjs build, no bundler. `console/model.py` carries `SPECIAL_ON_ENTRY`, `WITHDRAWS`, `BACKWARD`, `FORWARD` and a full `RULES` table; `console/views.py` and `console/renumber.py` are new. The server gained `/api/model`, `/api/needs`, `/api/items`, `/api/bulk`, `/api/views`, `/api/report/sections`, `/api/report/summary`, `/api/renumber`, `/api/push/build`, and `provenance` in `/api/state`.
- **Baselining still hands off to the previous console.** The new shell checks `Store.baseline.present && !Store.state.items.length`, the same test `/old/app.js`'s `stage()` uses, and shows a full-page notice with a link to `/old/` rather than porting the baseline screens (Duplicates, Row by row, Missing supports, Freeze). `console/static/old/` is kept for this; it is not dead code.
- **The theme switch and the Guide link now live in the new rail's foot**, copied from `old/app.js:401-414` so both consoles read and write the same `theme` localStorage key. `make test` passes, 179 tests.
- **`console/README.md`, `CLAUDE.md` and `console/static/guide.html` describe the new shape.** The README gained an API table (there was none before) and a full file list; `CLAUDE.md`'s layout table has one row per static module plus `views.py` and `renumber.py`.
- **abb-nokia is untouched by this branch.** `handoffs/baseline-abb-nokia.md` still holds its own next steps and was not read or edited beyond adding a cross-reference from `CLAUDE.md`'s open threads.

## Next steps

1. **On the work laptop, pull `main` and `make build && make up ENG=engagements/abb-nokia`.** Done when the console opens on the table with 179 items and `make test` passes there. The two regressions the final review's re-review found (Escape inside a panel field closing the panel; a stale `j`/`k` order after opening an item from a report) were fixed on `main` at the commit named above.
2. **Run the abb-nokia steps from `handoffs/baseline-abb-nokia.md` on the work laptop, now against the new console.** That engagement is Live already (179 items, frozen), so it opens straight on the table, not the baselining notice; check that Rationalise-era work (its Duplicates and Missing supports queues, in the new shape) still reads correctly there before relying on it for a real meeting.
3. **Spec items deferred by the final review**: hash routing (`#/view/<name>`, `#/item/<id>`) and the panel's Copy link; the has-link-word and raised-since filter chips; push scoped to the current view rather than the registers; a per-view column chooser (`Store.ui.columns` is declared but never written). None is needed to run abb-nokia.
4. **Port the baseline screens into the table shell**, the one piece the spec scoped out and this task left as a documented gap. Once Duplicates, Row by row, Missing supports and Freeze exist as table filters and the generated move form, `console/static/old/` and the `/old/` route can be deleted, and the baselining notice in `app.js` goes with them.
5. **Work the deferred minors.** The build ledger was deleted after the merge; the list below is what it held. None blocked a task; each was judged cheap to leave. The ones worth a look first: a self-linking item keeps a stale link after renumber and after a provenance walk, because both `rewrite_links` and the provenance walker skip an id linking to itself (Tasks 2 and 6, same root cause); `j`/`k` on the table walk id order even when the view is grouped, so keyboard order can disagree with what is on screen (Task 12); opening an item that is not in the current filter (a hop from a link) shows "0 of N" and the next arrow key jumps to the first row instead of stepping from where you were (Task 8). The rest are style and naming nits the ledger lists by task.

## Decisions taken on purpose

- **The baselining hand-off is a notice and a link, not a port.** The spec put Baseline mode out of scope and the plan's preflight scan ruled `old/` stays; this task's brief confirmed it. Reading `/api/baseline`'s `present` flag alongside `/api/state` was enough; no server change was needed since that endpoint already carried `present`.
- **`renumber()` moves every affected file through a temporary `kind-9nnn` id in two phases**, so a compacted id can never collide with a file still on disk mid-rename, and refuses outright if that staging range is already occupied (Task 6's ruling, tightening the plan's unguarded scheme).
- **`move_id` in `server.py` writes the renamed file directly rather than through `commit()`**, the one write path allowed beside it, because `commit()` keys a file on the item's id and cannot rename it. The docstring says so.
- **A provenance link with no id token is shown as dangling rather than dropped** (Task 2), so a malformed link is visible in the panel instead of silently missing.
- **Reports honour the full saved filter, not just types and statuses**, and a register tab folds its own type into the filter when saved (Task 13), both broader than the plan asked for.
- The build ledger with every ruling was deleted at the merge; the rulings that matter are the ones above. Remaining deferred minors: `needs()` repeats `transition()`'s disallowed-move message; bulk `set` passes request links through to `edit()`; report routes convert the overlay dict to a list and back; the empty table has no placeholder row; `.small` is redeclared in `style.css`; `Create()` and `Report()` return before their hooks; `guarded()` is duplicated per file; `make sample` leaves the sample Live; the duplicates count in the rail counts groups while the table counts items; `server.py`'s docstring still says model 2.22 and that item files are never written; `/api/state` carries a model copy the browser no longer reads.

## Open questions for the user

- **Whether to port the baseline screens next, or run the new console against abb-nokia first and let real use surface what the table shell is missing.** Both are reasonable; the ledger has no signal either way.
- **Whether `console/static/old/` should be deleted as soon as the port lands, or kept a while as a fallback.** The spec says delete it once every view it served exists in the new one; nothing says how long to wait after that.
- **Whether the deferred minors are worth their own clean-up pass**, or are better left until something depending on them actually breaks.

## Watch out for

- **The new front end has no automated coverage**, same as the old one; `make test` covers the server and the pure Python modules only. Every screen was checked in Chrome against `test-data/puppy-gloves` and `engagements/test`, with the check recorded in each task's report, but a regression in the browser will not show in `make test`.
- **`test-data/puppy-gloves` is not actually in the baselining stage after `make sample`.** It has a `baseline/` folder and register items both, so `Store.baseline.present && !items.length` is false there and it opens Live, not baselining. Checking the baselining notice needs an engagement with a baseline folder and no items yet, which this task did by temporarily emptying the sample's register folders and restoring them afterwards; nothing in the repository was left changed by that check beyond an unrelated pre-existing diff in `test-data/puppy-gloves/engagement.md`.
- **`make up` remembers the last pinned engagement** in `docker-compose.override.yaml`, so a bare `make up` after someone else's session can silently reopen their engagement rather than the one you meant. Pass `ENG=` explicitly when it matters.
- A running container serves stale python after a pull; `console/` is mounted over `/app`, so `make reload` is needed after a server change, `make down`/`make up` is not.
- **`engagements/test` carries uncommitted test fallout** from the browser checks: edited items, new CR-0058 and CR-0059, and a fixture `limitations/LIM-9001.md` that sits in renumber's staging range and would make Renumber REQ refuse there. Discard with `git checkout -- engagements/test && git clean -fd engagements/test` when convenient.
- The console is left running on `engagements/test` at the end of this session.

## Anchors

- files: console/static/app.js, console/static/store.js, console/static/rail.js, console/static/table.js, console/static/panel.js, console/static/move-form.js, console/static/bulk.js, console/static/report.js, console/model.py, console/views.py, console/renumber.py, console/server.py, console/static/old/app.js
- docs: README.md, ARCHITECTURE.md, console/README.md, CLAUDE.md, console/static/guide.html, solution-register-model.md, docs/superpowers/specs/2026-09-15-console-rethink-design.md, docs/superpowers/plans/2026-09-15-console-rethink.md, .superpowers/sdd/2026-09-15-console-rethink/progress.md
- config: none changed by this branch
- external: `main` branch to merge into; the work laptop's `engagements/abb-nokia`, out of scope for this branch and covered by `handoffs/baseline-abb-nokia.md`
