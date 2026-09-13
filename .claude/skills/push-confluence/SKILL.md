---
name: push-confluence
description: Use when asked to push, write back, publish or sync a frozen baseline's registers to the Confluence Design Register pages for a named engagement. Builds the pages first and sends nothing until the write gate is passed.
usage: /push-confluence <engagement>: build the frozen registers as pages, read the manifest, send under the write gate
---

# Push the frozen registers back to Confluence

Send the engagement's frozen registers back to the Confluence pages they were pulled from. Two halves: build, which writes files and sends nothing, then send, which is gated. Item files are never written by this skill.

**Invocation:** `/push-confluence <engagement>`. Missing argument: ask for it and stop.

## Build, always first

1. Read `confluence.json`. `push.engagement` must equal the argument. If it does not, say so and stop; do not edit the config to make it match. That field exists so a test copy or a transposed set can never be sent.
2. Run `make push-pages ENG=engagements/<engagement>`. It runs `console/push-pages.py` in the console image and refuses on its own if the engagement is wrong, the pages came from another parent, no pull is logged, or the baseline is not frozen. If Docker is not running, say so and stop; do not run host python.
3. Read `engagements/<engagement>/push/manifest.json`. Report in chat, one line per page: title, pulled version, items, and the `from` and `warning` fields when present. List the untouched pages. If any page has `warning`, or was built from pulled markdown rather than the raw copy, say so plainly and ask whether to continue with that page.

## Gate, in this order

1. `mcp_server` blank or no tool with that prefix loaded: run one ToolSearch for `confluence atlassian page`. None: say so and stop.
2. `permissions.write` is `denied`: stop. `ask`: ask in chat, naming the pages and the mode, wait for a yes, then write `granted` and a `log` entry `{date, action: "write permission", by: <user>}`. `granted`: continue.
3. For each page in the manifest, fetch its current version through the connector. If it is greater than the pulled `page-version`, stop and say which page moved on. Someone edited it since the pull; the pull and baseline need redoing for that page before it is overwritten.
4. Only pages listed in the manifest are written. No other page, space or search.

## Send

For each manifest entry, in order:

- `mode` `replace-tables`: update the page `id` with the `body` from its file, keeping the title, with version = current version + 1 and a version message `Baselined <date> by <user>`.
- `mode` `new-child`: create a page under `parentId` with the file's `title` and `body`.
- `rejections.json`, if present: create it as a child of the parent page. Skip it if a page with that title already exists under the parent and say so.

Never delete a page. After each write, record the returned version and page id in the manifest entry as `sent_version` and `sent_id`. If a write fails, stop, leave the manifest as it is, and report which pages were sent and which were not; the pages already sent stay sent, since Confluence keeps their history.

When done, append to `log` in `confluence.json`: `{date, action: "push", engagement, pages: n, mode, by: "Claude"}`.

## Report

One line per page sent: title, old version, new version, items. Then the parent page URL.

## Never

- Send anything before the manifest has been read and reported.
- Edit `push.engagement` or `parent_page_url` to get past a refusal.
- Push an engagement that is not frozen, or push twice without a fresh build.
- Write to a page whose version moved on since the pull.

Background: `console/confluence-runbook.md` step 4.
