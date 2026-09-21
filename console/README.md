# Register console

Version 0.11, 21 September 2026. Model 2.35.

See [Change proposal upgrade](../docs/change-proposal-upgrade.md) for the legacy CR-to-CP preview/apply migration and work-laptop rollout. Internal IDs/folders and links migrate; vendor references, original history and statuses are preserved.

## Use

The shared table opens actual registers. Rationalise and Desktop share the table and item panel. Rationalise saves single/bulk field and status corrections immediately through `/api/rationalise/edit`, skipping lifecycle entry requirements. Desktop follows the workflow; Desktop by scope applies a scope filter and restores workflow mode. Set Made by before writing. Saved reviews and meeting records remain optional tools.

Rationalise also offers **Change type** and **Merge…** with before/after previews and Accept/Cancel. `structure.py` builds deterministic plans; acceptance checks a digest of the current registers and choices. Type changes preserve old fields/history and redirect IDs. Merges keep lead values, fill blanks and retain conflicting values/history in Notes.

Deletion archives item snapshots and removed incoming links in private `rubbish-bin.json`. Restore recovers the original ID and history, adding links without reverting later edits. Deferred links are recovered when a referring record is itself restored. The bin is excluded from anonymised exports.

An optional structured review keeps its initial item snapshots, ordered IDs, per-item outcomes, correction drafts, evidence and content revisions in `reviews.json`. Saving a draft does not change registers. Preview shows changes and remaining state-entry gaps. Apply checks revisions and writes the correction batch through the normal commit boundary inside a recovery operation. Complete review requires every row reviewed, no unresolved clarification, and all mutating proposals applied. Integrity gaps can remain explicitly visible; review completion never claims missing evidence exists.

A meeting keeps a fixed agenda, original snapshots, discussion progress and outcomes in `meetings.json`. Its item panel uses ordinary workflow operations. Follow-up creation and recording the resulting ID happen in one operation. Export produces Markdown with a stable MTG reference. The transcript ingester is not changed; correlating that reference with later transcript proposals is an integration task for its repository.

Baseline-only inputs offer Import and review, which creates item files and a review immediately. The old freeze conversion function and map remain internal compatibility mechanisms. The previous `/old/` frontend is no longer the entry point.

## Persistence and compatibility

`engagement.md` accepts `- Writes: direct` (default) or `- Writes: change-sets`. Metadata can be saved in either mode. Historical corrections, merges, deletions and bulk register changes require direct mode. Explicit empty values clear fields in direct mode; change-set clearing is refused because no compatible clear operation exists. Change-set writes require `- Ingester model version: 2.30` or `2.31`; do not declare a version until the other repository supports it.

Published IDs stay stable. Merge and retype record `aliases.json`; old copied item URLs resolve to the survivor. Deleted IDs are reserved. A split keeps the original as an index naming the new records. Renumber is removed from normal navigation; its legacy endpoint additionally requires `allowUnpublished: true`.

Every HTTP mutation validates Made by and runs inside `operations.transaction`. Item and session revisions protect against stale browser writes. Operations record before/after snapshots, actor, context and meeting reference. Exceptions restore the starting snapshot, and startup rolls back prepared operations. Undo refuses if current engagement content differs from the operation's resulting snapshot. Journals contain private data and are deliberately excluded from anonymised exports. Completed operations retain changed files rather than duplicate every item; prepared operations retain full recovery snapshots. Keep these private and archive completed work deliberately.

The server serialises its reads and writes. The external ingester must not write the same engagement concurrently; its process does not share this lock. Git remains useful for durable version control and independent recovery.

## Reports

Tables and server summaries use the same type, state, scope, owner, search and integrity-rule filters. `since` is the report's change window; `updatedSince` is an optional row filter. Gaps are restricted to the filtered item set. Recorded historical corrections appear separately from workflow movements. Pending change-set values are labelled as proposals. Build full-register Confluence push is deliberately named for its actual scope.

## API additions

| Endpoint | Behaviour |
|---|---|
| `POST /api/import` | Create working items from pulled source rows and open a review; refuses existing registers |
| `POST /api/reviews/create` | `{name, ids}` starts a review snapshot |
| `POST /api/reviews/update` | `{batch, revision, id, entry}` saves a proposal or verdict; `close: true` completes |
| `POST /api/reviews/preview` | `{batch, revision}` checks revisions and returns proposed changes/errors |
| `POST /api/reviews/apply` | Applies reviewed corrections in direct mode; lifecycle transitions are not replayed |
| `POST /api/reviews/summary` | `{batch}` returns the review record as Markdown |
| `POST /api/meetings/create` | `{name, ids}` fixes the agenda and snapshots |
| `POST /api/meetings/update` | Saves outcomes, an exact agenda permutation, or closes the meeting |
| `POST /api/meetings/action` | Creates and records one follow-up open item atomically |
| `POST /api/meetings/summary` | Exports the agenda and outcomes |
| `POST /api/bulk/preview` | Returns valid IDs and per-item errors; `perItem` supports individual fields/links |
| `POST /api/bulk` | Preflights all items; optional explicit `applyValid: true` applies only valid IDs |
| `POST /api/merge/preview` | Returns compared records and conflicting fields requiring resolutions |
| `POST /api/operations/undo` | `{operation}` restores a prior operation if current content still matches |

Existing item, transition, support, report and view endpoints remain. Requests may carry `revisions: {id: hash}` and `session`; the browser supplies them. `/api/state` adds reviews, meetings, aliases, recent operation summaries and compatibility information.

## Files and checks

`model.py` holds model data; `items.py` parses/renders Markdown; `integrity.py` checks it. `workspaces.py` owns review/meeting metadata, `operations.py` owns recovery, `anonymise.py` builds deterministic fixtures, and `server.py` coordinates writes through `commit()`. The frontend's workspace UI is `static/workspaces.js`; pinned browser libraries are in `static/vendor/`.

Run `make test` inside Docker. Python tests cover corrections, stale revisions, recovery, aliases, agendas, reports and deterministic export in addition to the existing model/integrity coverage. `tests/browser-smoke.cjs` runs in the Puppeteer image against an isolated disposable engagement, using `CONSOLE_URL`. It writes screenshots to `/output`. See `../docs/work-laptop-acceptance.md` for interactive release checks.
