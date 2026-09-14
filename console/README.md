# Register console

Version 0.5, 15 September 2026.

A lifecycle console for the registers in `solution-register-model.md` (2.28). It reads an engagement folder, overlays any unapplied change sets, and writes every move, edit or new item in the engagement's mode. `- Writes: direct` in `engagement.md`, the default when the line is absent, rewrites the item file, stamps `updated` and appends a line to its History section; git is the record. `- Writes: change-sets` appends one item block to the current session's change set under `<engagement>/change-sets/` for the ingester in `solution-register` to apply (model section 11). The baseline freeze writes the registers' first item files in either mode.

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

The side navigation is grouped: Source (Baseline, shown only when the engagement has pulled pages), Meeting (Outstanding, Work through, Meeting report, Weekly SLT report), Registers (one per type) and Changes (Change sets). The console knows its stage: **Baselining** while the baseline folder is present and no register holds an item, when it opens on Baseline; **Live** from the first item, when it opens on Outstanding and the header shows the freeze date if one ran. The line under the header says what the current view is and what a write does at that stage.

- **Outstanding**: model section 8 in order, a defect list for non-terminal items with no owner or next action, a Register gaps note counting what the supports engine (`integrity.py`) finds missing, and the later-phase view.
- **One tab per register**: the frontmatter columns of section 7. Amber marks an item touched by a pending change set; a provisional id like `LIM-0002.3` means an item created in change set 2, block 3, that the ingester will number on apply.
- **Item drawer**: fields, links, pending blocks against the item, and only the moves section 4.4 allows from its current state. Each move asks for the fields that state requires (I2) before it will append. A Supports needed panel lists what the item's state implies and is missing, each with Accept and Dismiss. Moving to a new state fetches what that state will imply and offers the supports as ticked boxes; confirming writes the accepted support blocks first, then the transition block, to the same change set, so the transition's links can name the new supports as "item n", with the reverse link on each support written back the same way. A dismissal is recorded in `<engagement>/supports-dismissed.json` (rule, item, reason, who, when) and stays dismissed until the entry is removed by hand.
- **Baseline**, in order: Duplicates, Row by row, Missing supports, Freeze. Missing supports lists what the supports engine offers over the accepted candidates, each with Accept, Edit then accept, Link existing (point the row at an accepted candidate of the offered type that is already in the set, with the reverse link where the model names one, creating nothing; the tab lists the candidates whose title shares a word with the row and a datalist holds the rest) or Dismiss with a reason; a limitation whose source calls it Accepted or Change requested with no decision also offers Reconstruct (draft the decision from the row) or Reassess (drop the limitation to Under assessment and offer its open item instead). Accepted offers become implied candidates, linked both ways to the item that implied them. The freeze writes every candidate not rejected, merged or discarded and reports what is left: unreviewed rows, supports still missing, scopes off the list. From then on the same work continues on the **Rationalise** view over the items: Duplicates (groups set aside go to `duplicates-dismissed.json`), Row by row with Mark reviewed, Merge and Delete, Missing supports, and Scopes where the engagement declares any. Merge folds the loser into the survivor, rewrites links that named it and removes its file; Delete drops links naming the item and removes its file; both are direct-mode only and refuse in change-sets mode.
- **Change sets**: every file under `change-sets/`, its blocks, and the raw markdown.
- **Weekly SLT report**: gains a "Register gaps" section, one line per rule with a non-zero count.

## What it writes

One file per maker per session, `CS-nnnn.md`. Header per section 11; blocks in the dossier item-block shape with `Target`, `From`, `Based on`, the changed fields, `Links`, `Evidence` lines and a `Gist`. "Close session" stamps `Session closed` so the ingester can pick the file up and a later edit starts a new set. `Approver` and `Applied on` are the ingester's to fill. A duplicate group set aside on the Rationalise view is recorded as the sorted id list in `<engagement>/duplicates-dismissed.json`.

## Files

| File | Purpose |
|---|---|
| `model.py` | The model as data: states, transitions, required fields, link words, the `SUPPORTS` table. The only place the console knows the model. |
| `integrity.py` | Section 9 and the `SUPPORTS` table over item dicts. Pure; used by baseline and live. Rules read from `model.py` only. |
| `server.py` | Reads items and change sets, overlays them, serves the API, writes through `commit()` in the engagement's mode. |
| `items.py` | The item file layout: `parse_item` and `render_item`, shared by the server and the freeze. |
| `static/` | The page. Vanilla HTML, CSS and JS. |
| `baseline.py` | Baseline mode: tolerant table import, duplicate suggestions, verdicts, edits, freeze. |
| `confluence-runbook.md` | How Claude pulls the Confluence registers into `baseline/` and pushes the normalised result back, governed by `../confluence.json`. |
| `sample-baseline/` | Three pulled pages, as the runbook's pull step would write them, copied in by `make-sample.py`. |
| `make-sample.py` | Writes the sample engagement. |
| `Dockerfile`, `run.sh` | Run it. |
