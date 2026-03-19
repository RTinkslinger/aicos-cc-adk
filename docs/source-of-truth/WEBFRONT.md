# WebFront Architecture
*Last Updated: 2026-03-19*

The web frontend for the AI CoS system. Currently `digest.wiki` — evolving into a persistent, real-time interaction layer.

---

## Terminology

- **WebFront** — The web frontend (currently digest.wiki). Primary visual interaction surface.
- **Interface Layer** — All interaction surfaces: WebFront + CAI + WhatsApp + Notion.
- **Primary surfaces** — WebFront + CAI. These two carry the AI CoS vision forward.

---

## Current State (SSG, read-only)

### Stack
- **Framework:** Next.js (App Router)
- **Hosting:** Vercel (SSG, auto-deploy on git push)
- **Data:** Flat JSON files in `src/data/`, one per digest
- **Repo:** `RTinkslinger/aicos-digests` (separate git repo, 3 copies: Mac + Droplet + GitHub)
- **URL:** https://digest.wiki

### Data Flow (current)
```
Content Agent (droplet)
  → Writes {slug}.json to /opt/aicos-digests/src/data/
  → git commit + push origin main
  → GitHub receives push
  → Vercel Git Integration triggers build (~15s)
  → Next.js SSG reads all JSON files at build time
  → Static HTML deployed to digest.wiki
```

### Key Files
| File | Purpose |
|------|---------|
| `src/data/*.json` | Digest JSON files (17 currently) |
| `src/lib/types.ts` | DigestData TypeScript interface |
| `src/lib/digests.ts` | JSON reader + schema normalizer (v4↔v5 compat) |
| `src/app/page.tsx` | Digest list (sorted by generated_at) |
| `src/app/d/[slug]/page.tsx` | Individual digest detail page |
| `deploy.sh` | Manual deploy script (backup) |

### Limitations
- **No runtime DB connection.** Data is baked at build time.
- **Read-only.** No user interaction (no accept/reject, no messaging).
- **New digests require a full rebuild.** Content Agent must git push → Vercel rebuild.
- **No real-time state.** Pipeline status, thesis threads, action queue — all invisible.

---

## Target Architecture (Supabase + dynamic)

### Supabase (LIVE)
Postgres is on **Supabase** (ap-south-1 Mumbai, project `llfkxnsfczludgigknbs`, 31ms from droplet).

**What Supabase provides beyond managed Postgres:**
- **PostgREST** — Auto-generated REST API from tables. WebFront reads data without custom API routes.
- **Realtime** — Streams DB changes over WebSocket. Live action updates, pipeline status, thesis changes.
- **pgvector** (v0.8.0) — Semantic search. Combined with FTS for hybrid search (IRGI Phase A).
- **Auto Embeddings** — Invisible pipeline: DB trigger → pgmq → pg_cron → Edge Function → Voyage AI → vector column. Agents write content, embeddings appear automatically.
- **RLS** — Row Level Security for WebFront access control.
- **MCP server** — Schema management and debugging from Claude Code.

**Key architectural constraint:** Supabase extensions (pgmq, pg_cron, pg_net) are ONLY used as invisible infrastructure for Auto Embeddings. Agents never interact with them. Agents remain the orchestration layer; the database is storage + search.

Decision trail: `docs/superpowers/brainstorms/2026-03-18-managed-postgres-and-irgi-decisions.md`

### Data Flow (target)
```
Content Agent (droplet)
  → Writes analysis to Supabase (psql $DATABASE_URL)
  → Writes digest JSON to /opt/aicos-digests/src/data/ (for SSG compat)
  → git push → Vercel rebuild (for static digest pages)

WebFront (Vercel)
  → Server Components read from Supabase directly (@supabase/ssr)
  → Server Actions write to Supabase (action triage, thesis interaction)
  → Supabase Realtime for live pipeline status + agent notifications
  → ISR/on-demand revalidation for dynamic content
  → Static generation for digest detail pages (hybrid)
```

### Rendering Strategy
| Page Type | Strategy | Why |
|-----------|----------|-----|
| Digest list | ISR (revalidate on new content) | Frequently updated, benefits from caching |
| Digest detail `/d/[slug]` | SSG with on-demand revalidation | Content doesn't change after publish |
| Action triage | Server Components (dynamic) | Real-time data, user writes |
| Thesis dashboard | Server Components (dynamic) | Real-time conviction/evidence state |
| Pipeline status | Server Components + polling/streaming | Live operational view |
| Agent messaging | Server Components + streaming | Real-time bidirectional |

---

## Feature Roadmap

### Phase 1: Action Triage + Semantic Search Foundation
Accept/dismiss/defer proposed actions. Build IRGI Phase A (embeddings + FTS) as invisible infrastructure.
- `/actions` page: read `actions_queue` via `@supabase/ssr` (PostgREST)
- Server Actions: triage (Accept/Dismiss/Defer), rate outcome (Unknown/Helpful/Gold)
- Realtime subscription: new actions appear live without page refresh
- Related actions on digest detail pages
- **IRGI Phase A:** pgvector embedding columns (1024-dim Voyage AI `voyage-3.5`) + FTS indexes on content_digests and thesis_threads
- **Auto Embeddings pipeline:** DB trigger → pgmq → pg_cron → Edge Function → Voyage AI (invisible to agents)
- Hybrid search SQL function (vector similarity + FTS BM25)
- Full plan: `docs/superpowers/plans/2026-03-19-webfront-phase1-execution.md`

### Phase 2: Thesis Interaction
View thesis threads, evidence trail, conviction levels. Semantic search in action.
- Read `thesis_threads` from Supabase
- Evidence timeline view (for/against with timestamps)
- Key questions with OPEN/ANSWERED status
- Conviction visualization across threads
- **Semantic search:** "Find digests related to this thesis" powered by Phase 1 embeddings

### Phase 3: Pipeline Status
Live operational dashboard.
- `content_digests` status distribution (queued/processing/published/failed)
- Recent pipeline runs with timing
- Watch list overview
- Supabase Realtime for live status streaming

### Phase 4: Agent Messaging
Web UI alternative to CAI messaging relay.
- Post messages to `cai_inbox` via Server Actions
- Read `notifications` table for agent responses

---

## Connection Map

```
              ┌────────────────────────────────┐
              │         SUPABASE (Mumbai)       │
              │     (managed Postgres 17)       │
              │                                │
              │  11 tables (934 rows)          │
              │  pgvector 0.8.0 (semantic)     │
              │  FTS tsvector (keyword)        │
              │                                │
              │  PostgREST (auto REST API)     │
              │  Realtime (WebSocket streams)  │
              │  Auto Embeddings (invisible):  │
              │    trigger→pgmq→cron→Edge Fn   │
              │    →Voyage AI→vector column    │
              └──────┬──────┬──────────────────┘
                     │      │
          ┌──────────┘      └──────────┐
          │                            │
          ▼                            ▼
┌─────────────────┐          ┌──────────────────┐
│    DROPLET       │          │    VERCEL         │
│  (pure compute)  │          │  (WebFront)       │
│                  │          │                   │
│  Orchestrator    │          │  Server Components│
│  Content Agent   │          │    → @supabase/ssr│
│  State MCP       │          │  Server Actions   │
│  Web Tools MCP   │          │    → Supabase SDK │
│                  │          │  Realtime client  │
│  psql $DB_URL    │          │    → live updates │
│  (session pooler │          │  SSG digests      │
│   31ms latency)  │          │    → JSON files   │
└─────────────────┘          └──────────────────┘
          │                            │
          │  git push (digest JSONs)   │
          └────────────────────────────┘
```

---

## Key Decisions

| Decision | Rationale | Date |
|----------|-----------|------|
| Supabase over Neon | Heartbeat negates scale-to-zero. $6/mo more for real-time + PostgREST + MCP + dashboard. Real-time needed for Phases 3-4. | 2026-03-18 |
| Hybrid rendering (SSG + dynamic) | Digests are static content, interaction features need real-time data | 2026-03-18 |
| WebFront + CAI as primary surfaces | Focus investment on two surfaces that carry the AI CoS vision | 2026-03-18 |
| Feature order: triage → thesis → status → messaging | Triage has highest immediate value (action on insights), messaging is lowest (CAI relay works) | 2026-03-18 |

---

## Session Reference

Architecture decisions and initial documentation created in CC session **"webfront build out start"** (2026-03-18). To find the full decision trail in QMD, search conversations collection for `2026-03-18` + `webfront` or `neon` or `digest.wiki`.
