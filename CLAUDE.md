# design-register

Version 1.3, 21 September 2026.

Read `README.md` first. This file holds coding-session constraints and non-obvious operating rules.

## Purpose and boundaries

This repository owns the solution register model (2.34), local console, rationalisation and meeting tools, and Confluence import/push path. The sibling `../solution-register` owns transcript ingestion and is **never edited from here**. Its documented model is still 2.20 until Adam ports it. Declare a compatible ingester version only after that work actually happens.

Real source registers and the identifying glossary stay on the work laptop. This checkout contains synthetic or reviewed anonymised fixtures. Generic anonymisation code is tracked in `console/anonymise.py`; the private glossary is not. `docs/anonymisation.md` describes the deterministic format and review boundary. Opus can run `.claude/skills/anonymise-register/` without performing free-form rewriting.

## Working contexts

- **Rationalise** uses the shared table for immediate single/bulk corrections via `/api/rationalise/edit`, without workflow transitions, required supporting records or a review/evidence form. Keep field structure, valid statuses, revisions, transaction rollback and history. Immediate type changes and lead-first merges use before/after previews; structured reviews remain optional for older batches and splits. Do not manufacture intermediate open items or guessed approvals to repair a generated register.
- **Desktop by scope** is a predefined scope filter in Desktop, retaining workflow rules.
- **Desktop** follows the normal model transitions and required-field checks.
- **Meetings** retain a fixed agenda, outcomes, action references and stable session ID. Workflow writes still use Desktop operations.
- `- Writes: direct` versus `change-sets` is a separate persistence choice. Review, meeting and view metadata work in both modes. Historical correction application and structural register operations require direct mode. Do not invent incompatible ingester blocks.
- There is **no user-facing freeze mode**. A baseline-only input offers Import and review, which writes working registers and opens a review. `baseline.freeze()` and `baseline/frozen.md` remain internal provenance/push compatibility mechanisms. The previous `static/old/` frontend is not the entry point and should not be extended.

## Write rules

- HTTP mutations run through `operations.transaction` under the server lock. Register writes use `commit()` in `server.py`; coordinated link rewrites and legacy renumber moves remain inside that transaction. Do not add an unjournalled API write path.
- Generic edits accept only fields belonging to the type. Status changes use a workflow transition or a review correction. Empty strings explicitly clear fields in direct mode; change-set clearing is unsupported and refused.
- Bulk preflight runs before writes. A mixed-validity batch writes nothing unless the request explicitly chooses `applyValid`.
- Item revisions detect stale browser edits. Review and meeting records have their own revision. Preserve both protections when changing forms.
- Recovery journals contain private snapshots. Startup recovers prepared operations; undo refuses changed engagement content. Coordinate with the ingester rather than running two writers concurrently.
- Immediate Rationalise merge keeps lead values, fills blanks and preserves differing values/history in Notes. Its preview token protects acceptance from stale data. Legacy structured reviews retain explicit conflict choices. Merges record aliases. Retype rewrites incoming links and preserves the old ID as an alias. Split keeps the original as an index to the new items. Published IDs stay stable. Renumber is a legacy operation requiring `allowUnpublished`, a clean engagement git tree and an unused staging range.
- Delete archives the record and incoming links in private `rubbish-bin.json`; restore preserves the original ID and later edits to referring records. Keep bin content excluded from anonymised exports.
- The model document remains authoritative; `console/model.py` holds field/state/rule data. Bump and date the model when its semantics change. Review semantics are section 12; item and change-set wire formats remain unchanged.
- Scope is declared by engagement. `required_on_create()` applies that conditionality. A follow-up item in a scoped engagement must ask for Scope.

## Run and test

Everything runs in Docker. `make up ENG=<folder>` starts the console; `make test` builds and runs the Python suite in the image. Do not substitute a host Python server when Docker is down. The existing `make sample` host script only writes fixture files; stop a mounted sample before regenerating it.

Pinned Preact and htm libraries are in `console/static/vendor/`. No runtime CDN dependency. UI code remains small modules without a build step. `console/tests/browser-smoke.cjs` runs in the Puppeteer image against a disposable sample container. Never use a real engagement for browser mutations. `docs/work-laptop-acceptance.md` lists release checks and expected outcomes.

`make up` remembers the engagement in ignored `docker-compose.override.yaml`. Pass `ENG=` deliberately. Keep the current console running while testing another container on a spare port. Python code changes require process restart; static assets reload in the browser.

## Claude commands and Confluence

Commands remain under `.claude/skills/`, with a `usage:` frontmatter line discovered by `.claude/hooks/list-commands.sh`. Do not move them into a different agent's directory. New `/anonymise-register` and `/check-register-release` wrap deterministic scripts and acceptance instructions. Existing `/handoff` and `/resume` remain available.

Confluence reads/writes use `confluence.json`, the declared parent and direct children, and the existing permission log. `ask` means ask and record the answer. Never change engagement/source guards to make a refusal pass. No live connector behaviour has been validated by this feature implementation. `/push-confluence` still reviews built output and checks page versions before sending.

## Change proposals (2.34)

Internal CR records are Change proposals. Preserve CR IDs, `change-requests/`, existing statuses and vendor references. Source must name the solution design; `based on DEC-…` optionally references the chosen approach. Requirements have optional Options. `proposal_upgrade.py` is a read-only inventory, not a writer. See `docs/change-proposal-upgrade.md` for work-laptop rollout. Do not declare the external ingester ported or silently rewrite old records.

## Main files

`server.py`: coordination and API. `items.py`: item files. `model.py`: model data. `integrity.py`: pure findings/provenance. `workspaces.py`: review/meeting state. `operations.py`: journal/recovery/events. `views.py`: filter/report semantics. `anonymise.py`: deterministic export. `static/workspaces.js`: shared review/meeting interface. `static/store.js`: browser state and revision-aware requests.

## Conventions

Australian English. No em dashes or "not x but y" framing. Documents carry a version and date. Preserve actual source evidence and distinguish recorded date from historical effective date. Item History and private operation journals complement git history. Commits use any attribution lines supplied by the session; never invent them.
