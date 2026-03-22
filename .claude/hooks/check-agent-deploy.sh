#!/bin/bash
# Hook #7: Stop — Check if agent CLAUDE.md or skill files were modified but not deployed to droplet
# Prevents the "2 sessions of undeployed agent files" gap

cd "$CLAUDE_PROJECT_DIR" 2>/dev/null || exit 0

# Check if any agent files were modified (staged or unstaged)
AGENT_CHANGES=$(git diff --name-only HEAD 2>/dev/null | grep -E "mcp-servers/agents/.*(CLAUDE|skill)" | head -5)
AGENT_STAGED=$(git diff --cached --name-only 2>/dev/null | grep -E "mcp-servers/agents/.*(CLAUDE|skill)" | head -5)

CHANGES="${AGENT_CHANGES}${AGENT_STAGED}"

if [ -n "$CHANGES" ]; then
  # Check when deploy.sh was last run by looking at the deploy log
  DEPLOY_LOG="$CLAUDE_PROJECT_DIR/mcp-servers/agents/.last_deploy"
  LAST_DEPLOY=""
  if [ -f "$DEPLOY_LOG" ]; then
    LAST_DEPLOY=$(cat "$DEPLOY_LOG" 2>/dev/null)
  fi

  echo "⚠️ AGENT FILES MODIFIED but may not be deployed to droplet:"
  echo "$CHANGES" | while read -r f; do echo "  → $f"; done
  echo ""
  if [ -n "$LAST_DEPLOY" ]; then
    echo "Last deploy.sh run: $LAST_DEPLOY"
  else
    echo "No deploy.sh run recorded this session."
  fi
  echo "Run: cd mcp-servers/agents && bash deploy.sh"
  echo "This syncs agent CLAUDE.md + skills to the droplet where persistent agents run."
fi

exit 0
