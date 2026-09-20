# Change proposal upgrade on the work laptop

Version 1.0, 21 September 2026. Model 2.34.

The internal **Change request** register is now **Change proposals**. Existing CR records load under the new name automatically. Keep `CR-…` IDs, the `change-requests/` folder, links, history, vendor references and existing status values. No bulk retype, renumber or file rewrite is needed. This upgrade does not edit engagement data at startup.

A proposal tracks outstanding work discovered through iterative requirements and solution design. It links to the design in Source and to its triggering requirement or limitation. Lightweight options stay upstream; requirements now support an optional Options section. Where a Decision selected the approach, use **based on DEC-…**. Proposal approval authorises cost and delivery. The vendor manages its own change request, referenced in Vendor ref when one exists.

## Pull and check

Use the repository folder on the work laptop. Replace `/absolute/path/to/engagement` below with the actual engagement folder, and retain your usual port if different from 8085.

1. Stop the console with `make down`, and pause the separate ingester or other writers. Back up the **whole engagement folder**, including hidden files, journals and rubbish bin, using your normal work-laptop backup process. Record the current repo commit with `git rev-parse HEAD` for rollback.
2. Check `git status`. Preserve any local code changes before pulling; do not discard them. Pull the published update on `feature/rationalisation-meetings` using `git pull --ff-only`. Confirm `console/model.py` declares `MODEL_VERSION = "2.34"`. If not, the update has not reached your checkout.
3. Run the read-only compatibility inventory:

   ```sh
   make proposal-check ENG=/absolute/path/to/engagement
   ```

   It builds the image and mounts the engagement read-only. Every existing CR is listed with its status, scope, phase, estimate, vendor reference and Source. Errors identify unrecognised statuses or malformed records; resolve these deliberately before proceeding. Missing facts are review work, not a reason to fabricate values. No report file is created; terminal output may contain private register content.
4. Start the updated console against the same engagement:

   ```sh
   make up ENG=/absolute/path/to/engagement PORT=8085
   ```

5. Refresh the browser. Open **Change proposals** under Registers and check a known CR's ID, history, incoming links and Vendor ref. Its status should be unchanged. `Submitted` still means handed to the implementer; LIM `Change requested` still means dispositioned through a proposal. Neither requires renaming historical records.

## Review the existing proposals

In Rationalise, set Made by and correct only facts supported by evidence:

- **Source:** ensure it includes the solution design and relevant section. Keep existing citations. The inventory cannot decide whether a citation is a valid design reference; review this manually.
- **Scope / Phase:** set the delivery scope and intended phase, including deferred work. Leave unknown values visible until confirmed.
- **Estimate:** use `Indicative` or `Confirmed`, followed by cost, duration/effort, source and date. Blank displays as **Not sized**, never zero. No automatic cost total is calculated from these free-text values.
- **Vendor ref:** retain the vendor's ID/link. Blank may mean no vendor request exists yet, or that none is needed for internal delivery. Vendor ref is required by the existing Desktop rule on handover (`Submitted`) for Vendor implementation.
- **Links:** retain `triggered by` and any limitation disposition links. Add `based on DEC-…` if a separate Decision selected the option. No new Decision is needed just to restate proposal approval.

Use **Outstanding proposals** under Work for all unfinished proposals, including Deferred. This opens the shared table without switching editing mode and shows scope, phase, estimate, implementer, vendor reference and Source. Choose Phase and use **+ Filter → Scope**, or Rationalise's Scope dropdown, to prepare a Phase 1 / Enterprise Ethernet view. **No phase** exposes unallocated work. The view includes unsized and not-yet-approved proposals. Save the current view to reuse its filters and columns in Reports; existing saved views are preserved.

## Compatibility and rollback

The separate `solution-register` ingester is not changed or declared compatible by this update. Keep the engagement's declared ingester version accurate. Before using new requirement Options or `based on` links through a change-set ingester, port and verify that support there. Direct console writes retain the existing journalled transaction and recovery boundary.

Before any new edits, rollback is a code rollback and restart because the upgrade does not rewrite data. After edits using new Options or relationships, do not run an older writer without checking field preservation. Restore a backup only deliberately, with writers stopped, accounting for work recorded since that backup. No live Confluence publication is part of this upgrade.
