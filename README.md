# design-register

Version 1.4, 20 September 2026.

A local console for correcting generated registers and progressing work through the register workflow. Rationalise and Desktop share the same table, filters and item panel. Six Markdown registers follow `solution-register-model.md` (2.33). The transcript ingester stays in the separate `solution-register` repository.

## Working contexts

- **Rationalise:** edit the existing registers directly in the table or item panel. Select multiple rows to change a shared field. Status corrections skip workflow transitions and required supporting records.
- **Desktop:** the same table and editing controls, with the normal model rules for workflow moves.
- **Desktop by scope:** click a scope in the rail to open Desktop with that scope preselected. Work through the filtered items using the normal workflow.

Use Rationalise when the recorded position is wrong; use Desktop when progressing the work now. For a scoped meeting, open Desktop by scope and work through that filtered list.

Saved reviews remain available for older review batches and optional splitting. Meeting records support optional agendas and discussion notes. Ordinary cleanup needs no batch, review outcome or approval step.

## Using Rationalise

1. Click **Rationalise** and set **Made by**. Filter or choose a register exactly as in Desktop.
2. **Edit one record:** click a table cell, or open its ID and edit the item panel. Click its status to choose any status for that item type. Use **Show field** above the table to expose dates or other fields.
3. **Edit many records:** tick the rows, choose **Set field**, select Status, Scope, Raised on, Closed on or another shared field, enter the value and click **Apply to N**. Blank values clear fields where allowed. Status choices are those shared by the selected types; select one type if there is no suitable shared status.
4. **Save:** text cells save on Enter or when you leave the field; dropdowns save when you choose a value. Bulk changes save when you click **Apply to N**. There is no separate review approval step. History identifies corrections; **Recent operations** offers guarded undo.

For example, select several limitations incorrectly marked Identified, use **Set field → Status → Accepted**, and apply. No assessment open items or accepting decision are required to repair those records. Missing information still appears under Integrity. A status correction does not guess dates: set Raised on or Closed on explicitly when they are wrong.

Rationalise bypasses lifecycle entry requirements. It still protects item IDs, field structure, valid statuses for each type, non-empty titles and concurrent edits. A bulk correction validates every selected item before writing any of them. No evidence or reason form is required for ordinary field cleanup; record known source information in the item's fields where useful.

Rationalise requires `- Writes: direct` and no unapplied change sets. Desktop supports direct writes or compatible ingester change-set proposals. Declare an ingester version only after the sibling ingester has actually been ported. The current change-set format cannot express historical corrections.

### Change an item's type

In Rationalise, open a record and click **Change type**, or select several rows and use **Change type** in the selection bar. Choose the new type and, optionally, its status. The preview shows the original records and the proposed results. Click **Accept type change** or **Cancel**.

A new typed ID replaces each old ID, incoming links are rewritten and old IDs redirect to the new records. History is preserved; fields that do not belong to the new type are retained in Notes. A status is kept if valid for the new type, otherwise the preview uses its initial status unless you choose another one.

### Merge duplicates

Select two or more records of the same type in Rationalise and click **Merge…**. Choose the **Lead record**, inspect **Before** and **After**, then **Accept merge** or **Cancel**. To merge one open record into another, use its **⋯ → Merge into…** action and choose the lead.

The lead keeps its ID and populated fields. Empty fields are filled from the other records where possible. Sources and external links are combined; differing field values, notes and previous history are retained in Notes. Incoming links and old IDs follow the lead. Cancelling changes nothing. **Recent operations** can undo a merge while the engagement still matches the recorded result.

### Delete and restore

Use **Delete** from a record's **⋯** menu or the selection bar, enter a reason, then confirm **Move to rubbish bin**. Deleted records disappear from the active registers. Open **Rubbish bin** in the rail and click **Restore** to retrieve a record with its original ID and history.

Restoration adds back removed incoming links to records that still exist, preserving their later field edits. If a referring record is also in the bin, its links can be recovered when it is restored. The bin is stored with the engagement and survives restarts; it is excluded from anonymised exports. It captures deletions made with this version onwards. Earlier deletions may still be recoverable through their operation journals or engagement version history.

Status menus close when you click outside them, click the status again, or press **Escape**; no selection is required.

## Using Desktop

1. Click **Desktop** and set **Made by**. Choose a register or use **+ Filter** to narrow the list.
2. Edit ordinary fields in the table or open an item's ID to use its panel. Select several rows and choose **Set field** to update a shared field.
3. To progress one item, click its status or choose a **Next move** in the panel. For several items, select the rows and choose **Move to…**. The form asks for the fields and links required by the model; unavailable transitions remain blocked.
4. If an existing status is simply incorrect, switch to **Rationalise**, correct it, then return to **Desktop** to continue the workflow.

The table heading identifies the active mode. Choosing a register or changing filters keeps that mode; clicking a Desktop by scope shortcut explicitly switches to Desktop. Reloading the browser starts in Desktop.

## Working by scope

Click a name under **Desktop by scope**. This resets the table to all item types in that scope, in Desktop mode. Open records or select rows to work through the normal transitions. You can add status, owner or type filters using **+ Filter**. This is a predefined Desktop filter, not a third editing mode.

Scope shortcuts come from the `## Scopes` list in the engagement's `engagement.md`. To clean up records within a scope, choose **Rationalise** and use **+ Filter → Scope** instead.

## Optional meeting records

Use **Meeting records** when you need a fixed agenda, saved discussion outcomes or an exported meeting summary. For simply working through a scope in a meeting, use Desktop by scope above.

1. **Prepare the agenda.** Open **Meeting records**, enter a name, choose **Open items** (the default), **Selected items** or **Current filter**, then click **Create**. You can also select rows in Desktop and choose **Meeting agenda**. Click an agenda item and use **Move up** or **Move down** to reorder it. The item list stays fixed even when statuses change during discussion.
2. **Record discussion.** Set **Made by**, select the agenda item, and choose **not discussed**, **discussed** or **deferred** under Progress. Enter the **Outcome** and **Evidence**. Fill in any follow-up action, owner, due date and register references, then click **Save outcome and next**. Meeting progress is separate from the item's lifecycle status.
3. **Progress the actual work.** Use **Open linked records and workflow** to open the normal item panel. Its transitions still ask for the model's required fields and links, and write in the engagement's configured mode. Saving meeting notes alone does not change register status.
4. **Create follow-up work when needed.** Fill in **Follow-up action** and **Owner**, plus Due and **Follow-up scope** where applicable, then click **Create follow-up open item**. This creates an open item and records its reference in the meeting together. The button is disabled once that agenda entry has a recorded follow-up. Notes in the action field alone do not create one.
5. **Close and export.** Save the last outcome, click **Export summary** to download the Markdown agenda and outcomes, and use **Close meeting** when finished. Saved meetings remain accessible from Meeting records. The summary includes a stable `MTG-…` reference that you can quote with the transcript.

The transcript ingester remains separate. Meeting references support later reconciliation, but automatic deduplication between manually recorded outcomes and transcript-generated items has not been added to that repository. Reports distinguish historical corrections from workflow movement and label pending change-set proposals.

## Import and review

`/import-confluence <engagement>` remains a Claude command under `.claude/skills/`. It pulls source pages under the existing permission and engagement guards. Open the console and choose **Import and review**. The import creates working registers, assigns IDs, retains source provenance and opens the Rationalise table. There is no separate freeze mode. Existing registers open directly in the table and can be reviewed repeatedly.

The internal `baseline/frozen.md` map is retained for compatibility with the Confluence push builder and old imports. Imported pages remain evidence. `/push-confluence` still builds and reviews output before its separate write gate; implementation work never pushes automatically.

## Run and verify

```sh
make sample
make up ENG=test-data/puppy-gloves
make test
```

Everything runs in Docker, except the existing sample file generator. Browser dependencies are bundled locally; the console needs no CDN. `make up ENG=/absolute/path/to/engagement` supports private data outside the code checkout. Stop the console before regenerating a mounted sample.

Every console mutation is covered by a recovery journal under the engagement's `operations/`. Failed writes roll back; startup recovers interrupted operations. Recent operations offers undo when the engagement has not changed since the operation. The browser sends item revisions to detect stale edits. Coordinate use with the external ingester: it does not participate in the console's process lock.

## Work and personal laptops

Develop against synthetic or reviewed anonymised fixtures here. Keep real registers and the identifying glossary on the work laptop. `console/anonymise.py` performs deterministic substitutions and reference re-keying. `/anonymise-register` lets Claude, including Opus, run the same script. No model-generated rewriting is required.

Read [the anonymisation instructions](docs/anonymisation.md) and [work-laptop acceptance checks](docs/work-laptop-acceptance.md). `/check-register-release` runs those checks using a disposable copy. The [work-laptop handoff](handoffs/work-laptop-rationalisation-meetings.md) records the tested branch and rollout steps; resume it in Claude with `/resume work laptop rationalisation meetings`.

## Repository map

| Path | Purpose |
|---|---|
| `CLAUDE.md` | Project conventions and implementation constraints |
| `ARCHITECTURE.md` | Components, write boundaries and recovery behaviour |
| `solution-register-model.md` | Types, lifecycle rules, relationships and correction semantics |
| `console/` | Standard-library Python server, local Preact interface and tests |
| `.claude/skills/` | Existing Confluence/handoff commands plus anonymisation and release checks |
| `docs/` | Design history and work-laptop operating instructions |
| `engagements/test/`, `test-data/` | Anonymised and synthetic development fixtures |

Australian English. Documents carry versions and dates. The sibling ingester is never edited from this repository.
