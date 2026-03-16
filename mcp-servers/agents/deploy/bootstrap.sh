#!/bin/bash
# Bootstrap — idempotent first-run setup. Creates dirs and seed files ONLY if they don't exist.
# Safe to run on every deploy.
set -e

DIR="${1:-/opt/agents}"

echo "  [bootstrap] Ensuring runtime directories..."
mkdir -p "$DIR"/{data/queue/processed,data/sessions,data/digests,logs,cookies}
mkdir -p "$DIR"/traces/archive
mkdir -p "$DIR"/orchestrator/state
mkdir -p "$DIR"/content/state

# Traces seed files
if [ ! -f "$DIR/traces/manifest.json" ]; then
  echo "  [bootstrap] Seeding traces/manifest.json"
  cat > "$DIR/traces/manifest.json" << 'EOF'
{
  "orc": {
    "session": 1,
    "input_tokens": 0,
    "output_tokens": 0,
    "last_updated": null
  },
  "content": {
    "session": 1,
    "input_tokens": 0,
    "output_tokens": 0,
    "last_updated": null
  }
}
EOF
fi

if [ ! -f "$DIR/traces/active.txt" ]; then
  TRACEFILE="traces/$(date -u +%Y%m%d-%H%M).md"
  echo "  [bootstrap] Seeding traces/active.txt -> $TRACEFILE"
  echo "$TRACEFILE" > "$DIR/traces/active.txt"
  cat > "$DIR/$TRACEFILE" << EOF
# Traces — Started $(date -u +"%Y-%m-%d %H:%M UTC")

## Summary
(written on compaction)

## Iteration Logs
EOF
fi

# Orchestrator state seed
[ ! -f "$DIR/orchestrator/state/orc_session.txt" ] && echo "1" > "$DIR/orchestrator/state/orc_session.txt" && echo "  [bootstrap] Seeded orc_session.txt"
[ ! -f "$DIR/orchestrator/state/orc_iteration.txt" ] && echo "0" > "$DIR/orchestrator/state/orc_iteration.txt" && echo "  [bootstrap] Seeded orc_iteration.txt"

# Content state seed
[ ! -f "$DIR/content/state/content_session.txt" ] && echo "1" > "$DIR/content/state/content_session.txt" && echo "  [bootstrap] Seeded content_session.txt"
[ ! -f "$DIR/content/state/content_iteration.txt" ] && echo "0" > "$DIR/content/state/content_iteration.txt" && echo "  [bootstrap] Seeded content_iteration.txt"
[ ! -f "$DIR/content/state/last_pipeline_run.txt" ] && date -u +"%Y-%m-%dT%H:%M:%SZ" > "$DIR/content/state/last_pipeline_run.txt" && echo "  [bootstrap] Seeded last_pipeline_run.txt"

echo "  [bootstrap] Done"
