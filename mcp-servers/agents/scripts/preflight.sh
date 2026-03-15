#!/bin/bash
# Pre-flight checks for agent services.
# Usage: preflight.sh <agent-name>
# Called by systemd ExecStartPre.
# Exits 0 on success, 1 on failure (blocks service start).

set -e

AGENT="$1"
AGENTS_DIR="/opt/agents"
MAX_WAIT=30

log() { echo "$(date -Iseconds) [preflight:$AGENT] $1"; }

# --- Common checks (all agents) ---

# .env must exist (H5 fix — not optional)
if [ ! -f "$AGENTS_DIR/.env" ]; then
    log "FATAL: $AGENTS_DIR/.env not found"
    exit 1
fi

# ANTHROPIC_API_KEY must be set
if ! grep -q "^ANTHROPIC_API_KEY=sk-" "$AGENTS_DIR/.env" 2>/dev/null; then
    log "FATAL: ANTHROPIC_API_KEY not set or invalid in .env"
    exit 1
fi

# --- Agent-specific checks ---

case "$AGENT" in
    sync-agent)
        # Postgres must be accepting connections
        log "Waiting for Postgres..."
        for i in $(seq 1 $MAX_WAIT); do
            if pg_isready -q 2>/dev/null; then
                log "Postgres ready after ${i}s"
                break
            fi
            if [ "$i" -eq "$MAX_WAIT" ]; then
                log "FATAL: Postgres not ready after ${MAX_WAIT}s"
                exit 1
            fi
            sleep 1
        done

        # NOTION_TOKEN must be set
        if ! grep -q "^NOTION_TOKEN=" "$AGENTS_DIR/.env" 2>/dev/null; then
            log "FATAL: NOTION_TOKEN not set in .env"
            exit 1
        fi

        # DATABASE_URL must be set
        if ! grep -q "^DATABASE_URL=" "$AGENTS_DIR/.env" 2>/dev/null; then
            log "FATAL: DATABASE_URL not set in .env"
            exit 1
        fi
        ;;

    web-agent)
        # Chrome/Chromium must be installed
        if ! command -v google-chrome >/dev/null 2>&1 && ! command -v chromium-browser >/dev/null 2>&1; then
            log "FATAL: Neither google-chrome nor chromium-browser found"
            exit 1
        fi
        ;;

    content-agent)
        # Sync Agent must be reachable (Content Agent depends on it)
        log "Checking Sync Agent..."
        if ! curl -sf --max-time 5 http://localhost:8000/health >/dev/null 2>&1; then
            log "WARNING: Sync Agent not reachable on port 8000 (will retry on first pipeline run)"
        fi
        ;;

    *)
        log "Unknown agent: $AGENT"
        exit 1
        ;;
esac

log "Pre-flight OK"
exit 0
