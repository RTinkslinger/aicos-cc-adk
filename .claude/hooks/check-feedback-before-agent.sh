#!/bin/bash
# Hook: Before launching any Agent tool, check for unprocessed user feedback
# This ensures the orchestrator NEVER misses feedback when relaunching machines

# Only trigger on Agent tool
TOOL_NAME="${TOOL_INPUT_tool_name:-}"

# Query Supabase for unprocessed feedback
SUPABASE_URL="${NEXT_PUBLIC_SUPABASE_URL:-https://llfkxnsfczludgigknbs.supabase.co}"
SUPABASE_KEY="${SUPABASE_SECRET_KEY:-}"

if [ -z "$SUPABASE_KEY" ]; then
  # Try reading from aicos-digests .env.local
  ENV_FILE="$CLAUDE_PROJECT_DIR/aicos-digests/.env.local"
  if [ -f "$ENV_FILE" ]; then
    SUPABASE_KEY=$(grep SUPABASE_SECRET_KEY "$ENV_FILE" 2>/dev/null | cut -d= -f2-)
  fi
fi

if [ -n "$SUPABASE_KEY" ]; then
  FEEDBACK=$(curl -s "${SUPABASE_URL}/rest/v1/user_feedback_store?processed_by=not.cs.{}&select=id,page,feedback_text,rating&order=created_at.desc&limit=5" \
    -H "apikey: ${SUPABASE_KEY}" \
    -H "Authorization: Bearer ${SUPABASE_KEY}" 2>/dev/null)

  if [ -n "$FEEDBACK" ] && [ "$FEEDBACK" != "[]" ]; then
    COUNT=$(echo "$FEEDBACK" | python3 -c "import sys,json; print(len(json.loads(sys.stdin.read())))" 2>/dev/null || echo "0")
    if [ "$COUNT" != "0" ] && [ "$COUNT" != "" ]; then
      echo "⚠️ UNPROCESSED USER FEEDBACK: $COUNT entries waiting. Check user_feedback_store BEFORE launching this agent. Run: SELECT * FROM get_machine_feedback('M{N}') for the relevant machine. Include feedback in the agent prompt. DO NOT SKIP."
    fi
  fi
fi
