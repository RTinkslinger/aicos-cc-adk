# Checkpoint
*Written: 2026-03-20 18:30 UTC — 76 agents, 8 machines, iteration 30*
*ALL 8 MACHINES AT TARGET: 7 at loop 20, M12 at loop 10*

## Current Task
Running 8 permanent machineries (M1 WebFront, M5 Scoring, M6 IRGI, M7 Megamind, M8 Cindy, M9 Intel QA, M10 CIR, M12 Data Enrichment) with armies of specialized agents per loop step. All reached minimum 10 loops, 7 at loop 20.

## Progress
- [x] M12 Data Enrichment: L1-10 (column rename, roles, dedup, connections 19,421, embeddings 100%, page content 9.2%/7.6%)
- [x] M7 Megamind: L5-20 (blockers fixed, deployed, 41 depth grades, cascade, convergence 0.28)
- [x] M5 Scoring: L7-20 (6-factor model, 4-fix migration, percentile normalization, staleness boost)
- [x] M6 IRGI: L6-20 (8 functions <200ms, FTS rebuilt, P0s fixed, 8.75/10)
- [x] M10 CIR: L3-20 (triggers, propagation, queue fixed 3,495→0, dead-letter, 8.6/10)
- [x] M9 Intel QA: L4-20 (20+ audits, quality 6.2→7.3/10)
- [x] M1+M11 WebFront: L6-20 (/comms, /strategy, depth grading, Geist, a11y, deployed 3x)
- [x] M8 Cindy: L5-20 (5 processors 4,729L Python, deployed, e2e tested, 7.5/10)
- [ ] Commit 284 uncommitted files in parent repo
- [ ] Fix M7→M5 broken feedback loop (strategic_score not read by priority function)
- [ ] M12 enrichment at scale (page_content 90.8% missing, email 0%, website 91.7%)
- [ ] M8 AgentMail API key deployment for real email processing

## Key Decisions (not yet persisted)
All decisions already persisted in CHECKPOINT.md cross-machine context section and TRACES.md iteration 30.

## Next Steps
1. `cd "/Users/Aakash/Claude Projects/Aakash AI CoS CC ADK" && git add -A && git commit -m "iteration 30: 76 agents, 8 machines at 10-20 loops"` — commit all work
2. Resume all 8 machines L21-40 with army pattern (read CROSS-MACHINE CONTEXT section below)
3. Priority fixes: M7→M5 strategic_score integration, M12 Notion page extraction, M8 AgentMail API key
4. Each machine agent gets the cross-machine context so it knows what other machines built

## Context
- Parent repo has 284 uncommitted files (243 modified + 41 new). MUST commit before next work.
- Digests repo is clean (3 pushes deployed this session).
- Supabase project `llfkxnsfczludgigknbs` (Mumbai) has 28 tables, 41 functions, 15 views, 38 triggers.
- Droplet has M7+M8 deployed, all 3 services healthy (state-mcp:8000, web-tools-mcp:8001, orchestrator with 4 agents).
- WhatsApp iCloud backup is encrypted (.enc) — uses Export Chat .txt fallback.
- Granola MCP permissions blocked from Cindy agent on droplet.

## Resume Command
> "Resume machineries" → read CHECKPOINT.md → restart ALL 8 permanent machines with armies of agents

**Pattern:** Each loop step gets specialized agents (builder + reviewer + fixer). Waves of agents, not monolithic runners. Target: loop 40 next session.

---

## CROSS-MACHINE CONTEXT (CRITICAL — feed to every machine's agents)

Every machine's agents MUST know what the other machines have built. This is the intertwined nervous system.

### What M12 (Data Enrichment) built that ALL machines use:
- `network.role_title` column (renamed from `current_role`). **ALL SQL must use `role_title` not `current_role`**
- `page_content TEXT` column on companies (422 rows, 9.2%) and network (269 rows, 7.6%)
- `entity_connections` table: **19,421 rows** across 11 pair types (company-company 6,867, network-company 5,019, network-network 2,000, company-thesis 2,000, portfolio-thesis 176, portfolio-company 142, action-thesis 138, thesis-thesis 18, network-thesis 3)
- Network deduped: 3,722→3,525 (backup in `network_dedup_backup`)
- 38 new websites (5.3%→8.3% companies with website)
- 18 portfolio↔thesis connections at 0.55 cosine threshold
- `page_content_path` populated on 526 companies, 239 network

### What M5 (Scoring) built that ALL machines use:
- `compute_user_priority_score()` function — 6-factor weighted model:
  - time_sensitivity (0.15), conviction_change (0.20), stakeholder/bucket_impact (0.20), effort_vs_impact (0.15), action_novelty (0.10), irgi_relevance (0.20)
  - LEAST(val, 1.0) clamping (not /10.0)
  - Exponential decay: `POWER(0.97, GREATEST(0, days_old - 14))` — 3%/day after 14 days
  - Acceptance signal: per-action_type accept/dismiss rate from history
  - Staleness boost: log(days_proposed+1) capped at +0.8
  - Network boost: name match → e_e_priority, vector fallback at 0.65
  - Preference learning: reads `preference_weight_adjustments` table
- `action_scores_ranked` view: within-type percentile normalization (blended_score spans 3.93-9.82)
- `action_score_breakdown` view: all 6 factors exposed for WebFront
- Score hierarchy: Portfolio (8.64) > Meeting (7.96) > Pipeline (7.71) > Research (6.94) > Thesis (6.10)
- **KNOWN GAP:** strategic_score from M7 is NOT read by priority function (broken M7→M5 feedback loop)

### What M6 (IRGI) built that ALL machines use:
- 8 intelligence functions, all <200ms:
  1. `hybrid_search(query, embedding, limit, kw_weight, sem_weight)` — cross-table FTS+vector, ghost results fixed
  2. `find_related_companies(company_id, limit)` — vector similarity
  3. `find_related_entities(company_id, limit)` — companies + network people
  4. `score_action_thesis_relevance(action_id)` — 4-method weighted scoring
  5. `route_action_to_bucket(action_id)` — portfolio/network/thesis routing with network lookup
  6. `suggest_actions_for_thesis(thesis_id)` — suggestions + network contacts
  7. `aggregate_thesis_evidence(thesis_id)` — digests+actions+outcomes+network, 117ms (was 1.4s)
  8. `detect_thesis_bias(thesis_id)` — 6-flag structured output (confirmation, possible, source, stale, mismatch, thin)
- `bias_summary` view: all theses with severity flags (3 flagged: AI-Native CRITICAL, Cybersecurity HIGH, Agentic AI HIGH)
- `bias_flags JSONB` column on thesis_threads
- `update_thesis_bias_flags()` function
- FTS generated columns rebuilt on companies+network to include `page_content`
- `embedding_input_companies()` enriched with 5 additional fields
- `entity_relationships` view with short-name false positive fix (LENGTH >= 4)
- IRGI score: **8.75/10**, search: **62/100** (needs Edge Function for embedding generation)

### What M7 (Megamind) built that ALL machines use:
- `strategic_score NUMERIC` column on actions_queue
- `depth_grades` table: 41 rows (action_id, action_text, auto_depth 1-4, reasoning, strategic_score, confidence)
- `strategic_assessments` table: 3 daily snapshots (portfolio_summary, market_conditions, recommendations JSONB)
- `cascade_events` table: 6 events with trigger/propagation
- `strategic_config` table: 12 configuration values (trust, decay, budget)
- `process_cascade_event()` trigger function — auto-propagates score deltas
- `megamind_dashboard` view: actions + depth grades + strategic scores
- `megamind_convergence` view: 15-column system health (priority distribution, depth distribution, staleness)
- Auto-grading rules: Portfolio+score>8→investigate(3), Meeting+score>7→scan(2), Research/Thesis→skip(1)
- Convergence ratio: 0.28 (23.3% graded, 21.7% resolved)
- **Deployed to droplet**, Megamind live as ClaudeSDKClient

### What M8 (Cindy) built that ALL machines use:
- `interactions` table: embedding trigger armed (AFTER INSERT/UPDATE → pgmq embedding_jobs)
- `obligations` table: 7 sample rows with urgency classification
- `obligation_dashboard` view: obligations with days_old, urgency (overdue/urgent/upcoming)
- `interaction_timeline` view: interactions with signal_richness scoring
- 5 Python processors in `mcp-servers/agents/cindy/`:
  - `email/email_processor.py` (785L) — AgentMail API client, signal extraction, obligation detection
  - `email/obligation_extractor.py` (393L) — 11 I-owe + 7 they-owe + 8 request patterns
  - `calendar/ics_processor.py` (578L) — .ics parsing, attendee resolution, pre-meeting context
  - `whatsapp/extractor.py` (982L) — Export Chat .txt parser (backup is encrypted)
  - `granola/processor.py` (1,069L) — transcript parsing, calendar matching, signal extraction
  - `obligations/obligation_detector.py` — full spec, 10 categories, priority formula
- **Deployed to droplet**, all processors pass dry-run
- **Blockers:** AgentMail inbox needs API key on droplet, Granola MCP permissions, WhatsApp backup encrypted

### What M10 (CIR) built that ALL machines use:
- 7 triggers on 6 tables (column-specific to exclude embedding updates)
- `cir_queue` pgmq queue: healthy (0 pending), processor runs every minute
- `cir_dead_letter` queue: 0 failures
- `process_cir_queue()` function: batch 100, per-message error handling, dead-letter routing
- `process_cir_queue_item(msg JSONB)` router: dispatches to propagation functions
- 4 propagation functions:
  - `rescore_related_actions(thesis_id)` — updates strategic_score from entity_connections
  - `propagate_company_change(company_id)` — ILIKE match on company name in actions
  - `propagate_network_change(person_id)` — ILIKE match on person name in assigned_to
  - `update_thesis_indicators(thesis_id)` — momentum/health computation
- `cir_state` table: 8,562 entries tracking all entities with staleness
- `staleness_monitor` view: avg staleness by entity type
- `staleness_alerts` view: entities stale > 30 days
- Connection decay: daily 0.98x factor, prune at 0.1 (~104 day TTL)
- CIR health: **8.6/10**, 97/100
- **KNOWN GAP:** queue processor logs but doesn't always call process_cir_queue_item() to route

### What M9 (Intel QA) built that ALL machines consume:
- 20+ audit reports in `docs/audits/2026-03-20-m9-*.md`
- Final quality score: **7.3/10** (from 6.2 at session start)
- **3 critical findings still open:**
  1. Score compression: 60% in bucket 8 (target <30%). Partially addressed by M5 percentile normalization view.
  2. M7→M5 broken feedback loop: strategic_score written but never read by compute_user_priority_score
  3. M12 enrichment gaps: page_content 9.2%/7.6%, email 0%, website 8.3%
- Infrastructure audit: 15 tables, 41 functions, 13 views, 136 indexes, 43 triggers

### What M1 (WebFront) built that all machines should know:
- `/comms` page (608L): Cindy Communications Intelligence, You Owe / They Owe columns, interaction timeline
- `/strategy` page (826L): Megamind Strategic Command Center, convergence meter, cascade feed, depth queue
- `DepthGradingClient.tsx`: interactive Skip/Scan/Investigate/Ultra with Server Action → depth_grades table
- Geist fonts via next/font (zero CLS), service worker v2
- Strategy in mobile BottomNav, contrast fixed (#8a8894), loading grid responsive
- Improved empty states with illustrations + CTAs
- `src/lib/utils/time.ts` shared timeAgo utility
- Deployed 3x to digest.wiki, all builds pass
- UX: 7.0-7.5/10

---

## Per-Machine State & Next Loops

### M12: Data Enrichment | Loop 10 ✅ | Next: L11-30
**What's done:** Column rename, roles, dedup, connections, embeddings, page content loaded, websites enriched
**What's not done:**
- 4,143 companies still without page_content (90.8%)
- 3,256 network still without page_content (92.4%)
- 4,186 companies without website (91.7%)
- 0% email on network (3,525 rows)
- 0% phone on network
- 0% domain on companies
- 537 orphaned entities (no connections)
**Next loop plan (L11-30):**
- L11-14: Notion page content extraction at scale (query Notion MCP for remaining 4,000+ companies)
- L15-18: Web enrichment batch 2-5 (websites, LinkedIn for network)
- L19-22: Network email extraction from LinkedIn/web search
- L23-26: Domain extraction from websites
- L27-30: Re-embed after enrichment, verify quality improvement

### M7: Megamind | Loop 20 ✅ | Next: L21-40
**What's done:** All blockers fixed, deployed, 41 depth grades, cascade events, convergence monitoring
**What's not done:**
- strategic_score not consumed by compute_user_priority_score (M5 broken feedback)
- Only 41/115 actions depth-graded (36%)
- Convergence ratio 0.28 (target >0.5)
- No real Megamind agent sessions yet (agent is live but hasn't processed real inbox)
**Next loop plan (L21-40):**
- L21-24: Fix M7→M5 feedback loop (add strategic_score to priority function)
- L25-28: Auto-grade remaining 74 ungraded actions
- L29-32: Test Megamind agent via orchestrator inbox message
- L33-36: Convergence optimization (tune thresholds, decay rates)
- L37-40: Strategic assessment automation (daily cron)

### M5: Scoring | Loop 20 ✅ | Next: L21-40
**What's done:** 6-factor model, 4 fixes (clamp, decay, acceptance, score), percentile normalization, staleness boost
**What's not done:**
- Score compression still at 60% in bucket 8 (within stored user_priority_score)
- blended_score from action_scores_ranked not yet used by WebFront
- M7 strategic_score not incorporated
- Acceptance signal weak (23 accepted / 2 dismissed — not enough data)
**Next loop plan (L21-40):**
- L21-24: Integrate strategic_score into compute_user_priority_score (close M7→M5 loop)
- L25-28: Switch WebFront to use blended_score from action_scores_ranked view
- L29-32: Add outcome rating feedback → preference_weight_adjustments
- L33-36: Train on accumulated accept/dismiss data
- L37-40: Score validation with user (show top-10, get approval)

### M6: IRGI | Loop 20 ✅ | Next: L21-40
**What's done:** All 8 functions, network support, bias detection, FTS rebuilt, P0 fixes
**What's not done:**
- Search 62/100 without embeddings (Edge Function needed for text-to-vector)
- 3 false positives in suggest_actions for USTOL thesis
- Same VC partners repeat across all thesis suggestions (diversity constraint needed)
- semantic_score shows 0 in hybrid_search results
**Next loop plan (L21-40):**
- L21-24: Fix semantic_score display in hybrid_search
- L25-28: Add diversity constraint to suggest_actions_for_thesis (no repeated names across theses)
- L29-32: Tighten USTOL vector threshold (0.5→0.6)
- L33-36: After M12 enrichment, re-verify embedding quality
- L37-40: Add new intelligence functions (find_similar_network, thesis_momentum_report)

### M10: CIR | Loop 20 ✅ | Next: L21-40
**What's done:** Triggers, propagation, queue healthy, dead-letter, decay, state tracking
**What's not done:**
- Queue processor routing gap (logs but doesn't always call process_cir_queue_item)
- 537 orphaned entities
- Connection decay hasn't fired in production yet (created today)
- No real-world propagation test (only synthetic)
**Next loop plan (L21-40):**
- L21-24: Fix queue processor to always call process_cir_queue_item
- L25-28: Expand connections to cover orphaned entities
- L29-32: Monitor decay cron after 24h (should fire at 21:30 UTC)
- L33-36: Real-world propagation test (update a company, verify cascade)
- L37-40: Performance optimization (batch propagation, connection pruning)

### M9: Intel QA | Loop 20 ✅ | Next: L21-40
**What's done:** 20+ audit reports, final scorecard 7.3/10
**What's not done:**
- Re-audit after M5 percentile normalization
- Re-audit after M12 page content loading
- Cross-machine integration gaps not yet fixed
**Next loop plan (L21-40):**
- L21-24: Post-enrichment re-audit (after M12 loads more page content)
- L25-28: M7→M5 feedback loop verification (after M5 integrates strategic_score)
- L29-32: Search quality re-audit (after M6 fixes semantic_score)
- L33-36: Cindy pipeline audit (after M8 processes real data)
- L37-40: Full system stress test + regression suite

### M1: WebFront | Loop 20 ✅ | Next: L21-40
**What's done:** /comms, /strategy, depth grading, Geist, a11y, responsive, QA fixes, empty states
**What's not done:**
- Score breakdown radar chart (M5 action_score_breakdown view exists but not rendered)
- blended_score from action_scores_ranked not used
- Network page still shows limited data (email/phone 0%)
- Supabase Realtime subscriptions (live updates)
- Outcome rating UX refinement
**Next loop plan (L21-40):**
- L21-24: Switch /actions to use blended_score, add score breakdown bars
- L25-28: Network page enrichment (after M12 adds email/LinkedIn)
- L29-32: Supabase Realtime for live action updates
- L33-36: Outcome rating flow improvement (quick rate from action list)
- L37-40: Performance audit + Lighthouse optimization

### M8: Cindy | Loop 20 ✅ | Next: L21-40
**What's done:** All 5 processors built+tested, deployed, embedding triggers, sample data
**What's not done:**
- AgentMail API key not deployed to droplet .env
- Granola MCP permission blocked from Cindy agent
- No real email/meeting data processed yet
- Calendar API setup (only .ics parsing)
- WhatsApp backup encrypted (.enc) — uses Export Chat .txt fallback
**Next loop plan (L21-40):**
- L21-24: Deploy AgentMail API key, test real email fetch
- L25-28: Fix Granola MCP permissions for Cindy agent on droplet
- L29-32: Process first real batch of emails → obligations
- L33-36: Calendar integration via AgentMail .ics attachments
- L37-40: WhatsApp Export Chat batch processing

---

## Database Snapshot (Supabase llfkxnsfczludgigknbs, Mumbai)

### Tables (28 tables, ~48,831 total rows)
| Table | Rows | Key State |
|-------|------|-----------|
| entity_connections | 19,421 | 11 pair types: co-co 6,867, net-co 5,019(current+past emp), net-net 1,998, co-thesis 2,000, portfolio-thesis 176, portfolio-co 142, action-thesis 138 |
| cir_state | 8,562 | All entities tracked, 98.7% fresh (<1 day) |
| cir_propagation_log | 7,534 | Healthy, queue=0, 7 event types |
| companies | 4,565 | 100% embedded, 8.3% website (379), 9.2% page_content (422), 87.6% linkedin via network |
| network_dedup_backup | 3,722 | Pre-dedup backup — DROP when verified |
| network | 3,525 | 100% embedded, 87.6% linkedin (3,089), 86.8% roles, 7.6% page_content (269) |
| change_events | 742 | Historical sync events |
| portfolio | 142 | 100% embedded, 100% research_file_path, 12.7% thesis_connection (18) |
| actions_queue | 115 | 100% scored (avg 8.83), 100% IRGI, 41 depth-graded, strategic_score on all |
| action_scores | 90 | Materialized view, 15-min auto-refresh |
| depth_grades | 41 | M7 auto-graded (17 investigate, 1 scan, 2 skip + 21 more) |
| notifications | 34 | System notifications |
| content_digests | 22 | All published |
| preference_weight_adjustments | 16 | 4 dimensions (action_type, priority, source, thesis) |
| strategic_config | 12 | Trust=manual, decay=0.7, budget=$10/day |
| interactions | 11 | Sample data (4 surfaces: email, meeting, whatsapp, granola) |
| sync_metadata | 8 | Sync state |
| thesis_threads | 8 | bias_flags JSONB, 3 flagged (AI-Native HIGH, Cybersec+Agentic MEDIUM) |
| obligations | 7 | Sample data (urgency: overdue/urgent/upcoming) |
| cir_propagation_rules | 7 | All enabled (content, thesis, actions, outcomes, interactions, network, companies) |
| cascade_events | 6 | Test cascades with propagation |
| action_outcomes | 4 | All proposed |
| strategic_assessments | 3 | Daily snapshots |
| cai_inbox | 1 | CAI relay |
| datum_requests | 0 | Ready for Datum |
| people_interactions | 0 | Ready for Cindy |
| context_gaps | 0 | Ready for Cindy |
| sync_queue | 0 | Unused |

### Key Views
| View | Purpose |
|------|---------|
| user_triage_queue | 83 user actions sorted by priority |
| agent_work_queue | 8 agent-delegable actions |
| action_scores (matview) | Cached scores, 15-min refresh |
| action_scores_ranked | Percentile normalization within type |
| action_score_breakdown | 6 factors exposed for WebFront |
| megamind_dashboard | Actions + depth grades |
| megamind_convergence | 15-column system health |
| bias_summary | Thesis bias flags + severity |
| staleness_monitor | CIR entity freshness |
| staleness_alerts | Entities stale > 30 days |
| obligation_dashboard | Obligations with urgency |
| interaction_timeline | Interactions with signal richness |
| entity_relationships | Cross-entity links |

### pg_cron Jobs (5 active)
1. Embedding processor (10s)
2. Connection decay (daily 21:30 UTC)
3. action_scores matview refresh (15 min)
4. Stale action check (hourly)
5. CIR queue processor (every minute)

### pgmq Queues
- `embedding_jobs` — auto-embedding pipeline
- `cir_queue` — CIR change events (healthy, ~0 pending)
- `cir_dead_letter` — failed CIR messages (0)

---

## Uncommitted Changes (284 files)
- 243 modified files (column rename propagation, agent CLAUDE.md fixes, audit updates)
- 41 new files (Cindy processors, audit reports, SQL files, enrichment scripts)
- **MUST commit before next session work**

## Git State
- Parent repo: `RTinkslinger/aicos-cc-adk` on `main`, 284 uncommitted changes
- Digests repo: `RTinkslinger/aicos-digests` on `main`, clean (3 pushes deployed this session)

---

## Verified DB Object Counts (from audit)
- **28 tables**, ~48,831 total rows
- **41 custom functions** (+ 31 pg_trgm extension)
- **15 views** (user_triage_queue, agent_work_queue, action_scores matview, action_scores_ranked, action_score_breakdown, megamind_dashboard, megamind_convergence, bias_summary, staleness_monitor, staleness_alerts, obligation_dashboard, interaction_timeline, entity_relationships, interactions_public, obligations_with_staleness, cir_staleness_monitor)
- **38 triggers** across 11 tables (3-trigger embedding pattern + CIR triggers per table)
- **134 indexes** (portfolio 20, companies 14, network 13, obligations 9, interactions 9)
- **5 pg_cron jobs** (embeddings 10s, decay daily, matview 15min, stale hourly, CIR queue 1min)
- **3 pgmq queues** (embedding_jobs, cir_queue, cir_dead_letter)

## Session Stats
- **76 agents spawned**, 70 completed, 6 hit API limit
- **8 machines**, 7 at loop 20, 1 at loop 10
- **20+ audit reports** in docs/audits/
- **3 deployments** to digest.wiki, **2 deploys** to droplet
- Quality: **6.2 → 7.3/10**
- IRGI: **8.75/10**, CIR: **8.6/10**, Cindy: **7.5/10**, Scoring: **7.5/10**
- Entity connections: **0 → 19,421**
- All 8,232 entities **100% embedded**
