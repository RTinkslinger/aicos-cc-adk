#!/bin/bash
# Hook: SessionStart — enforce golden pattern requirements on every session
# Fires on startup/resume/clear/compact

echo "═══════════════════════════════════════════════════════════"
echo "GOLDEN PATTERN v2 ENFORCEMENT"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Check 1: GOLDEN-SESSION-PATTERN.md exists
if [ -f "$CLAUDE_PROJECT_DIR/docs/source-of-truth/GOLDEN-SESSION-PATTERN.md" ]; then
  echo "✅ GOLDEN-SESSION-PATTERN.md exists"
else
  echo "❌ GOLDEN-SESSION-PATTERN.md MISSING — cannot proceed without golden pattern"
fi

# Check 2: CHECKPOINT.md exists
if [ -f "$CLAUDE_PROJECT_DIR/CHECKPOINT.md" ]; then
  echo "✅ CHECKPOINT.md exists — read it for machine states"
else
  echo "⚠️ No CHECKPOINT.md — starting fresh"
fi

# Check 3: Feedback timeline for today
TODAY=$(date +%Y-%m-%d)
if [ -f "$CLAUDE_PROJECT_DIR/docs/feedback-timeline-${TODAY}.md" ]; then
  echo "✅ Feedback timeline exists for today"
else
  echo "❌ CREATE docs/feedback-timeline-${TODAY}.md NOW — mandatory for machine loops"
fi

echo ""
echo "MANDATORY BEFORE ANY WORK:"
echo "1. Read GOLDEN-SESSION-PATTERN.md — THE ENTIRE FILE"
echo "2. Read CHECKPOINT.md for machine states"
echo "3. Create feedback timeline if missing"
echo "4. Launch ALL permanent machines as perpetual loops"
echo "5. Agents do ALL thinking. SQL/Python = plumbing."
echo "6. Machine loop BUILDS agents (CLAUDE.md + skills + tools), doesn't DO agent work"
echo "7. Agent CLAUDE.md = OBJECTIVES not scripts"
echo "8. NEVER neglect Datum (M4)"
echo "9. Deploy M1 after EVERY loop"
echo "10. Check get_machine_feedback() at EVERY machine relaunch"
echo "═══════════════════════════════════════════════════════════"
