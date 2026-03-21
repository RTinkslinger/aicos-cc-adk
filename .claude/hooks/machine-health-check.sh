#!/bin/bash
# Hook: UserPromptSubmit — every time user sends a message, check machine health
# Detects stalled machines, reports status, enforces active monitoring

SESSION_DIR="$HOME/.claude/projects/-Users-Aakash-Claude-Projects-Aakash-AI-CoS-CC-ADK"
SUBAGENT_DIR=""

# Find the current session's subagent directory
for dir in "$SESSION_DIR"/*/subagents; do
  if [ -d "$dir" ]; then
    SUBAGENT_DIR="$dir"
  fi
done

if [ -z "$SUBAGENT_DIR" ] || [ ! -d "$SUBAGENT_DIR" ]; then
  exit 0
fi

# Check for running agents and detect stalls
NOW=$(date +%s)
STALLED=0
RUNNING=0
STALLED_LIST=""

for agent_file in "$SUBAGENT_DIR"/agent-*.jsonl; do
  [ -f "$agent_file" ] || continue

  # Get last timestamp
  LAST_TS=$(tail -1 "$agent_file" 2>/dev/null | python3 -c "
import sys, json
try:
    d = json.loads(sys.stdin.read())
    print(d.get('timestamp','')[:19])
except: pass
" 2>/dev/null)

  if [ -z "$LAST_TS" ]; then continue; fi

  # Convert to epoch
  AGENT_EPOCH=$(python3 -c "
from datetime import datetime
try:
    dt = datetime.fromisoformat('${LAST_TS}'.replace('Z','+00:00'))
    print(int(dt.timestamp()))
except: print(0)
" 2>/dev/null)

  if [ "$AGENT_EPOCH" = "0" ]; then continue; fi

  DIFF=$((NOW - AGENT_EPOCH))

  # If agent was active in last hour but stalled >20 minutes, it's stalled
  if [ $DIFF -gt 1200 ] && [ $DIFF -lt 7200 ]; then
    STALLED=$((STALLED + 1))
    AGENT_NAME=$(basename "$agent_file" .jsonl | sed 's/agent-//')
    MINS=$((DIFF / 60))
    STALLED_LIST="${STALLED_LIST}  ⚠️ Agent ${AGENT_NAME:0:12}... stalled ${MINS}m ago\n"
  elif [ $DIFF -lt 1200 ]; then
    RUNNING=$((RUNNING + 1))
  fi
done

if [ $STALLED -gt 0 ]; then
  echo "🚨 MACHINE STALL DETECTED: $STALLED machine(s) stalled, $RUNNING still active"
  echo ""
  echo -e "$STALLED_LIST"
  echo "ACTION: Check stalled machines and RELAUNCH them. Machines must not silently die."
  echo "Golden Pattern Section 1a-v: Orchestrator MUST actively monitor."
fi
