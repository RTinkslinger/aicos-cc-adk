#!/bin/bash
# UserPromptSubmit hook: check manifest for context limits.
# If agent's token count exceeds threshold, inject compaction instructions.
# Exit 0 = proceed normally. Exit 2 = continue with stderr as context.

set -euo pipefail
command -v jq >/dev/null 2>&1 || exit 0

INPUT=$(cat)
CWD=$(echo "$INPUT" | jq -r '.cwd // empty')
if [ -z "$CWD" ]; then
  exit 0
fi

AGENT="content"
THRESHOLD=100000
AGENTS_ROOT="$(dirname "$CWD")"
MANIFEST="${AGENTS_ROOT}/traces/manifest.json"

if [ ! -f "$MANIFEST" ]; then
  exit 0
fi

INPUT_TOKENS=$(jq -r ".${AGENT}.input_tokens // 0" "$MANIFEST" 2>/dev/null || echo "0")
OUTPUT_TOKENS=$(jq -r ".${AGENT}.output_tokens // 0" "$MANIFEST" 2>/dev/null || echo "0")
TOTAL=$((INPUT_TOKENS + OUTPUT_TOKENS))

if [ "$TOTAL" -gt "$THRESHOLD" ]; then
  cat >&2 <<EOF
COMPACTION REQUIRED: Session at ${TOTAL} tokens (threshold: ${THRESHOLD}).
Before doing anything else:
1. Write your full state to state/${AGENT}_checkpoint.md
   Include: current state, pending work, recent context (last 5 iterations), key facts.
2. End your response with the exact word: COMPACT_NOW
EOF
  exit 2
fi

exit 0
