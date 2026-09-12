# Register console

Version 0.1, 11 September 2026.

A lifecycle console for the registers in `solution-register-model.md` (2.24). It reads an engagement folder and shows the registers as they would be once every unapplied change set is applied. Every move, edit or new item made in it is appended as one item block to the current session's change set under `<engagement>/change-sets/`. It writes item files only once, at the baseline freeze. The ingester in `solution-register` applies change sets as its second pathway (model section 11) and resolves conflicts there.

## Run

```
make sample                        # writes test-data/puppy-gloves (re-run to reset)
make up                            # build and run in Docker; http://localhost:8085/
make up ENG=engagements/acme PORT=8090
make down | restart | logs | status | clean
```

`console/run.sh [engagement-dir] [port]` does the same as `make up` without make.

Only the Python standard library is used. Nothing is installed on the host.

## What it shows

- **Work through**: a triage queue for cleaning up a big register. Register defects first, then limitations awaiting assessment, open items by due date, risks past review, change requests with the business, stale decisions and drafts. One item per screen with its linked items beside it and only its legal moves. Keys j, k and p for next, previous and park; position and parked items are remembered in the browser.
- **Meeting report**: one page for the meeting: calls needed, change requests with estimates, risks to review, new limitations, actions by owner, drafts, and every pending change since the last ingestion. Copy as markdown for meeting notes, or print.
- **Baseline**: appears when `<engagement>/baseline/` holds pulled register pages (see `confluence-runbook.md`). Every table row is a candidate whatever it claims; source ids are kept as references and source statuses go to Notes. Suggested duplicate groups with pick-the-survivor merge (an already accepted row can still lead, so a late find folds into it), filters by type, page, verdict and text, bulk Accept, Reject with a reason, Discard, retype, set owner or MoSCoW. Clicking a title opens an editor for the candidate's fields, including the status it will start in. Verdicts and edits live in `baseline/verdicts.json`. **Freeze baseline** writes the accepted set as the registers' first item files, assigning ids in order, turning source-id links into real links where both ends were accepted, and writing the id map to `baseline/frozen.md` and the rejections to `baseline/rejections.md`. It runs once and only into empty registers; afterwards the view is read only and every change is a change set.
- **Guide**: the lifecycle explained, with the diagrams: requirements first, limitations first, the change request track, where designs sit, risk kinds, and where the console fits.
- **Outstanding**: model section 8 in order, a defect list for non-terminal items with no owner or next action, and the later-phase view.
- **One tab per register**: the frontmatter columns of section 7. Amber marks an item touched by a pending change set; a provisional id like `LIM-0002.3` means an item created in change set 2, block 3, that the ingester will number on apply.
- **Item drawer**: fields, links, pending blocks against the item, and only the moves section 4.4 allows from its current state. Each move asks for the fields that state requires (I2) before it will append.
- **Change sets**: every file under `change-sets/`, its blocks, and the raw markdown.

## What it writes

One file per maker per session, `CS-nnnn.md`. Header per section 11; blocks in the dossier item-block shape with `Target`, `From`, `Based on`, the changed fields, `Links`, `Evidence` lines and a `Gist`. "Close session" stamps `Session closed` so the ingester can pick the file up and a later edit starts a new set. `Approver` and `Applied on` are the ingester's to fill.

## Files

| File | Purpose |
|---|---|
| `model.py` | The model as data: states, transitions, required fields, link words. The only place the console knows the model. |
| `server.py` | Reads items and change sets, overlays them, serves the API, appends blocks. |
| `static/` | The page. Vanilla HTML, CSS and JS. |
| `baseline.py` | Baseline mode: tolerant table import, duplicate suggestions, verdicts, export. |
| `confluence-runbook.md` | How Claude pulls the Confluence registers into `baseline/` and pushes the normalised result back, governed by `../confluence.json`. |
| `sample-baseline/` | Three pulled pages, as the runbook's pull step would write them, copied in by `make-sample.py`. |
| `make-sample.py` | Writes the sample engagement. |
| `Dockerfile`, `run.sh` | Run it. |
