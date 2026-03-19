# WebFront Architecture Decisions
*2026-03-18 — Think-through session*
*CC Session: "webfront build out start" (2026-03-18, search QMD: `webfront neon digest.wiki`)*

How we arrived at the architecture for evolving digest.wiki from a static read-only site into the primary web interaction layer for AI CoS.

---

## Starting Point

**Objective:** digest.wiki is currently a static SSG site that displays content digests. It needs to evolve into a persistent, real-time interaction layer — the "WebFront" — where Aakash interacts with AI CoS agents and data beyond just reading digests.

**Current state:**
- Next.js SSG on Vercel, flat JSON files baked at build time
- Content Agent on droplet writes JSON → git push → Vercel rebuild
- No runtime DB connection, no user interaction
- Only interaction with agents: CAI messaging relay (Claude.ai → State MCP → cai_inbox → Orchestrator → Content Agent)

---

## Decision 1: What interactions to build first?

**Options considered:**
1. Action triage (accept/dismiss proposed actions from digest pages)
2. Agent messaging (web UI for talking to Content Agent)
3. Live pipeline status (what's queued/processing/published)
4. Thesis interaction (view threads, evidence, conviction)

**Choice:** 1 → 4 → 3 → 2

**Reasoning:**
- **Action triage first** — highest immediate value. Actions are the output of the entire content pipeline. Being able to act on them from the WebFront closes the feedback loop (currently done in Notion, which is clunky).
- **Thesis interaction second** — viewing thesis threads with evidence trails is high-value and currently requires manual postgres-to-notion dumps.
- **Pipeline status third** — operational visibility. Currently invisible without SSH + psql.
- **Agent messaging last** — CAI relay already works. WebFront messaging is a nice-to-have, not blocking.

---

## Decision 2: How to connect the frontend to data?

**The constraint:** Postgres lives on the droplet. Vercel serverless functions can't reach it (no Tailscale on Vercel infrastructure).

**Options considered:**

| Option | Approach | Tradeoffs |
|--------|----------|-----------|
| **A. Move to Neon** | Managed Postgres on Vercel Marketplace. Agents + frontend both connect. | Clean single source of truth. Migration effort. |
| **B. Expand State MCP** | Frontend calls existing MCP server via Cloudflare Tunnel | Zero new infra. But MCP protocol isn't REST-native. Only 5 tools currently. |
| **C. Build REST API** | New HTTP service on droplet, exposed via Cloudflare Tunnel | Full control. But another service to maintain. |
| **D. Hybrid SSG + API** | Digests stay JSON/SSG. Interactive features call droplet API (B or C) | Incremental. But two data paths, potential staleness. |

**Follow-up question:** Keep Postgres on droplet (option B/C) or move to Neon (option A)?

User leaned toward keeping on droplet but wanted "whatever is more scalable."

**Scalability analysis:**
- For a single-user system, load isn't the concern — resilience and architectural separation are.
- Option 3 (Neon + droplet copy) was considered as "most robust" → rejected because two databases means building a replication layer, introducing distributed consistency problems for zero benefit.
- Agent latency to Neon: ~5-20ms/query × 30 queries = ~500ms per analysis. Claude API calls take 5-30s. DB latency is noise.

**Choice:** Option A — Neon only.

**Reasoning:**
- Simplest architecture that scales
- One `DATABASE_URL` everywhere (agents + frontend)
- No API layer needed for reads (server components query Neon directly)
- Server Actions for writes
- Droplet becomes pure compute, not a data store
- Managed backups, recovery, branching come free
- Migration is mechanical: `pg_dump` → Neon import → update env vars

---

## Decision 3: Naming and scope

**Options:**
- `FRONTEND-ARCHITECTURE.md` — just the web frontend
- `INTERFACE-LAYER.md` — all interaction surfaces

**Choice:** Split terminology:
- **"WebFront"** = the web frontend (currently digest.wiki). Gets its own doc: `WEBFRONT.md`
- **"Interface Layer"** = all surfaces: WebFront + CAI + WhatsApp + Notion
- **Primary focus** = WebFront + CAI as the two main surfaces for building the AI CoS vision

---

## Architecture Summary

```
Before (current):
  Content Agent → JSON files → git push → Vercel SSG → static site
  User interaction: Notion (clunky) + CAI messaging (text only)

After (target):
  Content Agent → Neon Postgres → direct server component reads
  WebFront → Server Actions → Neon writes (action triage, thesis, messaging)
  Digest pages: still SSG from JSON (hybrid)
  Droplet: pure compute (agents + MCP servers)
  Neon: single data store for everything
```

---

## What's Next

1. **Provision Neon** via Vercel Marketplace
2. **Migrate Postgres** (pg_dump → Neon)
3. **Update DATABASE_URL** on droplet + Vercel
4. **Verify agent pipeline** works against Neon
5. **Build Phase 1** (action triage on WebFront)
