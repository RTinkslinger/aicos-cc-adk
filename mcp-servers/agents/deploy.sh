#!/bin/bash
# Deploy v3 agents monorepo to droplet via Tailscale
# 3-phase idempotent deploy: SYNC → BOOTSTRAP → CLEANUP+RESTART
#
# Active services: state-mcp, web-tools-mcp, orchestrator
# Orchestrator manages content agent + datum agent internally via lifecycle.py
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

DROPLET="aicos-droplet"
REMOTE_DIR="/opt/agents"
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

echo "=== Deploying v3 agents to $DROPLET:$REMOTE_DIR ==="

# =====================================================================
# PHASE 1 — SYNC CODE
# =====================================================================

# 1a. Rsync code (excludes protect runtime data from being overwritten)
echo "[1/8] Syncing code..."
rsync -avz \
  --exclude='.env' --exclude='.venv' --exclude='__pycache__' \
  --exclude='*.pyc' --exclude='.git' \
  --exclude='*/state/' --exclude='traces/' \
  --exclude='data/' --exclude='logs/' --exclude='cookies/' \
  --exclude='sql/' --exclude='deploy/' \
  --exclude='live.log' --exclude='*.log' \
  ./ root@${DROPLET}:${REMOTE_DIR}/

# 1b. Sync deploy tools (view-logs.py, live-*.sh)
echo "[2/8] Syncing deploy tools..."
rsync -avz deploy/tools/ root@${DROPLET}:${REMOTE_DIR}/
ssh root@${DROPLET} "chmod +x ${REMOTE_DIR}/live-*.sh ${REMOTE_DIR}/view-logs.py"

# 1c. Install dependencies
echo "[3/8] Installing dependencies..."
ssh root@${DROPLET} "cd ${REMOTE_DIR} && /root/.local/bin/uv sync"

# 1d. Sync CONTEXT.md from parent project
echo "[4/8] Syncing CONTEXT.md..."
CONTEXT_SRC="${PROJECT_ROOT}/CONTEXT.md"
if [ -f "$CONTEXT_SRC" ]; then
  rsync -avz "$CONTEXT_SRC" root@${DROPLET}:${REMOTE_DIR}/CONTEXT.md
else
  echo "  WARNING: CONTEXT.md not found at $CONTEXT_SRC"
fi

# 1e. Sync skills and subagent definitions
echo "[5/8] Syncing skills + subagents..."
rsync -avz --delete skills/ root@${DROPLET}:${REMOTE_DIR}/skills/
ssh root@${DROPLET} "mkdir -p ${REMOTE_DIR}/.claude/agents"
rsync -avz --delete .claude/agents/ root@${DROPLET}:${REMOTE_DIR}/.claude/agents/

# =====================================================================
# PHASE 2 — BOOTSTRAP (idempotent, create-if-not-exists)
# =====================================================================

echo "[6/8] Bootstrap (seed runtime state if missing)..."
rsync -avz deploy/bootstrap.sh deploy/cleanup.sh root@${DROPLET}:${REMOTE_DIR}/deploy/
ssh root@${DROPLET} "bash ${REMOTE_DIR}/deploy/bootstrap.sh ${REMOTE_DIR}"

# =====================================================================
# PHASE 3 — CLEANUP + RESTART
# =====================================================================

echo "[7/8] Cleanup stale files + install services..."
ssh root@${DROPLET} "bash ${REMOTE_DIR}/deploy/cleanup.sh ${REMOTE_DIR}"

# Install systemd units
ssh root@${DROPLET} "
  cp ${REMOTE_DIR}/infra/state-mcp.service /etc/systemd/system/
  cp ${REMOTE_DIR}/infra/web-tools-mcp.service /etc/systemd/system/
  cp ${REMOTE_DIR}/infra/orchestrator.service /etc/systemd/system/
  systemctl daemon-reload
  systemctl enable state-mcp web-tools-mcp orchestrator
"

# Restart services in dependency order
echo "[8/8] Restarting services..."
ssh root@${DROPLET} '
  systemctl restart state-mcp
  echo "  Waiting for state-mcp..."
  for i in $(seq 1 30); do
    if curl -sf --max-time 2 http://localhost:8000/health > /dev/null 2>&1; then
      echo "  state-mcp: OK (ready after ${i}s)"
      break
    fi
    if [ "$i" -eq 30 ]; then
      echo "  state-mcp: FAILED after 30s"
      exit 1
    fi
    sleep 1
  done

  systemctl restart web-tools-mcp
  echo "  Waiting for web-tools-mcp..."
  for i in $(seq 1 30); do
    if curl -sf --max-time 2 http://localhost:8001/health > /dev/null 2>&1; then
      echo "  web-tools-mcp: OK (ready after ${i}s)"
      break
    fi
    if [ "$i" -eq 30 ]; then
      echo "  web-tools-mcp: FAILED after 30s"
      exit 1
    fi
    sleep 1
  done

  systemctl restart orchestrator
  sleep 5
'

# Health check
echo ""
echo "=== Health Checks ==="
for svc in "state-mcp:8000" "web-tools-mcp:8001"; do
  name="${svc%%:*}"
  port="${svc##*:}"
  ssh root@${DROPLET} "curl -sf http://localhost:${port}/health > /dev/null" \
    && echo "  ${name} (port ${port}): OK" \
    || echo "  ${name} (port ${port}): FAILED"
done

for svc in orchestrator; do
  ssh root@${DROPLET} "systemctl is-active --quiet ${svc}" \
    && echo "  ${svc} (systemctl): OK" \
    || echo "  ${svc} (systemctl): FAILED"
done

echo ""
echo "=== Deploy complete ==="
echo "  Live logs: ssh -t root@${DROPLET} /opt/agents/live-orc.sh"
echo "             ssh -t root@${DROPLET} /opt/agents/live-content.sh"
echo "             ssh -t root@${DROPLET} /opt/agents/live-datum.sh"
echo "             ssh -t root@${DROPLET} /opt/agents/live-traces.sh"
echo "             ssh -t root@${DROPLET} journalctl -u orchestrator -f"
