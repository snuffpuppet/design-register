# Direct writes: the console manages the registers in place

Version 1.0, 14 September 2026. Owner: Adam Moyes. Status: agreed, not built.

## Purpose

Until now the console has written item files once, at the baseline freeze, and recorded every later change as a change set block for the ingester in `solution-register` to apply. The ingester has not been ported to the current model and is not in the loop for the abb-nokia engagement. Adam wants to run the registers from the console now and push them back to Confluence, with the change set pathway kept for later.

This design makes writing item files in place the default mode of a Live engagement, keeps change sets as a mode an engagement can choose, and lets the push build from the registers as they stand.

## Decisions taken

- **Mode is per engagement, default direct.** A `- Writes:` line in `engagement.md` holds `direct` or `change-sets`. A missing line means direct. Nothing about change sets is deleted; the reader, the overlay and the appending code stay, and an engagement that names `change-sets` behaves exactly as today.
- **History lives in the item.** Beyond git, each direct write appends one line to a `## History` section at the end of the item file. That is the per-item trail the console shows and the push may carry or drop.
- **Freeze stays.** It is the one place candidates become item files with ids in order, the id map in `frozen.md` and the rejections list. In direct mode it is the start of the registers, not the end of writing them. Its refusal to run into a non-empty register stays, so a second freeze cannot overwrite ids.
- **No stale-write check in direct mode.** The console is single-user today and git shows a collision. The change set path keeps its `Based on` line as before.

## The mode

`load_engagement()` in `server.py` reads the `- Writes:` line alongside the phases and returns `writes` as `direct` or `change-sets`. The state API carries it. Anything else on the line is an error at start and the console says so rather than guessing.

## One write layer

Every Live write in the server goes through one function, `commit(kind, target, fields, links, evidence, gist, frm)`, where `target` is an item id or `new`. Callers: transition, create, edit, support_accept, support_link, and write_offer for offers ticked in the move dialog. They build the same fields and links they build today and stop deciding where those go.

In change-sets mode `commit` appends a block to the maker's current change set and returns `{"changeSet", "item", "ref"}` as today.

In direct mode `commit`:

- For `new`, takes the next number for the type from the files on disk (max existing plus one), so the id is real at once. Ticked offers are written before the move, and the move's link names the real id. There are no provisional `item n` references in direct mode.
- For an existing id, reads the file, applies the fields (label to key through `field_key`), appends links not already present, bumps `updated` to today, sets `closed-on` to today when the new state closes the item, and rewrites the file.
- Appends one History line: `- <date> | <who> | <from → to, when a move> | <gist> | <evidence note>`.
- Returns `{"item": id, "written": path}`.

Guards do not move: I20 transitions, required fields for the target state, the owner on an offered requirement, Made by named. They run before `commit` as they do before `append_block` today.

Reading is unchanged. Unapplied change sets on disk are still overlaid, so an engagement that switches from change-sets to direct keeps seeing what it recorded. Their provisional items stay provisional until an ingester applies them or the maker recreates them; the console does not convert them.

## items.py

A new `console/items.py` holds the item file layout in one place: `parse_item(path)` as `server.py` has it today, and `render_item(item)` that writes the frontmatter in the order model section 7 gives per type, then the long sections in the model's order, then Source, Notes and History. `parse_item(render_item(x))` round-trips every field the console reads, including History. The server and the freeze use it. `push-pages.py` keeps its own reader for now, since it runs as a script; folding it in is a later tidy.

Frontmatter order is `M.SHORT[kind]` between `status` and `links`, then `raised-on`, `closed-on`, `updated`, as `baseline.item_text` writes now. The RSK `kind` field is written as `kind` and read back as `risk-kind`, as today.

## Console

- The banner under the header says which mode the engagement is in. Direct: "Every move, edit or new item writes the item file; git holds the history." Change sets: the sentence it shows today.
- Toasts name the item written ("RSK-0003 written") rather than a change set block.
- Close session is hidden in direct mode. The Change sets view is shown only when change set files exist.
- The detail panel shows History as a list under the long fields.
- Made by stays required in both modes.
- Baseline mode, the tabs, the supports engine and Freeze are unchanged.

## Push

`push-pages.py` builds from the register files as they stand. `frozen.md` is optional: when present its id map fills the Source id column; when absent the column is empty and the manifest says so. The page note reads "Register as at <date> from this page; N items" rather than "Baselined". The manifest key `frozen` becomes `as_of` and holds the build date. The refusal "not frozen" goes; the engagement, parent and pull-logged refusals stay.

The `/push-confluence` skill drops "frozen" from its wording, and after each successful write it records the new page version into the pulled page's frontmatter `page-version`, so the next build's "moved since the pull" check compares against the version the console itself sent. Without that the second push would refuse every page.

## Model and docs

- Model 2.26: section 7 adds History as an optional body section, one line per write by a tool, and says the item's history is that section plus version control. Section 11 says a tool may write item files directly or through change sets, and that the ingester's apply stage is for the change set mode. The version note at the top says why.
- CLAUDE.md's rule "the console writes item files once" becomes the two-mode rule with direct as the default.
- Console README, the guide page, the runbook and ARCHITECTURE describe the mode, the History section and the push from live registers.
- The handoff gains the mode as a decision taken on purpose.

## Tests

- `items.py`: round-trip of an item with every short field, every long field, links and History; a file with no History section renders without one.
- Direct mode: create assigns the next id per type and writes the file; edit rewrites the file with the fields, bumps `updated` and appends History; transition writes the move, sets `closed-on` on a closing state, and writes ticked offers with real ids the link names; support_link writes both files.
- Mode: `engagement.md` with no line gives direct; with `change-sets` the existing server tests still pass unchanged; an unknown value is refused.
- Push: a build with item files and no `frozen.md` produces a manifest with `as_of` and an empty Source id column.

## Out of scope

- Converting provisional items from old change sets into files.
- A stale-write check in direct mode.
- Porting the ingester.
- Folding `push-pages.py`'s reader into `items.py`.
