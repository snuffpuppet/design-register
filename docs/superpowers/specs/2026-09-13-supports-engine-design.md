# Supports engine: implied items, integrity and suggestions

Version 1.2, 13 September 2026. Owner: Adam Moyes. Status: built. 1.2: matches the build. 1.1: dismissals in Live go to a json file beside the registers, not a change set block, so the ingester sees only blocks it knows; the baseline order puts Missing supports after Row by row because supports are computed over accepted rows; S20 folds into S8 and the new rules are I21 to I23.

## Purpose

The register model (2.25) says, in sections 4.4 and 5, what must exist beside an item in a given state: a requirement in Draft has an open item, a limitation in Accepted has a decision, a change request has the limitation or requirement that triggered it. Section 9 checks those as failures after the fact. Nothing today offers the missing item.

The supports engine reads the same implications as data, finds every item whose supports are absent, and offers each missing support as a prefilled item the reviewer confirms, edits or dismisses. It runs in both console modes. In Baselining it fills the gaps in imported registers before the freeze. In Live it turns a transition into the transition plus its supports, in one change set.

The goals it serves, in order: less busy work for the person running the registers, a chain of records the SLT can read for progress, and a justification trail that answers "why did we do it this way" from one path of links.

## Principles

- The model stays the source of truth. The implications live in one table in `console/model.py` beside `TRANSITIONS`, and the model document gains the rules the table implies. A change to the model changes the table and nothing else.
- The engine drafts, a person approves. It never creates a decision in Accepted or a change request past Proposed. Anything that carries Approved by is offered in its first state with Approved by empty.
- The engine writes through the paths that exist. In Baselining an accepted suggestion is a candidate in `verdicts.json`. In Live it is a block in the current change set. No new write path touches item files.
- A suggestion is never applied silently. Every accepted support is visible as a candidate or a change set block with the item that implied it named in Source.

## The implication table

`SUPPORTS` in `model.py`. One row per implication. Fields:

| Field | Meaning |
|---|---|
| `when` | trigger type and the states in which the implication holds |
| `unless` | a condition that satisfies it: usually a link word present on the trigger, sometimes a field |
| `offer` | the type and first state of the item to create |
| `link` | the link word written on the trigger and its reverse on the new item |
| `copy` | fields prefilled from the trigger, as pairs of source field and target field |
| `rule` | the section 9 rule the implication satisfies |

Rows, derived from 4.4 and 5. The first sixteen restate rules the model already checks. The last four are new rules; S20 is folded into S8.

| # | When | Unless | Offer | Link on trigger | Copy | Rule |
|---|---|---|---|---|---|---|
| S1 | REQ Draft | link worked by | OI Open | worked by | owner, title as "Agree REQ: <title>", next action "Confirm the need with <owner> and set Phase" | I3 |
| S2 | DEC Proposed | link proposed by | OI Open | proposed by | owner, title as "Decide: <title>" | I3 |
| S3 | LIM Under assessment | link assessed by | OI Open | assessed by | owner, title as "Assess LIM: <title>", next action "Find the requirement this constrains; write constrains REQ-nnnn" | I3 |
| S4 | LIM Under assessment, Accepted, Change requested | link constrains | REQ Draft | constrains | title from LIM title rephrased as a need, owner empty with a prompt for the stakeholder, implemented-by from LIM | I7 |
| S5 | LIM Accepted | link dispositioned by DEC | DEC Proposed | dispositioned by | title "Accept: <LIM title>", rationale from Chosen option and the options it beat, consulted "Vendor", implemented-by from LIM, owner from LIM | I7 |
| S6 | LIM Change requested | link dispositioned by CR | CR Proposed | dispositioned by, CR carries triggered by | title from the chosen option, reason from Impact, chosen-option copied, implemented-by from LIM, owner from LIM, phase from the option's phase text | I7, I10 |
| S7 | CR Proposed, For approval, Submitted | link worked by | OI Open | worked by | owner, title "Progress CR: <title>", next action by state: shape and estimate, chase the approver, chase the implementer | I3 |
| S8 | CR any state | link triggered by | LIM Under assessment | triggered by | title from CR title as a fact about the platform, impact from Reason, owner from CR, implemented-by from CR, vendor-ref noted in Source | I10 |
| S9 | RSK Realised | link realised as | OI Open | realised as | owner, title "Respond: <RSK title>", next action from Mitigation | I13 |
| S10 | OI Closed | link resolves into | none: reviewer must choose a target or write "none: <reason>" | resolves into | | I9 |
| S11 | DEC Superseded | link superseded by | DEC Proposed | superseded by | title, rationale, consulted, implemented-by from old DEC | I8 |
| S12 | LIM Accepted with a DEC link | DEC is in Accepted | none: flag the DEC as needing approval | | | I7 |
| S13 | LIM Change requested with a CR link | CR not Withdrawn or Rejected | move LIM to Under assessment with S3's OI, relink as previously dispositioned by | | | I7, 4.4 |
| S14 | CR in Approved, Submitted, Delivered, Deferred, Withdrawn, Rejected | approved-by and closed-on filled | none: field prompt | | | I10 |
| S15 | LIM Accepted, Change requested | impact, two options, chosen-option filled | none: field prompt | | | I2 |
| S16 | REQ Designed, Delivered, Verified | source or a link names a design section | none: field prompt | | | 4.4 |
| S17 | RSK Mitigating whose Mitigation names an action | link mitigated by | OI Open | mitigated by | owner, title "Mitigate: <RSK title>", next action from Mitigation, due from RSK due | I21 new |
| S18 | LIM Accepted whose Chosen option text says a workaround needs something built | link needs | REQ Draft, implemented-by Internal | needs | title from the option text, owner from LIM | I22 new |
| S19 | CR Delivered | link delivers | none: reviewer picks the REQ, which then moves | delivers | | I23 new |
| S20 | folded into S8: a CR with no trigger is one case whatever its Vendor ref | | | | | |
| S21 | LIM Accepted whose Chosen option leaves the need wholly unmet | constrained REQ is Won't or its Phase is later | field prompt on the REQ, and S6's Deferred CR | | | I7, 4.4 |

S17 and S18 need two new link words: `mitigated by` from RSK to OI, and `needs` from LIM to REQ. Both go into `LINK_WORDS` and section 5.

S18 is the only row that reads text rather than a field. It looks for "build", "report", "tool", "script" or "extract" in the chosen option line. It is a warning, never a failure, so a miss costs nothing.

## Where each mode uses it

### Baselining

The candidate set is every table row on every non-skipped page, whatever state it claims. The engine runs over the effective candidates (verdicts applied, merges collapsed) and produces suggestions. A new tab, Missing supports, sits after Row by row. Each suggestion shows the trigger candidate, the rule, the offered item with its prefilled fields, and three verdicts: Accept, Edit then accept, Dismiss with a reason.

Accepting creates a candidate with:

- `source` "Baselined from <page>; implied by <source id> under <rule>"
- `raised-on` copied from the trigger
- the link on the trigger's candidate and the reverse on the new one, using candidate keys until the freeze maps them to ids
- `implied: true` so the freeze and the push can mark it

Dismissing records the reason in `verdicts.json` and the suggestion does not return unless the trigger changes.

The engine reruns after every verdict, so accepting S4's requirement may retire S8's suggestion on a related change request. Order of work in the view: Duplicates, then Row by row, then Missing supports, then Freeze. Supports are computed over accepted candidates, so the pass comes first. The note at the top of the Baseline view and the guide page gain that step.

The reconstruction choice. A source limitation already marked Accepted with no decision anywhere is offered S5 in two forms on the same row:

- Reconstruct: a DEC in Proposed with Rationale from the chosen option, flagged "reconstructed at baseline" in Notes. The reviewer sets Approved by from what the source page or the meeting record says and moves it to Accepted in the editor before the freeze, or leaves it Proposed and the LIM drops to Under assessment at the freeze.
- Reassess: the LIM goes to Under assessment and S3's open item is offered instead.

The default is Reconstruct where the source row carries a rationale or a chosen option, and Reassess where it carries neither.

The freeze refuses to run while any suggestion under a failure rule is undecided. Suggestions under warning rules (I15, I16, S18) do not block. Freezing remaps every candidate id in every field, including the implied ones, and `baseline/frozen.md` lists the implied items under "Implied at baseline", with an "Items by type" line.

### Live

The engine runs over the overlay of item files plus change sets. Suggestions appear in two places:

- On an item's view, a Supports needed panel listing what the item's state implies and is missing, each with Accept and Dismiss.
- On Outstanding, a Register gaps note.

When a transition is made in the console, the transition dialog shows the supports the new state will need before the move is confirmed. Confirming writes the transition block and the support blocks to the same change set, in that order, with the support's Source naming the transition. The reviewer can untick a support and the transition still proceeds; the missing support then appears on the item's panel.

Dismissals in Live are recorded in `<engagement>/supports-dismissed.json` with the rule, the item, the reason, who and when, so the change sets carry only blocks the ingester knows. A dismissed key stays dismissed until removed from that file.

The weekly SLT report gains one line per rule with a non-zero count, headed "Register gaps", after the existing sections.

## What the engine never does

- Create a DEC in Accepted or Rejected, or a CR past Proposed.
- Fill Approved by.
- Guess a stakeholder for a REQ raised from a limitation. The owner is left empty and the candidate cannot be accepted until it is set.
- Write an item file.
- Apply a suggestion without a verdict.

## Changes by file

| Path | Change |
|---|---|
| `solution-register-model.md` | Bump to 2.25. Section 5 gains `mitigated by` and `needs`. Section 9 gains I21 to I23. A sentence in section 10 says the console offers a fix for each failing item. Dated line at the top. |
| `console/model.py` | `SUPPORTS` table, two link words, the three new rules as `RULES`. |
| `console/integrity.py` | New. `check(items, phases, stakeholders, today) -> failures, warnings, prompts, suggestions`. Pure function over a list of item dicts. Section 9 rules I1 to I17 and I19, plus the `SUPPORTS` table (S1 to S19 and S21; S20 is folded into S8). I18 and I20 are not checked here; I20 is checked by the transition endpoint. |
| `console/baseline.py` | Suggestions over effective candidates; verdicts Accept, Edit then accept, Dismiss with a reason, and for a limitation's disposition Reconstruct or Reassess, on suggestion keys; accepted suggestions stored as implied candidates under `_implied` in `verdicts.json`, linked both ways; freeze guard. |
| `console/server.py` | `/api/integrity` for Live; `/api/baseline` gains `suggestions`; `/api/baseline/support` for verdicts; `/api/transition` returns the supports the target state needs and accepts a list of supports to write with the move. |
| `console/static/app.js` | Missing supports tab; Supports needed panel on the item view; supports in the transition dialog; Register gaps note on Outstanding; the line in the SLT report. |
| `console/static/guide.html`, `console/confluence-runbook.md`, `console/README.md` | The new step in the baseline order and the Live behaviour. |
| `console/make-sample.py`, `console/sample-baseline/` | Sample pages gain rows that trip S4, S5, S6, S8 and S17, so the tab has content in the test engagement. |

## Testing

- `integrity.py` gets a test file run in the console image: one fixture per row S1 to S21, each asserting the suggestion appears with the expected prefilled fields, and a fixture where the support exists asserting silence.
- The reconstruction default is tested both ways.
- The baseline is exercised on `test-data/puppy-gloves` in Chrome: work Duplicates, then Missing supports to zero, then freeze, and confirm `frozen.md` lists the implied items and the registers pass `check()` with no failures.
- Live is exercised by moving a LIM to Change requested in the console and reading the change set: one transition block and one CR block, linked both ways.

## Out of scope

- The ingester. It stays at model 2.20 and is ported separately. The change sets the engine writes use the existing block format, so nothing new is needed for them to apply.
- Automatic owner assignment from the stakeholder register.
- Pushing implied items to Confluence differently from any other item. They are rows like the rest, with Source saying they were implied.

## Open questions

- Whether S8 should offer a REQ directly when the CR's Reason plainly states a need and no limitation is involved. The model says LIM first, and this spec follows it; revisit after the first real baseline.
- Whether the SLT report should show gaps at all, or only the console. Gaps are register hygiene, and the SLT may not care. Default here is to show them, one line per rule, and drop them if unwanted.
