# Source of Truth — Index & Update Protocol

Exhaustive reference for the AI CoS system. Each file is self-contained and shareable with external AI without codebase access.

---

## File Index

| File | What It Covers | When to Read |
|------|---------------|--------------|
| **TLDR.md** | Concise project picture: agent system, build pattern, priority buckets, current state | First and last — before and after reading everything else |
| **VISION-AND-DIRECTION.md** | Vision, optimization problem, design principles, north star | Strategic planning, contextualizing work, understanding the "why" |
| **METHODOLOGY.md** | 15 build principles, technology evaluation framework | Making technology choices, understanding why we build the way we do |
| **ARCHITECTURE.md** | 3-layer architecture, agent pattern, MCP tools, scoring, learning loop, conviction engine | Understanding system design, planning new capabilities |
| **MCP-TOOLS-INVENTORY.md** | All MCP tools: signatures, params, purpose, surfaces, routing rules | Before calling or building MCP tools |
| **DATA-ARCHITECTURE.md** | Notion DBs + Postgres tables: schemas, field ownership, sync patterns | Before any data operation, understanding where data lives |
| **CAPABILITY-MAP.md** | 8 capabilities at IDS levels (+/++/+++), dependency graph, growth model | Planning what to build next, understanding capability dependencies |
| **ENTITY-SCHEMAS.md** | Vision-state entity schemas, runner pattern template, IDS trail spec, 3-actor sovereignty model | Designing new entities/fields, extending data model |
| **PRIOR-ART.md** | Full chronological build history (35+ entries, 4 eras). Append-only. | Before building anything — check what's been tried, what worked, what didn't |
| **WEBFRONT.md** | Web frontend (digest.wiki): current SSG state, Supabase migration plan, feature roadmap, connection map | Planning frontend features, understanding data flow to/from WebFront |
| **DROPLET-RUNBOOK.md** | Operational guide: services, directory layout, credentials, deploy, monitoring, failure recovery, scaling | Debugging infra, deploying, adding services |
| **MCP-CLOUDFLARE-TUNNEL-SETUP.md** | Cloudflare Tunnel setup and configuration guide | Setting up or debugging MCP tunnel endpoints |
| **MACHINERIES.md** | Build protocol: 6 iteration machines, army-of-agents approach, loop patterns, restart context | Starting a new session, resuming work, understanding the build approach |
| **GOLDEN-SESSION-PATTERN.md** | **THE definitive execution pattern (v2).** Machine list, loop structure, feedback infrastructure, orchestrator behavior, agent-first architecture, session checklist. | **MUST READ before any "resume machineries" command. Loaded by CLAUDE.md.** |
| **MACHINE-LOOP-PLAYBOOK.md** | Operational supplement: quick reference, prompt template, Supabase IDs, Cindy email setup, droplet services | Quick operational lookup during machine loops |

---

## Update Protocol

### Triggers

Update these docs when:

- **"Update your source of truth"** — User explicitly requests it
- **After major deploys** — New services, infrastructure changes, tool additions
- **After milestone compaction** — TRACES.md milestone archive = good checkpoint for docs update
- **After schema changes** — New Postgres tables, Notion DB modifications, field ownership changes

### What to Update

| Trigger | Files to Update |
|---------|----------------|
| New infra (droplet, tunnel, services) | DROPLET-RUNBOOK.md |
| New MCP tool or tool signature change | MCP-TOOLS-INVENTORY.md |
| New Postgres table or Notion DB schema change | DATA-ARCHITECTURE.md |
| New component, integration, or architectural pattern | ARCHITECTURE.md |
| Frontend feature, data flow, or rendering strategy change | WEBFRONT.md |
| Direction shift, design principle change | VISION-AND-DIRECTION.md |

### How to Update

1. Read the file being updated
2. Check against live state (code, config, infrastructure)
3. Update deltas — don't rewrite from scratch unless major restructuring happened
4. Update the "Last Updated" date at the top of each file

### Cross-References

**This folder is the single canonical reference.** Other docs are operational or historical:

| Doc | Purpose | Location |
|-----|---------|----------|
| CLAUDE.md | Coding context, commands, protocols | Project root |
| CONTEXT.md | Domain context (Aakash's world, priorities, methodology) | Project root |
| TRACES.md | Recent build history (rolling window) | Project root |
| `docs/notion/README.md` | Notion operations guide, recipes, gotchas | `docs/notion/` |
