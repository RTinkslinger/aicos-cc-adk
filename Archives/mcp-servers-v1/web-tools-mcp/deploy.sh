#!/bin/bash
# Deploy web-tools-mcp to the DO droplet
set -e

DROPLET="aicos-droplet"
REMOTE_DIR="/opt/web-tools-mcp"

echo "Deploying web-tools-mcp to $DROPLET:$REMOTE_DIR..."

rsync -avz --exclude='.env' --exclude='__pycache__' --exclude='.venv' --exclude='tests' \
  ./ root@${DROPLET}:${REMOTE_DIR}/

ssh root@${DROPLET} "cd ${REMOTE_DIR} && /root/.local/bin/uv sync && systemctl restart web-tools-mcp"

echo ""
echo "Deployed. Checking status..."
ssh root@${DROPLET} "systemctl status web-tools-mcp --no-pager | head -10"
