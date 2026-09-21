# Migrate internal CRs to Change proposals

Version 2.0, 21 September 2026. Model 2.35.

**This version performs the actual migration.** Version 2.34 only changed the display name; that did not distinguish our records from the vendor's CRs. Follow these steps even if you already ran the earlier inventory.

- Internal `CR-0001` becomes **`CP-0001`**, in **`change-proposals/CP-0001.md`**. The numeric suffix stays the same.
- The vendor's CR number/link stays unchanged in **Vendor ref**, even if it happens to match an old internal ID.
- Structured register links, saved-view type filters, review/meeting identities, rubbish-bin records and internal baseline-map destinations are updated.
- Original item history, titles, narrative, Source citations and raw imported pages remain unchanged. The journal records who migrated and the full ID mapping; aliases keep old internal CR URLs resolvable.
- Existing lifecycle statuses remain unchanged. `Submitted` still means handed to the implementer; LIM `Change requested` still means dispositioned through a proposal.

`proposal-check` is **preview only**. Its output is a plan for you or your work-laptop agent to inspect. **`proposal-migrate` applies it**; no free-form rewriting by an agent is required.

## Work-laptop steps

Run from the repository folder. Replace `/absolute/path/to/engagement`, the operator and the token below with actual values. Retain your usual port if it differs from 8085.

1. Stop the console with `make down` and stop the separate ingester or any other writer. Back up the **whole engagement folder**, including hidden files, journals and rubbish bin. Record the current code commit with `git rev-parse HEAD`. Resolve unapplied change sets through the existing ingester before upgrading; the migration refuses them.
2. Preserve any local code changes shown by `git status`, then pull the update on `feature/rationalisation-meetings` with `git pull --ff-only`. Check that `console/model.py` declares model **2.35** and `"CP": "change-proposals"`.
3. Preview the migration:

   ```sh
   make proposal-check ENG=/absolute/path/to/engagement
   ```

   This mounts the engagement read-only. Check the `CR-… → CP-…` mapping and changed paths. It refuses malformed records, existing/reserved CP ID collisions, unapplied change sets and interrupted operations. Keep the **Preview token** printed at the end. Missing dates, estimates or design references are not invented.
4. Apply that exact preview:

   ```sh
   make proposal-migrate ENG=/absolute/path/to/engagement MADE_BY="Your name" EXPECT=PASTE_PREVIEW_TOKEN_HERE
   ```

   This is the data migration. It requires a named operator and a matching token; if the engagement changed after preview, run the preview again. File moves and link/metadata updates happen in one recovery-journal transaction. Failures roll back. The current console and migration share an exclusive writer lock; older consoles and the external ingester must still be stopped explicitly.
5. Run the check again:

   ```sh
   make proposal-check ENG=/absolute/path/to/engagement
   ```

   Expect **0 active CR records**, **0 internal IDs to migrate**, and no Write/Remove paths. Re-running apply after completion is also a no-op.
6. Start the updated console and refresh the browser:

   ```sh
   make up ENG=/absolute/path/to/engagement PORT=8085
   ```

   Check a known **CP-…** record, its history, incoming links and unchanged Vendor ref. Open an old `/#item/CR-…` URL and confirm it resolves to the CP. Check **Outstanding proposals** and a saved scope/phase view. The server refuses to start with unmigrated active or binned internal CR records rather than silently omitting them.

Review/meeting IDs are retained. When migrated identities affect a review, its old item approval revision stays stale: reconfirm it before applying an outstanding review. This deliberately preserves stale-edit protection. Old CRs in preserved narrative/history are historical citations, not active record IDs. If a saved report name itself says CR, you can rename that caption separately; its type filter is migrated automatically.

## After migration

Use **Outstanding proposals** to see unfinished and deferred work by scope and phase. Source should reference the solution design and section. Keep lightweight Options on the requirement/limitation and use `based on DEC-…` where a separate Decision selected the approach. Estimate should state Indicative or Confirmed, cost, duration/effort, source and date; blank remains **Not sized**, never zero. Fill missing facts only from evidence.

The separate `solution-register` ingester is **not ported by this update**. It must support `CP` IDs, `change-proposals/`, Options and proposal relationships before resuming writes to the migrated engagement. Do not falsely change its declared version. The console requires a declared 2.35 ingester for change-set writes; direct console work remains available without that declaration. No live Confluence publication occurs during migration.

## Recovery and rollback

For an interrupted migration or earlier prepared operation, keep all writers stopped and run:

```sh
make proposal-recover ENG=/absolute/path/to/engagement
```

This restores prepared transaction snapshots and prints a fresh preview. Inspect it, then apply using its new token. Ordinary exceptions already roll back automatically.

For rollback to old code, stop writers and deliberately restore the pre-migration engagement backup together with the matching old code. Do not run an older writer against CP files. Account for any subsequent work before restoring a backup. Historical operation journals are retained unchanged; do not use an old undo operation to restore a CR-era snapshot under the new model.
