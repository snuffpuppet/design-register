---
name: check-register-release
description: Validate a register-console code update on the work laptop against a disposable engagement copy and report sanitised failures.
usage: "/check-register-release: run container tests and the work-laptop acceptance checks"
---

# Check a register release

Version 1.0, 19 September 2026.

Read `CLAUDE.md` and `docs/work-laptop-acceptance.md`. Run `make test`. Use a disposable copy for the interactive acceptance checks; do not change the real registers to test a release. Keep the separate ingester repository untouched.

The acceptance document specifies expected outcomes. Report each checked behaviour as passed, failed or not exercised. A passing unit suite does not imply browser checks passed. If Docker is unavailable, report that prerequisite without substituting a host server.

When returning a defect to the personal laptop, reproduce it using the sample or export a fixture with `/anonymise-register`. Include the code commit, operation, expected result and sanitised actual result. Keep source contents, private paths and identifying glossary entries on the work laptop.
