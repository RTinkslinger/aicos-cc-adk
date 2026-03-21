#!/bin/bash
# Hook: Before launching any Agent tool, check for unprocessed user feedback
# AND tell the orchestrator which machines need the feedback dispatched to
# Zero trust in orchestrator discipline — this hook enforces feedback flow

SUPABASE_URL="https://llfkxnsfczludgigknbs.supabase.co"
SUPABASE_KEY=""

# Try reading key from aicos-digests .env.local
ENV_FILE="$CLAUDE_PROJECT_DIR/aicos-digests/.env.local"
if [ -f "$ENV_FILE" ]; then
  SUPABASE_KEY=$(grep SUPABASE_SECRET_KEY "$ENV_FILE" 2>/dev/null | cut -d= -f2- | tr -d ' "')
fi

if [ -z "$SUPABASE_KEY" ]; then
  exit 0
fi

# Query unprocessed feedback with machine routing info
FEEDBACK=$(curl -s "${SUPABASE_URL}/rest/v1/user_feedback_store?select=id,page,feedback_text,rating,context&order=created_at.desc&limit=10" \
  -H "apikey: ${SUPABASE_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_KEY}" 2>/dev/null)

if [ -z "$FEEDBACK" ] || [ "$FEEDBACK" = "[]" ]; then
  exit 0
fi

# Parse unprocessed entries (where processed_by doesn't contain all target machines)
RESULT=$(python3 -c "
import sys, json
try:
    entries = json.loads('''$FEEDBACK''')
    unprocessed = []
    dispatch_map = {}  # machine -> [feedback entries]

    for e in entries:
        ctx = e.get('context', {}) or {}
        processed = ctx.get('processed_by', []) if isinstance(ctx, dict) else []
        # Also check top-level processed_by if context doesn't have it
        machines = []
        if isinstance(ctx, dict):
            ms = ctx.get('machine_sources', [])
            if isinstance(ms, str):
                import ast
                try: ms = ast.literal_eval(ms)
                except: ms = []
            machines = ms if isinstance(ms, list) else []

        # Check if any target machine hasn't processed this
        needs_dispatch = False
        for m in machines:
            if m not in processed:
                needs_dispatch = True
                if m not in dispatch_map:
                    dispatch_map[m] = []
                dispatch_map[m].append({'id': e['id'], 'text': (e.get('feedback_text','') or '')[:80], 'page': e.get('page','')})

        if needs_dispatch:
            unprocessed.append(e)

    if unprocessed:
        print(f'⚠️ UNPROCESSED USER FEEDBACK: {len(unprocessed)} entries waiting!')
        print()
        for e in unprocessed[:5]:
            txt = (e.get('feedback_text','') or '')[:100]
            page = e.get('page','')
            print(f'  #{e[\"id\"]} [{page}]: {txt}')
        print()
        print('DISPATCH REQUIRED — include feedback in these machine prompts:')
        for m, items in dispatch_map.items():
            ids = ', '.join([f'#{i[\"id\"]}' for i in items])
            print(f'  → {m}: {ids}')
        print()
        print('After dispatching, mark processed: SELECT mark_feedback_processed(ID, MACHINE)')
        print('DO NOT SKIP. DO NOT LAUNCH WITHOUT DISPATCHING.')
except Exception as ex:
    print(f'Feedback check error: {ex}')
" 2>/dev/null)

if [ -n "$RESULT" ]; then
  echo "$RESULT"
fi
