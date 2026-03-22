#!/bin/bash
# Hook #4: SessionStart — Check for unprocessed WebFront feedback since last session
# Prompts orchestrator to run M-FEEDBACK before launching machines

SUPABASE_URL="https://llfkxnsfczludgigknbs.supabase.co"
SUPABASE_KEY=""

for f in "$CLAUDE_PROJECT_DIR/.env.local" "$CLAUDE_PROJECT_DIR/aicos-digests/.env.local"; do
  if [ -f "$f" ]; then
    KEY=$(grep -E "SUPABASE_SECRET_KEY|SUPABASE_SERVICE_ROLE_KEY" "$f" 2>/dev/null | head -1 | cut -d= -f2- | tr -d ' "')
    [ -n "$KEY" ] && SUPABASE_KEY="$KEY" && break
  fi
done

[ -z "$SUPABASE_KEY" ] && exit 0

# Count unprocessed feedback (where processed_by is empty array or null)
UNPROCESSED=$(curl -s "${SUPABASE_URL}/rest/v1/user_feedback_store?select=id,page,feedback_text,feedback_type&order=created_at.desc&limit=20" \
  -H "apikey: ${SUPABASE_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_KEY}" 2>/dev/null)

if [ -z "$UNPROCESSED" ] || [ "$UNPROCESSED" = "[]" ]; then
  exit 0
fi

# Count items not yet decomposed
NOT_DECOMPOSED=$(python3 -c "
import sys, json, urllib.request
url = '${SUPABASE_URL}/rest/v1/feedback_decomposition?select=feedback_id'
headers = {'apikey': '${SUPABASE_KEY}', 'Authorization': 'Bearer ${SUPABASE_KEY}'}
req = urllib.request.Request(url, headers=headers)
try:
    resp = urllib.request.urlopen(req)
    decomposed_ids = set(d['feedback_id'] for d in json.loads(resp.read()))
except:
    decomposed_ids = set()

entries = json.loads('''$UNPROCESSED''')
not_decomposed = [e for e in entries if e['id'] not in decomposed_ids and e.get('feedback_text')]
if not_decomposed:
    print(f'📬 {len(not_decomposed)} WEBFRONT FEEDBACK ITEMS NOT YET ANALYZED BY M-FEEDBACK:')
    for e in not_decomposed[:8]:
        txt = (e.get('feedback_text','') or '')[:100]
        print(f'  FB-{e[\"id\"]} [{e.get(\"page\",\"\")}] {e.get(\"feedback_type\",\"\")}: {txt}')
    print()
    print('→ Run M-FEEDBACK machine FIRST to decompose these into component tasks before launching other machines.')
    print('→ M-FEEDBACK analyzes feedback with product org specialists and routes to relevant machines.')
" 2>/dev/null)

[ -n "$NOT_DECOMPOSED" ] && echo "$NOT_DECOMPOSED"
exit 0
