#!/bin/sh
# SessionStart hook: print the project's local slash commands, one line each, from .claude/skills/*/SKILL.md.
# A skill's "usage:" frontmatter line is used when present; otherwise the first clause of its description.
cd "$(dirname "$0")/../.." || exit 0
out=""
for f in .claude/skills/*/SKILL.md; do
  [ -f "$f" ] || continue
  name=$(sed -n 's/^name: *//p' "$f" | head -1)
  usage=$(sed -n 's/^usage: *//p' "$f" | head -1 | sed 's/^"//; s/"$//')
  if [ -z "$usage" ]; then
    usage=$(sed -n 's/^description: *//p' "$f" | head -1 | sed 's/^Use when //; s/^Use at //; s/[.;].*$//' | cut -c1-90)
  fi
  case "$usage" in /*) out="$out  $usage\n";; *) out="$out  /$name: $usage\n";; esac
done
[ -n "$out" ] || exit 0
msg=$(printf 'Project commands:\n%b' "$out" | sed 's/"/\\"/g' | awk '{printf "%s\\n", $0}')
printf '{"systemMessage": "%s"}\n' "$msg"
