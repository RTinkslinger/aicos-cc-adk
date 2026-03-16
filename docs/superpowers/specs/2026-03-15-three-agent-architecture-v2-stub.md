# Three-Agent Architecture v2 — Design Stub

**Date:** 2026-03-15
**Status:** STUB — design-in-progress, re-anchoring from fundamentals
**Supersedes:** `2026-03-15-three-agent-architecture-design.md` (v1, LOCKED but architecturally revised)

---

## Design Principles (APPROVED)

1. **Fully Agentic First** — Token costs not a design constraint. Optimize later.
2. **Extensible by Instruction, Not by Code** — New sources/rules = instruction changes, not Python.
3. **Agent Behavior = Instructions (.md files)** — system_prompt.md is the primary config.
4. **Postgres Access is Universal, Locality Determines Method** — shared/db/ direct for local, MCP gateway for remote.
5. **Flag-Based Sync** — Agents write Postgres with `notion_synced = false`. Sync Agent pushes to Notion. No sync_queue.
6. **Infrastructure vs Intelligence** — Python = plumbing. Agents = thinking.
7. **CAI is a Generalist Agent** — Same logical capabilities as any agent, accessed via MCP.
8. **Agent = ClaudeSDKClient** — No raw API calls. No manual tool loops.

## Key Decisions (from checkpoint + brainstorming)

1. Agents get direct Postgres access via shared/db/
2. Sync Agent = Notion specialist + CAI gateway (not DB gatekeeper)
3. DB tools in shared/db/ (domain-split modules)
4. Timers internal to each agent process
5. Agentic-first thinking (agent SDK methods first, always)
6. Content Agent has zero Sync Agent dependency
7. Flag-based sync (notion_synced column, no sync_queue table)
8. Freshness = sync_metadata Postgres table + agent reasoning (not an MCP tool)
9. CAI has same logical capabilities as local agents (via Sync Agent gateway)
10. Web is an MCP (tools) + Skills (intelligence), not an agent
11. Skills carry reasoning intelligence as markdown, loaded on demand
12. The formula: Agent = Model + Instructions + MCPs + Skills + System Tools + Hooks

## Taxonomy (APPROVED v4)

| Term | Definition | CC Parallel |
|------|-----------|------------|
| Agent | ClaudeSDKClient + instructions + MCPs + skills + system tools + hooks | Claude in a project |
| Instructions | system_prompt.md — identity, rules, domain knowledge | CLAUDE.md |
| MCP | Tool server providing capabilities via tools | Playwright MCP, Notion MCP |
| Tool | Callable capability on an MCP | Read, Write, mcp__notion__search |
| Skill | Markdown instruction loaded on demand. Intelligence as text. | CC skills |
| System Tool | shared/db/ — direct Postgres access in tool handlers | CC built-ins (Read, Write, Bash) |
| Hook | Lifecycle callback for observability + guardrails | CC hooks |
| Session | One agent reasoning conversation | CC conversation |
| Scheduled Session | Timer-triggered session | (no CC parallel) |
| Gateway | Sync Agent exposing tools for remote callers (CAI) | (no CC parallel) |

## Architecture Sketch

Three processes:
1. **Web Tools MCP** (port 8001) — Stateful tool server (Playwright, strategy, cookies). NOT an agent.
2. **Content Agent** (port 8002) — Agent on 5-min timer. Uses web tools + content skills + shared/db/.
3. **Sync Agent** (port 8000, gateway) — Agent on 10-min timer. Notion sync + CAI gateway.

Shared: shared/db/, skills/, shared/types.py, shared/logging.py

## RE-ANCHORING IN PROGRESS

The above was developed through iterative brainstorming. Now re-anchoring from fundamentals:
- Correcting CC parallel (Claude = model, CC = agent, Agent SDK = same harness as CC)
- Clarifying the three consumer tiers: CAI (cloud-native, MCP-only, no skills), CC (Mac, full access), Custom Agents (droplet, CC-like capabilities)
- CAI as the only persistent conversational interface — gateway to everything
- The architectural problem: how to give CAI parity with CC/custom agents given MCP-only access and no skills

See conversation for full context. Next step: rebuild from corrected fundamentals.
