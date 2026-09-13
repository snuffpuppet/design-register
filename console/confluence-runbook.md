# Confluence baseline runbook

Version 0.2, 14 September 2026.

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

In the console, Baseline mode. Work through the candidates: reject with a reason, retype, merge duplicates into a survivor, fix owner and priority in bulk, accept. State lives in `<local_copy>/verdicts.json`. Click a title to correct a candidate's fields before deciding. Then work Missing supports to zero failures before the freeze: it offers the record each accepted candidate's state implies is missing, for accepting, editing then accepting, or dismissing with a reason. When done, Freeze baseline writes every accepted candidate as an item file in the engagement's registers, assigns ids, and writes `<local_copy>/frozen.md` (the id map) and `<local_copy>/rejections.md` for the knowledge base pipeline. The freeze runs once, refuses while any failure-level offer in Missing supports is undecided, and refuses if a register already has items.

## 3. Apply

Nothing to apply: the frozen item files are the baseline. From here the console writes in the engagement's mode: in place by default, or as change sets the ingester in `solution-register` applies through its gate.

## 4. Push

`/push-confluence <engagement>`. The skill runs in two halves, and the first sends nothing.

1. **Build.** `make push-pages ENG=engagements/<engagement>` runs `console/push-pages.py` in the console image. It refuses unless the engagement is the one named in `confluence.json` under `push.engagement`, every pulled page came from the configured parent page, and a pull for that engagement is in `log`. The pages carry the registers as they stand; `baseline/frozen.md`, when present, fills the Source id column. It then writes `<engagement>/push/`: a `manifest.json` and one `<page-id>.json` per register page holding the storage-format body to send. Each item goes back to the page it was pulled from, with the model's columns for its type, our ids, statuses in the model's words, links, and a `Source id` column carrying the knowledge base's own id so its pipeline can reconcile. In `replace-tables` mode the body is the page's own body with the register table swapped and the note added; when the `.raw` audit copy of the page is missing the body is rebuilt from the pulled markdown and the manifest says so. In `new-child` mode the body is a fresh page named `<title> (baselined)`. Pages that gave no items (summaries, conventions) are listed as untouched and are not sent. Rejections become a `Baseline rejections` child page if any were rejected.
2. **Read the manifest** and say in chat what would be sent: each page, its pulled version, item count, and any warning.
3. **Gate.** `permissions.write` must be `granted`, or `ask` answered yes in chat and then recorded. Re-read each page's current version through the connector; if it is past the pulled `page-version`, stop and say which page moved on. After a successful send the skill writes the new version into that line, so a later push compares against what the console last sent.
4. **Send**, one page at a time, through the connector's update-page call with the body from the file, and the create-page call for new children. Never delete a page; Confluence keeps the previous version. After each page, note its new version in the manifest entry.
5. Append a `push` entry to `log`: date, engagement, pages sent, by.

## What normalising means

- One table per register subpage, columns exactly as model section 7 for that type, plus `Source id`.
- Status values are the model's strings. Anything the source had is in Notes, not in Status.
- Dates in `D Month YYYY`.
- Rejected candidates do not appear in the pushed tables. They go to the `Baseline rejections` child page built from `rejections.md`.
