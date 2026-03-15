#!/bin/bash
# Deploy 3-agent monorepo to droplet via Tailscale
set -e

DROPLET="aicos-droplet"
REMOTE_DIR="/opt/agents"

echo "=== Deploying agents to $DROPLET:$REMOTE_DIR ==="

# 1. Rsync code (exclude runtime data)
echo "[1/6] Syncing code..."
rsync -avz --exclude='.env' --exclude='.venv' --exclude='__pycache__' \
  --exclude='data/' --exclude='logs/' --exclude='cookies/' --exclude='.git' \
  ./ root@${DROPLET}:${REMOTE_DIR}/

# 2. Install/update deps
echo "[2/6] Installing dependencies..."
ssh root@${DROPLET} "cd ${REMOTE_DIR} && /root/.local/bin/uv sync"

# 3. Sync CONTEXT.md from parent project
echo "[3/6] Syncing CONTEXT.md..."
CONTEXT_SRC="$(cd "$(dirname "$0")/../.." && pwd)/CONTEXT.md"
if [ -f "$CONTEXT_SRC" ]; then
  rsync -avz "$CONTEXT_SRC" root@${DROPLET}:${REMOTE_DIR}/CONTEXT.md
else
  echo "  WARNING: CONTEXT.md not found at $CONTEXT_SRC"
fi

# 4. Create runtime directories
echo "[4/6] Creating runtime directories..."
ssh root@${DROPLET} "mkdir -p ${REMOTE_DIR}/{data/queue/processed,data/sessions,logs,cookies}"

# 5. Restart services (sync first — it's the gateway)
echo "[5/6] Restarting services..."
ssh root@${DROPLET} '
  systemctl restart sync-agent
  echo "  Waiting for sync-agent..."
  for i in $(seq 1 30); do
    if curl -sf --max-time 2 http://localhost:8000/health > /dev/null 2>&1; then
      echo "  sync-agent: OK (ready after ${i}s)"
      break
    fi
    if [ "$i" -eq 30 ]; then
      echo "  sync-agent: FAILED after 30s — continuing anyway"
    fi
    sleep 1
  done

  systemctl restart content-agent
  systemctl restart web-agent
  sleep 3
'

# 6. Health check all 3
echo "[6/6] Health checks..."
for svc in "sync-agent:8000" "content-agent:8002" "web-agent:8001"; do
  name="${svc%%:*}"
  port="${svc##*:}"
  ssh root@${DROPLET} "curl -sf http://localhost:${port}/health > /dev/null" \
    && echo "  ${name} (port ${port}): OK" \
    || echo "  ${name} (port ${port}): FAILED"
done

echo ""
echo "=== Deploy complete ==="
