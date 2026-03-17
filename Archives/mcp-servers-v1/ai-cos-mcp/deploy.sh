#!/bin/bash
# Deploy ai-cos-mcp to the DO droplet via Tailscale
set -e

DROPLET="aicos-droplet"
REMOTE_DIR="/opt/ai-cos-mcp"
DIGESTS_REPO="/opt/aicos-digests"

echo "Deploying to $DROPLET:$REMOTE_DIR..."

# Sync files (exclude .env, __pycache__, .venv)
rsync -avz --exclude='.env' --exclude='__pycache__' --exclude='.venv' \
  ./ root@${DROPLET}:${REMOTE_DIR}/

# Create queue and log directories
ssh root@${DROPLET} "mkdir -p ${REMOTE_DIR}/queue/processed ${REMOTE_DIR}/logs"

# Install deps and restart MCP server
ssh root@${DROPLET} "cd ${REMOTE_DIR} && /root/.local/bin/uv sync && systemctl restart ai-cos-mcp"

# Sync CONTEXT.md to droplet (for context loading)
CONTEXT_SRC="$(dirname "$(dirname "$(pwd)")")/CONTEXT.md"
if [ -f "$CONTEXT_SRC" ]; then
  echo "Syncing CONTEXT.md..."
  rsync -avz "$CONTEXT_SRC" root@${DROPLET}:${REMOTE_DIR}/CONTEXT.md
fi

# Sync aicos-digests repo on droplet (pull latest from remote)
echo "Syncing aicos-digests repo..."
ssh root@${DROPLET} "
  if [ ! -d ${DIGESTS_REPO}/.git ]; then
    echo 'Cloning aicos-digests...'
    git clone https://github.com/RTinkslinger/aicos-digests.git ${DIGESTS_REPO} || {
      echo 'WARNING: Could not clone aicos-digests.'
    }
  else
    echo 'Pulling latest aicos-digests...'
    cd ${DIGESTS_REPO} && git pull --ff-only origin main || echo '(pull failed — check for local changes)'
  fi
"

# Make cron wrapper executable
ssh root@${DROPLET} "chmod +x ${REMOTE_DIR}/cron/pipeline.sh"

# Clean up stale lockfile if it exists
ssh root@${DROPLET} "rm -f /tmp/aicos-pipeline.lock /tmp/aicos-pipeline-cron.lock"

# Install cron job — unified pipeline every 5 minutes
echo "Installing cron job (pipeline every 5 min)..."
ssh root@${DROPLET} "
  # Remove old ai-cos-mcp cron entries
  crontab -l 2>/dev/null | grep -v 'ai-cos-mcp' | crontab - 2>/dev/null || true

  # Add 5-minute pipeline cron
  (crontab -l 2>/dev/null; echo '# ai-cos-mcp: unified content pipeline every 5 min') | crontab -
  (crontab -l 2>/dev/null; echo '*/5 * * * * ${REMOTE_DIR}/cron/pipeline.sh >> ${REMOTE_DIR}/logs/pipeline.log 2>&1 # ai-cos-mcp') | crontab -

  # Add 10-minute SyncAgent cron
  (crontab -l 2>/dev/null; echo '# ai-cos-mcp: SyncAgent every 10 min') | crontab -
  (crontab -l 2>/dev/null; echo '*/10 * * * * cd ${REMOTE_DIR} && /root/.local/bin/uv run python -m runners.sync_agent full >> ${REMOTE_DIR}/logs/sync_agent.log 2>&1 # ai-cos-mcp') | crontab -

  echo 'Cron jobs installed:'
  crontab -l | grep ai-cos-mcp
"

echo ""
echo "Deployed. Checking status..."
ssh root@${DROPLET} "systemctl status ai-cos-mcp --no-pager | head -10"
echo ""
echo "Pipeline will run every 5 minutes. Manual trigger: ./scripts/yt"
