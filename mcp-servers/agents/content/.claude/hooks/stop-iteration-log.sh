#!/bin/bash
# Stop hook: log iteration + pipeline timestamp management.
# Fires after every completed query (heartbeat or task).
# Reads agent's self-reported summary from state/{AGENT}_last_log.txt.
#
# Pipeline timestamp logic (two conditions, both required):
#   1. state/pipeline_requested.txt exists (set by UserPromptSubmit when prompt contains "pipeline cycle")
#   2. Agent's ACK summary contains "Pipeline" (proof the pipeline actually completed)
# If flag exists without ACK match, flag is cleaned up (stale from crash/compaction).
#
# Exit 0 = agent stops normally.

set -euo pipefail
command -v jq >/dev/null 2>&1 || exit 0

INPUT=$(cat)

STOP_ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active // false')
if [ "$STOP_ACTIVE" = "true" ]; then
  exit 0
fi

CWD=$(echo "$INPUT" | jq -r '.cwd // empty')
if [ -z "$CWD" ]; then
  exit 0
fi

AGENT="content"
STATE_DIR="${CWD}/state"
ITER_FILE="${STATE_DIR}/${AGENT}_iteration.txt"
SESS_FILE="${STATE_DIR}/${AGENT}_session.txt"
LOG_FILE="${STATE_DIR}/${AGENT}_last_log.txt"
PIPELINE_FLAG="${STATE_DIR}/pipeline_requested.txt"
PIPELINE_TS="${STATE_DIR}/last_pipeline_run.txt"

AGENTS_ROOT="$(dirname "$CWD")"
ACTIVE_TRACES_PTR="${AGENTS_ROOT}/traces/active.txt"
if [ ! -f "$ACTIVE_TRACES_PTR" ]; then
  exit 0
fi
ACTIVE_TRACES="${AGENTS_ROOT}/$(cat "$ACTIVE_TRACES_PTR")"

SESS=$(cat "$SESS_FILE" 2>/dev/null || echo "1")
ITER=$(cat "$ITER_FILE" 2>/dev/null || echo "0")
ITER=$((ITER + 1))
echo "$ITER" > "$ITER_FILE"

SUMMARY=""
if [ -f "$LOG_FILE" ]; then
  SUMMARY=$(head -1 "$LOG_FILE" | cut -c1-200)
  : > "$LOG_FILE"
fi
[ -z "$SUMMARY" ] && SUMMARY="did nothing"

TIMESTAMP=$(date -u +"%H:%M UTC")

echo "\$${AGENT} | sess #${SESS} | it ${ITER} | ${TIMESTAMP} :: '${SUMMARY}'" >> "$ACTIVE_TRACES"

# --- Pipeline timestamp: write only if flag exists AND ACK confirms pipeline ran ---
if [ -f "$PIPELINE_FLAG" ]; then
  if echo "$SUMMARY" | grep -qi "pipeline"; then
    # Both conditions met: pipeline was requested AND completed
    date -u +"%Y-%m-%dT%H:%M:%SZ" > "$PIPELINE_TS"
  fi
  # Always clean up flag (prevents stale flags from crash/compaction)
  rm -f "$PIPELINE_FLAG"
fi

exit 0
