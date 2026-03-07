# Source of Truth — Index & Update Protocol

Exhaustive reference for the AI CoS current build state. Each file is self-contained and shareable with external AI without codebase access.

---

## File Index

| File | What It Covers | When to Read |
|------|---------------|--------------|
| **SYSTEM-STATE.md** | Infrastructure: droplet, Postgres, Cloudflare, Tailscale, Vercel, crons, endpoints, services | Debugging infra, adding services, onboarding a new AI surface |
| **MCP-TOOLS-INVENTORY.md** | All 17 MCP tools: signatures, params, purpose, surfaces, routing rules | Before calling or building MCP tools, understanding what the system can do |
| **DATA-ARCHITECTURE.md** | 8 Notion DBs + 7 Postgres tables: schemas, field ownership, sync patterns | Before any data operation, understanding where data lives and who owns it |
| **ARCHITECTURE.md** | 3-layer architecture, runners, integrations, live vs planned components | Understanding system design, planning new capabilities |
| **VISION-AND-DIRECTION.md** | Vision, build phases, current state vs ideal, gaps, design principles | Strategic planning, contextualizing work, understanding the "why" |

---

## Update Protocol

### Triggers

Update these docs when:

- **"Update your source of truth"** — User explicitly requests it
- **After major deploys** — New services, infrastructure changes, tool additions
- **After milestone compaction** — TRACES.md milestone archive = good checkpoint for docs update
- **After schema changes** — New Postgres tables, Notion DB modifications, field ownership changes
- **After new infrastructure** — New crons, endpoints, tunnels, services

### What to Update

| Trigger | Files to Update |
|---------|----------------|
| New infra (droplet, tunnel, cron) | SYSTEM-STATE.md |
| New MCP tool or tool signature change | MCP-TOOLS-INVENTORY.md |
| New Postgres table or Notion DB schema change | DATA-ARCHITECTURE.md |
| New runner, integration, or component | ARCHITECTURE.md |
| Direction shift, phase completion, new gaps identified | VISION-AND-DIRECTION.md |

### How to Update

1. Read the file being updated
2. Check against live state (code, config, infrastructure)
3. Update deltas — don't rewrite from scratch unless major restructuring happened
4. Update the "Last Updated" date at the top of each file

### Cross-References

These docs complement (not replace) existing documentation:

| Doc | Purpose | Location |
|-----|---------|----------|
| CLAUDE.md | Coding context, commands, protocols | Project root |
| CONTEXT.md | Domain context (Aakash's world, priorities, methodology) | Project root |
| TRACES.md | Recent build history (rolling window) | Project root |
| `docs/architecture/architecture-v0.3.md` | Full architecture spec | `docs/architecture/` |
| `docs/architecture/vision-v5.md` | Full vision narrative | `docs/architecture/` |
| `docs/architecture/DATA-SOVEREIGNTY.md` | Field ownership rules, sync patterns | `docs/architecture/` |
| `docs/architecture/DROPLET-RUNBOOK.md` | Operational runbook for droplet | `docs/architecture/` |
| `docs/notion/README.md` | Notion operations guide, recipes, gotchas | `docs/notion/` |
