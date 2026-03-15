#!/bin/bash
# Health check for all 3 agents. Restarts on failure.
# Installed as cron: * * * * * /opt/agents/cron/health_check.sh >> /opt/agents/logs/health.log 2>&1

LOCKFILE="/tmp/agents-health-check.lock"
RESTART_COOLDOWN_FILE="/tmp/agents-last-restart"
COOLDOWN_SECONDS=300  # Don't restart same service twice in 5 min

# Prevent concurrent runs
exec 200>"$LOCKFILE"
flock -n 200 || exit 0

check_and_restart() {
  local service=$1
  local port=$2

  if curl -sf --max-time 10 "http://localhost:${port}/health_check" > /dev/null 2>&1; then
    return 0
  fi

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

  echo "$(date -Iseconds) RESTART ${service} (health check failed on port ${port})"
  systemctl restart "$service"
  date +%s > "$cooldown_file"
  return 1
}

check_and_restart "sync-agent" 8000
check_and_restart "web-agent" 8001
check_and_restart "content-agent" 8002
