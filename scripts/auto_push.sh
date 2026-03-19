#!/bin/bash
# auto_push.sh — Watches aicos-digests for unpushed commits, pushes to GitHub
# Designed to run via macOS launchd every 2 minutes.
# When Cowork pipeline commits digest JSONs locally, this picks them up and pushes.
#
# Install:
#   cp scripts/com.aicos.autopush.plist ~/Library/LaunchAgents/
#   launchctl load ~/Library/LaunchAgents/com.aicos.autopush.plist
#
# Uninstall:
#   launchctl unload ~/Library/LaunchAgents/com.aicos.autopush.plist

REPO="$HOME/Claude Projects/Aakash AI CoS CC ADK/aicos-digests"
LOG="$HOME/Claude Projects/Aakash AI CoS CC ADK/logs/auto_push.log"

mkdir -p "$(dirname "$LOG")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG"
}

# Bail if repo doesn't exist
if [ ! -d "$REPO/.git" ]; then
    log "ERROR: Repo not found at $REPO"
    exit 1
fi

cd "$REPO" || exit 1

# Fetch to know what origin/main looks like
git fetch origin main --quiet 2>/dev/null

# Check for unpushed commits on main
UNPUSHED=$(git log origin/main..HEAD --oneline 2>/dev/null)

if [ -z "$UNPUSHED" ]; then
    # Nothing to push — silent exit (don't spam log)
    exit 0
fi

# We have unpushed commits — push them
COMMIT_COUNT=$(echo "$UNPUSHED" | wc -l | tr -d ' ')
log "Found $COMMIT_COUNT unpushed commit(s):"
echo "$UNPUSHED" | while read -r line; do
    log "  $line"
done

git push origin main 2>&1 | while read -r line; do
    log "  git push: $line"
done

if [ ${PIPESTATUS[0]} -eq 0 ]; then
    log "SUCCESS: Pushed $COMMIT_COUNT commit(s) → GitHub Action will auto-deploy to Vercel"
else
    log "FAILED: git push returned non-zero. Will retry next cycle."
fi
