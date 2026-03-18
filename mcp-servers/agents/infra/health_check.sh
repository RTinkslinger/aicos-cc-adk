#!/bin/bash
# v2.2 Health check for 2 MCP servers + 2 agents
# Installed as cron: * * * * * /opt/agents/infra/health_check.sh >> /opt/agents/logs/health.log 2>&1

LOCKFILE="/tmp/agents-health-check.lock"
RESTART_COOLDOWN_FILE="/tmp/agents-last-restart"
COOLDOWN_SECONDS=300  # Don't restart same service twice in 5 min

# Prevent concurrent runs
exec 200>"$LOCKFILE"
flock -n 200 || exit 0

check_port_service() {
  local service=$1
  local port=$2

  if curl -sf --max-time 10 "http://localhost:${port}/health" > /dev/null 2>&1; then
    return 0
  fi

  restart_with_cooldown "$service" "health check failed on port ${port}"
}

check_systemd_service() {
  local service=$1

  if systemctl is-active --quiet "$service"; then
    return 0
  fi

  restart_with_cooldown "$service" "systemctl is-active check failed"
}

restart_with_cooldown() {
  local service=$1
  local reason=$2

  # Check cooldown
  local cooldown_file="${RESTART_COOLDOWN_FILE}-${service}"
  if [ -f "$cooldown_file" ]; then
    local last_restart=$(cat "$cooldown_file")
    local now=$(date +%s)
    local elapsed=$((now - last_restart))
    if [ $elapsed -lt $COOLDOWN_SECONDS ]; then
      echo "$(date -Iseconds) SKIP ${service} restart (cooldown: ${elapsed}s < ${COOLDOWN_SECONDS}s)"
      return 1
    fi
  fi

  echo "$(date -Iseconds) RESTART ${service} (${reason})"
  systemctl restart "$service"
  date +%s > "$cooldown_file"
  return 1
}

# MCP servers — check via HTTP health endpoint
check_port_service "state-mcp" 8000
check_port_service "web-tools-mcp" 8001

# Orchestrator — manages both persistent agent sessions (no HTTP port)
check_systemd_service "orchestrator"
