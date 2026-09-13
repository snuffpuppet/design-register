# Scope: a per-engagement filter restored to the item

Version 1.0, 14 September 2026. Owner: Adam Moyes. Status: agreed, not built.

## Purpose

Section 6 of the model has said since 2.17 that items carry no Scope, and named the condition for bringing it back: "A way of filtering the registers by service or domain can be added when an engagement has several services to name." The abb-nokia engagement is that case. It delivers four technical services and two compositions, its Confluence pages carry a Scope column on every register, and it maintains a Scope Taxonomy page defining the allowed values.

The baseline currently drops that column into Notes, because the model has no field for it. Three hundred and one of the 320 candidates carry a Scope the console cannot filter, sort or push back. This design gives Scope a field, declares its vocabulary per engagement, and leaves every engagement that does not declare one behaving exactly as 2.26 does.

## Decisions taken

- **The feature is an engagement opt-in.** A `## Scopes` section in `engagement.md` declares the vocabulary, read by the same loop that reads `## Phases`. An engagement that declares none carries no Scope, is never asked for one, and is checked by no Scope rule. This is section 6's own wording made mechanical, and it keeps `test-data/puppy-gloves`, `engagements/test` and the 2.20 ingester untouched.
- **One scope per item, not a list.** The taxonomy page says each item is tagged once, at the lowest level that applies. A list would make the rollup double-count and give the reviewer a decision to avoid rather than make.
- **Scope is a header field, on every type.** It goes in section 4.1 beside Owner and Links, not in 4.2 with the type-specific fields. Every register page in the source carries it, and a filter that covered four types of six would not be worth having.
- **Required on create when the engagement declares scopes.** The source fills it on every row that has the column, so nothing is lost at the freeze, and a blank Scope makes a filter under-report silently rather than visibly. An item offered by the supports engine inherits its trigger's Scope, so accepting an offer stays one click.
- **A set value must be on the list.** Mirrors I5 for Phase. Free text would let the vocabulary drift into the synonyms the taxonomy page exists to prevent.
- **The Scope Taxonomy page stays in `skip-pages.txt`.** It is the vocabulary, not a register. It seeds `## Scopes` and produces no candidates.

## What the model document says

Version 2.27, with a dated note at the top saying Scope returns as an engagement-level filter and why.

**Section 6** stops recording a removal and defines the field: Scope names the service or area an item belongs to; the engagement declares its values; each item is tagged once, at the lowest level that applies; an engagement with one service declares none and items carry no Scope.

**Section 4.1** gains a row:

| Scope | The service or area the item belongs to, from the engagement's Scopes list (6). One value, at the lowest level that applies. Required while the engagement declares scopes. Absent where it declares none. |

**Section 7** adds `scope` to all six frontmatter tables, directly after `status`.

**Section 9** gains one rule, worded from I5:

> **I24.** Every item's Scope is one of the engagement's Scopes, and no item is without one, where the engagement declares any.

## console/model.py

`scope` goes **first** in every `SHORT` list. That single placement gives two things without further code, because `items.render_item` (line 61) and `push_pages.columns` (line 107) both build from `M.SHORT[kind]`: the frontmatter position directly after `status`, and the pushed table column in the same position.

```python
SHORT = {
    "REQ": ["scope", "moscow", "phase", "owner", "implemented-by"],
    "DEC": ["scope", "owner", "consulted", "approved-by", "implemented-by"],
    "LIM": ["scope", "owner", "chosen-option", "implemented-by"],
    "RSK": ["scope", "risk-kind", "owner", "likelihood", "impact", "due"],
    "OI":  ["scope", "owner", "due"],
    "CR":  ["scope", "owner", "chosen-option", "estimate", "approved-by", "phase", "implemented-by", "vendor-ref"],
}
```

`LABELS` gains `"scope": "Scope"`. `REQUIRED_ON_CREATE` gains `scope` to all six lists. `RULES` gains the I24 text.

`REQUIRED_ON_CREATE` is enforced only when the engagement declares scopes, so the requirement travels with the engagement rather than the model file. The server already holds the engagement when it checks required fields; the check filters `scope` out of the required list when `eng["scopes"]` is empty.

## console/server.py

`load_engagement()` returns `scopes` as a list beside `phases`, parsed by the same block at line 76. `## Scopes` opens the section, `- ` lines are values, the next `## ` closes it. No `(current)` convention applies.

The state API carries `engagement.scopes`. `I.check(...)` is passed `scopes=eng["scopes"] or None`, matching how `phases` is passed today at line 236.

`commit()` is unchanged. Scope is an ordinary field and flows through the fields dict it already takes.

## console/integrity.py

One rule beside I5 at line 218, taking `scopes` the way `check()` and `rules()` already take `phases`:

- A Scope that is set and off the list fails, naming the value.
- A Scope that is blank fails, but only when `scopes` is not None.
- When `scopes` is None the rule never fires, so an engagement that declares none is checked exactly as today.

## console/baseline.py

`COLS` gains a `scope` key, placed above the broad keys as the table's own ordering comment directs, so that a future word added to `kind` or `owner` cannot claim `Domain` first:

```python
"scope": ["scope", "domain", "service", "area"],
```

`EDITABLE` gains `scope`, so the candidate editor and the existing bulk field fix can set it.

**The freeze refuses** while the engagement declares scopes and any accepted candidate has a blank or off-list Scope, naming the count and the offending values. This matches the freeze's existing refusal on an undecided failure-level offer. The bulk field fix makes clearing the refusal cheap.

**The supports engine** sets `scope` on an offered item from its trigger, in the same place it sets the other templated fields. Scope is copied rather than templated, since the trigger's value is the answer in every case.

## console/static/app.js

Four changes, each following an existing pattern:

- The field editor at line 259 special-cases `scope` the way it special-cases `phase`, rendering a select from `S.engagement.scopes` with a blank option.
- The baseline bulk bar at line 623 gains a "set Scope…" select beside "set MoSCoW…", and its handler at line 746 adds `scope` alongside `owner`, `moscow` and `implemented-by`.
- The candidate editor at line 653 shows Scope, and the candidates table at line 631 shows it as a column.
- The register views gain a scope filter beside the existing filters, shown only when the engagement declares scopes.

Every one of these is hidden when `S.engagement.scopes` is empty, so the page for an engagement without scopes is the page as it stands today.

## abb-nokia

`## Scopes` is seeded from the Scope Taxonomy page's sixteen values. The baseline then needs three reconciliations, all in the candidate editor or the bulk fix:

- `NBN TC4 Access` on one row becomes `NbnTC4Access`.
- `Pool Management` and `Location Management`, on one CR row each, are vendor-side names absent from the taxonomy. Either they join the list or the rows are retagged.
- The nineteen `CRs Register` rows take their Scope from the `Domain` column once `COLS` claims it.

Three taxonomy values go unused by the current rows: TC4 Internet, Cross-service design, Inventory and resources. They stay on the list, since an engagement's vocabulary is not defined by what has been tagged so far.

`engagement.md` also has a stale `Model version: 2.22` line to bump to 2.27.

## Tests

In `console/tests/`, beside the existing suites:

- `test_model.py`: `scope` is first in every `SHORT`, is in `LABELS` and `REQUIRED_ON_CREATE`.
- `test_integrity.py`: I24 fails on an off-list value, fails on a blank, and does not fire when `scopes` is None.
- `test_items.py`: an item with a Scope round-trips through `render_item` and `parse_item` with Scope directly after `status`; an item without one round-trips unchanged.
- `test_push_pages.py`: the built table carries a Scope column in the right position, and carries none for an engagement without scopes.
- `test_baseline_supports.py`: `Domain` and `Scope` headers both map to `scope`; an offered item inherits its trigger's Scope; the freeze refuses on a blank Scope and passes once set.
- `test_server_direct.py`: `## Scopes` parses; creating an item without a Scope is refused while scopes are declared and allowed while they are not.

`make test` runs them in the python image.

## Out of scope

- Rolling Scope up into the weekly SLT report or the meeting view. The filter comes first; whether a report should break down by scope is a separate question.
- Backfilling Scope into `engagements/test`. It is regenerated by `make anonymise` from abb-nokia and will carry scopes on the next run.
- The ingester in `solution-register`. It parses model 2.20, is not in the loop for a direct-mode engagement, and is ported when Adam chooses.
- Any change to how the Scope Taxonomy page itself is pulled or pushed. It remains a skipped view page.
