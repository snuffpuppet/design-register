# Rationalise in place: the registers as the working space

Version 1.0, 15 September 2026. Owner: Adam Moyes. Status: agreed, not built.

## Purpose

The console today holds an engagement in Baselining until every candidate has a verdict, every failure-level support offer is decided and every Scope is on the list. Only then does the freeze write item files and Live begin. On the abb-nokia engagement that gate has become the obstacle: new items need raising now, and the rationalising of 320 pulled candidates is not finished and need not be finished first.

This design makes the registers the working space from the freeze onward. The freeze writes everything the reviewer has not rejected or merged, unreviewed rows included. After it, the same rationalising work continues over the real items: finding duplicates, merging, deleting, creating and linking the supporting records the model implies, with the console highlighting what is still unreviewed and what is still missing. New items can be raised from the moment the freeze has run.

## Decisions taken

- **The freeze writes every candidate that is not rejected or merged.** An undecided candidate is written the same way an accepted one is. Rejected: not written, logged in `rejections.md` as now. Merged: folded into its survivor as now. The freeze still needs empty registers. Alternatives rejected: writing only accepted candidates and keeping the rest as importable candidates, which leaves two workspaces alive at once; and keeping the verdict gate while dropping the others, which still blocks new items until the review is done.
- **The supports gate and the Scope gate move from the freeze to the highlights.** The freeze no longer refuses over an undecided failure-level offer or an off-list Scope. Both are reported by the freeze and shown afterwards in the Rationalise view, where they are worked down over the items. I24 and the supports rules are unchanged; only where they are enforced changes.
- **"Unreviewed" is derived from the baseline ledger, never written into an item file.** The freeze already records `frozenAs` on every candidate in `baseline/verdicts.json`. An item is unreviewed when the candidate it was frozen from carries no verdict. Marking it reviewed sets that candidate's verdict to Accept. Item files stay exactly the model's section 7; nothing new goes in the frontmatter, the push tables or the ingester port. Alternative rejected: a `review` frontmatter key, which is filterable anywhere and survives the baseline folder being deleted, at the cost of a model field the ingester would have to learn.
- **Baseline becomes Rationalise once the registers hold items.** Same navigation slot, same tabs, reading and writing items rather than candidates. It stays for the life of the engagement. Alternatives rejected: folding the tabs into the register views and the drawer, which loses the walk-through that the Row by row and Duplicates tabs give; and keeping Baseline and Rationalise as two views, which is two places to learn for one job.
- **Merge and Delete are real writes that remove a file.** Git holds the history, which is the direct-mode principle already recorded in the model's section 11. Alternative rejected: marking the loser with a terminal state and hiding it, which leaves the registers carrying items the model would count and the push would send.
- **Merge and Delete exist only in direct mode.** The ingester's change set format has no block for either, and the ingester is not edited from here. In change-sets mode both refuse with a message that says so.
- **Every write still goes through `commit()`.** Merge and Delete are new callers, not new write paths. The file removal is the one thing `commit()` does not do today and is added to it as a target of `delete`.

## What the model document says

Version 2.28, with a dated note at the top.

**Section 11, Imports** gains one paragraph: an import may be written into the registers before its review is complete, with every row that was neither rejected nor folded becoming an item in its first state or a mapped one, and the review continuing over the items. A tool that does this keeps its own record of which items are still unreviewed and shows it; the record is the tool's, not a field on the item.

**Section 7** gains one sentence after the History sentence: when a tool merges one item into another or deletes one, the surviving item's History line says what was folded in or removed, every item whose Links named the removed id has that link rewritten or dropped with a History line of its own, and version control holds the removed file.

Nothing in sections 4, 5 or 9 changes.

## The freeze

`baseline.freeze()` keeps its refusal on a non-empty register and on nothing to write. It loses the pending-supports refusal and the off-list Scope refusal. `assemble()` treats a candidate with no verdict as written; a Reject or Merge verdict behaves as it does now.

The freeze returns, and the console shows, four counts beside the counts it returns today: items written unreviewed, failure-level supports still missing over the written set, warning-level supports still missing, and items whose Scope is off the list or blank where the engagement declares scopes. `baseline/frozen.md` gains a line for each.

The id map, `rejections.md`, the Implied at baseline section and the `frozenAs` stamps are unchanged.

## Stage

The console is Live when any register holds an item. Baselining is the stage before that, and only when the baseline folder is present. `stage()` in `app.js` drops its `frozen` test, because the presence of items is the whole test; `frozen` still feeds the header line. Nothing dims after the freeze. Register views, the item drawer, Create and every meeting view behave exactly as they do in Live today.

## The Rationalise view

Shown in the Source group in place of Baseline whenever the engagement is Live and the baseline folder is present. The nav badge is the unreviewed count. Four tabs, in the order the work runs.

**Duplicates.** The baseline's `clusters()` heuristic run over the live items instead of candidates: same key, same related-kinds exclusion. A group can be set aside, recorded as the sorted id list in `<engagement>/duplicates-dismissed.json`, the same shape as `supports-dismissed.json`. Each group offers Keep one and merge the rest, which calls Merge once per loser.

**Row by row.** Walks the items of one register at a time, unreviewed first, with the same keys the candidate walk has. Actions: Mark reviewed, Edit, Merge into, Delete, Skip. Mark reviewed sets the frozen-from candidate's verdict to Accept; an item with no frozen-from candidate, such as one raised in the console, is never unreviewed and is not listed under the unreviewed filter.

**Missing supports.** The live integrity offers, `S.integrity.suggestions`, listed by rule with the same four actions the drawer's Supports needed panel has: Accept, Edit then accept, Link existing, Dismiss. They call the existing `/api/support/*` endpoints. Failure level first, then warnings.

**Scopes.** Shown only where the engagement declares scopes. Lists items whose Scope is blank or off the list, each with a select of the declared values that writes through Edit. Empty when I24 holds.

The Freeze tab and the candidate tabs are gone from this view once Live, as the candidates are.

## The two new writes

**`/api/merge` `{survivor, losers: [ids], madeBy, evidence}`.** For each loser, in order:

1. Refuse if either id is unknown, if survivor and loser differ in type, or if the engagement writes change sets.
2. Fold into the survivor the loser's Source lines, its Notes prefixed `Merged in from <loser id>:`, its links not already held, and any short or long field the survivor has blank and the loser has set. Scope and Status are never taken from the loser.
3. Across every item, rewrite each link that names the loser to name the survivor; a rewritten link that duplicates one already held is dropped. Each touched item gets a History line `merged <loser> into <survivor>`.
4. Write the survivor through `commit()` with gist `merged <loser> into this item`.
5. Delete the loser file.

**`/api/delete` `{id, madeBy, evidence, reason}`.** Refuse on an unknown id or in change-sets mode. Across every item, drop each link naming it, with a History line `dropped link to <id>, deleted: <reason>`. Delete the file. The reason is required, so the git commit that follows has a message to carry.

Both endpoints return the ids touched. The item drawer gains Merge into, a select of same-type items, and Delete, which asks for the reason. In change-sets mode the two buttons are shown disabled with the refusal as the title.

`commit()` gains one target, `delete`, which removes the file and returns its path, so that file removal is still the one write function's work. The link rewrites are ordinary `commit()` calls with `target = id`, `fields = {}` and a gist; `commit()` is made to accept an empty field set when a gist is given.

## Files touched

| File | Change |
|---|---|
| `solution-register-model.md` | 2.28: section 11 Imports paragraph, section 7 sentence, dated note at the top. |
| `console/baseline.py` | `assemble()` writes undecided candidates; `freeze()` drops two gates and reports four counts; `clusters()` accepts items as well as candidates; `frozen()` reads the new count lines. |
| `console/server.py` | `merge()`, `delete()`, the `delete` target in `commit()`, `/api/merge`, `/api/delete`, `/api/rationalise/not-duplicates`, `/api/rationalise/reviewed`; `state()` adds `unreviewed` ids and `dupes` clusters; `duplicates-dismissed.json` load and save. |
| `console/integrity.py` | No change. |
| `console/static/app.js` | `stage()`; Rationalise view with four tabs; drawer Merge into and Delete; freeze result toast. |
| `console/static/guide.html`, `console/README.md`, `console/confluence-runbook.md`, `CLAUDE.md` | The new stage boundary and the Rationalise view. |
| `console/tests/` | Tests below. |

## Testing

Python, in the existing suite:

- Freeze with undecided candidates writes them, stamps `frozenAs`, and reports the unreviewed count.
- Freeze with a pending failure-level offer succeeds and reports it.
- Freeze with an off-list Scope succeeds and reports it.
- Merge folds Source, Notes, links and blank fields; never takes Status or Scope; rewrites links on third items with a History line; deletes the loser file.
- Merge refuses across types and in change-sets mode, and writes nothing on refusal.
- Delete drops links on other items with a History line and removes the file; refuses without a reason.
- `state()` derives unreviewed ids from the verdicts and lists none for an item raised in the console.
- `clusters()` over items finds the same groups it finds over the equivalent candidates.

Browser, on `engagements/test`, which has the pulled pages and a verdicts file: freeze with rows left undecided, confirm Live opens with the Rationalise badge at the unreviewed count, raise a new item, merge two, delete one, and check the item files and `git status` after each.

## Out of scope

Bringing new candidates into a Live engagement from a later pull. Any change to the push. Merge or Delete in change-sets mode. Porting anything to the ingester.
