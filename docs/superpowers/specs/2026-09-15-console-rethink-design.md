# Console rethink: one table, a side panel and a bulk bar

Version 1.0, 15 September 2026. Owner: Adam Moyes. Status: agreed, not built.

Mockups: https://claude.ai/artifact/NNJWAReYeP3DuHXqtetw3V (five screens, referred to below by number).

## Purpose

The console grew one view at a time and each view has its own way of showing and changing an item. Changing a requirement's state today is select, edit, edit again, find the field, save. Nothing works on more than one item. The model knows what every move needs, but the interface only tells the user after they have tried.

This design replaces the front end with one spine that the model drives. A single table of items, filtered and grouped, with cells that edit in place. A side panel over the table for the whole item and its provenance. A bulk bar that applies one change to a selection. Every state change, single or bulk, goes through one move form generated from `model.py`, which asks only for what that move needs. Integrity failures, suggested supports, duplicates and reports are all the same table with a different filter and a different set of editable columns.

Desk mode is the driver: working a queue of changes after meetings and driving the abb-nokia import to zero integrity failures. Meeting mode is served by the same table with keyboard moves. Reporting mode is a saved filter with a column choice and a push.

The server keeps its write path. Every write still goes through `commit()`; this design adds callers, not a second path.

## Decisions taken

- **One table, not one view per register.** The register views, Outstanding, Rationalise tabs and the Triage view become filters over the same table. Alternative rejected: a queue-first layout with a list per queue and a page per item, which is two surfaces to keep consistent and weak at ad hoc filtering.
- **Side panel, not a page.** The item opens over the table and the table stays where it was. Arrow keys step through rows without closing. Alternative rejected: a full item page, which reads better but costs a round trip back to the table on every item.
- **Three tiers of editing, one form.** A cell edits one field. The panel edits the whole item. The bulk bar edits many. When any of the three changes a state that needs fields or links, the same move form opens, showing only those fields, with shared ones asked once and per-item gaps listed. Alternative rejected: a separate bulk editor, which is a fourth way to change an item.
- **The move form is generated, not written.** `REQUIRED_ON_ENTRY`, `REQUIRED_ON_CREATE`, `CHOICES`, `LABELS` and `LINK_WORDS` in `model.py` are served to the browser once and the form reads them. A model change reaches the form with no front-end edit. The two special cases in `transition()` (Blocked prefix on next action, Vendor ref for a vendor CR going to Submitted) move into `model.py` as data so the form can show them before the user presses Apply.
- **Pick existing first, create as fallback.** When a move or a create needs a linked item, the form opens a picker filtered to the types the link word allows, with a search box. Create new, prefilled from the current item the way the support rules already draft one, sits at the bottom of the picker.
- **Integrity is a filter, not a report.** The rail's Integrity entry expands to one line per rule with its count. Choosing a rule filters the table to the failing items and makes the failing field the editable column. The count drops as rows are fixed. Grouping by item, scope or type is the table's group-by. Alternative rejected: a separate clean-up wizard.
- **Reports are saved filters.** A report is a name, a filter, a column list and a sections list stored in `<engagement>/views.json`. The SLT weekly report is one such view with a date filter and the Moved, Raised, Outstanding and Gaps sections. Push to Confluence and Copy email summary act on the current view. Alternative rejected: hand-written report views, which is what exists today and cannot be reshaped without code.
- **Renumber is a register command.** It compacts one register's ids in raised-on order, rewrites every link in every register, writes a History line on each renamed item and records the old to new map in `<engagement>/renumbered.md`. It refuses in change-sets mode and refuses if the working tree has uncommitted changes, so there is always a rollback point. It is a menu item under the register name and is expected to run once per register after the tidy-up.
- **Preact and htm from a pinned CDN, no build step.** `app.js` is replaced by a handful of ES modules served as they are. Alternatives rejected: keeping hand-written DOM code, which is what made the current file hard to extend; and a bundled framework, which adds a build stage to a repository that has none.
- **Change-sets mode keeps working for single moves and creates.** Bulk, merge, delete and renumber refuse in that mode with a message that says so, as merge and delete do today.

## What the model document says

Nothing in sections 4, 5 or 9 changes. Section 7 gains one sentence after the merge and delete sentence: a tool that renumbers a register rewrites every link that named a renamed id, writes a History line on each renamed item, and keeps the map of old to new ids beside the registers. Version becomes 2.29 with a dated note.

## The front end

### Files

| File | Holds |
|---|---|
| `console/static/index.html` | Header, rail slot, table slot, panel slot, one module script. Loads Preact 10 and htm 3 from cdnjs by exact version. |
| `console/static/app.js` | Boot: fetch state and model, mount. Routing by hash: `#/view/<name>`, `#/item/<id>`. |
| `console/static/store.js` | Client state: items, model, views, filter, selection, open item. Fetches and re-fetches `/api/state`. Every write calls the API then reloads state; no optimistic updates. |
| `console/static/rail.js` | Left rail: engagement, Work queues with counts, Registers with counts, Reports, Save current view. |
| `console/static/table.js` | The table: columns, filter chips, group-by, sort, selection, inline cells, keyboard. |
| `console/static/cells.js` | One editor per field kind: text, choice, status, date, owner, scope, links. Reads `CHOICES` and `STATES`. |
| `console/static/panel.js` | The side panel: title, chips, next moves, long fields, links, provenance column, gaps, History. |
| `console/static/move-form.js` | The generated move and create form, single and bulk, with the per-item gap list. |
| `console/static/picker.js` | Link picker: search, type filter from the link word, create-new fallback. |
| `console/static/bulk.js` | The bulk bar and its five actions. |
| `console/static/report.js` | Sections renderer for a saved view, email summary draft, push and copy buttons. |
| `console/static/style.css` | Kept. Tokens unchanged. |

`guide.html` is unchanged.

### The rail (screen 1)

Work: Outstanding, Integrity (expands to rules), Suggested supports, Duplicates, Unreviewed. Registers: All items and one per type, with counts. Reports: the saved views, then Save current view. The engagement name and stage sit at the top. Baseline mode is unchanged and keeps its existing screens until the freeze; the rail shows Baseline in place of Work until then.

### The table (screens 1 and 4)

Columns are chosen per view and default to id, title, status, scope, owner, one type-specific field, link count and issue count. Filter chips are type, status, scope, owner, failing rule, has link word, raised since, updated since and free text over title, id and notes. Group-by is none, type, status, scope, owner or rule.

A cell edits on click. Text and date cells edit inline and save on blur or Enter. Choice cells open a list. The status cell opens the list of states for the type, greys the ones that are not reachable from the current state and names, beside each reachable one, the fields and links it needs. Choosing a reachable state that needs nothing writes at once. Choosing one that needs something opens the move form for that one item.

Selection is a checkbox column, `x` on the focused row, Shift-click for a range and a header checkbox for every matching row. The bulk bar appears above the table while anything is selected.

Keyboard: `j` and `k` move focus, `x` selects, Enter opens the panel, `e` edits the title, `m` opens the status list, `/` focuses search, Esc clears selection or closes whatever is open. Keys are inert while an input has focus.

### The side panel (screen 3)

Opens at 760px over the right of the table; the table row stays highlighted behind it. Header: id, position in the current list, Link to, Merge into, More (Delete, Mark reviewed, Copy link), close. Left column: title as an inline editor, chips for the short fields each of which edits on click, Next moves with each move's needs written beside it, the long fields as inline editors, Source, History. Right column: Where it came from, the provenance chain walked backward through the link words the model derives (triggered by, constrains, introduces, raised by, proposed by, supersedes); What it produces, walked forward (worked by, delivers, dispositioned by, resolves into, realised as, mitigated by), with a dashed slot and a Pick button for each link the current or a later state will need; Gaps, the item's integrity failures and support offers with the rule id. Up and down arrows step to the neighbouring row in the table's current order.

### The move form (screen 2)

Opens for a status change from any tier and for New item. Title says the move and the count. Shared fields are those the target state requires on every selected item and that share a value or are empty on all; each is one input. Per-item rows list each item with its from and to states and anything that item alone still needs, with an inline input for it. A History note applies to every item. Apply is enabled when nothing is missing. The server receives one bulk request and applies it item by item; the first refusal stops the run and the form shows which items were written and which were not.

### The bulk bar

Set field: choose a field from those common to the selected types, enter a value, Apply. Move to: the states common to every selected item's type, then the move form. Link to: choose a link word from those allowed on the selected types, then the picker for the target, Apply writes one link on each. Merge: choose the survivor from the selection, the rest fold in through the existing merge. Withdraw: the terminal withdrawing state per type, through the move form. Delete: confirm with the count, through the existing delete.

### Reports (screen 5)

A saved view renders as sections. Table sections take the view's columns. The SLT weekly view has Moved since, Raised since, Outstanding for SLT and Register gaps. Copy email summary drafts plain text from the sections, one paragraph each, which the user edits in a text box before copying. Push to Confluence builds the pages for the current view through `push-pages.py` and hands off to the existing gate.

## The API

Existing endpoints are kept. Added:

| Endpoint | Does |
|---|---|
| `GET /api/model` | `STATES`, `TERMINAL`, `TRANSITIONS`, `SHORT`, `LONG`, `LABELS`, `CHOICES`, `REQUIRED_ON_ENTRY`, `REQUIRED_ON_CREATE`, `LINK_WORDS`, `RULES`, `FIRST_STATE`, the engagement's scopes and owners, and the two special-case rules now held as data. |
| `POST /api/bulk` | `{ids, op, ...}` where `op` is `set`, `transition`, `link` or `withdraw`. Runs the matching single operation per id inside one lock, stops at the first `ValueError`, returns `{written: [...], failed: {id, error}}`. Refuses in change-sets mode. |
| `POST /api/needs` | `{ids, to}` returns, per id, the missing fields and links for that move, computed by `missing_for` over the item with no fields applied. The move form calls it to draw itself. |
| `GET /api/items?q=&types=&exclude=` | The picker's search: id or title contains `q`, restricted to the types the link word allows. Served from the loaded state; no new index. |
| `GET /api/views` and `POST /api/views` | Read and write `<engagement>/views.json`, a list of `{name, filter, columns, sections, groupBy}`. Direct-mode file, never a change set. |
| `POST /api/renumber` | `{type, madeBy}`. Refuses in change-sets mode, on a dirty working tree, or if a lock is held. Writes every affected file through `commit()`, writes `renumbered.md`, returns the map. |
| `POST /api/report/summary` | `{view}` returns the drafted email text. Pure text assembly on the server so it is testable. |

`/api/state` gains `provenance` per item: the backward and forward chains resolved to ids and words, computed in `integrity.py` alongside the failures so the panel does not walk links in the browser.

Every write endpoint still takes `madeBy` and still stamps `updated` and a History line through `commit()`.

## Model changes in `model.py`

- `SPECIAL_ON_ENTRY`: the two rules now inlined in `transition()`, as data: `("OI", "Blocked", "next action", "prefix", "Blocked: ")` and `("CR", "Submitted", "vendor-ref", "required_if", ("implemented-by", "Vendor"))`. `missing_for` reads them.
- `WITHDRAWS`: the withdrawing terminal state per type, for the bulk bar: REQ Withdrawn, LIM Withdrawn, CR Withdrawn, DEC Rejected, RSK Retired, OI Closed.
- `BACKWARD` and `FORWARD`: the link words that read as provenance in each direction, for the panel's chains.

## Testing

`make test` covers the server and the pure modules. New tests:

- `test_bulk.py`: set, transition, link and withdraw over three items; stop on the first failure with the written list correct; refusal in change-sets mode.
- `test_needs.py`: a Draft REQ moving to Agreed with and without Phase; a CR to Submitted with and without Vendor ref; an OI to Blocked with the prefix.
- `test_renumber.py`: three REQs with a gap, links from a LIM and a CR, the map, the History lines, the refusal on a dirty tree.
- `test_views.py`: round trip of `views.json`, the summary text for a fixed set of moves.
- `test_provenance.py`: chains over the sample engagement, both directions, a dangling link.

The front end has no unit tests today and this design does not add a JavaScript test runner. Each screen is checked in Chrome against `test-data/puppy-gloves` and the `test` engagement before it is called done, with the check recorded in the plan. The old `app.js` is kept under `console/static/old/` until every view it served exists in the new one, then deleted.

## Build order

1. `model.py` additions, `/api/model`, `/api/needs`, provenance in state. Server only, all tested.
2. The shell: `index.html`, `app.js`, `store.js`, `rail.js`, the table with filters and columns, read only. Registers, Outstanding and All items work. The old console stays reachable at `/old/`.
3. The side panel, read only, with provenance and gaps.
4. The move form and the status cell, single item. Inline cells for text, choice, date, owner, scope. `edit` and `transition` are the only writes so far.
5. The picker, and Link to and New item through it.
6. Selection, the bulk bar and `/api/bulk`.
7. Integrity, Suggested supports, Duplicates and Unreviewed as filters with their editable columns. Merge and Delete from the panel and the bar.
8. Views, the report renderer, summary and push. Renumber.
9. Delete `old/`, update `console/README.md`, `guide.html` and CLAUDE.md.

Each step is a commit that leaves the console usable.

## Out of scope

- Baseline mode before the freeze. It keeps its screens.
- The ingester and change-sets mode beyond what refuses today.
- The push format to Confluence.
- Dark theme changes; the tokens are kept as they are.
