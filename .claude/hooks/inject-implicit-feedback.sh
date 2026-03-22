#!/bin/bash
# Hook #2: PreToolUse on Agent — Inject implicit feedback (conversation logs) for agent machines
# Only fires for agent machines: M4, M7, M8, M-ENIAC

SUPABASE_URL="https://llfkxnsfczludgigknbs.supabase.co"
SUPABASE_KEY=""

for f in "$CLAUDE_PROJECT_DIR/.env.local" "$CLAUDE_PROJECT_DIR/aicos-digests/.env.local"; do
  if [ -f "$f" ]; then
    KEY=$(grep -E "SUPABASE_SECRET_KEY|SUPABASE_SERVICE_ROLE_KEY" "$f" 2>/dev/null | head -1 | cut -d= -f2- | tr -d ' "')
    [ -n "$KEY" ] && SUPABASE_KEY="$KEY" && break
  fi
done

[ -z "$SUPABASE_KEY" ] && exit 0

PROMPT=$(cat)

# Detect agent machine and map to agent name
AGENT=""
if echo "$PROMPT" | grep -qi "M4\|Datum"; then AGENT="datum"; fi
if echo "$PROMPT" | grep -qi "M8\|Cindy"; then AGENT="cindy"; fi
if echo "$PROMPT" | grep -qi "M7\|Megamind"; then AGENT="megamind"; fi
if echo "$PROMPT" | grep -qi "M-ENIAC\|ENIAC"; then AGENT="eniac"; fi

[ -z "$AGENT" ] && exit 0

# Query recent implicit feedback from conversation log
IMPLICIT=$(curl -s "${SUPABASE_URL}/rest/v1/rpc/cindy_conversation_log" \
  -X POST \
  -H "apikey: ${SUPABASE_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"p_mode": "recent", "p_limit": 5}' 2>/dev/null)

if [ -n "$IMPLICIT" ] && [ "$IMPLICIT" != "[]" ] && [ "$IMPLICIT" != "null" ]; then
  COUNT=$(echo "$IMPLICIT" | python3 -c "import sys,json; d=json.loads(sys.stdin.read()); print(len(d) if isinstance(d,list) else 0)" 2>/dev/null || echo "0")
  if [ "$COUNT" != "0" ]; then
    echo "🧠 IMPLICIT FEEDBACK (user agent interactions — RL signal for ${AGENT}):"
    python3 -c "
import sys, json
try:
    data = json.loads('''$IMPLICIT''')
    if isinstance(data, list):
        for d in data[:5]:
            etype = d.get('exchange_type','?')
            person = d.get('person_name','?')
            resp = str(d.get('user_response',''))[:80]
            print(f'  [{etype}] {person}: {resp}')
    elif isinstance(data, dict) and 'exchanges' in data:
        for d in data['exchanges'][:5]:
            etype = d.get('exchange_type','?')
            person = d.get('person_name','?')
            resp = str(d.get('user_response',''))[:80]
            print(f'  [{etype}] {person}: {resp}')
except: pass
" 2>/dev/null
    echo "Use these patterns to improve ${AGENT}'s reasoning and tools."
  fi
fi

exit 0
