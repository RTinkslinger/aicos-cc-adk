#!/bin/bash
# Hook #3: PostToolUse on Agent — Verify machine addressed its pending feedback
# Warns if machine completed without mentioning feedback items

SUPABASE_URL="https://llfkxnsfczludgigknbs.supabase.co"
SUPABASE_KEY=""

for f in "$CLAUDE_PROJECT_DIR/.env.local" "$CLAUDE_PROJECT_DIR/aicos-digests/.env.local"; do
  if [ -f "$f" ]; then
    KEY=$(grep -E "SUPABASE_SECRET_KEY|SUPABASE_SERVICE_ROLE_KEY" "$f" 2>/dev/null | head -1 | cut -d= -f2- | tr -d ' "')
    [ -n "$KEY" ] && SUPABASE_KEY="$KEY" && break
  fi
done

[ -z "$SUPABASE_KEY" ] && exit 0

# Check if any P0 feedback items are still pending across all machines
P0_COUNT=$(curl -s "${SUPABASE_URL}/rest/v1/feedback_decomposition?priority=eq.P0&status=eq.pending&select=id&limit=1" \
  -H "apikey: ${SUPABASE_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_KEY}" 2>/dev/null | python3 -c "import sys,json; print(len(json.loads(sys.stdin.read())))" 2>/dev/null || echo "0")

if [ "$P0_COUNT" != "0" ]; then
  echo "⚠️ P0 feedback items still pending in feedback_decomposition. Ensure machines are addressing them."
fi

exit 0
