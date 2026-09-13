---
name: handoff
description: Use at the end of a working session, or when asked to hand off, wrap up, pause, or leave notes for the next session. Writes a handoff keyed on the objective being pursued, at an altitude that stays useful if the next session is days or weeks later.
---

# Hand off to the next session

Write `handoffs/<objective-slug>.md`, one file per objective, replacing any earlier handoff for the same objective. The file is committed with the work, so it travels to any machine that pulls the repository.

**Invocation:** `/handoff [guide]`. The argument is free text and is a guide to the objective, not a file name: `/handoff baseline abb-nokia`, `/handoff getting the push working`, `/handoff the SLT report`. Use it to decide which objective this handoff is about:

1. Read `handoffs/README.md`. If an existing handoff's title or slug matches the guide, this handoff replaces it and keeps its slug.
2. If none matches, this is a new objective. Write its title from the guide in the user's terms, and derive a short slug from it.
3. If the guide is ambiguous between two existing handoffs, ask which.

With no argument, re-establish the objective from the session itself: what the user has been driving at across the conversation, in their words, not the last task done. Check it against `handoffs/README.md` the same way. If the session served two objectives, write two files and say so. If you cannot name the objective with confidence, ask in one line rather than guessing.

## Altitude

A handoff is read by someone who was not here and may arrive after other sessions have moved things on. So:

- Name the objective and why it matters, in two sentences a stranger could act on.
- Say where things stand as facts that can be checked, not as a narrative of the session. "Freeze writes item files; verified on a copy" rather than "we then built the freeze".
- Give next steps in order, each one startable on its own, each saying how to tell it is done.
- Record decisions taken on purpose with the alternative rejected, so the next session does not reopen them without a reason.
- List anchors: the files, commits, config keys and documents whose change would mean the handoff needs rechecking. `/resume` uses these to judge relevance.
- Leave out anything the repository already records: code structure, commit messages, what the docs say. Point at them instead.

## File shape

```
---
objective: <slug>
title: <the objective in one line>
written: <D Month YYYY>
commit: <short sha of HEAD when written>
branch: <branch>
status: active | parked | done
model-version: <from solution-register-model.md>
---

## Objective
## Where things stand
## Next steps
## Decisions taken on purpose
## Open questions for the user
## Watch out for
## Anchors
- files: <paths, one per line>
- docs: <paths>
- config: <keys in confluence.json or elsewhere>
- external: <things outside the repository, such as the work machine, a connector, an engagement folder there>
```

## Steps

1. Read `git status` and `git log --oneline -20` so the handoff names the real commit and notes anything uncommitted.
2. Read any existing `handoffs/*.md`. If one has the same objective, replace it; if a different objective is marked active and the session did not touch it, leave it alone and say so in chat.
3. Write the file. Bump `written` and `commit`. Update `handoffs/README.md`, the index: one line per handoff, `- [title](file) · status · written`.
4. Do not commit unless the user asks, and say so.

## Never

- Write session narrative, tool output, or a list of every change made.
- Put anything in the handoff that CLAUDE.md, README.md or ARCHITECTURE.md should hold instead. If a rule or a fact belongs there, put it there and point at it.
- Mark an objective done unless the user said it is.
