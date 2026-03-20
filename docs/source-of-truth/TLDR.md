# AI CoS — TL;DR
*Read this before and after the other source-of-truth docs for the concise picture.*
*Last updated: 2026-03-19*

---

## What Is This Project

An **AI Chief of Staff** for Aakash Kumar (MD at Z47/$550M fund + MD at DeVC/$60M fund). Not a task automator — an **action optimizer** that answers **"What's Next?"** across his full action space: investing, building, meetings, content, research, thesis building.

---

## It's a System of Agents, Not One Agent

| Agent | Role | Status |
|-------|------|--------|
| **ENIAC** | Content + thesis specialist. Analyses content, connects to thesis/portfolio/network, proposes scored actions. | Live (content pipeline running on droplet) |
| **Meetings Agent** (TBD name) | Real-world interaction specialist. Processes Granola transcripts, calendar, people signals → action suggestions. | Planned |
| **Action Strategist** (TBD) | Prioritises and manages the action queue across all sources: ENIAC + Meetings Agent + Aakash's own inputs. The "What's Next?" orchestrator. | Planned |
| **CRM Specialist** (maybe) | Manages Companies DB and Network DB data models. Keeps the structured data layer clean and queryable. | Idea stage |

Each agent is a specialist. They propose actions into a shared **Actions Queue**. The Action Strategist (eventually) and Aakash (now, via WebFront) prioritise and triage.

---

## How We Build: Team of Agents Pattern

We use a **team of CC subagents** to build. When prompted ("use a team of agents..."), CC assembles:

- **APM agents** — Product context for each domain. Loaded as reference docs so every subagent knows the product vision, data models, quality bars, and open questions for their area.
- **Backend specialists** — Database, API, agent code, infrastructure
- **Frontend specialists** — WebFront (digest.wiki), UI, rendering, Supabase client
- **QA specialists** — Verification, testing, edge cases

Each APM brief lives in `docs/product/` and gets loaded as context for the relevant subagents:

| APM Brief | Covers | File |
|-----------|--------|------|
| ENIAC APM | Content agent + action layer WebFront | `docs/product/eniac-apm-brief.md` |
| *(more as agents are built)* | | |

---

## The 4 Priority Buckets

Everything maps to these. They define WHY an action matters.

| # | Bucket | Data Model (fuel) | Status |
|---|--------|--------------------|--------|
| 1 | **New Cap Tables** — Find amazing companies to invest in | Companies DB | Not yet fully built |
| 2 | **Deepen Existing Cap Tables** — Follow-on decisions on portfolio | Portfolio DB + Companies DB | Partially connected |
| 3 | **DeVC Collective** — Grow the funnel: Community → External → Core | Network DB | Not yet fully built |
| 4 | **Thesis Evolution** — Evolve investment thesis lines | Thesis Tracker | Live |

---

## Everything Is Evolving

Three pillars being built simultaneously:

### 1. Agents
- ENIAC is live but early (1 content source, no Companies/Network DB connection yet)
- Meetings Agent and Action Strategist are designed but not built
- Each agent gets richer as data models and infra mature

### 2. Infrastructure
- Droplet (Ubuntu, Tailscale) runs the agent runtime
- Supabase Mumbai (PG17, pgvector) is the shared data layer
- Cloudflare Tunnels expose MCP endpoints
- digest.wiki (Next.js 16 on Vercel) is the WebFront

### 3. IRGI (Information Retrieval & Graph Intelligence)
- Phase A (in progress): Vector columns, Auto Embeddings (Voyage AI), FTS, hybrid search
- Phase B+ (future): Cross-content reasoning, knowledge graph, semantic retrieval across companies + people + thesis + content
- IRGI is what makes "this video + these thesis threads + these portfolio companies" queries possible

As each pillar matures, the others get better. ENIAC's analysis quality step-changes when Companies DB is queryable. IRGI enables cross-content reasoning. The Action Strategist can't exist until enough actions flow from multiple agents.

---

## Current State (March 2026)

**What works:**
- ENIAC processes YouTube content → structured digests → scored actions → Postgres + digest.wiki
- 6 active thesis threads with autonomous conviction management
- 115 actions in queue, 22 published digests
- Supabase (Mumbai, 31ms) as shared DB, WebFront connected

**What's being built now:**
- WebFront `/actions` page (accept/dismiss/rate — closes the feedback loop)
- IRGI Phase A (semantic search foundation)

**What's next:**
- Thesis `.md` file architecture (evidence trails in files, DB as index)
- Multi-source content (RSS, articles, podcasts)
- Companies DB + Network DB connections for ENIAC
- Meetings Agent design + build

---

## Quick Links

| Doc | What | When |
|-----|------|------|
| `CONTEXT.md` | Aakash's world, priorities, methodology, Notion schema | Domain context needed |
| `docs/source-of-truth/` | Full technical specs (11 files) | Building anything |
| `docs/product/eniac-apm-brief.md` | ENIAC product context | Building ENIAC or its WebFront |
| `TRACES.md` | Recent build history | Start of coding session |
| `mcp-servers/agents/content/CLAUDE.md` | ENIAC's actual instructions | Modifying agent behavior |
