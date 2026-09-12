---
name: import-confluence
description: Use when asked to import, pull, fetch or refresh the Confluence Design Register pages for a named engagement into this repository, or when a baseline needs the Confluence registers brought local first.
---

# Import Confluence registers

Pull the Design Register parent page's subpages into `engagements/<engagement>/baseline/` as Markdown pages the console can baseline. Read only. Nothing in Confluence is written by this skill, and no item file is written.

**Invocation:** `/import-confluence <engagement>`. The argument is the engagement name and becomes the folder name. Missing argument: ask for it and stop.

## Gate, in this order

1. Read `confluence.json` at the repository root.
2. `mcp_server` blank or no tool with that prefix loaded in this session: run one ToolSearch for `confluence atlassian page`. If a connector appears, write its prefix into `mcp_server` and continue. If none, say so in chat and stop. Create nothing.
3. `parent_page_url` blank: ask for it and stop.
4. `permissions.read` is `denied`: stop. `ask`: ask in chat, wait for a yes, then write `granted` into the file with a `log` entry `{date, action: "read permission", by: <user>}`. `granted`: continue.
5. Only the parent page and its direct children are read. No other page, space or search.

## Pull

For each child page of the parent, in the order the connector lists them:

1. Fetch the page with its body in storage or export HTML, its version number and its URL.
2. Save the raw response as `engagements/<engagement>/baseline/.raw/<page-id>.json` with keys `id, title, version, url, parentId, body`. This is the audit copy; keep it.
3. Convert it with the console image, never with a host interpreter:

```
docker run --rm -v "$PWD:/work" -w /work register-console \
  python /app/pull-page.py engagements/<engagement>/baseline/.raw/<page-id>.json engagements/<engagement>/baseline/
```

If the image is missing, build it first: `docker build -q -t register-console console`. If Docker is not running, say so and stop; do not fall back to host python.

4. A child that has no table is still written; the console ignores pages without tables.
5. A table Confluence renders with a number column gains a leading `#` column, since the reader sees that number but the storage format does not hold it. Where `derive_columns` in `confluence.json` names the page, the pull adds one further column built from that number and writes a line above the table saying it is derived. Use it only where the source's own numbering is the row position, and know the refs shift if someone inserts a row upstream.

When every child is written, append to `log` in `confluence.json`: `{date, action: "pull", engagement, pages: n, by: "Claude"}`.

If `engagements/<engagement>/engagement.md` does not exist, create it from the template in `console/README.md`'s sample with the engagement name, `Domain: to be set`, one phase `Day one (current)`, and `Model version: 2.22`. Nothing else is created.

## Report

In chat, one line per page: title, version, number of table rows. Then the console command to baseline it:

```
console/run.sh engagements/<engagement>
```

## Never

- Write a status, README or placeholder file into the engagement folder. The outcome goes in chat and in `log`.
- Create the engagement folder when nothing was pulled.
- Rename columns, drop rows, or merge tables at pull time. Normalising is the console's job, after a person has given verdicts.
- Push anything to Confluence. That is the runbook's step 4 and needs `permissions.write`.

## Quick reference

| Situation | Do |
|---|---|
| No connector | Say so, stop, create nothing |
| Connector present, URL blank | Ask for the URL, stop |
| `read: ask` | Ask, wait, record `granted` and a log entry, continue |
| Page has prose and two tables | Write prose as text, both tables in full |
| Re-run on an existing engagement | Overwrite the page files and raw copies; leave `verdicts.json` alone |
| Source numbers its rows and you need those numbers | Add the page to `derive_columns` in `confluence.json`; never hand-edit a pulled page |

Background: `console/confluence-runbook.md` for how pull, baseline, apply and push fit together.
