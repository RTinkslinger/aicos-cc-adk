#!/bin/bash
# WhatsApp Sync Pipeline — runs every 15 minutes via launchd
# Extracts new messages from WhatsApp SQLite → markdown → Supabase
set -euo pipefail

PROJECT_DIR="/Users/Aakash/Claude Projects/Aakash AI CoS CC ADK"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/whatsapp-sync.log"
PYTHON="/opt/homebrew/bin/python3"
LOCK_FILE="/tmp/whatsapp-sync.lock"

mkdir -p "$LOG_DIR"

# Prevent overlapping runs
if [ -f "$LOCK_FILE" ]; then
    pid=$(cat "$LOCK_FILE" 2>/dev/null)
    if kill -0 "$pid" 2>/dev/null; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') SKIP: previous run still active (PID $pid)" >> "$LOG_FILE"
        exit 0
    fi
    rm -f "$LOCK_FILE"
fi
echo $$ > "$LOCK_FILE"
trap 'rm -f "$LOCK_FILE"' EXIT

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOG_FILE"
}

log "START: WhatsApp sync pipeline"

# Check WhatsApp DB exists and is recent
DB_PATH="$HOME/Library/Group Containers/group.net.whatsapp.WhatsApp.shared/ChatStorage.sqlite"
if [ ! -f "$DB_PATH" ]; then
    log "ERROR: WhatsApp database not found"
    exit 1
fi

# Check DB was modified in the last 2 hours (WhatsApp Desktop is running)
DB_AGE=$(( $(date +%s) - $(stat -f %m "$DB_PATH") ))
if [ "$DB_AGE" -gt 7200 ]; then
    log "WARN: WhatsApp DB is ${DB_AGE}s old — WhatsApp Desktop may not be running"
fi

# Step 1: Extract (SQLite → markdown, incremental)
log "EXTRACT: starting incremental extraction"
EXTRACT_OUTPUT=$($PYTHON "$PROJECT_DIR/scripts/whatsapp_extract.py" --min-messages 1 2>&1) || {
    log "ERROR: extraction failed: $EXTRACT_OUTPUT"
    exit 1
}
log "EXTRACT: $EXTRACT_OUTPUT" | tail -3 >> "$LOG_FILE"

# Step 2: Ingest (markdown → Supabase, via REST API)
log "INGEST: starting Supabase ingestion"
INGEST_OUTPUT=$($PYTHON "$PROJECT_DIR/scripts/whatsapp_ingest.py" --api 2>&1) || {
    log "ERROR: ingestion failed: $INGEST_OUTPUT"
    exit 1
}
log "INGEST: $INGEST_OUTPUT" | tail -3 >> "$LOG_FILE"

log "DONE: pipeline complete"

# Trim log to last 1000 lines
if [ -f "$LOG_FILE" ] && [ "$(wc -l < "$LOG_FILE")" -gt 1000 ]; then
    tail -500 "$LOG_FILE" > "$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"
fi
