#!/bin/bash
# Cleanup — removes known stale files from previous versions.
# Safe to run on every deploy. Only removes files we KNOW are stale.
set -e

DIR="${1:-/opt/agents}"

echo "  [cleanup] Removing stale files..."

# Old v1 systemd units (replaced by infra/)
rm -rf "$DIR/systemd/" 2>/dev/null && echo "    removed systemd/" || true

# Old v1 root server.py
rm -f "$DIR/server.py" 2>/dev/null && echo "    removed server.py" || true

# Old cron scripts (replaced by systemd)
rm -rf "$DIR/cron/" 2>/dev/null && echo "    removed cron/" || true

# Old sync manual scripts (not in repo)
for f in notion_pull.py pull_changes.py pull_human_changes.py pull_human_fields.py pull_notion_changes.py push_thesis_threads.py; do
  rm -f "$DIR/sync/$f" 2>/dev/null && echo "    removed sync/$f" || true
done

# Stale content-agent.service (content agent now managed by lifecycle.py)
rm -f "$DIR/infra/content-agent.service" 2>/dev/null && echo "    removed infra/content-agent.service" || true
systemctl disable content-agent 2>/dev/null || true
systemctl stop content-agent 2>/dev/null || true

# Orphaned state files at wrong path (old v2.2)
rm -f "$DIR/state/content_last_log.txt" "$DIR/state/last_pipeline_run.txt" 2>/dev/null && echo "    removed orphaned state files" || true

# Stale settings.local.json (debugging artifacts)
rm -f "$DIR/orchestrator/.claude/settings.local.json" "$DIR/content/.claude/settings.local.json" 2>/dev/null && echo "    removed settings.local.json copies" || true

# Old data queue files (v1 extraction pipeline)
if [ -d "$DIR/data/queue" ] && [ "$(ls -1 "$DIR/data/queue"/youtube_extract_*.json 2>/dev/null | wc -l)" -gt 0 ]; then
  rm -f "$DIR/data/queue"/youtube_extract_*.json 2>/dev/null && echo "    removed old queue extraction JSONs" || true
fi

echo "  [cleanup] Done"
