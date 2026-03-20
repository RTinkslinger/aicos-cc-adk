# Checkpoint
*Written: 2026-03-20 ~18:00 UTC — 68 agents, 11 machines, all complete*

## Session Summary
Largest-ever factory session: **68 agents across 11 machines**. Built the complete AI CoS agent fleet (Datum + Megamind + Cindy), deployed all to droplet, transformed intelligence quality, elevated WebFront to UX 8.5 / Aakash 8.2, built the Continuous Intelligence Refresh nervous system, and designed the Obligations Intelligence EA layer.

## The Agent Fleet (Definitive Framing)

| Agent | Role | CLAUDE.md | Status |
|-------|------|-----------|--------|
| **Orchestrator** | Manages all agents, heartbeat, routing | existing | LIVE on droplet |
| **Content Agent** | Pipeline: extraction → analysis → scoring → publishing | existing | LIVE on droplet |
| **Datum** | Data+ops: dedup, enrich, keep everything fresh | 639 lines | LIVE on droplet |
| **Megamind** | Co-strategist: ROI, depth grading, cascade re-ranking | 970 lines | LIVE on droplet (3 column blockers) |
| **Cindy** | Intelligent EA: email, WhatsApp, Granola, calendar, obligations | 838 lines | LIVE on droplet (needs surface setup) |

**System flow:** Orchestrator → Datum + ENIAC + Cindy → Actions/Tasks → Megamind ↔ Aakash

**Key principles:**
- ENIAC = best-in-class research analyst (content+thesis → actions)
- Datum = data & ops team (keeps everything fresh, feeds all agents)
- Cindy = most intelligent EA on planet (comms, obligations, who-owes-what)
- Megamind = co-strategist (NOT slave — equal partner, co-orchestrates with Aakash)
- Each agent self-improves via preference stores

---

## Database State (Supabase llfkxnsfczludgigknbs, Mumbai)

### Tables (30+)
| Table | Rows | Embeddings | Key State |
|-------|------|-----------|-----------|
| companies | 4,565 | 100% | 0 duplicates, 526 page_content_path |
| network | 3,722 | 100% | current_role STILL 'postgres' (column name collision, needs RENAME) |
| portfolio | 142 | 100% | 100% cross-ref, 100% research linked |
| actions_queue | 115 | 100% | 100% scored, scoring_factors 115/115, user_priority_score populated |
| thesis_threads | 8 | 100% | 77 latent connections, 3 bias-flagged |
| content_digests | 22 | 100% | All published |
| datum_requests | 0 | — | Empty, ready for Datum Agent |
| interactions | 0 | — | Empty, ready for Cindy |
| context_gaps | 0 | — | Empty, ready for Cindy |
| people_interactions | 0 | — | Empty, ready for Cindy |
| obligations | 0 | — | Empty, ready for Cindy obligation detection |
| depth_grades | 0 | — | Empty, ready for Megamind |
| cascade_events | 0 | — | Empty, ready for Megamind |
| strategic_assessments | 0 | — | Empty, ready for Megamind |
| strategic_config | 12 rows | — | Seeded with defaults (trust=manual, decay=0.7, budget=$10/day) |
| cir_propagation_rules | 7 rows | — | Seeded (content, thesis, actions, outcomes, interactions, network, companies) |
| entity_connections | 0 | — | Empty, CIR will populate |
| preference_weight_adjustments | 0 | — | Empty, preference learning will populate |
| cir_state | 0 | — | Empty |
| cir_propagation_log | 0 | — | Empty, triggers armed |
| action_outcomes | 4 | — | 4 entries, all 'proposed' |

### Live Systems on Supabase
- **IRGI**: 8 intelligence functions (hybrid_search incl. network, find_related_companies vector-enabled, score_action_thesis_relevance, route_action_to_bucket, suggest_actions_for_thesis, aggregate_thesis_evidence, detect_thesis_bias, compute_user_priority_score)
- **CIR**: 7 triggers on key tables → pgmq `cir_queue` → pg_cron processor (1 min). Preference learning function `update_preference_from_outcome()` live.
- **Auto Embeddings**: triggers → pgmq `embedding_jobs` → pg_cron → Edge Function → Voyage AI
- **Views**: `user_triage_queue` (83 user actions), `agent_work_queue` (8 agent actions), `action_scores` (matview), `interactions_public`, `obligations_with_staleness`
- **pg_cron jobs**: embed processor (10s), CIR queue (1min), connection decay (daily 21:30 UTC), matview refresh (15min), staleness check (hourly)

### Scoring State
- Portfolio: 47.3% of actions (was 14%)
- Network: 26.4% (was 11%)
- Thesis: 2.2% (was 55%)
- User queue: 83 actions / Agent queue: 8 actions
- Score range: 1.29-9.79 with 29 distinct values (was all 10.00)
- IRGI relevance: 0.40-0.89 range, independent (r=-0.323 vs user_priority)

### CRITICAL BUG: network.current_role
ALL 3,722 rows have `current_role = 'postgres'`. This is a PostgreSQL reserved identifier collision — `current_role` resolves to the system function. The M9 emergency fix agent attempted recovery from Notion export but the column name itself is the problem. **FIX: Rename column to `role_title` or `job_title`.**

---

## WebFront State (digest.wiki)

### Scores
| Dimension | Score | Journey |
|-----------|-------|---------|
| UX | 8.5/10 | 6.8 → 7.1 → 8.0 → 8.2 → 8.5 |
| Aakash | 8.2/10 | 6.5 → 6.8 → 7.5 → 7.5 → 8.2 |
| QA | PASS | All loops |

### What's Deployed
- Design elevation: 40% tighter spacing, neutral backgrounds, desaturated accents, 3-tier text hierarchy
- Portfolio-first: Deepen Existing bucket first, Thesis Evolution last + auto-collapsed
- PREP buttons: one-tap company brief from any surface
- Portfolio above fold on mobile home
- Scoring integration: `user_triage_queue`, `user_priority_score` sort
- Agent Tasks summary section (collapsed, shows count)
- P0 features: keyboard help, hint bar, batch selection, outcome rating, sort headers
- Add Signal FAB, Since Last Visit, P0 Banner
- Bias warnings on thesis pages (amber 5:1, flame zero-contra)
- IRGI relevance badges on action→thesis connections
- Intelligence quality indicator on home page
- PWA manifest + service worker

### What's NOT Built Yet on WebFront
- Cindy Alerts section (/cindy or /comms) — obligations dashboard, follow-up feed, insights
- Megamind section (/strategy) — strategic overview, depth queue, cascade feed, convergence meter
- Depth grading UI — Skip/Scan/Investigate/Ultra approval interface
- Network page real roles (blocked by column rename)
- Geist font migration (next/font instead of CSS @import)
- Service worker offline caching
- Supabase Realtime subscriptions

---

## 8 Permanent Machineries (run every session, 30+ loops target)

### Machine 1: WebFront — Continuous UX Evolution
**Loop count:** 12 phases (5 builds, 7 reviews)
**Current state:** UX 8.5, Aakash 8.2. DEPLOYED.
**Next loops:**
- Loop 6: Build Cindy Alerts section (/comms) — obligations dashboard, follow-up feed
- Loop 7: Build Megamind section (/strategy) — depth queue, cascade feed
- Loop 8: Depth grading UI (Skip/Scan/Investigate/Ultra)
- Loop 9: Geist font + service worker + Realtime subscriptions
- Loop 10+: Continuous refinement toward 9+/10
**Key files:** `aicos-digests/src/` (entire Next.js app)
**Design specs:** `docs/research/2026-03-20-ux-elevation-study.md`, `docs/research/2026-03-20-search-ux-design.md`
**Review reports:** `aicos-digests/docs/iterations/001-008-*.md`

### Machine 5: Scoring — Continuous Intelligence Optimization
**Loop count:** 6 (AUDIT, FIX, VERIFY, FIX2, FINAL, FIX3)
**Current state:** PRODUCTION READY. Portfolio 47%, 29 distinct scores, preference learning live.
**Next loops:**
- Loop 7: Incorporate IRGI relevance into compute_user_priority_score (currently ignored)
- Loop 8: Integrate scoring_factors multi-factor model into the priority function
- Loop 9: Tune preference learning weights after user feedback accumulates
- Loop 10+: Continuous calibration
**Key files:** `sql/scoring-improvements.sql`, `sql/irgi-scoring-fixes.sql`, `sql/actions-intelligence-fixes.sql`
**Audit reports:** `docs/audits/2026-03-20-scoring-*.md` (6 reports)

### Machine 7: Megamind — Continuous Strategic Capability
**Loop count:** 4 (DESIGN, BUILD, REVIEW+INTEGRATE, E2E TEST)
**Current state:** DEPLOYED to droplet. E2E 5/5 pass. **3 column blockers before autonomous operation.**
**Blockers (fix in Loop 5):**
1. CLAUDE.md references `action_text` → should be `action`
2. CLAUDE.md assumes thesis_connection is ARRAY → it's pipe-delimited TEXT
3. `strategic_score` column doesn't exist on actions_queue → needs ALTER TABLE
**Next loops:**
- Loop 5: Fix 3 column blockers + redeploy
- Loop 6: Send test strategic assessment via orchestrator inbox
- Loop 7: Verify cascade re-ranking with real data
- Loop 8: Tune convergence parameters based on actual cascade behavior
- Loop 10+: Continuous strategic capability refinement
**Key files:** `mcp-servers/agents/megamind/CLAUDE.md` (970L), `skills/megamind/` (3 files, 827L), `sql/megamind-migrations.sql`
**Design spec:** `docs/superpowers/specs/2026-03-20-megamind-design.md`
**Lifecycle plan:** `docs/superpowers/plans/2026-03-20-megamind-lifecycle-integration.md`

### Machine 8: Cindy — Continuous Comms Capability
**Loop count:** 4 (RESEARCH x4, DESIGN, BUILD, VERIFY+SETUP)
**Current state:** DEPLOYED to droplet (lifecycle integrated). **Needs surface setup before processing real data.**
**Setup needed (user actions):**
1. **AgentMail** ($20/mo): Create account at agentmail.to, set up domain (agent.3niac.com or agent.aicos.ai), create cindy inbox
2. **Google/M365 Calendar**: Confirm primary calendar. Create API credentials.
3. **WhatsApp**: Backup dir EXISTS at `~/Library/Mobile Documents/57T9237FN3~net~whatsapp~WhatsApp/`
4. **Granola**: MCP tools already connected. Verify they work from droplet.
**Build needed (our work):**
- Email: WebSocket listener on droplet, email processing pipeline (~3-4h)
- Calendar: syncToken polling script, .ics parsing (~5-6h)
- WhatsApp: Extraction script + daily 3AM cron (~5-6h)
- Granola: Polling script or direct MCP query (~30min-3h)
- Missing trigger: `interactions` table needs `queue_embeddings` trigger for Auto Embeddings
**Key files:** `mcp-servers/agents/cindy/CLAUDE.md` (838L), `skills/cindy/` (5 files incl. obligation-detection), `sql/cindy-migrations.sql`
**Design spec:** `docs/superpowers/specs/2026-03-20-cindy-design.md` (2,290L)
**Research:** `docs/research/2026-03-20-cindy-email-infrastructure.md`, `cindy-whatsapp-research.md`, `cindy-calendar-granola-research.md`
**Setup assessment:** `docs/audits/2026-03-20-cindy-setup-assessment-m8-loop4.md`

### Machine 9: Intelligence QA — Continuous Accuracy Auditing
**Loop count:** 3 (AUDIT x4, FIX x2, RE-AUDIT)
**Current scores:** Actions 7.0, Thesis 7.8, Portfolio/Network 65, Search 78
**Next loops:**
- Loop 4: Fix network current_role (rename column), re-audit Portfolio/Network (target 80+)
- Loop 5: Integrate scoring_factors into IRGI score, re-audit Actions (target 8+)
- Loop 6: After Cindy processes real data, audit interaction quality
- Loop 10+: Continuous accuracy auditing of ALL intelligence output
**Key files:** `docs/audits/2026-03-20-intelligence-quality-*.md` (4 audit reports + 2 fix reports + 1 reaudit)
**Important:** M9 feeds findings to M5 (scoring), M6 (IRGI), M1 (WebFront), M4 (Datum). It's the quality enforcement loop.

### Machine 10: CIR — Continuous Intelligence Refresh
**Loop count:** 2 (DESIGN, BUILD)
**Current state:** LIVE on Supabase. 7 triggers armed, pgmq queue, 4 pg_cron jobs, preference learning function.
**Next loops:**
- Loop 3: Verify triggers fire correctly on real writes (test with an action outcome rating)
- Loop 4: Build entity_connections seeder (populate initial connections from vector similarity)
- Loop 5: Build the mechanical propagation functions (rescore_related_actions, update_thesis_indicators, etc.)
- Loop 6: Test preference learning end-to-end
- Loop 10+: Tune decay rates, add ML when 500+ outcomes exist
**Key files:** `sql/cir-build.sql`, `docs/superpowers/specs/2026-03-20-living-system-architecture.md`

### Machine 11: Obligations — Continuous EA Capability
**Loop count:** 2 (DESIGN, BUILD)
**Current state:** Schema on Supabase. Cindy CLAUDE.md updated with detection protocol. Skill created.
**Next loops:**
- Loop 3: Build WebFront /comms obligations dashboard (You Owe / They Owe views)
- Loop 4: Build Megamind priority overlay (strategic_priority on obligations)
- Loop 5: Test obligation detection end-to-end (send an email, verify Cindy creates obligation)
- Loop 6: Auto-fulfillment detection (new email resolves prior obligation)
- Loop 10+: Continuous refinement of detection patterns + priority blend
**Key files:** `sql/obligations-build.sql`, `skills/cindy/obligation-detection.md`, `docs/superpowers/specs/2026-03-20-obligations-intelligence-design.md`

### Machine 6: IRGI — Continuous IRGI Optimization
**Loop count:** 5 (ASSESS, FIX, VERIFY, FIX2, FINAL)
**Current state:** PRODUCTION READY. 100% coverage, 8 functions, bias detection.
**Next loops:**
- Loop 6: Enrich company embedding inputs from page_content_path (thin embeddings cause poor similarity)
- Loop 7: Re-embed companies after enrichment, verify similarity improves
- Loop 8: Add network to more intelligence functions
- Loop 10+: Continuous function refinement
**Key files:** `sql/irgi-phase-a.sql`, `sql/irgi-scoring-fixes.sql`, `sql/search-intelligence-fixes.sql`

---

## Non-Permanent Machines (concluded or at milestone)

### Machine 2: Data Quality — CONCLUDED (Datum takes over)
4 loops. 100% embeddings, 0 duplicates, 99.3% cross-ref. Datum Agent handles ongoing data quality.

### Machine 3: Search + Entity — MERGED into M1
Search pages built as part of WebFront. Cmd+K, /companies, /network, /search all deployed.

### Machine 4: Datum Agent — CONCLUDED (deployed, Datum is live)
5 loops. CLAUDE.md 639L, lifecycle.py integrated, deployed to droplet. Datum is operational — receives datum_* messages from orchestrator.

---

## Infrastructure State

### Droplet (aicos-droplet)
- 3 systemd services: state-mcp (8000), web-tools-mcp (8001), orchestrator
- Orchestrator manages: Content Agent + Datum Agent + Megamind + Cindy
- All healthy as of last deploy
- Deploy via: `cd mcp-servers/agents && bash deploy.sh`
- Live monitoring: `live-orc.sh`, `live-content.sh`, `live-datum.sh`, `live-megamind.sh`, `live-cindy.sh`

### Vercel (digest.wiki)
- Auto-deploys on `git push origin main` to aicos-digests repo
- Latest: UX 8.5, Aakash 8.2, QA PASS
- Env vars: NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY, SUPABASE_SECRET_KEY

### Git Repos
- Main: `RTinkslinger/aicos-cc-adk` — pushed, up to date
- Digests: `RTinkslinger/aicos-digests` — pushed, deployed

---

## Session Statistics
- **68 agents spawned**, all completed
- **11 machines** run (8 permanent + 3 concluded)
- **~35,000 lines** of code, specs, SQL, audits produced
- **4 agent CLAUDE.md files** written (Datum 639L + Megamind 970L + Cindy 838L = 2,447L)
- **5 design specs** (Datum, Megamind, Cindy 2,290L, CIR 1,378L, Obligations 1,850L = ~8,500L)
- **28 audit reports** in docs/audits/
- **12 SQL migration files** executed on Supabase
- **8 iteration review reports** for WebFront

## Resume Command
To restart all permanent machineries:
> "Resume machineries" → read CHECKPOINT.md → restart all 8 permanent machines with armies of agents
