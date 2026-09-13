---
objective: baseline-abb-nokia
title: Baseline the abb-nokia registers from Confluence and start running them
written: 13 September 2026
commit: dbfaff2
branch: main
status: active
model-version: 2.24
---

## Objective

Turn the registers already held in the oss-kb Confluence Design Register, part pipeline-generated and part hand-written, into the abb-nokia engagement's starting registers: reconcile and de-duplicate them in the console, correct what is at the wrong altitude, freeze the result as item files, push the frozen tables back to the same Confluence pages, and from then on run the engagement through meetings with every change as a change set. The real engagement folder lives only on the work machine, where Opus is the available model; this repository is where the tooling is built and tested against a transposed copy called `test`.

## Where things stand

- The console's Baseline mode does the whole reconciliation: skip list for view pages, duplicate groups with a leader, row-by-row pass with keys, bulk field fixes, an editor per candidate, and Freeze, which writes item files once into empty registers and records the id map. Verified in Chrome on the test engagement and on a scratch copy that was frozen with 300 items.
- The push back to Confluence is built as two halves: `make push-pages` builds storage bodies into `engagements/<name>/push/` and refuses anything but the engagement named in `confluence.json` under `push.engagement` (abb-nokia); `/push-confluence` sends them under the write gate. The send half has never met a live connector.
- The console is stage-aware (Baselining until the freeze, Live after), has grouped navigation, a weekly SLT report beside the meeting report, one sans typeface, and a Light/Auto/Dark switch.
- ARCHITECTURE.md, README.md, CLAUDE.md, the console README, the runbook and the guide page all describe the above. The commit named above is the last of twelve from the session of 12 September 2026; the remote is shared with the work machine and only the user pushes and pulls.
- Nothing has been run against the real abb-nokia folder since these changes. Its `verdicts.json` from Opus's earlier work should reparse under the new code without change.

## Next steps

1. On the work machine: pull, then `make up ENG=engagements/abb-nokia`. Done when the console opens on Baseline with the real candidate count and no page renders blank.
2. Name the view pages: filter to each summary or conventions page and press Treat as a view. Done when `engagements/abb-nokia/baseline/skip-pages.txt` lists them and the duplicates tab shows only real groups.
3. Check the column mapping on the real pages: any field landing in Notes that should be a field means a word to add to `COLS` in `console/baseline.py`. Done when Owner, Status, MoSCoW and Phase fill for the register pages.
4. Work the baseline to zero undecided using the order in the Baseline view's note. Freeze. Done when `baseline/frozen.md` exists and the register tabs show items.
5. `make push-pages ENG=engagements/abb-nokia`, read the manifest, then `/push-confluence abb-nokia`. The first real send will show whether the connector's update call takes the storage body as built and how it reports versions; expect to adjust the skill's send step. Done when the log in `confluence.json` has a push entry.
6. Start running the engagement: Made by set, meetings from Outstanding and Work through, weekly SLT report. Change sets accumulate for the ingester.

## Decisions taken on purpose

- The baseline produces a register (item files at the freeze), not a change set. Rejected: exporting the accepted set as one change set for the ingester to apply, which left the engagement empty until another machine ran the ingester and pushed 300 items through a path built for a meeting's worth of changes.
- The push builds to files first and only the named engagement can be pushed. Rejected: guessing the engagement from the folder, which would let a test copy reach Confluence.
- View pages are named by a person in `skip-pages.txt`, never guessed from their content.
- One typeface (Inter) with mono for ids; the serif was dropped as clunky.

## Open questions for the user

- Whether the pushed tables should carry Notes as a column. They carry ID, Title, Status, the type's short fields, dates, Links, Source and Source id; Notes was left out to keep the page readable.
- Whether the "Baseline rejections" child page should be created on the first push or held back until the pipeline owner asks for it.

## Watch out for

- The first week's SLT report after a freeze reads high on "raised this week", because the freeze stamps items with the source's raised dates.
- A page pulled without a `.raw` audit copy is rebuilt from markdown on push and loses formatting the pull flattened; the manifest flags it per page.
- Clicking a nav link in Chrome straight after load can land before the first render; wait two seconds after `make up`.

## Anchors

- files: console/baseline.py, console/server.py, console/static/app.js, console/push-pages.py, .claude/skills/push-confluence/SKILL.md, .claude/skills/import-confluence/SKILL.md
- docs: CLAUDE.md, ARCHITECTURE.md, console/confluence-runbook.md
- config: confluence.json push.engagement, confluence.json permissions.write, confluence.json parent_page_url
- external: engagements/abb-nokia on the work machine; the Confluence connector in that session; the sibling repository solution-register at model 2.20
