# Register console

Version 0.2, 14 September 2026.

A lifecycle console for the registers in `solution-register-model.md` (2.25). It reads an engagement folder and shows the registers as they would be once every unapplied change set is applied. Every move, edit or new item made in it is appended as one item block to the current session's change set under `<engagement>/change-sets/`. It writes item files only once, at the baseline freeze. The ingester in `solution-register` applies change sets as its second pathway (model section 11) and resolves conflicts there.

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

The side navigation is grouped: Source (Baseline, shown only when the engagement has pulled pages), Meeting (Outstanding, Work through, Meeting report, Weekly SLT report), Registers (one per type) and Changes (Change sets). The console knows its stage: **Baselining** until the freeze, when it opens on Baseline and dims the meeting views because the registers are empty; **Live** afterwards, when it opens on Outstanding and the header shows the freeze date. The line under the header says what the current view is and what a write does at that stage.

- **Outstanding**: model section 8 in order, a defect list for non-terminal items with no owner or next action, a Register gaps note counting what the supports engine (`integrity.py`) finds missing, and the later-phase view.
- **One tab per register**: the frontmatter columns of section 7. Amber marks an item touched by a pending change set; a provisional id like `LIM-0002.3` means an item created in change set 2, block 3, that the ingester will number on apply.
- **Item drawer**: fields, links, pending blocks against the item, and only the moves section 4.4 allows from its current state. Each move asks for the fields that state requires (I2) before it will append. A Supports needed panel lists what the item's state implies and is missing, each with Accept and Dismiss. Moving to a new state fetches what that state will imply and offers the supports as ticked boxes; confirming writes the accepted support blocks first, then the transition block, to the same change set, so the transition's links can name the new supports as "item n", with the reverse link on each support written back the same way. A dismissal is recorded in `<engagement>/supports-dismissed.json` (rule, item, reason, who, when) and stays dismissed until the entry is removed by hand.
- **Baseline**, in order: Duplicates, Row by row, Missing supports, Freeze. Missing supports lists what the supports engine offers over the accepted candidates, each with Accept, Edit then accept, Link existing (point the row at an accepted candidate of the offered type that is already in the set, with the reverse link where the model names one, creating nothing; the tab lists the candidates whose title shares a word with the row and a datalist holds the rest) or Dismiss with a reason; a limitation whose source calls it Accepted or Change requested with no decision also offers Reconstruct (draft the decision from the row) or Reassess (drop the limitation to Under assessment and offer its open item instead). Accepted offers become implied candidates, linked both ways to the item that implied them. Freeze refuses while any failure-level offer is undecided, and `baseline/frozen.md` lists what was implied under "Implied at baseline".
- **Change sets**: every file under `change-sets/`, its blocks, and the raw markdown.
- **Weekly SLT report**: gains a "Register gaps" section, one line per rule with a non-zero count.

## What it writes

One file per maker per session, `CS-nnnn.md`. Header per section 11; blocks in the dossier item-block shape with `Target`, `From`, `Based on`, the changed fields, `Links`, `Evidence` lines and a `Gist`. "Close session" stamps `Session closed` so the ingester can pick the file up and a later edit starts a new set. `Approver` and `Applied on` are the ingester's to fill.

## Files

| File | Purpose |
|---|---|
| `model.py` | The model as data: states, transitions, required fields, link words, the `SUPPORTS` table. The only place the console knows the model. |
| `integrity.py` | Section 9 and the `SUPPORTS` table over item dicts. Pure; used by baseline and live. Rules read from `model.py` only. |
| `server.py` | Reads items and change sets, overlays them, serves the API, appends blocks. |
| `static/` | The page. Vanilla HTML, CSS and JS. |
| `baseline.py` | Baseline mode: tolerant table import, duplicate suggestions, verdicts, edits, freeze. |
| `confluence-runbook.md` | How Claude pulls the Confluence registers into `baseline/` and pushes the normalised result back, governed by `../confluence.json`. |
| `sample-baseline/` | Three pulled pages, as the runbook's pull step would write them, copied in by `make-sample.py`. |
| `make-sample.py` | Writes the sample engagement. |
| `Dockerfile`, `run.sh` | Run it. |
