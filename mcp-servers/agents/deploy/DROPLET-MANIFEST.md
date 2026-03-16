# Droplet Manifest — /opt/agents/

Everything expected on the droplet and why. Updated when files are added/removed.

## CODE (from rsync — deploy.sh Phase 1)

Synced from repo on every deploy. `--delete` removes files deleted from repo.

| Path | Purpose |
|------|---------|
| `orchestrator/lifecycle.py` | Python daemon — manages both agents |
| `orchestrator/CLAUDE.md` | Orchestrator identity + rules |
| `orchestrator/HEARTBEAT.md` | Heartbeat checklist |
| `orchestrator/COMPACTION_PROTOCOL.md` | Traces compaction protocol |
| `orchestrator/CHECKPOINT_FORMAT.md` | Session checkpoint format |
| `orchestrator/.claude/hooks/*.sh` | Filesystem hooks (Stop, UserPromptSubmit, PreCompact) |
| `orchestrator/.claude/settings.json` | Hook registration |
| `content/CLAUDE.md` | Content agent identity + rules |
| `content/CHECKPOINT_FORMAT.md` | Session checkpoint format |
| `content/.claude/hooks/*.sh` | Filesystem hooks |
| `content/.claude/settings.json` | Hook registration |
| `content/*.py` | v2.2 code (agent.py, server.py, tools.py, hooks.py, lib/) |
| `state/` | State MCP server (server.py, db/) |
| `web/` | Web Tools MCP server |
| `shared/` | Shared modules |
| `sync/` | Sync agent (disabled, code stays) |
| `skills/**/*.md` | 14 skill files across 4 categories |
| `.claude/agents/*.md` | Subagent definitions |
| `infra/*.service` | systemd unit files |
| `pyproject.toml`, `uv.lock` | Python dependencies |

## TOOLS (from deploy/tools/ — deploy.sh Phase 1)

Utility scripts synced on every deploy.

| Path | Purpose |
|------|---------|
| `view-logs.py` | JSONL log viewer (piped through for clean output) |
| `live-orc.sh` | `ssh -t root@droplet /opt/agents/live-orc.sh` |
| `live-content.sh` | `ssh -t root@droplet /opt/agents/live-content.sh` |
| `live-traces.sh` | `ssh -t root@droplet /opt/agents/live-traces.sh` |

## RUNTIME (created by bootstrap or agents — never in repo)

| Path | Created By | Purpose |
|------|-----------|---------|
| `orchestrator/state/orc_session.txt` | bootstrap / lifecycle.py | Session counter |
| `orchestrator/state/orc_iteration.txt` | bootstrap / Stop hook | Iteration counter |
| `orchestrator/state/orc_last_log.txt` | Agent (Write tool) | Last heartbeat summary |
| `orchestrator/state/orc_checkpoint.md` | Agent (on compaction) | Session checkpoint |
| `orchestrator/live.log` | lifecycle.py PostToolUse hook | Real-time activity log |
| `content/state/content_session.txt` | bootstrap / lifecycle.py | Session counter |
| `content/state/content_iteration.txt` | bootstrap / Stop hook | Iteration counter |
| `content/state/content_last_log.txt` | Agent (Write tool) | Last prompt summary |
| `content/state/last_pipeline_run.txt` | Agent (Bash) | Pipeline timestamp |
| `content/state/content_checkpoint.md` | Agent (on compaction) | Session checkpoint |
| `content/live.log` | lifecycle.py PostToolUse hook | Real-time activity log |
| `traces/manifest.json` | bootstrap / lifecycle.py | Token usage per agent |
| `traces/active.txt` | bootstrap / orchestrator | Pointer to current traces file |
| `traces/*.md` | bootstrap / Stop hook | Iteration log files |
| `traces/archive/*.md` | Orchestrator (compaction) | Archived traces |
| `data/watch_list.json` | Manual (Aakash) | Curated content sources |
| `data/digests/*.json` | Content agent | Published digest JSONs |
| `logs/*.log` | systemd | Service logs |

## SECRETS (manual setup — never in repo)

| Path | Purpose |
|------|---------|
| `.env` | ANTHROPIC_API_KEY, DATABASE_URL, FIRECRAWL_API_KEY |

## EXTERNAL (separate sync — not managed by deploy.sh)

| Path | Synced By | Purpose |
|------|----------|---------|
| `CONTEXT.md` | deploy.sh step 3 | Domain knowledge from parent project |
| `cookies/*.txt` | `~/.ai-cos/scripts/cookie-sync.sh` (Mac cron) | YouTube auth cookies |
