#!/bin/bash
# Hook #1: PreToolUse on Agent — Inject M-FEEDBACK decomposed tasks + raw feedback for the machine being launched
# Reads the agent prompt to detect which machine, then queries feedback_decomposition for pending tasks

SUPABASE_URL="https://llfkxnsfczludgigknbs.supabase.co"
SUPABASE_KEY=""

# Read key from .env.local
for f in "$CLAUDE_PROJECT_DIR/.env.local" "$CLAUDE_PROJECT_DIR/aicos-digests/.env.local"; do
  if [ -f "$f" ]; then
    KEY=$(grep -E "SUPABASE_SECRET_KEY|SUPABASE_SERVICE_ROLE_KEY" "$f" 2>/dev/null | head -1 | cut -d= -f2- | tr -d ' "')
    [ -n "$KEY" ] && SUPABASE_KEY="$KEY" && break
  fi
done

[ -z "$SUPABASE_KEY" ] && exit 0

# Detect machine from agent prompt (stdin has the tool input JSON)
PROMPT=$(cat)
MACHINE=""

# Match machine names in the prompt
for m in "M1" "M4" "M5" "M6" "M7" "M8" "M9" "M10" "M12" "M-ENIAC" "M-FEEDBACK"; do
  if echo "$PROMPT" | grep -qi "Machine ${m}\b\|You are ${m}\|${m}[- ]"; then
    MACHINE="$m"
    break
  fi
done

[ -z "$MACHINE" ] && exit 0

# Query decomposed feedback tasks for this machine
TASKS=$(curl -s "${SUPABASE_URL}/rest/v1/feedback_decomposition?target_machine=eq.${MACHINE}&status=eq.pending&select=id,feedback_id,component,analysis,priority&order=priority.asc,created_at.asc&limit=10" \
  -H "apikey: ${SUPABASE_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_KEY}" 2>/dev/null)

# Query raw unprocessed feedback targeted at this machine
RAW=$(curl -s "${SUPABASE_URL}/rest/v1/user_feedback_store?select=id,page,feedback_text,feedback_type,rating&order=created_at.desc&limit=5" \
  -H "apikey: ${SUPABASE_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_KEY}" 2>/dev/null)

OUTPUT=""

if [ -n "$TASKS" ] && [ "$TASKS" != "[]" ]; then
  COUNT=$(echo "$TASKS" | python3 -c "import sys,json; print(len(json.loads(sys.stdin.read())))" 2>/dev/null || echo "0")
  if [ "$COUNT" != "0" ]; then
    OUTPUT="📋 M-FEEDBACK ROUTED TASKS FOR ${MACHINE}: ${COUNT} pending\n"
    OUTPUT+=$(python3 -c "
import sys, json
tasks = json.loads('''$TASKS''')
for t in tasks:
    print(f'  [{t[\"priority\"]}] #{t[\"id\"]} ({t[\"component\"]}): {(t.get(\"analysis\",\"\") or \"\")[:120]}')
" 2>/dev/null)
    OUTPUT+="\nAddress these tasks in this loop. Mark addressed when done."
  fi
fi

if [ -n "$RAW" ] && [ "$RAW" != "[]" ]; then
  RAW_COUNT=$(echo "$RAW" | python3 -c "import sys,json; print(len([e for e in json.loads(sys.stdin.read()) if e.get('feedback_text')]))" 2>/dev/null || echo "0")
  if [ "$RAW_COUNT" != "0" ]; then
    OUTPUT+="\n\n📢 LATEST USER FEEDBACK (check if relevant to ${MACHINE}):\n"
    OUTPUT+=$(python3 -c "
import sys, json
entries = json.loads('''$RAW''')
for e in entries[:5]:
    txt = (e.get('feedback_text','') or '')[:100]
    if txt:
        print(f'  FB-{e[\"id\"]} [{e.get(\"page\",\"\")}] {e.get(\"feedback_type\",\"\")}: {txt}')
" 2>/dev/null)
  fi
fi

[ -n "$OUTPUT" ] && echo -e "$OUTPUT"
exit 0
