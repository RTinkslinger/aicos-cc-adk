#!/bin/bash
# PreCompact hook: emergency state dump before SDK auto-compaction.
# Safety net — primary path is agent-written checkpoints at 100K tokens.
# Exit 0 = allow compaction to proceed.

set -euo pipefail
command -v jq >/dev/null 2>&1 || exit 0

INPUT=$(cat)
CWD=$(echo "$INPUT" | jq -r '.cwd // empty')
if [ -z "$CWD" ]; then
  exit 0
fi

AGENT="content"
STATE_DIR="${CWD}/state"
AGENTS_ROOT="$(dirname "$CWD")"
ACTIVE_TRACES_PTR="${AGENTS_ROOT}/traces/active.txt"
CHECKPOINT="${STATE_DIR}/${AGENT}_checkpoint.md"
TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M UTC")

# Only write if no checkpoint already exists
if [ -f "$CHECKPOINT" ]; then
  exit 0
fi

RECENT_TRACES=""
if [ -f "$ACTIVE_TRACES_PTR" ]; then
  ACTIVE_TRACES="${AGENTS_ROOT}/$(cat "$ACTIVE_TRACES_PTR")"
  if [ -f "$ACTIVE_TRACES" ]; then
    RECENT_TRACES=$(tail -30 "$ACTIVE_TRACES" 2>/dev/null || echo "no traces available")
  fi
fi

cat > "$CHECKPOINT" <<EOF
# Emergency Checkpoint — SDK Auto-Compaction
*Written: ${TIMESTAMP} by PreCompact hook (NOT by agent)*

## Warning
This checkpoint was written by the PreCompact safety net, not by the agent.
Read recent traces and state files for fuller context.

## Recent Traces (last 30 lines)
\`\`\`
${RECENT_TRACES}
\`\`\`

## Recovery Instructions
1. Read CLAUDE.md for your task checklist
2. Read traces/ for recent history
3. Check state/ for any pending work
4. Resume normal heartbeat operation
EOF

exit 0
