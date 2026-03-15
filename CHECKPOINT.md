# Checkpoint
*Written: 2026-03-15 23:45 IST*

## Current Task
Architecture revision: shift from "Sync Agent as DB gatekeeper" to "agents have direct Postgres access, Sync Agent handles external sync + conflict resolution." Then implement the revised architecture.

## Progress
- [x] Three-agent build complete (63 files, 9,358 lines, deployed)
- [x] Code audit complete (25/25 items resolved)
- [x] Architecture rethink discussed and clarified (see Key Decisions below)
- [ ] Revise design spec with new architecture
- [ ] Implement: move DB tools to shared/db/, give agents direct Postgres access
- [ ] Implement: asyncpg migration (urgent — sync DB calls block event loop)
- [ ] Implement: convert batch tools to singular
- [ ] Implement: revised Sync Agent (Notion sync + freshness + conflict resolution only)

## Key Decisions (from this conversation, NOT yet in spec)

### 1. Agents get direct Postgres access
- All agents import from `shared/db/` (in-process tools, like CC's built-in file tools)
- No more Sync Agent as DB gatekeeper (Decision #15 from old spec is REVISED)
- Postgres is a local resource → in-process access (no MCP overhead)
- Future: if agents run on different machines, THEN add Postgres MCP server (YAGNI)

### 2. Sync Agent's revised role
- **Notion sync:** Reads Postgres for new/changed records → pushes to Notion
- **Notion→Postgres sync:** Pulls human-owned field changes (Status, Outcome) from Notion to Postgres
- **Freshness guarantee:** Provides `is_synced(table?)` tool — tells other agents "Postgres reflects latest Notion state"
- **Conflict resolution:** If multiple agents write conflicting data, Sync Agent resolves
- **Gateway for CAI:** Still serves mcp.3niac.com, provides state query tools
- **NO LONGER:** Write-receiver tools (write_digest, write_actions, etc.) — agents write directly

### 3. DB tools location: shared/db/ (domain-split)
```
shared/db/
├── __init__.py        # re-exports
├── connection.py      # asyncpg pool (shared by all agents)
├── thesis_db.py       # thesis CRUD
├── actions_db.py      # actions CRUD
├── preferences.py     # preference store
├── digests_db.py      # digest entries
└── change_events.py   # change tracking
```

### 4. Timers are internal to each agent
- Content Agent: 5-min pipeline timer is part of agent's own logic
- Sync Agent: 10-min sync timer is part of agent's own logic
- NOT external cron. NOT Python scripts. Agent's own scheduling.

### 5. Agentic-first thinking (user mandate)
- Stop mixing Python/cron patterns with agentic architecture
- Agents have skills, tools, MCPs, and Agent SDK capabilities
- Build with agentic lens, not script lens
- Reference: `docs/superpowers/specs/2026-03-15-agentic-pipeline-reference.md`

### 6. Rule: Never act without AskUserQuestion
- Added to top of ~/.claude/CLAUDE.md
- Memory: `feedback_never_act_without_askuserquestion.md`
- For ANY code fix: research → analyse → present → AskUserQuestion → act → log

## Next Steps (for new session)
1. Read this CHECKPOINT.md
2. Read the current spec: `docs/superpowers/specs/2026-03-15-three-agent-architecture-design.md`
3. Read the agentic pipeline reference: `docs/superpowers/specs/2026-03-15-agentic-pipeline-reference.md`
4. Revise the spec with decisions 1-5 above (use superpowers:brainstorming skill)
5. Write implementation plan for the revision (move DB to shared/db/, asyncpg, revise Sync Agent)
6. Execute via subagent-driven development

## Context
- Branch: `feat/three-agent-architecture` (pushed, 30+ commits)
- Droplet: 3 agents running (sync:8000, web:8001, content:8002), old services stopped
- Droplet tier: 2 vCPU, 4GB RAM ($24/mo)
- Agent SDK: claude-agent-sdk 0.1.48, FastMCP 3.1.1
- Key learnings from this session:
  - FastMCP 3.x uses `lifespan` context manager, not `on_startup`
  - FastMCP 3.x uses `custom_route("/health", methods=["GET"])` for ops endpoints
  - query() DOES support hooks in SDK 0.1.48 (tested live)
  - cron.d drop-in files > crontab manipulation
  - systemd cgroup kill handles Chrome cleanup (no ExecStopPost needed)
  - WatchdogSec without sd_notify is worse than useless
