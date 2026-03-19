# Checkpoint
*Written: 2026-03-18 ~afternoon*

## Current Task
Evolving digest.wiki into "WebFront" — the primary web interaction layer for AI CoS. Architecture decisions complete, documentation done, ready to begin Supabase migration and Phase 1 (action triage) build.

## Progress
- [x] Mapped full content agent → Postgres → digest.wiki data flow
- [x] Named the web frontend "WebFront", defined terminology (WebFront + CAI = primary surfaces)
- [x] Decided: managed Postgres (not self-hosted, not dual-DB)
- [x] Researched Apache AGE — dead on all managed Postgres. Graph = separate service (Neo4j/Graphiti).
- [x] Deep comparison: Neon vs Supabase, scoped to AI CoS use case
- [x] Key finding: agent heartbeat (60s) negates Neon scale-to-zero
- [x] Decision: **Supabase** confirmed as managed Postgres provider
- [x] Feature roadmap: Action triage → Thesis interaction → Pipeline status → Agent messaging
- [x] Rendering strategy: Hybrid SSG (digest pages) + dynamic server components (interactive features)
- [x] Created `docs/source-of-truth/WEBFRONT.md` (new canonical reference)
- [x] Created `docs/superpowers/brainstorms/2026-03-18-webfront-architecture-decisions.md`
- [x] Created `docs/superpowers/brainstorms/2026-03-18-managed-postgres-and-irgi-decisions.md`
- [x] Updated 6 source-of-truth docs — all reflect Supabase, all dated 2026-03-18
- [x] TRACES.md updated with Iteration 17 (needs Neon→Supabase fix)
- [x] Fix TRACES.md Iteration 17 to say Supabase not Neon
- [ ] Exhaustive code review on the repo (carried from prior checkpoint)
- [ ] Address code review findings
- [ ] Milestone 3 compaction (iterations 1-3 → archive, overdue)
- [ ] Merge feat/three-agent-architecture → main
- [ ] Supabase project creation + Postgres migration
- [ ] Update DATABASE_URL on droplet + Vercel
- [ ] Verify agent pipeline works against Supabase
- [ ] WebFront Phase 1: Action triage build

## Key Decisions (not yet persisted)
- TRACES.md Iteration 17 still says "Neon" — needs updating to "Supabase" (decision changed mid-session after deeper research)
- Design principle #1 changed from "WhatsApp-first" to "WebFront + CAI are the primary surfaces" (already in VISION-AND-DIRECTION.md)
- IRGI compatibility verified: no phase blocked by Supabase. Already documented in brainstorm doc.

## Next Steps
1. **Exhaustive code review** on the repo (carried from prior session, not started)
2. **Milestone 3 compaction** — iterations 1-3 → `traces/archive/milestone-3.md` (overdue since iteration 3)
3. **Merge branch** — `feat/three-agent-architecture` → `main` (after review + compaction)
4. **Create Supabase project** — sign up, provision Postgres
5. **Migrate Postgres**: `pg_dump` from droplet → import to Supabase. Enable pgvector.
6. **Update DATABASE_URL**: droplet `.env` + Vercel env vars
7. **Verify agent pipeline**: restart orchestrator, confirm pipeline works against Supabase
8. **Connect WebFront**: install `@supabase/ssr`, configure server component queries
9. **Build Phase 1**: Action triage on WebFront

## Context
- Session name: "webfront build out start"
- Branch: `feat/three-agent-architecture`
- IRGI docs: `/Users/Aakash/Claude Projects/Documents/Intelligent Retrieval and Graphing Infrastructure/docs/` (4 files, brainstorming not finality)
- aicos-digests: separate git repo at `aicos-digests/`, 17 digest JSONs in `src/data/`
- Droplet Postgres: 10 tables (see DATA-ARCHITECTURE.md), agents use `psql $DATABASE_URL`
- Digest site: Next.js SSG, no runtime DB, JSON files baked at build time
- Cross-sync inbox: 1 unread about droplet RAM upgrade (1GB→4GB for Chrome/Playwright) — not acted on
- Source-of-truth now has 11 files (WEBFRONT.md added this session)
