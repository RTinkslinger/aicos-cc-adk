#!/bin/bash
# Hook #5: UserPromptSubmit — Detect when user's CC message is feedback and auto-log
# Captures feedback given in CC chat (not just WebFront widget)

# Read the user's prompt from stdin
USER_MSG=$(cat)

# Check for feedback keywords
IS_FEEDBACK=$(echo "$USER_MSG" | python3 -c "
import sys
msg = sys.stdin.read().lower()
feedback_signals = [
    'wrong', 'broken', 'off', 'should be', 'why is', 'fix', 'improve',
    'not working', 'bug', 'ugly', 'bad', 'poor', 'garbage', 'dumb',
    'missing', 'incorrect', 'issue', 'problem', 'doesn\'t work',
    'needs work', 'half baked', 'can\'t see', 'not showing',
    'feedback:', 'fb:', 'ux issue', 'ui issue'
]
# Need at least one strong signal
matches = [s for s in feedback_signals if s in msg]
if len(matches) >= 1 and len(msg) > 20:
    print('YES')
else:
    print('NO')
" 2>/dev/null)

if [ "$IS_FEEDBACK" = "YES" ]; then
  SNIPPET=$(echo "$USER_MSG" | head -c 200)
  echo "📝 FEEDBACK DETECTED in CC chat. Capture this in docs/feedback-timeline-*.md and route to relevant machines."
  echo "   Snippet: ${SNIPPET}..."
fi

exit 0
