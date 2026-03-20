# Checkpoint
*Written: 2026-03-20 ~11:00 UTC*

## Session Summary
Largest agent session ever: **87+ agents spawned across 20 workstreams**. Three iteration machines ran simultaneously: WebFront BUILD→TEST→FIX, Data AUDIT→FILL→LINK→VERIFY, and Search DESIGN→BUILD→TEST.

## What Was Accomplished

### Database (Supabase — llfkxnsfczludgigknbs, Mumbai)
- **4,635 companies** (full Notion DB via API pagination)
- **3,728 network** (3,326 from Notion + 402 enrichment-created founders)
- **142 portfolio** (100% research linked, 100% embedded)
- **22 content_digests + 8 thesis_threads + 115 actions_queue** (pre-existing)
- **Total: 8,650 rows**
- **Embeddings:** All 1,597 existing rows embedded. 6,804 queued for new rows (pg_cron processing autonomously every 10s)

### IRGI (fully live on Supabase)
- pgvector 0.8.0, pgmq 1.5.1, pg_cron 1.6.4, pg_net 0.20.0
- 6 tables with vector(1024) columns + HNSW indexes
- 6 tables with FTS tsvector columns + GIN indexes
- `hybrid_search()` — cross-table RRF-based semantic + keyword search
- `score_action_thesis_relevance()`, `route_action_to_bucket()`, `find_related_companies()`
- `aggregate_thesis_evidence()`, `suggest_actions_for_thesis()`
- `entity_relationships` view (929 connections), `action_scores` materialized view
- Edge Functions: `embed` (ACTIVE, no JWT) + `search` (ACTIVE, JWT)
- Vault: `project_url` + `VOYAGE_API_KEY` stored
- Auto-embedding triggers on all 6 tables → pgmq queue → pg_cron → Edge Function → Voyage AI

### Research Files
- **252 MD files** in `portfolio-research/` (141 batch 1 + 108 batch 2 + 3 pre-existing)
- **142/142 portfolio** companies have `research_file_path` linked
- **21 companies** have `research_file_path` linked
- **334 founders** extracted from research files (68 matched to network, 266 identified as new)

### Page Content (Notion page bodies → MD files)
- `companies-pages/`: ~300+ files (A-F: 153, G-N: done, O-Z: in progress)
- `network-pages/`: 531 files (A-H: 250, I-P: 120, Q-Z: 174)
- `portfolio-pages/`: 142 stubs (20 populated via MCP, rest via API batch)
- `page_content_path` column added to portfolio, network, companies tables

### Enrichment State
- 6 alphabet enrichment agents ran (A-D ✅, E-I ✅, J-O ✅, P-S ✅, T-Z ⏳, 0-9 ✅)
- 197 new founders created in network (with LinkedIn as durable key)
- 291 founders discovered via Parallel LinkedIn search (268 LinkedIn URLs, 92% coverage)
- Deep enrichment orchestrator ran 3 loops (37 portfolio linked, 130 network linked, 10 companies created)
- Column fill agents audited portfolio (ZERO gaps), companies and network (in progress)
- Gap fillers launched for: website URLs, LinkedIn URLs, sector classification

### WebFront (digest.wiki — DEPLOYED)
**Branch `feat/webfront-v4` merged to main, pushed, deploying.**

Pages:
- `/` — Command center (priority actions strip, thesis momentum, portfolio health, activity feed)
- `/actions` + `/actions/[id]` — Bucket-grouped + keyboard shortcuts + intelligence RPC + sheet/drawer detail
- `/thesis` + `/thesis/[id]` — Evidence timeline + bull/bear + suggestions + related companies
- `/portfolio` + `/portfolio/[id]` — Health badges + founders + thesis + research + company brief
- `/companies` + `/companies/[id]` — Full linkages (people, thesis, actions, research)
- `/network` + `/network/[id]` — Career history, portfolio connections, activity
- `/search` — Tabbed full search results
- `/d/[slug]` — 22 SSG digests
- `/api/search` + `/api/search/related` + `/api/portfolio/[id]/brief`

Features:
- Card-stack swipe triage (Tinder UX) with keyboard shortcuts
- ⌘K command palette with rich entity previews
- Bottom tab nav (mobile) + collapsible sidebar (desktop)
- PWA manifest + service worker + offline shell
- Add Signal FAB (write capability) + Sonner toasts
- Since Last Visit delta tracking + P0 Emergency Banner
- `?` keyboard help overlay
- Pull-to-refresh, safe areas, hover guards, WCAG focus indicators

Reviews (I1):
- QA: PASS (0 critical, 1 high fixed, 3 medium fixed)
- UX: 6.8/10
- Aakash: 6.5/10 (write capability was #1 gap — now addressed)

### Notion Full Exports (on disk)
- `sql/data/companies-full-export.json` — 4,635 entries, 37MB
- `sql/data/network-full-export.json` — 3,339 entries, 23MB
- `sql/data/portfolio-notion-export.json` — 142 entries
- `sql/data/companies-notion-export.json` — 545 entries (original MCP extraction)
- `sql/data/network-notion-export.json` — 529 entries (original MCP extraction)
- `sql/data/notion_paginator.py` — Reusable script for future full exports
- Notion API token: stored in `.env.local` as `NOTION_TOKEN` (gitignored) + on droplet at `/opt/agents/.env`
- API database IDs differ from MCP data_source_ids: Companies=`45a7e3ff...`, Network=`d5f52503...`

## Machineries to Restart

### Machine 1: WebFront BUILD→TEST→REVIEW→FIX Loop
**State:** I2 BUILD complete (5 fix agents done). I2 REVIEW not yet run. WS20 search/entity pages built.
**Next:** Run I2 review (QA + UX + Aakash agents) → parse findings → launch I3 fix agents → repeat until 8+/10.
**Key files:** `aicos-digests/docs/iterations/004-*.md` (QA, UX, Aakash reports)
**Design specs:** `docs/research/2026-03-20-webfront-product-design.md`, `docs/research/2026-03-20-shadcn-component-composition.md`, `docs/research/2026-03-20-search-ux-design.md`
**Strategic backlog:** `docs/superpowers/plans/2026-03-20-next-iterations-plan.md`

### Machine 2: Data AUDIT→FILL→LINK→VERIFY Loop
**State:** Mass upserts DONE (4,635 companies + 3,728 network). Embeddings processing (6,804 queued). Column fill agents ran for portfolio (ZERO gaps). Companies + network column fill in progress.
**Next:** Re-run full audit. Fill gaps from Notion exports. Run Parallel batch for website/LinkedIn/sector gaps. Verify cross-references. Loop until <5% gaps.
**Key data:** `sql/data/` (all exports), `sql/data/live-schema-reference.md`, `sql/data/research-founders-registry.json`, `sql/data/founder-network-mapping.json`
**Enrichment reports:** `docs/audits/2026-03-20-enrichment-completion.md`, `docs/audits/2026-03-20-data-quality-validation.md`

### Machine 3: Search + Entity DESIGN→BUILD→TEST Loop
**State:** WS20 design spec written. ⌘K enhanced, /companies, /network, /search pages built and deployed.
**Next:** Search-specific QA + UX review. Optimize search speed. Add entity relationship graph. Test with real queries.

### Machine 4: Datum Agent (NOT STARTED)
**Spec from user:** New ClaudeSDKClient agent on droplet. Input: image/link/name/text from CAI → processes to create de-duped, fully data-filled network or company entries. Asks user for fields it can't fill (via "datum requests" tab on WebFront). Flow: CAI message → orchestrator → Datum → process → add to DB → ask user for missing fields → complete entry → trigger content agent reprocessing.
**Needs:** CLAUDE.md for Datum agent, lifecycle.py integration, WebFront CRM tab, inbox system for user requests.

### Machine 5: Action Scoring Scrutiny (NOT STARTED)
**Spec from user:** Actions must not become an overwhelming dump. System needs: impact delta reranking, thoughtful scrutiny, high-impact/high-connection/high-relevance filtering, preference store feedback loop, deep selection when suggesting. Current `route_action_to_bucket()` and `score_action_thesis_relevance()` are v1 — need iteration.

### Machine 6: Content Reprocessing (NOT STARTED)
**Spec:** Existing 22 digests + 115 actions were generated WITHOUT intelligence infra. Need reprocessing through IRGI (vector search, scoring functions, bucket routing). Content Agent on droplet needs to re-analyze with full company/network/thesis context.

## Infrastructure Notes
- Supabase connection pool: MEDIUM compute (4GB), hits capacity with 15+ parallel agents. Stagger heavy DB agents.
- Voyage AI: VOYAGE_API_KEY set in both Vault and Edge Function secrets. Cost: ~$0.02/month at current scale.
- Notion API: Integration token on droplet. Page IDs ≠ MCP data_source_ids.
- aicos-digests Vercel CLI: v50.33.1, authenticated, linked.

## Files Created This Session
- `sql/irgi-phase-a.sql` (1004 lines, executed)
- `sql/irgi-edge-function.ts` (253 lines)
- `sql/companies-network-migration.sql` (executed)
- `sql/portfolio-migration.sql` (executed)
- `sql/data/` — 15+ data files (exports, registries, matching data)
- `supabase/functions/embed/index.ts` + `supabase/functions/search/index.ts` (deployed)
- `supabase/deploy-functions.sh`
- `docs/audits/` — 12+ audit reports
- `docs/research/` — 4 research/design docs
- `docs/superpowers/plans/` — 2 plan files
- `portfolio-research/` — 252 MD files
- `companies-pages/` — 300+ MD files
- `network-pages/` — 531 MD files
- `portfolio-pages/` — 142 stubs

## TRACES.md
Iteration 28 logged. Compaction overdue (massive session).
