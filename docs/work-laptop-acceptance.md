# Work laptop acceptance

Version 1.1, 20 September 2026.

Use `/check-register-release` from Claude, including Opus, or follow these steps manually. No model-specific features or external AI service are required.

1. Check out the feature branch and run `make test`. Keep the real engagement outside the code checkout where practical. Point Docker at it only for actual use.
2. Copy a synthetic/sample engagement to a disposable folder. Start it on a spare port with `console/run.sh <copy> 18085` after ensuring that container name is available, or use a separately named Docker container. Do not stop or repoint an active production session to test this release.
3. Open the console with network access unavailable after the image is built. The table, review form and meeting agenda should load without CDN requests. Set Made by.
4. Clear an incorrect optional field. It should stay empty after reload. Attempting to change Status through a generic edit API must fail; normal status moves still ask for model requirements.
5. Open Rationalise. Correct a status directly in the table or item panel without a review form. Select several rows and use Set field to change status, scope and dates; clear a date. Reload and verify persistence, correction History and visible integrity findings. A mixed-type invalid status batch must write nothing. Click a Desktop by scope shortcut: only that scope should appear and normal workflow requirements must apply again. `tests/browser-rationalise.cjs` exercises this against a disposable fixture declaring at least one scope and two limitations.
6. Create a review of two conflicting duplicate records. Choose the survivor and resolve each conflicting field. Apply. Incoming links should target the survivor and the old ID should resolve through its alias. Test retyping similarly; splitting preserves the original as an index pointing at the new records.
7. Save a proposal, edit the item in another window, then apply the old proposal. It must refuse as stale. A bulk transition containing an invalid row must write nothing; select or explicitly apply valid rows only after reviewing the errors.
8. Open Recent operations and undo the latest register edit. Its previous content must return. A later external file edit must prevent undo from overwriting it. Crash recovery is covered by container tests; do not deliberately interrupt a real engagement.
9. Prepare a meeting from open items or a table selection. Reorder the agenda, discuss an item, save an outcome and reload. Order and progress must remain. Changing a record's state must not remove it from the agenda. Create one follow-up open item; repeated creation must be refused. Export the summary and check the stable MTG reference.
10. Filter a report by type, search and integrity rule. Its table, summary and gap count must describe the same item set. Historical corrections must appear separately from workflow movement; pending proposals must be labelled.
11. For a baseline-only fixture, the console should offer Import and review. It creates working registers and a review batch without a freeze screen. The old provenance/id map remains available internally for Confluence push compatibility.
12. For change-sets mode, review/meeting/view metadata must remain usable. Register writes require an explicit compatible `- Ingester model version: 2.30` or `2.31` in `engagement.md`. Do not declare compatibility until the sibling ingester has actually been ported. Historical correction application remains direct-only.
13. Run `/anonymise-register` against a disposable local source and private glossary. Export twice into new destinations and compare manifests. Inspect remaining content on the work laptop before transferring it.

Return failures with code commit, reproducible steps, expected and actual behaviour, and synthetic or reviewed anonymised examples. Do not include company data in cross-laptop handoffs.
