#!/bin/bash
# Cron wrapper: AI CoS unified content pipeline (every 5 minutes)
# Uses flock to prevent overlapping runs — if previous run is still
# processing videos, this invocation silently exits.
#
# Install in crontab:
#   */5 * * * * /opt/ai-cos-mcp/cron/pipeline.sh >> /opt/ai-cos-mcp/logs/pipeline.log 2>&1

export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/root/.deno/bin"

LOCKFILE="/tmp/aicos-pipeline-cron.lock"

exec 200>"$LOCKFILE"
flock -n 200 || { echo "$(date -u '+%Y-%m-%d %H:%M:%S') Pipeline already running, skipping."; exit 0; }

cd /opt/ai-cos-mcp
/root/.local/bin/uv run python -m runners.pipeline
