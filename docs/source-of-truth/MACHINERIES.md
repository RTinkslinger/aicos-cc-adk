# Machineries, Loops & Armies — Build Protocol
*Source of truth for the army-of-agents build approach*

## Philosophy

The AI CoS system is built using **parallel iteration machines** — each machine runs a BUILD→TEST→REVIEW→FIX loop with armies of agents at each step. Multiple machines run simultaneously on intertwined fronts. Each machine is autonomous: it loops until its quality target is met. Machines feed each other: better data → better intelligence → better WebFront → reveals data gaps → fills them → repeat.

## How to Restart

**In a new session, say:** "Resume machineries" or "Restart all machines"

Claude should:
1. Read `CHECKPOINT.md` for current state of each machine
2. Read this file (`MACHINERIES.md`) for the approach
3. For each machine, check what loop iteration it was on
4. Launch the next step of each machine's loop — all in parallel
5. Use armies of agents (parallel subagents) for each step
6. Report progress, keep looping until targets are met

---

## Machine 1: WebFront BUILD→TEST→REVIEW→FIX

**Goal:** World-class app UX (target: 9+/10 on UX + Aakash reviews)
**Current state:** I2 complete, deployed to digest.wiki. Reviews: QA PASS, UX 6.8/10, Aakash 6.5/10.

### Loop Pattern
```
1. BUILD: Launch 3-6 parallel agents, each owns non-overlapping files
   - Split by page/feature: actions, thesis, portfolio, companies, network, home, search
   - Each agent reads design specs before building
   - Each agent commits on feature branch

2. TEST: Launch QA agent
   - Build verification (npm run build must pass)
   - Agent conflict check (duplicate functions, clashing types)
   - Accessibility audit (focus, contrast, touch targets)
   - Smoke test key routes

3. REVIEW: Launch 3 parallel review agents
   - QA Agent: code quality, accessibility, performance
   - UX Reviewer: 8-category scoring (info arch, decision support, density, interaction, visual, mobile, intelligence, completeness)
   - Think-Like-Aakash Agent: 5 scenario scoring (morning check-in, pre-meeting, post-meeting, weekly review, bucket routing)

4. FIX: Parse all findings → launch parallel fix agents (one per issue category)
   - Zero file overlap between fix agents
   - Fix build errors first, then high→medium→low

5. REPEAT: Until UX + Aakash scores reach 8+/10
```

### Design Specs (agents must read these)
- `docs/research/2026-03-20-webfront-product-design.md` — 5 major flows, wireframes, interaction specs
- `docs/research/2026-03-20-shadcn-component-composition.md` — 59 components mapped, code snippets
- `docs/research/2026-03-20-search-ux-design.md` — Search UX, entity details, graph spec
- `investment-action-triage-ux-patterns.md` — Parallel deep research on UX patterns
- `docs/superpowers/plans/2026-03-20-next-iterations-plan.md` — Prioritized P0/P1/P2 backlog

### Strategic P0 Features (not yet built)
- Outcome rating (action_outcomes writes — THE compounding mechanism)
- People/Network view with "People You Should Meet" recommendations
- List mode with batch operations (for 20+ action days)
- Supabase Realtime for live action updates

---

## Machine 2: Data AUDIT→FILL→LINK→VERIFY

**Goal:** Complete, connected intelligence database (<5% gaps on critical columns)
**Current state:** 8,650 rows. All Notion data loaded. Embeddings processing. Enrichment loops ran 3+ times.

### Loop Pattern
```
1. AUDIT: Full column-by-column gap analysis across all tables
   - Row counts, fill rates per column, relation completeness
   - Embedding coverage, cross-reference integrity (orphan detection)
   - Compare Postgres vs Notion export for missed data

2. FILL: From existing data sources first, then external
   - Notion exports: sql/data/*-full-export.json (4,635 companies, 3,339 network)
   - Research files: sql/data/research-founders-registry.json (334 founders)
   - Founder mapping: sql/data/founder-network-mapping.json (291 founders, 268 LinkedIn)
   - Page content: companies-pages/, network-pages/, portfolio-pages/
   - For unfillable gaps → Parallel batch (website URLs, LinkedIn, sector classification)

3. LINK: Cross-table connections
   - Network ↔ Companies (current_company_ids, current_people_ids)
   - Portfolio ↔ Network (led_by_ids)
   - Companies ↔ Portfolio (portfolio_notion_ids)
   - Actions ↔ Thesis (thesis_connection scoring)
   - Split by alphabet range for parallelism (A-D, E-I, J-O, P-S, T-Z, 0-9)

4. VERIFY: Re-audit, compare deltas, confirm improvements
   - Refresh action_scores materialized view
   - Queue new embeddings for any missing rows
   - Report gaps that are genuinely unfillable (schools, VCs, etc.)

5. REPEAT: Until audit shows <5% gaps on critical columns
```

### Parallelism Strategy
- **6 alphabet-range agents** for linking (zero overlap)
- **3 column-fill agents** (one per table)
- **3 gap-filler agents** (website, LinkedIn, sector via Parallel)
- **1 master data loop agent** (coordinates, re-audits, loops)

### Key Data Files
- `sql/data/live-schema-reference.md` — exact column names/types (CRITICAL for schema safety)
- `sql/data/companies-full-export.json` — 4,635 entries, 37MB (raw Notion API)
- `sql/data/network-full-export.json` — 3,339 entries, 23MB
- `sql/data/portfolio-notion-export.json` — 142 entries
- `sql/data/research-founders-registry.json` — 334 founders from research files
- `sql/data/founder-network-mapping.json` — 291 founders with LinkedIn URLs
- `sql/data/notion_paginator.py` — reusable Notion API pagination script
- `.env.local` — NOTION_TOKEN (gitignored, read by scripts)

### Schema Safety Rules (MANDATORY)
- Network: `person_name` NOT `name`, `role_title` (renamed from current_role)
- Relations: TEXT[] arrays of Notion page UUIDs
- UPSERT: ON CONFLICT (notion_page_id) DO UPDATE
- New entries without notion_page_id: plain INSERT
- Always read `sql/data/live-schema-reference.md` before any DB write

---

## Machine 3: Search + Entity DESIGN→BUILD→TEST

**Goal:** Best-in-class search across 8,650+ entities with rich detail views
**Current state:** ⌘K enhanced, /companies, /network, /search pages built. Design spec written (1,464 lines).

### Loop Pattern
```
1. DESIGN: Research + spec (already done: search-ux-design.md)
2. BUILD: 4 parallel agents (⌘K, company detail, person detail, search page)
3. TEST: Search-specific QA (query speed, result quality, type safety)
4. REVIEW: Test with real queries from Aakash scenarios
5. FIX: Optimize search speed, improve result ranking
6. REPEAT: Until search feels instant and results are relevant
```

### Next Steps
- pg_trgm indexes for fuzzy search (specified in design doc)
- Entity panel navigation stack (drill-through without losing context)
- shadcn Command component migration (40% code reduction)
- Entity relationship graph (v2, force-directed)

---

## Machine 4: Datum Agent (NEW — not yet started)

**Goal:** ClaudeSDKClient on droplet that processes inputs into DB entries
**Flow:** CAI message → orchestrator/lifecycle.py → Datum → process → DB → ask user for missing fields → complete entry → trigger content agent reprocessing

### Build Plan
```
1. DESIGN: Write CLAUDE.md for Datum agent (similar to ENIAC)
   - Input types: image, link, name, text
   - Processing: de-dup, data fill from existing DB + research + Parallel
   - Output: new/updated network or company entry
   - User interaction: "datum requests" for fields agent can't fill

2. BUILD (Droplet):
   - mcp-servers/agents/datum/CLAUDE.md
   - Integration in orchestrator/lifecycle.py (similar to content agent bridge)
   - Inbox pattern: cai_inbox → orchestrator → datum agent
   - @tool bridge for datum ↔ orchestrator communication

3. BUILD (WebFront):
   - New /crm tab (or /datum) — shows pending datum requests
   - User fills missing fields → writes to DB → triggers completion
   - Real-time updates (Supabase Realtime?)

4. BUILD (Intelligence loop):
   - After datum completes an entry → trigger content agent reprocessing
   - Content agent re-evaluates actions against new person/company context
   - New actions get scored, bucketed, and surfaced on WebFront

5. TEST: End-to-end: "add this person" from CAI → datum → DB → WebFront shows it
```

---

## Machine 5: Action Scoring Scrutiny (NEW — not yet started)

**Goal:** Actions are high-signal, not an overwhelming dump
**Principle:** Impact delta reranking, thoughtful scrutiny, preference store feedback

### Build Plan
```
1. AUDIT: Current action scoring (route_action_to_bucket, score_action_thesis_relevance)
   - How many actions are surfaced? (currently 92 proposed)
   - Are they actually high-impact or noise?

2. BUILD: Enhanced scoring functions on Supabase
   - Impact delta calculation (new action's marginal value over existing)
   - Duplicate/similar action detection (vector similarity)
   - Confidence threshold (only surface actions above X score)
   - Preference store feedback loop (action_outcomes → scoring calibration)
   - Time-decay (older unactioned → lower priority)

3. BUILD: Outcome rating on WebFront
   - After accepting an action, show outcome rating prompt
   - Write to action_outcomes table
   - Feed back into scoring model

4. TEST: Quality check — are top-5 actions genuinely the best?
5. REPEAT: Calibrate thresholds based on Aakash's feedback
```

---

## Machine 6: Content Reprocessing (NEW — not yet started)

**Goal:** Re-analyze existing content with full intelligence infrastructure
**Context:** 22 digests + 115 actions were generated WITHOUT IRGI (no vector search, no company data, no network context)

### Build Plan
```
1. AUDIT: Current content_digests and actions_queue — what's missing?
   - Actions without bucket routing → route them
   - Actions without thesis_connection → score them
   - Digests without company/person links → link them

2. REPROCESS: Tell Content Agent on droplet to re-run
   - Via orchestrator inbox: "reprocess all 22 digests with IRGI intelligence"
   - Content Agent uses vector search, scoring functions, company/network data
   - Produces better actions with real scores, real connections

3. VERIFY: Compare before/after
   - Are new actions more specific? Better bucketed?
   - Are thesis connections more accurate?
   - Refresh action_scores materialized view

4. ONGOING: Every new digest processed with full intelligence from day 1
```

---

## Cross-Machine Dependencies

```
Machine 2 (Data) → feeds → Machine 1 (WebFront) → intelligence views need data
Machine 2 (Data) → feeds → Machine 3 (Search) → search needs populated tables
Machine 2 (Data) → feeds → Machine 5 (Scoring) → scoring needs company/network context
Machine 4 (Datum) → feeds → Machine 2 (Data) → new entries from user input
Machine 4 (Datum) → triggers → Machine 6 (Reprocessing) → new data triggers re-analysis
Machine 5 (Scoring) → feeds → Machine 1 (WebFront) → better scores → better triage
Machine 6 (Reprocessing) → feeds → Machine 1 (WebFront) → better actions displayed
```

## Infrastructure References
- **Supabase:** project `llfkxnsfczludgigknbs`, Mumbai (ap-south-1), PG17
- **IRGI:** 6 intelligence functions, 2 Edge Functions (embed + search), pg_cron embedding pipeline
- **Notion token:** `.env.local` (Mac) + `/opt/agents/.env` (droplet)
- **Parallel MCP:** For batch enrichment (company research, LinkedIn search, sector classification)
- **WebFront:** Next.js 16, `aicos-digests/`, deploys via git push to Vercel
- **Droplet:** `ssh root@aicos-droplet`, orchestrator manages ENIAC + future Datum agent
