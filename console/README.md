# Register console

Version 0.6, 16 September 2026.

A lifecycle console for the registers in `solution-register-model.md` (2.29). It reads an engagement folder, overlays any unapplied change sets, and writes every move, edit or new item in the engagement's mode. `- Writes: direct` in `engagement.md`, the default when the line is absent, rewrites the item file, stamps `updated` and appends a line to its History section; git is the record. `- Writes: change-sets` appends one item block to the current session's change set under `<engagement>/change-sets/` for the ingester in `solution-register` to apply (model section 11). The baseline freeze writes the registers' first item files in either mode.

An engagement may declare its scopes in a `## Scopes` section of `engagement.md`, one value per line, the same shape as `## Phases`. Where it does, every item carries a Scope from that list, a new item cannot be created without one, the register views gain a scope filter and the pushed tables gain a Scope column. Where it does not, Scope does not exist for that engagement: nothing asks for it, no rule checks it, and the pushed tables are as they were.

## Run

```
make sample                        # writes test-data/puppy-gloves (re-run to reset)
make up                            # build and run in Docker; http://localhost:8085/
make up ENG=engagements/acme PORT=8090
make test                          # runs the console's unit tests in the python image
make down | restart | logs | status | clean
```

`console/run.sh [engagement-dir] [port]` does the same as `make up` without make.

Only the Python standard library is used. Nothing is installed on the host.

If the console is up when `make sample` regenerates the test engagement, the running container's bind mount is left pointing at the deleted folder and every write fails. Run `make down` first, then `make sample`, then `make up`.

## What it shows

The console is one table of items, filtered and grouped, with a side panel over it and a bulk bar above it when anything is selected. Every write, single or bulk, goes through one move form generated from `model.py`, so it asks only for what the move needs. The rail's Work queues, Registers and a rule's failing items are all the same table with a different fixed filter and a different set of editable columns; there is no separate Outstanding page, Rationalise view or Triage view.

The console knows its stage: **Baselining** while the baseline folder is present and no register holds an item; **Live** from the first item. While baselining, the table shell shows a full-page notice and hands off to the previous console at `/old/`, which still runs the baseline screens (Duplicates, Row by row, Missing supports, Freeze) until the freeze. Everything below describes the Live shell.

- **The rail**: the engagement name; Work queues with counts (Outstanding, Integrity expanding to one line per rule, Suggested supports, Duplicates, Unreviewed); Registers (All items and one per type, with counts and a per-register ⋯ menu offering Renumber); Reports (saved views, then Save current view); and, in the foot, a Guide link and the Light/Auto/Dark theme switch.
- **The table**: columns are chosen per view and default to id, title, status, scope, owner, one type-specific field, link count and issue count. Filter chips cover type, status, scope, owner, failing rule, raised since, updated since and free text over title, id and notes; group-by is none, type, status, scope, owner or rule. A cell edits on click: text and date cells inline, choice cells as a list, the status cell as the list of states for the type with the unreachable ones greyed and each reachable one's needs named beside it. Choosing a reachable state that needs nothing writes at once; choosing one that needs something opens the move form. Selection is a checkbox column, `x` on the focused row, Shift-click for a range and a header checkbox for the visible rows. Keyboard: `j`/`k` move focus, `x` selects, Enter opens the panel, `e` edits the title, `m` opens the status list, `/` focuses search, Esc clears selection or closes whatever is open; keys are inert while an input has focus.
- **The side panel**: opens over the right of the table; the row stays highlighted behind it. Left column: title and chips as inline editors, Next moves with each move's needs written beside it, the long fields, History. Right column: provenance, walked backward (Where it came from) and forward (What it produces) through the link words the model derives, with a Pick button on a dashed slot for a link a later state will need; Gaps, the item's integrity failures and support offers by rule id. Link to, Merge into and More (Delete, Mark reviewed, Copy link) sit in the header. Up and down arrows step to the neighbouring row in the table's current order.
- **The move form**: opens for a status change from any tier (cell, panel or bulk bar) and for New item. Shared fields are those the target state requires on every selected item and that agree or are empty across them; per-item rows list each item's own remaining gaps. Apply is enabled only once nothing is missing. A bulk request is applied item by item on the server; the first refusal stops the run and the form shows what was written and what was not.
- **The bulk bar**: Set field, Move to (through the move form), Link to (a picker, then one link written on each item), Merge (fold the rest into a chosen survivor), Withdraw (the type's withdrawing terminal state, through the move form) and Delete (confirm with the count). Merge and Delete are direct-mode only and refuse in change-sets mode, as they always have.
- **Work queues as filters**: Outstanding is model section 8's non-terminal items; Integrity expands to one line per rule and filters to its failing items with the failing field as an editable column; Suggested supports and Duplicates are the supports engine and the duplicate clusters as filters; Unreviewed is the baseline ledger's unreviewed ids. A dismissal from Suggested supports is recorded in `<engagement>/supports-dismissed.json` (rule, item, reason, who, when); a duplicate group set aside is recorded in `<engagement>/duplicates-dismissed.json`.
- **Saved views and reports**: a saved view is a name, filter, column list and sections list in `<engagement>/views.json`. It renders as sections; a table section takes the view's columns, and a summary section (Moved since, Raised since, Outstanding, Register gaps) is text the SLT weekly view is built from. Copy email summary drafts plain text from the sections for editing before it is copied; Push to Confluence builds the pages for the current view through `push-pages.py` and hands off to the existing write gate.
- **Renumber**: a per-register menu command. It compacts that register's ids in raised-on order, rewrites every link in every register that named a renamed id, writes a History line on each renamed item, and records the old to new map in `<engagement>/renumbered.md`. It refuses in change-sets mode and refuses on a dirty working tree in the engagement folder, so there is always a rollback point.

`views.json` and `renumbered.md` are direct-mode files: they are written straight to the engagement folder in either write mode and never go through a change set, the same way `supports-dismissed.json` and `duplicates-dismissed.json` do.

## API

`/api/state` carries `provenance` per item, the backward and forward link chains resolved to ids and words, so the panel does not walk links in the browser. Every write endpoint takes `madeBy` and stamps `updated` and a History line through `commit()`, except renumber, merge and delete, which write their own History lines for the reason each names.

| Endpoint | Does |
|---|---|
| `GET /api/state` | Items, stakeholders, integrity failures, provenance, duplicate clusters, unreviewed ids, change sets, today's date and the state model. |
| `GET /api/baseline` | `present`, candidates, clusters, suggestions and `frozen` for the baseline folder, or `present: false` when there is none. |
| `GET /api/model` | `STATES`, `TERMINAL`, `TRANSITIONS`, `SHORT`, `LONG`, `LABELS`, `CHOICES`, `REQUIRED_ON_ENTRY`, `REQUIRED_ON_CREATE`, `LINK_WORDS`, `RULES`, `FIRST_STATE`, the engagement's scopes and owners, and the special-case rules held as data. |
| `GET /api/items?q=&types=&exclude=` | The picker's search: id or title contains `q`, restricted to the given types. Served from the loaded state. |
| `GET /api/views` / `POST /api/views` | Read and write `<engagement>/views.json`, a list of `{name, filter, columns, sections, groupBy}`. The POST refuses outside direct mode. |
| `POST /api/needs` | `{ids, to}`; the missing fields and links per id for that move, computed by `missing_for` with no fields applied. The move form draws itself from this. |
| `POST /api/transition` / `POST /api/create` / `POST /api/edit` | The single-item writes: move a state, create an item, edit fields, each through `commit()`. |
| `POST /api/bulk` | `{ids, op, ...}` where `op` is `set`, `transition`, `link` or `withdraw`. Runs the matching single operation per id under one lock, stops at the first failure, returns `{written, failed}`. Refuses in change-sets mode. |
| `POST /api/renumber` | `{type, madeBy}`. Refuses in change-sets mode or on a dirty working tree. Writes every affected file through `commit()`, writes `renumbered.md`, returns the old to new map. |
| `POST /api/merge` / `POST /api/delete` | Fold the loser into a survivor, or remove an item, rewriting links that named it either way. Direct-mode only. |
| `POST /api/report/summary` | `{view}`; the drafted email text for that saved view, assembled on the server so it is testable. |
| `POST /api/report/sections` | `{view}`; the view's sections (table rows and summary text) for the report renderer. |
| `POST /api/push/build` | Builds the Confluence push for the current engagement into `<engagement>/push/` from `confluence.json`. Sends nothing. |
| `POST /api/close-session` | Stamps the open change set `Session closed` so the ingester can pick it up. |
| `POST /api/support/accept` / `POST /api/support/dismiss` / `POST /api/support/link` | Accept a suggested support, dismiss it with a reason to `supports-dismissed.json`, or point it at an existing item instead of creating one. |
| `POST /api/rationalise/not-duplicates` / `POST /api/rationalise/reviewed` | Set aside a duplicate cluster to `duplicates-dismissed.json`, or mark a frozen item reviewed in the baseline ledger. |
| `POST /api/baseline/*` | Baseline-mode writes: verdicts, skip-page, not-duplicates, support, export and freeze. Unchanged; still served for `/old/`. |

## What it writes

One file per maker per session, `CS-nnnn.md`. Header per section 11; blocks in the dossier item-block shape with `Target`, `From`, `Based on`, the changed fields, `Links`, `Evidence` lines and a `Gist`. "Close session" stamps `Session closed` so the ingester can pick the file up and a later edit starts a new set. `Approver` and `Applied on` are the ingester's to fill. A duplicate group set aside from the Duplicates queue is recorded as the sorted id list in `<engagement>/duplicates-dismissed.json`.

## Files

| File | Purpose |
|---|---|
| `model.py` | The model as data: states, transitions, required fields, link words, the `SUPPORTS` table, `SPECIAL_ON_ENTRY`, `WITHDRAWS`, `BACKWARD`, `FORWARD` and `RULES`. The only place the console knows the model. |
| `integrity.py` | Section 9, the `SUPPORTS` table and the provenance chains over item dicts. Pure; used by baseline and live. Rules read from `model.py` only. |
| `server.py` | Reads items and change sets, overlays them, serves the API, writes through `commit()` in the engagement's mode. |
| `items.py` | The item file layout: `parse_item` and `render_item`, shared by the server and the freeze. |
| `views.py` | Saved views: load and save `views.json`, apply a view's filter, render its sections, draft the summary text. |
| `renumber.py` | Compacting a register's ids in two phases through a temporary id, rewriting links, and writing `renumbered.md`. |
| `baseline.py` | Baseline mode: tolerant table import, duplicate suggestions, verdicts, edits, freeze. |
| `static/index.html` | Header, rail slot, table slot, panel slot. Loads Preact 10 and htm 3 from cdnjs by exact version. |
| `static/store.js` | Client state: items, model, views, baseline presence, filter, selection, open item. Every write calls the API then reloads state. |
| `static/rail.js` | The left rail: engagement, Work queues, Registers with the renumber menu, Reports, the theme switch and the Guide link. |
| `static/table.js` | The table: columns, filter chips, group-by, sort, selection, keyboard. |
| `static/cells.js` | One editor per field kind: text, choice, status, date, owner, scope, links. |
| `static/panel.js` | The side panel: title, chips, next moves, long fields, links, provenance, gaps, History. |
| `static/move-form.js` | The generated move and create form, single and bulk, with the per-item gap list. |
| `static/picker.js` | Link picker: search, type filter from the link word, create-new fallback. |
| `static/bulk.js` | The bulk bar and its five actions. |
| `static/report.js` | Sections renderer for a saved view, email summary draft, push and copy buttons. |
| `static/app.js` | Boot: fetch state and model, mount, keyboard routing, the baselining hand-off notice. |
| `static/style.css` | Shared by both consoles; tokens for both themes. |
| `static/old/` | The console this replaced, still serving Baseline mode's screens at `/old/` until they are ported. |
| `static/guide.html` | The lifecycle explanation, served alongside the console. |
| `confluence-runbook.md` | How Claude pulls the Confluence registers into `baseline/` and pushes the normalised result back, governed by `../confluence.json`. |
| `sample-baseline/` | Three pulled pages, as the runbook's pull step would write them, copied in by `make-sample.py`. |
| `make-sample.py` | Writes the sample engagement. |
| `Dockerfile`, `run.sh` | Run it. |
