# solution-workflows

Read `README.md` first for what is here and how the pieces fit. This file is what a session needs that the README does not say.

## What this repository is for

The solution architecture process for a vendor build, and the tools that make it cheap to run. Three things live here: the register model (`solution-register-model.md`, currently 2.24), the register console (`console/`), and the Confluence import path (`confluence.json`, `.claude/skills/import-confluence/`, `console/confluence-runbook.md`).

The sibling repository `../solution-register` holds the ingester that writes register item files from transcripts. It is at model 2.20 and is **never edited from here**. Adam ports the model to it when he chooses. The two repositories share nothing but the model document and the change set file format (model section 11).

## Rules that are not obvious from the code

- **The console writes item files once, at the baseline freeze, and never again.** Every move, edit or new item appends a block to `<engagement>/change-sets/CS-nnnn.md`. The ingester applies change sets and assigns ids. The one exception is Freeze baseline (`baseline.freeze`), which writes the accepted candidates as the registers' first item files, refuses to run if any register already has an item, and records the id map in `baseline/frozen.md`. Do not add any other write path that touches `requirements/`, `decisions/` and so on.
- **Everything runs in Docker.** `make up` builds and runs the console; `run.sh` refuses to start without Docker. Do not start a host python server as a fallback. If Docker is down, say so and ask. The only host tool used is `python3` for `make sample`, which writes files and runs no server.
- **The model is the source of truth.** `console/model.py` mirrors sections 4.2, 4.4 and 9 as data and is the only place the console knows the states, transitions, required fields and link words. A change to the model changes `model.py` and nothing else in the console needs to learn it. Bump the model version and add a dated line at the top of the model document.
- **The Confluence import is gated.** `confluence.json` names the connector, the parent page and read and write permissions. `ask` means ask in chat and record the answer in `log`. Only the parent page and its direct children are ever read or written. No connector was available as of 12 September 2026, so no real pull has run.
- **The baseline never trusts its input.** In Baseline mode every table row is a candidate whatever id or status it claims. Source ids are kept as references in Notes and become our ids only at the freeze. A source status is kept at the freeze only if it is one of the model's own states for that type, otherwise the item starts at its first state; the reviewer can set the status in the candidate editor before freezing. Do not create the engagement folder or write placeholder pages when nothing was pulled.

## Layout worth knowing

| Path | Note |
|---|---|
| `console/server.py` | Standard library only. Reads items and change sets, overlays them, serves the API, appends blocks. An item's `kind` in the API is its type; the risk's Kind field is exposed as `risk-kind`. |
| `console/baseline.py` | Tolerant table import, duplicate suggestions, verdicts and edits in `baseline/verdicts.json`, freeze. Column heuristics are the `COLS` table at the top; add words there when a real page uses a header the mapping misses. `EDITABLE` lists what the editor may change. `skip-pages.txt` in the baseline folder names pages that produce no candidates. |
| `console/pull-page.py` | Converts one raw Confluence page JSON to the baseline page format. Run inside the console image. |
| `console/push-pages.py` | Builds the Confluence push from a frozen engagement into `<engagement>/push/` and sends nothing. Guarded by `push.engagement` in `confluence.json`, which names abb-nokia. `/push-confluence` sends the files. |
| `console/static/app.js` | One file, vanilla JS. Views: outstanding, triage, report, baseline, one per register, change sets. `guide.html` is the lifecycle explanation served alongside. |
| `console/make-sample.py` | Writes `test-data/puppy-gloves`. Resets change sets and baseline verdicts. Sample baseline pages come from `console/sample-baseline/`. |
| `engagements/` | Real engagements, one folder each, created only by `/import-confluence`. |

## Testing the console

Chrome via the Claude in Chrome extension refuses `localhost` and `127.0.0.1`. Use `http://localtest.me:8085/`, which resolves to the machine. After a rebuild wait two seconds before loading, or the first fetch races the container start and the page renders blank. The API is quicker to check than the page: `curl localhost:8085/api/state` and `curl localhost:8085/api/baseline`.

## Conventions

Australian English. No em dashes. No rhyming patterns of three, no "not x but y" framing. Documents carry a version and date near the top and are bumped on change. Commits end with the attribution lines the session provides. Item files carry `updated` and rely on git for history.

## Where the thinking is

The model document's version notes at the top say why each change was made. The console README says what each mode does. `console/confluence-runbook.md` says how pull, baseline, apply and push fit together. The artifact "Two Ways Into the Registers" is the same content as `console/static/guide.html`.

## Open threads as of 12 September 2026

- Connect a Confluence connector and set `parent_page_url`, then run `/import-confluence <engagement>` for the first real pull. Expect to add column words to `COLS` in `baseline.py` on the first real page.
- The ingester still parses model 2.20. Porting 2.23 (CR type, field trim, risk Kind, I20 forward transitions, change set apply stage) is Adam's call and happens in the other repository.
- The push back to Confluence is built (`push-pages.py` and `/push-confluence`) but has never run against a live connector. The first real run will show whether the connector's update call wants the body in storage format as written, and whether the version check reads as expected.
- `baseline/skip-pages.txt` names the pages that are views rather than registers. The test engagement has its four. On the first pull of a new source, expect to add them after seeing them.
