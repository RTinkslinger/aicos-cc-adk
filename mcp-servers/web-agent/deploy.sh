#!/bin/bash
set -e
DROPLET="aicos-droplet"
REMOTE_DIR="/opt/web-agent"

echo "Deploying web-agent to $DROPLET:$REMOTE_DIR..."

rsync -avz --delete --exclude='.env' --exclude='__pycache__' --exclude='.venv' \
  --exclude='tests' --exclude='strategy.db' --exclude='test_*.py' \
  ./ root@${DROPLET}:${REMOTE_DIR}/

ssh root@${DROPLET} "cd ${REMOTE_DIR} && /root/.local/bin/uv sync"

# Syntax check before restart
ssh root@${DROPLET} "cd ${REMOTE_DIR} && .venv/bin/python -c 'import server; import lib.browser; import lib.scrape; import lib.search; import lib.cookies; import lib.stealth' 2>&1" || {
  echo "ERROR: Syntax check failed — aborting deploy"
  exit 1
}

ssh root@${DROPLET} "systemctl restart web-agent"

# Post-deploy: health check (wait up to 30s for server to come up)
echo "Waiting for server to start..."
for i in $(seq 1 15); do
  if ssh root@${DROPLET} "curl -sf -m 5 -o /dev/null http://localhost:8001/mcp -X POST -H 'Content-Type: application/json' -d '{}'"; then
    echo "Health check passed after $((i*2)) seconds."
    break
  fi
  if [ $i -eq 15 ]; then
    echo "ERROR: Server did not respond within 30s"
    exit 1
  fi
  sleep 2
done

ssh root@${DROPLET} "systemctl status web-agent --no-pager | head -10"
