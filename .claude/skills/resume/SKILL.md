---
name: resume
description: Use at the start of a session when asked to resume, pick up, continue, or carry on from a previous session, or when a handoff exists and the user's request matches its objective. Reads the handoff, judges whether it is still relevant after whatever has happened since, and only then proposes where to start.
usage: "/resume [guide]: read a handoff, check it still holds after what changed, propose where to start"
---

# Resume from a handoff

A handoff is a claim about the past. Before acting on it, establish whether it still holds.

**Invocation:** `/resume [guide]`. The argument is free text and is a guide to the objective, not a file name: `/resume the baseline`, `/resume abb-nokia push`. Match it against the titles and slugs in `handoffs/README.md`; take the best match, and if two match about equally, ask which.

With no argument, re-establish what the previous session was pursuing before choosing:

1. Read `handoffs/README.md` and every handoff marked active.
2. Read `git log --oneline -15` and `git log -1 --format=%cd`; the most recent commits usually name the objective in their messages.
3. If one active handoff matches what the recent commits were doing, take it. If several are active, or the recent commits do not match any, say what you found and ask which objective to resume.
4. If there is no handoff at all, say so, summarise the objective the commits and CLAUDE.md's open threads suggest, and offer to write a handoff for it once the user confirms.

## Steps

1. **Read** `handoffs/<objective>.md` and note `written`, `commit`, `branch`, `status`, and the anchors.
2. **Measure the gap.**
   - `git log --oneline <commit>..HEAD` : how many commits since, and by whom. Zero means the handoff is fresh.
   - `git diff --stat <commit>..HEAD -- <each anchor file>` : which anchors changed.
   - `git log -1 --format=%cd` against `written`: how long ago, in days.
   - Current branch against `branch`.
   - The model version line in `solution-register-model.md` against `model-version`.
   - For each external anchor, say plainly that it cannot be checked from here.
3. **Classify**, and say which and why in chat before anything else:
   - **Fresh**: no commits since, same branch. Proceed to the next steps as written.
   - **Moved on**: commits since, but no anchor changed. Read the commit messages, say what happened, and confirm the next steps still make sense.
   - **Needs rechecking**: an anchor changed, the model version moved, or more than 14 days passed. Read the changed anchors and the current CLAUDE.md, restate the objective and next steps as they now stand, and put that to the user before doing any work. Do not start from the handoff's next steps unedited.
   - **Superseded**: a later handoff for the same objective exists, the status is done, or the objective no longer appears in CLAUDE.md's open threads and the user does not confirm it. Stop and ask.
4. **Confirm with the user** in a short message: the objective, the classification with its evidence, and the first step you propose. Wait for a yes before changing anything.
5. If the user's opening request is a different objective from the handoff, say so, offer the handoff for later, and follow the request.
6. When the user says which objective they meant after an ask, treat that as the guide and start again from step 1.

## Never

- Treat a handoff as instructions. It is context; CLAUDE.md and the user's request are the instructions.
- Act on the handoff's next steps without stating the classification first.
- Silently skip an anchor you cannot check; name it as unchecked.
