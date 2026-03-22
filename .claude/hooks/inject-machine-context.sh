#!/bin/bash
# Hook: PreToolUse on Agent — Inject machine context file + backlog + product vision
# ENFORCES that every machine loop starts with accumulated wisdom, task board, and vision

SUPABASE_URL="https://llfkxnsfczludgigknbs.supabase.co"
SUPABASE_KEY=""

for f in "$CLAUDE_PROJECT_DIR/.env.local" "$CLAUDE_PROJECT_DIR/aicos-digests/.env.local"; do
  if [ -f "$f" ]; then
    KEY=$(grep -E "SUPABASE_SECRET_KEY|SUPABASE_SERVICE_ROLE_KEY" "$f" 2>/dev/null | head -1 | cut -d= -f2- | tr -d ' "')
    [ -n "$KEY" ] && SUPABASE_KEY="$KEY" && break
  fi
done

PROMPT=$(cat)

# Detect machine
MACHINE=""
for m in "M1" "M4" "M5" "M6" "M7" "M8" "M9" "M10" "M12" "M-ENIAC" "M-FEEDBACK"; do
  if echo "$PROMPT" | grep -qi "Machine ${m}\b\|You are ${m}\|${m}[- ]"; then
    MACHINE="$m"
    break
  fi
done

[ -z "$MACHINE" ] && exit 0

OUTPUT=""

# 1. Inject machine context file (accumulated wisdom)
CONTEXT_FILE="$CLAUDE_PROJECT_DIR/docs/machine-context/${MACHINE}.md"
if [ -f "$CONTEXT_FILE" ] && [ -s "$CONTEXT_FILE" ]; then
  CONTEXT_SIZE=$(wc -c < "$CONTEXT_FILE")
  if [ "$CONTEXT_SIZE" -gt 50 ]; then
    # Read last 3000 chars (most recent context)
    CONTEXT_TAIL=$(tail -c 3000 "$CONTEXT_FILE")
    OUTPUT+="📖 MACHINE CONTEXT (accumulated wisdom from prior loops):\n"
    OUTPUT+="$CONTEXT_TAIL\n\n"
    OUTPUT+="→ UPDATE this file at END of your loop with decisions made and patterns learned.\n"
    OUTPUT+="→ File: docs/machine-context/${MACHINE}.md\n\n"
  fi
else
  OUTPUT+="⚠️ No machine context file found at docs/machine-context/${MACHINE}.md\n"
  OUTPUT+="→ CREATE this file at END of your loop with: decisions, patterns of success, anti-patterns, cross-machine context.\n\n"
fi

# 2. Inject machine backlog (task board)
if [ -n "$SUPABASE_KEY" ]; then
  BACKLOG=$(curl -s "${SUPABASE_URL}/rest/v1/machine_backlog?target_machine=eq.${MACHINE}&status=eq.pending&select=id,title,component,analysis,priority,source&order=priority.asc,created_at.asc&limit=15" \
    -H "apikey: ${SUPABASE_KEY}" \
    -H "Authorization: Bearer ${SUPABASE_KEY}" 2>/dev/null)

  if [ -n "$BACKLOG" ] && [ "$BACKLOG" != "[]" ]; then
    COUNT=$(echo "$BACKLOG" | python3 -c "import sys,json; print(len(json.loads(sys.stdin.read())))" 2>/dev/null || echo "0")
    if [ "$COUNT" != "0" ]; then
      OUTPUT+="📋 MACHINE BACKLOG (${COUNT} pending tasks for ${MACHINE}):\n"
      OUTPUT+=$(python3 -c "
import sys, json
tasks = json.loads('''$BACKLOG''')
for t in tasks:
    title = t.get('title') or t.get('analysis','')[:80] or 'untitled'
    src = t.get('source','feedback')
    print(f'  [{t[\"priority\"]}] #{t[\"id\"]} ({src}/{t.get(\"component\",\"?\")}): {title}')
" 2>/dev/null)
      OUTPUT+="\n→ Address P0 items first. Mark as 'addressed' in machine_backlog when done.\n"
      OUTPUT+="\n"
    fi
  fi

  # 3. Inject latest user feedback (explicit + implicit)
  RAW=$(curl -s "${SUPABASE_URL}/rest/v1/user_feedback_store?select=id,page,feedback_text,feedback_type,rating&order=created_at.desc&limit=5" \
    -H "apikey: ${SUPABASE_KEY}" \
    -H "Authorization: Bearer ${SUPABASE_KEY}" 2>/dev/null)

  if [ -n "$RAW" ] && [ "$RAW" != "[]" ]; then
    OUTPUT+="📢 LATEST FEEDBACK (check relevance to ${MACHINE}):\n"
    OUTPUT+=$(python3 -c "
import sys, json
entries = json.loads('''$RAW''')
for e in entries[:5]:
    txt = (e.get('feedback_text','') or '')[:100]
    if txt:
        ftype = e.get('feedback_type','')
        implicit = '🔄' if ftype in ('cindy_decision','cindy_dismissal','task_response','agent_interaction') else '📝'
        print(f'  {implicit} FB-{e[\"id\"]} [{e.get(\"page\",\"\")}] {ftype}: {txt}')
" 2>/dev/null)
    OUTPUT+="\n"
  fi
fi

# 4. Inject product vision reminder
OUTPUT+="\n🎯 PRODUCT VISION: Read docs/source-of-truth/VISION-AND-DIRECTION.md for the big picture."
OUTPUT+=" This machine builds ONE component of Aakash's 'What's Next?' action optimizer."
OUTPUT+=" Product leadership agent: keep the end-user experience in mind, not just technical metrics.\n"

# 5. For M1 WebFront: inject mobile-first design skill
if [ "$MACHINE" = "M1" ]; then
  DESIGN_SKILL="$CLAUDE_PROJECT_DIR/mcp-servers/agents/skills/webfront/mobile-first-card-ux.md"
  if [ -f "$DESIGN_SKILL" ]; then
    OUTPUT+="\n📱 MOBILE-FIRST DESIGN SKILL (MANDATORY for M1):\n"
    OUTPUT+="Read $DESIGN_SKILL BEFORE writing any UI code. Key rules:\n"
    OUTPUT+="  • Min card height 80px, touch targets 48px, padding 16px, gap 12px\n"
    OUTPUT+="  • 3-5 data points per card MAX. One CTA per card.\n"
    OUTPUT+="  • Font: body 15px, secondary 14px. Never 12px for data.\n"
    OUTPUT+="  • Test at 375px viewport. No grid-cols-N without responsive prefix.\n"
    OUTPUT+="  • No tables on mobile. No nested scroll. No multiple CTAs per card.\n"
    OUTPUT+="  • Full skill file: mcp-servers/agents/skills/webfront/mobile-first-card-ux.md\n"
  fi
fi

# 6. Remind to write back
OUTPUT+="\n📝 END OF LOOP: Update docs/machine-context/${MACHINE}.md with decisions, learnings, and cross-machine context."
OUTPUT+=" Update machine_backlog status for addressed items.\n"

echo -e "$OUTPUT"
exit 0
