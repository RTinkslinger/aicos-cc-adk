#!/bin/bash
# Hook #6: PreToolUse on Agent — For M1 WebFront, verify previous deploy is live
# Prevents building on top of a failed deploy

PROMPT=$(cat)

# Only fire for M1 WebFront
if ! echo "$PROMPT" | grep -qi "M1\|WebFront"; then
  exit 0
fi

# Check latest commit in aicos-digests matches what's on remote
cd "$CLAUDE_PROJECT_DIR/aicos-digests" 2>/dev/null || exit 0

LOCAL_HEAD=$(git rev-parse HEAD 2>/dev/null)
REMOTE_HEAD=$(git ls-remote origin main 2>/dev/null | cut -f1)

if [ -n "$LOCAL_HEAD" ] && [ -n "$REMOTE_HEAD" ] && [ "$LOCAL_HEAD" != "$REMOTE_HEAD" ]; then
  echo "⚠️ M1 DEPLOY GAP: Local HEAD ($LOCAL_HEAD) != remote ($REMOTE_HEAD). Push before building more."
fi

# Check for uncommitted changes
DIRTY=$(git status --porcelain 2>/dev/null | head -5)
if [ -n "$DIRTY" ]; then
  echo "⚠️ M1 has uncommitted changes in aicos-digests/. Commit + push before launching new loop."
fi

exit 0
