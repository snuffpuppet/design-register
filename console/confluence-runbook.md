# Confluence baseline runbook

Version 0.1, 11 September 2026.

How generated registers held in Confluence become a baselined engagement, and how the result goes back. Claude Code does the Confluence side through an MCP connector; the console does the baseline; the ingester in `solution-register` applies the change set. The three never share anything but files.

## 0. Before anything

Read `confluence.json` at the repository root. It names the parent page, the connector, the engagement, the local copy folder and the permissions. If `mcp_server` is blank, no connector is available: say so and stop. If a permission is `ask`, ask in chat before that action and record the answer in `log` with the date. If `denied`, stop. Nothing outside the parent page and its subpages is read or written under any setting.

## 1. Pull

1. Resolve `parent_page_url` to a page id through the connector and list its child pages. Each child is one register (Requirements, Decisions, Risks and so on, in whatever names the knowledge base used).
2. For each child, fetch the page body and write `<engagement>/<local_copy>/<child title>.md`:

```
---
page-id: 123456
page-title: Requirements
page-version: 7
page-url: https://…/pages/123456
parent-page-id: 123400
pulled-on: 11 September 2026
---

# Requirements

<any prose on the page, as Markdown>

| ID | Requirement | Priority | Owner | Status | Source |
|---|---|---|---|---|---|
| R-12 | … | Must | … | Open | … |
```

Tables are converted cell for cell; nothing is renamed or dropped at this step. Confluence storage format is converted to Markdown, with `<br>` inside a cell kept as a line break, and list items inside a cell separated the same way.

Two columns the pull adds rather than copies. A table Confluence renders with a number column gains a leading `#`, because the reader sees that number but the storage format does not hold it. Where `derive_columns` in `confluence.json` names the page, one further column is built from that number and the pulled page carries a line above the table saying it is derived:

```json
"derive_columns": {
  "1924399124": { "column": "Vendor ref", "format": "CR2-{n}", "page_title": "CRs Register" }
}
```

Use it only where the source's own numbering is the row position. The refs shift if someone inserts a row upstream, so a re-pull after an edit to the source table is worth reading before it is baselined. Never hand-edit a pulled page to add the column; the next pull would overwrite it.
3. Append `{ "date", "action": "pull", "pages": n, "by": "Claude" }` to `log` in `confluence.json`.

The console reads every `.md` in that folder as candidates. Every row is a candidate whatever id or status it claims; the id is kept as a reference, the status is kept in Notes.

## 2. Baseline

In the console, Baseline mode. Work through the candidates: reject with a reason, retype, merge duplicates into a survivor, fix owner and priority in bulk, accept. State lives in `<local_copy>/verdicts.json`. Click a title to correct a candidate's fields before deciding. When done, Freeze baseline writes every accepted candidate as an item file in the engagement's registers, assigns ids, and writes `<local_copy>/frozen.md` (the id map) and `<local_copy>/rejections.md` for the knowledge base pipeline. The freeze runs once and refuses if a register already has items.

## 3. Apply

Nothing to apply: the frozen item files are the baseline. From here every change is a change set, and the ingester in `solution-register` applies those through its gate as usual.

## 4. Push

With `permissions.write` granted or confirmed:

1. Re-read the pulled pages to confirm `page-version` still matches Confluence. If a page moved on, stop and say which.
2. For each register subpage, in `replace-tables` mode, rewrite the register table on that page with the normalised rows: the model's columns (section 7), our ids, statuses in the model's words, and a `Source id` column carrying the knowledge base's original id so its pipeline can reconcile. Prose above and below the table is kept. If `add_note` is set, a short note goes under the heading: "Baselined <date>; n items accepted, n merged, n rejected. Source of truth is now the engagement register." In `new-child` mode the originals are untouched and the normalised registers are written as new subpages instead.
3. Never delete a page. Confluence keeps the previous version.
4. Append a `push` entry to `log`.

## What normalising means

- One table per register subpage, columns exactly as model section 7 for that type, plus `Source id`.
- Status values are the model's strings. Anything the source had is in Notes, not in Status.
- Dates in `D Month YYYY`.
- Rejected candidates do not appear in the pushed tables. They appear in `rejections.md`, which can be pushed as a child page called "Baseline rejections" if wanted.
