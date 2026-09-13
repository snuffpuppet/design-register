---
objective: baseline-abb-nokia
title: Baseline the abb-nokia registers from Confluence and start running them
written: 14 September 2026
commit: 4e864ab
branch: main
status: active
model-version: 2.26
---

## Objective

Turn the registers already held in the oss-kb Confluence Design Register, part pipeline-generated and part hand-written, into the abb-nokia engagement's starting registers: reconcile and de-duplicate them in the console, correct what is at the wrong altitude, freeze the result as item files, push the frozen tables back to the same Confluence pages, and from then on run the engagement through meetings with every change written straight into the item files and pushed back. The real engagement folder lives only on the work machine, where Opus is the available model; this repository is where the tooling is built and tested against a transposed copy called `test` and the sample `test-data/puppy-gloves`.

## Where things stand

- The console's Baseline mode does the whole reconciliation and is verified in Chrome on the test engagement and the sample: a skip list for pages that are views, duplicate groups with a leader, a Row by row tab with keyboard verdicts, bulk field fixes, an editor per candidate, and Freeze, which writes item files once into empty registers and records the id map. Baseline mode writes nothing but `baseline/verdicts.json` and `skip-pages.txt`, whatever the engagement's write mode.
- The supports engine (model 2.25, `console/integrity.py`) offers every record an accepted row's state implies, on the Missing supports tab and in Live. Verdicts are Accept, Edit then accept, Link existing, Dismiss with a reason, and for limitations Reconstruct or Reassess. Link existing (14 September 2026) lists the accepted candidates, or live records, of the offered type whose title shares a word with the trigger, with a datalist for the rest; one click writes the link and the reverse where the model names one, creating nothing. The freeze refuses while a failure-level offer is undecided.
- Live writes are in place by default (model 2.26, 14 September 2026). With no `- Writes:` line in `engagement.md` the console rewrites the item file on every move, edit or new item, stamps `updated` and appends a History line; `- Writes: change-sets` restores the block-appending path for the ingester. Every write goes through `commit()` in `console/server.py`. Verified in Chrome on the sample and by 95 unit tests (`make test`). CLAUDE.md states the rule.
- The push builds from the registers as they stand (`make push-pages`), with `frozen.md` optional and used for the Source id column when present. `/push-confluence` sends under the write gate, checks each page's version against the pulled `page-version`, and after a send writes the new version back into that line so a second push is not refused. The send half has never met a live connector.
- The console is stage-aware, has grouped navigation, a weekly SLT report, one sans typeface, a Light/Auto/Dark switch, and a banner that says which write mode is in force. Close session is hidden in direct mode. The container clock runs in Australia/Sydney.
- Nothing has been run against the real abb-nokia folder since these changes. Its `verdicts.json` reparses under the new code; its view pages are not yet named; its `change-sets/` folder is empty, so there is nothing to fold in. The ten commits from ebf2244 to 4e864ab are on main and not yet pushed; only the user pushes and pulls.

## Next steps

1. Push from this machine. On the work machine: pull, open `/hooks` once so the command list appears, then `make up ENG=engagements/abb-nokia`. Done when the console opens on Baseline with the real candidate count and no page renders blank.
2. Name the view pages: filter to each summary or conventions page and press Treat as a view. Done when `engagements/abb-nokia/baseline/skip-pages.txt` lists them and the duplicates tab shows only real groups.
3. Check the column mapping on the real pages: any field landing in Notes that should be a field means a word to add to `COLS` in `console/baseline.py`. Done when Owner, Status, MoSCoW and Phase fill for the register pages.
4. Work the baseline to zero undecided: duplicates tab first, then Row by row per register page, then bulk field fixes. Done when Row by row shows nothing undecided.
5. Work Missing supports to zero failures. Expect S8 to fire for every vendor CR without a trigger and S5 for every limitation the source calls Accepted with no decision behind it. Where the decisions register already holds the decision, use Link existing; Reconstruct where the row carries a rationale and nothing exists; Reassess where it carries nothing. Set owners on offered requirements from the stakeholder register. Freeze. Done when `baseline/frozen.md` exists and the register tabs show items.
6. `make push-pages ENG=engagements/abb-nokia`, read the manifest, then `/push-confluence abb-nokia`. The first real send will show whether the connector's update call takes the storage body as built and how it reports versions; expect to adjust the skill's send step. Done when the log in `confluence.json` has a push entry and each pulled page's `page-version` holds the sent version.
7. Run the engagement: Made by set, meetings from Outstanding and Work through, weekly SLT report. Each change rewrites its item file with a History line; commit the engagement folder in git as the record, and push to Confluence again when the pages should catch up. Done when the first meeting's moves show in the item files' History sections and the next push carries them.

## Decisions taken on purpose

- Direct writes are the default (14 September 2026): the console rewrites item files in place with a History line, and change sets stay as a per-engagement mode for when the ingester is ported. Rejected: keeping change sets as the only Live path, which left the engagement unable to move until another machine ran an ingester that has not been ported; and writing both, which gives the ingester two sources of truth to reconcile.
- Freeze stays as the one way registers are created from a pull. Rejected: writing item files straight from accepted candidates as you go, which loses the single moment where ids are assigned in order and the id map the push relies on is written.
- No stale-write check in direct mode: the console is single-user and git shows a collision.
- Link existing matches on title tokens only, no model call; the datalist covers what the heuristic misses. A wrong top match was seen on the sample and is why a person clicks.
- The baseline produces a register (item files at the freeze), not a change set.
- The push builds to files first and only the engagement named in `confluence.json` can be pushed.
- View pages are named by a person in `skip-pages.txt`, never guessed from their content.
- Duplicate suggestion needs two shared title words and ignores common verbs.
- An accepted limitation still needs a DEC; a change-requested one needs only the CR. Offers arrive in their first state with Approved by empty.
- Live dismissals live in `supports-dismissed.json`, not in a change set block or an item file.

## Open questions for the user

- Whether the pushed tables should carry Notes or History as columns. They carry ID, Title, Status, the type's short fields, dates, Links, Source and Source id.
- Whether register gaps belong on the weekly SLT report at all; they are one line per rule today.
- Whether the "Baseline rejections" child page should be created on the first push or held back until the pipeline owner asks for it.
- Whether the engagement folder on the work machine should be committed after every meeting or once a week; the History lines make either readable.

## Watch out for

- The first week's SLT report after a freeze reads high on "raised this week", because the freeze stamps items with the source's raised dates.
- A page pulled without a `.raw` audit copy is rebuilt from markdown on push and loses formatting the pull flattened; the manifest flags it per page.
- Clicking a nav link in Chrome straight after load can land before the first render; wait two seconds after `make up`. The retry loop swallows render errors, so a page that stays blank with "Reconnecting" is usually a JS exception: run `loadOnce()` in the page console to see it.
- The Row by row keys are inert while a text field has focus; click the page background first.
- Running `make sample` while the console is up leaves the container's mount on the deleted folder and every write fails; `make down` first.
- I17's later-phase check only tests that Phase is set; the engine has no current-phase input. A dismissed live support has no undo in the UI; remove its key from `supports-dismissed.json`.
- Old change set files under an engagement in direct mode are still overlaid for reading and never applied; their items stay amber and provisional. abb-nokia has none.
- The first real pages may need column words in `COLS` for Chosen option and Options before S5 and S6 templates read well; "Disposition record" is already mapped to the dispositioned by link.

## Anchors

- files: console/model.py, console/integrity.py, console/baseline.py, console/items.py, console/server.py, console/static/app.js, console/push-pages.py, docker-compose.yaml, .claude/skills/push-confluence/SKILL.md, .claude/skills/import-confluence/SKILL.md
- docs: CLAUDE.md, ARCHITECTURE.md, console/confluence-runbook.md, solution-register-model.md, docs/superpowers/specs/2026-09-14-direct-writes-design.md, docs/superpowers/specs/2026-09-13-supports-engine-design.md
- config: confluence.json push.engagement, confluence.json permissions.write, confluence.json parent_page_url, engagements/abb-nokia/engagement.md Writes line (absent means direct)
- external: engagements/abb-nokia on the work machine; the Confluence connector in that session; the sibling repository solution-register at model 2.20
