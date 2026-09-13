# design-register

Read `README.md` first for what is here and how the pieces fit. This file is what a session needs that the README does not say.

## What this repository is for

The solution architecture process for a vendor build, and the tools that make it cheap to run. Three things live here: the register model (`solution-register-model.md`, currently 2.26), the register console (`console/`), and the Confluence import path (`confluence.json`, `.claude/skills/import-confluence/`, `console/confluence-runbook.md`).

The sibling repository `../solution-register` holds the ingester that writes register item files from transcripts. It is at model 2.20 and is **never edited from here**. Adam ports the model to it when he chooses. The two repositories share nothing but the model document and the change set file format (model section 11).

## Rules that are not obvious from the code

- **The console has two write modes, chosen by `- Writes:` in `engagement.md`.** `direct`, the default, rewrites the item file on every move, edit or new item, stamps `updated` and appends a History line; git holds the history. `change-sets` appends blocks to `<engagement>/change-sets/CS-nnnn.md` for the ingester and never touches item files. Every Live write goes through `commit()` in `server.py`; do not add a write path beside it. Freeze baseline (`baseline.freeze`) is the same in both modes: it writes the accepted candidates as the registers' first item files, refuses to run if any register already has an item, and records the id map in `baseline/frozen.md`.
- **Everything runs in Docker.** `make up` builds and runs the console; `run.sh` refuses to start without Docker. Do not start a host python server as a fallback. If Docker is down, say so and ask. The only host tool used is `python3` for `make sample`, which writes files and runs no server.
- **The model is the source of truth.** `console/model.py` mirrors sections 4.2, 4.4 and 9 as data and is the only place the console knows the states, transitions, required fields and link words. A change to the model changes `model.py` and nothing else in the console needs to learn it. Bump the model version and add a dated line at the top of the model document.
- **Scope is declared per engagement, not by the model.** A `## Scopes` section in `engagement.md` names the values; an engagement without one carries no Scope, is never asked for one, and I24 never fires. `required_on_create()` in `server.py` is the only place that conditionality lives.
- **The Confluence import is gated.** `confluence.json` names the connector, the parent page and read and write permissions. `ask` means ask in chat and record the answer in `log`. Only the parent page and its direct children are ever read or written. No connector was available as of 12 September 2026, so no real pull has run.
- **The baseline never trusts its input.** In Baseline mode every table row is a candidate whatever id or status it claims. Source ids are kept as references in Notes and become our ids only at the freeze. A source status is kept at the freeze only if it is one of the model's own states for that type, otherwise the item starts at its first state; the reviewer can set the status in the candidate editor before freezing. Do not create the engagement folder or write placeholder pages when nothing was pulled.

## Layout worth knowing

| Path | Note |
|---|---|
| `console/server.py` | Standard library only. Reads items and change sets, overlays them, serves the API, and writes through `commit()` in the engagement's mode. `console/items.py` is the item file layout, parse and render, shared with the freeze. An item's `kind` in the API is its type; the risk's Kind field is exposed as `risk-kind`. A support dismissed in Live is recorded in `<engagement>/supports-dismissed.json`, never in a change set, so the ingester sees only blocks it knows. |
| `console/integrity.py` | Section 9 and the `SUPPORTS` table over item dicts. Pure; used by baseline and live. Rules read from `model.py` only. |
| `console/baseline.py` | Tolerant table import, duplicate suggestions, verdicts and edits in `baseline/verdicts.json`, freeze. Column heuristics are the `COLS` table at the top; add words there when a real page uses a header the mapping misses. `EDITABLE` lists what the editor may change. `skip-pages.txt` in the baseline folder names pages that produce no candidates. |
| `console/pull-page.py` | Converts one raw Confluence page JSON to the baseline page format. Run inside the console image. |
| `console/push-pages.py` | Builds the Confluence push from the registers as they stand into `<engagement>/push/` and sends nothing. Guarded by `push.engagement` in `confluence.json`, which names abb-nokia. `/push-confluence` sends the files. |
| `console/static/app.js` | One file, vanilla JS. Views: outstanding, triage, meeting report, weekly SLT report, baseline (tabs: candidates, duplicates, row by row, missing supports), one per register, change sets. `stage()` decides Baselining or Live and the opening view. `guide.html` is the lifecycle explanation served alongside and shares the theme choice. |
| `.claude/settings.json`, `.claude/hooks/` | A SessionStart hook prints the project's slash commands at the start of every session, read from each skill's `usage:` line. Add a `usage:` line to any new skill. |
| `handoffs/` | One file per objective written by `/handoff`, read by `/resume`, which checks relevance against the commit, anchors and date before acting. Start a session with `/resume` when a handoff is active. |
| `console/make-sample.py` | Writes `test-data/puppy-gloves`. Resets change sets and baseline verdicts. Sample baseline pages come from `console/sample-baseline/`. |
| `engagements/` | Real engagements, one folder each, created only by `/import-confluence`. |

## Testing the console

Chrome via the Claude in Chrome extension refuses `localhost` and `127.0.0.1`. Use `http://localtest.me:8085/`, which resolves to the machine. After a rebuild wait two seconds before loading, or the first fetch races the container start and the page renders blank. The API is quicker to check than the page: `curl localhost:8085/api/state` and `curl localhost:8085/api/baseline`. `make test` runs the console's unit tests in the python image, no browser needed.

## Conventions

Australian English. No em dashes. No rhyming patterns of three, no "not x but y" framing. Documents carry a version and date near the top and are bumped on change. Commits end with the attribution lines the session provides. Item files carry `updated` and a History section and rely on git for history.

## Where the thinking is

The model document's version notes at the top say why each change was made. The console README says what each mode does. `console/confluence-runbook.md` says how pull, baseline, apply and push fit together. The artifact "Two Ways Into the Registers" is the same content as `console/static/guide.html`.

## Open threads as of 14 September 2026

The active handoff `handoffs/baseline-abb-nokia.md` holds the ordered next steps for the real engagement; the threads below are the standing ones.

- Connect a Confluence connector and set `parent_page_url`, then run `/import-confluence <engagement>` for the first real pull. Expect to add column words to `COLS` in `baseline.py` on the first real page.
- The ingester still parses model 2.20. The model here is at 2.26. It is needed only by engagements in change-sets mode; direct mode is the default. Porting it (CR type, field trim, risk Kind, I20 forward transitions, change set apply stage, and the supports rules I21 to I23 with the link words `mitigated by` and `needs`) is Adam's call and happens in the other repository.
- The push back to Confluence is built (`push-pages.py` and `/push-confluence`) but has never run against a live connector. The first real run will show whether the connector's update call wants the body in storage format as written, and whether the version check reads as expected.
- `baseline/skip-pages.txt` names the pages that are views rather than registers. The test engagement has its four. On the first pull of a new source, expect to add them after seeing them.
