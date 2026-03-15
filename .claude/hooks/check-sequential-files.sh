#!/bin/bash
# Check if a file being edited is classified as Sequential.
# Outputs JSON with additionalContext so Claude actually sees the warning.
# Never blocks (always exit 0). Only fires for subagents (uses agent_id field).
# TRACES.md, LEARNINGS.md, ROADMAP.md are always exempt — they must never be blocked
# because the Stop hook requires updating them.

# jq is required for parsing hook input JSON
command -v jq >/dev/null 2>&1 || exit 0

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.filePath // empty')
AGENT_ID=$(echo "$INPUT" | jq -r '.agent_id // empty')
CWD=$(echo "$INPUT" | jq -r '.cwd // empty')

# Only relevant for subagents — main session can edit anything
# agent_id is only present when hook fires inside a subagent
if [ -z "$AGENT_ID" ]; then
  exit 0
fi

# Build system files are always exempt (Stop hook requires updating these)
BASENAME=$(basename "$FILE_PATH" 2>/dev/null)
case "$BASENAME" in
  TRACES.md|LEARNINGS.md|ROADMAP.md) exit 0 ;;
esac

# Check sequential files list using cwd from JSON
SEQ_FILE="$CWD/.claude/sequential-files.txt"
if [ ! -f "$SEQ_FILE" ]; then
  exit 0  # No list = no restriction
fi

# Match against the list (exact whole-line match on basename to avoid false positives)
if [ -n "$BASENAME" ] && grep -qxF "$BASENAME" "$SEQ_FILE" 2>/dev/null; then
  # Use jq to safely build JSON (prevents injection from filenames with special chars)
  jq -n --arg bn "$BASENAME" '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "allow",
      permissionDecisionReason: ("Allowed, but warning: " + $bn + " is a Sequential file. Ensure no other agent is editing it simultaneously."),
      additionalContext: ("Warning: " + $bn + " is listed in .claude/sequential-files.txt as a Sequential file. If other agents are running in parallel, coordinate to avoid merge conflicts.")
    }
  }'
  exit 0
fi

exit 0
