#!/bin/bash
# Deploy to droplet with lock file to prevent concurrent deploys.
# Machines call this instead of deploy.sh directly.
set -euo pipefail

LOCK_FILE="/tmp/aicos-deploy.lock"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MAX_WAIT=120  # seconds to wait for existing deploy

# Check for existing lock
if [ -f "$LOCK_FILE" ]; then
  LOCK_PID=$(cat "$LOCK_FILE" 2>/dev/null)
  LOCK_AGE=$(( $(date +%s) - $(stat -f %m "$LOCK_FILE" 2>/dev/null || echo "0") ))

  # If lock is stale (>5 min), remove it
  if [ "$LOCK_AGE" -gt 300 ]; then
    echo "[deploy-lock] Stale lock (${LOCK_AGE}s old). Removing."
    rm -f "$LOCK_FILE"
  else
    echo "[deploy-lock] Deploy in progress (PID $LOCK_PID, ${LOCK_AGE}s ago). Waiting..."
    WAITED=0
    while [ -f "$LOCK_FILE" ] && [ "$WAITED" -lt "$MAX_WAIT" ]; do
      sleep 5
      WAITED=$((WAITED + 5))
    done
    if [ -f "$LOCK_FILE" ]; then
      echo "[deploy-lock] Timeout waiting for lock after ${MAX_WAIT}s. Proceeding anyway."
      rm -f "$LOCK_FILE"
    else
      echo "[deploy-lock] Previous deploy finished. Proceeding."
    fi
  fi
fi

# Acquire lock
echo $$ > "$LOCK_FILE"
trap 'rm -f "$LOCK_FILE"' EXIT

echo "[deploy-lock] Lock acquired (PID $$). Deploying..."

# Run the actual deploy
cd "$SCRIPT_DIR"
bash deploy.sh

# Record deploy timestamp
date -u "+%Y-%m-%dT%H:%M:%SZ" > "$SCRIPT_DIR/.last_deploy"

echo "[deploy-lock] Deploy complete. Lock released."
