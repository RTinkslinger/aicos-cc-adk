# Folder Index

Active file map for the AI CoS project. Updated 2026-03-16 post-cleanup.

## Root

| Path | Purpose |
|------|---------|
| `CLAUDE.md` | Project instructions for Claude Code |
| `CONTEXT.md` | Domain knowledge — Aakash's world, priorities, data architecture |
| `TRACES.md` | Rolling build traces (current milestone iterations) |
| `LEARNINGS.md` | Trial-and-error patterns from sessions |
| `ROADMAP.md` | High-level roadmap |
| `CHECKPOINT.md` | In-progress state for context compaction recovery |
| `.mcp.json` | MCP server connections (State MCP + Web Tools MCP) |
| `.gitignore` | Git exclusions |

## mcp-servers/agents/ — Live System

The v3 agents monorepo. Everything that runs on the droplet.

| Path | Purpose |
|------|---------|
| `orchestrator/lifecycle.py` | Python daemon — manages both agent sessions + @tool bridge |
| `orchestrator/CLAUDE.md` | Orchestrator identity, rules, heartbeat protocol |
| `orchestrator/HEARTBEAT.md` | 5-step heartbeat checklist |
| `orchestrator/COMPACTION_PROTOCOL.md` | Traces file rotation protocol |
| `orchestrator/CHECKPOINT_FORMAT.md` | Session checkpoint template |
| `orchestrator/.claude/hooks/` | Filesystem hooks (Stop, UserPromptSubmit, PreCompact) |
| `orchestrator/.claude/settings.json` | Hook registration |
| `content/CLAUDE.md` | Content agent identity, pipeline, scoring, publishing |
| `content/CHECKPOINT_FORMAT.md` | Session checkpoint template |
| `content/.claude/hooks/` | Filesystem hooks |
| `content/.claude/settings.json` | Hook registration |
| `state/server.py` | State MCP server (5 tools, port 8000) |
| `state/db/` | Postgres connection, inbox, notifications, thesis |
| `web/server.py` | Web Tools MCP server (11 tools, port 8001) |
| `web/lib/` | Browser, scrape, search, fingerprint, strategy, stealth |
| `skills/` | 14 skill markdown files (content, web, sync, data) |
| `sync/` | Sync agent (disabled, code in repo) |
| `shared/` | Shared modules (types, logging, mcp_client) |
| `deploy.sh` | 3-phase deploy: SYNC → BOOTSTRAP → CLEANUP+RESTART |
| `deploy/bootstrap.sh` | Idempotent first-run state seeding |
| `deploy/cleanup.sh` | Remove known stale files |
| `deploy/tools/` | Droplet utility scripts (view-logs.py, live-*.sh) |
| `deploy/DROPLET-MANIFEST.md` | Every file expected on droplet + why |
| `infra/*.service` | systemd unit files |
| `sql/v2.2-migrations.sql` | Postgres schema migrations |
| `pyproject.toml` + `uv.lock` | Python dependencies |

## docs/ — Active Documentation

| Path | Purpose |
|------|---------|
| `source-of-truth/` | 9 canonical reference files (architecture, data, MCP tools, vision, methodology, capabilities, entities, system state) |
| `research/claude-agent-sdk-reference/` | 14 files — authoritative SDK reference |
| `research/2026-03-15-agent-web-mastery/` | 7 files — web intelligence research |
| `research/persistent-agent-architecture-research.md` | Persistent agent patterns (27 sources) |
| `research/2026-03-16-openclaw-architecture-ultra.md` | OpenClaw architecture deep research |
| `research/2026-03-16-agent-cost-optimization.md` | Cost optimization strategies |
| `research/2026-03-16-system-audit.md` | System monitoring audit |
| `research/cc-skills-to-adk-porting.md` | Skills porting guide |
| `research/Knowledge infra/` | Knowledge infrastructure research |
| `superpowers/specs/2026-03-15-architecture-v2.2-design.md` | v2.2 architecture spec (APPROVED) |
| `superpowers/plans/2026-03-16-agent-lifecycle-management.md` | Lifecycle management plan |
| `superpowers/plans/2026-03-16-orchestrator-content-agent.md` | Orchestrator + content agent plan |
| `superpowers/plans/2026-03-16-v2.2-implementation.md` | v2.2 implementation plan |
| `architecture/DROPLET-RUNBOOK.md` | Droplet operations runbook |
| `architecture/REPO-GUIDE.md` | Repo trust hierarchy and prior art |
| `architecture/CUSTOM-MCP-SETUP-HTTP.md` | MCP HTTP setup guide |
| `notion/README.md` | Notion operations guide + DB schemas |
| `v2.2-build-log.md` | v2.2 build testing reference |
| `archives/` | Archived docs by type (iteration-logs, checkpoints, audits, old plans/specs) |

## scripts/ — Local Tools

| Path | Purpose |
|------|---------|
| `yt` | YouTube content extraction CLI shortcut |
| `youtube_extractor.py` | YouTube playlist extractor (yt-dlp) |
| `branch_lifecycle.sh` | Branch create/status/diff/merge/close CLI |
| `action_scorer.py` | Standalone action scoring |
| `publish_digest.py` | Manual digest publishing |
| `content_digest_pdf.py` | PDF digest generation |
| `subagent-prompts/` | Subagent prompt templates |

## Other Active Directories

| Path | Purpose |
|------|---------|
| `claude-ai-sync/` | Cross-surface sync (CC ↔ CAI memory entries, changelog) |
| `portfolio-research/` | 20 per-company deep research files |
| `Training Data/` | 9 IDS methodology samples (emails, docs) |
| `queue/` | Content pipeline queue (YouTube extraction JSONs) |
| `traces/` | Build traces archive (milestone-1.md, milestone-2.md) |
| `aicos-digests/` | Separate git repo (gitignored) — digest.wiki Next.js site |

## Archives/ — Superseded Code

| Path | What was superseded by |
|------|----------------------|
| `Archives/mcp-servers-v1/ai-cos-mcp/` | `mcp-servers/agents/state/` + `content/` + `sync/` |
| `Archives/mcp-servers-v1/web-agent/` | `mcp-servers/agents/web/` |
| `Archives/mcp-servers-v1/web-tools-mcp/` | `mcp-servers/agents/web/` |
| `Archives/cowork-skills/` | Claude Code skills + CLAUDE.md |
