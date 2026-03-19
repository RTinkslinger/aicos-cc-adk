# Managed Postgres & IRGI Infrastructure Decisions
*2026-03-18 — Architecture decision session*
*CC Session: "webfront build out start" (2026-03-18, search QMD: `neon supabase irgi postgres managed`)*

How we selected the managed Postgres provider and validated the architecture against IRGI (Intelligent Retrieval & Graphing Infrastructure) requirements.

---

## Starting Point

**Context:** WebFront (digest.wiki) is evolving from static SSG to a dynamic interaction layer. It needs a Postgres connection from Vercel serverless. Current Postgres is self-hosted on the droplet (unreachable from Vercel).

**Decision made earlier in session:** Move to managed Postgres. Build the API layer is unnecessary — Next.js server components can query managed Postgres directly.

---

## Decision 1: Managed Postgres is the Path

**Why not keep self-hosted?**
- Vercel serverless functions can't reach droplet Postgres (no Tailscale on Vercel)
- Would need an API layer on the droplet (State MCP expansion or REST API)
- Single point of failure (droplet = agents + DB + MCP)

**Why not dual-DB (managed + droplet copy)?**
- Rejected: two databases = building a replication layer for zero benefit in a single-user system
- Distributed consistency problems outweigh any resilience gain

**Decision: Single managed Postgres. Agents connect to it. Frontend connects to it. One source of truth.**

---

## Decision 2: Apache AGE is Dead for Managed Postgres

IRGI Phase C (Temporal Knowledge Graph) had Apache AGE as the "keep everything in Postgres" option.

**Research finding:** Apache AGE is NOT supported on ANY major managed Postgres:
- Neon: ❌ (requested on Discord, not committed)
- Supabase: ❌ (GitHub discussion Nov 2025 — users gave up)
- AWS RDS: ❌
- Self-hosted: ✅ (only option)

**Impact:** Graph layer must be a separate service regardless of Postgres provider.

**IRGI research already favored** Neo4j / Zep/Graphiti over AGE for temporal knowledge graphs (bi-temporal timestamps, community detection, etc.).

**Decision: Graph = separate service (Neo4j/Zep/Graphiti). Managed Postgres handles relational + pgvector + FTS. Clean separation.**

---

## Decision 3: Supabase over Neon

### The Critical Realization

Neon's biggest advantage is scale-to-zero. But the AI CoS orchestrator runs `has_work()` every 60 seconds via `psql`. Neon auto-suspends after 5 minutes of inactivity. **The heartbeat prevents suspension — Neon would never scale to zero for this workload.** Scale-to-zero is negated.

### Revised Pricing

| Provider | Monthly Cost | What You Get |
|----------|-------------|--------------|
| **Neon Launch** | $19/mo (always active) | Pure Postgres |
| **Supabase Pro** | $25/mo (always on) | Postgres + real-time + PostgREST + MCP + dashboard |

$6/mo delta for significant DX and feature advantages.

### Comparison (AI CoS specific)

| Dimension | Neon | Supabase | Winner |
|-----------|------|----------|--------|
| Vercel integration | Native serverless driver | Good (supabase-ssr) | Neon (slight) |
| Agent psql from droplet | Standard connection | Standard connection | Equal |
| pgvector + FTS | Full support | Full support | Equal |
| Real-time subscriptions | Need Pusher/Ably ($15-25/mo) | Built-in (LISTEN/NOTIFY) | **Supabase** |
| PostgREST (auto REST API) | None | Auto-generated from tables | **Supabase** |
| MCP server | Via Vercel MCP | Official, 20+ tools | **Supabase** |
| Auth | External (Clerk) | Built-in | Irrelevant (single user) |
| Storage | External | Built-in | Irrelevant (JSON in git) |
| Edge Functions | None | Deno-based | Irrelevant (droplet handles) |
| Scale-to-zero | Yes (but negated by heartbeat) | No | Negated |
| Branching | Instant copy-on-write | Migration-based | Neon (not critical for us) |
| Lock-in | Zero (pure Postgres) | Mild (supabase-js patterns) | Neon (slight) |
| Dashboard | Basic | Rich (visual DB inspection) | **Supabase** |
| Extensions | ~80 | ~100+ | Supabase (slight) |

### Why Supabase for AI CoS Specifically

1. **Real-time for WebFront Phases 3-4** (pipeline status, agent messaging) — built-in, no extra service
2. **MCP server for development velocity** — manage schema, query, debug from Claude Code
3. **PostgREST for rapid prototyping** — instant API when server components aren't needed
4. **Dashboard for debugging** — visual inspection of agent-written data
5. **Scale-to-zero is irrelevant** — heartbeat keeps DB always-active regardless
6. **$6/mo for all of the above** — trivial cost difference

### What We Accept

- No instant branching (not critical for single-dev)
- Mild lock-in via supabase-js (mitigated: can always use raw SQL via connection string)
- No native Vercel serverless driver (mitigated: `@supabase/ssr` works well)

---

## Architecture Summary (Post-Decisions)

```
SUPABASE (managed Postgres)
├── Relational data (10 tables)
├── pgvector (IRGI Phase A: hybrid search embeddings)
├── Postgres FTS (IRGI Phase A: BM25 keyword search)
├── Real-time subscriptions (WebFront pipeline status + messaging)
├── PostgREST (auto REST API for rapid prototyping)
└── Direct psql access (agents on droplet)

DROPLET (pure compute)
├── Orchestrator agent (ClaudeSDKClient)
├── Content Agent (ClaudeSDKClient)
├── State MCP (CAI window)
├── Web Tools MCP (browser automation)
└── Embedding compute (llama-cpp-python, future)

SEPARATE SERVICES (future)
├── Graph: Neo4j or Zep/Graphiti (IRGI Phase C)
└── Code/docs search: QMD (IRGI Phase B, already deployed)

VERCEL (WebFront)
├── Next.js server components → Supabase direct queries
├── Server Actions → Supabase writes
├── SSG digest pages → JSON files (existing flow)
└── Real-time subscriptions → Supabase Realtime
```

---

## IRGI Compatibility Check

| IRGI Phase | Requirement | Supabase Fit |
|-----------|------------|--------------|
| Phase A: Hybrid Search | pgvector + Postgres FTS + reranking | ✅ pgvector + FTS built-in. Reranking = compute on droplet. |
| Phase B: QMD Cloud | Separate service, index sync | ✅ Already deployed, independent of DB choice |
| Phase C: Temporal Graph | Apache AGE or Neo4j/Graphiti | ✅ Separate service. Not a Postgres extension concern. |
| Phase D: Query Router | Routes to hybrid search, graph, QMD | ✅ Orchestration logic, DB-agnostic |
| Phase E: RL Infrastructure | action_outcomes table + preference queries | ✅ Standard Postgres, works on Supabase |

**No IRGI phase is blocked or compromised by the Supabase choice.**
