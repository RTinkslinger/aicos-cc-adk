# WebFront Architecture
*Last Updated: 2026-03-18*

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

### Decision: Postgres → Supabase
Postgres moves from the droplet to **Supabase** (managed Postgres with real-time, PostgREST, MCP).

**Why Supabase over Neon:**
- Agent heartbeat (60s) prevents Neon scale-to-zero — negates its biggest advantage
- For $6/mo more ($25 vs $19), Supabase adds: real-time subscriptions, PostgREST, MCP server, dashboard
- Real-time subscriptions are needed for WebFront Phases 3-4 (pipeline status, agent messaging)
- MCP server (20+ tools) accelerates development from Claude Code
- PostgREST gives instant API for rapid prototyping
- Both support pgvector + FTS equally (IRGI hybrid search)
- Full decision trail: `docs/superpowers/brainstorms/2026-03-18-managed-postgres-and-irgi-decisions.md`

**Migration path:**
1. Create Supabase project
2. `pg_dump` droplet Postgres → import to Supabase
3. Enable pgvector extension
4. Update `DATABASE_URL` on droplet (.env) and Vercel (env vars)
5. Verify agent pipeline works against Supabase
6. Decommission droplet Postgres

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

### Phase 1: Action Triage
Accept/dismiss/defer proposed actions directly from digest pages and a dedicated actions view.
- Read `actions_queue` from Supabase via server components
- Server Actions to update status (Proposed → Accepted/Dismissed)
- Filter by priority, thesis connection, status
- Outcome feedback (Unknown/Helpful/Gold)

### Phase 2: Thesis Interaction
View thesis threads, evidence trail, conviction levels. Light editing.
- Read `thesis_threads` from Supabase
- Evidence timeline view (for/against with timestamps)
- Key questions with OPEN/ANSWERED status
- Conviction visualization across threads

### Phase 3: Pipeline Status
Live operational dashboard replacing the manual postgres-to-notion dump.
- `content_digests` status distribution (queued/processing/published/failed)
- Recent pipeline runs with timing
- Watch list overview
- Agent session status (from `traces/manifest.json` or Supabase)

### Phase 4: Agent Messaging
Web UI alternative to CAI messaging relay.
- Post messages to `cai_inbox` via Server Actions
- Read `notifications` table for agent responses
- Streaming responses (if agent architecture supports it)

---

## Connection Map

```
              ┌───────────────────────┐
              │      SUPABASE          │
              │  (managed Postgres)    │
              │                       │
              │  content_digests      │
              │  thesis_threads       │
              │  actions_queue        │
              │  cai_inbox            │
              │  notifications        │
              │  action_outcomes      │
              │  + 4 more tables      │
              │  + pgvector (future)  │
              │                       │
              │  PostgREST (auto API) │
              │  Realtime (WebSocket) │
              └──────┬──────┬─────────┘
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
└─────────────────┘          │  SSG digests      │
          │                  │    → JSON files    │
          │  git push        └──────────────────┘
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
