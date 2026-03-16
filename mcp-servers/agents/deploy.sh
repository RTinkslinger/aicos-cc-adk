#!/bin/bash
# Deploy v3 agents monorepo to droplet via Tailscale
# Active services: state-mcp, web-tools-mcp, orchestrator (manages content agent)
# Disabled: sync-agent, content-agent (now managed by orchestrator lifecycle.py)
set -e

DROPLET="aicos-droplet"
REMOTE_DIR="/opt/agents"
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

echo "=== Deploying v3 agents to $DROPLET:$REMOTE_DIR ==="

# 1. Rsync code (exclude runtime data, state, traces, sql)
echo "[1/9] Syncing code..."
rsync -avz --exclude='.env' --exclude='.venv' --exclude='__pycache__' \
  --exclude='data/' --exclude='logs/' --exclude='cookies/' --exclude='.git' \
  --exclude='sql/' --exclude='traces/' --exclude='*/state/' \
  ./ root@${DROPLET}:${REMOTE_DIR}/

# 2. Install/update deps
echo "[2/9] Installing dependencies..."
ssh root@${DROPLET} "cd ${REMOTE_DIR} && /root/.local/bin/uv sync"

# 3. Sync CONTEXT.md from parent project
echo "[3/9] Syncing CONTEXT.md..."
CONTEXT_SRC="${PROJECT_ROOT}/CONTEXT.md"
if [ -f "$CONTEXT_SRC" ]; then
  rsync -avz "$CONTEXT_SRC" root@${DROPLET}:${REMOTE_DIR}/CONTEXT.md
else
  echo "  WARNING: CONTEXT.md not found at $CONTEXT_SRC"
fi

# 4. Sync skills/ directory
echo "[4/9] Syncing skills/..."
rsync -avz --delete skills/ root@${DROPLET}:${REMOTE_DIR}/skills/

# 5. Sync .claude/agents/ subagent definitions
echo "[5/9] Syncing .claude/agents/..."
ssh root@${DROPLET} "mkdir -p ${REMOTE_DIR}/.claude/agents"
rsync -avz --delete .claude/agents/ root@${DROPLET}:${REMOTE_DIR}/.claude/agents/

# 6. Create runtime directories (survive deploys via rsync excludes)
echo "[6/9] Creating runtime directories..."
ssh root@${DROPLET} "mkdir -p ${REMOTE_DIR}/{data/queue/processed,data/sessions,logs,cookies} ${REMOTE_DIR}/traces/archive ${REMOTE_DIR}/orchestrator/state ${REMOTE_DIR}/content/state"

# 7. Install systemd units from infra/
echo "[7/9] Installing systemd units..."
ssh root@${DROPLET} "
  cp ${REMOTE_DIR}/infra/state-mcp.service /etc/systemd/system/
  cp ${REMOTE_DIR}/infra/web-tools-mcp.service /etc/systemd/system/
  cp ${REMOTE_DIR}/infra/orchestrator.service /etc/systemd/system/
  # content-agent: no longer a separate service — managed by orchestrator lifecycle.py
  # sync-agent: disabled
  systemctl daemon-reload
  systemctl disable content-agent 2>/dev/null || true
  systemctl stop content-agent 2>/dev/null || true
  systemctl enable state-mcp web-tools-mcp orchestrator
"

# 8. Restart services in dependency order
echo "[8/9] Restarting services..."
ssh root@${DROPLET} '
  # state-mcp first — everything depends on it
  systemctl restart state-mcp
  echo "  Waiting for state-mcp..."
  for i in $(seq 1 30); do
    if curl -sf --max-time 2 http://localhost:8000/health > /dev/null 2>&1; then
      echo "  state-mcp: OK (ready after ${i}s)"
      break
    fi
    if [ "$i" -eq 30 ]; then
      echo "  state-mcp: FAILED after 30s — continuing anyway"
    fi
    sleep 1
  done

  # web-tools-mcp next
  systemctl restart web-tools-mcp
  echo "  Waiting for web-tools-mcp..."
  for i in $(seq 1 30); do
    if curl -sf --max-time 2 http://localhost:8001/health > /dev/null 2>&1; then
      echo "  web-tools-mcp: OK (ready after ${i}s)"
      break
    fi
    if [ "$i" -eq 30 ]; then
      echo "  web-tools-mcp: FAILED after 30s — continuing anyway"
    fi
    sleep 1
  done

  # Orchestrator last — manages content agent internally
  systemctl restart orchestrator
  sleep 5
'

# 9. Health check
echo "[9/9] Health checks..."

# MCP servers — check via port
for svc in "state-mcp:8000" "web-tools-mcp:8001"; do
  name="${svc%%:*}"
  port="${svc##*:}"
  ssh root@${DROPLET} "curl -sf http://localhost:${port}/health > /dev/null" \
    && echo "  ${name} (port ${port}): OK" \
    || echo "  ${name} (port ${port}): FAILED"
done

# Orchestrator — check via systemctl (manages both orc + content agent)
for svc in orchestrator; do
  ssh root@${DROPLET} "systemctl is-active --quiet ${svc}" \
    && echo "  ${svc} (systemctl): OK" \
    || echo "  ${svc} (systemctl): FAILED"
done

echo ""
echo "=== Deploy complete ==="
